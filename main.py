from controllers.router_agent import route_query
import streamlit as st
import time
from langchain.schema import AIMessage, HumanMessage

def main():
    st.set_page_config(page_title="Financial Advisor", page_icon="💰")
    st.title("💼 Financial Advisor")

    if "chat_history" not in st.session_state:
        st.session_state.chat_history = [AIMessage(content="Hello! How can I help you today?")]

   # st.download_button("Download Chat", data=st.session_state.chat_history, file_name="chat_history.txt")
    # Display chat history
    for message in st.session_state.chat_history:
        role = "AI" if isinstance(message, AIMessage) else "Human"
        with st.chat_message(role):
            st.markdown(message.content)

    # Input from user
    user_query = st.chat_input("Your message")

    if user_query:
        # Add user message to chat history
        st.session_state.chat_history.append(HumanMessage(content=user_query))

        with st.chat_message("Human"):
            st.markdown(user_query)

        with st.chat_message("AI"):
            with st.spinner("Thinking..."):
                # Use the router agent for all queries
                output = route_query(user_query)
                # If the output is a dict (stock agent), extract the output string
                if isinstance(output, dict) and "output" in output:
                    output = output["output"]

                # Add AI response to chat history
                st.session_state.chat_history.append(AIMessage(content=output))

                # Simulate streaming response
                output_placeholder = st.empty()
                full_response = ""
                for char in output:
                    full_response += char
                    output_placeholder.markdown(full_response + "▌")  # Typing cursor
                    time.sleep(0.02)  # Typing speed

                output_placeholder.markdown(full_response)  # Final display

if __name__ == "__main__":
    main()