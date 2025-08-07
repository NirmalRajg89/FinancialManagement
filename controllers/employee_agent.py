import streamlit as st
import os
import json
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage

os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

# Load model using LangChain
llm = ChatOpenAI(model_name="gpt-4", temperature=0.3)


def load_customer_data(file_path="data/customer.json"):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def get_user_summary_data(name, data):
    print(name)
    if name not in data:
        return None, "Name not found in data."

    user = data[name]
    employment = user.get("employment", {})
    credit_score = employment.get("creditScore", "N/A")
    monthly_income = employment.get("monthlyIncomeAmount", 0)

    total_assets = sum(asset.get("total", 0) for asset in user.get("assets", []))
    total_liabilities = sum(liab.get("unpaidBalanceAmount", 0) for liab in user.get("liabilities", []))

    summary = {
        "Name": name,
        "Credit Score": credit_score,
        "Monthly Income": f"${monthly_income:,.2f}",
        "Total Assets": f"${total_assets:,.2f}",
        "Total Liabilities": f"${total_liabilities:,.2f}"
    }

    return {
        "name": name,
        "credit_score": credit_score,
        "monthly_income": monthly_income,
        "total_assets": total_assets,
        "total_liabilities": total_liabilities,
        "summary": summary
    }, None


def generate_financial_summary_langchain(name, credit_score, total_assets, total_liabilities):
    prompt_template = ChatPromptTemplate.from_messages([
        ("system", "You are a financial analyst AI assistant."),
        ("human", """
            Provide a financial summary for the following user in markdown tables when appropriate:
            - Name: {name}
            - Credit Score: {credit_score}
            - Total Assets: ${total_assets}
            - Total Liabilities: ${total_liabilities}
            - Highlight his Financial Status (Good/Bad/Better/High/Worst) color highlight
            
            The summary should be concise and professional in 2-3 sentences. Provide suggestion to improve his financial wealth.
            """)
    ])

    message = prompt_template.format_messages(
        name=name,
        credit_score=credit_score,
        total_assets=total_assets,
        total_liabilities=total_liabilities
    )

    response = llm(message)
    return response.content