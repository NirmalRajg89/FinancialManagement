import base64
import json
import pandas as pd
import streamlit as st
from langchain.memory import ConversationSummaryBufferMemory
from langchain_openai import ChatOpenAI
from controllers.agent_controller import create_agent_executor
from controllers.employee_agent import generate_financial_summary_langchain, get_user_summary_data, load_customer_data
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
            options=["Stock News", "Financial Advisor", "Fitness Wellness", "Tracker", "Goal based"],
            icons=["clipboard-data", "graph-up-arrow", "heart-pulse-fill", "graph-up-arrow", "clipboard-data"],
            menu_icon="cast",
            default_index=4,
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

    elif mode == "Tracker":
        st.title("📊 Financial Tracker Agent")
        st.write("AI-powered customer financial summary using LangChain + OpenAI")

        data = load_customer_data()
        if not data:
            st.error("❌ Customer data file not found.")
            return

        name = st.text_input("🔍 Enter customer name (e.g., Amanda,Brad,Chris,David):")

        if name:
            result, error = get_user_summary_data(name, data)

            if error:
                st.warning(f"⚠️ {error}")
            else:
                st.markdown(f"## 📄 Summary for **{name}**")
                st.markdown(f"""
                   **💳 Credit Score:** `{result['credit_score']}`  
                   **💰 Monthly Income:** `${result['monthly_income']:,.2f}`  
                   **🏦 Total Assets:** `${result['total_assets']:,.2f}`  
                   **📉 Total Liabilities:** `${result['total_liabilities']:,.2f}`
                   """)

                ai_summary = generate_financial_summary_langchain(
                    result["name"],
                    result["credit_score"],
                    result["total_assets"],
                    result["total_liabilities"]
                )
                st.markdown("### 🤖 AI Summary")
                st.markdown(f"> {ai_summary}")

    elif mode == "Goal based":

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

            summary_data = {
                "Monthly Income": [employment["monthlyIncomeAmount"]],
                "Credit Score": [employment["creditScore"]],
                "Total Assets": [sum(a["total"] for a in assets)],
                "Total Liabilities": [sum(l["unpaidBalanceAmount"] for l in liabilities)],
                "Debt-to-Income Ratio": [round(
                    sum(l["monthlyPaymentAmount"] for l in liabilities) / employment["monthlyIncomeAmount"], 2
                )]
            }
            st.table(pd.DataFrame(summary_data))

            # Step 3: Preferences
            st.subheader("🎯 Investment Preferences")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                goal_options = ["Retirement", "Buy Home", "Travel", "Education", "Wealth Building",
                                "Emergency Fund", "Risk Tolerance"]
                goals = st.multiselect("Select your goals", goal_options)

            with col2:
                tenure = st.selectbox("Select risk tolerance", ["1 year", "3 year", "5 year", "7 year", "9 year", "10 year", "15 year" ])

            with col3:
                risk_level = st.selectbox("Select risk tolerance", ["Low", "Moderate", "High"])

            with col4:
                default_contribution = round(employment["monthlyIncomeAmount"] * 0.6, 2)
                monthly_contribution = st.number_input(
                    "Monthly Contribution",
                    min_value=100.0,
                    max_value=float(employment["monthlyIncomeAmount"]),
                    value=default_contribution,
                    step=100.0
                )
            # Step 4: Generate Plan
            if goals and risk_level and monthly_contribution:
                if st.button("Generate Investment Plan"):
                    with st.spinner("Getting expert advice..."):
                        st.session_state.investment_input_data = {
                            "profile": user_profile,
                            "user_inputs": {
                                "goals": goals,
                                "risk_tolerance": risk_level.lower(),
                                "tenure": tenure,
                                "monthly_contribution": monthly_contribution
                            }
                        }

                        # Create agent
                        st.session_state.agent = create_agent_executor()

                        # Ask the agent for the investment plan
                        plan_prompt = {
                            "profile": user_profile,
                            "user_inputs": st.session_state.investment_input_data["user_inputs"],
                            "task": "Generate a detailed investment plan based on the above."
                        }

                        # Animated streaming effect
                        output_placeholder = st.empty()
                        full_response = ""
                        response = st.session_state.agent.ask(plan_prompt)
                        for char in response:
                            full_response += char
                            output_placeholder.markdown(full_response + "▌")
                            time.sleep(0.01)

                        # Store final response for later chat context
                        st.session_state.generated_plan = full_response
                        st.session_state.chat_history = []

            # Step 5: Show plan + chat
            if "generated_plan" in st.session_state:
                st.subheader("💬 Ask Follow-up Financial Questions")
                if "chat_history" not in st.session_state:
                    st.session_state.chat_history = []

                # Display chat history
                for msg in st.session_state.chat_history:
                    if msg["role"] == "user":
                        st.markdown(f"**You:** {msg['content']}")
                    else:
                        st.markdown(f"**Advisor:** {msg['content']}")

                # Chat input
                user_query = st.chat_input("Type your question and press Enter...")
                if user_query:
                    follow_up_context = {
                        "profile": user_profile,
                        "user_inputs": st.session_state.investment_input_data["user_inputs"],
                        "question": user_query
                    }

                    with st.spinner("Thinking..."):
                        output_placeholder = st.empty()
                        full_response = ""
                        response = st.session_state.agent.ask(follow_up_context)
                        for char in response:
                            full_response += char
                            output_placeholder.markdown(full_response + "▌")
                            time.sleep(0.01)

                        st.session_state.chat_history.append({"role": "user", "content": user_query})
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
