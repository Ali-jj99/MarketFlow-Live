"""
MarketFlow Live — Streamlit Frontend (dashboard.py)

I built this as the main user interface for MarketFlow Live. It connects to
the FastAPI backend to fetch live market data, news, and manage watchlists.
I used Streamlit for the frontend, Plotly for interactive charts, and custom
CSS for the dark financial-dashboard theme.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from requests.exceptions import RequestException

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app.services.education import GLOSSARY, TIPS, LEARN_SECTIONS


# I implemented these brief descriptions so users can see what each asset is
# at a glance — important for the educational goal of the platform.
ASSET_BRIEFS: dict[str, str] = {
    "AAPL":  "Apple — Consumer electronics giant. Makes iPhones, Macs, and services.",
    "MSFT":  "Microsoft — Software & cloud leader. Azure, Office 365, Windows.",
    "GOOGL": "Alphabet (Google) — Search, ads, YouTube, and cloud computing.",
    "AMZN":  "Amazon — E-commerce and AWS cloud. Largest online retailer.",
    "NVDA":  "NVIDIA — AI chip leader. GPUs for gaming, data centres, and AI.",
    "TSLA":  "Tesla — Electric vehicles and clean energy. High-growth, high-volatility.",
    "META":  "Meta (Facebook) — Social media and metaverse. Instagram, WhatsApp.",
    "NFLX":  "Netflix — Streaming entertainment. Global subscriber base.",
    "JPM":   "JPMorgan Chase — Largest US bank. Investment banking and retail.",
    "V":     "Visa — Global payments network. Processes billions of transactions.",
    "DIS":   "Disney — Entertainment conglomerate. Theme parks, streaming (Disney+).",
    "BA":    "Boeing — Aerospace manufacturer. Commercial and defence aircraft.",
    "AMD":   "AMD — Semiconductor company. CPUs and GPUs competing with Intel/NVIDIA.",
    "INTC":  "Intel — Legacy chip maker. CPUs for PCs and servers.",
    "PYPL":  "PayPal — Digital payments platform. Online transactions worldwide.",
    "bitcoin":     "Bitcoin (BTC) — The original cryptocurrency. Digital gold, store of value.",
    "ethereum":    "Ethereum (ETH) — Smart contract platform. Powers DeFi and NFTs.",
    "tether":      "Tether (USDT) — Stablecoin pegged to $1. Safe haven in crypto.",
    "binancecoin": "BNB — Binance exchange token. Used for trading fee discounts.",
    "solana":      "Solana (SOL) — Fast, low-cost blockchain. Competes with Ethereum.",
    "ripple":      "XRP — Cross-border payments. Used by financial institutions.",
    "usd-coin":    "USDC — Stablecoin pegged to $1. Backed by regulated reserves.",
    "cardano":     "Cardano (ADA) — Research-driven blockchain. Proof-of-stake.",
    "dogecoin":    "Dogecoin (DOGE) — Meme coin turned mainstream. Community-driven.",
    "avalanche-2": "Avalanche (AVAX) — Fast smart contract platform. Sub-second finality.",
    "polkadot":    "Polkadot (DOT) — Multi-chain network. Connects blockchains together.",
    "chainlink":   "Chainlink (LINK) — Oracle network. Feeds real-world data to blockchains.",
    "litecoin":    "Litecoin (LTC) — Early Bitcoin alternative. Faster, cheaper transactions.",
    "tron":        "TRON (TRX) — Content-sharing blockchain. High throughput.",
    "shiba-inu":   "Shiba Inu (SHIB) — Meme token. Community-driven, high volatility.",
}


# I wrote a shared Plotly layout so every chart matches the dark theme.
_PLOTLY_LAYOUT = dict(
    paper_bgcolor="#0b0e11",
    plot_bgcolor="#1e2329",
    font=dict(color="#eaecef", size=12),
    xaxis=dict(gridcolor="#2b3139", linecolor="#2b3139",
               tickfont=dict(color="#848e9c")),
    yaxis=dict(gridcolor="#2b3139", linecolor="#2b3139",
               tickfont=dict(color="#848e9c"), tickprefix="$"),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#eaecef", size=11)),
    margin=dict(l=50, r=20, t=40, b=40),
    hovermode="x unified",
)


st.set_page_config(
    page_title="MarketFlow Live",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# I wrote custom CSS for a dark financial-dashboard theme because Streamlit's
# default light styling didn't suit the professional look I wanted.
st.markdown("""
<style>
/* I updated the colour scheme to reduce blue dominance and make the platform
   more visually engaging for young users. Inspired by Binance (amber accents)
   and Bloomberg Terminal (dark, professional backgrounds). */
