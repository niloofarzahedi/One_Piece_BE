import os
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from dotenv import load_dotenv

load_dotenv()

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


async def send_otp_email(email: str, otp_code: str):
    message = MessageSchema(
        subject="Your Verification Code",
        recipients=[email],
        body=f"Your OTP verification code is: {otp_code}",
        subtype="plain"
    )
    mail = FastMail(conf)
    await mail.send_message(message)
