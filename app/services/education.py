GLOSSARY: dict[str, str] = {
    "Stock": (
        "A stock represents a small piece of ownership in a company. "
        "When you buy a share of Apple (AAPL), you literally own a tiny "
        "fraction of that company. Stock prices go up when more people "
        "want to buy than sell, and down when more people want to sell."
    ),
    "Cryptocurrency": (
        "A digital currency that uses cryptography for security and "
        "operates on a decentralised network (blockchain). Unlike "
        "traditional money, crypto is not controlled by any bank or "
        "government. Bitcoin was the first cryptocurrency, created in 2009."
    ),
    "Market Price": (
        "The current price at which an asset (stock or crypto) can be "
        "bought or sold. This changes constantly during trading hours "
        "based on supply and demand — how many people want to buy vs sell."
    ),
    "24h Change (%)": (
        "The percentage difference between the current price and the "
        "price 24 hours ago. A positive number (green) means the price "
        "went up; a negative number (red) means it went down. This helps "
        "you quickly see which assets are gaining or losing value today."
    ),
    "Market Capitalisation": (
        "The total value of all shares or coins in circulation. "
        "Calculated as: price x total number of shares/coins. A company "
        "with a share price of $100 and 1 million shares has a market "
        "cap of $100 million. Larger market cap generally means a more "
        "established and stable asset."
    ),
    "Bull Market": (
        "A period when prices are rising or expected to rise. The term "
        "'bullish' means optimistic about prices going up. Named after "
        "the way a bull attacks — thrusting its horns upward."
    ),
    "Bear Market": (
        "A period when prices are falling or expected to fall. The term "
        "'bearish' means expecting prices to go down. Named after the "
        "way a bear attacks — swiping its paws downward."
    ),
    "Volatility": (
        "How much and how quickly an asset's price changes. High "
        "volatility means big price swings (common in crypto). Low "
        "volatility means steadier prices (common in large, established "
        "stocks). Beginners should be aware that high volatility means "
        "higher risk but also higher potential reward."
    ),
    "Portfolio": (
        "The collection of all investments a person holds. A diversified "
        "portfolio spreads money across different types of assets (stocks, "
        "crypto, bonds) to reduce risk — if one goes down, others might "
        "go up."
    ),
    "Stablecoin": (
        "A type of cryptocurrency designed to maintain a stable price, "
        "usually pegged to a real currency like the US dollar. Tether "
        "(USDT) and USD Coin (USDC) are examples — they aim to always "
        "be worth $1.00. Used as a safe haven during crypto volatility."
    ),
    "Blockchain": (
        "A digital ledger (record book) that stores transactions across "
        "many computers. Once data is recorded, it cannot be changed — "
        "making it secure and transparent. Every cryptocurrency runs on "
        "a blockchain."
    ),
    "Dividend": (
        "A portion of a company's profits paid to shareholders. Not all "
        "companies pay dividends — fast-growing tech companies often "
        "reinvest profits instead. Dividends provide income even when "
        "the stock price is not rising."
    ),
    "Exchange": (
        "A marketplace where assets are bought and sold. The NYSE (New "
        "York Stock Exchange) is where stocks are traded. Binance and "
        "Coinbase are popular cryptocurrency exchanges."
    ),
    "Sentiment": (
        "The overall mood or attitude of investors toward a market or "
        "asset. Positive sentiment (optimism) tends to push prices up. "
        "Negative sentiment (fear) tends to push prices down. News, "
        "social media, and economic data all influence sentiment."
    ),
    "Liquidity": (
        "How easily an asset can be bought or sold without affecting its "
        "price. Bitcoin and Apple stock are highly liquid — you can buy "
        "or sell quickly. Smaller, lesser-known assets may be illiquid, "
        "meaning fewer buyers and sellers."
    ),
}


