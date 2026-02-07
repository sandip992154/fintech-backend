import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from config.config import settings

logger = logging.getLogger(__name__)

def send_otp_email(
    to_email: str,
    otp: str,
    purpose: str = "verification",
    user_data: Dict[str, Any] = None
) -> Optional[str]:
    """
    Send OTP email to user
    
    Args:
        to_email: Email address to send OTP to
        otp: The OTP code
        purpose: Purpose of the OTP (verification, reset, mpin setup etc)
        user_data: Additional user data to include in email
        
    Returns:
        None if successful, error message if failed
    """
    try:
        subject = f"BandruPay - Your OTP for {purpose.title()}"
        
        # Basic email body
        body = f"""
        Hello,

        Your One-Time Password (OTP) for {purpose} is: {otp}
        
        This OTP is valid for {settings.OTP_EXPIRY_MINUTES} minutes.
        
        Please do not share this OTP with anyone.
        """
        
        # Add user details if provided
        if user_data:
            body += "\nUser Details:"
            for key, value in user_data.items():
                body += f"\n{key.title()}: {value}"
        
        body += "\n\nRegards,\nBandruPay Team"
        
        msg = MIMEMultipart()
        msg['From'] = settings.EMAIL_SENDER
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        # Get SMTP settings from config
        smtp_server = settings.SMTP_SERVER
        smtp_port = settings.SMTP_PORT
        smtp_user = settings.SMTP_USER
        smtp_password = settings.SMTP_PASSWORD
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, msg.as_string())
            
        logger.info(f"OTP email sent successfully to {to_email}")
        return None
        
    except Exception as e:
        error_msg = f"Failed to send OTP email: {str(e)}"
        logger.error(error_msg)
        return error_msg

def send_account_email(
    smtp_server: str,
    smtp_port: int,
    smtp_user: str,
    smtp_password: str,
    to_email: str,
    user_id: str,
    password: str,
    signup_link: str,
    role: str
) -> Optional[str]:
    subject = f"Welcome to BandruPay - Your {role.title()} Account Details"
    body = f"""
    Hello {user_id},

    Your {role.title()} account has been created successfully.

    Login ID: {user_id}
    Password: {password}
    Signup/Activation Link: {signup_link}

    Please change your password after first login.

    Regards,\nBandruPay Team
    """
    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.sendmail(smtp_user, to_email, msg.as_string())
        return None
    except Exception as e:
        return str(e)
