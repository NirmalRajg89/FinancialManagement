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

from controllers.loan_alternatives import should_offer_loans, suggest_loans
from models.tools import (
    send_sms_tool,
    send_email_tool,
    send_whatsapp_tool,
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
        send_sms_tool,
        send_email_tool,
        send_whatsapp_tool,
    ]

    base_prompt = ChatPromptTemplate.from_messages([
        ("system", """
    You are a **Financial Analyst Agent**.

    Your role:
    - Perform **financial calculations internally**.
    - Present all results as **clean Markdown tables**.
    - Do **not** include contextual recommendations (e.g., HELOC, mortgage, refinance) — these will be handled by another agent.

    ---
    ### Data
    {funds_data}

    ### RULES
    - Perform all calculations internally; **never show formulas**.
    - **Output only Markdown tables** and short Markdown text blocks.
    - Always format monetary values as **$X,XXX.XX** (US style).
    - Always include **%** with percentage values.
    - Prefix monetary values with `$`.
    - Clearly separate investment categories with `###` headings.
    - Keep output professional, minimal, and visually scannable.
    - For Equity Mutual Funds Output section, show only above Funds from Data section having Return greater than {req_return} and calculate monthly investment requrired to achieve the maturity value within goal tenure at expected return
    - For Index Funds Output section, show only above Funds from Data section having Return greater than {req_return} and calculate monthly investment requrired to achieve the maturity value within goal tenure at expected return
    - For Stocks Investments, Consider sectors from above data only and Return greater than {req_return} and calculate monthly investment requrired to achieve the maturity value within goal tenure at expected return
    # - Suggest Commodities & Alternatives only if their Expected Return greater than {req_return}
    ---

    ### OUTPUT SECTIONS

    #### 1. Investment Summary Overview
    Summarize user's goal, plan type, tenure, monthly contribution, and goal amount.

    #### 2. Investment Options Analysis
    Use {monthly_contribution_investment} and show potential monthly allocations or assumptions. Show all the options irrespective of req_return, don't trim any options.
    
    #### 3. Equity Mutual Funds
    Include:
    - Fund Name
    - Category (Large/Mid/Small Cap)
    - Expected Return (%)
    - Risk Level (Low/Medium/High)
    - Monthly Investment
    - Goal Tenure ({tenure})
    - Maturity Value ({goal_amount})
    
    #### 4. Index Funds
    Include:
    - Fund Name
    - Category (Large/Mid/Small Cap)
    - Expected Return (%)
    - Risk Level (Low/Medium/High)
    - Monthly Investment
    - Goal Tenure ({tenure})
    - Maturity Value ({goal_amount})

    #### 5. Stocks Investments
    Include:
    - Sector/Theme Name
    - Expected Return (%)
    - Market Cap Segment (Large/Mid/Small)
    - Investment Horizon (Short/Medium/Long-term)
    - Monthly Investment
    - Maturity Value ({goal_amount})
    - Example Stocks/Companies

    # #### 6. Commodities & Alternatives
    # Include:
    # - Investment Option
    # - Expected Return (%)
    # - Risk Level
    # - Monthly Contribution (optional)
    # - Maturity Value ({goal_amount})
    # - Notes on liquidity and characteristics

    #### 7. Goal Feasibility
    Assess if the current monthly contribution can achieve the goal amount over tenure.
    Provide a simple eloboration of the result (including {goal_amount}, {tenure} and {req_return}) with involving below terms:
    - "Feasible"
    - "Needs higher contribution"
    - "Requires longer tenure"

    ---

    Output clean Markdown only.
    Do **not** include alternate suggestions like HELOC or mortgage.
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