"""
email_utils.py
Email sending for OTP verification
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Email Configuration
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', 587))
SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'your_email@gmail.com')
SENDER_PASSWORD = os.environ.get('SENDER_PASSWORD', 'your_app_password')
SENDER_NAME = os.environ.get('SENDER_NAME', 'JobHub')


def send_otp_email(to_email: str, user_name: str, otp: str) -> bool:
    """
    Send OTP verification email.
    
    Args:
        to_email: Recipient email
        user_name: User's name
        otp: OTP code
    
    Returns:
        True if email sent successfully, False otherwise
    """
    try:
        # Check if email is configured
        if not SENDER_EMAIL or SENDER_EMAIL == 'your_email@gmail.com':
            print("[EMAIL] Email not configured. OTP:", otp)
            return False
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Your JobHub Verification Code'
        msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg['To'] = to_email
        
        # Plain text version
        text = f"""\
Hi {user_name},

Your JobHub 2FA verification code is:

{otp}

This code expires in 5 minutes.

If you didn't request this code, please ignore this email.

Best regards,
JobHub Team
"""
        
        # HTML version
        html = f"""\
<html>
  <body style="font-family: Arial, sans-serif; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
      <h2 style="color: #007bff;">JobHub 2FA Verification</h2>
      
      <p>Hi {user_name},</p>
      
      <p>Your JobHub 2FA verification code is:</p>
      
      <div style="background-color: #f5f5f5; padding: 20px; text-align: center; border-radius: 5px; margin: 20px 0;">
        <h1 style="color: #007bff; letter-spacing: 5px; margin: 0;">{otp}</h1>
      </div>
      
      <p style="color: #999; font-size: 14px;">This code expires in 5 minutes.</p>
      
      <p>If you didn't request this code, please ignore this email.</p>
      
      <p>Best regards,<br><strong>JobHub Team</strong></p>
    </div>
  </body>
</html>
"""
        
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print(f"[EMAIL] OTP email sent to {to_email}")
        return True
    
    except smtplib.SMTPAuthenticationError:
        print("[EMAIL] SMTP authentication failed. Check email credentials in .env")
        return False
    except smtplib.SMTPException as e:
        print(f"[EMAIL] SMTP error: {e}")
        return False
    except Exception as e:
        print(f"[EMAIL] Error sending email: {e}")
        return False


def send_2fa_enabled_email(to_email: str, user_name: str) -> bool:
    """Send email notification when 2FA is enabled."""
    try:
        if not SENDER_EMAIL or SENDER_EMAIL == 'your_email@gmail.com':
            return False
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'Two-Factor Authentication Enabled'
        msg['From'] = f"{SENDER_NAME} <{SENDER_EMAIL}>"
        msg['To'] = to_email
        
        text = f"""\
Hi {user_name},

Two-Factor Authentication (2FA) has been enabled on your JobHub account.

From now on, you'll need to enter a verification code when you log in.

If you didn't enable this, please contact us immediately.

Best regards,
JobHub Team
"""
        
        html = f"""\
<html>
  <body style="font-family: Arial, sans-serif; color: #333;">
    <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
      <h2 style="color: #007bff;">Security Alert</h2>
      <p>Hi {user_name},</p>
      <p><strong>Two-Factor Authentication (2FA)</strong> has been enabled on your JobHub account.</p>
      <p>From now on, you'll need to enter a verification code when you log in.</p>
      <p style="color: #d9534f;">If you didn't enable this, please contact us immediately.</p>
      <p>Best regards,<br><strong>JobHub Team</strong></p>
    </div>
  </body>
</html>
"""
        
        part1 = MIMEText(text, 'plain')
        part2 = MIMEText(html, 'html')
        msg.attach(part1)
        msg.attach(part2)
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        return True
    except Exception as e:
        print(f"[EMAIL] Error sending 2FA notification: {e}")
        return False
