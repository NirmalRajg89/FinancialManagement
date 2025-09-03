import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st
from datetime import datetime, timedelta
import requests
from typing import Dict, List, Tuple
import json

class MarketIntelligence:
    def __init__(self):
        self.news_api_key = 'd4a44082cfa14bf7b8a95de96aefbcec'
        self.base_url = 'https://newsapi.org/v2/everything'
        
    def get_market_impact_news(self, days_back: int = 7) -> List[Dict]:
        """
        Get news that has significant market impact with curated analysis.
        """
        impact_keywords = [
            "market impact", "stock surge", "market crash", "rally", "selloff",
            "earnings beat", "earnings miss", "guidance", "analyst upgrade", "analyst downgrade",
            "Fed decision", "interest rates", "inflation", "GDP", "jobs report",
            "merger announcement", "acquisition", "IPO", "dividend increase", "stock split"
        ]
        
        all_news = []
        for keyword in impact_keywords:
            params = {
                'q': f'"{keyword}" AND (stock OR market OR trading)',
                'apiKey': self.news_api_key,
                'language': 'en',
                'pageSize': 5,
                'sortBy': 'relevancy',
                'from': (datetime.utcnow() - timedelta(days=days_back)).isoformat(),
                'to': datetime.utcnow().isoformat(),
            }
            
            try:
                response = requests.get(self.base_url, params=params)
                if response.status_code == 200:
                    articles = response.json()['articles']
                    for article in articles:
                        article['impact_keyword'] = keyword
                        article['impact_score'] = self._calculate_impact_score(article)
                    all_news.extend(articles)
            except Exception as e:
                print(f"Error fetching news for {keyword}: {e}")
        
        # Sort by impact score and remove duplicates
        unique_news = []
        seen_titles = set()
        for article in sorted(all_news, key=lambda x: x.get('impact_score', 0), reverse=True):
            title = article.get('title', '')
            if title not in seen_titles:
                unique_news.append(article)
                seen_titles.add(title)
        
        return unique_news[:20]
    
    def _calculate_impact_score(self, article: Dict) -> float:
        """Calculate the potential market impact score of a news article."""
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        content = f"{title} {description}"
        
        # High impact keywords
        high_impact = ['crash', 'surge', 'rally', 'plunge', 'soar', 'tank', 'earnings', 'guidance', 'fed', 'rate']
        # Medium impact keywords
        medium_impact = ['upgrade', 'downgrade', 'merger', 'acquisition', 'ipo', 'dividend', 'split']
        # Low impact keywords
        low_impact = ['announcement', 'update', 'report', 'news', 'statement']
        
        score = 0
        for keyword in high_impact:
            if keyword in content:
                score += 3
        for keyword in medium_impact:
            if keyword in content:
                score += 2
        for keyword in low_impact:
            if keyword in content:
                score += 1
        
        # Boost score for recent articles
        published_at = article.get('publishedAt', '')
        if published_at:
            try:
                pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                hours_ago = (datetime.utcnow() - pub_date).total_seconds() / 3600
                if hours_ago < 24:
                    score += 2
                elif hours_ago < 72:
                    score += 1
            except:
                pass
        
        return score
    
    def get_stock_price_graph(self, symbol: str, period: str = "1mo") -> go.Figure:
        """
        Create an interactive stock price graph with volume and technical indicators.
        """
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period=period)
            
            if hist.empty:
                return None
            
            # Create subplots
            fig = make_subplots(
                rows=3, cols=1,
                shared_xaxes=True,
                vertical_spacing=0.05,
                subplot_titles=(f'{symbol} Stock Price', 'Volume', 'RSI'),
                row_heights=[0.6, 0.2, 0.2]
            )
            
            # Candlestick chart
            fig.add_trace(
                go.Candlestick(
                    x=hist.index,
                    open=hist['Open'],
                    high=hist['High'],
                    low=hist['Low'],
                    close=hist['Close'],
                    name=f'{symbol} Price',
                    increasing_line_color='#00ff00',
                    decreasing_line_color='#ff0000'
                ),
                row=1, col=1
            )
            
            # Volume bars
            colors = ['red' if close < open else 'green' for close, open in zip(hist['Close'], hist['Open'])]
            fig.add_trace(
                go.Bar(
                    x=hist.index,
                    y=hist['Volume'],
                    name='Volume',
                    marker_color=colors,
                    opacity=0.7
                ),
                row=2, col=1
            )
            
            # RSI indicator
            rsi = self._calculate_rsi(hist['Close'])
            fig.add_trace(
                go.Scatter(
                    x=hist.index,
                    y=rsi,
                    name='RSI',
                    line=dict(color='purple')
                ),
                row=3, col=1
            )
            
            # Add RSI overbought/oversold lines
            fig.add_hline(y=70, line_dash="dash", line_color="red", row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="green", row=3, col=1)
            
            # Update layout
            fig.update_layout(
                title=f'{symbol} Market Analysis',
                xaxis_rangeslider_visible=False,
                height=600,
                showlegend=True
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating graph for {symbol}: {e}")
            return None
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate RSI technical indicator."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def get_sector_performance_graph(self) -> go.Figure:
        """
        Create a sector performance comparison graph.
        """
        sectors = {
            'Technology': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'NVDA', 'META'],
            'Healthcare': ['JNJ', 'PFE', 'UNH', 'ABBV', 'MRK', 'TMO', 'ABT'],
            'Financial': ['JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'BLK'],
            'Energy': ['XOM', 'CVX', 'COP', 'EOG', 'SLB', 'PSX', 'VLO'],
            'Consumer': ['PG', 'KO', 'PEP', 'WMT', 'HD', 'MCD', 'DIS']
        }
        
        sector_data = {}
        
        for sector_name, symbols in sectors.items():
            sector_returns = []
            for symbol in symbols:
                try:
                    stock = yf.Ticker(symbol)
                    hist = stock.history(period="1mo")
                    if not hist.empty:
                        return_pct = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
                        sector_returns.append(return_pct)
                except:
                    continue
            
            if sector_returns:
                sector_data[sector_name] = np.mean(sector_returns)
        
        # Create bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=list(sector_data.keys()),
                y=list(sector_data.values()),
                marker_color=['red' if x < 0 else 'green' for x in sector_data.values()],
                text=[f'{x:.2f}%' for x in sector_data.values()],
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title='Sector Performance (1 Month)',
            xaxis_title='Sectors',
            yaxis_title='Average Return (%)',
            height=400
        )
        
        return fig
    
    def get_market_correlation_graph(self, symbol: str) -> go.Figure:
        """
        Show correlation between a stock and major indices.
        """
        try:
            stock = yf.Ticker(symbol)
            stock_hist = stock.history(period="3mo")
            
            indices = {
                'S&P 500': '^GSPC',
                'NASDAQ': '^IXIC',
                'Dow Jones': '^DJI'
            }
            
            correlations = {}
            for index_name, index_symbol in indices.items():
                index = yf.Ticker(index_symbol)
                index_hist = index.history(period="3mo")
                
                if not stock_hist.empty and not index_hist.empty:
                    # Align dates
                    common_dates = stock_hist.index.intersection(index_hist.index)
                    if len(common_dates) > 10:
                        stock_returns = stock_hist.loc[common_dates]['Close'].pct_change().dropna()
                        index_returns = index_hist.loc[common_dates]['Close'].pct_change().dropna()
                        
                        # Align lengths
                        min_len = min(len(stock_returns), len(index_returns))
                        correlation = stock_returns.iloc[:min_len].corr(index_returns.iloc[:min_len])
                        correlations[index_name] = correlation
            
            # Create correlation heatmap
            fig = go.Figure(data=go.Heatmap(
                z=[[correlations.get('S&P 500', 0), correlations.get('NASDAQ', 0), correlations.get('Dow Jones', 0)]],
                x=['S&P 500', 'NASDAQ', 'Dow Jones'],
                y=[symbol],
                colorscale='RdBu',
                zmid=0,
                text=[[f'{correlations.get("S&P 500", 0):.3f}', f'{correlations.get("NASDAQ", 0):.3f}', f'{correlations.get("Dow Jones", 0):.3f}']],
                texttemplate='%{text}',
                textfont={"size": 14},
                showscale=True
            ))
            
            fig.update_layout(
                title=f'{symbol} Market Correlation Analysis',
                height=300
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating correlation graph for {symbol}: {e}")
            return None
    
    def get_news_impact_timeline(self, symbol: str) -> go.Figure:
        """
        Create a timeline showing news events and their impact on stock price.
        """
        try:
            # Get stock data
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1mo")
            
            if hist.empty:
                return None
            
            # Get news for the symbol
            params = {
                'q': f'({symbol}) AND (stock OR market OR trading)',
                'apiKey': self.news_api_key,
                'language': 'en',
                'pageSize': 10,
                'sortBy': 'publishedAt',
                'from': (datetime.utcnow() - timedelta(days=30)).isoformat(),
                'to': datetime.utcnow().isoformat(),
            }
            
            news_events = []
            try:
                response = requests.get(self.base_url, params=params)
                if response.status_code == 200:
                    articles = response.json()['articles']
                    for article in articles:
                        published_at = article.get('publishedAt', '')
                        if published_at:
                            try:
                                pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                                news_events.append({
                                    'date': pub_date,
                                    'title': article.get('title', ''),
                                    'impact_score': self._calculate_impact_score(article)
                                })
                            except:
                                continue
            except Exception as e:
                print(f"Error fetching news for timeline: {e}")
            
            # Create timeline
            fig = go.Figure()
            
            # Stock price line
            fig.add_trace(go.Scatter(
                x=hist.index,
                y=hist['Close'],
                mode='lines',
                name=f'{symbol} Price',
                line=dict(color='blue', width=2)
            ))
            
            # News events as annotations
            for event in news_events:
                # Find closest price point
                closest_date = min(hist.index, key=lambda x: abs((x - event['date']).total_seconds()))
                price_at_date = hist.loc[closest_date, 'Close']
                
                # Color based on impact score
                color = 'red' if event['impact_score'] > 5 else 'orange' if event['impact_score'] > 3 else 'green'
                
                fig.add_annotation(
                    x=closest_date,
                    y=price_at_date,
                    text=f"📰 {event['title'][:30]}...",
                    showarrow=True,
                    arrowhead=2,
                    arrowsize=1,
                    arrowwidth=2,
                    arrowcolor=color,
                    bgcolor=color,
                    bordercolor=color,
                    borderwidth=1,
                    font=dict(color="white", size=10)
                )
            
            fig.update_layout(
                title=f'{symbol} News Impact Timeline',
                xaxis_title='Date',
                yaxis_title='Stock Price ($)',
                height=500
            )
            
            return fig
            
        except Exception as e:
            print(f"Error creating timeline for {symbol}: {e}")
            return None

@st.cache_resource
def get_market_intelligence():
    """Get cached market intelligence instance."""
    return MarketIntelligence()

def get_curated_market_news():
    """Get curated market impact news."""
    mi = get_market_intelligence()
    return mi.get_market_impact_news()

def create_stock_analysis_graph(symbol: str, period: str = "1mo"):
    """Create comprehensive stock analysis graph."""
    mi = get_market_intelligence()
    return mi.get_stock_price_graph(symbol, period)

def create_sector_performance_graph():
    """Create sector performance comparison graph."""
    mi = get_market_intelligence()
    return mi.get_sector_performance_graph()

def create_market_correlation_graph(symbol: str):
    """Create market correlation analysis graph."""
    mi = get_market_intelligence()
    return mi.get_market_correlation_graph(symbol)

def create_news_impact_timeline(symbol: str):
    """Create news impact timeline graph."""
    mi = get_market_intelligence()
    return mi.get_news_impact_timeline(symbol)
