import itertools
import pandas as pd

import pandas as pd
import itertools


def portfolio_optimizer(monthly_contribution, monthsCount, goal, funds, top_n=2):
    """
    Simple deterministic portfolio optimizer for expected returns.

    Args:
        monthly_contribution (float): Amount contributed per month.
        monthsCount (int): Investment horizon in months.
        goal (float): Target future value.
        funds (dict): Dict of fund_name -> expected annual return (decimal).
        top_n (int): Number of top results to return.

    Returns:
        pd.DataFrame: Top N feasible allocations sorted by diversification and return.
        float: Required annual return.
    """
    months = int(monthsCount)

    # --- Helper functions ---
    def fv_of_annuity(monthly_c, annual_r, months):
        if annual_r == 0:
            return monthly_c * months
        monthly_r = annual_r / 12.0
        return monthly_c * ((1 + monthly_r) ** months - 1) / monthly_r

    def find_required_return(monthly_c, months, target):
        lo, hi = -0.999, 1.0
        f_lo = fv_of_annuity(monthly_c, lo, months) - target
        f_hi = fv_of_annuity(monthly_c, hi, months) - target
        if f_lo == 0: return lo
        if f_hi == 0: return hi
        if f_lo * f_hi > 0: return None
        for _ in range(80):
            mid = (lo + hi) / 2.0
            f_mid = fv_of_annuity(monthly_c, mid, months) - target
            if f_mid == 0: return mid
            if f_lo * f_mid < 0:
                hi = mid
                f_hi = f_mid
            else:
                lo = mid
                f_lo = f_mid
        return (lo + hi) / 2.0

    def feasible_two_fund(pair, r_req):
        (n1, r1), (n2, r2) = pair
        if r1 == r2:
            return {n1: 0.5, n2: 0.5} if abs(r1 - r_req) < 1e-9 else None
        w1 = (r_req - r2) / (r1 - r2)
        w2 = 1 - w1
        if 0 <= w1 <= 1 and 0 <= w2 <= 1:
            return {n1: w1, n2: w2}
        return None

    def feasible_three_fund(triple, r_req):
        names = [t[0] for t in triple]
        rs = [t[1] for t in triple]
        for perm_idx in range(3):
            i_lonely = perm_idx
            i_a = (perm_idx + 1) % 3
            i_b = (perm_idx + 2) % 3
            r_lonely = rs[i_lonely]
            r_a = rs[i_a]
            r_b = rs[i_b]
            denom = (r_a - r_lonely) + (r_b - r_lonely)
            if abs(denom) < 1e-12:
                continue
            x = (r_req - r_lonely) / denom
            w = [0.0, 0.0, 0.0]
            w[i_a] = x
            w[i_b] = x
            w[i_lonely] = 1 - 2 * x
            if all(-1e-9 <= wi <= 1 + 1e-9 for wi in w):
                w = [max(0.0, wi) for wi in w]
                s = sum(w)
                if s == 0:
                    continue
                w = [wi / s for wi in w]
                return {names[0]: w[0], names[1]: w[1], names[2]: w[2]}
        return None

    # --- Main computation ---
    r_req = find_required_return(monthly_contribution, months, goal)
    if r_req is None:
        print("Required return is outside search bounds (-99.9% to +100%).")
        return pd.DataFrame(), None

    fund_items = list(funds.items())
    results = []

    for k in (2, 3):
        for combo in itertools.combinations(fund_items, 3):
            rates = [r for (_, r) in combo]
            r_min = min(rates)
            r_max = max(rates)
            if not (r_min - 1e-12 <= r_req <= r_max + 1e-12):
                continue
            alloc = feasible_three_fund(combo, r_req)
            if alloc is None:
                continue
            weights = alloc
            r_port = sum(weights[name] * funds[name] for name in weights)
            fv_total = fv_of_annuity(monthly_contribution, r_port, months)

            # Compute individual fund FVs
            fv_per_fund = {name: fv_of_annuity(monthly_contribution * w, funds[name], months)
                           for name, w in weights.items()}

            conc = max(weights.values())
            results.append({
                "combination": ", ".join(weights.keys()),
                "weights": weights,
                "portfolio_return_%": r_port * 100,
                "fv_at_return": fv_total,
                "fv_per_fund": fv_per_fund,
                "concentration_max_weight": conc
            })

    if not results:
        alt = []
        for k in (2, 3):
            for combo in itertools.combinations(fund_items, k):
                r_max = max(r for (_, r) in combo)
                alt.append((combo, r_max))
        alt_sorted = sorted(alt, key=lambda x: x[1], reverse=True)
        for combo, r_max in alt_sorted[:8]:
            best_name = max(combo, key=lambda x: x[1])[0]
            weights = {name: (1.0 if name == best_name else 0.0) for name, _ in combo}
            fv_total = fv_of_annuity(monthly_contribution, r_max, months)
            fv_per_fund = {name: fv_total if name == best_name else 0.0 for name in weights}
            results.append({
                "combination": ", ".join([c[0] for c in combo]),
                "weights": weights,
                "portfolio_return_%": r_max * 100,
                "fv_at_return": fv_total,
                "fv_per_fund": fv_per_fund,
                "concentration_max_weight": 1.0
            })

    # --- Prepare DataFrame ---
    rows = []
    for r in results:
        fv_fund_str = "; ".join([f"{name}: ${fv:,.0f}" for name, fv in r["fv_per_fund"].items()])
        rows.append({
            "Combination": r["combination"],
            "Weights": "; ".join([f"{name}: {w * 100:.1f}%" for name, w in r["weights"].items()]),
            "Portfolio return (%)": round(r["portfolio_return_%"], 4),
            "FV at return ($)": f"${r['fv_at_return']:,.0f}",
            "FV per fund ($)": fv_fund_str,
            "Max weight": round(r["concentration_max_weight"], 3)
        })

    df = pd.DataFrame(rows)
    df = df.sort_values(by=["Max weight", "Portfolio return (%)"], ascending=[True, False]).reset_index(drop=True)
    df_top = df.head(top_n)

    return df_top, r_req

# ----------------------
# Example usage:
# if __name__ == "__main__":
#     monthly_contribution = 1500.0
#     years = 20
#     goal = 1000000.0
#     funds = {
#         "Bank Savings Account": 0.035,  # 3–4% -> midpoint 3.5%
#         "Recurring Deposit": 0.06,  # 5–7% -> midpoint 6%
#         "Public Provident Fund": 0.075,  # 7–8% -> midpoint 7.5%
#         "Equity Mutual Funds": 0.10,  # 8–12% -> midpoint 10%
#         "Index Funds": 0.125,  # 10–15% -> midpoint 12.5%
#         "Stock Market": 0.175  # 15–20% -> midpoint 17.5%
#     }
#
#     top_allocations, required_return = portfolio_optimizer(monthly_contribution, years, goal, funds, top_n=2)
#     print(f"\nRequired annual return: {required_return * 100:.3f}%\n")
#     print("Top 2 feasible allocations:")
#     print(top_allocations)
