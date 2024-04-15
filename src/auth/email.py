from sqlalchemy import select
from pathlib import Path

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from auth.service import auth_service

conf = ConnectionConfig(
    MAIL_USERNAME="fastapi_project@meta.ua",
    MAIL_PASSWORD="Pythoncourse2024",
    MAIL_FROM="fastapi_project@meta.ua",
    MAIL_PORT="465",
    MAIL_SERVER="smtp.meta.ua",
    MAIL_FROM_NAME="ContactManager",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)


async def send_email(email: str, username: str, host: str):
    """
    Sends an email to confirm the email address.

    :param email: The email address to which the email will be sent.
    :param username: The username to be displayed in the email.
    :param host: The host on which the program is running.
    """
    try:
        token_verification = auth_service.create_email_token(data={"sub": email})
        message = MessageSchema(
            subject="Confirm your email ",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as err:
        print(err)

async def send_email_reset(email: str, username: str, host: str):
    """
    Sends an email to reset the password.

    :param email: The email address to which the email will be sent.
    :param username: The username to be displayed in the email.
    :param host: The host on which the program is running.
    """
    try:
        token_verification = auth_service.create_email_token(data={"sub": email})
        message = MessageSchema(
            subject="Confirm your email ",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="reset_password.html")
    except ConnectionErrors as err:
        print(err)