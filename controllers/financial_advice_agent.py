import json
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI

from models.portfolio_optimizer import portfolio_optimizer


# SIP future value calculation
def future_value_sip(monthly_investment, annual_return, months):
    monthly_rate = (1 + annual_return) ** (1 / 12) - 1
    fv = monthly_investment * (((1 + monthly_rate) ** months - 1) / monthly_rate) * (1 + monthly_rate)
    return fv

# Generate Investment Diversification Markdown table
def generate_portfolio_diversification_table(monthly_contribution, monthsCount, funds_data, goal, funds, top_n=2):
    # Run optimizer
    df_top, req_return = portfolio_optimizer(monthly_contribution, monthsCount, goal, funds, top_n=top_n)
    if df_top.empty:
        return "💹 No feasible allocations found."

    table = "#### 💹 Investment Diversification\n\n"
    table += "| Instrument Name | Type | Allocation % | Monthly Investment ($) | Expected Return (%) | Risk Level | Future Value ($) |\n"
    table += "|-----------------|------|--------------|----------------------|------------------|-----------|----------------|\n"

    top_row = df_top.iloc[0]

    # Extract allocations from the optimizer output
    weights = {
        item.split(":")[0].strip(): float(item.split(":")[1].strip().replace("%", "")) / 100
        for item in top_row["Weights"].split(";")
    }

    for alloc_name, alloc_pct in weights.items():
        # Calculate split: divide allocation equally between 2 funds
        split_pct = alloc_pct / 2

        # Determine category and pick top 2 matching instruments
        instruments = []
        fund_type = "Other"

        if "Equity" in alloc_name or "Mutual" in alloc_name:
            category = "Equity Mutual Funds"
            if category in funds_data:
                sorted_funds = sorted(
                    funds_data[category].items(),
                    key=lambda x: -x[1]["return"]
                )[:2]
                fund_type = "Mutual Fund"
                instruments = [(f[0], f[1]["return"], f[1]["risk"]) for f in sorted_funds]

        elif "Index" in alloc_name:
            category = "Index Funds"
            if category in funds_data:
                sorted_indexes = sorted(
                    funds_data[category].items(),
                    key=lambda x: -x[1]["return"]
                )[:2]
                fund_type = "Index Fund"
                instruments = [(f[0], f[1]["return"], f[1]["risk"]) for f in sorted_indexes]

        elif "Stock" in alloc_name:
            category = "Stocks"
            if category in funds_data:
                all_stocks = []
                for sector_name, sector_data in funds_data["Stocks"].items():
                    # sector_data now has 'Expected Return' and 'stocks'
                    stocks_dict = sector_data.get("stocks", {})
                    for stock_name, stock_info in stocks_dict.items():
                        all_stocks.append((f"{sector_name} ({stock_name})", stock_info["return"], stock_info["risk"]))
                sorted_stocks = sorted(all_stocks, key=lambda x: -x[1])[:2]
                fund_type = "Stock"
                instruments = sorted_stocks

        # Fallback: use alloc_name itself if no instruments found
        if not instruments:
            instruments = [(alloc_name, funds.get(alloc_name, 0.08), "Moderate")]

        # --- Calculate monthly investment and future value per instrument ---
        for name, expected_return, risk in instruments:
            monthly_investment = monthly_contribution * split_pct
            future_value = future_value_sip(monthly_investment, expected_return, monthsCount)
            table += (
                f"| {name} | {fund_type} | {split_pct*100:.1f}% "
                f"| ${monthly_investment:,.2f} | {expected_return*100:.2f}% | {risk} | ${future_value:,.2f} |\n"
            )

    return table

