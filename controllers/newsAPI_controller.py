import streamlit as st
import requests

API_KEY = 'a9d2d7605e0b4f96b4f06e3ac61cf3b7'
BASE_URL = 'https://newsapi.org/v2/everything'

def get_stock_news():
    params = {
        'q': 'stocks OR finance OR market',  # Keywords related to stock news
        'apiKey': API_KEY,
        'language': 'en',  # Get news in English
        'pageSize': 10,  # Limit to 10 articles
    }

    response = requests.get(BASE_URL, params=params)

    if response.status_code == 200:
        return response.json()['articles']
    else:
        st.error(f"Error fetching news: {response.status_code}")
        return []
