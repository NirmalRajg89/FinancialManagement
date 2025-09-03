import streamlit as st
import pandas as pd
import math


def generate_investment_strategy(monthly_income, credit_score, total_assets, total_liabilities):
    disposable_income = monthly_income - (total_liabilities if total_liabilities else 0)

    # Short-Term
    emergency_fund_min = monthly_income * 3
    emergency_fund_max = monthly_income * 6

    # Medium-Term
    medium_term_investment = disposable_income * 0.20  # 20% of disposable income
    projection_10yr = medium_term_investment * 12 * 10 * 1.08  # rough 10-yr growth

    # Long-Term
    retirement_contribution = disposable_income * 0.10  # 10% of disposable income

    return {
        "emergency_fund_min": emergency_fund_min,
        "emergency_fund_max": emergency_fund_max,
        "medium_term_investment": medium_term_investment,
        "projection_10yr": projection_10yr,
        "retirement_contribution": retirement_contribution,
    }


# Function: Display investment strategy (UI only)
def display_investment_strategy(strategy):
    st.markdown("### 📊 Investment Strategy Overview")

    data = {
        "Term": ["Short-Term", "Medium-Term", "Long-Term"],
        "Category": [
            "Emergency Fund",
            "ETF / Index Funds",
            "401(k) / IRA / REITs",
        ],
        "Contribution ($)": [
            f"${strategy['emergency_fund_min']:,.0f} – ${strategy['emergency_fund_max']:,.0f}",
            f"${strategy['medium_term_investment']:,.0f}/month",
            f"${strategy['retirement_contribution']:,.0f}/month",
        ],
        "10-Year Projection ($)": [
            "N/A",
            f"${strategy['projection_10yr']:,.0f}",
            "Depends on retirement plan growth",
        ],
        "Goal": [
            "Liquidity + safety for unexpected events",
            "Wealth accumulation & steady growth",
            "Retirement assets & financial independence",
        ],
    }

    st.table(pd.DataFrame(data))


def calculate_goal_duration(monthly_contribution, goal_amount):
    """
    Calculate how many years it will take to reach the goal amount
    under different investment return assumptions.
    """

    results = []

    # Parse investment options
    options = [
        ("Bank Savings Account", (3, 4)),
        ("Recurring Deposit", (5, 7)),
        ("Public Provident Fund", (7, 8)),
        ("Equity Mutual Funds", (8, 12)),
        ("Index Funds", (10, 15)),
        ("Stock Market", (15, 20))
    ]

    for name, (low, high) in options:
        return_rates = [(low + high) / 2]  # use average return assumption
        for rate in return_rates:
            annual_rate = rate / 100
            monthly_rate = annual_rate / 12

            months = 0
            future_value = 0

            # Compound monthly contributions until goal reached
            while future_value < goal_amount and months < 100 * 12:  # cap 100 years
                months += 1
                future_value = monthly_contribution * ((1 + monthly_rate) ** months - 1) / monthly_rate

            years = math.ceil(months / 12)  # round UP to nearest year

            results.append({
                "Investment Option": name,
                "Return Assumption": f"{low}–{high}%",
                "Duration to Reach Goal (Years)": years if future_value >= goal_amount else "Not achievable"
            })

    # Convert to DataFrame for nice table format
    df = pd.DataFrame(results)
    return df
