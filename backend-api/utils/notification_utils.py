"""
Email notification utilities for sending OTP and system notifications
"""
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

def send_otp_email(email: str, otp: str, name: str) -> bool:
    """Send OTP via email"""
    try:
        # Email configuration from environment variables
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        from_email = os.getenv("FROM_EMAIL", smtp_username)
        
        if not smtp_username or not smtp_password:
            print("Email credentials not configured")
            return False
        
        # Create message
        message = MIMEMultipart()
        message["From"] = from_email
        message["To"] = email
        message["Subject"] = "Your MPIN Reset OTP - Bandaru Pay"
        
        # Email body
        body = f"""
        Dear {name},
        
        Your OTP for MPIN reset is: {otp}
        
        This OTP is valid for 10 minutes only. Please do not share this OTP with anyone.
        
        If you did not request this OTP, please ignore this email.
        
        Best regards,
        Bandaru Pay Team
        """
        
        message.attach(MIMEText(body, "plain"))
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
        
        return True
    
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def send_kyc_notification_email(email: str, name: str, status: str, reason: Optional[str] = None) -> bool:
    """Send KYC status notification via email"""
    try:
        # Email configuration from environment variables
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        from_email = os.getenv("FROM_EMAIL", smtp_username)
        
        if not smtp_username or not smtp_password:
            print("Email credentials not configured")
            return False
        
        # Create message
        message = MIMEMultipart()
        message["From"] = from_email
        message["To"] = email
        message["Subject"] = f"KYC Status Update - Bandaru Pay"
        
        # Email body based on status
        if status == "approved":
            body = f"""
            Dear {name},
            
            Congratulations! Your KYC verification has been approved.
            
            You can now access all services on the Bandaru Pay platform.
            
            Best regards,
            Bandaru Pay Team
            """
        else:  # rejected
            body = f"""
            Dear {name},
            
            We regret to inform you that your KYC verification has been rejected.
            
            Reason: {reason or "Please check your documents and resubmit"}
            
            You can update your KYC documents and resubmit for verification.
            
            Best regards,
            Bandaru Pay Team
            """
        
        message.attach(MIMEText(body, "plain"))
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
        
        return True
    
    except Exception as e:
        print(f"Failed to send KYC notification email: {str(e)}")
        return False

def send_welcome_email(email: str, name: str, user_code: str, temp_password: str) -> bool:
    """Send welcome email to new member"""
    try:
        # Email configuration from environment variables
        smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_username = os.getenv("SMTP_USERNAME")
        smtp_password = os.getenv("SMTP_PASSWORD")
        from_email = os.getenv("FROM_EMAIL", smtp_username)
        
        if not smtp_username or not smtp_password:
            print("Email credentials not configured")
            return False
        
        # Create message
        message = MIMEMultipart()
        message["From"] = from_email
        message["To"] = email
        message["Subject"] = "Welcome to Bandaru Pay - Account Created"
        
        # Email body
        body = f"""
        Dear {name},
        
        Welcome to Bandaru Pay! Your account has been created successfully.
        
        Your login credentials:
        User Code: {user_code}
        Username: {email}
        Temporary Password: {temp_password}
        
        Please login and:
        1. Setup your MPIN
        2. Complete your KYC verification
        3. Update your profile
        
        For security reasons, please change your password after first login.
        
        Best regards,
        Bandaru Pay Team
        """
        
        message.attach(MIMEText(body, "plain"))
        
        # Send email
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.send_message(message)
        
        return True
    
    except Exception as e:
        print(f"Failed to send welcome email: {str(e)}")
        return False