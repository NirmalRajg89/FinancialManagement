import streamlit as st
import numpy as np
from streamlit_echarts import st_echarts
import time


# -------------------- CORE CALCULATION -------------------- #
def calculate_compound_growth(monthly_contribution, annual_return, months):
    monthly_return = annual_return / 12
    total_invested, total_value, interest_earned = [], [], []

    for month in range(months + 1):
        if month == 0:
            invested, value, interest = 0, 0, 0
        else:
            prev_value = total_value[-1] if total_value else 0
            grown_value = prev_value * (1 + monthly_return)
            value = grown_value + monthly_contribution
            invested = (total_invested[-1] if total_invested else 0) + monthly_contribution
            interest = value - invested

        total_invested.append(invested)
        total_value.append(value)
        interest_earned.append(interest)

    return total_invested, total_value, interest_earned


# -------------------- ECHARTS DARK MODE CONFIG -------------------- #
def get_dark_base():
    """Return common dark-theme style for all charts."""
    return {
        "backgroundColor": "#0e1117",
        "textStyle": {"color": "#eee"},
        "grid": {"left": "8%", "right": "5%", "bottom": "15%", "top": "10%"},
        "xAxis": {
            "axisLine": {"lineStyle": {"color": "#888"}},
            "axisLabel": {"color": "#ccc"},
            "splitLine": {"show": True, "lineStyle": {"color": "rgba(255,255,255,0.1)"}},
        },
        "yAxis": {
            "axisLine": {"lineStyle": {"color": "#888"}},
            "axisLabel": {"color": "#ccc"},
            "splitLine": {"show": True, "lineStyle": {"color": "rgba(255,255,255,0.1)"}},
        },
    }


# # -------------------- ECHARTS CHARTS -------------------- #
# def echarts_investment_growth(investment_data):
#     months = 20 * 12
#     x_data = list(range(months + 1))
#     base = get_dark_base()
#     color_palette = ['#73C0DE', '#FAC858', '#EE6666', '#91CC75', '#5470C6', '#3BA272']

#     series_data = []
#     for option, data in investment_data.items():
#         _, values, _ = calculate_compound_growth(
#             data['monthly_contribution'],
#             data['annual_return'] / 100,
#             months
#         )
#         series_data.append({
#             "name": f"{option} (${values[-1]:,.0f})",
#             "type": "line",
#             "smooth": True,
#             "symbol": "none",
#             "lineStyle": {"width": 3},
#             "data": [round(v, 2) for v in values],
#         })

#     option = {
#         **base,
#         "color": color_palette,
#         "title": {"text": "Investment Growth Comparison Over Time", "textStyle": {"color": "#fff"}},
#         "tooltip": {"trigger": "axis", "backgroundColor": "#222", "textStyle": {"color": "#fff"}},
#         "legend": {"type": "scroll", "top": "bottom", "textStyle": {"color": "#ccc"}},
#         "xAxis": {**base["xAxis"], "type": "category", "name": "Months", "data": x_data},
#         "yAxis": {**base["yAxis"], "type": "value", "name": "Portfolio Value ($)"},
#         "series": series_data,
#     }

#     st_echarts(option, height="600px", key=f"growth_chart_dark{int(time.time()*1000)}")


def echarts_contribution_pie(investment_data):
    base = get_dark_base()
    labels = list(investment_data.keys())
    values = [v["monthly_contribution"] for v in investment_data.values()]
    series_data = [
        {"value": v, "name": f"{labels[i]} (${'{:,.0f}'.format(v)})"} for i, v in enumerate(values)
    ]

    option = {
        **base,
        "title": {"text": "Monthly Contribution Distribution", "left": "center", "textStyle": {"color": "#fff"}},
        "tooltip": {
            "trigger": "item", 
            "backgroundColor": "#222", 
            "textStyle": {"color": "#fff"},
            "formatter": "{b}"
        },
        "legend": {"bottom": "0", "orient": "horizontal", "textStyle": {"color": "#ccc"}},
        "series": [{
            "name": "Monthly Contribution",
            "type": "pie",
            "radius": ["40%", "70%"],
            "avoidLabelOverlap": True,
            "itemStyle": {"borderRadius": 10, "borderColor": "#0e1117", "borderWidth": 2},
            "label": {"show": True, "formatter": "{b}"},
            "emphasis": {"label": {"show": True, "fontSize": 16, "fontWeight": "bold"}},
            "data": series_data,
        }]
    }

    st_echarts(option, height="600px", key=f"pie_chart_dark{int(time.time()*1000)}")