def generate_refinance_options_table():
    """
    Generate a Markdown table for refinancing options.
    refinance_data: list of dicts with keys: loan_type, rate, apr, points, payment
    """
    refinance_data = [
        {"loan_type": "30-year Fixed Conventional", "rate": 6.125, "apr": 6.380, "points": 0.975,
         "points_value": "$3,240.00", "payment": 1825.40},
        {"loan_type": "30-year Jumbo Fixed", "rate": 6.450, "apr": 6.720, "points": 1.150, "points_value": "$4,870.00",
         "payment": 4925.65},
        {"loan_type": "20-year Fixed Conventional", "rate": 5.980, "apr": 6.210, "points": 1.025,
         "points_value": "$3,580.00", "payment": 2178.30},
        {"loan_type": "15-year Fixed", "rate": 5.450, "apr": 5.720, "points": 0.995, "points_value": "$2,990.00",
         "payment": 2480.15},
        {"loan_type": "FHA Loan (Refinance)", "rate": 5.650, "apr": 6.280, "points": 1.125, "points_value": "$3,240.00",
         "payment": 1589.70},
        {"loan_type": "VA Loan (Refinance)", "rate": 5.480, "apr": 5.820, "points": 1.050, "points_value": "$3,050.00",
         "payment": 1725.10},
    ]

    table = "#### Refinance Options\n\n"
    table += "| Loan Type | Rate | APR | Points | Monthly Payment |\n"
    table += "|------------|------|------|---------|----------------|\n"

    for loan in refinance_data:
        points_str = f"{loan['points']} ({loan['points_value']})" if 'points_value' in loan else str(loan['points'])
        table += (
            f"| {loan['loan_type']} | {loan['rate']}% | {loan['apr']}% "
            f"| {points_str} | ${loan['payment']:,.2f} |\n"
        )

    return table


class AdvisorAgent:
    """Wrapper around AgentExecutor so we can safely add custom methods."""
    def __init__(self, executor, funds_data=None, monthly_contribution=None, tenure_months=None, goal=None, funds=None):
        self.executor = executor
        self.funds_data = funds_data
        self.monthly_contribution = monthly_contribution
        self.tenure_months = tenure_months
        self.goal = goal
        self.funds = funds

    def ask(self, input_dict):
        # Dynamically generate table
        if self.funds_data and self.monthly_contribution and self.tenure_months and self.goal and self.funds:
            input_dict["generate_portfolio_diversification_table"] = generate_portfolio_diversification_table(
                monthly_contribution=self.monthly_contribution,
                monthsCount=self.tenure_months,
                funds_data=self.funds_data,
                goal=self.goal,
                funds=self.funds
            )
            input_dict["generate_refinance_options_table"] = generate_refinance_options_table()

        result = self.executor.invoke(input_dict)
        return result.get("output", result)
