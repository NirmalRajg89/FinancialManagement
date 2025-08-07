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
