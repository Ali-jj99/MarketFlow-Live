"""I created this route to integrate AI-powered summaries into the platform.
I used OpenRouter's API with the NVIDIA Nemotron 3 Super model because it's
free, reliable, and ranked highly for finance — which fits the educational
goal of helping users understand what each stock or crypto actually is."""

import requests as http_requests
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from app.config import OPENROUTER_API_KEY

router = APIRouter(prefix="/api/ai", tags=["ai"])

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL_ID = "nvidia/nemotron-3-super-120b-a12b:free"

# I implemented a simple in-memory cache so the same asset doesn't trigger
# repeated API calls — this keeps the platform fast and avoids unnecessary requests.
_summary_cache: dict[str, str] = {}


def _call_nemotron(messages: list[dict], max_tokens: int = 120) -> str:
    """I centralised the API call logic here to avoid repeating it
    in every endpoint — keeps the code DRY and easier to maintain."""
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


# I switched to a few-shot prompting approach because Nemotron was echoing
# back system message instructions in its responses. By showing the model
# example Q&A pairs, it learns the expected format by imitation rather than
# by following rules it might repeat out loud.
_SUMMARY_EXAMPLES = [
    {
        "role": "user",
        "content": "Tell me about Apple Inc. (AAPL), a stock at $185.50, up 1.20% today."
    },
    {
        "role": "assistant",
        "content": (
            "Apple is one of the biggest tech companies in the world, known for "
            "making iPhones, MacBooks, and running services like iCloud and Apple Music. "
            "The stock is up a bit today, which could be tied to positive market "
            "sentiment or recent product news."
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
        "content": "About Tesla Inc. (TSLA), a stock at $245.00, up 3.50% today: Why is it going up?"
    },
    {
        "role": "assistant",
        "content": (
            "Tesla's price can jump on things like strong delivery numbers, new factory "
            "updates, or general excitement around electric vehicles. A 3.5% move up in "
            "a day is fairly typical for Tesla since it's known for big swings."
        ),
    },
]


@router.get("/summary")
def get_ai_summary(
    symbol: str = Query(..., description="Ticker or coin ID, e.g. AAPL or bitcoin"),
    name: str = Query("", description="Display name of the asset"),
    asset_type: str = Query("stock", description="stock or crypto"),
    price: float = Query(0.0, description="Current price"),
    change: float = Query(0.0, description="24h change percentage"),
):
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    cache_key = f"{symbol.lower()}:{asset_type}"
    if cache_key in _summary_cache:
        return {"summary": _summary_cache[cache_key], "source": "cache"}

    direction = "up" if change > 0 else ("down" if change < 0 else "flat")
    asset_label = f"{name} ({symbol.upper()})" if name else symbol.upper()
    type_label = "stock" if asset_type == "stock" else "cryptocurrency"

    messages = list(_SUMMARY_EXAMPLES) + [
        {
            "role": "user",
            "content": (
                f"Tell me about {asset_label}, a {type_label} at "
                f"${price:,.2f}, {direction} {abs(change):.2f}% today."
            ),
        },
    ]

    try:
        summary = _call_nemotron(messages, max_tokens=120)
        _summary_cache[cache_key] = summary
        return {"summary": summary, "source": "live"}
    except http_requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI service timed out — please try again")
    except Exception as e:
        print(f"[ai] Nemotron request failed: {e}")
        raise HTTPException(status_code=502, detail="AI summary is temporarily unavailable")


@router.get("/ask")
def ask_ai_question(
    symbol: str = Query(..., description="Ticker or coin ID"),
    name: str = Query("", description="Display name of the asset"),
    asset_type: str = Query("stock", description="stock or crypto"),
    price: float = Query(0.0, description="Current price"),
    change: float = Query(0.0, description="24h change percentage"),
    question: str = Query(..., description="The user's question about this asset"),
):
    """I implemented this endpoint so users can ask their own questions about
    any asset. I did this because the educational goal of the platform means
    users should be able to interact with the data and learn by asking."""
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    asset_label = f"{name} ({symbol.upper()})" if name else symbol.upper()
    type_label = "stock" if asset_type == "stock" else "cryptocurrency"
    direction = "up" if change > 0 else ("down" if change < 0 else "flat")

    messages = list(_ASK_EXAMPLES) + [
        {
            "role": "user",
            "content": (
                f"About {asset_label} (a {type_label} at ${price:,.2f}, "
                f"{direction} {abs(change):.2f}% today): {question}"
            ),
        },
    ]

    try:
        answer = _call_nemotron(messages, max_tokens=120)
        return {"answer": answer}
    except http_requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI service timed out")
    except Exception as e:
        print(f"[ai] Nemotron ask failed: {e}")
        raise HTTPException(status_code=502, detail="AI is temporarily unavailable")


class ChartRequest(BaseModel):
    symbol: str
    name: str = ""
    asset_type: str = "stock"
    period: str = "7d"
    history: list[dict] = []
    question: str = ""


# I used a few-shot example for chart analysis too, showing the model
# exactly what a good chart summary looks like with real dates and prices.
_CHART_EXAMPLE = [
    {
        "role": "user",
        "content": (
            "Here is the 7 Days price data for Tesla Inc. (TSLA):\n"
            "2026-04-01: $240.00 | 2026-04-02: $238.50 | 2026-04-03: $242.10 | "
            "2026-04-04: $245.00 | 2026-04-05: $243.80 | 2026-04-06: $248.90 | "
            "2026-04-07: $252.30\n"
            "Overall: up 5.13% (from $240.00 to $252.30)."
        ),
    },
    {
        "role": "assistant",
        "content": (
            "Tesla had a strong week, climbing from $240.00 on Apr 1 to $252.30 by "
            "Apr 7. There was a small dip on Apr 2 down to $238.50, but it recovered "
            "quickly. The biggest jump was between Apr 5 and Apr 7, where it gained "
            "about $9 in two days. Overall a solid 5.1% gain for the week."
        ),
    },
]


@router.post("/chart")
def analyse_chart(req: ChartRequest):
    """I created this endpoint so the AI can analyse actual chart data —
    specific dates and prices — rather than giving generic summaries.
    The frontend sends the price history points so the AI can reference them."""
    if not OPENROUTER_API_KEY:
        raise HTTPException(status_code=503, detail="AI service not configured")

    asset_label = f"{req.name} ({req.symbol.upper()})" if req.name else req.symbol.upper()
    type_label = "stock" if req.asset_type == "stock" else "cryptocurrency"

    data_lines = []
    for point in req.history:
        date = point.get("date", "")
        price = point.get("price", 0)
        data_lines.append(f"{date}: ${price:,.2f}")
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

    if req.question:
        user_content += f"\nMy question: {req.question}"

    messages = list(_CHART_EXAMPLE) + [
        {"role": "user", "content": user_content},
    ]

    try:
        answer = _call_nemotron(messages, max_tokens=180)
        return {"answer": answer}
    except http_requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="AI service timed out")
    except Exception as e:
        print(f"[ai] Nemotron chart analysis failed: {e}")
        raise HTTPException(status_code=502, detail="AI chart analysis is temporarily unavailable")
