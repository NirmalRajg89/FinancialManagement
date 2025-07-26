import base64
import streamlit as st
from controllers.newsAPI_controller import get_stock_news
from controllers.router_agent import route_query
from langchain.schema import AIMessage, HumanMessage
import time
from controllers.wellness_controller import get_wellness_response, extract_youtube_links
from streamlit_option_menu import option_menu

def img_to_base64(image_path):
    """Convert image to base64."""
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception as e:
        print(f"Error converting image to base64: {str(e)}")
        return None
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
            menu_title="Main Menu",
            options=["Latest Stock News", "Financial Advisor", "Fitness & Wellness"],
            icons=["clipboard-data", "cash-coin", "heart-pulse-fill"],
            menu_icon="cast",
            default_index=0,
            # orientation = "horizontal",
        )


    # Sidebar for Mode Selection
    #mode = st.sidebar.radio("Select Mode:", options=["Latest Stock Updates", "Financial Advisor", "Fitness and Wellness"], index=1)

    st.sidebar.markdown("---")

    # Add vertical space to push the logo to the bottom
    st.sidebar.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)
    st.sidebar.markdown("<br><br><br><br>", unsafe_allow_html=True)  # Adjust as needed

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
                    output = route_query(user_query)

                if isinstance(output, dict) and "output" in output:
                    output = output["output"]

                ai_msg = AIMessage(content=output)
                st.session_state.chat_history.append(ai_msg)

                output_placeholder = st.empty()
                full_response = ""
                for char in output:
                    full_response += char
                    output_placeholder.markdown(full_response + "▌")
                    time.sleep(0.01)

                output_placeholder.markdown(full_response)
    elif mode == "Fitness & Wellness":
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
                    st.markdown(response)
                    for link in extract_youtube_links(response):
                        st.video(link)

            st.session_state.chat_history_wellness.append((user_input, response))

    else:
        # Get and display stock news in the main area
        with st.spinner("Fetching latest stock news..."):
            news_response = get_stock_news()
            st.markdown("## 📰 Latest Stock Updates")
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
