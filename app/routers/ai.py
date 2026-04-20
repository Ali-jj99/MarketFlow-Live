"""I created this route to integrate AI-powered summaries into the platform.
I use OpenRouter's API with OpenAI's GPT-OSS 120B model because it's free,
follows instructions well, and produces clear educational explanations —
which fits the goal of helping users understand what each stock or crypto is."""

import requests as http_requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.config import OPENROUTER_API_KEY

router = APIRouter(prefix="/api/ai", tags=["ai"])

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_ID = "openai/gpt-oss-120b:free"

# I implemented a simple in-memory cache so the same asset doesn't trigger
# repeated API calls — this keeps the platform fast and avoids unnecessary requests.
_summary_cache: dict[str, str] = {}

# GPT-OSS follows system messages properly (unlike Nemotron which echoed them),
# so I can now use a system message to set the tone and rules consistently.
_SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "You are a friendly finance tutor for beginners on an educational platform. "
        "Explain in plain, conversational English. Keep answers to 2-4 sentences. "
        "If you use any financial term, briefly define it. "
        "Never give investment advice — stick to education and factual context. "
        "Do not use bullet points or numbered lists. "
        "When recent news is provided, reference it naturally to explain price moves."
    ),
}


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------

class NewsArticle(BaseModel):
    title: str = ""
    sentiment: str = "Neutral"
    published: str = ""


class SummaryRequest(BaseModel):
    symbol: str
    name: str = ""
    asset_type: str = "stock"
    price: float = 0.0
    change: float = 0.0
    news: list[NewsArticle] = []


class AskRequest(BaseModel):
    symbol: str
    name: str = ""
    asset_type: str = "stock"
    price: float = 0.0
    change: float = 0.0
    question: str
    news: list[NewsArticle] = []


class ChartRequest(BaseModel):
    symbol: str
    name: str = ""
    asset_type: str = "stock"
    period: str = "7d"
    history: list[dict] = []
    question: str = ""
    news: list[NewsArticle] = []


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _call_ai(messages: list[dict], max_tokens: int = 250) -> str:
    """Centralised API call logic — keeps the code DRY and easier to maintain."""
    resp = http_requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": MODEL_ID,
            "messages": [_SYSTEM_MESSAGE] + messages,
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


def _build_news_context(news: list[NewsArticle]) -> str:
    """Format matched news articles into a compact context block.
    Returns empty string when no news is available so the prompt
    works identically to before (graceful degradation)."""
    if not news:
        return ""
    lines = []
    for art in news[:2]:
        lines.append(f'- "{art.title}" ({art.sentiment})')
    return "\nRecent news:\n" + "\n".join(lines)


# ---------------------------------------------------------------------------
# Few-shot examples
# ---------------------------------------------------------------------------

# Few-shot examples help the model match the desired tone and length,
# complementing the system message with concrete demonstrations.
_SUMMARY_EXAMPLES = [
    {
        "role": "user",
        "content": (
            "Tell me about Apple Inc. (AAPL), a stock at $185.50, up 1.20% today.\n"
            "Recent news:\n"
            '- "Apple announces record Q2 services revenue" (Bullish)'
        ),
    },
    {
        "role": "assistant",
        "content": (
            "Apple is one of the biggest tech companies in the world, known for "
            "making iPhones, MacBooks, and running services like iCloud and Apple Music. "
            "The stock is up a bit today, which lines up with their recent news about "
            "hitting record revenue from services like subscriptions and the App Store."
        ),
    },
    {
        "role": "user",
        "content": "Tell me about Bitcoin (bitcoin), a cryptocurrency at $64,200.00, down 2.30% today."
    },
    {
        "role": "assistant",
        "content": (
            "Bitcoin is the original cryptocurrency, often called digital gold because "
            "people use it as a store of value. It's down a couple percent today, which "
            "is pretty normal for crypto since it tends to swing more than traditional stocks."
        ),
    },
]

_ASK_EXAMPLES = [
    {
        "role": "user",
        "content": (
            "About Tesla Inc. (TSLA), a stock at $245.00, up 3.50% today: Why is it going up?\n"
            "Recent news:\n"
            '- "Tesla Q1 deliveries beat analyst estimates" (Bullish)'
        ),
    },
    {
        "role": "assistant",
        "content": (
            "Tesla's price can jump on things like strong delivery numbers, and "
            "today's news about Q1 deliveries beating estimates is likely fuelling "
            "that move. A 3.5% rise in a day is fairly typical for Tesla since "
            "it's known for big swings on news like this."
        ),
    },
]

