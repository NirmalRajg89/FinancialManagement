from controllers.router_agent import route_query
import streamlit as st
import time
from langchain.schema import AIMessage, HumanMessage

def main():
    st.set_page_config(page_title="Financial Advisor and Wellness", page_icon="💰")
    st.title("💼 Financial Advisor")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [
            AIMessage(content="Hello! How can I help you today?")
        ]

    # Display chat history
    for message in st.session_state.chat_history:
        # Convert Langchain messages to streamlit-friendly roles
        if isinstance(message, AIMessage):
            role = "assistant"
        elif isinstance(message, HumanMessage):
            role = "user"
        else:
            role = "assistant"  # default fallback
        with st.chat_message(role):
            st.markdown(message.content)

    # Input from user
    user_query = st.chat_input("Your message")

    if user_query:
        # Add user message to chat history
        human_msg = HumanMessage(content=user_query)
        st.session_state.chat_history.append(human_msg)

        with st.chat_message("user"):
            st.markdown(user_query)

        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                output = route_query(user_query)

            # If output is a dict with 'output' key
            if isinstance(output, dict) and "output" in output:
                output = output["output"]

            ai_msg = AIMessage(content=output)
            st.session_state.chat_history.append(ai_msg)

            # Typing effect
            output_placeholder = st.empty()
            full_response = ""
            for char in output:
                full_response += char
                output_placeholder.markdown(full_response + "▌")
                time.sleep(0.01)

            output_placeholder.markdown(full_response)

if __name__ == "__main__":
    main()
