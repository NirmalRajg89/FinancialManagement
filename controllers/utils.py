import base64


def img_to_base64(image_path):
    """Convert image to base64."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        print(f"Error converting image to base64: {str(e)}")
        return None

def format_tenure(term_months):
    if not term_months:
        return "ongoing"
    years, months = divmod(term_months, 12)
    parts = []
    if years > 0:
        parts.append(f"{years} year{'s' if years > 1 else ''}")
    if months > 0:
        parts.append(f"{months} month{'s' if months > 1 else ''}")
    return " and ".join(parts)


def future_value_sip(p, r, n, t):
    return p * (((1 + r / n) ** (n * t) - 1) / (r / n)) * (1 + r / n)


def required_return(p, fv_target, n, t):
    """Find required annual return using binary search"""
    low, high = 0.0, 0.25  # 0% to 25% annual return
    for _ in range(100):  # iterate for precision
        mid = (low + high) / 2
        fv = future_value_sip(p, mid, n, t)
        if fv < fv_target:
            low = mid
        else:
            high = mid
    return mid * 100  # return in %


def add_indicators(df):
    df = df.copy()
    if df.at[0, "Credit Score"] >= 700:
        df.at[0, "Credit Score"] = f"{df.at[0, 'Credit Score']} ✅"
    elif df.at[0, "Credit Score"] >= 600:
        df.at[0, "Credit Score"] = f"{df.at[0, 'Credit Score']} ⚠️"
    else:
        df.at[0, "Credit Score"] = f"{df.at[0, 'Credit Score']} ❌"

    dti = float(str(df.at[0, "Debt-to-Income Ratio (%)"]).split()[0])
    if dti <= 30:
        df.at[0, "Debt-to-Income Ratio (%)"] = f"{dti}% ✅"
    elif dti <= 40:
        df.at[0, "Debt-to-Income Ratio (%)"] = f"{dti}% ⚠️"
    else:
        df.at[0, "Debt-to-Income Ratio (%)"] = f"{dti}% ❌"

    # net_worth = float(str(df.at[0, "Net Worth ($)"]).split()[0])
    # if net_worth > 0:
    #    df.at[0, "Net Worth ($)"] = f"{net_worth} ✅"
    # else:
    #    df.at[0, "Net Worth ($)"] = f"{net_worth} ❌"

    return df


def calculate_risk_tolerance(profile: dict) -> str:
    """Derive risk tolerance from credit score, income, liabilities, and assets."""

    emp = profile.get("employment", {})
    credit = emp.get("creditScore", 600)
    income = emp.get("monthlyIncomeAmount", 0)

    # liabilities: sum monthly payments
    liabilities = profile.get("liabilities", [])
    monthly_debt = sum(l.get("monthlyPaymentAmount", 0) for l in liabilities)

    # assets: sum liquid totals
    assets = profile.get("assets", [])
    liquid_assets = sum(a.get("total", 0) for a in assets)

    # ratios
    dti = monthly_debt / income if income else 1
    months_of_cushion = liquid_assets / income if income else 0

    # base level from credit
    if credit < 600:
        level = 1  # Low
    elif 600 <= credit <= 720:
        level = 2  # Moderate
    else:
        level = 3  # High

    # adjust by cushion
    if months_of_cushion < 3:
        level = max(1, level - 1)
    elif months_of_cushion > 12:
        level = min(3, level + 1)

    # adjust by DTI
    if dti > 0.4:
        level = max(1, level - 1)

    return {1: "Low", 2: "Moderate", 3: "High"}[level]


def get_tolerance(risk_tolerance: str):

    if risk_tolerance == "Low":
        result = f"""
            ### 🟢 Risk Tolerance: **{risk_tolerance}**
            - You prefer safer investments with minimal volatility.  
            - Focus on **capital protection** and stable returns.  
        """
    elif risk_tolerance == "Moderate":
        result = f"""
            ### 🟡 Risk Tolerance: **{risk_tolerance}**
            - You are open to **balanced growth** with some risk.  
            - Diversified mix of equity and fixed income is recommended.  
        """
    else:  # High
        result = f"""
            ### 🔴 Risk Tolerance: **{risk_tolerance}**
            - You are comfortable with **higher volatility** for potentially higher rewards.  
            - Consider aggressive growth strategies with equity focus.  
        """

    return result


# Risk tolerance data
formula_df =([
    {"Risk Level": "High", "Credit Score": "> 700", "Debt Ratio": "< 40%",
     "Savings Condition": "Has savings > 0", "Interpretation": "Aggressive (Equity, Index Funds)."},
    {"Risk Level": "Moderate", "Credit Score": "650 – 700", "Debt Ratio": "40% – 70%",
     "Savings Condition": "Emergency fund only", "Interpretation": "Balanced (Debt + Equity)."},
    {"Risk Level": "Low", "Credit Score": "< 650", "Debt Ratio": "≥ 100%",
     "Savings Condition": "No savings", "Interpretation": "Conservative (FDs, Bonds)."},
])


# Function to get risk tolerance summary
def get_tolerance(risk_tolerance: str):
    # Filter the DataFrame based on the selected risk tolerance
    risk_row = formula_df[formula_df["Risk Level"] == risk_tolerance].iloc[0]

    # Format the result for Streamlit UI
    result = f"""
        ### Risk Tolerance: **{risk_tolerance}**
        - **Credit Score**: {risk_row['Credit Score']}
        - **Debt Ratio**: {risk_row['Debt Ratio']}
        - **Savings Condition**: {risk_row['Savings Condition']}

        **Interpretation**:
        {risk_row['Interpretation']}
    """

    return result


# Function to get risk tolerance summary
def get_tolerance_v1(risk_tolerance, formula_df ):
    # Filter the DataFrame based on the selected risk tolerance
    risk_row = formula_df[formula_df["Risk Level"] == risk_tolerance].iloc[0]

    # Format the result for Streamlit UI
    result = f"""
        ### Risk Tolerance: **{risk_tolerance}**
        - **Credit Score**: {risk_row['Credit Score']}
        - **Debt Ratio**: {risk_row['Debt Ratio']}
        - **Savings Condition**: {risk_row['Savings Condition']}

    """

    return result
