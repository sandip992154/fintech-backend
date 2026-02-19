from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import smtplib
from typing import Optional, Dict, Any
import logging
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, select_autoescape

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.sender_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.signup_link_base = "https://customer.bandarupay.pro/signin"
        self.is_configured = all([
            self.smtp_host,
            self.smtp_port,
            self.smtp_username,
            self.smtp_password,
            self.sender_email
        ])
        
        # Log configuration status
        if not self.is_configured:
            logger.error("Email service not properly configured. Missing SMTP credentials in environment variables.")
        else:
            logger.info(f"Email service configured for {self.sender_email}")
        
        # Set up template environment (optional)
        try:
            template_dir = Path(__file__).parent.parent / "templates" / "email"
            if template_dir.exists():
                self.template_env = Environment(
                    loader=FileSystemLoader(str(template_dir)),
                    autoescape=select_autoescape(['html', 'xml'])
                )
            else:
                self.template_env = None
        except Exception as e:
            logger.warning(f"Template environment setup failed: {e}")
            self.template_env = None

    def send_email(
        self,
        to_email: str,
        subject: str,
        content: str,
        cc: Optional[list] = None,
        bcc: Optional[list] = None
    ) -> bool:
        """
        Send an email
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            content: Email content (HTML)
            cc: List of CC recipients
            bcc: List of BCC recipients
            
        Returns:
            bool: True if email was sent successfully, False otherwise
        """
        if not self.is_configured:
            logger.error(
                "Email send aborted — SMTP is not configured. "
                "Set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, "
                "FROM_EMAIL in environment variables."
            )
            return False

        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.sender_email
            message['To'] = to_email
            
            if cc:
                message['Cc'] = ', '.join(cc)
            if bcc:
                message['Bcc'] = ', '.join(bcc)

            # Attach HTML content
            html_part = MIMEText(content, 'html')
            message.attach(html_part)

            # Create SMTP connection
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                
                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)
                
                server.sendmail(
                    self.sender_email,
                    recipients,
                    message.as_string()
                )

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.sender_email
            message['To'] = to_email
            
            if cc:
                message['Cc'] = ', '.join(cc)
            if bcc:
                message['Bcc'] = ', '.join(bcc)

            # Attach HTML content
            html_part = MIMEText(html_content, 'html')
            message.attach(html_part)

            # Create SMTP connection
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                
                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)
                
                server.sendmail(
                    self.sender_email,
                    recipients,
                    message.as_string()
                )

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email: {str(e)}")
            return False

    def send_otp_email(self, to_email: str, otp: str, user_name: str) -> bool:
        """Send OTP email to user"""
        content = f"""
        <p>Dear {user_name},</p>
        <p>Your One-Time Password (OTP) for BandaruPay authentication is: <strong>{otp}</strong></p>
        <p>This OTP is valid for 10 minutes.</p>
        <p>If you didn't request this OTP, please ignore this email.</p>
        """
        return self.send_email(
            to_email=to_email,
            subject="Your BandaruPay OTP",
            content=content
        )

    def send_welcome_email(self, to_email: str, user_data: Dict[str, Any]) -> bool:
        """Send welcome email to new user"""
        content = f"""
        <p>Dear {user_data.get('full_name')},</p>
        <p>Welcome to BandaruPay! Your account has been created successfully.</p>
        <p>User ID: {user_data.get('username')}</p>
        <p>Please click <a href="{self.signup_link_base}">here</a> to login.</p>
        """
        return self.send_email(
            to_email=to_email,
            subject="Welcome to BandaruPay",
            content=content
        )

    def send_password_reset_email(self, to_email: str, reset_token: str, user_name: str) -> bool:
        """Send password reset email"""
        reset_link = f"{self.signup_link_base}/reset-password?token={reset_token}"
        content = f"""
        <p>Dear {user_name},</p>
        <p>Click <a href="{reset_link}">here</a> to reset your password.</p>
        <p>This link is valid for 24 hours.</p>
        <p>If you didn't request this, please ignore this email.</p>
        """
        return self.send_email(
            to_email=to_email,
            subject="Reset Your BandaruPay Password",
            content=content
        )

    def send_kyc_verification_email(self, to_email: str, verification_token: str, user_data: Dict[str, Any]) -> bool:
        """Send KYC verification email"""
        verification_link = f"{self.signup_link_base}/verify-kyc?token={verification_token}"
        content = f"""
        <p>Dear {user_data.get('full_name')},</p>
        <p>Please complete your KYC verification by clicking <a href="{verification_link}">here</a>.</p>
        <p>User ID: {user_data.get('username')}</p>
        <p>This link is valid for 7 days.</p>
        """
        return self.send_email(
            to_email=to_email,
            subject="Complete Your BandaruPay KYC Verification",
            content=content
        )