TIPS: dict[str, str] = {
    "overview_stocks": (
        "Stock prices change during US market hours (Mon-Fri, "
        "9:30 AM - 4:00 PM Eastern Time / 2:30 PM - 9:00 PM UK time). "
        "Outside these hours, the price shown is the last closing price. "
        "A green percentage means the stock gained value today; red means "
        "it lost value."
    ),
    "overview_crypto": (
        "Unlike stocks, cryptocurrency markets never close — they trade "
        "24 hours a day, 7 days a week, including weekends and holidays. "
        "This is why crypto prices can change dramatically overnight. "
        "The 24h change shows movement over the last full 24-hour window."
    ),
    "search": (
        "You can search for any stock by its ticker symbol (e.g. AAPL "
        "for Apple, GOOGL for Google) or any cryptocurrency by its name "
        "(e.g. 'dogecoin', 'solana'). Ticker symbols are short codes "
        "used to identify publicly traded companies."
    ),
    "watchlist": (
        "Your watchlist is like a personal shortlist of assets you want "
        "to keep an eye on. Professional traders and investors always "
        "maintain watchlists to track opportunities. Add assets here "
        "to see their prices every time you log in."
    ),
    "compare": (
        "Comparing assets side by side helps you understand relative "
        "performance. For example, comparing Bitcoin to Ethereum shows "
        "which has grown more over a period. Comparing a stock to a "
        "crypto shows how different asset classes behave differently."
    ),
    "news_sentiment": (
        "Each news article has a sentiment label: Bullish (positive for "
        "prices), Bearish (negative for prices), or Neutral. This is "
        "calculated by analysing the language in the article. In real "
        "markets, news sentiment is one of the biggest short-term drivers "
        "of price movement."
    ),
}


