import streamlit as st
import pandas as pd
import math

def color_monthly_contribution(val, threshold):
    color = 'red' if val > threshold else 'green'
    return f'color: {color}'

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


def calculate_monthly_contribution(goal_amount, duration, plan_type, monthly_contribution):
    """
    Calculate monthly contribution to reach goal amount over duration.

    For compound interest instruments: calculate based on monthly compounding.
    For simple interest instruments: calculate based on simple interest assumption.

    Parameters:
    - goal_amount: target maturity amount
    - duration: years (if long-term) or months (if short-term)
    - plan_type: "Long-term" or "Short-term"

    Returns:
    - DataFrame with investment options and monthly contributions
    """
    results = []
    # Investment options with interest type
    options = [
        ("Bank Savings Account", (3, 4), "compound"),
        ("Recurring Deposit", (5, 7), "compound"),
        ("Public Provident Fund", (7, 8), "compound"),
        ("Equity Mutual Funds", (8, 12), "compound"),
        ("Index Funds", (10, 15), "compound"),
        ("Stock Market", (15, 20), "compound")
    ]

    # Convert duration to months
    if plan_type.lower() == "long-term":
        duration_months = duration * 12
    else:
        duration_months = duration

    duration_years = duration_months / 12

    for name, (low, high), interest_type in options:
        avg_return_annual = (low + high) / 2
        monthly_rate = (avg_return_annual / 100) / 12

        if interest_type == "compound":
            # compound interest monthly contribution formula
            if monthly_rate == 0:
                monthly_calculated_contribution = goal_amount / duration_months
            else:
                monthly_calculated_contribution = goal_amount * monthly_rate / ((1 + monthly_rate) ** duration_months - 1)

            effective_annual_return = round(((1 + monthly_rate) ** 12 - 1) * 100, 2)
            compounding_note = "Monthly Compounding"

        else:  # simple interest
            # Simple interest total interest = P * r * t
            # Goal = Principal + Interest = P + P*r*t = P*(1 + r*t)
            # Solve for Principal (P)
            total_rate = avg_return_annual / 100 * duration_years
            principal = goal_amount / (1 + total_rate)
            monthly_calculated_contribution = principal / duration_months
            effective_annual_return = round(avg_return_annual, 2)
            compounding_note = "Simple Interest"

        duration_value = duration_months if plan_type.lower() == 'short_term' else duration_years

        results.append({
            "Investment Option": name,
            "Return Assumption (%)": f"{low}–{high}",
            "Effective Annual Return (%)": effective_annual_return,
            # "Interest Type": compounding_note,
            "Monthly Contribution": round(monthly_calculated_contribution, 2),
            "Duration": round(duration_value, 2),  # months or years based on plan_type
            "Goal Amount": round(goal_amount, 2),
            "Recommended": "Yes" if monthly_contribution > monthly_calculated_contribution else "No"
        })

    df = pd.DataFrame(results)

    # Rename the Duration column to include unit
    duration_unit = "Months" if plan_type.lower() == 'short-term' else "Years"
    df.rename(columns={"Duration": f"Duration ({duration_unit})"}, inplace=True)

    return df
    # st.session_state.df_data = df  # raw DataFrame is JSON-serializable
    #
    # threshold = monthly_contribution
    # # Apply color styling to Monthly Contribution
    # def color_monthly_contribution(val):
    #     color = 'red' if val > int(threshold) else 'green'
    #     return f'color: {color}; font-weight: bold'
    #
    # st.dataframe(df.style.applymap(color_monthly_contribution, subset=['Monthly Contribution']))


def calculate_risk_tolerance_v1(customer_data: dict) -> dict:
    """
    Core logic for risk tolerance classification and contribution calculation.

    Returns:
        dict with 'risk_level' and 'monthly_contribution'
    """
    credit_score = customer_data["credit_score"]
    # monthly_salary = customer_data["monthly_salary"]
    Debt_to_Income_Ratio = customer_data["Debt_to_Income_Ratio"]
    # savings_amount = customer_data["savings_amount"]

    debt_ratio = Debt_to_Income_Ratio

    # Determine risk level
    if credit_score > 700 and debt_ratio < 40 :
        risk_level = "High"
    elif 650 <= credit_score <= 700 and 40 <= debt_ratio <= 70:
        risk_level = "Moderate"
    else:
        risk_level = "Low"

    # Contribution mapping
    # risk_contribution_percent = {
    #     "High": 0.70,
    #     "Moderate": 0.50,
    #     "Low": 0.30
    # }

    # contribution = monthly_salary * risk_contribution_percent[risk_level]

    return {
        "risk_level": risk_level,
        # "monthly_contribution": round(contribution, 2)
    }
