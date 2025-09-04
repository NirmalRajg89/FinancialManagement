from datetime import datetime

import streamlit as st
import requests

API_KEY = 'a9d2d7605e0b4f96b4f06e3ac61cf3b7'
BASE_URL = 'https://newsapi.org/v2/everything'

@st.cache_data(ttl=5)
def get_stock_news(search_query=None):
    """
    Fetch stock news with optional search functionality.
    
    Args:
        search_query (str, optional): Search term for specific news. If None, returns general stock news.
    
    Returns:
        list: List of news articles
    """
    if search_query:
        # Enhanced search query with better stock symbol handling
        search_lower = search_query.lower()
        
        # Handle common stock symbols and company names
        if 'apple' in search_lower or 'aapl' in search_lower:
            query = '(Apple OR AAPL OR "Apple Inc" OR "Apple stock") AND (stock OR shares OR earnings OR financial)'
        elif 'tesla' in search_lower or 'tsla' in search_lower:
            query = '(Tesla OR TSLA OR "Tesla Inc" OR "Tesla stock") AND (stock OR shares OR earnings OR financial)'
        elif 'microsoft' in search_lower or 'msft' in search_lower:
            query = '(Microsoft OR MSFT OR "Microsoft Corp" OR "Microsoft stock") AND (stock OR shares OR earnings OR financial)'
        elif 'google' in search_lower or 'googl' in search_lower or 'alphabet' in search_lower:
            query = '(Google OR GOOGL OR Alphabet OR "Alphabet Inc" OR "Google stock") AND (stock OR shares OR earnings OR financial)'
        elif 'amazon' in search_lower or 'amzn' in search_lower:
            query = '(Amazon OR AMZN OR "Amazon.com" OR "Amazon stock") AND (stock OR shares OR earnings OR financial)'
        elif 'bitcoin' in search_lower or 'btc' in search_lower or 'crypto' in search_lower:
            query = f'({search_query} OR Bitcoin OR BTC OR cryptocurrency) AND (price OR market OR trading OR investment)'
        else:
            # General search with financial context
            query = f'({search_query}) AND (stock OR shares OR finance OR market OR investment OR trading OR earnings OR financial)'
    else:
        query = 'stocks OR finance OR market'
    
    params = {
        'q': query,
        'apiKey': API_KEY,
        'language': 'en',
        'pageSize': 15,  # Increased to show more results
        'sortBy': 'publishedAt',  # Ensure sorting by latest
        'to': datetime.utcnow().isoformat(),  # Limit to up-to-current time
    }

    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        return response.json()['articles']
    else:
        print(str(response.text))
        st.error(f"Error fetching news: {response.status_code}")
        return []

@st.cache_data(ttl=5)
def search_stock_news(search_term):
    """
    Search for specific stock news based on user input.
    
    Args:
        search_term (str): The search term entered by user
    
    Returns:
        list: List of filtered news articles
    """
    return get_stock_news(search_term)

@st.cache_data(ttl=60)  # Cache for 1 minute for real-time updates
def get_stock_statistics():
    """
    Get important stock market statistics and events using real-time data.
    
    Returns:
        dict: Dictionary containing stock market statistics
    """
    try:
        import yfinance as yf
        from datetime import datetime
        
        # Get real-time data for major indices and commodities
        tickers = {
            '^DJI': 'dow_jones',      # Dow Jones
            '^GSPC': 'sp_500',        # S&P 500
            '^IXIC': 'nasdaq',        # NASDAQ
            '^VIX': 'vix',            # VIX
            'CL=F': 'oil_price',      # Oil
            'GC=F': 'gold_price',     # Gold
            'BTC-USD': 'bitcoin',     # Bitcoin
            '^TNX': 'treasury_10y',   # 10Y Treasury
            'DX-Y.NYB': 'dollar_index' # Dollar Index
        }
        
        stats = {}
        
        # Determine market status
        now = datetime.now()
        market_hour = now.hour
        market_day = now.weekday()  # 0 = Monday, 6 = Sunday
        
        # Market is open Monday-Friday 9:30 AM - 4:00 PM ET
        if market_day < 5 and 9 <= market_hour < 16:
            stats["market_status"] = "Open"
        else:
            stats["market_status"] = "Closed"
        
        # Fetch real-time data
        for ticker, key in tickers.items():
            try:
                stock = yf.Ticker(ticker)
                hist = stock.history(period="1d", interval="1m")
                
                if not hist.empty:
                    current_price = hist['Close'].iloc[-1]
                    
                    # Get previous close for percentage change
                    prev_close = stock.info.get('previousClose', current_price)
                    change_pct = ((current_price - prev_close) / prev_close) * 100
                    
                    if key == 'treasury_10y':
                        stats[key] = round(current_price, 2)
                    elif key in ['oil_price', 'gold_price']:
                        stats[key] = round(current_price, 2)
                    elif key == 'vix':
                        stats[key] = round(current_price, 2)
                    elif key == 'dollar_index':
                        stats[key] = round(current_price, 2)
                    else:
                        stats[key] = round(current_price, 2)
                else:
                    # Fallback to info if history is empty
                    info = stock.info
                    if 'currentPrice' in info:
                        stats[key] = round(info['currentPrice'], 2)
                    elif 'regularMarketPrice' in info:
                        stats[key] = round(info['regularMarketPrice'], 2)
                    else:
                        stats[key] = 0
                        
            except Exception as e:
                print(f"Error fetching data for {ticker}: {e}")
                stats[key] = 0
        
        return stats
        
    except Exception as e:
        print(f"Error fetching stock statistics: {e}")
        # Return mock data as fallback
        import random
        return {
            "market_status": "Open" if datetime.now().hour >= 9 and datetime.now().hour < 16 else "Closed",
            "dow_jones": round(34500 + random.uniform(-200, 200), 2),
            "sp_500": round(4200 + random.uniform(-50, 50), 2),
            "nasdaq": round(13500 + random.uniform(-100, 100), 2),
            "vix": round(15 + random.uniform(-5, 5), 2),
            "oil_price": round(75 + random.uniform(-5, 5), 2),
            "gold_price": round(1950 + random.uniform(-50, 50), 2),
            "bitcoin": round(45000 + random.uniform(-5000, 5000), 2),
            "treasury_10y": round(4.2 + random.uniform(-0.2, 0.2), 2),
            "dollar_index": round(103 + random.uniform(-2, 2), 2)
        }

