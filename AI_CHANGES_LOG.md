# AI Usage Log — MarketFlow Live

This file documents specific instances where I used Claude (Anthropic) to assist with debugging during development.

---

## 1. Streamlit HTML Rendering Bug — dashboard.py

**Problem:** Raw HTML tags like `<div class="card-tooltip">` were appearing visibly on screen under every asset card instead of rendering as hover tooltips.

**What happened:** I originally implemented CSS hover tooltips so that hovering over a stock or crypto card would show a brief description and related news. But in Streamlit, each `st.markdown(unsafe_allow_html=True)` call gets wrapped in its own isolated DOM container. This meant my parent-child CSS `:hover` selectors could never work — the tooltip div and the card div ended up in completely separate containers in the DOM.

**How Claude helped:** I asked Claude to help diagnose why the HTML was rendering as raw text. It identified the Streamlit container isolation as the root cause and suggested replacing the CSS hover approach with `st.expander()` (a native Streamlit widget) for news, and embedding the asset brief directly inside each card's HTML so it stays within the same `st.markdown()` call.

**What I did after:** I reviewed the suggested approach, tested it, and adapted the implementation to fit the rest of my dashboard design. I wrote the ASSET_BRIEFS dictionary and the news matching logic myself to connect the feature to my existing API structure.

---

## 2. Database Migration Issue — app/main.py

**Problem:** The watchlist save feature was silently failing. Users could click the Save button but nothing would happen.

**What happened:** SQLAlchemy's `create_all()` only creates tables that don't exist yet — it never modifies existing tables. As I added new columns to my models during development, the on-disk SQLite database still had the old schema, causing "no such column" errors that weren't visible in the frontend.

**How Claude helped:** I asked Claude to help trace why saves were failing. It identified that the issue was at the database schema level (not the API or frontend) and suggested writing a startup migration function that uses SQLAlchemy's inspector to compare live table columns against the ORM models and run ALTER TABLE for anything missing.

**What I did after:** I implemented the `_migrate_missing_columns()` function in `app/main.py` based on this approach, tested it by checking my local database, and added error logging to the watchlist route so I could trace issues in the future.

---

## 3. Plotly Chart Integration — dashboard.py

**Problem:** The built-in `st.line_chart()` was too basic for an educational platform — no hover tooltips, no labels, no way for students to see exact prices on specific dates.

**How Claude helped:** I asked Claude for guidance on integrating Plotly with Streamlit for interactive charts with hover tooltips. It helped me set up the `go.Figure()` and `go.Scatter()` configuration with proper dark-theme styling, and showed me how to use `hovertemplate` for custom tooltip formatting.

**What I did after:** I used this as a starting point and built out all the chart types myself — the price history chart on Market Overview, and the three comparison charts (bar, line, pie) on the Compare page. I designed the colour scheme and layout to match my existing dashboard theme.

---

## 4. AI Prompt Engineering — Nemotron Instruction Echoing Bug

**Problem:** The AI summary feature was repeating its own instructions back to users instead of giving clean answers. For example, clicking "AI Summary" on Disney would show: *"We need to answer: What is The Walt Disney Co.? Must be 2-3 short sentences, casual, no bullet points... So maybe: Disney is a multinational..."*

**What happened:** NVIDIA's Nemotron 3 Super is a reasoning model that processes instructions as part of its visible chain-of-thought. When I gave it system messages with rules like "reply in 2-3 sentences, no bullet points, no financial advice", it would think through those rules out loud in the response — effectively echoing them back to the user.

**How Claude helped:** I asked Claude to diagnose why the model was repeating instructions. It identified the issue as a known behaviour with reasoning models and suggested switching from rule-based prompts (system messages with "do this, don't do that") to a few-shot example approach — providing example question-and-answer pairs so the model imitates the format instead of reasoning about rules.

**What I did after:** I restructured all three AI endpoints (`/summary`, `/ask`, `/chart`) to use few-shot examples. I wrote the example conversations myself to match the educational tone of my platform, tested them across multiple assets, and verified the model stopped echoing. I also refactored the API call logic into a shared `_call_nemotron()` helper to keep the code clean.
