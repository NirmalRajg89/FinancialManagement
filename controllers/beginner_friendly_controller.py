import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime, timedelta
import requests
from typing import Dict, List

class BeginnerFriendlyStockNews:
    def __init__(self):
        self.news_api_key = 'd4a44082cfa14bf7b8a95de96aefbcec'
        self.base_url = 'https://newsapi.org/v2/everything'
        
    def get_simple_stock_info(self, symbol: str) -> Dict:
        """Get simple, beginner-friendly stock information."""
        try:
            stock = yf.Ticker(symbol.upper())
            info = stock.info
            hist = stock.history(period="5d")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                prev_close = hist['Close'].iloc[-2] if len(hist) > 1 else current_price
                change = current_price - prev_close
                change_pct = (change / prev_close) * 100
                
                # Simple trend analysis
                if change_pct > 5:
                    trend = "🚀 Strong Up"
                    trend_color = "green"
                elif change_pct > 0:
                    trend = "📈 Up"
                    trend_color = "lightgreen"
                elif change_pct > -5:
                    trend = "📉 Down"
                    trend_color = "orange"
                else:
                    trend = "💥 Strong Down"
                    trend_color = "red"
                
                return {
                    "symbol": symbol.upper(),
                    "name": info.get('longName', symbol.upper()),
                    "price": round(current_price, 2),
                    "change": round(change, 2),
                    "change_pct": round(change_pct, 2),
                    "trend": trend,
                    "trend_color": trend_color,
                    "sector": info.get('sector', 'Unknown'),
                    "market_cap": info.get('marketCap', 0),
                    "volume": info.get('volume', 0)
                }
        except Exception as e:
            print(f"Error fetching stock info for {symbol}: {e}")
            return None
    
    def get_popular_stocks_summary(self) -> List[Dict]:
        """Get summary of popular stocks for beginners."""
        popular_stocks = [
            {"symbol": "AAPL", "name": "Apple", "description": "iPhone and Mac maker"},
            {"symbol": "MSFT", "name": "Microsoft", "description": "Windows and Office software"},
            {"symbol": "GOOGL", "name": "Google", "description": "Search engine and Android"},
            {"symbol": "AMZN", "name": "Amazon", "description": "Online shopping giant"},
            {"symbol": "TSLA", "name": "Tesla", "description": "Electric car company"},
            {"symbol": "NVDA", "name": "NVIDIA", "description": "Computer graphics chips"},
            {"symbol": "META", "name": "Meta", "description": "Facebook and social media"},
            {"symbol": "NFLX", "name": "Netflix", "description": "Streaming TV and movies"}
        ]
        
        summary = []
        for stock in popular_stocks:
            stock_info = self.get_simple_stock_info(stock["symbol"])
            if stock_info:
                stock_info.update({
                    "description": stock["description"]
                })
                summary.append(stock_info)
        
        return summary
    
    def get_beginner_friendly_news(self) -> List[Dict]:
        """Get news that's easy for beginners to understand."""
        # Simple, beginner-friendly search terms
        beginner_terms = [
            "stock market", "earnings", "company news", "business news",
            "technology news", "market update", "investment news"
        ]
        
        all_news = []
        for term in beginner_terms:
            params = {
                'q': f'"{term}" AND (stock OR market OR business)',
                'apiKey': self.news_api_key,
                'language': 'en',
                'pageSize': 3,
                'sortBy': 'relevancy',
                'from': (datetime.utcnow() - timedelta(days=3)).isoformat(),
                'to': datetime.utcnow().isoformat(),
            }
            
            try:
                response = requests.get(self.base_url, params=params)
                if response.status_code == 200:
                    articles = response.json()['articles']
                    for article in articles:
                        article['category'] = term
                        article['difficulty'] = 'beginner'
                    all_news.extend(articles)
            except Exception as e:
                print(f"Error fetching news for {term}: {e}")
        
        # Remove duplicates and return top 10
        unique_news = []
        seen_titles = set()
        for article in all_news:
            title = article.get('title', '')
            if title not in seen_titles:
                unique_news.append(article)
                seen_titles.add(title)
        
        return unique_news[:10]
    
    def get_market_sentiment_simple(self) -> str:
        """Get simple market sentiment for beginners."""
        try:
            # Get major indices
            indices = {
                'S&P 500': '^GSPC',
                'NASDAQ': '^IXIC',
                'Dow Jones': '^DJI'
            }
            
            up_count = 0
            total_count = 0
            
            for name, symbol in indices.items():
                stock = yf.Ticker(symbol)
                hist = stock.history(period="1d")
                if not hist.empty:
                    current = hist['Close'].iloc[-1]
                    prev = hist['Open'].iloc[0]
                    if current > prev:
                        up_count += 1
                    total_count += 1
            
            if total_count == 0:
                return "🤔 Market data unavailable"
            elif up_count == total_count:
                return "🚀 Bull Market - Most stocks are rising!"
            elif up_count > total_count / 2:
                return "📈 Mostly Positive - More stocks up than down"
            elif up_count == 0:
                return "📉 Bear Market - Most stocks are falling"
            else:
                return "📊 Mixed - Some stocks up, some down"
                
        except Exception as e:
            return "🤔 Market sentiment unavailable"
    
    def get_stock_tips_for_beginners(self) -> List[str]:
        """Get simple stock tips for beginners."""
        return [
            "💡 **Start Small**: Begin with small investments to learn",
            "📚 **Do Your Research**: Learn about companies before investing",
            "⏰ **Think Long Term**: Don't panic over daily price changes",
            "💰 **Diversify**: Don't put all your money in one stock",
            "📊 **Watch the News**: Stay informed about market events",
            "🎯 **Set Goals**: Know why you're investing",
            "📈 **Buy Low, Sell High**: Simple but effective strategy",
            "🔄 **Regular Investing**: Consider regular small investments"
        ]

@st.cache_resource
def get_beginner_friendly_stocks():
    """Get cached beginner-friendly stock instance."""
    return BeginnerFriendlyStockNews()

def get_simple_stock_data(symbol: str):
    """Get simple stock data for beginners."""
    bf = get_beginner_friendly_stocks()
    return bf.get_simple_stock_info(symbol)

def get_popular_stocks_overview():
    """Get overview of popular stocks."""
    bf = get_beginner_friendly_stocks()
    return bf.get_popular_stocks_summary()

def get_beginner_news():
    """Get beginner-friendly news."""
    bf = get_beginner_friendly_stocks()
    return bf.get_beginner_friendly_news()

def get_simple_market_sentiment():
    """Get simple market sentiment."""
    bf = get_beginner_friendly_stocks()
    return bf.get_market_sentiment_simple()

def get_beginner_tips():
    """Get beginner tips."""
    bf = get_beginner_friendly_stocks()
    return bf.get_stock_tips_for_beginners() 
