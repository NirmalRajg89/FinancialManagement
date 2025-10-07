import pandas as pd

def calc():
    # Given values
    monthly_contribution = 466  # PMT
    annual_interest_rate = 0.19  # 19%
    years = 20
    compounding_frequency = 12  # monthly

    # Derived values
    monthly_rate = annual_interest_rate / compounding_frequency

    # Create table
    data = []
    cumulative_contribution = 0

    for year in range(1, years + 1):
        months = year * 12
        cumulative_contribution = monthly_contribution * months

        # Future Value of an ordinary annuity
        fv = monthly_contribution * (((1 + monthly_rate) ** months - 1) / monthly_rate)
        interest_earned = fv - cumulative_contribution

        data.append({
            "Year": year,
            "Total Contribution (₹)": round(cumulative_contribution, 2),
            "Future Value (₹)": round(fv, 2),
            "Interest Earned (₹)": round(interest_earned, 2)
        })

    # Create DataFrame
    ci_table = pd.DataFrame(data)
    print(ci_table)


if __name__ == "__main__":
    calc()