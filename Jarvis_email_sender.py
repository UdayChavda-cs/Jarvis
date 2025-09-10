import os
import smtplib
import logging
import json
import re # Import the regular expression library
import ast # Import the Abstract Syntax Tree library
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from langchain.tools import tool
from pydantic import BaseModel, Field, field_validator
from typing import Union, List

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Define a very flexible Pydantic model for the tool's arguments ---
class SendEmailInput(BaseModel):
    recipients: Union[str, List[str]] = Field(description="The email address or list of addresses.", alias='to')
    subject: str = Field(description="The subject line of the email.")
    message: str = Field(description="The main content/message of the email.", alias='body')

    @field_validator('recipients', 'subject', 'message', pre=True, always=True)
    def anystr_to_str(cls, v):
        if v is None:
            return "" # Return empty string if argument is missing
        return v
        
# --- Update the tool to be extremely robust ---
@tool
async def send_email(data: Union[str, dict, SendEmailInput]) -> str:
    """Sends an email to one or more recipients."""
    
    try:
        dict_data = {}
        if isinstance(data, str):
            # ast.literal_eval is safer than json.loads for Python-style dict strings
            dict_data = ast.literal_eval(data)
        elif isinstance(data, dict):
            dict_data = data
        else:
            dict_data = data.model_dump()

        # Pydantic's model_validate will handle the aliases ('to' -> 'recipients', 'body' -> 'message')
        email_data = SendEmailInput.model_validate(dict_data)

    except Exception as e:
        return f"Error: I'm missing some information. Please provide a clear recipient, subject, and body. Details: {e}"

    # Extract the details from the validated data
    raw_recipients = email_data.recipients
    subject = email_data.subject
    body = email_data.message

    # --- FIX: Clean the extracted email addresses ---
    if not isinstance(raw_recipients, list):
        raw_recipients = [raw_recipients]

    cleaned_recipients = []
    # This regex finds email addresses, even if they have names attached
    email_regex = r'[\w\.\-\+]+@[\w\.\-]+'
    for r in raw_recipients:
        found_emails = re.findall(email_regex, str(r))
        if found_emails:
            cleaned_recipients.extend(found_emails)

    if not cleaned_recipients:
        return "❌ I couldn't find any valid email addresses in your request."


    # Fetch email credentials from environment variables
    sender_email = os.getenv("EMAIL_SENDER")
    sender_password = os.getenv("EMAIL_PASSWORD")
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))

    if not all([sender_email, sender_password]):
        return "❌ Email credentials are not set in the environment variables."

    try:
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = ", ".join(cleaned_recipients)
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        text = message.as_string()
        # Use the cleaned list of recipients for sending
        server.sendmail(sender_email, cleaned_recipients, text)
        server.quit()
        
        logger.info(f"✅ Email sent successfully to {cleaned_recipients}")
        return f"✅ Email sent successfully to {', '.join(cleaned_recipients)}."
    except Exception as e:
        logger.error(f"❌ Failed to send email: {e}")
        return f"❌ Failed to send email: {e}"