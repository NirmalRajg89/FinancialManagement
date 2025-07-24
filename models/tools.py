# models/tools.py

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


def fetch_data(endpoint: str) -> list:
    """Fetch data from FMP API, works for symbol-based or direct endpoints."""
    url = f"{BASE_URL}{endpoint}&apikey={FINANCIAL_MODELING_PREP_API_KEY}" \
        if "?" in endpoint else f"{BASE_URL}{endpoint}?apikey={FINANCIAL_MODELING_PREP_API_KEY}"

    response = requests.get(url)
    response.raise_for_status()
    return response.json()
