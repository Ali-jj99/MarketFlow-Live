"""AI-powered asset analysis routes using structured JSON output.

I rebuilt the AI endpoints to use schema-driven JSON responses instead of
free-text generation. Each endpoint returns a typed Pydantic model so the
frontend can render structured, consistent output (overview, key facts,
sentiment, risks etc.) rather than unpredictable prose.

Key design decisions:
- System prompt drives behaviour; context is a structured key:value block.
- Output schema is embedded in the prompt so the model knows exactly what
  fields to fill. Field `description` attributes act as per-field instructions.
- JSON mode via OpenRouter's response_format, with a defensive retry if the
  first response fails validation — and a final plain-text fallback so the
  feature never fully breaks.
- POST endpoints with JSON bodies for richer context passing.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Literal, Optional

import requests as http_requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.config import OPENROUTER_API_KEY

log = logging.getLogger(__name__)
router = APIRouter(prefix="/api/ai", tags=["ai"])

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_ID = "nvidia/nemotron-3-super-120b-a12b:free"


# ---------------------------------------------------------------------------
# Context model — everything the AI might want to know about an asset.
# Optional fields are only rendered into the prompt if present.
# ---------------------------------------------------------------------------

class AssetContext(BaseModel):
    symbol: str
    name: str = ""
    asset_type: Literal["stock", "crypto"] = "stock"
    price: float = 0.0
    change_pct_24h: float = 0.0
    volume_24h: Optional[float] = None
    market_cap: Optional[float] = None
    sector: Optional[str] = None
    week_52_high: Optional[float] = None
    week_52_low: Optional[float] = None
    all_time_high: Optional[float] = None
    description_hint: Optional[str] = None


# ---------------------------------------------------------------------------
# Typed response schemas. Field descriptions act as per-field instructions.
# ---------------------------------------------------------------------------

class SummaryResponse(BaseModel):
    overview: str = Field(
        description="2-3 sentences in plain English: what is this asset and what does it do?"
    )
    why_people_hold_it: str = Field(
        description="1-2 sentences on why investors typically buy this. No hype."
    )
    todays_move: str = Field(
        description=(
            "1-2 sentences on plausible general reasons today's price could be moving "
            "this way. Do NOT invent specific news or earnings. If the move is small, say so."
        )
    )
    key_facts: list[str] = Field(description="3-5 short factual bullet points.")
    sentiment: Literal["bullish", "bearish", "neutral"] = Field(
        description="Overall short-term read from the data provided only."
    )
    risks: list[str] = Field(
        description="2-3 educational risks a beginner should understand."
    )


class AskResponse(BaseModel):
    answer: str = Field(description="Direct, clear answer to the user's question in 2-4 sentences.")
    supporting_points: list[str] = Field(description="2-4 facts that back the answer.")
    caveats: list[str] = Field(
        description="1-2 things the answer doesn't account for, or where the user should be careful."
    )
    confidence: Literal["low", "medium", "high"] = Field(
        description="How well the provided context supports the answer."
    )


class ChartMoment(BaseModel):
    date: str
    price: float
    note: str = Field(description="What stood out about this point (e.g. 'largest single-day drop').")


class ChartAnalysisResponse(BaseModel):
    trend_summary: str = Field(description="2-3 sentence overview of what happened in this period.")
    overall_direction: Literal["up", "down", "flat"]
    overall_change_pct: float
    volatility: Literal["low", "medium", "high"]
    key_moments: list[ChartMoment] = Field(
        description="2-4 notable points in the series — peaks, troughs, big moves."
    )
    takeaway: str = Field(description="One-line headline summarising the chart.")


# ---------------------------------------------------------------------------
# Prompt plumbing
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = (
    "You are a finance explainer for a retail education platform. Your audience "
    "is curious beginners: use plain language, define jargon when you use it, "
    "and never invent specific news, numbers, or insider reasons for a price "
    "move. If a move could have multiple causes, say so.\n\n"
    "You will receive structured asset context followed by a JSON schema. "
    "Respond with a SINGLE valid JSON object matching that schema exactly. "
    "No markdown fences, no prose before or after, no restating of these "
    "instructions."
)


def _render_context(ctx: AssetContext) -> str:
    """Turn the context model into a clean key:value block."""
    direction = (
        "up" if ctx.change_pct_24h > 0
        else "down" if ctx.change_pct_24h < 0
        else "flat"
    )
    label = f"{ctx.name} ({ctx.symbol.upper()})" if ctx.name else ctx.symbol.upper()
    type_label = "stock" if ctx.asset_type == "stock" else "cryptocurrency"

    lines = [
        f"Asset:         {label}",
        f"Type:          {type_label}",
        f"Price:         ${ctx.price:,.2f}",
        f"24h change:    {direction} {abs(ctx.change_pct_24h):.2f}%",
    ]
    if ctx.volume_24h is not None:
        lines.append(f"24h volume:    ${ctx.volume_24h:,.0f}")
    if ctx.market_cap is not None:
        lines.append(f"Market cap:    ${ctx.market_cap:,.0f}")
    if ctx.sector:
        lines.append(f"Sector:        {ctx.sector}")
    if ctx.week_52_low is not None and ctx.week_52_high is not None:
        lines.append(f"52-week range: ${ctx.week_52_low:,.2f} – ${ctx.week_52_high:,.2f}")
    if ctx.all_time_high is not None:
        lines.append(f"All-time high: ${ctx.all_time_high:,.2f}")
    if ctx.description_hint:
        lines.append(f"Notes:         {ctx.description_hint}")

    return "\n".join(lines)


def _strip_fences(text: str) -> str:
    """Remove markdown code fences that some models wrap JSON in."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*", "", text)
    text = re.sub(r"\s*```$", "", text)
    return text.strip()


