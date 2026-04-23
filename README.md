# MarketFlow Live

MarketFlow Live is a financial literacy platform designed to make stock and cryptocurrency markets accessible to complete beginners. Unlike traditional trading platforms that assume prior knowledge and overwhelm users with jargon, MarketFlow Live prioritises education at every touchpoint, explaining what data means rather than simply displaying it.

## The Problem

Most financial platforms are built for experienced traders. A beginner searching for "Apple stock" is met with candlestick charts, P/E ratios, and moving averages with no explanation of what any of it means. Research consistently shows that low financial literacy leads to poor investment decisions, yet the tools available do little to bridge that knowledge gap.

MarketFlow Live takes a different approach. Every chart, every metric, and every data point is accompanied by plain language explanations. An AI assistant is available on every page to answer questions in a conversational, educational tone without ever giving financial advice.

## What It Does

**Live Market Data**
The dashboard displays real time prices for 15 major stocks and 15 cryptocurrencies, pulled from Yahoo Finance and CoinGecko. Each asset is presented as a card showing price, percentage change, and a mini trend indicator. Data is cached with a 60 second TTL to balance freshness with API rate limits.

**Interactive Charts**
Clicking any asset opens an interactive Plotly chart with full OHLC candlestick data for stocks and line charts for crypto. Users can toggle between time periods and hover over individual data points. A dedicated learn section explains how to read these charts before users encounter them.

**AI Powered Explanations**
Every asset page includes an AI summary button and a question answering chat. These use OpenRouter's GPT OSS 120B model with a dual steering prompt strategy that combines system messages with few shot examples to keep responses educational, concise, and consistent. The AI never gives financial advice, instead explaining concepts like market capitalisation, volatility, and sector performance in beginner friendly language.

**Watchlist**
Logged in users can save assets to a personalised watchlist that persists across sessions. The watchlist uses a composite unique constraint to prevent duplicates and updates with live prices each time the page loads.

**Asset Comparison**
The compare feature lets users overlay two to four assets on a single normalised chart showing percentage returns over time. This allows beginners to visually understand relative performance without needing to understand absolute price differences. Each comparison includes an AI generated analysis highlighting key differences.

**Financial News with Sentiment**
A news feed pulls the latest financial headlines from Alpha Vantage and labels each article as bullish, bearish, or neutral using sentiment analysis. This helps beginners start recognising how news events connect to market movements.

**Portfolio Simulator**
A hypothetical investment calculator lets users ask "what if I had invested X amount in this asset Y months ago" and see what their return would have been. This makes abstract concepts like compound growth and volatility tangible without requiring real money.

**Market Mood**
An aggregate sentiment indicator analyses the overall mood across tracked assets, giving beginners a quick sense of whether markets are generally optimistic or pessimistic on any given day.

## What Makes It Different

Most beginner finance apps either oversimplify to the point of being useless or simply replicate what professional platforms already offer with a slightly cleaner UI. MarketFlow Live sits in the middle by providing real, live market data with genuine analytical tools while wrapping everything in an educational layer.

The AI integration is the key differentiator. Rather than linking out to external glossaries or embedding static tooltips, the platform offers a context aware AI assistant that knows which asset the user is looking at and can answer specific questions about it in real time. The dual steering prompt strategy ensures the AI maintains a consistent educational personality across all interactions.

The three tier data fallback system (live data, stale cache, zero fallback) means the platform never crashes or shows error pages to users, even when external APIs are temporarily unavailable. This resilience is particularly important for a learning platform where encountering a broken page could discourage a beginner from returning.

## Architecture

The system follows a decoupled architecture with a FastAPI backend serving a REST API and a Streamlit frontend consuming it.

**Backend (FastAPI)**
Seven routers handle distinct concerns: authentication, market data, search, watchlist, compare, news, and AI. Password hashing uses PBKDF2 SHA256 via passlib. A ThreadPoolExecutor with six workers handles concurrent stock data fetching. An in memory TTL cache layer provides 60 second caching for market data and 30 minute caching for news.

**Frontend (Streamlit)**
A single page application with a custom CSS dark theme, card based layout, and Plotly charts. The frontend communicates with the backend entirely through HTTP requests, making the two components independently deployable.

**Database (SQLite + SQLAlchemy)**
Two models: User and Watchlist. A startup migration function uses SQLAlchemy's inspector to detect and add missing columns automatically, preventing schema drift issues during development.

**External APIs**
Yahoo Finance (stocks), CoinGecko (crypto), Alpha Vantage (news and sentiment), and OpenRouter (AI). All API calls include error handling and fallback strategies.


- **Application:** https://marketflowlive.streamlit.app
- **API Documentation:** https://mfl-project.onrender.com/docs


Note: The backend runs on a free hosting tier and may take 10 to 15 seconds to wake up on first load if it has been idle.