def create_financial_advice_agent(static_vars: dict):
    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0.3)

    base_prompt = ChatPromptTemplate.from_messages([
        ("system", """
You are a financial assistant for Guaranteed Rate, providing concise, actionable advice on Mortgage, HELOC, Refinancing, and Investment products.

---

### INPUT VARIABLES
- {plan_type}: "Short-term" or "Long-term"
- {goals}: Short-term: [education, car, bike, emergency fund]; Long-term: [retirement, home]
- {monthly_contribution}: numeric value
- {assets}, {cash_reserves}, {liabilities}, {has_house_asset}
- {mortgage_info_url}, {heloc_info_url}, {refinance_info_url}
- {investment_options}
- {analysis_summary} (optional)
- {req_return}: required return (%) for goal
- {risk_as_per_tenure_and_goal}: ["Low", "Moderate", "High", "Very High", "Unrealistic"]
- {funds_data}: list of available Stocks, Mutual Funds, Index Funds
- {emergency_fund_amount}: numeric value, existing emergency fund 
---

### LOGIC AND RULES

#### Short-term Plans
- Focus on liquidity and capital safety.
- Consider the {req_return}:
    - if {req_return} greater than 8%. Focus to invest on higher risk (10%-20% returns) like Mutual Funds or Index Funds or Stocks.
    - if {req_return} less than 8%. Focus to invest on higher risk (10%-20% returns) like Mutual Funds or Index Funds or Stocks and partial investment in Debt Mutual Funds or Recurring Deposits.
- Suggest diversification of funds.
- If liabilities exist: recommend Refinancing.
- If {has_house_asset} and home not in liabilities mortgage, suggest HELOC.
- Build 6 months emergency fund if {emergency_fund_amount} is lower than {monthly_contribution}.

#### Long-term Plans
- If {goals} is Home: if goal unmet → suggest Mortgage; if has house → HELOC with Mortgage.
- If {goals} is Retirement: diversify partially in PPF, Equity Mutual Funds, Index Funds; Stocks, HELOC for emergency if has {has_house_asset}.
- If liabilities > 0 → advise Refinancing.
- Align advice with {req_return}.

#### Investment Diversification
Include  the table provided in {generate_portfolio_diversification_table}.

# #### Guaranteed Rate Services
# - Consider suggestions of short-term & Long-term Plans logics created earlier.
# - If liabilities exist → recommend **Refinancing** via ([Learn more]({refinance_info_url})). 
# - Build 6 months emergency fund if {emergency_fund_amount} is lower than {monthly_contribution}. 
# - If {has_house_asset} = True -> HELOC can provide emergency liquidity.
# - If liabilities exist → advise **Refinancing** for lower rates ([Learn more]({refinance_info_url})).
# - **For “Home” goal:** - Suggest **Mortgage** via ({mortgage_info_url}). 
#     - If {has_house_asset} = True → offer **HELOC** via ([Learn more]({heloc_info_url})) as backup liquidity. 
# - **For “Retirement” goal:** - Suggest portfolio diversification: PPF, MF (Equity/Hybrid), Index Funds. 
#     - If {has_house_asset} = True → HELOC can provide emergency liquidity. 
# - If refinancing is advised, Include the table provided in {generate_refinance_options_table}
# ---

#### Guaranteed Rate Services
- Follow suggestions of short-term & long-term plan logics.
- If liabilities exist → recommend **Refinancing** via ({refinance_info_url}).
  - Include table from {generate_refinance_options_table} if refinancing is suggested.
- If {emergency_fund_amount} < {monthly_contribution} → recommend building a 6-month emergency fund. Suggest HELOC if "home" is in {assets}.
- **For “Home” goal:** 
  - Suggest **Mortgage** via ({mortgage_info_url}).
  - If {has_house_asset} = True or "home" in {assets} → suggest **HELOC** via ({heloc_info_url}) as backup liquidity.
- **For “Retirement” goal:** 
  - Suggest portfolio diversification: PPF, Mutual Funds (Equity/Hybrid), Index Funds.
  - Suggest **HELOC** only if {has_house_asset} = True or "home" is in {assets}.
- Do not reference ownership status explicitly; only suggest items if conditions are satisfied.

### OUTPUT RULES
- Output only **Markdown bullet points and tables**, grouped under:
  - 🕒 Short-term Plan Recommendations
  - 🏦 Long-term Plan Recommendations
  - 💹 Investment Diversification
  - 🏠 Guaranteed Rate Services
- Suggestions: 1–2 lines, clear and actionable.
- Include relevant links where applicable.
- Never show formulas or internal calculations.

"""),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{analysis_summary}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    prompt = base_prompt.partial(**static_vars)
    agent = create_openai_tools_agent(llm=llm, prompt=prompt, tools=[])

    executor = AgentExecutor(agent=agent, tools=[], verbose=True, return_intermediate_steps=False)

    advisor = AdvisorAgent(
        executor=executor,
        funds_data=static_vars.get("funds_data"),
        monthly_contribution=float(static_vars.get("monthly_contribution")),
        tenure_months=int(static_vars.get("tenure_months")),
        goal=float(static_vars.get("goal_amount")),
        funds={
        # "Bank Savings Account": 0.035,
        # "Recurring Deposit": 0.06,
        # "Public Provident Fund": 0.075,
        "Equity Mutual Funds": 0.10,
        "Index Funds": 0.125,
        "Stock Market": 0.175
    }
    )

    return advisor