def _call_nemotron_json(
    system: str,
    user: str,
    response_model: type[BaseModel],
    max_tokens: int = 500,
) -> BaseModel:
    """Call the model asking for JSON matching response_model's schema.
    Validates and retries once if the first response fails parsing.
    Falls back to a plain-text approach if JSON mode completely fails."""
    schema = response_model.model_json_schema()
    schema_block = (
        "Respond with a JSON object matching this schema:\n"
        f"{json.dumps(schema, indent=2)}"
    )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": f"{user}\n\n{schema_block}"},
    ]

    def _post(msgs: list[dict], use_json_mode: bool = True) -> str:
        payload = {
            "model": MODEL_ID,
            "messages": msgs,
            "max_tokens": max_tokens,
            "temperature": 0.3,
        }
        if use_json_mode:
            payload["response_format"] = {"type": "json_object"}

        resp = http_requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()
        return (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
            .strip()
        )

    # Attempt 1: JSON mode
    raw = _post(messages)
    raw = _strip_fences(raw)
    try:
        return response_model.model_validate_json(raw)
    except Exception as first_err:
        log.warning("First JSON parse failed (%s); retrying.", first_err)

    # Attempt 2: Stricter retry
    retry_messages = messages + [
        {"role": "assistant", "content": raw},
        {
            "role": "user",
            "content": (
                "That wasn't valid JSON matching the schema. "
                "Reply again with ONLY the JSON object — no prose, no markdown."
            ),
        },
    ]
    raw2 = _post(retry_messages)
    raw2 = _strip_fences(raw2)
    try:
        return response_model.model_validate_json(raw2)
    except Exception as second_err:
        log.warning("Second JSON parse also failed (%s); using fallback.", second_err)
        # Final fallback: return whatever text we got in a minimal valid structure
        raise ValueError(f"JSON parsing failed after retry: {second_err}")


# ---------------------------------------------------------------------------
# Plain-text fallback (reuses the old few-shot approach if JSON mode fails)
# ---------------------------------------------------------------------------

def _call_nemotron_text(messages: list[dict], max_tokens: int = 150) -> str:
    """Simple text completion — used as fallback if JSON mode fails."""
    resp = http_requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL_ID,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    text = (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
    )
    if not text:
        raise ValueError("Empty response from AI model")
    return text


# ---------------------------------------------------------------------------
# In-memory cache
# ---------------------------------------------------------------------------

_summary_cache: dict[str, dict] = {}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/summary", response_model=dict)
def get_ai_summary(ctx: AssetContext):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    cache_key = f"{ctx.symbol.lower()}:{ctx.asset_type}"
    if cached := _summary_cache.get(cache_key):
        return {"summary": cached, "source": "cache", "format": "structured"}

    user_msg = (
        "Explain the following asset to a beginner and assess today's move.\n\n"
        f"{_render_context(ctx)}"
    )

    try:
        summary = _call_nemotron_json(SYSTEM_PROMPT, user_msg, SummaryResponse, max_tokens=500)
        result = summary.model_dump()
        _summary_cache[cache_key] = result
        return {"summary": result, "source": "live", "format": "structured"}
    except (ValueError, Exception) as json_err:
        # Fallback to plain text if JSON mode fails
        log.warning("JSON summary failed, falling back to text: %s", json_err)
        try:
            direction = "up" if ctx.change_pct_24h > 0 else ("down" if ctx.change_pct_24h < 0 else "flat")
            label = f"{ctx.name} ({ctx.symbol.upper()})" if ctx.name else ctx.symbol.upper()
            type_label = "stock" if ctx.asset_type == "stock" else "cryptocurrency"
            messages = [
                {"role": "user", "content": f"Tell me about {label}, a {type_label} at ${ctx.price:,.2f}, {direction} {abs(ctx.change_pct_24h):.2f}% today. Keep it to 2-3 sentences, educational and casual."},
            ]
            text = _call_nemotron_text(messages, max_tokens=150)
            _summary_cache[cache_key] = text
            return {"summary": text, "source": "live", "format": "plain"}
        except http_requests.exceptions.Timeout:
            raise HTTPException(status_code=504, detail="AI service timed out")
        except Exception as e:
            log.exception("Nemotron summary completely failed: %s", e)
            raise HTTPException(status_code=502, detail="AI summary is temporarily unavailable")


