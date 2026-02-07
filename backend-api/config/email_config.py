# Environment-based email configuration for BandruPay
import os
from dotenv import load_dotenv

load_dotenv()

# Email settings from environment variables
SMTP_SERVER = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USERNAME", "firewing.test@gmail.com")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "lhpk tutj zpux pbnm")
FROM_EMAIL = os.getenv("FROM_EMAIL", "no-reply@bandarupay.com")

# Environment-aware signup link
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "production":
    SIGNUP_LINK_BASE = "https://customer.bandarupay.pro/signin"
    RESET_LINK_BASE = "https://superadmin.bandarupay.pro/reset-password"
    ADMIN_PANEL_BASE = "https://admin.bandarupay.pro"
else:
    SIGNUP_LINK_BASE = "http://localhost:5179/signin"
    RESET_LINK_BASE = "http://localhost:5173/reset-password"
    ADMIN_PANEL_BASE = "http://localhost:5174"