[data-testid="stAppViewContainer"] { background-color: #0b0e11; color: #eaecef; }
[data-testid="stSidebar"]           { background-color: #12161c; border-right: 1px solid #2b3139; }
[data-testid="stHeader"]            { background: transparent; }

.hero-banner {
    background: linear-gradient(135deg, #1e2329 0%, #0b0e11 100%);
    border: 1px solid #2b3139; border-radius: 12px;
    padding: 28px 36px; margin-bottom: 24px;
    display: flex; align-items: center; justify-content: space-between;
}
.hero-title   { font-size: 2rem; font-weight: 700; color: #f0b90b; margin: 0; }
.hero-tagline { font-size: 0.95rem; color: #848e9c; margin-top: 4px; }
.hero-time    { font-size: 0.85rem; color: #5e6673; text-align: right; }

.section-header {
    font-size: 1rem; font-weight: 600; color: #f0b90b;
    text-transform: uppercase; letter-spacing: 0.08em;
    margin: 24px 0 12px 0; padding-bottom: 8px;
    border-bottom: 1px solid #2b3139;
}

.asset-card {
    background: #1e2329; border: 1px solid #2b3139;
    border-radius: 10px; padding: 18px 20px; margin-bottom: 4px;
    transition: border-color 0.2s;
}
.asset-card:hover { border-color: #f0b90b; }
.asset-name  { font-size: 0.78rem; color: #848e9c; font-weight: 500;
               text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 2px; }
.asset-ticker { font-size: 0.72rem; color: #5e6673; margin-bottom: 6px; }
.asset-price { font-size: 1.45rem; font-weight: 700; color: #eaecef; margin-bottom: 4px; }
.change-pos  { font-size: 0.85rem; font-weight: 600; color: #0ecb81; }
.change-neg  { font-size: 0.85rem; font-weight: 600; color: #f6465d; }
.change-neu  { font-size: 0.85rem; font-weight: 600; color: #5e6673; }
.asset-brief { font-size: 0.72rem; color: #5e6673; margin-top: 6px;
               line-height: 1.4; font-style: italic; }
.badge-live     { display:inline-block; font-size:0.68rem; padding:2px 7px;
                  border-radius:99px; background:#0d2912; color:#0ecb81; margin-top:6px; }
.badge-cache    { display:inline-block; font-size:0.68rem; padding:2px 7px;
                  border-radius:99px; background:#3d2e08; color:#f0b90b; margin-top:6px; }
.badge-fallback { display:inline-block; font-size:0.68rem; padding:2px 7px;
                  border-radius:99px; background:#2d1519; color:#f6465d; margin-top:6px; }

.auth-card {
    background: #1e2329; border: 1px solid #2b3139;
    border-radius: 12px; padding: 28px 32px; margin-bottom: 16px;
}
.auth-title    { font-size: 1.4rem; font-weight: 700; color: #eaecef; margin-bottom: 4px; }
.auth-subtitle { font-size: 0.88rem; color: #848e9c; }

.empty-card {
    background: #1e2329; border: 1px dashed #3b4450;
    border-radius: 12px; padding: 48px 36px; text-align: center;
}
.empty-icon  { font-size: 2.5rem; margin-bottom: 12px; }
.empty-title { font-size: 1.2rem; font-weight: 600; color: #eaecef; margin-bottom: 8px; }
.empty-desc  { font-size: 0.88rem; color: #5e6673; line-height: 1.6;
               max-width: 400px; margin: 0 auto; }

.sidebar-brand       { padding: 16px 0 20px 0; border-bottom: 1px solid #2b3139; margin-bottom: 16px; }
.sidebar-brand-title { font-size: 1.1rem; font-weight: 700; color: #f0b90b; }
.sidebar-brand-sub   { font-size: 0.75rem; color: #5e6673; margin-top: 2px; }
.sidebar-user-badge  { background: #1e2329; border: 1px solid #2b3139; border-radius: 8px;
                       padding: 10px 14px; margin-bottom: 12px;
                       font-size: 0.8rem; color: #0ecb81; word-break: break-all; }
.divider { border: none; border-top: 1px solid #2b3139; margin: 20px 0; }
[data-testid="stButton"] > button { border-radius: 8px; font-weight: 500; }

/* Sidebar quick-info widgets */
.sb-widget {
    background: #1e2329; border: 1px solid #2b3139; border-radius: 10px;
    padding: 14px 16px; margin-bottom: 12px;
}
.sb-widget-title { font-size: 0.7rem; font-weight: 600; color: #f0b90b;
                   text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 8px; }
.sb-widget-row { display: flex; justify-content: space-between; align-items: center;
                 padding: 4px 0; }
.sb-widget-label { font-size: 0.75rem; color: #848e9c; }
.sb-widget-value { font-size: 0.75rem; font-weight: 600; color: #eaecef; }
.sb-widget-value.green { color: #0ecb81; }
.sb-widget-value.red   { color: #f6465d; }
.sb-tip {
    background: #1e2329; border-left: 3px solid #f0b90b;
    border-radius: 0 8px 8px 0; padding: 12px 14px; margin-bottom: 12px;
}
.sb-tip-title { font-size: 0.7rem; font-weight: 600; color: #f0b90b;
                text-transform: uppercase; margin-bottom: 4px; }
.sb-tip-text  { font-size: 0.74rem; color: #848e9c; line-height: 1.5; }

.news-card {
    background: #1e2329; border: 1px solid #2b3139; border-radius: 8px;
    padding: 14px 16px; margin-bottom: 10px;
}
.news-card:hover { border-color: #f0b90b; }
.news-title { font-size: 0.82rem; font-weight: 600; color: #eaecef;
              line-height: 1.4; margin-bottom: 6px; }
.news-meta  { font-size: 0.7rem; color: #5e6673; margin-bottom: 4px; }
.news-summary { font-size: 0.75rem; color: #848e9c; line-height: 1.4; }
.sentiment-bullish { display:inline-block; font-size:0.65rem; padding:2px 8px;
                     border-radius:99px; background:#0d2912; color:#0ecb81;
                     font-weight:600; margin-right:6px; }
.sentiment-bearish { display:inline-block; font-size:0.65rem; padding:2px 8px;
                     border-radius:99px; background:#2d1519; color:#f6465d;
                     font-weight:600; margin-right:6px; }
.sentiment-neutral { display:inline-block; font-size:0.65rem; padding:2px 8px;
                     border-radius:99px; background:#1e2329; color:#848e9c;
                     font-weight:600; margin-right:6px; }

.tip-box {
    background: #1e2329; border: 1px solid #2b3139; border-radius: 10px;
    padding: 14px 18px; margin: 12px 0 20px 0;
}
.tip-label   { font-size: 0.72rem; font-weight: 600; color: #f0b90b;
               text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 4px; }
.tip-content { font-size: 0.82rem; color: #848e9c; line-height: 1.55; }

.guide-card {
    background: linear-gradient(135deg, #1e2329 0%, #12161c 100%);
    border: 1px solid #2b3139; border-radius: 12px;
    padding: 22px 26px; margin-bottom: 14px;
}
.guide-step-num  { display:inline-block; width:28px; height:28px; line-height:28px;
                   text-align:center; border-radius:50%; background:#f0b90b;
                   color:#0b0e11; font-size:0.8rem; font-weight:700; margin-right:10px; }
.guide-step-text { font-size: 0.88rem; color: #c0c8dc; line-height: 1.6; }
.guide-title     { font-size: 1.1rem; font-weight: 700; color: #eaecef; margin-bottom: 14px; }
.wl-saved-badge { display:inline-block; font-size:0.72rem; padding:4px 12px;
                  border-radius:99px; background:#0d2912; color:#0ecb81; font-weight:600; }
.wl-status-card {
    background: #1e2329; border: 1px solid #2b3139; border-radius: 10px;
    padding: 16px 20px; margin-bottom: 16px; text-align: center;
}
.wl-status-count { font-size: 1.8rem; font-weight: 700; color: #f0b90b; }
.wl-status-label { font-size: 0.8rem; color: #848e9c; margin-top: 2px; }

div[data-testid="column"]:has(button[key*="save_"]) button,
button[key*="save_"] {
    background: #0d2912 !important; color: #0ecb81 !important;
    border: 1px solid #14532d !important;
}
div[data-testid="column"]:has(button[key*="save_"]) button:hover,
button[key*="save_"]:hover {
    background: #14532d !important; color: #fff !important;
}
div[data-testid="column"]:has(button[key*="del_"]) button,
button[key*="del_"] {
    background: #2d1519 !important; color: #f6465d !important;
    border: 1px solid #7f1d1d !important;
}
div[data-testid="column"]:has(button[key*="del_"]) button:hover,
button[key*="del_"]:hover {
    background: #7f1d1d !important; color: #fff !important;
}
div[data-testid="column"]:has(button[key*="cmp_"]) button,
button[key*="cmp_"] {
    background: #1e2329 !important; color: #f0b90b !important;
    border: 1px solid #3d2e08 !important;
}
div[data-testid="column"]:has(button[key*="cmp_"]) button:hover,
button[key*="cmp_"]:hover {
    background: #3d2e08 !important; color: #fff !important;
}
/* AI Summary button styling — amber accent to stand out */
button[key*="ai_"] {
    background: #3d2e08 !important; color: #f0b90b !important;
    border: 1px solid #f0b90b !important;
}
button[key*="ai_"]:hover {
    background: #f0b90b !important; color: #0b0e11 !important;
}
button[key*="chart_ai_"] {
    background: #3d2e08 !important; color: #f0b90b !important;
    border: 1px solid #f0b90b !important;
}
button[key*="chart_ai_"]:hover {
    background: #f0b90b !important; color: #0b0e11 !important;
}

.howto-step {
    display: flex; align-items: flex-start; gap: 14px;
    background: #1e2329; border: 1px solid #2b3139; border-radius: 10px;
    padding: 18px 22px; margin-bottom: 12px;
}
.howto-step:hover { border-color: #f0b90b; }
.howto-num  { flex-shrink:0; width:32px; height:32px; line-height:32px;
              text-align:center; border-radius:50%; background:#f0b90b;
              color:#0b0e11; font-size:0.85rem; font-weight:700; }
.howto-body { flex: 1; }
.howto-title { font-size: 0.95rem; font-weight: 600; color: #eaecef; margin-bottom: 4px; }
.howto-desc  { font-size: 0.82rem; color: #848e9c; line-height: 1.55; }

.learn-hero {
    background: linear-gradient(135deg, #1e2329 0%, #12161c 70%);
    border: 1px solid #2b3139; border-radius: 14px;
    padding: 36px 40px; margin-bottom: 28px; text-align: center;
}
.learn-hero-title { font-size: 1.6rem; font-weight: 700; color: #f0b90b; margin-bottom: 8px; }
.learn-hero-sub   { font-size: 0.95rem; color: #848e9c; line-height: 1.6;
                    max-width: 600px; margin: 0 auto; }
.learn-flow-section {
    display: flex; gap: 28px; margin-bottom: 32px; align-items: flex-start;
}
.learn-flow-section.reverse { flex-direction: row-reverse; }
.learn-flow-visual {
    flex-shrink: 0; width: 80px; height: 80px; border-radius: 16px;
    display: flex; align-items: center; justify-content: center; font-size: 2.2rem;
}
.learn-flow-visual.blue   { background: #1e2329; border: 1px solid #2b3139; }
.learn-flow-visual.green  { background: #0d2912; border: 1px solid #14532d; }
.learn-flow-visual.red    { background: #2d1519; border: 1px solid #7f1d1d; }
.learn-flow-visual.purple { background: #1a0d37; border: 1px solid #4c1d95; }
.learn-flow-content { flex: 1; }
.learn-flow-title   { font-size: 1.1rem; font-weight: 700; color: #eaecef; margin-bottom: 6px; }
.learn-flow-body    { font-size: 0.86rem; color: #c0c8dc; line-height: 1.7; }
.learn-flow-callout {
    background: #1e2329; border-left: 3px solid #f0b90b;
    border-radius: 0 8px 8px 0; padding: 12px 16px; margin-top: 10px;
    font-size: 0.82rem; color: #848e9c; line-height: 1.5;
}
.learn-divider { border: none; border-top: 1px solid #2b3139; margin: 12px 0 28px 0; }

/* Market Mood indicator */
.mood-bar {
    background: #1e2329; border: 1px solid #2b3139; border-radius: 12px;
    padding: 18px 24px; margin-bottom: 20px;
    display: flex; align-items: center; gap: 20px;
}
.mood-emoji { font-size: 2rem; }
.mood-info  { flex: 1; }
.mood-label { font-size: 0.7rem; font-weight: 600; color: #848e9c;
              text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 2px; }
.mood-title { font-size: 1.1rem; font-weight: 700; margin-bottom: 4px; }
.mood-desc  { font-size: 0.78rem; color: #848e9c; line-height: 1.4; }
.mood-meter { height: 8px; border-radius: 4px; background: #2b3139; overflow: hidden;
              margin-top: 8px; }
.mood-meter-fill { height: 100%; border-radius: 4px; transition: width 0.3s; }

/* Portfolio Simulator */
.sim-result {
    background: #1e2329; border: 1px solid #2b3139; border-radius: 12px;
    padding: 20px 24px; margin-top: 16px;
}
.sim-result-title { font-size: 0.72rem; font-weight: 600; color: #f0b90b;
                    text-transform: uppercase; letter-spacing: 0.06em; margin-bottom: 12px; }
.sim-row { display: flex; justify-content: space-between; padding: 6px 0;
           border-bottom: 1px solid #2b3139; }
.sim-row:last-child { border-bottom: none; }
.sim-row-label { font-size: 0.82rem; color: #848e9c; }
.sim-row-value { font-size: 0.82rem; font-weight: 600; color: #eaecef; }
.sim-row-value.profit { color: #0ecb81; }
.sim-row-value.loss   { color: #f6465d; }
</style>
""", unsafe_allow_html=True)


# I made the backend URL configurable so the frontend works both locally
# and when hosted on Streamlit Cloud. Streamlit Cloud uses st.secrets (TOML),
# while local development uses environment variables or the default.
def _get_backend_url():
    try:
        if "BACKEND_URL" in st.secrets:
            return st.secrets["BACKEND_URL"]
    except Exception:
        pass
    return os.environ.get("BACKEND_URL", "http://127.0.0.1:8000")

BACKEND_URL     = _get_backend_url()
REQUEST_TIMEOUT = 10

PUBLIC_PAGES  = ["Login", "Register", "Market Overview (Guest)", "Learn"]
PRIVATE_PAGES = ["Market Overview", "Search", "My Watchlist", "Compare", "Learn"]


# I used session_state to persist data across Streamlit reruns because
# Streamlit re-executes the entire script on every user interaction.
def _init_state():
    defaults = {
        "user_email":        None,
        "user_id":           None,
        "page":              "Login",
        "page_selector":     "Login",
        "pending_page":      None,
        "register_success":  False,
        "login_error":       None,
        "search_results":    [],
        "compare_selection": [],   # list of {symbol, name, asset_type}
        "watchlist":         [],   # cached watchlist rows from backend
        "wl_loaded":         False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


_init_state()


# Streamlit renders text between $ signs as LaTeX math, which breaks
# AI responses containing dollar amounts like "$259.48". This helper
# escapes dollar signs so they display as plain text.
def _escape_ai(text: str) -> str:
    return text.replace("$", "&#36;")


def _apply_pending_page():
    if st.session_state["pending_page"]:
        t = st.session_state["pending_page"]
        st.session_state["page"] = t
        st.session_state["page_selector"] = t
        st.session_state["pending_page"] = None


_apply_pending_page()


def api_get(path: str):
    """Send a GET request to the FastAPI backend."""
    try:
        r = requests.get(f"{BACKEND_URL}{path}", timeout=REQUEST_TIMEOUT)
        return r, None
    except RequestException:
        return None, "Cannot reach the backend server."


def api_post(path: str, payload: dict, timeout: int = None):
    """Send a POST request to the FastAPI backend."""
    try:
        r = requests.post(f"{BACKEND_URL}{path}", json=payload,
                          timeout=timeout or REQUEST_TIMEOUT)
        return r, None
    except RequestException:
        return None, "Cannot reach the backend server."


def api_delete(path: str):
    """Send a DELETE request to the FastAPI backend."""
    try:
        r = requests.delete(f"{BACKEND_URL}{path}", timeout=REQUEST_TIMEOUT)
        return r, None
    except RequestException:
        return None, "Cannot reach the backend server."


def _sync_from_sidebar():
    st.session_state["page"] = st.session_state["page_selector"]


def set_page(target: str):
    st.session_state["pending_page"] = target


def logout():
    for k in ("user_email", "user_id", "login_error", "pending_page",
              "search_results", "compare_selection", "watchlist", "wl_loaded"):
        if isinstance(st.session_state.get(k), list):
            st.session_state[k] = []
        elif isinstance(st.session_state.get(k), bool):
            st.session_state[k] = False
        else:
            st.session_state[k] = None
    st.session_state["page"] = "Login"
    st.session_state["page_selector"] = "Login"


def render_tip(tip_key: str):
    tip_text = TIPS.get(tip_key, "")
    if tip_text:
        st.markdown(f"""
        <div class="tip-box">
            <div class="tip-label">💡 Did you know?</div>
            <div class="tip-content">{tip_text}</div>
        </div>
        """, unsafe_allow_html=True)


def _source_badge(source: str) -> str:
    if source == "live":
        return '<span class="badge-live">● Live</span>'
    if source == "cache":
        return '<span class="badge-cache">⚠ Cached data</span>'
    return '<span class="badge-fallback">✕ API unavailable — fallback</span>'


def _match_news_for_asset(symbol: str, name: str, articles: list) -> list:
    """I wrote this to match news articles to a specific asset by checking
    if the title mentions the symbol or company name."""
    matched = []
    sym_up = symbol.upper()
    name_lower = name.lower()
    keywords = [w.lower() for w in name.replace("Inc.", "").replace("Corp.", "").split()
                if len(w) > 2][:2]
    for art in articles:
        title = art.get("title", "")
        title_lower = title.lower()
        if (sym_up in title
                or name_lower in title_lower
                or any(kw in title_lower for kw in keywords)):
            matched.append(art)
            if len(matched) >= 2:
                break
    return matched


def render_asset_card(item: dict, show_save_btn: bool = False,
                      wl_symbols: set | None = None,
                      news_articles: list | None = None):
    """I implemented this as the core reusable card component for displaying
    any stock or crypto with price, change, brief, and expandable news."""
    price   = item.get("price") or 0.0
    change  = item.get("change") or 0.0
    name    = item.get("name", "N/A")
    symbol  = item.get("symbol", "")
    atype   = item.get("asset_type", "")
    source  = item.get("source", "live")

    arrow  = "▲" if change > 0 else ("▼" if change < 0 else "─")
    ch_cls = "change-pos" if change > 0 else ("change-neg" if change < 0 else "change-neu")

    brief = ASSET_BRIEFS.get(symbol.upper(), ASSET_BRIEFS.get(symbol.lower(), ""))
    brief_html = f'<div class="asset-brief">{brief}</div>' if brief else ""

    st.markdown(f"""
    <div class="asset-card">
        <div class="asset-name">{name}</div>
        <div class="asset-ticker">{symbol.upper()} · {atype.capitalize()}</div>
        <div class="asset-price">${price:,.2f}</div>
        <div class="{ch_cls}">{arrow} {abs(change):.2f}%</div>
        {_source_badge(source)}
        {brief_html}
    </div>
    """, unsafe_allow_html=True)

    if news_articles:
        matched = _match_news_for_asset(symbol, name, news_articles)
        if matched:
            with st.expander(f"📰 News for {symbol.upper()}"):
                for art in matched:
                    sentiment = art.get("sentiment", "Neutral")
                    st.markdown(
                        f"**{sentiment}** — {art.get('title', '')[:100]}",
                    )
                    if art.get("url"):
                        st.caption(f"[Read article →]({art['url']})")

    # I added this AI section so users can get a beginner-friendly explanation
    # of any asset, or ask their own questions — powered by NVIDIA Nemotron
    # via OpenRouter. I did this because the educational goal of the platform
    # means users should be able to learn about assets interactively.
    ai_key = f"ai_{symbol}_{atype}"
    if st.button("AI Summary", key=ai_key, use_container_width=True):
        with st.spinner("Getting AI summary..."):
            ai_resp, ai_err = api_get(
                f"/api/ai/summary?symbol={symbol}&name={name}"
                f"&asset_type={atype}&price={price}&change={change}"
            )
        if ai_err:
            st.warning("AI summary is temporarily unavailable.")
        elif ai_resp.status_code == 200:
            st.session_state[f"ai_result_{ai_key}"] = ai_resp.json().get("summary", "")
        elif ai_resp.status_code == 503:
            st.warning("AI service is not configured. Add your OpenRouter API key to .env.")
        else:
            st.warning("Could not generate summary right now. Please try again.")

    if st.session_state.get(f"ai_result_{ai_key}"):
        st.markdown(
            f'<div class="tip-box">'
            f'<div class="tip-label">AI Summary — {symbol.upper()}</div>'
            f'<div class="tip-content">{_escape_ai(st.session_state[f"ai_result_{ai_key}"])}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    # I implemented this "Ask AI" text input so users can type their own
    # questions about the asset — e.g. "what does this stock do" or
    # "is this crypto safe for beginners". This makes the platform more
    # interactive and educational rather than just showing static data.
    ask_key = f"ask_{symbol}_{atype}"
    user_q = st.text_input(
        "Ask AI about this asset",
        placeholder=f"e.g. What does {symbol.upper()} do?",
        key=ask_key,
        label_visibility="collapsed",
    )
    if user_q and st.button("Ask", key=f"askbtn_{symbol}_{atype}", use_container_width=True):
        with st.spinner("Thinking..."):
            ai_resp, ai_err = api_get(
                f"/api/ai/ask?symbol={symbol}&name={name}"
                f"&asset_type={atype}&price={price}&change={change}"
                f"&question={user_q}"
            )
        if ai_err:
            st.warning("AI is temporarily unavailable.")
        elif ai_resp.status_code == 200:
            st.session_state[f"ai_answer_{ask_key}"] = ai_resp.json().get("answer", "")
        else:
            st.warning("Could not get an answer right now. Please try again.")

    if st.session_state.get(f"ai_answer_{ask_key}"):
        st.markdown(
            f'<div class="tip-box">'
            f'<div class="tip-label">AI Answer — {symbol.upper()}</div>'
            f'<div class="tip-content">{_escape_ai(st.session_state[f"ai_answer_{ask_key}"])}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

    if show_save_btn:
        uid = st.session_state.get("user_id")
        if not uid:
            st.caption("🔒 Log in to save assets to your watchlist")
        else:
            already = wl_symbols and symbol.lower() in wl_symbols
            if already:
                st.markdown(
                    '<span class="wl-saved-badge">✓ In your watchlist</span>',
                    unsafe_allow_html=True,
                )
            else:
                if st.button(f"＋ Save  {symbol.upper()}", key=f"save_{symbol}_{atype}"):
                    resp, err = api_post("/api/watchlist", {
                        "symbol": symbol,
                        "name": name,
                        "asset_type": atype,
                        "user_id": uid,
                    })
                    if err:
                        st.error(err)
                    elif resp.status_code in (200, 201):
                        st.success(f"✓ {name} added to watchlist!")
                        st.session_state["watchlist"] = []
                        st.session_state["wl_loaded"] = False
                        st.rerun()
                    elif resp.status_code == 409:
                        st.info("Already in your watchlist.")
                    else:
                        try:
                            detail = resp.json().get("detail", "Unknown error")
                        except Exception:
                            detail = f"Server returned status {resp.status_code}"
                        st.error(f"Could not save: {detail}")


def _load_watchlist():
    uid = st.session_state.get("user_id")
    if not uid:
        return
    resp, err = api_get(f"/api/watchlist/{uid}")
    if not err and resp.status_code == 200:
        st.session_state["watchlist"] = resp.json()
        st.session_state["wl_loaded"] = True


def render_news_sidebar():
    st.markdown('<div class="section-header">📰 Market News</div>', unsafe_allow_html=True)
    render_tip("news_sentiment")

    resp, err = api_get("/api/news?limit=8")
    if err or resp is None:
        st.caption("News is temporarily unavailable.")
        return

    data = resp.json()
    if not data.get("api_configured"):
        st.markdown("""
        <div class="news-card">
            <div class="news-title">News API not configured</div>
            <div class="news-summary">Add your Alpha Vantage API key to the .env
            file to enable live financial news with sentiment analysis.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    articles = data.get("articles", [])
    if not articles:
        st.caption("No recent news available.")
        return

    for article in articles:
        sentiment = article.get("sentiment", "Neutral")
        s_class = f"sentiment-{sentiment.lower()}"
        st.markdown(f"""
        <div class="news-card">
            <div class="news-meta">
                <span class="{s_class}">{sentiment}</span> {article.get("source", "")}
            </div>
            <div class="news-title">{article.get("title", "")}</div>
            <div class="news-summary">{article.get("summary", "")}</div>
        </div>
        """, unsafe_allow_html=True)
        if article.get("url"):
            st.markdown(f"[Read full article →]({article['url']})")


with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
        <div class="sidebar-brand-title">📈 MarketFlow Live</div>
        <div class="sidebar-brand-sub">Real-time market insights</div>
    </div>
    """, unsafe_allow_html=True)

    if st.session_state["user_email"]:
        st.markdown(
            f'<div class="sidebar-user-badge">● &nbsp;{st.session_state["user_email"]}</div>',
            unsafe_allow_html=True,
        )
        st.button("Sign Out", on_click=logout, use_container_width=True)
        st.markdown('<hr class="divider">', unsafe_allow_html=True)

        if st.session_state["page"] not in PRIVATE_PAGES:
            st.session_state["page"] = "Market Overview"
            st.session_state["page_selector"] = "Market Overview"

        st.radio("Navigation", PRIVATE_PAGES, key="page_selector",
                 on_change=_sync_from_sidebar)
    else:
        if st.session_state["page"] not in PUBLIC_PAGES:
            st.session_state["page"] = "Login"
            st.session_state["page_selector"] = "Login"

        st.radio("Navigation", PUBLIC_PAGES, key="page_selector",
                 on_change=_sync_from_sidebar)

    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    # I added sidebar widgets to fill the empty space below navigation
    # and give users useful at-a-glance information.
    if st.session_state.get("user_email"):
        import random
        sidebar_tips = [
            "Green percentages mean the asset gained value. Red means it lost value. This is measured over the last 24 hours.",
            "A watchlist lets you track assets you're interested in without having to search for them each time.",
            "The Compare feature lets you see two or more assets side by side — great for spotting which one performed better.",
            "Candlestick charts show four prices per day: where the price opened, the highest it reached, the lowest, and where it closed.",
            "Market prices change because of supply and demand — if more people want to buy than sell, the price goes up.",
            "Crypto markets run 24/7, but stock markets only trade on weekdays during set hours (9:30 AM - 4:00 PM ET).",
            "AI summaries on this platform are educational — they explain what an asset is, not whether you should invest.",
            "A stock represents a small piece of ownership in a company. When the company does well, the stock price usually rises.",
        ]
        tip = random.choice(sidebar_tips)
        st.markdown(f"""
        <div class="sb-tip">
            <div class="sb-tip-title">Quick Tip</div>
            <div class="sb-tip-text">{tip}</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="sb-widget">
            <div class="sb-widget-title">Platform Features</div>
            <div class="sb-widget-row">
                <span class="sb-widget-label">Live Stocks</span>
                <span class="sb-widget-value">15 assets</span>
            </div>
            <div class="sb-widget-row">
                <span class="sb-widget-label">Live Crypto</span>
                <span class="sb-widget-value">15 coins</span>
            </div>
            <div class="sb-widget-row">
                <span class="sb-widget-label">AI Assistant</span>
                <span class="sb-widget-value green">Active</span>
            </div>
            <div class="sb-widget-row">
                <span class="sb-widget-label">Market News</span>
                <span class="sb-widget-value green">Live</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown(
        '<p style="font-size:0.72rem;color:#5e6673;text-align:center;">'
        'Data: CoinGecko, Yahoo Finance &amp; Alpha Vantage</p>',
        unsafe_allow_html=True,
    )


_now = datetime.now().strftime("%A, %d %b %Y  ·  %H:%M")
st.markdown(f"""
<div class="hero-banner">
    <div>
        <div class="hero-title">📈 MarketFlow Live</div>
        <div class="hero-tagline">Simplified market data for students and young investors</div>
    </div>
    <div class="hero-time">🕐 {_now}</div>
</div>
""", unsafe_allow_html=True)


def render_market_overview():
    main_col, news_col = st.columns([3, 1])

    with main_col:
        c1, c2, c3 = st.columns([4, 2, 1])
        with c1:
            st.markdown("#### Live Market Data")
        with c2:
            period = st.selectbox("Chart period", ["7d", "1mo", "3mo"],
                                  label_visibility="collapsed", key="ov_period")
        with c3:
            if st.button("🔄 Refresh", use_container_width=True):
                st.rerun()

        with st.spinner("Fetching live prices..."):
            resp, err = api_get("/api/market/overview")

        if err:
            st.error(f"⚠️ {err}")
            return
        if resp.status_code != 200:
            st.error("⚠️ Failed to fetch market data.")
            return

        data = resp.json()

        # I built this Market Mood indicator to give beginners an instant
        # sense of whether the market is having a good or bad day — before
        # they even look at individual prices. No other student aggregator
        # does this, and it reinforces the educational goal.
        all_items = data.get("stocks", []) + data.get("crypto", [])
        ups   = sum(1 for a in all_items if (a.get("change") or 0) > 0)
        downs = sum(1 for a in all_items if (a.get("change") or 0) < 0)
        total = len(all_items) or 1
        pct_up = int((ups / total) * 100)

        if pct_up >= 75:
            mood_label, mood_color, mood_emoji = "Bullish", "#0ecb81", "🟢"
            mood_desc = f"{ups} out of {total} assets are up today — the market is looking strong."
        elif pct_up >= 50:
            mood_label, mood_color, mood_emoji = "Mostly Bullish", "#0ecb81", "🟡"
            mood_desc = f"{ups} assets up, {downs} down — overall a positive day with some mixed signals."
        elif pct_up >= 25:
            mood_label, mood_color, mood_emoji = "Mostly Bearish", "#f6465d", "🟠"
            mood_desc = f"Only {ups} assets are up while {downs} are down — caution in the market today."
        else:
            mood_label, mood_color, mood_emoji = "Bearish", "#f6465d", "🔴"
            mood_desc = f"{downs} out of {total} assets are down today — a tough day for the markets."

        st.markdown(f"""
        <div class="mood-bar">
            <div class="mood-emoji">{mood_emoji}</div>
            <div class="mood-info">
                <div class="mood-label">Market Mood</div>
                <div class="mood-title" style="color:{mood_color};">{mood_label}</div>
                <div class="mood-desc">{mood_desc}</div>
                <div class="mood-meter">
                    <div class="mood-meter-fill" style="width:{pct_up}%; background:{mood_color};"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        _ov_articles: list = []
        try:
            news_resp, news_err = api_get("/api/news?limit=20")
            if not news_err and news_resp.status_code == 200:
                _ov_articles = news_resp.json().get("articles", [])
        except Exception:
            pass

        wl_symbols: set = set()
        if st.session_state.get("user_id"):
            if not st.session_state["wl_loaded"]:
                _load_watchlist()
            wl_symbols = {w["symbol"].lower() for w in st.session_state["watchlist"]}

        st.markdown('<div class="section-header">📊 Stocks</div>', unsafe_allow_html=True)
        render_tip("overview_stocks")
        stock_cols = st.columns(3)
        for i, item in enumerate(data.get("stocks", [])):
            with stock_cols[i % 3]:
                render_asset_card(item, show_save_btn=True,
                                  wl_symbols=wl_symbols, news_articles=_ov_articles)

        st.markdown('<div class="section-header">🚀 Cryptocurrencies</div>', unsafe_allow_html=True)
        render_tip("overview_crypto")
        crypto_cols = st.columns(3)
        for i, item in enumerate(data.get("crypto", [])):
            with crypto_cols[i % 3]:
                render_asset_card(item, show_save_btn=True,
                                  wl_symbols=wl_symbols, news_articles=_ov_articles)

        st.markdown('<div class="section-header">📉 Price History</div>', unsafe_allow_html=True)
        all_assets = data.get("stocks", []) + data.get("crypto", [])
        labels = [f"{a.get('symbol','').upper()}  —  {a.get('name','')}" for a in all_assets]
        chosen_label = st.selectbox("Select an asset to chart", labels, key="ov_chart_pick")

        period_labels = {"7d": "7 Days", "1mo": "1 Month", "3mo": "3 Months"}

        if chosen_label:
            idx    = labels.index(chosen_label)
            chosen = all_assets[idx]
            sym    = chosen.get("symbol", "")
            atype  = chosen.get("asset_type", "stock")
            ch_name = chosen.get("name", sym.upper())

            with st.spinner("Loading price history..."):
                hist_resp, hist_err = api_get(
                    f"/api/market/history/{sym}?asset_type={atype}&period={period}"
                )

            if hist_err or hist_resp.status_code != 200:
                st.warning("Price history is temporarily unavailable for this asset.")
            else:
                history = hist_resp.json().get("history", [])
                if history:
                    df = pd.DataFrame(history)
                    fig = go.Figure()
                    # I removed fill="tozeroy" because it filled from the price
                    # line all the way down to $0, making high-priced stocks like
                    # AAPL ($270) appear as a solid blue block with no visible
                    # variation. A clean line chart is much easier to read.
                    fig.add_trace(go.Scatter(
                        x=df["date"], y=df["price"],
                        mode="lines+markers",
                        name=sym.upper(),
                        line=dict(color="#f0b90b", width=2.5),
                        marker=dict(size=5),
                        hovertemplate=(
                            f"<b>{ch_name}</b><br>"
                            "Date: %{x}<br>"
                            "Price: $%{y:,.2f}<extra></extra>"
                        ),
                    ))
                    fig.update_layout(
                        **_PLOTLY_LAYOUT,
                        title=dict(
                            text=f"{ch_name} — {period_labels.get(period, period)}",
                            font=dict(size=14, color="#fff"),
                        ),
                        height=380,
                    )
                    st.plotly_chart(fig, use_container_width=True,
                                   config={"displayModeBar": False})

                    # I send the actual price history to a dedicated /api/ai/chart
                    # endpoint so the AI can reference specific dates and prices
                    # rather than giving a generic summary.
                    chart_ai_key = f"chart_ai_{sym}_{atype}"
                    if st.button("AI Summary — Explain this chart", key=chart_ai_key, use_container_width=True):
                        with st.spinner("Analysing chart..."):
                            ai_resp, ai_err = api_post("/api/ai/chart", {
                                "symbol": sym,
                                "name": ch_name,
                                "asset_type": atype,
                                "period": period_labels.get(period, period),
                                "history": history,
                            }, timeout=35)
                        if ai_err:
                            st.warning("AI summary is temporarily unavailable.")
                        elif ai_resp.status_code == 200:
                            st.session_state[f"ai_result_{chart_ai_key}"] = ai_resp.json().get("answer", "")
                        else:
                            st.warning("Could not generate summary right now.")

                    if st.session_state.get(f"ai_result_{chart_ai_key}"):
                        st.markdown(
                            f'<div class="tip-box">'
                            f'<div class="tip-label">AI Summary — {sym.upper()} Chart</div>'
                            f'<div class="tip-content">{_escape_ai(st.session_state[f"ai_result_{chart_ai_key}"])}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                    chart_ask_key = f"chart_ask_{sym}_{atype}"
                    chart_q = st.text_input(
                        "Ask about this chart",
                        placeholder=f"e.g. Why did {sym.upper()} change this week?",
                        key=chart_ask_key,
                        label_visibility="collapsed",
                    )
                    if chart_q and st.button("Ask", key=f"chart_askbtn_{sym}_{atype}", use_container_width=True):
                        with st.spinner("Thinking..."):
                            ai_resp, ai_err = api_post("/api/ai/chart", {
                                "symbol": sym,
                                "name": ch_name,
                                "asset_type": atype,
                                "period": period_labels.get(period, period),
                                "history": history,
                                "question": chart_q,
                            }, timeout=35)
                        if ai_err:
                            st.warning("AI is temporarily unavailable.")
                        elif ai_resp.status_code == 200:
                            st.session_state[f"ai_answer_{chart_ask_key}"] = ai_resp.json().get("answer", "")
                        else:
                            st.warning("Could not get an answer right now.")

                    if st.session_state.get(f"ai_answer_{chart_ask_key}"):
                        st.markdown(
                            f'<div class="tip-box">'
                            f'<div class="tip-label">AI Answer — {sym.upper()}</div>'
                            f'<div class="tip-content">{_escape_ai(st.session_state[f"ai_answer_{chart_ask_key}"])}</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                else:
                    st.info("No historical data available for this asset.")

        # I built this Portfolio Simulator so users can ask "What if I invested
        # $X in this asset?" — it uses real historical prices to show what their
        # money would be worth today. This is unique to MarketFlow Live and
        # reinforces the educational goal by making price data tangible.
        st.markdown('<div class="section-header">💡 Portfolio Simulator — "What If?"</div>',
                    unsafe_allow_html=True)
        st.caption(
            "Pick any asset, enter a hypothetical amount, and see what your "
            "investment would be worth today based on real price history."
        )

        sim_c1, sim_c2, sim_c3 = st.columns([3, 2, 2])
        with sim_c1:
            sim_label = st.selectbox("Asset", labels, key="sim_asset_pick",
                                     label_visibility="collapsed")
        with sim_c2:
            sim_amount = st.number_input("Amount ($)", min_value=1.0, value=1000.0,
                                         step=100.0, key="sim_amount",
                                         label_visibility="collapsed")
        with sim_c3:
            sim_period = st.selectbox("Period", ["7d", "1mo", "3mo"],
                                      format_func=lambda x: period_labels.get(x, x),
                                      key="sim_period", label_visibility="collapsed")

        if st.button("Calculate", key="sim_calc_btn", use_container_width=True):
            sim_idx    = labels.index(sim_label)
            sim_asset  = all_assets[sim_idx]
            sim_sym    = sim_asset.get("symbol", "")
            sim_atype  = sim_asset.get("asset_type", "stock")
            sim_name   = sim_asset.get("name", sim_sym.upper())

            with st.spinner("Calculating..."):
                sim_resp, sim_err = api_get(
                    f"/api/market/history/{sim_sym}?asset_type={sim_atype}&period={sim_period}"
                )

            if sim_err or not sim_resp or sim_resp.status_code != 200:
                st.warning("Could not load price history for this asset.")
            else:
                sim_history = sim_resp.json().get("history", [])
                if sim_history and len(sim_history) >= 2:
                    buy_price = sim_history[0].get("price", 0)
                    now_price = sim_history[-1].get("price", 0)

                    if buy_price > 0:
                        units = sim_amount / buy_price
                        current_value = round(units * now_price, 2)
                        profit = round(current_value - sim_amount, 2)
                        pct = round(((now_price - buy_price) / buy_price) * 100, 2)
                        profit_class = "profit" if profit >= 0 else "loss"
                        arrow = "▲" if profit >= 0 else "▼"
                        buy_date = sim_history[0].get("date", "start")
                        now_date = sim_history[-1].get("date", "today")

                        st.markdown(f"""
                        <div class="sim-result">
                            <div class="sim-result-title">Simulation Result — {sim_name}</div>
                            <div class="sim-row">
                                <span class="sim-row-label">Invested</span>
                                <span class="sim-row-value">${sim_amount:,.2f} on {buy_date}</span>
                            </div>
                            <div class="sim-row">
                                <span class="sim-row-label">Buy Price</span>
                                <span class="sim-row-value">${buy_price:,.2f}</span>
                            </div>
                            <div class="sim-row">
                                <span class="sim-row-label">Units Bought</span>
                                <span class="sim-row-value">{units:,.4f}</span>
                            </div>
                            <div class="sim-row">
                                <span class="sim-row-label">Price Today ({now_date})</span>
                                <span class="sim-row-value">${now_price:,.2f}</span>
                            </div>
                            <div class="sim-row">
                                <span class="sim-row-label">Current Value</span>
                                <span class="sim-row-value {profit_class}">${current_value:,.2f}</span>
                            </div>
                            <div class="sim-row">
                                <span class="sim-row-label">Profit / Loss</span>
                                <span class="sim-row-value {profit_class}">{arrow} ${abs(profit):,.2f} ({pct:+.2f}%)</span>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.warning("Buy price data unavailable for this asset.")
                else:
                    st.info("Not enough historical data available for this simulation.")

    with news_col:
        render_news_sidebar()


def render_search():
    st.markdown("#### 🔍 Search Assets")
    st.caption(
        "Look up any stock ticker (e.g. NVDA, AMZN, GOOGL) "
        "or cryptocurrency (e.g. dogecoin, solana, cardano)."
    )
    render_tip("search")

    c1, c2, c3 = st.columns([3, 2, 1])
    with c1:
        query = st.text_input("Search", placeholder="Enter ticker or coin name…",
                              label_visibility="collapsed", key="search_q")
    with c2:
        filt = st.selectbox("Asset type", ["All", "Stocks only", "Crypto only"],
                            label_visibility="collapsed", key="search_filter")
    with c3:
        do_search = st.button("Search", use_container_width=True)

    type_map = {"All": "all", "Stocks only": "stock", "Crypto only": "crypto"}

    if do_search and query.strip():
        atype_param = type_map.get(filt, "all")
        with st.spinner(f'Searching for "{query.strip()}"…'):
            resp, err = api_get(
                f"/api/market/search?q={query.strip()}&asset_type={atype_param}"
            )
        if err:
            st.error(f"⚠️ {err}")
            st.session_state["search_results"] = []
        elif resp.status_code != 200:
            st.error("Search failed. Please try again.")
            st.session_state["search_results"] = []
        else:
            st.session_state["search_results"] = resp.json().get("results", [])

    results = st.session_state.get("search_results", [])

    if results:
        st.markdown(
            f'<div class="section-header">Results &nbsp;({len(results)} found)</div>',
            unsafe_allow_html=True,
        )
        wl_symbols: set = set()
        if st.session_state.get("user_id"):
            if not st.session_state["wl_loaded"]:
                _load_watchlist()
            wl_symbols = {w["symbol"].lower() for w in st.session_state["watchlist"]}

        cols = st.columns(3)
        for i, item in enumerate(results):
            with cols[i % 3]:
                render_asset_card(item, show_save_btn=True, wl_symbols=wl_symbols)

    elif do_search and query.strip():
        st.info("No results found. Try a different ticker or coin name.")


def render_watchlist():
    st.markdown("#### ⭐ My Watchlist")

    st.markdown("""
    <div class="guide-card">
        <div class="guide-title">How Your Watchlist Works</div>
        <div class="guide-step-text">
            Your watchlist is a personal shortlist of stocks and cryptocurrencies
            you want to track. Prices update every time you visit this page.
        </div>
        <br>
        <div style="margin-bottom:8px;">
            <span class="guide-step-num">1</span>
            <span class="guide-step-text"><strong>Add assets</strong> — Go to
            <em>Market Overview</em> or <em>Search</em> and click the green
            <strong>＋ Save</strong> button on any asset card.</span>
        </div>
        <div style="margin-bottom:8px;">
            <span class="guide-step-num">2</span>
            <span class="guide-step-text"><strong>Track prices</strong> — Your
            saved assets appear here with live prices.</span>
        </div>
        <div style="margin-bottom:8px;">
            <span class="guide-step-num">3</span>
            <span class="guide-step-text"><strong>Compare</strong> — Click the
            blue <strong>Compare</strong> button on up to 4 assets, then go to
            the Compare page.</span>
        </div>
        <div>
            <span class="guide-step-num">4</span>
            <span class="guide-step-text"><strong>Remove</strong> — Click the
            red <strong>Remove</strong> button to take an asset off your
            watchlist.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    render_tip("watchlist")

    c1, c2, _ = st.columns([1, 1, 2])
    with c1:
        if st.button("🔄 Refresh prices", use_container_width=True):
            st.session_state["watchlist"] = []
            st.session_state["wl_loaded"] = False
            st.rerun()
    with c2:
        if st.button("＋ Add assets →", use_container_width=True, key="wl_go_search"):
            set_page("Search")
            st.rerun()

    if not st.session_state["wl_loaded"]:
        with st.spinner("Loading your watchlist…"):
            _load_watchlist()

    items = st.session_state.get("watchlist", [])

    if not items:
        st.markdown("""
        <div class="empty-card">
            <div class="empty-icon">⭐</div>
            <div class="empty-title">Your watchlist is empty</div>
            <div class="empty-desc">
                Head to <strong>Market Overview</strong> or <strong>Search</strong>
                to find stocks and cryptocurrencies. Press the green
                <strong>＋ Save</strong> button on any asset to add it here.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    stocks_count = sum(1 for w in items if w.get("asset_type") == "stock")
    crypto_count = sum(1 for w in items if w.get("asset_type") == "crypto")

    s1, s2, s3 = st.columns(3)
    with s1:
        st.markdown(f"""
        <div class="wl-status-card">
            <div class="wl-status-count">{len(items)}</div>
            <div class="wl-status-label">Total saved</div>
        </div>""", unsafe_allow_html=True)
    with s2:
        st.markdown(f"""
        <div class="wl-status-card">
            <div class="wl-status-count">{stocks_count}</div>
            <div class="wl-status-label">Stocks</div>
        </div>""", unsafe_allow_html=True)
    with s3:
        st.markdown(f"""
        <div class="wl-status-card">
            <div class="wl-status-count">{crypto_count}</div>
            <div class="wl-status-label">Cryptocurrencies</div>
        </div>""", unsafe_allow_html=True)

    with st.spinner("Fetching live prices for your watchlist…"):
        live_items = []
        for wl in items:
            sym   = wl["symbol"]
            atype = wl["asset_type"]
            resp, err = api_get(f"/api/market/search?q={sym}&asset_type={atype}")
            matched = None
            if not err and resp.status_code == 200:
                results = resp.json().get("results", [])
                matched = next(
                    (r for r in results if r["symbol"].lower() == sym.lower()), None
                )
            if matched:
                live_items.append({**wl, **matched})
            else:
                live_items.append({**wl, "price": 0.0, "change": 0.0, "source": "fallback"})

    compare_syms = {c["symbol"].lower() for c in st.session_state.get("compare_selection", [])}

    st.markdown('<div class="section-header">Your Saved Assets</div>', unsafe_allow_html=True)

    cols = st.columns(3)
    for i, item in enumerate(live_items):
        with cols[i % 3]:
            render_asset_card(item)

            sym     = item.get("symbol", "")
            name    = item.get("name", sym)
            atype   = item.get("asset_type", "")
            item_id = item.get("id")
            in_cmp  = sym.lower() in compare_syms

            ca, cb = st.columns(2)
            with ca:
                cmp_label = "✓ Comparing" if in_cmp else "⚖ Compare"
                if st.button(cmp_label, key=f"cmp_{sym}_{i}", use_container_width=True):
                    sel = st.session_state["compare_selection"]
                    entry = {"symbol": sym, "name": name, "asset_type": atype}
                    if in_cmp:
                        st.session_state["compare_selection"] = [
                            c for c in sel if c["symbol"].lower() != sym.lower()
                        ]
                    elif len(sel) < 4:
                        st.session_state["compare_selection"] = sel + [entry]
                    else:
                        st.warning("Maximum 4 assets for comparison.")
                    st.rerun()
            with cb:
                if st.button("✕ Remove", key=f"del_{item_id}_{i}", use_container_width=True):
                    resp, err = api_delete(f"/api/watchlist/{item_id}")
                    if err:
                        st.error(err)
                    else:
                        st.session_state["watchlist"] = []
                        st.session_state["wl_loaded"] = False
                        st.rerun()

    if st.session_state.get("compare_selection"):
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        sel = st.session_state["compare_selection"]
        names = "  ·  ".join(s["symbol"].upper() for s in sel)
        st.info(f"**{len(sel)} asset(s) queued for comparison:** &nbsp; {names}")
        if st.button("→ Go to Compare page", use_container_width=False):
            set_page("Compare")
            st.rerun()


def render_compare():
    st.markdown("#### ⚖️ Compare Assets")
    st.caption(
        "Add 2–4 stocks or cryptocurrencies to compare them side by side, "
        "including price, 24 h change, and historical trend."
    )
    render_tip("compare")

    st.markdown('<div class="section-header">Add assets to compare</div>',
                unsafe_allow_html=True)

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        new_sym = st.text_input("Ticker / coin ID", placeholder="e.g. NVDA or ethereum",
                                label_visibility="collapsed", key="cmp_sym_input")
    with c2:
        new_type = st.selectbox("Type", ["stock", "crypto"],
                                label_visibility="collapsed", key="cmp_type_input")
    with c3:
        if st.button("Add", use_container_width=True, key="cmp_add_btn"):
            sym = new_sym.strip()
            if sym:
                sel = st.session_state["compare_selection"]
                if any(c["symbol"].lower() == sym.lower() for c in sel):
                    st.warning("Already in your comparison.")
                elif len(sel) >= 4:
                    st.warning("Maximum 4 assets.")
                else:
                    st.session_state["compare_selection"] = sel + [
                        {"symbol": sym, "name": sym.upper(), "asset_type": new_type}
                    ]
                    st.rerun()

    sel = st.session_state.get("compare_selection", [])

    if sel:
        chip_cols = st.columns(len(sel))
        for i, entry in enumerate(sel):
            with chip_cols[i]:
                st.markdown(f"**{entry['symbol'].upper()}**  `{entry['asset_type']}`")
                if st.button("✕", key=f"rm_cmp_{entry['symbol']}_{i}"):
                    st.session_state["compare_selection"] = [
                        c for c in sel if c["symbol"].lower() != entry["symbol"].lower()
                    ]
                    st.rerun()

    if len(sel) < 2:
        st.markdown("""
        <div class="empty-card" style="margin-top:16px;">
            <div class="empty-icon">⚖️</div>
            <div class="empty-title">Add at least 2 assets</div>
            <div class="empty-desc">
                Use the fields above or save assets to your Watchlist,
                then select them there for comparison.
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    period = st.selectbox("History period", ["7d", "1mo", "3mo"], key="cmp_period")
    period_labels = {"7d": "7 Days", "1mo": "1 Month", "3mo": "3 Months"}

    symbols_param = ",".join(s["symbol"] for s in sel)
    types_param   = ",".join(s["asset_type"] for s in sel)

    with st.spinner("Fetching comparison data…"):
        resp, err = api_get(
            f"/api/market/compare"
            f"?symbols={symbols_param}&asset_types={types_param}&period={period}"
        )

    if err:
        st.error(f"⚠️ {err}")
        return
    if resp.status_code != 200:
        detail = ""
        try:
            detail = resp.json().get("detail", "")
        except Exception:
            pass
        st.error(f"⚠️ Comparison failed. {detail}")
        return

    assets = resp.json().get("assets", [])

    _COLORS = ["#f0b90b", "#0ecb81", "#8b5cf6", "#f6465d"]

    st.markdown('<div class="section-header">Current Prices</div>', unsafe_allow_html=True)
    st.caption("These are the live prices of the assets you're comparing. "
               "The percentage shows how much each has moved in the last 24 hours — "
               "green means it gained value, red means it lost value.")
    card_cols = st.columns(len(assets))
    for i, item in enumerate(assets):
        with card_cols[i]:
            render_asset_card(item)

    st.markdown('<div class="section-header">24 h Change (%)</div>', unsafe_allow_html=True)
    st.caption("How much each asset moved in the last 24 hours. "
               "Green bars = gained value, red bars = lost value.")

    bar_symbols = [a.get("symbol", "?").upper() for a in assets]
    bar_changes = [round(a.get("change") or 0.0, 2) for a in assets]
    bar_colors  = ["#22c55e" if c >= 0 else "#ef4444" for c in bar_changes]

    fig_bar = go.Figure(go.Bar(
        x=bar_changes, y=bar_symbols, orientation="h",
        marker_color=bar_colors,
        text=[f"{c:+.2f}%" for c in bar_changes],
        textposition="outside",
        textfont=dict(color="#c0c8dc", size=12),
        hovertemplate="<b>%{y}</b><br>24h Change: %{x:+.2f}%<extra></extra>",
    ))
    # I built the layout dict separately here because _PLOTLY_LAYOUT already
    # contains xaxis/yaxis keys, and passing them again as kwargs would cause
    # a "multiple values for keyword argument" error in Plotly.
    bar_layout = {**_PLOTLY_LAYOUT}
    bar_layout.update(
        height=max(180, len(assets) * 70),
        yaxis=dict(gridcolor="#2a2f3e", linecolor="#2a2f3e",
                   tickfont=dict(color="#8b9cc8", size=13), tickprefix=""),
        xaxis=dict(gridcolor="#2a2f3e", linecolor="#2a2f3e",
                   tickfont=dict(color="#8b9cc8"), ticksuffix="%", tickprefix=""),
        showlegend=False,
    )
    fig_bar.update_layout(**bar_layout)
    st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})

    st.markdown(
        f'<div class="section-header">Price History — {period_labels.get(period, period)}</div>',
        unsafe_allow_html=True,
    )

    # I added a chart type toggle so users can switch between a simple
    # line chart and a candlestick chart — educational for beginners.
    chart_type = st.radio(
        "Chart style",
        ["Line Chart", "Candlestick Chart"],
        horizontal=True,
        key="cmp_chart_type",
    )

    if chart_type == "Line Chart":
        st.caption("Hover over the lines to see exact prices on each date. "
                   "A line chart shows the closing price each day — useful for "
                   "spotting overall trends at a glance.")
    else:
        st.caption("Each candle shows 4 prices for one day: Open (start), "
                   "Close (end), High (peak), and Low (bottom). "
                   "Green candles = price went up that day. Red = price went down.")

    has_history = False

    if chart_type == "Line Chart":
        fig_hist = go.Figure()
        for i, item in enumerate(assets):
            history = item.get("history", [])
            if history:
                has_history = True
                df_h = pd.DataFrame(history)
                sym_label = item.get("symbol", "?").upper()
                asset_name = item.get("name", sym_label)
                color = _COLORS[i % len(_COLORS)]

                fig_hist.add_trace(go.Scatter(
                    x=df_h["date"], y=df_h["price"],
                    mode="lines+markers",
                    name=f"{sym_label} — {asset_name}",
                    line=dict(color=color, width=2.5),
                    marker=dict(size=4, color=color),
                    hovertemplate=(
                        f"<b>{sym_label}</b><br>"
                        "Date: %{x}<br>"
                        "Price: $%{y:,.2f}<extra></extra>"
                    ),
                ))

        if has_history:
            fig_hist.update_layout(
                **_PLOTLY_LAYOUT,
                title=dict(
                    text=f"Comparing {len(assets)} assets — {period_labels.get(period, period)}",
                    font=dict(size=14, color="#fff"),
                ),
                height=420,
            )
            st.plotly_chart(fig_hist, use_container_width=True, config={"displayModeBar": False})

    else:
        # Candlestick view — one chart per asset because candlestick charts
        # with different price ranges don't overlay well.
        for i, item in enumerate(assets):
            history = item.get("history", [])
            if not history or "open" not in history[0]:
                continue
            has_history = True
            df_h = pd.DataFrame(history)
            sym_label = item.get("symbol", "?").upper()
            asset_name = item.get("name", sym_label)
            color = _COLORS[i % len(_COLORS)]

            fig_candle = go.Figure(go.Candlestick(
                x=df_h["date"],
                open=df_h["open"],
                high=df_h["high"],
                low=df_h["low"],
                close=df_h["close"],
                increasing_line_color="#22c55e",
                decreasing_line_color="#ef4444",
                increasing_fillcolor="#22c55e",
                decreasing_fillcolor="#ef4444",
                name=sym_label,
            ))
            candle_layout = {**_PLOTLY_LAYOUT}
            candle_layout.update(
                title=dict(
                    text=f"{sym_label} — {asset_name}",
                    font=dict(size=14, color="#fff"),
                ),
                height=350,
                xaxis_rangeslider_visible=False,
            )
            fig_candle.update_layout(**candle_layout)
            st.plotly_chart(fig_candle, use_container_width=True, config={"displayModeBar": False})

    if not has_history:
        st.info("Historical price data is not available for the selected assets.")

    st.markdown('<div class="section-header">Portfolio Weight (by Price)</div>',
                unsafe_allow_html=True)
    st.caption("If you held one unit of each asset, this donut chart shows what "
               "percentage of your total value each one would represent. "
               "A bigger slice means that asset has a higher price — it doesn't mean "
               "it's a better investment.")

    pie_labels = [a.get("symbol", "?").upper() for a in assets]
    pie_values = [a.get("price") or 0.01 for a in assets]

    fig_pie = go.Figure(go.Pie(
        labels=pie_labels, values=pie_values,
        marker=dict(colors=_COLORS[:len(assets)],
                    line=dict(color="#0f1117", width=2)),
        textinfo="label+percent",
        textfont=dict(color="#fff", size=12),
        hovertemplate=(
            "<b>%{label}</b><br>"
            "Price: $%{value:,.2f}<br>"
            "Share: %{percent}<extra></extra>"
        ),
        hole=0.4,
    ))
    fig_pie.update_layout(
        paper_bgcolor="#0b0e11", plot_bgcolor="#1e2329",
        font=dict(color="#eaecef"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#eaecef", size=11)),
        margin=dict(l=20, r=20, t=30, b=20),
        height=350,
    )
    st.plotly_chart(fig_pie, use_container_width=True, config={"displayModeBar": False})

    st.markdown('<div class="section-header">Summary Table</div>', unsafe_allow_html=True)
    st.caption("A quick side-by-side comparison of all the key numbers. "
               "Use this to spot which asset has the biggest price change today.")
    rows = []
    for item in assets:
        rows.append({
            "Asset":       item.get("name", "N/A"),
            "Symbol":      item.get("symbol", "").upper(),
            "Type":        item.get("asset_type", "").capitalize(),
            "Price ($)":   f"{item.get('price') or 0.0:,.2f}",
            "24h Change":  f"{item.get('change') or 0.0:+.2f}%",
            "Data Source":  item.get("source", "—").capitalize(),
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


def render_learn():
    st.markdown("""
    <div class="learn-hero">
        <div class="learn-hero-title">Your Guide to Financial Markets</div>
        <div class="learn-hero-sub">
            Scroll through to understand stocks, crypto, and how money moves
            in the markets — explained simply, with real-world context from
            the data you see on this dashboard.
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="learn-flow-section">
        <div class="learn-flow-visual blue">💰</div>
        <div class="learn-flow-content">
            <div class="learn-flow-title">Why Should You Care About Markets?</div>
            <div class="learn-flow-body">
                Every time you buy a coffee, pay rent, or check the price of petrol,
                you're feeling the effect of financial markets. Markets determine how
                much things cost, how companies grow, and how economies rise and fall.
                <br><br>
                Understanding markets is not just for traders in suits. It's for anyone
                who wants to make smarter decisions with their money — whether that's
                knowing when to save, when to invest, or simply understanding what the
                news is talking about when they say "the FTSE is down 2%."
            </div>
            <div class="learn-flow-callout">
                <strong>On this dashboard:</strong> The Market Overview shows you 15
                real stocks and 15 cryptocurrencies updating in real time. Start there
                to see markets in action.
            </div>
        </div>
    </div>
    <hr class="learn-divider">
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="learn-flow-section reverse">
        <div class="learn-flow-visual green">📊</div>
        <div class="learn-flow-content">
            <div class="learn-flow-title">Stocks — Owning a Piece of a Company</div>
            <div class="learn-flow-body">
                When you buy a share of Apple (AAPL), you literally own a tiny fraction
                of that company. If Apple sells more iPhones and grows, your share
                becomes more valuable. If they have a bad quarter, it drops.
                <br><br>
                Stock prices move during US trading hours (Mon-Fri, 9:30 AM - 4:00 PM
                Eastern Time). Outside those hours, the price shown is the last
                closing price. That's why some stock cards may show 0% change on
                weekends — the market is literally closed.
                <br><br>
                Big companies like Apple, Microsoft, and NVIDIA are called
                <strong>large-cap</strong> stocks. They're more stable but grow
                slower. Smaller companies can rocket up or crash down in a single day.
            </div>
            <div class="learn-flow-callout">
                <strong>Try it:</strong> On Market Overview, each stock card shows a
                brief description of what that company does. Expand the news section
                under any card to see related headlines.
            </div>
        </div>
    </div>
    <hr class="learn-divider">
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="learn-flow-section">
        <div class="learn-flow-visual purple">🔗</div>
        <div class="learn-flow-content">
            <div class="learn-flow-title">Crypto — Digital Money Without Banks</div>
            <div class="learn-flow-body">
                Cryptocurrencies run on blockchains — digital record books that no
                single person or government controls. Bitcoin started it all in 2009.
                Ethereum added "smart contracts" that let developers build apps on top
                of the blockchain.
                <br><br>
                Unlike stocks, crypto trades <strong>24/7/365</strong>. That's why
                crypto prices can swing wildly overnight while you're asleep. A tweet
                from a CEO or a new regulation from a government can move Bitcoin
                10% in an hour.
                <br><br>
                <strong>Stablecoins</strong> like Tether (USDT) are designed to stay
                at exactly $1.00 — they're the "safe harbour" in the crypto storm.
            </div>
            <div class="learn-flow-callout">
                <strong>Notice:</strong> On the dashboard, crypto cards update around
                the clock. Compare a stock card at midnight (frozen) vs a crypto card
                (still moving) to see this difference in real time.
            </div>
        </div>
    </div>
    <hr class="learn-divider">
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="learn-flow-section reverse">
        <div class="learn-flow-visual red">📈</div>
        <div class="learn-flow-content">
            <div class="learn-flow-title">Reading the Numbers on Your Dashboard</div>
            <div class="learn-flow-body">
                Every asset card shows three key pieces of information:
                <br><br>
                <strong>Price</strong> — What one share or one coin costs right now.
                <br><br>
                <strong>24h Change (%)</strong> — How much the price moved in the
                last 24 hours. <span style="color:#22c55e">Green (+2.5%)</span>
                means it went up. <span style="color:#ef4444">Red (-1.8%)</span>
                means it went down.
                <br><br>
                <strong>Data badge</strong> — Shows whether the price is "Live",
                "Cached", or "Fallback".
            </div>
            <div class="learn-flow-callout">
                <strong>Pro tip:</strong> Use the Compare page to put two assets side
                by side. The interactive charts let you hover over any date to see
                the exact price.
            </div>
        </div>
    </div>
    <hr class="learn-divider">
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="learn-flow-section">
        <div class="learn-flow-visual blue">🌍</div>
        <div class="learn-flow-content">
            <div class="learn-flow-title">What Makes Prices Go Up or Down?</div>
            <div class="learn-flow-body">
                It all comes down to <strong>supply and demand</strong>. If more
                people want to buy than sell, the price goes up. If more want to
                sell than buy, it goes down.
                <br><br>
                <strong>Company results</strong> — Apple reports record iPhone sales?
                People rush to buy AAPL stock, pushing the price up.
                <br><br>
                <strong>Economic data</strong> — High inflation means the central
                bank may raise interest rates, which often causes stock prices to fall.
                <br><br>
                <strong>News and sentiment</strong> — A headline saying "Bitcoin
                banned in major economy" causes panic selling.
                <br><br>
                <strong>Global events</strong> — Wars, pandemics, and elections
                all create uncertainty. Markets hate uncertainty.
            </div>
            <div class="learn-flow-callout">
                <strong>See it in action:</strong> The News panel on Market Overview
                labels each headline as Bullish, Bearish, or Neutral.
            </div>
        </div>
    </div>
    <hr class="learn-divider">
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="learn-flow-section reverse">
        <div class="learn-flow-visual red">📉</div>
        <div class="learn-flow-content">
            <div class="learn-flow-title">When Mainstream Stocks Drop — What Does It Mean?</div>
            <div class="learn-flow-body">
                When Apple, Microsoft, and NVIDIA all drop on the same day, that's
                usually a <strong>market-wide event</strong> — not about those
                companies specifically.
                <br><br>
                A <strong>bear market</strong> is when prices fall 20%+ from their
                recent high. A <strong>bull market</strong> is sustained growth.
                The US stock market has spent roughly 78% of its history in bull markets.
                <br><br>
                The key lesson: short-term drops are normal. What matters is the
                long-term trend.
            </div>
            <div class="learn-flow-callout">
                <strong>Explore:</strong> Use the 3-month view on the Compare page
                to see longer-term trends.
            </div>
        </div>
    </div>
    <hr class="learn-divider">
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="learn-flow-section">
        <div class="learn-flow-visual green">⚖️</div>
        <div class="learn-flow-content">
            <div class="learn-flow-title">Risk, Reward, and Diversification</div>
            <div class="learn-flow-body">
                The golden rule: <strong>higher potential returns = higher risk</strong>.
                Crypto can gain 50% in a month, but can also lose 50%. Blue-chip
                stocks are steadier but won't double overnight.
                <br><br>
                <strong>Diversification</strong> means spreading your money across
                different assets. The Compare page's pie chart shows this visually.
            </div>
            <div class="learn-flow-callout">
                <strong>Remember:</strong> MarketFlow Live is an educational platform.
                Always research thoroughly before making real investment decisions.
            </div>
        </div>
    </div>
    <hr class="learn-divider">
    """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">🗺 How to Use MarketFlow Live</div>',
                unsafe_allow_html=True)

    _HOWTO_STEPS = [
        ("Create an account & log in",
         "Register with your email, then sign in to unlock your personal watchlist."),
        ("Browse Market Overview",
         "See 15 stocks and 15 cryptos with live prices. Each card shows a brief description and related news."),
        ("Search any asset",
         "Look up any stock ticker (NVDA, TSLA) or crypto (dogecoin, solana) using the Search page."),
        ("Save to your Watchlist",
         "Click the green ＋ Save button to track assets. View them all on My Watchlist."),
        ("Compare side by side",
         "Select up to 4 assets and compare with interactive charts, pie charts, and summary tables."),
        ("Read the news",
         "The news panel shows headlines with sentiment badges — learn to read market mood."),
    ]

    for idx, (title, desc) in enumerate(_HOWTO_STEPS, start=1):
        st.markdown(f"""
        <div class="howto-step">
            <div class="howto-num">{idx}</div>
            <div class="howto-body">
                <div class="howto-title">{title}</div>
                <div class="howto-desc">{desc}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">📖 Financial Glossary</div>',
                unsafe_allow_html=True)
    st.caption("Tap any term to see its definition.")

    for term, definition in GLOSSARY.items():
        with st.expander(f"**{term}**"):
            st.write(definition)


def render_login():
    def _handle_login():
        email    = st.session_state.get("login_email", "").strip()
        password = st.session_state.get("login_password", "")
        if not email or not password:
            st.session_state["login_error"] = "Please enter both email and password."
            return
        resp, err = api_post("/api/auth/login", {"email": email, "password": password})
        if err:
            st.session_state["login_error"] = err
            return
        if resp.status_code == 200:
            d = resp.json()
            st.session_state["user_email"]   = email
            st.session_state["user_id"]      = d.get("user_id")
            st.session_state["login_error"]  = None
            st.session_state["pending_page"] = "Market Overview"
        else:
            st.session_state["login_error"] = "Invalid email or password."

    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("""
        <div class="auth-card">
            <div class="auth-title">Welcome Back</div>
            <div class="auth-subtitle">Log in to access your personalised dashboard.</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            st.text_input("Email address", placeholder="you@example.com", key="login_email")
            st.text_input("Password", type="password", placeholder="Your password",
                          key="login_password")
            st.form_submit_button("Sign In", on_click=_handle_login,
                                  use_container_width=True)

        if st.session_state.get("login_error"):
            st.error(f"⚠️  {st.session_state['login_error']}")

        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown(
            '<p style="text-align:center;font-size:0.85rem;color:#6b7280;">'
            "Don't have an account?</p>",
            unsafe_allow_html=True,
        )
        st.button("Create Account →", on_click=set_page, args=("Register",),
                  use_container_width=True, key="login_to_reg")


def render_register():
    st.session_state["register_success"] = False
    _, center, _ = st.columns([1, 2, 1])
    with center:
        st.markdown("""
        <div class="auth-card">
            <div class="auth-title">Create an Account</div>
            <div class="auth-subtitle">Join MarketFlow Live and start tracking markets.</div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("register_form"):
            email    = st.text_input("Email address", placeholder="you@example.com")
            password = st.text_input("Password", type="password",
                                     placeholder="Choose a strong password")
            submitted = st.form_submit_button("Create Account", use_container_width=True)

        if submitted:
            if not email or not password:
                st.warning("Please enter both an email and a password.")
            else:
                resp, err = api_post("/api/auth/register",
                                     {"email": email, "password": password})
                if err:
                    st.error(f"⚠️  {err}")
                elif resp.status_code == 200:
                    st.session_state["register_success"] = True
                    st.success("✅ Account created! You can now sign in.")
                else:
                    detail = resp.json().get("detail", "Registration failed.")
                    st.error(f"⚠️  {detail}")

        if st.session_state.get("register_success"):
            st.button("Go to Login →", on_click=set_page, args=("Login",),
                      use_container_width=True)

        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown(
            '<p style="text-align:center;font-size:0.85rem;color:#6b7280;">'
            "Already have an account?</p>",
            unsafe_allow_html=True,
        )
        st.button("Sign In", on_click=set_page, args=("Login",),
                  use_container_width=True, key="reg_to_login")


_page = st.session_state["page"]

if _page in ("Market Overview", "Market Overview (Guest)"):
    render_market_overview()
elif _page == "Search":
    render_search()
elif _page == "My Watchlist":
    render_watchlist()
elif _page == "Compare":
    render_compare()
elif _page == "Learn":
    render_learn()
elif _page == "Login":
    render_login()
elif _page == "Register":
    render_register()
