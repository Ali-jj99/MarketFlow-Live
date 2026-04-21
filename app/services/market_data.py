import requests as http_requests
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

from app.services.cache import get_cached, get_stale, set_cached
from app.config import COINGECKO_API_KEY

COINGECKO_BASE = "https://api.coingecko.com/api/v3"
TIMEOUT = 8          # seconds — HTTP request timeout


STOCK_DISPLAY_NAMES: dict[str, str] = {
    "AAPL":  "Apple Inc.",
    "MSFT":  "Microsoft Corp.",
    "GOOGL": "Alphabet Inc. (Google)",
    "AMZN":  "Amazon.com Inc.",
    "NVDA":  "NVIDIA Corp.",
    "TSLA":  "Tesla Inc.",
    "META":  "Meta Platforms Inc.",
    "NFLX":  "Netflix Inc.",
    "JPM":   "JPMorgan Chase & Co.",
    "V":     "Visa Inc.",
    "DIS":   "The Walt Disney Co.",
    "BA":    "Boeing Co.",
    "AMD":   "Advanced Micro Devices",
    "INTC":  "Intel Corp.",
    "PYPL":  "PayPal Holdings Inc.",
}

CRYPTO_DISPLAY_NAMES: dict[str, str] = {
    "bitcoin":          "Bitcoin",
    "ethereum":         "Ethereum",
    "tether":           "Tether (USDT)",
    "binancecoin":      "BNB",
    "solana":           "Solana",
    "ripple":           "XRP",
    "usd-coin":         "USD Coin (USDC)",
    "cardano":          "Cardano",
    "dogecoin":         "Dogecoin",
    "avalanche-2":      "Avalanche",
    "polkadot":         "Polkadot",
    "chainlink":        "Chainlink",
    "litecoin":         "Litecoin",
    "tron":             "TRON",
    "shiba-inu":        "Shiba Inu",
}


_YAHOO_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json",
}

_COINGECKO_HEADERS = {
    **_YAHOO_HEADERS,
    **({"x-cg-demo-api-key": COINGECKO_API_KEY} if COINGECKO_API_KEY else {}),
}

_API_HEADERS = _YAHOO_HEADERS


def _yahoo_chart(ticker: str, range_str: str = "2d", interval: str = "1d") -> dict:
    url = (
        f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}"
        f"?range={range_str}&interval={interval}"
    )
    resp = http_requests.get(url, headers=_YAHOO_HEADERS, timeout=TIMEOUT)
    resp.raise_for_status()
    return resp.json()


def get_stock_data(ticker: str) -> dict:
    ticker = ticker.upper()
    cache_key = f"stock:{ticker}"
    cached_data, is_stale = get_cached(cache_key)

    if not is_stale and cached_data:
        return cached_data

    try:
        data = _yahoo_chart(ticker, range_str="2d", interval="1d")
        meta = data["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice")
        prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")

        if price is None or prev_close is None:
            raise ValueError(f"Missing price fields for {ticker}")

        change = round(((price - prev_close) / prev_close) * 100, 2)
        display_name = STOCK_DISPLAY_NAMES.get(ticker, ticker)

        result = {
            "name": display_name,
            "symbol": ticker,
            "price": round(price, 2),
            "change": change,
            "asset_type": "stock",
            "source": "live",
        }
        set_cached(cache_key, result)
        return result

    except Exception as e:
        print(f"[market_data] Stock fetch failed for {ticker}: {e}")

    stale = get_stale(cache_key)
    if stale:
        stale_copy = dict(stale)
        stale_copy["source"] = "cache"
        return stale_copy

    return {
        "name": STOCK_DISPLAY_NAMES.get(ticker, ticker),
        "symbol": ticker,
        "price": 0.00,
        "change": 0.00,
        "asset_type": "stock",
        "source": "fallback",
    }


