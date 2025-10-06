import base64
import json

import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import ChatOpenAI
from controllers.agent_controller_v1 import create_investment_summary_v1, create_agent_executor_v1
from controllers.flow import get_dynamic_allocation, format_allocation_table
from controllers.investment_summary import calculate_goal_duration, calculate_monthly_contribution, calculate_risk_tolerance_v1
from controllers.newsAPI_controller import get_stock_news, search_stock_news, get_stock_statistics, get_stock_data, get_related_stocks
from controllers.beginner_friendly_controller import get_simple_stock_data, get_popular_stocks_overview, get_beginner_news, get_simple_market_sentiment, get_beginner_tips
import time

from controllers.router_graph import app
from controllers.utils import format_tenure, get_tolerance_v1
from controllers.voice_controller import speak_risk_tolerance_summary, speak_investment_plan_summary


def img_to_base64(image_path):
    """Convert image to base64."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        print(f"Error converting image to base64: {str(e)}")
        return None

def extract_stock_symbol(search_query):
    """
    Extract stock symbol from search query.
    
    Args:
        search_query (str): The search query entered by user
    
    Returns:
        str: Stock symbol if found, None otherwise
    """
    query_lower = search_query.lower().strip()
    
    # Common stock symbol mappings
    symbol_mapping = {
        'apple': 'AAPL',
        'aapl': 'AAPL',
        'microsoft': 'MSFT',
        'msft': 'MSFT',
        'google': 'GOOGL',
        'googl': 'GOOGL',
        'alphabet': 'GOOGL',
        'amazon': 'AMZN',
        'amzn': 'AMZN',
        'tesla': 'TSLA',
        'tsla': 'TSLA',
        'nvidia': 'NVDA',
        'nvda': 'NVDA',
        'meta': 'META',
        'facebook': 'META',
        'netflix': 'NFLX',
        'nflx': 'NFLX',
        'bitcoin': 'BTC-USD',
        'btc': 'BTC-USD',
        'crypto': 'BTC-USD'
    }
    
    # Check for exact matches first
    if query_lower in symbol_mapping:
        return symbol_mapping[query_lower]
    
    # Check if query contains any of the company names
    for company, symbol in symbol_mapping.items():
        if company in query_lower:
            return symbol
    
    # Check if query is already a stock symbol (3-5 uppercase letters)
    import re
    if re.match(r'^[A-Z]{1,5}$', search_query.upper()):
        return search_query.upper()
    
    return None


# Initialize the memory in session state
def get_session_memory():
    if 'memory' not in st.session_state:
        st.session_state.memory = ConversationSummaryBufferMemory(
            memory_key="chat_history",
            return_messages=True,
            input_key="question",
            max_token_limit=1000,
            llm=ChatOpenAI(temperature=0, model="gpt-3.5-turbo")
        )
    return st.session_state.memory


def main():
    st.set_page_config(
        layout="wide",
        page_title="Financial Advisor Pro",
        page_icon="💼",
        initial_sidebar_state="expanded"
    )

    # Modern CSS styling
    st.markdown(
        """
        <style>
        /* Import modern fonts */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        /* Global styles */
        .main {
            font-family: 'Inter', sans-serif;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
        }
        
        .css-1d391kg .css-1v0mbdj {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 12px;
            padding: 20px;
            margin: 10px 0;
        }
        
        /* Logo styling */
        .logo-container {
            text-align: center;
            padding: 20px 0;
            margin-bottom: 30px;
        }
        
        .main-logo {
            width: 80px;
            height: 80px;
            border-radius: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }
        
        .main-logo:hover {
            transform: scale(1.05);
        }
        
        .brand-text {
            color: white;
            font-size: 18px;
            font-weight: 600;
            margin-top: 10px;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        /* Menu styling */
        .menu-container {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 15px;
            margin: 20px 0;
        }
        
        /* Footer logo */
        .footer-logo {
            display:flex;
            justify-content:center;
            width: 60px,
            height: 100px;
            opacity: 0.8;
            border-radius:20px;
            transition: opacity 0.3s ease;
        }
        
        .footer-logo:hover {
            opacity: 1;
        }
        
        /* Main content styling */
        .main-content {
            background: #f8fafc;
            min-height: 100vh;
        }
        
        /* Card styling */
        .metric-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
            border: 1px solid #e2e8f0;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
        }
        
        /* Button styling */
        .stButton > button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .stButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        /* Input styling */
        .stTextInput > div > div > input {
            border-radius: 8px;
            border: 2px solid #e2e8f0;
            transition: border-color 0.3s ease;
        }
        
        .stTextInput > div > div > input:focus {
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        /* Table styling */
        .stDataFrame {
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        }
        
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        #header {visibility: hidden;}
        
        /* Custom scrollbar */
        ::-webkit-scrollbar {
            width: 6px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 3px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: #667eea;
            border-radius: 3px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: #764ba2;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Modern sidebar design
    with st.sidebar:
        # Main logo and brand
        st.markdown(
            """
            <div class="logo-container">
                <div style="display: flex; justify-content: center; align-items: center;">
            """,
            unsafe_allow_html=True
        )
        
        img_path = "imgs/rate_logo1.png"
        img_base64 = img_to_base64(img_path)
        if img_base64:
            st.markdown(
                f'<img src="data:image/png;base64,{img_base64}" class="main-logo">',
                unsafe_allow_html=True,
            )
        
        st.markdown(
            """
                </div>
                <div class="brand-text">Financial Advisor Pro</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Navigation menu
        st.markdown('<div class="menu-container">', unsafe_allow_html=True)
        mode = option_menu(
            menu_title=None,
            options=["Stock News", "Financial Advisor"],
            icons=["clipboard-data", "graph-up-arrow"],
            menu_icon=None,
            default_index=1,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "white", "font-size": "16px"},
                "nav-link": {
                    "font-size": "14px",
                    "text-align": "left",
                    "margin": "5px 0",
                    "color": "white",
                    "background-color": "transparent",
                    "border-radius": "8px",
                    "padding": "10px 15px",
                },
                "nav-link-selected": {
                    "background-color": "rgba(255, 255, 255, 0.2)",
                    "color": "white",
                },
            }
        )

        st.markdown('</div>', unsafe_allow_html=True)

        # Add spacer
        st.markdown("<div style='flex: 1;'></div>", unsafe_allow_html=True)
        
        # Footer with company logo
        st.markdown(
            """
            <div style="text-align: center; padding: 20px 0; border-top: 1px solid rgba(255, 255, 255, 0.2);">
                <div style="color: rgba(255, 255, 255, 0.7); font-size: 12px; margin-bottom: 2px;">
                    Powered by
                </div>
            """,
            unsafe_allow_html=True
        )
        
        img_path = "imgs/alti_logo1.png"
        img_base64 = img_to_base64(img_path)
        if img_base64:
            st.markdown(
                f'<img src="data:image/png;base64,{img_base64}" class="footer-logo">',
                unsafe_allow_html=True,
            )
        
        st.markdown("</div>", unsafe_allow_html=True)

    if mode == "Financial Advisor":

        # Load user data
        with open("data/customer.json") as f:
            all_user_data = json.load(f)

        st.set_page_config(page_title="Investment Planner", layout="wide")
        st.title("📊 Personalized Financial Wellness & Investment Advisory Platform")

        # Step 1: Ask for name
        user_name = st.text_input("Enter your name to begin:")

        if user_name:
            if user_name not in all_user_data:
                st.error(f"No data found for user: {user_name}")
                st.stop()

            # Speak welcome message automatically
            #speak_welcome_message(user_name)
            
            user_profile = all_user_data[user_name]

            # Step 2: Financial summary
            st.subheader(f"💼 {user_name}'s Financial Summary")
            employment = user_profile["employment"]
            assets = user_profile["assets"]
            liabilities = user_profile["liabilities"]
            debt_monthly_payment = {l["name"]: l["monthlyPaymentAmount"] for l in liabilities}
            debt_payment_str = {
                l["name"].title(): f"Monthly Payment: ${l['monthlyPaymentAmount']}, Tenure: {format_tenure(l.get('termMonths'))}"
                for l in liabilities
            }

            monthlyPaymentAmount = sum(l["monthlyPaymentAmount"] for l in liabilities)
            total_liabilities = sum(l["unpaidBalanceAmount"] for l in liabilities)
            savings = sum(a["total"] for a in assets)
            total_assets = sum(a["total"] for a in assets)
            cash_reserves = sum(a["total"] for a in assets if a["assetType"] in ["CheckingAccount", "SavingsAccount"])
            Debt_to_Income_Ratio = round((monthlyPaymentAmount / employment["monthlyIncomeAmount"]) * 100, 2)
            summary_data = {
                "Monthly Income ($)": [employment["monthlyIncomeAmount"]],
                "Credit Score": [employment["creditScore"]],
              
                "Saving - Liquid Fund ($)": savings,
                "Total Liabilities ($)": total_liabilities,
                "Monthly Debt Payments ($)": [monthlyPaymentAmount],
                "Debt-to-Income Ratio (%)": [
                    round((monthlyPaymentAmount / employment["monthlyIncomeAmount"]) * 100, 2)
                ],
            }
            has_house_asset = any(asset.get("type") == "house" for asset in user_profile.get("assets", []))
            df = pd.DataFrame(summary_data)
            
            # Add emoji indicators for the current DataFrame structure
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

                return df
            
            df_with_indicators = add_indicators(df)
            st.table(df_with_indicators)
            # ---- Debt Details Tooltip in Expander ---- #

            with st.expander("ℹ️ View Total Liabilities Detail"):
                st.write("#### Total Liabilities Details")
                for name, detail in debt_payment_str.items():
                    st.markdown(f"- **{name}**: {detail}")

            customer_data = {
                "credit_score": employment["creditScore"],
                "monthly_salary": employment["monthlyIncomeAmount"],
                "Debt_to_Income_Ratio": Debt_to_Income_Ratio,
                "savings_amount": savings
            }
            risk_salary = calculate_risk_tolerance_v1(customer_data)
            risk_tolerance = risk_salary['risk_level']
            # monthly_contribution = risk_salary['monthly_contribution']

            col1, col2 = st.columns([3, 1])  # Adjust the ratio to your preference

            formula_df = pd.DataFrame([
                {"Risk Level": "High", "Credit Score": "> 700", "Debt Ratio": "< 40%",
                 "Savings Condition": "Has savings > Emergency Fund"},
                {"Risk Level": "Moderate", "Credit Score": "650 – 700", "Debt Ratio": "40% – 70%",
                 "Savings Condition": "Emergency fund only"},
                {"Risk Level": "Low", "Credit Score": "< 650", "Debt Ratio": "≥ 100%",
                 "Savings Condition": "No savings"},
            ])
            # In the first column, display the markdown
            with col1:
                st.markdown(get_tolerance_v1(risk_tolerance,formula_df))
                
                # Automatically speak risk tolerance summary
                credit_score = employment["creditScore"]
                savings_condition = "Has savings > Emergency Fund" if total_assets > 22000 else "Emergency fund only" if total_assets > 0 else "No savings"
                speak_risk_tolerance_summary(risk_tolerance, credit_score, Debt_to_Income_Ratio, savings_condition)


            # In the second column, add the popover
            with col2:
                with st.popover("📘 Risk Formula Reference"):

                    st.dataframe(formula_df)


            # Step 3: Preferences
            st.subheader("🎯 Investment Suggestions")
            plan_type = st.radio("Select Plan Type", ["Short-term", "Long-term"], horizontal=True)
            # Calculate disposable income
            disposable_income = employment["monthlyIncomeAmount"] - monthlyPaymentAmount
            income_risk_ratios = {"Low": 0.3, "Moderate": 0.5, "High": 0.7}

            # Determine income-based risk tolerance ratio
            if disposable_income > 20000:
                income_risk_tolerance = income_risk_ratios['High']
            elif disposable_income > 7000:
                income_risk_tolerance = income_risk_ratios['Moderate']
            else:
                income_risk_tolerance = income_risk_ratios['Low']

            default_values = {
                "Emergency-fund": {"tenure": 6, "goal_amount": 22000},
                "Education": {"tenure": 24, "goal_amount": 80000},
                "Car": {"tenure": 12, "goal_amount": 35000},
                "Bike": {"tenure": 6, "goal_amount": 15000}
            }

            default_long_term_values = {
                "Retirement": {
                    "tenure": 20,
                    "goal_amount": 1000000
                },
                "Home": {
                    "tenure": 15,
                    "goal_amount": 450000
                }
            }

            # risk_levels = ["Low", "Moderate", "High", "Very High", "Unrealistic"]

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

            # risk_level = user_profile.get("riskTolerance", "Moderate")

            # Map risk tolerance to color and meaning
            risk_info = {
                "Low": {
                    "color": "#2ecc71",  # Green
                    "meaning": "Prefers safety, avoids loss, very low risk acceptance"
                },
                "Moderate": {
                    "color": "#f1c40f",  # Yellow
                    "meaning": "Balanced approach, some risk acceptable for moderate growth"
                },
                "High": {
                    "color": "#e67e22",  # Orange
                    "meaning": "Comfortable with ups and downs, seeks higher returns"
                },
                "Very High": {
                    "color": "#e74c3c",  # Red
                    "meaning": "Aggressive investor, accepts high volatility for maximum returns"
                },
                "Unrealistic": {
                    "color": "#8e44ad",  # Purple
                    "meaning": "Target requires >20% annual return, not practical — adjust tenure, or goal"
                }
            }

            base_risk = "Unknown"
            risk_level = "Unknown"
            info = {
                "color": "#95a5a6",
                "meaning": "Risk tolerance data not applicable"
            }
            monthly_contribution = round(disposable_income * income_risk_tolerance, 2)

            if plan_type == "Short-term":
                col1, col2, col4 = st.columns(3)  # first row with 3 columns
                #col4, col5, col6 = st.columns(3)  # second row with 2 columns

                with col1:
                    goals = st.selectbox("Goal", ["Emergency-fund", "Education", "Car", "Bike"])

                with col2:
                    tenure = st.number_input("Duration(in months)", min_value=6, max_value=60, value=default_values[goals]['tenure'], step=1)

                with col4:
                    goal_amount = st.number_input(
                        "Expected Goal Amount($)",
                        min_value=1000.0,
                        max_value=1_00_00_000.0,
                        step=1000.0,
                        value=float(default_values[goals]['goal_amount'])
                    )


            elif plan_type == "Long-term":
                col1, col2, col4 = st.columns(3)  # first row with 3 columns
                #col4, col5, col6 = st.columns(3)  # second row with 2 columns

                with col1:
                    goals = st.selectbox("Goal", ["Retirement", "Home"])

                with col2:
                    tenure = st.number_input("Duration(in years)", min_value=5, max_value=30, value=default_long_term_values[goals]['tenure'], step=1)

                #with col3:
                    # monthly_contribution = round(disposable_income * income_risk_tolerance, 2)
                    #monthly_contribution = st.number_input(
                    #    label=f"Monthly Investment - {int(income_risk_tolerance * 100)}% (Income - Liabilities) ($)",
                    #    min_value=100.0,
                    #    max_value=float(employment["monthlyIncomeAmount"]),
                    #    value=default_contribution,
                    #    step=100.0
                    #)

                with col4:
                    goal_amount = st.number_input(
                        "Expected Goal Amount($)",
                        min_value=1000.0,
                        max_value=5_00_00_000.0,
                        step=10000.0,
                        value=float(default_long_term_values[goals]['goal_amount'])
                    )

            # Required annual return
            req_return = required_return(monthly_contribution, goal_amount, 12, tenure)

            # Map to risk profile
            if req_return <= 7:
                base_risk = "Low"
            elif req_return <= 12:
                base_risk = "Moderate"
            elif req_return <= 16:
                base_risk = "High"
            elif req_return <= 20:
                base_risk = "Very High"
            else:
                base_risk = "Unrealistic"

            info = risk_info.get(base_risk, info)

            st.text(f""" Safer monthly contribution with tolerance of {income_risk_tolerance*100}%: {monthly_contribution}, Max monthly income after debts:{disposable_income} """)

            st.markdown(
                f"""
                <div style="
                    background-color: {info['color']};
                    padding: 15px;
                    border-radius: 10px;
                    font-weight: 600;
                    font-size: 1.1em;
                    color: white;
                    line-height: 1.4;">
                    📌 Risk Level as per Goal inputs: <strong>{base_risk} - ({info['meaning']})</strong><br>
                </div>
                </br>
                """,
                unsafe_allow_html=True
            )

            # Ensure chat history exists
            if "chat_history" not in st.session_state:
                st.session_state.chat_history = []

            investment_options = """
            - Bank Savings Account (3–4%)
            - Recurring Deposit (5–7%)
            - Public Provident Fund (7–8%)
            - Equity Mutual Funds (8–12%)
            - Index Funds (10–15%)
            - Stock Market (15–20%)
            """
            allocation = get_dynamic_allocation(risk_level, monthly_contribution)
            formatted_table = format_allocation_table(allocation, monthly_contribution)
            # goal_duration = calculate_goal_duration(monthly_contribution,goal_amount)
            monthly_contribution_investment = calculate_monthly_contribution(goal_amount, tenure, plan_type)
            #print(goal_duration)
            #print(monthly_contribution_investment)
            static_vars = {
                "monthly_contribution": str(monthly_contribution),
                "tenure": f"{tenure} months" if plan_type == "Short-term" else f"{tenure} years",
                "goal_amount": str(goal_amount),
                "risk_tolerance": str(risk_level),
                "investment_options": investment_options,
                "formatted_allocation_table": formatted_table,
                # "goal_duration":goal_duration,
                "monthly_contribution_investment":monthly_contribution_investment,
                "income_risk_tolerance":income_risk_tolerance,
                "monthlyPaymentAmount": str(monthlyPaymentAmount),
                "total_liabilities": str(total_liabilities),
                "goals": goals,
                "mortgage_info_url": "www.rate.com/mortgage-plans",
                "heloc_info_url": "www.rate.com/heloc",
                "refinance_info_url": "www.rate.com/refinance",
                "heloc_example": "HELOC is a Home Equity Line of Credit that allows borrowing against home equity.",
                "refinance_example": "Refinancing means replacing an existing loan with a new loan with better terms.",
                "goal_feasibility": "",
                "has_house_asset":has_house_asset,
                "plan_type":plan_type,
                "tenure_for_optimizer": int(tenure)
            }
            st.session_state.static_vars = static_vars
            # Step 4: Generate Plan
            if goals and monthly_contribution:
                if st.button("Generate Investment Plan"):
                    with st.spinner("Getting expert advice..."):
                        st.session_state.investment_input_data = {
                            "profile": user_profile,
                            "investment_options": investment_options,
                            "user_inputs": {
                                "plan_type": plan_type,
                                "goals": goals,
                                "risk_tolerance": risk_level.lower(),
                                "tenure": f"{tenure} months" if plan_type == "Short-term" else f"{tenure} years",
                                "monthly_contribution": monthly_contribution,
                                "goal_amount": goal_amount

                            }
                        }
                        # Create agent
                        st.session_state.agent = create_investment_summary_v1(static_vars)

                        plan_prompt = {
                            "profile": user_profile,
                            "user_inputs": st.session_state.investment_input_data["user_inputs"],
                            "tenure": f"{tenure} months" if plan_type == "Short-term" else f"{tenure} years",
                            "monthly_contribution": monthly_contribution,
                            "goal_amount": goal_amount,
                            "risk_tolerance": risk_level,
                            "investment_options": investment_options,
                            "question": "Generate a detailed investment plan based on the above.",
                            # **static_vars,
                        }

                        user_msg = f"Generate {plan_type} plan — goals: {goals}, risk: {risk_level}, tenure: {tenure} {'months' if plan_type == 'Short-term' else 'years'}, Goal to achieve: {goal_amount}"
                        st.session_state.chat_history.append({"role": "user", "content": user_msg})

                        full_response = ""
                        response = st.session_state.agent.ask(plan_prompt)

                        response_placeholder = st.empty()

                        for char in response:
                            full_response += char
                            response_placeholder.markdown(full_response + "▌")
                            time.sleep(0.001)

                        # Add loan recommendation if needed
                        #if req_return and plan_type == "Long-term":
                        #    loan_summary = create_loan_summary(goal_amount, cash_reserves, tenure, req_return)
                        #    full_response += "\n\n" + loan_summary

                        st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                        time.sleep(0.02)
                        response_placeholder.empty()
                        
                        # Automatically speak investment plan summary
                        speak_investment_plan_summary(plan_type, goals, risk_level, monthly_contribution, goal_amount, tenure)

            # Step 5: Show conversation + follow-up chat
            if st.session_state.chat_history:
                st.subheader("💬 Investment Summary")
                for msg in st.session_state.chat_history:
                    with st.chat_message(msg["role"]):
                        st.markdown(msg["content"])

                # Chat input for follow-ups
                user_query = st.chat_input("Type your question and press Enter...")
                if user_query:
                    st.session_state.chat_history.append({"role": "user", "content": user_query})
                    with st.chat_message("user"):
                        st.markdown(user_query)

                    chat_history = st.session_state.get("chat_history", [])
                    follow_up_context = {"question": user_query}
                    st.session_state.agent = create_agent_executor_v1(static_vars,  history=chat_history)
                    with st.chat_message("assistant"):
                        with st.spinner("Getting expert advice..."):
                            full_response = ""
                            memory = get_session_memory()
                            # Invoke the router graph with the current memory
                            output = app.invoke({
                                "question": user_query,
                                "routes": [],
                                "current_route": None,
                                "answer": "",
                                "intermediate": {},
                                "memory": memory,
                                "session_id": "streamlit_session"  # Can use st.session_state.id if needed
                            })

                            response = output.get("answer", "Sorry, something went wrong.")
                            response_placeholder = st.empty()
                            for char in response:
                                full_response += char
                                response_placeholder.markdown(full_response + "▌")
                                time.sleep(0.01)
                            response_placeholder.markdown(full_response)

                    st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                    st.rerun()

    else:
        # Handle initial state for stock news
        if "refresh_news" not in st.session_state:
            st.session_state.refresh_news = True
        if "news_data" not in st.session_state:
            st.session_state.news_data = []
        if "search_query" not in st.session_state:
            st.session_state.search_query = ""
        if "is_search_mode" not in st.session_state:
            st.session_state.is_search_mode = False
        if "search_results" not in st.session_state:
            st.session_state.search_results = []
        if "stock_data" not in st.session_state:
            st.session_state.stock_data = None
        if "related_stocks" not in st.session_state:
            st.session_state.related_stocks = []

        # Header
        col1, col2 = st.columns([10, 3])
        with col1:
            st.markdown("## 📰 Latest Stock Updates")
        with col2:
            col2_1, col2_2 = st.columns(2)
            with col2_1:
                if st.button("## ♻️ Update News", help="Refresh News"):
                    st.session_state.refresh_news = True
                    st.session_state.is_search_mode = False
                    st.session_state.search_query = ""  # Reset search input
                    st.rerun()
            with col2_2:
                if st.button("## 📊 Refresh Data", help="Refresh Market Data"):
                    # Clear cache for real-time data
                    get_stock_statistics.clear()
                    st.session_state.search_query = ""  # Reset search input
                    st.rerun()

                # Search functionality with better alignment
        st.markdown("### 🔍 Search Stock News")
        search_col1, search_col2 = st.columns([3, 1])
        
        with search_col1:
            # Stock Statistics Table
            st.markdown("### 📊 Market Statistics")
            try:
                stats = get_stock_statistics()
                if stats:
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        st.metric("Market Status", stats.get("market_status", "N/A"))
                        st.metric("Dow Jones", f"{stats.get('dow_jones', 0):,.0f}")
                    
                    with col2:
                        st.metric("S&P 500", f"{stats.get('sp_500', 0):,.0f}")
                        st.metric("NASDAQ", f"{stats.get('nasdaq', 0):,.0f}")
                    
                    with col3:
                        st.metric("VIX", f"{stats.get('vix', 0):.2f}")
                        st.metric("10Y Treasury", f"{stats.get('treasury_10y', 0):.2f}%")
                    
                    with col4:
                        st.metric("Oil Price", f"${stats.get('oil_price', 0):.2f}")
                        st.metric("Gold Price", f"${stats.get('gold_price', 0):.0f}")
                    
                    with col5:
                        st.metric("Bitcoin", f"${stats.get('bitcoin', 0):,.0f}")
                        st.metric("Dollar Index", f"{stats.get('dollar_index', 0):.2f}")
            except Exception as e:
                st.error("Unable to load market statistics")

        # 🆕 STOCK MARKET GUIDE (NEW ADDITION)
        st.markdown("---")
        
        # Create collapsible section
        with st.expander("📈 **Stock Market Guide** - Click to expand", expanded=False):
            st.markdown("*Simple explanations and easy-to-understand insights for all investors*")
            
            # Create tabs for features
            guide_tab1, guide_tab2, guide_tab3, guide_tab4 = st.tabs(["📊 Popular Stocks", "📰 Market News", "🎯 Market Mood", "💡 Investing Tips"])
        
            with guide_tab1:
                st.markdown("#### 📊 **Popular Stocks Overview**")
                st.markdown("*Quick look at well-known companies and their current status*")
                
                if st.button("🔄 Load Popular Stocks", type="primary"):
                    with st.spinner("Getting popular stocks data..."):
                        popular_stocks = get_popular_stocks_overview()
                        
                        if popular_stocks:
                            # Display in a simple grid
                            cols = st.columns(2)
                            for i, stock in enumerate(popular_stocks):
                                with cols[i % 2]:
                                    with st.container():
                                        st.markdown(f"### {stock['name']} ({stock['symbol']})")
                                        st.markdown(f"*{stock['description']}*")
                                        
                                        # Price and trend
                                        col_price, col_trend = st.columns(2)
                                        with col_price:
                                            st.metric("Price", f"${stock['price']}")
                                        with col_trend:
                                            st.markdown(f"**{stock['trend']}**")
                                        
                                        # Change info
                                        change_color = "green" if stock['change'] >= 0 else "red"
                                        st.markdown(f"<span style='color: {change_color}; font-size: 1.2em;'>📈 {stock['change_pct']:+.2f}% (${stock['change']:+.2f})</span>", unsafe_allow_html=True)
                                        
                                        st.markdown(f"**Sector:** {stock['sector']}")
                                        st.markdown("---")
                        else:
                            st.error("Unable to load popular stocks data")
                
                # Simple stock lookup
                st.markdown("#### 🔍 **Look Up Any Stock**")
                col_lookup1, col_lookup2 = st.columns(2)
                with col_lookup1:
                    lookup_symbol = st.text_input("Enter stock symbol (e.g., AAPL)", key="guide_lookup")
                with col_lookup2:
                    if st.button("🔍 Look Up", type="secondary"):
                        if lookup_symbol:
                            with st.spinner("Getting stock info..."):
                                stock_info = get_simple_stock_data(lookup_symbol)
                                if stock_info:
                                    st.markdown(f"### {stock_info['name']} ({stock_info['symbol']})")
                                    st.metric("Current Price", f"${stock_info['price']}")
                                    st.markdown(f"**Trend:** {stock_info['trend']}")
                                    st.markdown(f"**Change:** {stock_info['change_pct']:+.2f}% (${stock_info['change']:+.2f})")
                                    st.markdown(f"**Sector:** {stock_info['sector']}")
                                else:
                                    st.error(f"Unable to find data for {lookup_symbol}")
            
            with guide_tab2:
                st.markdown("#### 📰 **Market News**")
                st.markdown("*Easy-to-understand news that affects the stock market*")
                
                if st.button("📰 Load Market News", type="primary"):
                    with st.spinner("Getting market news..."):
                        market_news = get_beginner_news()
                        
                        if market_news:
                            for article in market_news:
                                with st.expander(f"📄 {article.get('title', 'No Title')}", expanded=False):
                                    st.markdown(f"**📰 Source:** {article.get('source', {}).get('name', 'Unknown')}")
                                    st.markdown(f"**📅 Published:** {article.get('publishedAt', 'Unknown')}")
                                    
                                    if article.get('url'):
                                        st.markdown(f"**[Read Full Article →]({article.get('url')})**")
                                    
                                    if article.get("urlToImage"):
                                        st.image(article["urlToImage"], width=300)
                                    
                                    description = article.get('description', '')
                                    if description:
                                        st.markdown(f"**📝 Summary:** {description}")
                                    
                                    st.markdown("**💡 Why This Matters:** This news could affect stock prices and market sentiment.")
                        else:
                            st.error("Unable to load news")
            
            with guide_tab3:
                st.markdown("#### 🎯 **Market Mood**")
                st.markdown("*Simple explanation of how the overall market is doing*")
                
                if st.button("🎯 Check Market Mood", type="primary"):
                    with st.spinner("Analyzing market mood..."):
                        sentiment = get_simple_market_sentiment()
                        st.markdown(f"### {sentiment}")
                        
                        # Add simple explanation
                        if "Bull Market" in sentiment:
                            st.markdown("**🐂 What this means:** A bull market means most stocks are going up! This is generally good for investors.")
                        elif "Bear Market" in sentiment:
                            st.markdown("**🐻 What this means:** A bear market means most stocks are going down. This can be challenging for investors.")
                        elif "Mostly Positive" in sentiment:
                            st.markdown("**📈 What this means:** More stocks are going up than down. This is a positive sign for the market.")
                        elif "Mixed" in sentiment:
                            st.markdown("**📊 What this means:** Some stocks are going up, some are going down. The market is uncertain.")
                        
                        st.markdown("**💡 Tip:** Market mood changes daily. Don't panic over short-term changes!")
            
            with guide_tab4:
                st.markdown("#### 💡 **Investing Tips**")
                st.markdown("*Simple advice to help you get started with investing*")
                
                tips = get_beginner_tips()
                for tip in tips:
                    st.markdown(tip)
                
                st.markdown("---")
                st.markdown("#### 📚 **Learning Resources**")
                st.markdown("""
                **📖 Books to Read:**
                - "The Intelligent Investor" by Benjamin Graham
                - "A Random Walk Down Wall Street" by Burton Malkiel
                - "The Little Book of Common Sense Investing" by John Bogle
                
                **🌐 Websites to Visit:**
                - Investopedia.com (for definitions)
                - Yahoo Finance (for stock data)
                - SEC.gov (for company information)
                
                **🎓 Courses to Take:**
                - Khan Academy Finance
                - Coursera Investment courses
                - Local community college classes
                """)

        # END OF STOCK MARKET GUIDE

        # Use form for better Enter key handling
        with st.form("search_form", clear_on_submit=False):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                # Empty space to align with market statistics
                search_input = st.text_input(
                    "Enter search term (e.g., 'Apple', 'Tesla', 'Bitcoin', 'Federal Reserve')",
                    value=st.session_state.search_query,
                    placeholder="Search for specific stocks, companies, or financial topics...",
                    key="search_input"
                )
            
            with col2:

                st.write("")
                st.write("")
                search_button = st.form_submit_button("🔍 Search", type="primary", use_container_width=True)

        # Handle search on form submission (Enter key or button click)
        if search_button and search_input.strip():
            st.session_state.search_query = search_input.strip()
            st.session_state.is_search_mode = True
            with st.spinner("Searching for news..."):
                search_results = search_stock_news(st.session_state.search_query)
                st.session_state.search_results = search_results
                
                # Extract stock symbol and get stock data
                stock_symbol = extract_stock_symbol(st.session_state.search_query)
                if stock_symbol:
                    st.session_state.stock_data = get_stock_data(stock_symbol)
                    st.session_state.related_stocks = get_related_stocks(stock_symbol)
                else:
                    st.session_state.stock_data = None
                    st.session_state.related_stocks = []


        # Fetch general news if not in search mode
        if st.session_state.refresh_news and not st.session_state.is_search_mode:
            with st.spinner("Fetching latest stock news..."):
                news_response = get_stock_news()
                st.session_state.news_data = news_response
                st.session_state.refresh_news = False

        # Display news based on mode
        if st.session_state.is_search_mode and st.session_state.search_query:
            # Search results view
            st.markdown(f"### 🔍 Search Results for: **{st.session_state.search_query}**")
            
            # Display stock data if available
            if st.session_state.stock_data:
                stock = st.session_state.stock_data
                st.markdown("### 📈 Stock Information")
                
                
                # Create columns for stock data and related stocks
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    # Stock name and symbol
                    st.markdown(f"**{stock['name']} ({stock['symbol']})**")
                    
                    # Price and change with color coding
                    change_color = "green" if stock['change'] >= 0 else "red"
                    change_symbol = "📈" if stock['change'] >= 0 else "📉"
                    
                    st.markdown(f"""
                    <div style="display: flex; align-items: center; gap: 20px; margin: 10px 0;">
                        <div style="font-size: 2em; font-weight: bold;">${stock['price']}</div>
                        <div style="color: {change_color}; font-size: 1.2em;">
                            {change_symbol} {stock['change']:+.2f} ({stock['change_pct']:+.2f}%)
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Additional stock info using Streamlit components
                    col_info1, col_info2, col_info3 = st.columns(3)
                    with col_info1:
                        st.metric("Previous Close", f"${stock['prev_close']}")
                    with col_info2:
                        st.metric("Currency", stock['currency'])
                    with col_info3:
                        if stock['market_cap'] > 0:
                            market_cap_formatted = f"${stock['market_cap']/1e12:.2f}T" if stock['market_cap'] > 1e12 else f"${stock['market_cap']/1e9:.2f}B"
                            st.metric("Market Cap", market_cap_formatted)
                        else:
                            st.metric("Market Cap", "N/A")
                    
                    st.markdown('</div>', unsafe_allow_html=True)
                
                with col2:
                    # Related stocks table
                    if st.session_state.related_stocks:
                        st.markdown("### 🔗 Related Stocks")
                        
                        # Create a table for related stocks
                        related_data = []
                        for stock in st.session_state.related_stocks:
                            change_color = "🟢" if stock['change'] >= 0 else "🔴"
                            related_data.append({
                                "Symbol": stock['symbol'],
                                "Price": f"${stock['price']}",
                                "Change": f"{change_color} {stock['change_pct']:+.2f}%"
                            })
                        
                        if related_data:
                            df_related = pd.DataFrame(related_data)
                            st.dataframe(df_related, use_container_width=True, hide_index=True)
            
            if st.session_state.search_results:
                # Show search results as a list with toggle
                for i, article in enumerate(st.session_state.search_results):
                    source = article.get("source", {})
                    
                    # Create expandable container for search results
                    with st.expander(f"📄 {article.get('title', 'No Title')}", expanded=True):
                        # Article title as clickable link
                        if article.get('url'):
                            st.markdown(f"**[Read Full Article →]({article.get('url')})**")
                        
                        # Article image
                        if article.get("urlToImage"):
                            st.image(article["urlToImage"], width=500)
                        
                        # Article metadata
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.markdown(f"**📰 Source:** {source.get('name', 'Unknown')}")
                        with col2:
                            st.markdown(f"**✍️ Author:** {article.get('author', 'Unknown')}")
                        with col3:
                            published_date = article.get('publishedAt', 'Unknown')
                            if published_date != 'Unknown':
                                try:
                                    from datetime import datetime
                                    dt = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                                    formatted_date = dt.strftime('%Y-%m-%d %H:%M')
                                    st.markdown(f"**📅 Published:** {formatted_date}")
                                except:
                                    st.markdown(f"**📅 Published:** {published_date}")
                            else:
                                st.markdown(f"**📅 Published:** {published_date}")
                        
                        # Article description
                        description = article.get('description', '')
                        if description:
                            st.markdown(f"**📝 Summary:** {description}")
                        
                        # External link button
                        if article.get('url'):
                            st.markdown(f"[🔗 Open External Link]({article.get('url')})")
                    
                    # Add separator between articles
                    if i < len(st.session_state.search_results) - 1:
                        st.markdown("---")
            else:
                st.warning(f"🔍 No news found for '{st.session_state.search_query}'. Try a different search term.")
            
            # Clear search button
            if st.button("🔍 Clear Search", help="Return to General News"):
                st.session_state.is_search_mode = False
                st.session_state.search_query = ""
                st.session_state.search_results = []
                st.session_state.stock_data = None
                st.session_state.related_stocks = []
                st.rerun()
        else:
            # General news view (original format - no collapsible)
            news_response = st.session_state.news_data
            if isinstance(news_response, list) and news_response:
                for article in news_response:
                    source = article.get("source", {})
                    st.markdown(f"### [{article.get('title', 'No Title')}]({article.get('url', '')})")
                    if article.get("urlToImage"):
                        st.image(article["urlToImage"], width=400)
                    st.markdown(f"**Source:** {source.get('name', 'Unknown')}")
                    st.markdown(f"**Author:** {article.get('author', 'Unknown')}")
                    st.markdown(f"**Published at:** {article.get('publishedAt', 'Unknown')}")
                    st.markdown(f"{article.get('description', '')}")
                    st.markdown('---')
            elif isinstance(news_response, list) and not news_response:
                st.warning("📰 No news available at the moment. Please try refreshing.")
            else:
                st.write(news_response)




if __name__ == "__main__":
    main()
