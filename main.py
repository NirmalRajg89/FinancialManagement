import base64
import json
import os

import pandas as pd
import streamlit as st

from controllers.employee_agent import generate_financial_summary_langchain, get_user_summary_data, load_customer_data
from controllers.flow import build_agent
from controllers.newsAPI_controller import get_stock_news
# from controllers.router_agent import route_query
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
    # Always initialize chat_history if not present

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
            options=["Stock News", "Financial Advisor", "Fitness Wellness","Tracker","Goal based"],
            icons=["clipboard-data", "graph-up-arrow", "heart-pulse-fill","graph-up-arrow","clipboard-data"],
            menu_icon="cast",
            default_index=0,
            # orientation = "horizontal",
        )


    # Sidebar for Mode Selection
    #mode = st.sidebar.radio("Select Mode:", options=["Latest Stock Updates", "Financial Advisor", "Fitness and Wellness"], index=1)

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

            # Now it's safe to display chat history
        for message in st.session_state.chat_history:
            role = "assistant" if isinstance(message, AIMessage) else "user"
            with st.chat_message(role):
                st.markdown(message.content)

        user_query = st.chat_input("Your message")

        if user_query:
            human_msg = HumanMessage(content=user_query)
            st.session_state.chat_history.append(human_msg)

            with st.chat_message("user"):
                st.markdown(user_query)

            with st.chat_message("assistant"):
                with st.spinner("Getting expert advice......"):
                    # output = route_query(user_query)
                    response = app.invoke({"question": user_query})
                    print(response)
                    output = response.get("answer", "Sorry, something went wrong.")

                # if isinstance(output, dict) and "output" in output:
                #     output = output["output"]

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
                    #st.markdown(response)
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
                # Display user query
                st.markdown(f"## 📄 Summary for **{name}**")

                # Display financial summary
                st.markdown(f"""
                   **💳 Credit Score:** `{result['credit_score']}`  
                   **💰 Monthly Income:** `${result['monthly_income']:,.2f}`  
                   **🏦 Total Assets:** `${result['total_assets']:,.2f}`  
                   **📉 Total Liabilities:** `${result['total_liabilities']:,.2f}`
                   """)

                # Optional AI summary
                #if st.button("✨ Generate AI Summary"):
                ai_summary = generate_financial_summary_langchain(
                    result["name"],
                    result["credit_score"],
                    result["total_assets"],
                    result["total_liabilities"]
                )
                st.markdown("### 🤖 AI Summary")
                st.markdown(f"> {ai_summary}")
    elif mode == "Goal based":
        with open("data/customer.json") as f:
            data = json.load(f)
        amanda_data = data["Amanda"]
        st.set_page_config(page_title="Investment Planner")
        st.title("📊 Personalized Investment Planning for Amanda")

        # --- Collect Dynamic Inputs from User ---
        st.subheader("Enter Your Investment Preferences")

        goal_options = ["Retirement", "Buy Home", "Travel", "Education", "Wealth Building"]
        goals = st.multiselect("Financial Goals", goal_options, default=["Retirement"])

        risk_level = st.selectbox("Risk Tolerance", ["Low", "Moderate", "High"], index=1)

        monthly_contribution = st.slider("How much can you invest monthly?", min_value=100, max_value=5000, step=100,
                                         value=1000)

        # On submit
        if st.button("Generate Investment Plan"):
            st.info("Generating personalized investment plan...")

            # Merge Amanda's data + user inputs
            input_data = {
                "profile": amanda_data,
                "user_inputs": {
                    "goals": goals,
                    "risk_tolerance": risk_level.lower(),
                    "monthly_contribution": monthly_contribution
                }
            }

            agent = build_agent()
            result = agent.invoke(input_data)

            st.subheader("🧠 Your Investment Plan")
            st.markdown(result.content)
    else:
        # Handle initial state
        if "refresh_news" not in st.session_state:
            st.session_state.refresh_news = True
        if "news_data" not in st.session_state:
            st.session_state.news_data = []

        # Heading with refresh button on the right
        col1, col2 = st.columns([10, 3])
        with col1:
            st.markdown("## 📰 Latest Stock Updates")
        with col2:
            if st.button("## ♻️ Update News", help="Refresh News"):
                st.session_state.refresh_news = True

        # Fetch news if needed
        if st.session_state.refresh_news:
            with st.spinner("Fetching latest stock news..."):
                news_response = get_stock_news()
                st.session_state.news_data = news_response
                st.session_state.refresh_news = False

        # Display news
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
