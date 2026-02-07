from dotenv import load_dotenv
import os
import smtplib
from email.mime.text import MIMEText

load_dotenv()

sender = os.getenv("EMAIL_USER")
password = os.getenv("EMAIL_PASS")
receiver = os.getenv("EMAIL_RECEIVER")
host = os.getenv("EMAIL_HOST", "smtp.gmail.com")
port = int(os.getenv("EMAIL_PORT", 465))

msg = MIMEText("This is a test email from FastAPI backend.")
msg["Subject"] = "Test Email"
msg["From"] = sender
msg["To"] = receiver

if port == 465:
    # SSL
    with smtplib.SMTP_SSL(host, port) as server:
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())
else:
    # TLS
    with smtplib.SMTP(host, port) as server:
        server.starttls()
        server.login(sender, password)
        server.sendmail(sender, receiver, msg.as_string())

print("✅ Test email sent. Check inbox/spam.")