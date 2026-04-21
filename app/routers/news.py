import time
import requests as http_requests
from fastapi import APIRouter, Query

from app.config import ALPHA_VANTAGE_API_KEY

router = APIRouter(prefix="/api/news", tags=["news"])

_news_cache: dict = {"data": None, "timestamp": 0}
NEWS_CACHE_TTL = 1800


def _fetch_news(topic: str = "financial_markets", limit: int = 10) -> list[dict]:
    if not ALPHA_VANTAGE_API_KEY:
        return []

    url = (
        f"https://www.alphavantage.co/query"
        f"?function=NEWS_SENTIMENT"
        f"&topics={topic}"
        f"&limit={limit}"
        f"&apikey={ALPHA_VANTAGE_API_KEY}"
    )

    try:
        resp = http_requests.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

        articles = data.get("feed", [])
        results = []

        for article in articles[:limit]:
            score = float(article.get("overall_sentiment_score", 0))

            if score >= 0.15:
                sentiment = "Bullish"
            elif score <= -0.15:
                sentiment = "Bearish"
            else:
                sentiment = "Neutral"

            results.append({
                "title": article.get("title", "No title"),
                "summary": article.get("summary", "")[:200],
                "source": article.get("source", "Unknown"),
                "url": article.get("url", ""),
                "published": article.get("time_published", "")[:8],  # YYYYMMDD
                "sentiment": sentiment,
                "sentiment_score": round(score, 3),
            })

        return results

    except Exception as e:
        print(f"[news] Alpha Vantage fetch failed: {e}")
        return []


@router.get("")
def get_financial_news(
    topic: str = Query("financial_markets", description="News topic filter"),
    limit: int = Query(10, ge=1, le=20, description="Number of articles"),
):
    now = time.time()

    if _news_cache["data"] is not None and (now - _news_cache["timestamp"]) < NEWS_CACHE_TTL:
        cached = _news_cache["data"]
        return {
            "articles": cached[:limit],
            "source": "cache",
            "api_configured": bool(ALPHA_VANTAGE_API_KEY),
        }

    articles = _fetch_news(topic=topic, limit=limit)

    if articles:
        _news_cache["data"] = articles
        _news_cache["timestamp"] = now

    return {
        "articles": articles[:limit],
        "source": "live" if articles else "unavailable",
        "api_configured": bool(ALPHA_VANTAGE_API_KEY),
    }
