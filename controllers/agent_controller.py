# agent_controller.py

import os
import json
from dotenv import load_dotenv

import streamlit as st
from langchain_openai import ChatOpenAI
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
    get_news, get_historical_data, get_latest_news,
)


# Load env once
def load_env():
    load_dotenv()
    os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]


class InvestmentAgent:
    """Wrapper around AgentExecutor so we can safely add custom methods."""
    def __init__(self, executor: AgentExecutor):
        self.executor = executor

    def ask(self, question):
        """Passes a question to the agent and returns the answer."""
        if isinstance(question, dict):
            question = json.dumps(question, indent=2)

        result = self.executor.invoke({"question": question})
        return result["output"] if "output" in result else result


def create_agent_executor():
    load_env()

    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)

    tools = [
        get_stock_list,
        get_stock_price,
        get_company_profile,
        get_balance_sheet,
        get_income_statement,
        get_cash_flow,
        get_latest_news,
        get_historical_data,
    ]

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        input_key="question",
        output_key="output",
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a financial assistant. Generate only the final investment strategy without any headers "
         "such as 'Investment Plan Overview', 'Profile Summary', 'Goals', 'Risk Tolerance','Tenure' or 'Monthly Contribution'. "
         "Start your answer directly with the strategy itself. When returning structured data, use JSON or Markdown tables. "
         "Avoid extra explanations."),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{question}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        return_intermediate_steps=False
    )

    return InvestmentAgent(executor)
