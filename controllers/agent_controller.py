# agent_controller.py

import os
from dotenv import load_dotenv

from langchain.chat_models import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.memory import ConversationBufferMemory
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder

from models.tools import (
    get_stock_list,
    get_stock_price,
    get_company_profile,
    get_balance_sheet,
    get_income_statement,
    get_cash_flow,
    get_news,
)
import streamlit as st

# Load .env only once
def load_env():
    load_dotenv()
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]


# Create the agent executor
def create_agent_executor():
    load_env()  # Ensure env is loaded

    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)

    tools = [
        get_stock_list,
        get_stock_price,
        get_company_profile,
        get_balance_sheet,
        get_income_statement,
        get_cash_flow,
        get_news,
    ]

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a financial assistant. When returning comparisons or structured data, format it as either JSON (array of objects) or a Markdown table. Avoid extra text."),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)
    return AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=True)