def get_stock_history(ticker: str, period: str = "7d") -> list:
    range_map = {
        "7d":  ("7d",  "1d"),
        "1mo": ("1mo", "1d"),
        "3mo": ("3mo", "1d"),
    }
    range_str, interval = range_map.get(period, ("7d", "1d"))

    try:
        data = _yahoo_chart(ticker.upper(), range_str=range_str, interval=interval)
        result_block = data["chart"]["result"][0]
        timestamps = result_block.get("timestamp", [])
        quote = result_block["indicators"]["quote"][0]
        closes = quote.get("close", [])
        opens  = quote.get("open", [])
        highs  = quote.get("high", [])
        lows   = quote.get("low", [])

        history = []
        for idx, ts in enumerate(timestamps):
            c = closes[idx] if idx < len(closes) else None
            if c is not None:
                date_str = datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")
                history.append({
                    "date":  date_str,
                    "price": round(c, 2),
                    "open":  round(opens[idx], 2) if idx < len(opens) and opens[idx] else round(c, 2),
                    "high":  round(highs[idx], 2) if idx < len(highs) and highs[idx] else round(c, 2),
                    "low":   round(lows[idx], 2)  if idx < len(lows) and lows[idx]   else round(c, 2),
                    "close": round(c, 2),
                })
        return history

    except Exception as e:
        print(f"[market_data] Stock history failed for {ticker}: {e}")
        return []


def search_stock(query: str) -> dict | None:
    try:
        ticker = query.upper().strip()
        data = _yahoo_chart(ticker, range_str="2d", interval="1d")
        meta = data["chart"]["result"][0]["meta"]
        price = meta.get("regularMarketPrice")
        prev_close = meta.get("chartPreviousClose") or meta.get("previousClose")

        if price is None or prev_close is None:
            return None

        change = round(((price - prev_close) / prev_close) * 100, 2)
        display_name = STOCK_DISPLAY_NAMES.get(ticker, ticker)

        return {
            "name": display_name,
            "symbol": ticker,
            "price": round(price, 2),
            "change": change,
            "asset_type": "stock",
            "source": "live",
        }
    except Exception:
        return None


