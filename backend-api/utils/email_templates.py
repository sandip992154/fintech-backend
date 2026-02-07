async def send_reset_password_email(to_email: str, username: str, reset_link: str):
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
    
    # Send email using your existing email utility
    await send_email(
        to_email=to_email,
        subject=subject,
        html_content=html_content
    )