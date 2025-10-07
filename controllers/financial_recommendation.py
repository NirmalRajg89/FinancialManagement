import pandas as pd


def calculate_investment_plan(goal_summary, contribution_split):
    """
    Calculate detailed investment plan based on goal summary and contribution splits.

    Parameters:
    - goal_summary: dict with keys
        - 'Goal'
        - 'Plan Type'
        - 'Tenure (years)'
        - 'Monthly Contribution ($)'
        - 'Goal Amount ($)'
    - contribution_split: dict mapping Investment Category to percentage allocation (0-1)

    Returns:
    - pd.DataFrame with detailed breakdown including:
        Investment Category, Investment Option, % of Monthly Contribution, Monthly Contribution ($),
        Total Invested ($), Return Assumption (%), Effective Annual Return (%), Total Sum ($)
    """

    tenure_years = goal_summary["Tenure (years)"]
    total_monthly_contribution = goal_summary["Monthly Contribution ($)"]

    # Sub-splits for each category (percentages sum to 1 within each category)
    stocks_split = {
        "Gold": 0.10,
        "Electric Vehicles (EV)": 0.10,
        "Pharma": 0.10,
    }

    mutual_funds_split = {
        "Growth Fund XYZ (Large Cap)": 0.40,
        "Equity Income Fund ABC (Mid Cap)": 0.35,
        "Emerging Markets Fund Q (Small Cap)": 0.25,
    }

    others_split = {
        "Gold": 0.25,
        "Real Estate": 0.75,
    }

    savings_rd_split = {
        "ICICI RD": 0.50,
        "HDFC RD": 0.50,
    }

    # Return assumptions and effective annual return per investment option
    return_info = {
        # Stocks
        "Gold": {"Return Assumption (%)": "3–7", "Effective Annual Return (%)": 4.87},
        "Electric Vehicles (EV)": {"Return Assumption (%)": "15–20", "Effective Annual Return (%)": 18.97},
        "Pharma": {"Return Assumption (%)": "10–12", "Effective Annual Return (%)": 11.0},

        # Mutual Funds
        "Growth Fund XYZ (Large Cap)": {"Return Assumption (%)": "8–12", "Effective Annual Return (%)": 10.47},
        "Equity Income Fund ABC (Mid Cap)": {"Return Assumption (%)": "7–10", "Effective Annual Return (%)": 8.5},
        "Emerging Markets Fund Q (Small Cap)": {"Return Assumption (%)": "12–15", "Effective Annual Return (%)": 13.5},

        # Others
        "Real Estate": {"Return Assumption (%)": "7–8", "Effective Annual Return (%)": 7.76},

        # Savings & RD
        "ICICI RD": {"Return Assumption (%)": "5–7", "Effective Annual Return (%)": 6.0},
        "HDFC RD": {"Return Assumption (%)": "5–7", "Effective Annual Return (%)": 6.0},
    }

    def future_value_monthly(P, r, n, t):
        """Calculate future value of monthly investments"""
        if r == 0:
            return P * n * t
        return P * (((1 + r / n) ** (n * t) - 1) / (r / n))

    records = []

    for category, cat_pct in contribution_split.items():
        if category == "Stock Market":
            sub_split = stocks_split
        elif category == "Equity Mutual Funds":
            sub_split = mutual_funds_split
        elif category == "Others":
            sub_split = others_split
        else:  # Savings & RD
            sub_split = savings_rd_split

        for investment_option, sub_pct in sub_split.items():
            total_pct = cat_pct * sub_pct
            monthly_cont = total_monthly_contribution * total_pct
            total_invested = monthly_cont * 12 * tenure_years
            r_annual = return_info.get(investment_option, {}).get("Effective Annual Return (%)", 0) / 100
            r_assumption = return_info.get(investment_option, {}).get("Return Assumption (%)", "N/A")

            total_sum = future_value_monthly(monthly_cont, r_annual, 12, tenure_years)

            records.append({
                "Investment Category": category,
                "Investment Option": investment_option,
                "% of Monthly Contribution": f"{total_pct * 100:.2f}%",
                "Monthly Contribution ($)": round(monthly_cont, 2),
                "Total Invested ($)": round(total_invested, 2),
                "Return Assumption (%)": r_assumption,
                "Effective Annual Return (%)": round(r_annual * 100, 2),
                "Total Sum ($)": round(total_sum, 2),
            })

    df = pd.DataFrame(records)

    # Sort by Effective Annual Return ascending
    df = df.sort_values(by="Effective Annual Return (%)", ascending=True).reset_index(drop=True)

    return df
