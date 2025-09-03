from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda

from langchain.chat_models import ChatOpenAI

llm = ChatOpenAI(model="gpt-4")

investment_plan_prompt = ChatPromptTemplate.from_template("""
You are a certified financial advisor helping clients plan investments.

Client Profile:
- Monthly Income: ${monthly_income}
- Credit Score: ${credit_score}
- Cash Available: ${cash_assets}
- Liabilities: ${liabilities}
- Debt-to-Income Ratio: ${dti}
- Monthly Contribution Available: ${monthly_contribution}
- Risk Tolerance: ${risk_tolerance}
- Financial Goals: ${goals}

Highlights:
Provide basic inputs on Client financial status.
we need to advise the stocks bases in Client financial data

Instructions:
1. Suggest a tailored investment strategy (based on goals + risk)
2. Recommend asset allocation: (% in stocks, bonds, real estate, cash)
3. Suggest investment types (e.g., ETFs, IRAs, short-term funds)
4. Provide warnings or suggestions (e.g., debt reduction, emergency fund)

Be practical, data-driven, and goal-specific. No generic suggestions.
""")
def calculate_dti(monthly_income, liabilities):
    total_debt_payments = sum([l['monthlyPaymentAmount'] for l in liabilities])
    return total_debt_payments / monthly_income if monthly_income else 0

def get_risk_profile(credit_score, dti, savings):
    if credit_score >= 740 and dti < 0.3 and savings > 10000:
        return "moderate"
    elif credit_score >= 680:
        return "cautious"
    else:
        return "high_risk"
def parse_combined_data(input_data):
    profile = input_data["profile"]
    user_inputs = input_data["user_inputs"]

    employment = profile["employment"]
    assets = profile["assets"]
    liabilities = profile["liabilities"]

    monthly_income = employment["monthlyIncomeAmount"]
    credit_score = employment["creditScore"]
    cash_assets = sum([a["total"] for a in assets])
    dti = calculate_dti(monthly_income, liabilities)
    system_risk = get_risk_profile(credit_score, dti, cash_assets)

    # Merge static + user input risk
    risk_tolerance = user_inputs["risk_tolerance"] or system_risk

    return {
        "monthly_income": monthly_income,
        "credit_score": credit_score,
        "cash_assets": cash_assets,
        "liabilities": liabilities,
        "dti": round(dti, 2),
        "risk_tolerance": risk_tolerance,
        "goals": ", ".join(user_inputs["goals"]),
        "monthly_contribution": user_inputs["monthly_contribution"]
    }

def build_agent():
    return (
        RunnableLambda(parse_combined_data)
        | investment_plan_prompt
        | llm
    )

chat_prompt = ChatPromptTemplate.from_template("""
You are a helpful financial advisor.
The client's profile is:
{profile}

Answer the question:
{question}

Your answers must be based ONLY on the profile data provided, not generic advice unless necessary.
""")

def build_chat_agent():
    return chat_prompt | llm



def get_dynamic_allocation(risk_tolerance: str, monthly_contribution: int):
    base_allocation = {
        "low": {"large": 80, "mid": 15, "small": 5},
        "moderate": {"large": 60, "mid": 25, "small": 15},
        "high": {"large": 40, "mid": 35, "small": 25},
    }

    allocation = base_allocation.get(risk_tolerance.lower(), base_allocation["moderate"])

    if monthly_contribution < 10000:
        shift = min(10, allocation["small"])
        allocation["large"] += shift
        allocation["small"] -= shift
    elif monthly_contribution > 50000:
        shift = 5
        allocation["small"] += shift
        allocation["large"] -= shift

    total = sum(allocation.values())
    if total != 100:
        diff = 100 - total
        allocation["mid"] += diff

    return allocation


def format_allocation_table(allocation: dict, monthly_contribution: int) -> str:
    example_stocks = {
        "large": ["HDFC Bank", "Infosys", "TCS"],
        "mid": ["Tata Elxsi", "Page Industries"],
        "small": ["Suzlon Energy", "Tejas Networks"]
    }

    def format_inr(value):
        return f"₹{value:,.0f}"

    table = f"""
| Market Cap Segment | Suggested Allocation (%) | Amount Range ($) | Investment Style           | Example Stocks/ETFs               |
|--------------------|--------------------------|------------------|-----------------------------|-----------------------------------|
| Large-cap          | {allocation["large"]}%                      | {format_inr(monthly_contribution * allocation["large"] / 100)}         | Stable, lower-risk          | {', '.join(example_stocks["large"])}           |
| Mid-cap            | {allocation["mid"]}%                      | {format_inr(monthly_contribution * allocation["mid"] / 100)}         | Moderate risk, growth focus | {', '.join(example_stocks["mid"])}       |
| Small-cap          | {allocation["small"]}%                      | {format_inr(monthly_contribution * allocation["small"] / 100)}         | High growth, high volatility| {', '.join(example_stocks["small"])}     |
""".strip()

    return table