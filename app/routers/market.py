"""Market data routes: overview and price history."""

from fastapi import APIRouter, HTTPException, Query
from concurrent.futures import ThreadPoolExecutor

from app.services.market_data import (
    get_stock_data,
    get_crypto_data,
    get_crypto_data_batch,
    get_stock_history,
    get_crypto_history,
)

router = APIRouter(prefix="/api/market", tags=["market"])

DEFAULT_STOCKS = [
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "NFLX",
    "JPM", "V", "DIS", "BA", "AMD", "INTC", "PYPL",
]

DEFAULT_CRYPTOS = [
    "bitcoin", "ethereum", "tether", "binancecoin", "solana", "ripple",
    "usd-coin", "cardano", "dogecoin", "avalanche-2", "polkadot",
    "chainlink", "litecoin", "tron", "shiba-inu",
]


@router.get("/overview")
def market_overview():
    # I implemented parallel fetching for stocks and batched API calls for crypto
    # because fetching 30 assets one by one would take 30+ seconds.
    with ThreadPoolExecutor(max_workers=6) as executor:
        stock_results = list(executor.map(get_stock_data, DEFAULT_STOCKS))

    crypto_results = get_crypto_data_batch(DEFAULT_CRYPTOS)

    return {
        "stocks": stock_results,
        "crypto": crypto_results,
    }


@router.get("/history/{symbol}")
def price_history(
    symbol: str,
    asset_type: str = Query(..., description="stock or crypto"),
    period: str = Query("7d", description="7d | 1mo | 3mo"),
):
    if asset_type == "stock":
        data = get_stock_history(symbol, period=period)
    elif asset_type == "crypto":
        days_map = {"7d": 7, "1mo": 30, "3mo": 90}
        days = days_map.get(period, 7)
        data = get_crypto_history(symbol, days=days)
    else:
        raise HTTPException(status_code=400, detail="asset_type must be 'stock' or 'crypto'")

    return {"symbol": symbol, "period": period, "history": data}
