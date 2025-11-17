# File: common/emailer.py
import random
import smtplib
from email.mime.text import MIMEText

ADMIN_EMAIL = "l230639@lhr.nu.edu.pk"  # replace with actual admin email
ADMIN_EMAIL = "l230639@lhr.nu.edu.pk"  # replace with actual admin email

def generate_code():
    """Generate a random 6-digit verification code."""
    return str(random.randint(100000, 999999))

def send_code(code):
    """Send verification code to admin email (mocked with print for testing)."""
    print(f"[DEBUG] Verification code sent to admin ({ADMIN_EMAIL}): {code}")

    # Uncomment below to send real email via SMTP
    sender_email = "mshaheerhussain902@gmail.com"
    sender_password = "ulnj cgaq jiaj cvvj"
    
    msg = MIMEText(f"New Receptionist Sign-Up verification code: {code}")
    msg['Subject'] = "Receptionist Sign-Up Code"
    msg['From'] = sender_email
    msg['To'] = ADMIN_EMAIL
    
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)

