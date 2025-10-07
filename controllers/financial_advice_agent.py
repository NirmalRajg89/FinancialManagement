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
    table += "| Instrument Name | Type | Allocation % | Monthly Investment ($) | Expected Return (%) | Future Value ($) |\n"
    table += "|-----------------|------|--------------|----------------------|------------------|----------------|\n"

    top_row = df_top.iloc[0]

    # Extract allocations from the optimizer output
    weights = {
        item.split(":")[0].strip(): float(item.split(":")[1].strip().replace("%", "")) / 100
        for item in top_row["Weights"].split(";")
    }

    for alloc_name, alloc_pct in weights.items():
        # Expected return suggested by optimizer for this instrument type
        expected_return = funds.get(alloc_name, 0.08)
        fund_type = "Other"
        instrument_name = None

        # --- Find closest matching real instrument by return ---
        if "Equity" in alloc_name or "Mutual" in alloc_name:
            category = "Equity Mutual Funds"
            if category in funds_data:
                closest_fund = min(
                    funds_data[category].items(),
                    key=lambda x: abs(x[1]["return"] - expected_return)
                )
                instrument_name = closest_fund[0]
                expected_return = closest_fund[1]["return"]
                fund_type = "Mutual Fund"

        elif "Index" in alloc_name:
            category = "Index Funds"
            if category in funds_data:
                closest_index = min(
                    funds_data[category].items(),
                    key=lambda x: abs(x[1]["return"] - expected_return)
                )
                instrument_name = closest_index[0]
                expected_return = closest_index[1]["return"]
                fund_type = "Index Fund"

        elif "Stock" in alloc_name:
            category = "Stocks"
            if category in funds_data:
                # Search all sectors under Stocks
                all_stocks = []
                for sector, stocks in funds_data[category].items():
                    for sname, sinfo in stocks.items():
                        all_stocks.append((sector, sname, sinfo["return"]))
                if all_stocks:
                    closest_stock = min(
                        all_stocks,
                        key=lambda x: abs(x[2] - expected_return)
                    )
                    sector, sname, ret = closest_stock
                    instrument_name = f"{sector} ({sname})"
                    expected_return = ret
                    fund_type = "Stock"

        # If still not found, fallback to generic
        if instrument_name is None:
            instrument_name = alloc_name

        # --- Calculate investments ---
        monthly_investment = monthly_contribution * alloc_pct
        future_value = future_value_sip(monthly_investment, expected_return, monthsCount)

        table += (
            f"| {instrument_name} | {fund_type} | {alloc_pct*100:.1f}% "
            f"| ${monthly_investment:,.2f} | {expected_return*100:.2f}% | ${future_value:,.2f} |\n"
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

---

### LOGIC AND RULES

#### Short-term Plans
- Focus on liquidity and capital safety.
- Prioritize Bank Savings, Recurring Deposits, or Liquid Funds.
- Extra liquidity: small % (10–20%) in conservative Mutual Funds or Index Funds.
- If liabilities exist: recommend Refinancing.
- Build 6 months emergency fund.

#### Long-term Plans
- Home: if goal unmet → suggest Mortgage; if has house → HELOC.
- Retirement: diversify in PPF, Equity/Hybrid Mutual Funds, Index Funds; HELOC for emergency if has house.
- If liabilities > 0 → advise Refinancing.
- Align advice with {req_return}.

#### Investment Diversification
Include  the table provided in {generate_portfolio_diversification_table}.

#### Guaranteed Rate Services
- Short-term: liquidity, RD/Liquid Funds, optional small MF/Index allocation, Refinancing if liabilities.
- Long-term: Mortgage/HELOC for home, diversified retirement portfolio, Refinancing if liabilities.

---

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
