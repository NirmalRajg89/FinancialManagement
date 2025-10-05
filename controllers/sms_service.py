import logging
import streamlit as st
import re
from twilio.rest import Client

logger = logging.getLogger(__name__)

TWILIO_ACCOUNT_SID = st.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_NUMBER = "+18887718337"
TWILIO_AUTH_TOKEN = st.secrets["TWILIO_AUTH_TOKEN"]
TWILIO_TO_NUMBER = "+14083894176"


def strip_markdown(text: str) -> str:
    # Remove common Markdown formatting
    text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)  # bold
    text = re.sub(r'\*(.*?)\*', r'\1', text)  # italic
    text = re.sub(r'`(.*?)`', r'\1', text)  # inline code
    text = re.sub(r'^#+\s*', '', text, flags=re.MULTILINE)  # headers
    text = re.sub(r'\|.*?\|', '', text)  # table rows
    text = re.sub(r'-{2,}', '', text)  # horizontal rules
    text = re.sub(r'\n{2,}', '\n', text)  # extra newlines
    return text.strip()


def send_sms(message_body: str = "Test message" ,number : str = TWILIO_TO_NUMBER ) -> str:
    # Internal helper to strip markdown

    # Strip formatting
    clean_message = strip_markdown(message_body)
    clean_message = clean_message[:500]

    # Twilio credentials
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    try:
        message = client.messages.create(
            body=clean_message,
            from_=TWILIO_NUMBER,
            to=number
        )
        print(f"Message sent with SID: {message.sid}")
        return f"Message sent successfully. SID: {message.sid}"
    except Exception as e:
        print(f"Error sending SMS: {str(e)}")
        return f"Failed to send message: {str(e)}"



if __name__ == "__main__":
    send_sms()