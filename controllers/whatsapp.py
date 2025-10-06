import requests
import json
import streamlit as st

ACCESS_TOKEN = "EAAOZBoOcG5TwBPoDX8zwgznKHntbhPrYlmGfGaNnx4zOusZCmSyPlPcRtWSegqsf62i9Lseug8VdUYordUnoTmtf05WSQHRb7HLNtkb7OQRb8EPZB6ktQmPYcqAkPcP3lB3cQ62iC1iCzhuUUJsRNmC0O7Xax4TTB0HZAjkUWkGlp6TjxD2par5831SShLo2UGe4eLEJRzsSFE3WZBZCCd57ENWEVrtZCjDReizHvJy"#st.secrets('WHATSAPP_ACCESS_TOKEN')
PHONE_NUMBER_ID = "687966121069132"#st.secrets('WHATSAPP_PHONE_ID')
#VERIFY_TOKEN = st.secrets('WHATSAPP_VERIFY_TOKEN')

def send_whatsapp_template_message( summary: str = "Message test",recipient_number : str = "919840116889"):
    url = f"https://graph.facebook.com/v22.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Template data with placeholders replaced
    message_data = {
        "messaging_product": "whatsapp",
        "to": recipient_number,
        "category": "UTILITY",
        "recipient_type": "individual",
        "type": "template",
        "template": {
            "name": "reminder_template",  # Your template name
            "language": {
                "code": "en_US"
            },
            "components": [
                {
                    "type": "header",
                    "parameters": [
                        {
                            "type": "image",
                            "image": {
                                "link": "https://www.shutterstock.com/image-photo/summary-heading-background-template-business-600w-328018895.jpg"
                            }
                        }
                    ]
                },
                {
                    "type": "body",
                    "parameters": [
                        {
                            "type": "text",
                            "parameter_name": "summary",  # Passing the summary here
                            "text": summary
                        },
                        {
                            "type": "text",
                            "parameter_name": "name",
                            "text": "Jeyaseelan"
                        },
                        {
                            "type": "text",
                            "parameter_name": "doc_name",
                            "text": "Nirmal Raj"
                        },
                        {
                            "type": "text",
                            "parameter_name": "date",
                            "text": "1st Jan 2025"
                        },
                        {
                            "type": "text",
                            "parameter_name": "time",
                            "text": "5PM"
                        }
                    ]
                }
            ]
        }
    }

    try:
        response = requests.post(url, headers=headers, data=json.dumps(message_data))
        if response.status_code == 200:
            print("Message sent successfully!")
        else:
            print(f"Error sending message: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")


# Example Usage
if __name__ == "__main__":

    # Example data
    recipient_number = "+9190"  # Recipient's phone number
    summary = "Your document (Nirmal Raj) is scheduled for 1st Jan 2025 at 5 PM."

    send_whatsapp_template_message( recipient_number, summary)
