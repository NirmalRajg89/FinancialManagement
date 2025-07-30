from datetime import datetime

import streamlit as st
import requests

API_KEY = 'd4a44082cfa14bf7b8a95de96aefbcec'
BASE_URL = 'https://newsapi.org/v2/everything'
@st.cache_data(ttl=5)
def get_stock_news():
    params = {
        'q': 'stocks OR finance OR market',
        'apiKey': API_KEY,
        'language': 'en',
        'pageSize': 10,
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