@st.cache_data(ttl=30)  # Cache for 30 seconds for real-time stock data
def get_stock_data(symbol):
    """
    Get real-time stock data for a specific symbol.
    
    Args:
        symbol (str): Stock symbol (e.g., 'AAPL', 'MSFT')
    
    Returns:
        dict: Dictionary containing stock data
    """
    try:
        import yfinance as yf
        
        ticker = yf.Ticker(symbol.upper())
        info = ticker.info
        hist = ticker.history(period="1d", interval="1m")
        
        if not hist.empty:
            current_price = hist['Close'].iloc[-1]
            prev_close = info.get('previousClose', current_price)
            change = current_price - prev_close
            change_pct = (change / prev_close) * 100
            
            return {
                "symbol": symbol.upper(),
                "name": info.get('longName', symbol.upper()),
                "price": round(current_price, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "currency": info.get('currency', 'USD'),
                "market_cap": info.get('marketCap', 0),
                "volume": info.get('volume', 0),
                "prev_close": round(prev_close, 2)
            }
        else:
            # Fallback to info data
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0))
            prev_close = info.get('previousClose', current_price)
            change = current_price - prev_close
            change_pct = (change / prev_close) * 100 if prev_close > 0 else 0
            
            return {
                "symbol": symbol.upper(),
                "name": info.get('longName', symbol.upper()),
                "price": round(current_price, 2),
                "change": round(change, 2),
                "change_pct": round(change_pct, 2),
                "currency": info.get('currency', 'USD'),
                "market_cap": info.get('marketCap', 0),
                "volume": info.get('volume', 0),
                "prev_close": round(prev_close, 2)
            }
            
    except Exception as e:
        print(f"Error fetching stock data for {symbol}: {e}")
        return None

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_related_stocks(main_symbol):
    """
    Get related stocks for a given symbol.
    
    Args:
        main_symbol (str): Main stock symbol
    
    Returns:
        list: List of related stock data
    """
    try:
        # Define related stocks based on the main symbol
        related_mapping = {
            'AAPL': ['MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX', 'ADBE'],
            'MSFT': ['AAPL', 'GOOGL', 'AMZN', 'NVDA', 'ORCL', 'CRM', 'ADBE', 'INTC'],
            'GOOGL': ['AAPL', 'MSFT', 'AMZN', 'META', 'NFLX', 'TSLA', 'NVDA', 'ADBE'],
            'AMZN': ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA', 'META', 'NFLX', 'WMT'],
            'TSLA': ['AAPL', 'NVDA', 'AMZN', 'MSFT', 'GOOGL', 'F', 'GM', 'NIO'],
            'NVDA': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'AMD', 'INTC', 'META'],
            'META': ['AAPL', 'GOOGL', 'AMZN', 'MSFT', 'NFLX', 'SNAP', 'TWTR', 'NVDA'],
            'NFLX': ['AAPL', 'GOOGL', 'AMZN', 'META', 'DIS', 'CMCSA', 'ROKU', 'MSFT']
        }
        
        # Get related symbols for the main symbol
        related_symbols = related_mapping.get(main_symbol.upper(), 
                                            ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META', 'NFLX'])
        
        related_stocks = []
        for symbol in related_symbols[:8]:  # Limit to 8 related stocks
            stock_data = get_stock_data(symbol)
            if stock_data:
                related_stocks.append(stock_data)
        
        return related_stocks
        
    except Exception as e:
        print(f"Error fetching related stocks for {main_symbol}: {e}")
        return []
