# agent_controller.py

import os
import json
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

def create_agent_executor_v1(static_vars: dict, history: list = None):
    load_env()

    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)

    tools = [
        send_sms_tool,
        send_email_tool,
        send_whatsapp_tool,
    ]

    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        input_key="question",
        output_key="output",
    )

    # Preload history into memory if available
    if history:
        for msg in history:
            role = msg.get("role")
            content = msg.get("content", "")
            if role == "user":
                memory.chat_memory.add_user_message(content)
            elif role == "assistant":
                memory.chat_memory.add_ai_message(content)
    prompt = ChatPromptTemplate.from_messages([
        ("system",
         """You are a financial assistant. When returning comparisons or structured data, format it as either JSON (array of objects) or a Markdown table. Avoid extra text.

    If the user requests to send the "goal plan summary", "investment plan summary", or similar:
    - Extract the most recent assistant message from the 'chat_history' (this is the summary).
    - Identify the requested delivery method (SMS, WhatsApp, or Email).
    - Extract the recipient contact information (phone number or email) from the user's message if provided.
    - If phone number or email is not provided, respond by asking for it.
    - Clean the message for SMS by removing markdown, tables, or other unsupported formatting.
    - Use the correct tool (`send_sms_tool`, `send_email_tool`, or `send_whatsapp_tool`) with the summary and contact detail.

    Examples:
    - If the user says: "Send the summary to +1234567890 via WhatsApp", use `send_whatsapp_tool(message, to_number=...)`.
    - If the user says: "Email the plan to me at example@example.com", use `send_email_tool(message, to_email=...)`.
    - If the user says: "Send via SMS", but doesn’t provide a number, ask them for the recipient's phone number.
    """),
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
        send_sms_tool,
        send_email_tool,
        send_whatsapp_tool,
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

### Based on Financial analysis : Monthly investment(40% of salary) : {monthly_contribution}
### 1. Investment Options Analysis
 {monthly_contribution_investment}
---
### 2. By Market Capitalization:
{formatted_allocation_table}
---
### 3. Sample Investment Examples
I want to generate a sample investment summary for:

1. Equity Mutual Funds
2. Stock Market investments (sector or theme-based)

For each type, show 5 sample investments. For each investment, include:

- Fund or Sector/Theme Name
- Monthly Contribution (use around {monthly_contribution} for Mutual Funds, less in {monthly_contribution} for Stocks)
- Maturity Value {goal_amount}
- Example Stocks/Companies
- Expected Return (%) — use realistic ranges (e.g. 8–12% for mutual funds, 15–20% for stock sectors)

Present all results in a clean, readable table format.

Label the two sections clearly.
Use sample values for illustration purposes only.

---
Would you like me to suggest specific mutual funds or ETFs that match this allocation?

Important:
- All values are for the full tenure, factoring in monthly contributions & compounding.
- Never show formulas, only the results.
- Always include the Goal Feasibility section.
- Alternate suggestions must be realistic (aligned with risk tolerance).
"""
         "If the user requests to send the 'Goal plan Summary report' or 'investment plan summary' or similar, you must extract the content of the **last AIMessage** from the 'chat_history' and then use the 'send_sms_tool', 'send_email_tool' or 'send_whatsapp_tool' with the extracted summary as input, depending on the user's requested delivery method."), # Added new instruction for sending summary
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