# Few-shot example for chart analysis — now includes OHLC data so the model
# can reference intraday ranges, not just closing prices.
_CHART_EXAMPLE = [
    {
        "role": "user",
        "content": (
            "Here is the 7 Days price data for Tesla Inc. (TSLA):\n"
            "2026-04-01: O$238 H$241 L$237 C$240 | "
            "2026-04-02: O$240 H$240 L$236 C$238.50 | "
            "2026-04-03: O$239 H$243 L$238 C$242.10 | "
            "2026-04-04: O$242 H$246 L$241 C$245 | "
            "2026-04-05: O$245 H$246 L$242 C$243.80 | "
            "2026-04-06: O$244 H$250 L$243 C$248.90 | "
            "2026-04-07: O$249 H$253 L$248 C$252.30\n"
            "Overall: up 5.13% (from $240.00 to $252.30)."
        ),
    },
    {
        "role": "assistant",
        "content": (
            "Tesla had a strong week, climbing from $240 on Apr 1 to $252.30 by "
            "Apr 7. There was a small dip on Apr 2 where the low hit $236, but it "
            "recovered quickly. The biggest push came Apr 6-7, with the high "
            "reaching $253. Overall a solid 5.1% gain for the week."
        ),
    },
]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/summary")
def get_ai_summary(req: SummaryRequest):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    has_news = len(req.news) > 0
    cache_key = f"{req.symbol.lower()}:{req.asset_type}:{'n' if has_news else 'b'}"
    if cache_key in _summary_cache:
        return {"summary": _summary_cache[cache_key], "source": "cache"}

    direction = "up" if req.change > 0 else ("down" if req.change < 0 else "flat")
    asset_label = f"{req.name} ({req.symbol.upper()})" if req.name else req.symbol.upper()
    type_label = "stock" if req.asset_type == "stock" else "cryptocurrency"

    user_content = (
        f"Tell me about {asset_label}, a {type_label} at "
        f"${req.price:,.2f}, {direction} {abs(req.change):.2f}% today."
    )
    user_content += _build_news_context(req.news)

    messages = list(_SUMMARY_EXAMPLES) + [
        {"role": "user", "content": user_content},
    ]

    try:
        summary = _call_ai(messages, max_tokens=250)
        _summary_cache[cache_key] = summary
        return {"summary": summary, "source": "live"}
    except http_requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI service timed out — please try again")
    except Exception as e:
        print(f"[ai] GPT-OSS request failed: {e}")
        raise HTTPException(status_code=502, detail="AI summary is temporarily unavailable")


@router.post("/ask")
def ask_ai_question(req: AskRequest):
    """Users can ask their own questions about any asset — the educational goal
    means they should be able to interact with the data and learn by asking."""
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    asset_label = f"{req.name} ({req.symbol.upper()})" if req.name else req.symbol.upper()
    type_label = "stock" if req.asset_type == "stock" else "cryptocurrency"
    direction = "up" if req.change > 0 else ("down" if req.change < 0 else "flat")

    user_content = (
        f"About {asset_label} (a {type_label} at ${req.price:,.2f}, "
        f"{direction} {abs(req.change):.2f}% today): {req.question}"
    )
    user_content += _build_news_context(req.news)

    messages = list(_ASK_EXAMPLES) + [
        {"role": "user", "content": user_content},
    ]

    try:
        answer = _call_ai(messages, max_tokens=250)
        return {"answer": answer}
    except http_requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI service timed out")
    except Exception as e:
        print(f"[ai] GPT-OSS ask failed: {e}")
        raise HTTPException(status_code=502, detail="AI is temporarily unavailable")


@router.post("/chart")
def analyse_chart(req: ChartRequest):
    """Analyses actual chart data — specific dates, OHLC prices — rather than
    giving generic summaries. The frontend sends the price history points so
    the AI can reference them directly."""
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    asset_label = f"{req.name} ({req.symbol.upper()})" if req.name else req.symbol.upper()
    type_label = "stock" if req.asset_type == "stock" else "cryptocurrency"

    # Format each day with full OHLC so the AI can discuss intraday ranges.
    data_lines = []
    for point in req.history:
        date = point.get("date", "")
        o = point.get("open", point.get("price", 0))
        h = point.get("high", point.get("price", 0))
        low = point.get("low", point.get("price", 0))
        c = point.get("price", point.get("close", 0))
        data_lines.append(f"{date}: O${o:,.0f} H${h:,.0f} L${low:,.0f} C${c:,.2f}")
    data_str = " | ".join(data_lines)

    start_price = req.history[0].get("price", 0) if req.history else 0
    end_price = req.history[-1].get("price", 0) if req.history else 0
    overall_change = round(((end_price - start_price) / start_price) * 100, 2) if start_price else 0
    direction = "up" if overall_change > 0 else ("down" if overall_change < 0 else "flat")

    user_content = (
        f"Here is the {req.period} price data for {asset_label} ({type_label}):\n"
        f"{data_str}\n"
        f"Overall: {direction} {abs(overall_change):.2f}% "
        f"(from ${start_price:,.2f} to ${end_price:,.2f})."
    )
    user_content += _build_news_context(req.news)

    if req.question:
        user_content += f"\nMy question: {req.question}"

    messages = list(_CHART_EXAMPLE) + [
        {"role": "user", "content": user_content},
    ]

    try:
        answer = _call_ai(messages, max_tokens=350)
        return {"answer": answer}
    except http_requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI service timed out")
    except Exception as e:
        print(f"[ai] GPT-OSS chart analysis failed: {e}")
        raise HTTPException(status_code=502, detail="AI chart analysis is temporarily unavailable")
