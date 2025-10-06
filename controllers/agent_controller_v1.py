# agent_controller.py

import os
import json
import re
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


def create_agent_executor_v1(static_vars: dict):
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
        input_key="question",   # we are using {question} in the prompt
        output_key="output",
    )
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         "You are a financial assistant. When returning comparisons or structured data, "
         "format it as either JSON (array of objects) or a Markdown table. Avoid extra text. "
         "If the user requests to send a summary or information as an SMS, use the 'send_sms_tool' "
         "with the summary or relevant information as input."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{question}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_openai_tools_agent(
        llm=llm,
        tools=tools,
        prompt=prompt
    )

    executor = AgentExecutor(agent=agent, tools=tools, memory=memory, verbose=True)
    return InvestmentAgent(executor)


def create_investment_summary_v1(static_vars: dict):
    load_env()

    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        input_key="question",   # we are using {question} in the prompt
        output_key="output",
    )
    tools = [
        get_stock_list,
        get_stock_price,
    ]


    base_prompt = ChatPromptTemplate.from_messages([
        ("system",
         """You are a financial assistant.
    Given the user profile, investment inputs, and target goal, calculate the final projected values for the entire tenure and check if the target goal can be achieved.

    -----
    ### RULES
    - Perform all calculations internally. Never explain formulas or steps.
    - Output must be in Markdown tables only.
    - Always format numbers in US numbering style with commas.
    - Prefix all monetary values with $.
    - Always show percentages with the % symbol.
    - In Suggestions column, show each recommendation on a new line using line breaks (- item 1 - item 2).
    - Never leave numbers in raw form.

    -------
    ### OUTPUT SECTIONS

    ### Based on Financial analysis : Max Monthly investment  : {monthly_contribution}

    ### 1. Investment Options Analysis

    {monthly_contribution_investment}

    ---
    ### 2. Sample Investment Examples
    Get 3 mutual funds in different caps large, small & medium with avg returns. 
    Also get equities in only 3 sectors Technology, healthcare, financial services with avg returns.  
    Calculate the monthly investment to contribute based on goal amount, tenure, avg returns and append.
    
    I want to generate a sample investment summary including:
    
    #### Mutual Funds (3 samples)
    For each mutual fund, include the following columns:
    - Fund Name
    - Category (Large Cap, Mid Cap, Small Cap, etc.)
    - Expected Return (%)
    - Risk Level (Low, Medium, High)
    - Monthly Investment
    - Goal Tenure ()
    - Maturity Value ({goal_amount})

    #### Equity Investments (3 samples)
    For each equity sector/theme, include:
    - Sector/Theme Name
    - Expected Return (%)
    - Market Cap Segment (Large, Mid, Small)
    - Investment Horizon Recommendation (Short, Medium, Long-term)
    - Monthly Investment
    - Maturity Value ({goal_amount})
    - Goal Tenure ()
    - Example Stocks/Companies

    #### Commodities & Alternative Investments (optional)
    Include key commodity or alternative asset classes with:
    - Investment Option
    - Expected Return (%)
    - Risk Level
    - Monthly Contribution (optional)
    - Maturity Value ({goal_amount})
    - Notes on liquidity and market characteristics

    Present all results in clean, readable Markdown tables with clear section headings.

    ---
    Would you like me to suggest specific mutual funds, ETFs, or commodity investments that match this allocation?

    Important:
    - All values are for the full tenure, factoring in monthly contributions & compounding where applicable.
    - Never show formulas, only the results.
    - Always include the Goal Feasibility section.
    # - Alternate suggestions must be realistic and aligned with risk tolerance.
    
    - In alternate Suggestions, if {plan_type} is "Short-term", Suggest diversification and review & adjust funds in account of financial goals.
    - If {plan_type} is "Long-term" and {goals} is “Home", suggest to consider the Mortgage plans by visiting {mortgage_info_url}.
    - If {plan_type} is "Long-term" {has_house_asset} and {goals} is "Retirement", optionally suggest HELOC as a liquidity strategy.
    - If {plan_type} is "Long-term" {has_house_asset} and {goals} is "Home", Suggest to go to HELOC by visiting {heloc_info_url} or Mortgage plans by visiting {mortgage_info_url}.
    - If there is no {has_house_asset}, skip HELOC advice.
    - If {total_liabilities} exists, suggest Refinancing for a better interest rate by visiting {refinance_info_url}.
    - For clarity:
        - HELOC Example: {heloc_example}
        - Refinancing Example: {refinance_example}
    """),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{question}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # 🔒 Bind your dynamic values here so the agent doesn't expect them later
    prompt = base_prompt.partial(**static_vars)

    agent = create_openai_tools_agent(llm=llm, prompt=prompt , tools=tools)

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        return_intermediate_steps=False
    )

    return InvestmentAgent(executor)


def calculate_monthly_contribution(goal_amount, annual_return, years):
    """Calculate the monthly contribution needed for the investment goal."""
    # Ensure goal_amount is a float (numeric)
    goal_amount = float(goal_amount)

    # Calculate the total number of months
    months = years * 12

    # Convert annual return to monthly return
    monthly_return = annual_return / 12

    # Calculate monthly contribution based on the formula
    if monthly_return == 0:
        # If there's no return (0% expected), we can simply divide goal amount by months
        monthly_contribution = goal_amount / months
    else:
        monthly_contribution = goal_amount * monthly_return / ((1 + monthly_return) ** months - 1)

    # Round to 2 decimal places
    return round(monthly_contribution, 2)