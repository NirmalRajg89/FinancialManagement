import boto3

client = boto3.client('ses', region_name="us-east-2")
SENDER_EMAIL = "support@prajna.ai"


def send_email(message: str, email: str):
    email_list = ["nirmal.raj@prajna.ai", email]
    try:

        # Send the email to multiple recipients
        response_email = client.send_email(
            Source=SENDER_EMAIL,
            Destination={
                'ToAddresses': email_list,
                'CcAddresses': ["nganesan7468@altimetrik.com"]
            },
            Message={
                'Subject': {
                    'Data': "Rate - Financial Investment Summary Report"
                },
                'Body': {
                    'Text': {
                        'Data': message
                    }
                }
            }
        )

        # Log the message ID for reference
        print("Email sent! Message ID:", response_email['MessageId'])
    except Exception as e:
        print("Error while Sending mail: ", e)
        return "Failed"
