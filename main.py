import base64
import json
from io import StringIO

import pandas as pd
import streamlit as st
from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import ChatOpenAI
from controllers.agent_controller import create_agent_executor, create_investment_summary
from controllers.employee_agent import generate_financial_summary_langchain, get_user_summary_data, load_customer_data
from controllers.flow import get_dynamic_allocation, format_allocation_table
from controllers.newsAPI_controller import get_stock_news
from langchain.schema import AIMessage, HumanMessage
import time
from controllers.wellness_controller import get_wellness_response, extract_youtube_links
from streamlit_option_menu import option_menu
from controllers.router_graph import app


def img_to_base64(image_path):
    """Convert image to base64."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        print(f"Error converting image to base64: {str(e)}")
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
    st.set_page_config(layout="wide")
    st.set_page_config(page_title="Financial Advisor and Wellness", page_icon="💰")

    # Insert custom CSS for glowing effect
    st.markdown(
        """
        <style>
        .cover-glow {
            width: 100%;
            height: auto;
            padding: 3px;
            box-shadow: 
                0 0 5px #330000,
                0 0 10px #660000,
                0 0 15px #990000,
                0 0 20px #CC0000,
                0 0 25px #FF0000,
                0 0 30px #FF3333,
                0 0 35px #FF6666;
            position: relative;
            z-index: -1;
            border-radius: 45px;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Load and display sidebar image
    img_path = "imgs/rate_logo1.png"
    img_base64 = img_to_base64(img_path)
    if img_base64:
        st.sidebar.markdown(
            f'<img src="data:image/png;base64,{img_base64}" class="cover-glow">',
            unsafe_allow_html=True,
        )

    st.sidebar.markdown("---")

    with st.sidebar:
        mode = option_menu(
            menu_title="Menu",
            options=["Stock News", "Financial Advisor", "Fitness Wellness", "Goal based"],
            icons=["clipboard-data", "graph-up-arrow", "heart-pulse-fill", "graph-up-arrow"],
            menu_icon="cast",
            default_index=3,
        )

    st.sidebar.markdown("---")

    # Add vertical space to push the logo to the bottom
    st.sidebar.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)
    st.sidebar.markdown("<br><br><br>", unsafe_allow_html=True)  # Adjust as needed

    # Display the altimetrik logo at the bottom of the sidebar
    img_path = "imgs/altimetrik.png"
    img_base64 = img_to_base64(img_path)
    if img_base64:
        st.sidebar.markdown(
            f'<img src="data:image/png;base64,{img_base64}">',
            unsafe_allow_html=True,
        )

    if mode == "Financial Advisor":
        st.title("💼 Financial Advisor")

        if "chat_history" not in st.session_state:
            st.session_state.chat_history = [AIMessage(content="Hello! How can I help you today?")]

        # Display chat history
        for message in st.session_state.chat_history:
            role = "assistant" if isinstance(message, AIMessage) else "user"
            with st.chat_message(role):
                st.markdown(message.content)

        # Get user input
        user_query = st.chat_input("Your message")

        if user_query:
            human_msg = HumanMessage(content=user_query)
            st.session_state.chat_history.append(human_msg)

            with st.chat_message("user"):
                st.markdown(user_query)

            with st.chat_message("assistant"):
                with st.spinner("Getting expert advice......"):
                    response = app.invoke({"question": user_query})
                    print(response)
                    output = response.get("answer", "Sorry, something went wrong.")

                ai_msg = AIMessage(content=output)
                st.session_state.chat_history.append(ai_msg)

                output_placeholder = st.empty()
                full_response = ""
                for char in output:
                    full_response += char
                    output_placeholder.markdown(full_response + "▌")
                    time.sleep(0.01)

                output_placeholder.markdown(full_response)

    elif mode == "Fitness Wellness":
        st.title("🧘 Your Fitness & Wellness Coach")
        st.write("Ask me anything about workouts, yoga, mental wellness, or diet. I'll even share videos when helpful.")

        if "chat_history_wellness" not in st.session_state:
            st.session_state.chat_history_wellness = []

        for question, answer in st.session_state.chat_history_wellness:
            with st.chat_message("user"):
                st.markdown(question)
            with st.chat_message("assistant"):
                st.markdown(answer)
                for link in extract_youtube_links(answer):
                    st.video(link)

        user_input = st.chat_input("What do you want help with today?")

        if user_input:
            st.chat_message("user").markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Getting expert advice..."):
                    response = get_wellness_response(user_input)
                    output_placeholder = st.empty()
                    full_response = ""
                    for char in response:
                        full_response += char
                        output_placeholder.markdown(full_response + "▌")
                        time.sleep(0.01)
                    for link in extract_youtube_links(response):
                        st.video(link)
            output_placeholder.markdown(full_response)
            st.session_state.chat_history_wellness.append((user_input, response))

    # Dummy function placeholder for your AI agent
    if mode == "Goal based":

        # Load user data
        with open("data/customer.json") as f:
            all_user_data = json.load(f)

        st.set_page_config(page_title="Investment Planner", layout="wide")
        st.title("📊 Personalized Investment Planning")

        # Step 1: Ask for name
        user_name = st.text_input("Enter your name to begin:")

        if user_name:
            if user_name not in all_user_data:
                st.error(f"No data found for user: {user_name}")
                st.stop()

            user_profile = all_user_data[user_name]

            # Step 2: Financial summary
            st.subheader(f"💼 {user_name}'s Financial Summary")
            employment = user_profile["employment"]
            assets = user_profile["assets"]
            liabilities = user_profile["liabilities"]
            total_liabilities = sum(l["unpaidBalanceAmount"] for l in liabilities)

            summary_data = {
                "Monthly Income ($)": [employment["monthlyIncomeAmount"]],
                "Credit Score": [employment["creditScore"]],
                "Total Assets ($)": [sum(a["total"] for a in assets)],
                "Total Liabilities ($)": total_liabilities,
            }
            st.table(pd.DataFrame(summary_data))

            # Step 3: Preferences
            st.subheader("🎯 Investment Preferences")

            plan_type = st.radio("Select Plan Type", ["Short-term", "Long-term"], horizontal=True)

            # Calculate disposable income
            disposable_income = employment["monthlyIncomeAmount"] - total_liabilities

            if plan_type == "Short-term":
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    goals = st.selectbox("Goal", ["Investment", "Education", "Car", "Bike"])

                with col2:
                    tenure = st.selectbox("Duration", ["5 years","6 months", "1 year", "2 years", "3 years"])

                with col3:
                    default_contribution = round(disposable_income * 0.4, 2)
                    monthly_contribution = st.number_input(
                        "Monthly Investment - 60% (Income - Expense)",
                        min_value=100.0,
                        max_value=float(employment["monthlyIncomeAmount"]),
                        value=default_contribution,
                        step=100.0
                    )

                with col4:
                    goal_amount = st.number_input(
                        "Expected Goal Amount",
                        min_value=1000.0,
                        max_value=1_00_00_000.0,
                        step=1000.0,
                        value=10_00_000.0
                    )

            elif plan_type == "Long-term":
                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    goals = st.selectbox("Goal", ["Retirement", "Home", "Others"])

                with col2:
                    current_age = st.number_input("Current Age", min_value=18, max_value=70, value=30, step=1)
                    expected_age = st.number_input("Expected Age at Goal", min_value=current_age + 1, max_value=100,
                                                   value=60, step=1)
                    tenure = f"{expected_age - current_age} years"
                    st.text_input("Duration", tenure, disabled=True)

                with col3:
                    default_contribution = round(disposable_income * 0.6, 2)
                    monthly_contribution = st.number_input(
                        "Investment(60% Salary - Liabilities)",
                        min_value=100.0,
                        max_value=float(employment["monthlyIncomeAmount"]),
                        value=default_contribution,
                        step=100.0
                    )

                with col4:
                    goal_amount = st.number_input(
                        "Expected Goal Amount",
                        min_value=1000.0,
                        max_value=5_00_00_000.0,
                        step=10000.0,
                        value=2000000.0
                    )

            risk_level = user_profile.get("riskTolerance", "Moderate")

            # Map risk tolerance to color and meaning
            risk_info = {
                "Low": {
                    "color": "#e74c3c",  # Green
                    "meaning": "Prefers safety, avoids loss, low risk acceptance"
                },
                "Moderate": {
                    "color": "#f1c40f",  # Yellow
                    "meaning": "Balanced approach, some risk acceptable"
                },
                "High": {
                    "color": "#2ecc71",  # Red
                    "meaning": "Comfortable with big ups and downs, seeks high returns"
                }
            }

            # Default if unknown risk level
            info = risk_info.get(risk_level, {
                "color": "#95a5a6",
                "meaning": "Risk tolerance data not available"
            })

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
                    📌 Risk Tolerance Level (based on profile): <strong>{risk_level} - ({info['meaning']})</strong><br>
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

            static_vars = {
                "monthly_contribution": str(monthly_contribution),
                "tenure": str(tenure),
                "goal_amount": str(goal_amount),
                "risk_tolerance": str(risk_level),
                "investment_options": investment_options,
                "formatted_allocation_table": formatted_table,
            }

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
                                "tenure": tenure,
                                "monthly_contribution": monthly_contribution,
                                "goal_amount": goal_amount

                            }
                        }
                        # Create agent
                        st.session_state.agent = create_investment_summary(static_vars)

                        plan_prompt = {
                            "profile": user_profile,
                            "user_inputs": st.session_state.investment_input_data["user_inputs"],
                            "tenure": tenure,
                            "monthly_contribution": monthly_contribution,
                            "goal_amount": goal_amount,
                            "risk_tolerance": risk_level,
                            "investment_options": investment_options,
                            "question": "Generate a detailed investment plan based on the above."
                        }

                        user_msg = f"Generate {plan_type} plan — goals: {goals}, risk: {risk_level}, tenure: {tenure}, contribution: {monthly_contribution}, Goal to achieve: {goal_amount}"
                        st.session_state.chat_history.append({"role": "user", "content": user_msg})

                        full_response = ""
                        response = st.session_state.agent.ask(plan_prompt)

                        response_placeholder = st.empty()
                        for char in response:
                            full_response += char
                            response_placeholder.markdown(full_response + "▌")
                            time.sleep(0.001)

                        st.session_state.chat_history.append({"role": "assistant", "content": full_response})
                        time.sleep(0.02)
                        response_placeholder.empty()

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

                    follow_up_context = {"question": user_query}
                    st.session_state.agent = create_agent_executor(static_vars)
                    with st.chat_message("assistant"):
                        with st.spinner("Getting expert advice..."):
                            full_response = ""
                            response = st.session_state.agent.ask(follow_up_context)
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

        col1, col2 = st.columns([10, 3])
        with col1:
            st.markdown("## 📰 Latest Stock Updates")
        with col2:
            if st.button("## ♻️ Update News", help="Refresh News"):
                st.session_state.refresh_news = True

        if st.session_state.refresh_news:
            with st.spinner("Fetching latest stock news..."):
                news_response = get_stock_news()
                st.session_state.news_data = news_response
                st.session_state.refresh_news = False

        news_response = st.session_state.news_data
        if isinstance(news_response, list):
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
        else:
            st.write(news_response)


if __name__ == "__main__":
    main()
