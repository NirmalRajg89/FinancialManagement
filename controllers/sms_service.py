import logging
import streamlit as st

from twilio.rest import Client
logger = logging.getLogger(__name__)


TWILIO_ACCOUNT_SID=st.secrets["TWILIO_ACCOUNT_SID"]
TWILIO_NUMBER="+18887718337"
TWILIO_AUTH_TOKEN=st.secrets["TWILIO_AUTH_TOKEN"]
TWILIO_TO_NUMBER="+14083894176"


def send_sms(self, message_body: str = "Test message") -> str:
    Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    message = self.client.messages.create(
        body= message_body,  # Message content
        from_=TWILIO_NUMBER,  # Your Twilio phone number (with country code)
        to=TWILIO_TO_NUMBER  # Recipient's phone number (with country code)
    )

    print(f"Message sent with SID: {message.sid}")


if __name__ == "__main__":
    send_sms()