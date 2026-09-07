import smtplib
from email.message import EmailMessage

async def sendEmail(e_from:str, e_to:str, e_subject:str, e_body:str):
    msg = EmailMessage()
    msg["Subject"] = e_subject
    msg["From"] = e_from
    msg["To"] = e_to
    msg.set_content(e_body)

    # Connect to local testing server running on port 1025
    with smtplib.SMTP("localhost", 1025) as server:
        server.send_message(msg)

    print("Email sent successfully!")

