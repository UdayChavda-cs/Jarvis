import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from langchain.tools import tool

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@tool
async def send_email(recipient: str, subject: str, body: str) -> str:
    """
    Sends an email to a specified recipient.

    Use this tool when the user wants to send an email. The agent should ask for the recipient's email address, the subject, and the body of the email if they are not provided.
    Example prompts:
    - "Send an email to example@example.com"
    - "Email my boss about the project update"
    """
    # Fetch email credentials from environment variables
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))

    if not all([sender_email, sender_password]):
        return "❌ Email credentials (EMAIL_SENDER, EMAIL_PASSWORD) are not set in the environment variables."

    try:
        # Create the email message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = recipient
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Connect to the SMTP server and send the email
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Secure the connection
        server.login(sender_email, sender_password)
        text = message.as_string()
        server.sendmail(sender_email, recipient, text)
        server.quit()
        
        logger.info(f"✅ Email sent successfully to {recipient}")
        return f"✅ Email sent successfully to {recipient}."
    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        return f"❌ Failed to send email: {e}"