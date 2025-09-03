# models/tools.py
from langchain.tools import tool
import yfinance as yf
from datetime import datetime, timedelta
import os
import requests
from langchain_core.tools import tool
from dotenv import load_dotenv
import streamlit as st
load_dotenv()
FINANCIAL_MODELING_PREP_API_KEY = st.secrets["FINANCIAL_MODELING_PREP_API_KEY"]

BASE_URL = "https://financialmodelingprep.com/api/v3"


def fetch_data_for_multiple_symbols(symbols: str, endpoint: str) -> list:
    """
    Fetch data for multiple comma-separated stock symbols from a specific endpoint.
    Returns a list of dicts, one per symbol.
    """
    data = []
    for symbol in symbols.split(","):
        symbol = symbol.strip().upper()
        if symbol:
            try:
                response_data = fetch_data(f"{endpoint}{symbol}")
                data.append({symbol: response_data})
            except requests.HTTPError as e:
                data.append({symbol: f"Error fetching data: {e.response.text}"})
    return data


@tool
def get_stock_list() -> list:
    """
    Get a list of stock symbols available from the API.
    Useful for looking up stock ticker symbols or building dropdown menus.
    Not used for getting news or financial data.
    """
    url = f"{BASE_URL}/stock/list?apikey={FINANCIAL_MODELING_PREP_API_KEY}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()[:20]


@tool
def get_stock_price(symbols: str) -> list:
    """Get real-time stock prices for one or more stock symbols (comma-separated)."""
    return fetch_data_for_multiple_symbols(symbols, "/quote/")


@tool
def get_company_profile(symbols: str) -> list:
    """Get company profiles for the given stock symbols (comma-separated)."""
    return fetch_data_for_multiple_symbols(symbols, "/profile/")


@tool
def get_balance_sheet(symbols: str) -> list:
    """Get balance sheet data for the given stock symbols (comma-separated)."""
    return fetch_data_for_multiple_symbols(symbols, "/balance-sheet-statement/")


@tool
def get_income_statement(symbols: str) -> list:
    """Get income statement data for the given stock symbols (comma-separated)."""
    return fetch_data_for_multiple_symbols(symbols, "/income-statement/")


@tool
def get_cash_flow(symbols: str) -> list:
    """Get cash flow statement data for the given stock symbols (comma-separated)."""
    return fetch_data_for_multiple_symbols(symbols, "/cash-flow-statement/")


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


def fetch_data(endpoint: str) -> list:
    """Fetch data from FMP API, works for symbol-based or direct endpoints."""
    url = f"{BASE_URL}{endpoint}&apikey={FINANCIAL_MODELING_PREP_API_KEY}" \
        if "?" in endpoint else f"{BASE_URL}{endpoint}?apikey={FINANCIAL_MODELING_PREP_API_KEY}"

    response = requests.get(url)
    response.raise_for_status()
    return response.json()

@tool("get_historical_data")
def get_historical_data(symbol: str) -> str:
    """
    Fetches historical stock price data (daily) for the past year for a given stock symbol like 'NFLX'.
    Returns the last 5 days of OHLC data.
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
