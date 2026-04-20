"""
Search route: look up any stock ticker or CoinGecko coin by name / symbol.
"""

from fastapi import APIRouter, Query

from app.services.market_data import search_stock, search_crypto

router = APIRouter(prefix="/api/market", tags=["search"])


@router.get("/search")
def search_assets(
    q: str = Query(..., min_length=1, description="Ticker symbol or coin name"),
    asset_type: str = Query("all", description="all | stock | crypto"),
):
    """
    Search for stocks and/or cryptocurrencies matching the query string.

    - asset_type='stock'  → only yfinance lookup
    - asset_type='crypto' → only CoinGecko lookup
    - asset_type='all'    → tries both and combines results

    Returns a list of MarketItem-compatible dicts.
    """
    results = []

    if asset_type in ("stock", "all"):
        stock_result = search_stock(q)
        if stock_result:
            results.append(stock_result)

    if asset_type in ("crypto", "all"):
        crypto_results = search_crypto(q)
        results.extend(crypto_results)

    return {"query": q, "results": results}
