"""
Comparison route: fetch data for multiple assets side by side.
"""

from fastapi import APIRouter, Query, HTTPException

from app.services.market_data import (
    get_stock_data,
    get_crypto_data,
    get_stock_history,
    get_crypto_history,
)

router = APIRouter(prefix="/api/market", tags=["compare"])


@router.get("/compare")
def compare_assets(
    symbols: str = Query(..., description="Comma-separated symbols, e.g. AAPL,TSLA"),
    asset_types: str = Query(..., description="Comma-separated types matching symbols, e.g. stock,stock"),
    period: str = Query("7d", description="History period: 7d | 1mo | 3mo"),
):
    """
    Compare two or more assets side by side.
    Returns current price data plus price history for each asset.

    Example: /api/market/compare?symbols=AAPL,bitcoin&asset_types=stock,crypto
    """
    symbol_list = [s.strip() for s in symbols.split(",")]
    type_list = [t.strip().lower() for t in asset_types.split(",")]

    if len(symbol_list) != len(type_list):
        raise HTTPException(
            status_code=400,
            detail="symbols and asset_types must have the same number of items",
        )

    if len(symbol_list) < 2:
        raise HTTPException(status_code=400, detail="Provide at least 2 assets to compare")

    if len(symbol_list) > 4:
        raise HTTPException(status_code=400, detail="Maximum 4 assets can be compared at once")

    results = []
    days_map = {"7d": 7, "1mo": 30, "3mo": 90}

    for symbol, asset_type in zip(symbol_list, type_list):
        if asset_type == "stock":
            data = get_stock_data(symbol)
            history = get_stock_history(symbol, period=period)
        elif asset_type == "crypto":
            data = get_crypto_data(symbol)
            days = days_map.get(period, 7)
            history = get_crypto_history(symbol, days=days)
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid asset_type '{asset_type}'. Use 'stock' or 'crypto'.",
            )

        results.append({**data, "history": history})

    return {"period": period, "assets": results}
