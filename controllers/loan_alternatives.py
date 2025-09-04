"""
loan_alternatives.py
U.S. version – Suggest loan alternatives when required return > moderate risk.
As of Sept 4, 2025
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional

# Gate thresholds (annual return in decimal)
MODERATE_RETURN_CAP = 10  # 10% p.a.

def calculate_emi(principal: float, annual_rate: float, months: int) -> float:
    """Compute monthly loan payment (EMI)."""
    if months <= 0:
        return 0.0
    r = (annual_rate / 100.0) / 12.0
    if r == 0:
        return principal / months
    return principal * r * (1 + r) ** months / ((1 + r) ** months - 1)

@dataclass
class LoanOption:
    code: str
    label: str
    rate_min: float
    rate_max: float
    typical_tenure_months: int
    secured: bool
    notes: str

def get_default_options() -> List[LoanOption]:
    # Indicative U.S. market ranges (Sep 4, 2025)
    return [
        LoanOption("mortgage_30yr", "30-Year Fixed Mortgage", 6.5, 6.7, 360, True,
                   "Best for long-term funding; stable monthly payments."),
        LoanOption("mortgage_15yr", "15-Year Fixed Mortgage", 5.7, 5.9, 180, True,
                   "Lower rate than 30-year but higher monthly payment."),
        LoanOption("personal_loan", "Personal Loan (Unsecured)", 6.5, 24.0, 60, False,
                   "Fast disbursal, no collateral; rates vary widely by credit score."),
        LoanOption("home_equity", "Home Equity Loan / HELOC", 7.0, 13.0, 180, True,
                   "Secured by home equity; often cheaper than personal loans."),
    ]

def should_offer_loans(required_return: Any) -> bool:
    """Offer loans if required return exceeds ~12% annual."""
    return float(required_return) >= MODERATE_RETURN_CAP

def suggest_loans(goal_amount: float,
                  current_savings: float,
                  time_horizon_years: float,
                  required_return: Any,
                  rate_overrides: Optional[Dict[str, Dict[str, float]]] = None
                 ) -> Dict[str, Any]:
    """Return loan comparison table based on funding gap and U.S. rates with savings-aware filtering."""
    outstanding = max(0.0, goal_amount - current_savings)
    months = max(1, int(round(time_horizon_years * 12)))
    options = get_default_options()

    if rate_overrides:
        for opt in options:
            if opt.code in rate_overrides:
                rr = rate_overrides[opt.code]
                opt.rate_min = rr.get("min", opt.rate_min)
                opt.rate_max = rr.get("max", opt.rate_max)

    # Apply intelligent filtering based on savings
    rows = []
    downpayment_required = 0.20 * goal_amount   # assume 20% min downpayment for mortgage
    allow_mortgage = current_savings >= downpayment_required

    for opt in options:
        # Skip mortgage if savings < downpayment requirement
        if opt.code == "MORTGAGE" and not allow_mortgage:
            continue

        # Encourage personal loan if savings are very low (<10% of goal)
        if current_savings < 0.10 * goal_amount and opt.code == "PERSONAL":
            opt.notes += " (suitable if you don’t have enough for a home loan downpayment)."

        # Midpoint rate
        mid_rate = (opt.rate_min + opt.rate_max) / 2.0
        tenure = min(opt.typical_tenure_months, months)
        emi = calculate_emi(outstanding, mid_rate, tenure) if outstanding > 0 else 0.0

        rows.append({
            "Product": opt.label,
            "Rate Range (p.a.)": f"{opt.rate_min:.2f}%–{opt.rate_max:.2f}%",
            "Assumed Rate": f"{mid_rate:.2f}%",
            "Tenure (months)": tenure,
            "Estimated Payment": round(emi, 2),
            "Secured": "Yes" if opt.secured else "No",
            "Notes": opt.notes,
        })

    # Add contextual suggestions
    extra_notes = []
    if not allow_mortgage:
        extra_notes.append("💡 You don’t meet the ~20% downpayment requirement for a home loan, consider a Personal Loan instead.")
    elif outstanding > 0.8 * goal_amount:
        extra_notes.append("💡 High borrowing need relative to savings — consider combining investments + smaller loan.")
    if current_savings > goal_amount:
        extra_notes.append("✅ You already have enough savings to cover the goal — a loan may not be necessary.")

    return {
        "required_return": required_return,
        "outstanding_needed_today": round(outstanding, 2),
        "time_horizon_months": months,
        "loan_rows": rows,
        "disclaimer": (
            "Rates are indicative ranges as of Sept 4, 2025 (U.S. market). "
            "Check lenders for exact offers. Loans increase total cost and "
            "should be used cautiously."
        ),
        "advice": extra_notes,
    }