def echarts_goal_progress(investment_data, goal_amount):
    base = get_dark_base()
    options = list(investment_data.keys())
    final_values, goal_achieved = [], []
    months = 20 * 12

    # Compute final values and goal achievement
    for _, data in investment_data.items():
        _, value, _ = calculate_compound_growth(data["monthly_contribution"], data["annual_return"] / 100, months)
        final_values.append(value[-1])
        goal_achieved.append(value[-1] >= goal_amount)

    # Convert to millions and format as string
    bar_data = [
        {"value": round(v/1_000_000, 2), "itemStyle": {"color": "#91CC75" if g else "#EE6666"}}
        for v, g in zip(final_values, goal_achieved)
    ]
    goal_amount_million = round(goal_amount/1_000_000, 2)

    # Pre-compute Y-axis ticks (0, 1M, 2M, ...)
    y_max = max(max([v['value'] for v in bar_data]), goal_amount_million)
    y_axis_ticks = [i for i in range(0, int(y_max)+2)]  # simple integers in millions

    option = {
        **base,
        "title": {"text": "Final Portfolio Value vs Goal", "textStyle": {"color": "#fff"}},
        "tooltip": {
            "trigger": "axis", 
            "backgroundColor": "#222", 
            "textStyle": {"color": "#fff"},
            "formatter": "{b}: {c}M"
        },
        "xAxis": {**base["xAxis"], "type": "category", "data": options},
        "yAxis": {
            **base["yAxis"],
            "type": "value",
            "name": "Final Value (M $)",
            "min": 0,
            "max": y_max,
            "interval": 1,
            "axisLabel": {"formatter": "{value}M"},
            "splitLine": {"lineStyle": {"color": "rgba(255,255,255,0.1)"}}
        },
        "series": [{
            "data": bar_data,
            "type": "bar",
            "barWidth": "50%",
            "label": {
                "show": True,
                "position": "top",
                "color": "#ccc",
                "formatter": "{c}M"  # ECharts will display the preformatted value
            },
            "markLine": {
                "symbol": "none",
                "data": [{"yAxis": goal_amount_million}],
                "lineStyle": {"color": "red", "type": "dashed", "width": 2},
                "label": {
                    "show": True,
                    "formatter": f"Goal: {goal_amount_million}M",
                    "color": "red",
                    "position": "end"
                }
            }
        }],
    }

    st_echarts(option, height="600px", key=f"goal_chart_dark_{int(time.time()*1000)}")




# -------------------- VISUALIZATION WRAPPER -------------------- #
def display_investment_visualizations(investment_table_text, goal_amount):
    try:
        if not investment_table_text or not investment_table_text.strip():
            st.warning("No investment table data provided.")
            return

        lines = [l for l in investment_table_text.strip().split('\n') if l.strip()]
        investment_data = {}
        for line in lines:
            if 'Investment Option' in line or '---' in line:
                continue
            parts = [p.strip() for p in line.split('|')][1:-1]
            if len(parts) < 7:
                continue

            option = parts[0]
            eff_return = parts[2]
            monthly = parts[3]
            try:
                annual_return = float(eff_return.replace('%',''))
                monthly_contribution = float(monthly.replace('$','').replace(',',''))
                investment_data[option] = {
                    'annual_return': annual_return,
                    'monthly_contribution': monthly_contribution
                }
            except Exception:
                continue

        if not investment_data:
            st.warning("Could not parse data. Using sample set.")
            investment_data = {
                "Bank Savings Account": {"annual_return": 3.56, "monthly_contribution": 2882.93},
                "Equity Mutual Funds": {"annual_return": 10.47, "monthly_contribution": 1316.88},
                "Index Funds": {"annual_return": 13.24, "monthly_contribution": 944.74},
                "Stock Market": {"annual_return": 18.97, "monthly_contribution": 466.09}
            }

        st.markdown("### 💹 Investment Growth Analysis")
        col1, col2 = st.columns(2)
        with col1:
            echarts_contribution_pie(investment_data)
        with col2:
            echarts_goal_progress(investment_data, goal_amount)

    except Exception as e:
        st.error(f"Error creating visualizations: {e}")

def extract_investment_table_from_response(response_text):
    """Extract the investment options table from the agent response."""
    if not response_text:
        return None
        
    lines = response_text.split('\n')
    table_lines = []
    inside_table = False
    
    for i, line in enumerate(lines):
        line_lower = line.lower()
        # Start table when header line is found
        if not inside_table and 'investment option' in line_lower and '|' in line:
            inside_table = True
            table_lines.append(line)
            continue
        
        if inside_table:
            if line.strip() == "" or line.startswith('####'):
                # end of table
                break
            elif '|' in line:
                table_lines.append(line)
            else:
                # ignore non-table lines inside table section
                continue
    
    if table_lines:
        return '\n'.join(table_lines)
    
    return None