LEARN_SECTIONS: list[dict] = [
    {
        "title": "What Are Stocks?",
        "icon": "chart_with_upwards_trend",
        "content": (
            "A stock (also called a share or equity) represents partial "
            "ownership of a company. When a company like Apple wants to "
            "raise money, it sells shares to the public through a stock "
            "exchange. When you buy one share of Apple, you own a tiny "
            "piece of that company.\n\n"
            "Stock prices are determined by supply and demand. If a "
            "company releases a great product and more people want to "
            "buy its stock, the price goes up. If the company reports "
            "losses or bad news, people sell and the price goes down.\n\n"
            "Key things that affect stock prices include: company "
            "earnings reports, industry trends, economic conditions, "
            "interest rates set by central banks, and overall market "
            "sentiment."
        ),
    },
    {
        "title": "What Are Cryptocurrencies?",
        "icon": "link",
        "content": (
            "Cryptocurrencies are digital assets that use blockchain "
            "technology — a decentralised, tamper-proof ledger. Unlike "
            "traditional currencies controlled by governments and central "
            "banks, most cryptocurrencies operate independently.\n\n"
            "Bitcoin, created in 2009, was the first cryptocurrency. "
            "Ethereum introduced 'smart contracts' — programs that run "
            "on the blockchain. Today there are thousands of different "
            "cryptocurrencies, each with different purposes.\n\n"
            "Crypto prices are far more volatile than stocks because "
            "the market is newer, smaller, and heavily influenced by "
            "social media, regulation news, and speculation. Stablecoins "
            "like Tether (USDT) are designed to avoid this volatility "
            "by pegging their value to the US dollar."
        ),
    },
    {
        "title": "How Do Prices Move?",
        "icon": "bar_chart",
        "content": (
            "All market prices are driven by one simple principle: "
            "supply and demand. If more people want to buy an asset "
            "than sell it, the price goes up. If more people want to "
            "sell than buy, the price goes down.\n\n"
            "Several forces influence this balance:\n\n"
            "Company performance — Strong earnings push stock prices "
            "up. Weak results push them down.\n\n"
            "Economic data — Reports on employment, inflation, and GDP "
            "affect entire markets. High inflation often leads to "
            "higher interest rates, which can cause stock prices to fall.\n\n"
            "Global events — Wars, pandemics, trade disputes, and "
            "elections create uncertainty. For example, conflict in "
            "oil-producing regions often causes energy stock prices to "
            "rise because investors expect oil supply to decrease.\n\n"
            "Regulation — Government decisions on cryptocurrency "
            "regulation can cause huge price swings. A country banning "
            "crypto trading can crash prices; a country adopting it "
            "can boost them.\n\n"
            "Market sentiment — How investors collectively feel. Fear "
            "causes selling (prices drop). Optimism causes buying "
            "(prices rise). News headlines are one of the biggest "
            "drivers of sentiment."
        ),
    },
    {
        "title": "Reading Price Changes",
        "icon": "mag",
        "content": (
            "On the MarketFlow Live dashboard, every asset card shows "
            "a percentage change. Here is how to read it:\n\n"
            "A green positive number (e.g. +2.5%) means the asset's "
            "price is 2.5% higher than it was 24 hours ago.\n\n"
            "A red negative number (e.g. -1.8%) means the asset's "
            "price dropped 1.8% in the last 24 hours.\n\n"
            "Small daily changes (under 1-2%) are normal for stocks. "
            "Larger swings (5-10%+) are more common in crypto and "
            "usually indicate significant news or market events.\n\n"
            "The price history charts show how an asset's price has "
            "moved over 7 days, 1 month, or 3 months. An upward "
            "trend line suggests the asset has been gaining value; "
            "a downward trend suggests it has been losing value."
        ),
    },
    {
        "title": "Stocks vs Cryptocurrencies",
        "icon": "scales",
        "content": (
            "Stocks and cryptocurrencies are both investment assets, "
            "but they behave very differently:\n\n"
            "Trading hours — Stocks trade during set hours (US market: "
            "Mon-Fri, 9:30 AM-4:00 PM ET). Crypto trades 24/7/365.\n\n"
            "Volatility — Stocks of large companies typically move "
            "1-3% per day. Cryptocurrencies can move 5-20% in a day.\n\n"
            "Regulation — Stocks are heavily regulated by government "
            "agencies (like the SEC in the US). Crypto regulation is "
            "still evolving and varies by country.\n\n"
            "Ownership — Buying a stock means owning part of a real "
            "company with revenue and employees. Buying crypto means "
            "owning a digital token whose value is based on utility, "
            "adoption, and speculation.\n\n"
            "The Compare feature on this dashboard lets you place "
            "stocks and cryptos side by side to see these differences "
            "in real data."
        ),
    },
    {
        "title": "What Is Market Sentiment?",
        "icon": "thought_balloon",
        "content": (
            "Market sentiment is the overall attitude of investors "
            "toward a particular asset or the market as a whole. It "
            "is one of the most important short-term drivers of price.\n\n"
            "Bullish sentiment means investors are optimistic — they "
            "expect prices to rise. This often leads to more buying.\n\n"
            "Bearish sentiment means investors are pessimistic — they "
            "expect prices to fall. This often leads to more selling.\n\n"
            "Neutral sentiment means no strong feeling either way.\n\n"
            "The News section on this dashboard shows a sentiment "
            "label for each article (Bullish / Bearish / Neutral). "
            "This is calculated by analysing the language used in the "
            "article — the same technique used by professional trading "
            "firms to gauge market mood. Learning to read sentiment "
            "is a valuable skill in understanding market behaviour."
        ),
    },
    {
        "title": "Understanding Risk",
        "icon": "warning",
        "content": (
            "Every investment carries risk — the possibility of losing "
            "money. Understanding risk is one of the most important "
            "concepts in finance.\n\n"
            "Higher potential returns usually come with higher risk. "
            "Cryptocurrencies can gain 50% in a month but can also "
            "lose 50%. Large-cap stocks are more stable but grow "
            "more slowly.\n\n"
            "Diversification means spreading investments across "
            "different assets to reduce risk. If one asset drops, "
            "others in your portfolio might hold steady or rise.\n\n"
            "Important: MarketFlow Live is an educational platform. "
            "The data shown here is for learning purposes. Always do "
            "thorough research and consider seeking professional "
            "financial advice before making real investment decisions."
        ),
    },
]
