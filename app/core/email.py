from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
import os
from dotenv import load_dotenv

load_dotenv()

# Configure email settings
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=587,
    MAIL_SERVER="smtp.gmail.com",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True
)


async def send_otp_email(recipient: str, otp_code: str):
    print("hello from send_otp_mail")
    message = MessageSchema(
        subject="Your OTP Code",
        recipients=[recipient],
        body=f"Your OTP code is: {otp_code}",
        subtype="plain"
    )
    mail = FastMail(conf)
    print(mail)
    await mail.send_message(message)

# Example usage:
# import asyncio
# asyncio.run(send_example_email("recipient@example.com"))
