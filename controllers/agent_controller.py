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

def create_agent_executor(static_vars: dict):
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
         "You are a financial assistant. When returning comparisons or structured data, format it as either JSON (array of objects) or a Markdown table. Avoid extra text."),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{question}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    # 🔒 Bind your dynamic values here so the agent doesn't expect them later
    prompt = prompt.partial(**static_vars)

    agent = create_openai_tools_agent(llm=llm, tools=tools, prompt=prompt)

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        return_intermediate_steps=False
    )

    return InvestmentAgent(executor)



def create_investment_summary(static_vars: dict):
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
- Always format numbers in Indian numbering style with commas.
- Prefix all monetary values with ₹.
- Always show percentages with the % symbol.
- In Suggestions column, show each recommendation on a new line using line breaks (- item 1<br>- item 2).
- Never leave numbers in raw form.

-------
### OUTPUT SECTIONS
### 1. Investment Options Analysis
- Use the given monthly contribution (₹{monthly_contribution}) and tenure ({tenure} years) to calculate the future value under each return range.
- For each investment option, show:
  * Expected Return (%)
  * Future Value at {tenure} Years (($))
  * Achieved Target? (Yes/No/Maybe, based on comparison with ₹{goal_amount})
  * Suggestions if Target is Not Met (use <br> for line breaks)
- **Important:** 
    * If the goal is achieved (Achieved Target? = Yes) for any investment option, stop the table there (i.e., don’t display further options).
    * Also, skip Section 2 entirely — no need to show alternative scenarios

The investment options to consider are:
{investment_options}

Table format:
| Investment Option | Expected Return (%) | Future Value at {tenure} Years (₹) | Achieved Target? | Suggestions if Target is Not Met |
|-------------------|---------------------|-------------------------------------|------------------|----------------------------------|
| <option>          | <range>             | <value>                             | Yes/No/Maybe     | <suggestions> |

---
### 2. To Reach ₹{goal_amount} in {tenure} Years
Show **two scenarios**:

1. **Required for {tenure} Years Goal**  
   - Calculate the required monthly contribution to reach the goal in the given tenure.  
   - Show a single row for this case.  

Format both scenarios into tables.

**Scenario 1: Required for {tenure} Years Goal**

| Monthly Contribution (₹) | Estimated Value (₹) | Duration (Years) | Return Assumption | 
|---------------------------|---------------------|------------------|-------------------|
| <calculated amount>       | <future value>      | {tenure}         | <return rate>     | 

---

**Scenario 2: With Provided Contribution (₹{monthly_contribution})**
 {goal_duration}

---

### 3. Risk Details
**Risk Level:** {risk_tolerance}
**Risk Notes:** If the user’s risk tolerance is High, explain that they can consider investment options across Low, Medium, and High risk levels.
If the risk tolerance is Medium, recommend only Low and Medium risk options, and advise caution against high-risk investments.
If the risk tolerance is Low, recommend only Low-risk options and explicitly advise avoiding medium and high-risk investments to protect their capital.
Make sure the explanation is clear, friendly, and tailored to guide the user toward suitable investments based on their risk appetite.
---------
### 4. By Market Capitalization:

{formatted_allocation_table}

Would you like me to suggest specific mutual funds or ETFs that match this allocation?

Important:
- All values are for the full tenure, factoring in monthly contributions & compounding.
- Never show formulas, only the results.
- Always include the Goal Feasibility section.
- Alternate suggestions must be realistic (aligned with risk tolerance).
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