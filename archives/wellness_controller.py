import openai
import streamlit as st
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

openai.api_key = st.secrets["OPENAI_API_KEY"]
llm = ChatOpenAI(
    model="gpt-4",
    temperature=0.7,
    api_key=st.secrets["OPENAI_API_KEY"]
)

def get_wellness_response(user_input):
    messages = [
        SystemMessage(content=get_system_prompt()),
        HumanMessage(content=user_input)
    ]

    response = llm.invoke(messages)
    return response.content
def get_system_prompt():
    return (
        "You are a certified fitness and wellness coach. "
        "Your job is to help users with personalized advice on workouts, nutrition, yoga, and mental wellness. "
        "Whenever helpful, share a YouTube video link related to the suggestion."
    )

import re

def extract_youtube_links(text):
    pattern = r'(https?://(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)[\w\-]+)'
    return re.findall(pattern, text)