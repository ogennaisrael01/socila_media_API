from email.message import EmailMessage
import os
from dotenv import load_dotenv
import aiosmtplib
import logging
load_dotenv()

logging.basicConfig(level=logging.INFO)

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_USER = os.getenv("EMAIL_USER")


async def send_email(subjet: str, email:str, body:str):
    message = EmailMessage()
    message["From"] = EMAIL_USER
    message["To"] = email
    message["Subject"] = subjet
    message.set_content(body)
    try: 
        await aiosmtplib.send(
            message,
            hostname=EMAIL_HOST,
            password=EMAIL_PASS,
            port=EMAIL_PORT,
            username=EMAIL_USER,
            start_tls=True
        )

    except aiosmtplib.SMTPException as e:
        logging.error(f"An error occured while connecting to aiosmtplib {e}")
    except Exception as e:
        logging.error(f"An error occured while sending email {e}")

    finally:
        logging.info("Email sent successfully, check your email address")


async def verification_email(url: str, email: str):
    subject = "Account verification"
    body = f"""Click the link to verify your account: {url} \n\n \
    Link expires in 30 munites
    """
    try:
        await send_email(subject, email, body)
    except Exception as e:
        logging.error(f"Error: {e}")
    finally:
        return True

async def send_updated_verification(email: str):
    subject = "Email verification successful"
    body =f"""
            Email verification is successfull, you may now proceed to login/signup
""" 
    try:
        await send_email(subject, email, body)
    except Exception as e:
        logging.error(f"error: {e}")
    finally:
        return True
    
async def password_reset_email(email: str, reset_url: str):
    subject = "password reset"
    body = f"""
        Click the link to reset your password. {reset_url} \n\n\
            This link expires in less than 30 minutes"""
    try:
        await send_email(subject=subject, email=email, body=body)
    except Exception as e:
        logging.error(f"an error occured {ee}")
    finally:
        return True
    
