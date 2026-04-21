# AI Usage Log — MarketFlow Live

This file documents specific instances where I used Claude via the Cmux code terminal to assist with debugging during development.

---

## 1. AI Prompt Engineering — Nemotron Instruction Echoing Bug

**Problem:** The AI summary feature was repeating its own instructions back to users instead of giving clean answers. For example, clicking "AI Summary" on Disney would show: *"We need to answer: What is The Walt Disney Co.? Must be 2-3 short sentences, casual, no bullet points... So maybe: Disney is a multinational..."*

**What happened:** NVIDIA's Nemotron 3 Super is a reasoning model that processes instructions as part of its visible chain-of-thought. When I gave it system messages with rules like "reply in 2-3 sentences, no bullet points, no financial advice", it would think through those rules out loud in the response — effectively echoing them back to the user.

**How Claude via Cmux helped:** I asked Claude via the Cmux code terminal to diagnose why the model was repeating instructions. It identified the issue as a known behaviour with reasoning models and suggested switching from rule-based prompts (system messages with "do this, don't do that") to a few-shot example approach — providing example question-and-answer pairs so the model imitates the format instead of reasoning about rules.

**What I did after:** I restructured all three AI endpoints (`/summary`, `/ask`, `/chart`) to use few-shot examples. I wrote the example conversations myself to match the educational tone of my platform, tested them across multiple assets, and verified the model stopped echoing. I also later switched from Nemotron to OpenAI's GPT-OSS 120B model which handles system messages properly, and implemented a dual-steering approach combining both system messages and few-shot examples for maximum consistency.

---

## 2. Concurrent API Fetching with Rate Limit Avoidance — market_data.py

**Problem:** The dashboard was taking 15–20 seconds to load the Market Overview page because it was making over 30 sequential HTTP requests — one per stock ticker to Yahoo Finance, then one per cryptocurrency to CoinGecko — each waiting for the previous one to finish before starting.

**What happened:** My initial implementation called `get_stock_data()` and `get_crypto_data()` in a simple loop, meaning each API call had to complete (up to 8 seconds timeout) before the next one started. On top of that, CoinGecko's free API has a rate limit of roughly 10–30 requests per minute, so hitting it with 15 individual coin requests in rapid succession would trigger HTTP 429 (Too Many Requests) errors, causing some crypto cards to silently fall back to zero values.

**How Claude via Cmux helped:** I described the slow load times and the intermittent 429 errors. Claude via the Cmux code terminal explained the difference between sequential and concurrent HTTP requests, and suggested two changes: (1) use CoinGecko's batch endpoint (`/simple/price?ids=bitcoin,ethereum,solana,...`) to fetch all crypto prices in a single API call instead of 15 separate ones, and (2) implement a three-tier fallback pattern — try live data first, fall back to stale cache if the API fails, and use zero-value placeholders as a last resort so the dashboard never crashes entirely.

**What I did after:** I wrote `get_crypto_data_batch()` which assembles all uncached coin IDs into one comma-separated API call, then distributes the results back to individual cache entries. I implemented the three-tier fallback (`live → stale cache → zero fallback`) across both stock and crypto functions, and added a TTL-based cache layer (`app/services/cache.py`) with separate fresh and stale thresholds so recently-fetched data serves instantly while older data still acts as a safety net.

---

## 3. Database Migration Issue — app/main.py

**Problem:** The watchlist save feature was silently failing. Users could click the Save button but nothing would happen.

**What happened:** SQLAlchemy's `create_all()` only creates tables that don't exist yet — it never modifies existing tables. As I added new columns to my models during development, the on-disk SQLite database still had the old schema, causing "no such column" errors that weren't visible in the frontend.

**How Claude via Cmux helped:** I asked Claude via the Cmux code terminal to help trace why saves were failing. It identified that the issue was at the database schema level (not the API or frontend) and suggested writing a startup migration function that uses SQLAlchemy's inspector to compare live table columns against the ORM models and run ALTER TABLE for anything missing.

**What I did after:** I implemented the `_migrate_missing_columns()` function in `app/main.py` based on this approach, tested it by checking my local database, and added error logging to the watchlist route so I could trace issues in the future.
