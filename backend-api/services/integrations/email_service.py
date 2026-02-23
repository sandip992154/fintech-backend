from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import smtplib
from typing import Optional, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_name = os.getenv("FROM_NAME", "BandruPay")
        self.sender_email = os.getenv("FROM_EMAIL", self.smtp_username)
        # Formatted sender: "BandruPay <email@example.com>"
        self.sender_formatted = formataddr((self.from_name, self.sender_email))
        self.signup_link_base = "https://customer.bandarupay.pro/signin"
        self.is_configured = all([
            self.smtp_host,
            self.smtp_port,
            self.smtp_username,
            self.smtp_password,
            self.sender_email
        ])

        if not self.is_configured:
            logger.error(
                "Email service not properly configured. "
                "Set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, FROM_EMAIL in environment variables."
            )
        else:
            logger.info(f"Email service configured — sending as: {self.sender_formatted}")

    def send_email(
        self,
        to_email: str,
        subject: str,
        content: str,
        cc: Optional[list] = None,
        bcc: Optional[list] = None
    ) -> bool:
        """
        Send an HTML email via SMTP.

        Args:
            to_email: Recipient email address
            subject: Email subject
            content: Email body (HTML)
            cc: Optional list of CC recipients
            bcc: Optional list of BCC recipients

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_configured:
            logger.error(
                "Email send aborted — SMTP is not configured. "
                "Set SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, "
                "FROM_EMAIL in environment variables."
            )
            return False

        try:
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = self.sender_formatted
            message['To'] = to_email

            if cc:
                message['Cc'] = ', '.join(cc)
            if bcc:
                message['Bcc'] = ', '.join(bcc)

            message.attach(MIMEText(content, 'html'))

            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)

                recipients = [to_email]
                if cc:
                    recipients.extend(cc)
                if bcc:
                    recipients.extend(bcc)

                server.sendmail(self.sender_email, recipients, message.as_string())

            logger.info(f"Email sent successfully to {to_email} | Subject: {subject}")
            return True

        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
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