def get_crypto_data(coin_id: str) -> dict:
    cache_key = f"crypto:{coin_id.lower()}"
    cached_data, is_stale = get_cached(cache_key)

    if not is_stale and cached_data:
        return cached_data

    try:
        url = (
            f"{COINGECKO_BASE}/simple/price"
            f"?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
        )
        resp = http_requests.get(url, headers=_COINGECKO_HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        data = resp.json()

        if coin_id not in data:
            raise ValueError(f"Coin ID '{coin_id}' not in response")

        coin = data[coin_id]
        display_name = CRYPTO_DISPLAY_NAMES.get(coin_id.lower(), coin_id.capitalize())

        result = {
            "name": display_name,
            "symbol": coin_id.lower(),
            "price": coin["usd"],
            "change": round(coin.get("usd_24h_change", 0.0), 2),
            "asset_type": "crypto",
            "source": "live",
        }
        set_cached(cache_key, result)
        return result

    except Exception as e:
        print(f"[market_data] Crypto fetch failed for {coin_id}: {e}")

    stale = get_stale(cache_key)
    if stale:
        stale_copy = dict(stale)
        stale_copy["source"] = "cache"
        return stale_copy

    return {
        "name": CRYPTO_DISPLAY_NAMES.get(coin_id.lower(), coin_id.capitalize()),
        "symbol": coin_id.lower(),
        "price": 0.00,
        "change": 0.00,
        "asset_type": "crypto",
        "source": "fallback",
    }


def get_crypto_data_batch(coin_ids: list[str]) -> list[dict]:
    results_map: dict[str, dict] = {}

    uncached_ids: list[str] = []
    for coin_id in coin_ids:
        cid = coin_id.lower()
        cache_key = f"crypto:{cid}"
        cached_data, is_stale = get_cached(cache_key)
        if not is_stale and cached_data:
            results_map[cid] = cached_data
        else:
            uncached_ids.append(cid)

    if uncached_ids:
        try:
            ids_param = ",".join(uncached_ids)
            url = (
                f"{COINGECKO_BASE}/simple/price"
                f"?ids={ids_param}&vs_currencies=usd&include_24hr_change=true"
            )
            resp = http_requests.get(url, headers=_COINGECKO_HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            data = resp.json()

            for cid in uncached_ids:
                if cid in data:
                    coin = data[cid]
                    display_name = CRYPTO_DISPLAY_NAMES.get(cid, cid.capitalize())
                    result = {
                        "name": display_name,
                        "symbol": cid,
                        "price": coin.get("usd", 0.0),
                        "change": round(coin.get("usd_24h_change", 0.0), 2),
                        "asset_type": "crypto",
                        "source": "live",
                    }
                    set_cached(f"crypto:{cid}", result)
                    results_map[cid] = result

        except Exception as e:
            print(f"[market_data] Batch crypto fetch failed: {e}")

    output: list[dict] = []
    for coin_id in coin_ids:
        cid = coin_id.lower()
        if cid in results_map:
            output.append(results_map[cid])
        else:
            stale = get_stale(f"crypto:{cid}")
            if stale:
                stale_copy = dict(stale)
                stale_copy["source"] = "cache"
                output.append(stale_copy)
            else:
                output.append({
                    "name": CRYPTO_DISPLAY_NAMES.get(cid, cid.capitalize()),
                    "symbol": cid,
                    "price": 0.00,
                    "change": 0.00,
                    "asset_type": "crypto",
                    "source": "fallback",
                })

    return output


def get_crypto_history(coin_id: str, days: int = 7) -> list:
    try:
        url = (
            f"{COINGECKO_BASE}/coins/{coin_id}/ohlc"
            f"?vs_currency=usd&days={days}"
        )
        resp = http_requests.get(url, headers=_COINGECKO_HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        ohlc = resp.json()
        history = []
        for row in ohlc:
            if len(row) >= 5:
                ts, o, h, l, c = row[0], row[1], row[2], row[3], row[4]
                history.append({
                    "date":  datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d"),
                    "price": round(c, 2),
                    "open":  round(o, 2),
                    "high":  round(h, 2),
                    "low":   round(l, 2),
                    "close": round(c, 2),
                })
        return history
    except Exception as e:
        print(f"[market_data] Crypto history failed for {coin_id}: {e}")
        try:
            url = (
                f"{COINGECKO_BASE}/coins/{coin_id}/market_chart"
                f"?vs_currency=usd&days={days}&interval=daily"
            )
            resp = http_requests.get(url, headers=_COINGECKO_HEADERS, timeout=TIMEOUT)
            resp.raise_for_status()
            prices = resp.json().get("prices", [])
            return [
                {
                    "date": datetime.utcfromtimestamp(ts / 1000).strftime("%Y-%m-%d"),
                    "price": round(price, 2),
                }
                for ts, price in prices
            ]
        except Exception:
            return []


def search_crypto(query: str) -> list:
    try:
        search_url = f"{COINGECKO_BASE}/search?query={query}"
        resp = http_requests.get(search_url, headers=_COINGECKO_HEADERS, timeout=TIMEOUT)
        resp.raise_for_status()
        coins = resp.json().get("coins", [])[:5]

        if not coins:
            return []

        ids = ",".join(c["id"] for c in coins)
        price_url = (
            f"{COINGECKO_BASE}/simple/price"
            f"?ids={ids}&vs_currencies=usd&include_24hr_change=true"
        )
        price_resp = http_requests.get(price_url, headers=_COINGECKO_HEADERS, timeout=TIMEOUT)
        price_resp.raise_for_status()
        prices = price_resp.json()

        results = []
        for coin in coins:
            cid = coin["id"]
            if cid in prices:
                display_name = coin.get("name", CRYPTO_DISPLAY_NAMES.get(cid, cid.capitalize()))
                results.append({
                    "name": display_name,
                    "symbol": cid.lower(),
                    "price": prices[cid].get("usd", 0.0),
                    "change": round(prices[cid].get("usd_24h_change", 0.0), 2),
                    "asset_type": "crypto",
                    "source": "live",
                })
        return results

    except Exception as e:
        print(f"[market_data] Crypto search failed for '{query}': {e}")
        return []
