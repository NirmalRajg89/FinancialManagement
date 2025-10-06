# models/tools.py
from langchain.tools import tool
import yfinance as yf
from datetime import datetime, timedelta
import os
import requests
from langchain_core.tools import tool
from dotenv import load_dotenv
import streamlit as st

# from controllers.sms_service import send_sms

load_dotenv()
FINANCIAL_MODELING_PREP_API_KEY = st.secrets["FINANCIAL_MODELING_PREP_API_KEY"]

BASE_URL = "https://financialmodelingprep.com/api/v3"

@tool
# def send_sms_tool(message: str) -> str:
#     """
#        Send the given message as an SMS to the customer.
#        Trigger your internal send_sms function here.
#        """
#     send_sms(message)
#     return "Summary sent via SMS."

def fetch_data(endpoint: str) -> list:
    """Fetch data from FMP API, works for symbol-based or direct endpoints."""
    # Properly append the API key
    url = f"{BASE_URL}{endpoint}"
    if '?' in url:
        url += f"&apikey={FINANCIAL_MODELING_PREP_API_KEY}"
    else:
        url += f"?apikey={FINANCIAL_MODELING_PREP_API_KEY}"
    response = requests.get(url)
    print(f"response", response)
    response.raise_for_status()
    return response.json()

def fetch_data_for_multiple_symbols(symbols: str, endpoint_template: str) -> list:
    """
    Fetch data for multiple comma-separated stock symbols from a specific endpoint.
    Returns a list of dicts, one per symbol.
    """
    results = []
    for symbol in symbols.split(","):
        symbol = symbol.strip().upper()
        if not symbol:
            continue
        try:
            endpoint = endpoint_template.format(symbol=symbol)
            data = fetch_data(endpoint)
            results.append({symbol: data})
        except requests.HTTPError as e:
            results.append({symbol: f"Error: {e.response.text}"})
    return results

# 🔁 Updated endpoint paths for FMP free tier under /v3
@tool
def get_stock_list() -> list:
    """Get a short list of stock symbols (for dropdowns etc.)."""
    return fetch_data("/stock/list")[:20]

@tool
def get_stock_price(symbols: str) -> list:
    """Get real-time stock prices for given symbols."""
    return fetch_data_for_multiple_symbols(symbols, "/quote/{symbol}")

@tool
def get_company_profile(symbols: str) -> list:
    """Get company profile info for given symbols."""
    return fetch_data_for_multiple_symbols(symbols, "/profile/{symbol}")

@tool
def get_balance_sheet(symbols: str) -> list:
    """Get latest balance sheet data for given symbols."""
    return fetch_data_for_multiple_symbols(symbols, "/balance-sheet-statement/{symbol}")

@tool
def get_income_statement(symbols: str) -> list:
    """Get latest income statement data for given symbols."""
    return fetch_data_for_multiple_symbols(symbols, "/income-statement/{symbol}")

@tool
def get_cash_flow(symbols: str) -> list:
    """Get latest cash flow statement data for given symbols."""
    return fetch_data_for_multiple_symbols(symbols, "/cash-flow-statement/{symbol}")

@tool("get_historical_data")
def get_historical_data(symbol: str) -> str:
    """
    Fetches historical stock price data (daily) for the past year for a given stock symbol.
    Returns the last 5 days of OHLC data using yfinance (since FMP free tier doesn't support detailed historical data).
    """
    try:
        end_date = datetime.today()
        start_date = end_date - timedelta(days=365)

        ticker = yf.Ticker(symbol.upper())
        hist = ticker.history(start=start_date.strftime("%Y-%m-%d"), end=end_date.strftime("%Y-%m-%d"))

        if hist.empty:
            return f"No historical data found for symbol: {symbol.upper()}"

        hist = hist.tail(5)  # Show last 5 days
        table = "| Date | Open | High | Low | Close |\n|------|------|------|-----|-------|\n"

        for idx, row in hist.iterrows():
            date = idx.strftime("%Y-%m-%d")
            table += f"| {date} | {round(row['Open'], 2)} | {round(row['High'], 2)} | {round(row['Low'], 2)} | {round(row['Close'], 2)} |\n"

        return f"Here is the recent historical price data for {symbol.upper()}:\n\n{table}"

    except Exception as e:
        return f"Error retrieving historical data: {str(e)}"

@tool
def get_news(symbols: str) -> list:
    """
    Get recent financial news for the given stock symbols (comma-separated, e.g. 'AAPL,MSFT').
    Returns a list of headlines with URLs and sources.
    """

    endpoint = "/fmp-articles?limit=5"

    return fetch_data(endpoint)


@tool
def get_latest_news(symbol: str) -> str:
    """
        Fetches the latest news headlines (title + link) for a given stock symbol using yfinance.
        Returns up to 5 recent news articles.
        """
    try:
        ticker = yf.Ticker(symbol.upper())
        news_items = ticker.news

        if not news_items:
            return f"No recent news found for {symbol.upper()}."

        # Filter out news with missing essential info (title & link)
        filtered_news = [
            item for item in news_items
            if item.get('title') and item.get('link')
        ]

        if not filtered_news:
            return f"No valid news articles found for {symbol.upper()}."

        # Limit to 5 latest news
        latest_news = filtered_news[:5]

        news_str = f"Latest news for {symbol.upper()}:\n\n"
        for item in latest_news:
            title = item.get('title')
            link = item.get('link')
            provider = item.get('publisher', 'Unknown source')
            published = item.get('providerPublishTime')
            date_str = datetime.utcfromtimestamp(published).strftime(
                '%Y-%m-%d %H:%M UTC') if published else 'Unknown date'

            news_str += f"- [{title}]({link})\n  Source: {provider} | Published: {date_str}\n\n"

        return news_str

    except Exception as e:
        return f"Error fetching latest news: {str(e)}"



