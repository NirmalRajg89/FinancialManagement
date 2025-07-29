import base64
import streamlit as st
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
def main():
    st.set_page_config(page_title="Financial Advisor and Wellness", page_icon="💰", layout="centered")

    # Override the max width of the central chat container to match ChatGPT
    st.markdown("""
            <style>
            /* Main chat content area */
            .block-container {
                max-width: 900px !important;
                margin: 0 auto;
                padding-left: 2rem;
                padding-right: 2rem;
            }
            .block-container > div:first-child {
                padding-top: 0rem !important;
                margin-top: 0rem !important;
            }

            h1 {
                margin-top: 0rem !important;
                padding-top: 0rem !important;
            }
            </style>
        """, unsafe_allow_html=True)

        # Insert custom CSS for glowing effect
    st.markdown("""
        <style>
        /* Sidebar as a full-height flex column */
        # [data-testid="stSidebar"] > div:first-child {
        #     display: flex;
        #     flex-direction: column;
        #     justify-content: space-between;
        #     height: 100%;
        # }
        [data-testid="stSidebarUserContent"] > div:first-child > [data-testid="stVerticalBlock"] {
            height: 80vh !important;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        

        .sidebar-header, .sidebar-footer {
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 10px 0;
        }

        .sidebar-content {
            flex-grow: 1;
            display: flex;
            flex-direction: column;
            justify-content: flex-start;
            gap: 1.5rem;
            padding: 10px 0;
        }

        .cover-glow {
            width: 100%;
            padding: 3px;
            border-radius: 45px;
        }
        </style>
    """, unsafe_allow_html=True)

    # -- Load Image Assets --
    rate_logo_path = "imgs/rate_logo1.png"
    altimetrik_logo_path = "imgs/altimetrik.png"

    rate_logo_b64 = img_to_base64(rate_logo_path)
    altimetrik_logo_b64 = img_to_base64(altimetrik_logo_path)

    # -- Render Sidebar Layout --
    # Load and convert logo images to base64
    rate_logo_b64 = img_to_base64("imgs/rate_logo1.png")
    altimetrik_logo_b64 = img_to_base64("imgs/altimetrik.png")

    # Render sidebar content
    with st.sidebar:
        # -- Header: Rate.com Logo --
        if rate_logo_b64:
            st.markdown(f"""
            <div class="sidebar-header">
                <img src="data:image/png;base64,{rate_logo_b64}" class="cover-glow">
            </div>
            """, unsafe_allow_html=True)

        # -- Middle Content --
        st.markdown("<div class='sidebar-content'>", unsafe_allow_html=True)
        st.markdown("---")
        mode = st.radio("Select Mode:", options=["Latest Stock Updates", "Financial Advisor"], index=1)
        st.markdown("---")
        st.markdown("</div>", unsafe_allow_html=True)

        # -- Footer: Altimetrik Logo --
        if altimetrik_logo_b64:
            st.markdown(f"""
            <div class="sidebar-footer">
                <img src="data:image/png;base64,{altimetrik_logo_b64}" width="130">
            </div>
            """, unsafe_allow_html=True)

    if mode == "Financial Advisor":
        st.title("💼 Financial Advisor")
        if "chat_history" not in st.session_state:
            st.session_state.chat_history = [AIMessage(content="Hello! How can I help you today?")]

            # Now it's safe to display chat history
        # Show chat history
        # Show chat history
        for message in st.session_state.chat_history:
            role = "assistant" if isinstance(message, AIMessage) else "user"

            if role == "user":
                with st.container():
                    st.markdown(
                        f"""
                        <div style='
                            display: flex;
                            justify-content: flex-end;
                            margin-bottom: 20px;
                            width: 100%;
                        '>
                            <div style='
                                background-color: #F0F0F0;
                                color: black;
                                padding: 10px 15px;
                                border-radius: 15px;
                                max-width: 500px;
                                word-wrap: break-word;
                                font-size: 16px;
                                line-height: 2;
                                text-align: justify;
                            '>
                                {message.content}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            else:
                with st.container():
                    st.markdown(
                        f"""
                        <div style='
                            display: flex;
                            justify-content: flex-start;
                            margin-bottom: 20px;
                            width: 100%;
                        '>
                            <div style='
                                font-size: 16px;
                                line-height: 2;
                                text-align: justify;
                                width: 100%;
                            '>
                                {message.content}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

        st.markdown("""
            <style>
            /* Set the main chat input width */
            div[data-testid="stBottomBlockContainer"] {
                max-width: 900px !important;
                margin: 0 auto;
            }

            /* Optional: remove top padding */
            div[data-testid="stChatInput"] {
                padding-top: 0rem;
            }
            </style>
        """, unsafe_allow_html=True)

        # Input
        user_query = st.chat_input("Your message")

        if user_query:
            # Append and show user message
            human_msg = HumanMessage(content=user_query)
            st.session_state.chat_history.append(human_msg)

            with st.container():
                st.markdown(
                    f"""
                    <div style='
                        display: flex;
                        justify-content: flex-end;
                        margin-bottom: 20px;
                        width: 100%;
                    '>
                        <div style='
                            background-color: #F0F0F0;
                            color: black;
                            padding: 10px 15px;
                            border-radius: 15px;
                            max-width: 500px;
                            word-wrap: break-word;
                            font-size: 16px;
                            line-height: 2;  
                        '>
                            {user_query}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            with st.spinner("Thinking..."):
                output = route_query(user_query)

            if isinstance(output, dict) and "output" in output:
                output = output["output"]

            ai_msg = AIMessage(content=output)
            st.session_state.chat_history.append(ai_msg)

            # Stream assistant response
            full_response = ""
            output_placeholder = st.empty()

            for char in output:
                full_response += char
                output_placeholder.markdown(
                    f"""
                    <div style='
                        display: flex;
                        justify-content: flex-start;
                        margin-bottom: 10px;
                        width: 100%;
                    '>
                        <div style='
                            font-size: 16px;
                            line-height: 2;
                            text-align:justify;
                            width: 100%;
                        '>
                            {full_response}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                time.sleep(0.01)

            # Final assistant message (no typing cursor)
            output_placeholder.markdown(
                f"""
                <div style='
                    display: flex;
                    justify-content: flex-start;
                    margin-bottom: 10px;
                    width: 100%;
                '>
                    <div style='
                        font-size: 16px;
                        line-height: 1.5;
                        width: 100%;
                    '>
                        {full_response}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

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
