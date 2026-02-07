import aiosmtplib
from email.mime.text import MIMEText
import os
from config import email_config

EMAIL_SENDER = email_config.SMTP_USER
EMAIL_PASSWORD = email_config.SMTP_PASSWORD
SMTP_SERVER = email_config.SMTP_SERVER
SMTP_PORT = email_config.SMTP_PORT

async def send_reset_password_email(*, to_email: str, username: str, reset_link: str):
    """
    Send password reset email to user
    """
    subject = "Password Reset Request - BandaruPay"
    
    html_content = f"""
    <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #1a73e8;">Password Reset Request</h2>
                
                <p>Dear {username},</p>
                
                <p>We received a request to reset your password for your BandaruPay account. 
                If you didn't make this request, please ignore this email.</p>
                
                <p>To reset your password, click the link below:</p>
                
                <p style="margin: 30px 0;">
                    <a href="{reset_link}" 
                       style="background-color: #1a73e8; 
                              color: white; 
                              padding: 12px 24px; 
                              text-decoration: none; 
                              border-radius: 4px;">
                        Reset Password
                    </a>
                </p>
                
                <p>This link will expire in 24 hours for security reasons.</p>
                
                <p>If you're having trouble clicking the button, copy and paste this URL into your browser:</p>
                <p style="word-break: break-all; color: #666;">{reset_link}</p>
                
                <p style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                    Best regards,<br>
                    The BandaruPay Team
                </p>
                
                <p style="font-size: 12px; color: #666; margin-top: 30px;">
                    If you didn't request this password reset, please ignore this email or contact support 
                    if you have concerns about your account security.
                </p>
            </div>
        </body>
    </html>
    """
    
    msg = MIMEText(html_content, 'html')
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email
    msg["Subject"] = subject

    try:
        await aiosmtplib.send(
            msg,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            start_tls=True,
            username=EMAIL_SENDER,
            password=EMAIL_PASSWORD,
        )
        print(f"✅ Password reset email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send password reset email to {to_email}: {e}")
        raise

async def send_login_email(*, to_email: str, name: str, login_id: str, password: str, signup_link: str, role: str, otp: str = None, user_code: str = None, dashboard_url: str = None):
    if otp:
        subject = f"Your {role.title()} Portal OTP for Login"
        body = (
            f"Hello {name},\n\n"
            f"Your OTP for login is: {otp}\n\n"
            f"Login ID: {login_id}\n"
            f"Role: {role.title()}\n"
            f"If you did not request this OTP, please ignore this email.\n\n"
            "Best regards,\nBandruPay Team"
        )
    else:
        subject = f"Welcome to BandruPay! Your {role.title()} Account Details"
        body = (
            f"Hello {name},\n\n"
            f"Your {role.title()} account has been created successfully.\n\n"
            f"User Code: {user_code if user_code else '[N/A]'}\n"
            f"Login ID: {login_id}\n"
            f"Password: {password if password else '[Set during registration]'}\n"
            f"Dashboard URL: {dashboard_url if dashboard_url else signup_link if signup_link else '[N/A]'}\n\n"
            "Please change your password after logging in for the first time.\n\n"
            "Best regards,\nBandruPay Team"
        )
    msg = MIMEText(body)
    msg["From"] = EMAIL_SENDER
    msg["To"] = to_email
    msg["Subject"] = subject

    try:
        await aiosmtplib.send(
            msg,
            hostname=SMTP_SERVER,
            port=SMTP_PORT,
            start_tls=True,
            username=EMAIL_SENDER,
            password=EMAIL_PASSWORD,
        )
        print(f"✅ Email sent to {to_email}")
    except Exception as e:
        print(f"❌ Failed to send email to {to_email}: {e}")