class AskRequest(BaseModel):
    context: AssetContext
    question: str


@router.post("/ask", response_model=dict)
def ask_ai_question(req: AskRequest):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    user_msg = (
        "Answer the user's question about this asset. Stay general-educational — "
        "do NOT invent specific news events.\n\n"
        f"{_render_context(req.context)}\n\n"
        f"Question: {req.question}"
    )

    try:
        answer = _call_nemotron_json(SYSTEM_PROMPT, user_msg, AskResponse, max_tokens=500)
        return {"answer": answer.model_dump(), "format": "structured"}
    except (ValueError, Exception) as json_err:
        log.warning("JSON ask failed, falling back to text: %s", json_err)
        try:
            label = f"{req.context.name} ({req.context.symbol.upper()})" if req.context.name else req.context.symbol.upper()
            messages = [
                {"role": "user", "content": f"About {label}: {req.question}. Answer in 2-3 sentences, educational and casual."},
            ]
            text = _call_nemotron_text(messages, max_tokens=150)
            return {"answer": text, "format": "plain"}
        except http_requests.exceptions.Timeout:
            raise HTTPException(status_code=504, detail="AI service timed out")
        except Exception as e:
            log.exception("Nemotron ask completely failed: %s", e)
            raise HTTPException(status_code=502, detail="AI is temporarily unavailable")


class ChartPoint(BaseModel):
    date: str
    price: float


class ChartRequest(BaseModel):
    context: AssetContext
    period: str = "7d"
    history: list[ChartPoint]
    question: str = ""


@router.post("/chart", response_model=dict)
def analyse_chart(req: ChartRequest):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")
    if not req.history:
        raise HTTPException(status_code=400, detail="history is empty")

    start = req.history[0].price
    end = req.history[-1].price
    overall_pct = round(((end - start) / start) * 100, 2) if start else 0.0
    direction = "up" if overall_pct > 0 else "down" if overall_pct < 0 else "flat"

    data_lines = "\n".join(f"  {p.date}: ${p.price:,.2f}" for p in req.history)
    user_msg = (
        "Analyse the following price history.\n\n"
        f"{_render_context(req.context)}\n"
        f"Period:        {req.period}\n"
        f"Overall move:  {direction} {abs(overall_pct):.2f}% "
        f"(${start:,.2f} -> ${end:,.2f})\n\n"
        f"Price points:\n{data_lines}"
    )
    if req.question:
        user_msg += f"\n\nUser question: {req.question}"

    try:
        result = _call_nemotron_json(SYSTEM_PROMPT, user_msg, ChartAnalysisResponse, max_tokens=700)
        return {"analysis": result.model_dump(), "format": "structured"}
    except (ValueError, Exception) as json_err:
        log.warning("JSON chart failed, falling back to text: %s", json_err)
        try:
            label = f"{req.context.name} ({req.context.symbol.upper()})" if req.context.name else req.context.symbol.upper()
            data_str = " | ".join(f"{p.date}: ${p.price:,.2f}" for p in req.history)
            messages = [
                {"role": "user", "content": (
                    f"Here is the {req.period} price data for {label}:\n{data_str}\n"
                    f"Overall: {direction} {abs(overall_pct):.2f}% (from ${start:,.2f} to ${end:,.2f}). "
                    f"Explain the trend in 3-4 sentences referencing specific dates and prices."
                )},
            ]
            text = _call_nemotron_text(messages, max_tokens=200)
            return {"analysis": text, "format": "plain"}
        except http_requests.exceptions.Timeout:
            raise HTTPException(status_code=504, detail="AI service timed out")
        except Exception as e:
            log.exception("Nemotron chart analysis completely failed: %s", e)
            raise HTTPException(status_code=502, detail="AI chart analysis is temporarily unavailable")
