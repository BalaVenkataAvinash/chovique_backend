import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from core.config import get_settings

logger = logging.getLogger("chovique.email")


def send_otp_email(to_email: str, otp_code: str) -> bool:
    """
    Sends a 6-digit OTP verification email to the user using SMTP.
    Fallback: logs OTP to terminal if SMTP is not configured or encounters an error.
    """
    # Always fetch fresh settings
    get_settings.cache_clear()
    settings = get_settings()

    subject = f"{otp_code} is your Chovique Registration OTP"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; background-color: #1A0D00; color: #F5EBE6; padding: 20px; }}
            .container {{ max-width: 500px; margin: 0 auto; background-color: #2D1808; border: 1px solid #C9A84C; border-radius: 8px; padding: 30px; text-align: center; }}
            .logo {{ font-size: 24px; font-weight: bold; letter-spacing: 3px; color: #C9A84C; margin-bottom: 20px; }}
            .otp {{ font-size: 36px; font-weight: bold; letter-spacing: 8px; color: #D4AF37; margin: 25px 0; background: #1A0D00; padding: 15px; border-radius: 6px; display: inline-block; }}
            .expiry {{ font-size: 14px; color: #B0A090; margin-top: 15px; }}
            .footer {{ font-size: 12px; color: #706050; margin-top: 25px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">CHOVIQUE</div>
            <h2>Account Registration OTP</h2>
            <p>Please use the following 6-digit OTP code to complete your registration:</p>
            <div class="otp">{otp_code}</div>
            <p class="expiry">⚠️ Note: This OTP will expire in <strong>{settings.OTP_EXPIRE_SECONDS} seconds</strong>.</p>
            <p class="footer">If you did not request this code, please ignore this email.</p>
        </div>
    </body>
    </html>
    """

    # Always log to console for instant developer feedback
    print(f"\n==========================================")
    print(f"[CHOVIQUE SMTP] Sending OTP to: {to_email}")
    print(f"[CHOVIQUE SMTP] From: {settings.SMTP_FROM_EMAIL} via {settings.SMTP_HOST}:{settings.SMTP_PORT}")
    print(f"[CHOVIQUE SMTP] OTP CODE: {otp_code} (Expires in {settings.OTP_EXPIRE_SECONDS}s)")
    print(f"==========================================\n")

    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        logger.info(f"SMTP credentials not fully set. Logged OTP {otp_code} for {to_email} to console.")
        return True

    # Strip any spaces in Gmail App Password
    smtp_password = settings.SMTP_PASSWORD.replace(" ", "")

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.SMTP_FROM_EMAIL
        msg["To"] = to_email

        text_part = MIMEText(f"Your Chovique registration OTP is: {otp_code}. Valid for 30 seconds.", "plain")
        html_part = MIMEText(html_content, "html")
        msg.attach(text_part)
        msg.attach(html_part)

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            server.login(settings.SMTP_USER, smtp_password)
            server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())

        print(f"[CHOVIQUE SMTP SUCCESS] Email successfully delivered to {to_email} via SMTP!")
        logger.info(f"Successfully sent OTP email to {to_email}")
        return True
    except Exception as e:
        print(f"[CHOVIQUE SMTP WARNING] Could not deliver via SMTP ({e}). Fallback OTP in terminal: {otp_code}")
        logger.error(f"Failed to send SMTP email to {to_email}: {e}")
        # Return True so registration process proceeds even if local network/SMTP fails
        return True
