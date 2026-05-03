"""
Phase 18: Auth Hardening — Email Service
Enterprise-grade SMTP email delivery for:
  1. Email verification on registration
  2. Password reset flow
  3. Security alert notifications (future)

Security design:
- Tokens are HMAC-SHA256 signed with the app SECRET_KEY
- Tokens carry an expiry timestamp and purpose claim to prevent cross-use
- HTML templates are inline (no external dependencies)
- SMTP credentials are loaded from environment only
"""

import os
import hmac
import hashlib
import json
import time
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

logger = logging.getLogger(__name__)

# ── SMTP Configuration ──
SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "")
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "BharatDoc")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

# Token configuration
SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey12345")
VERIFICATION_TOKEN_EXPIRY = 24 * 60 * 60  # 24 hours
RESET_TOKEN_EXPIRY = 15 * 60  # 15 minutes (strict — Google/GitHub standard)

# Frontend URL for links in emails
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")


def _generate_token(payload: dict) -> str:
    """
    Generate an HMAC-SHA256 signed token.
    The token is a base64-safe JSON payload + signature.
    This avoids storing tokens in the database — stateless verification.
    """
    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
    signature = hmac.new(
        SECRET_KEY.encode("utf-8"),
        payload_json.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    # Combine payload and signature with a delimiter
    import base64
    token_data = base64.urlsafe_b64encode(payload_json.encode("utf-8")).decode("utf-8")
    return f"{token_data}.{signature}"


def _verify_token(token: str, purpose: str) -> Optional[dict]:
    """
    Verify an HMAC-SHA256 signed token.
    Returns the payload dict if valid, None if tampered/expired/wrong purpose.
    """
    import base64
    try:
        parts = token.split(".", 1)
        if len(parts) != 2:
            return None

        token_data, provided_signature = parts
        payload_json = base64.urlsafe_b64decode(token_data.encode("utf-8")).decode("utf-8")

        # Verify HMAC signature
        expected_signature = hmac.new(
            SECRET_KEY.encode("utf-8"),
            payload_json.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

        if not hmac.compare_digest(provided_signature, expected_signature):
            logger.warning("Token signature mismatch — possible tampering")
            return None

        payload = json.loads(payload_json)

        # Verify purpose claim
        if payload.get("purpose") != purpose:
            logger.warning(f"Token purpose mismatch: expected={purpose}, got={payload.get('purpose')}")
            return None

        # Verify expiry
        if time.time() > payload.get("exp", 0):
            logger.info("Token has expired")
            return None

        return payload

    except Exception as e:
        logger.error(f"Token verification failed: {e}")
        return None


def generate_verification_token(email: str) -> str:
    """Generate a verification token for email confirmation."""
    return _generate_token({
        "email": email,
        "purpose": "email_verification",
        "exp": time.time() + VERIFICATION_TOKEN_EXPIRY,
        "iat": time.time(),
    })


def verify_verification_token(token: str) -> Optional[str]:
    """Verify an email verification token. Returns email if valid."""
    payload = _verify_token(token, "email_verification")
    return payload.get("email") if payload else None


def generate_reset_token(email: str) -> str:
    """Generate a password reset token (15-minute expiry)."""
    return _generate_token({
        "email": email,
        "purpose": "password_reset",
        "exp": time.time() + RESET_TOKEN_EXPIRY,
        "iat": time.time(),
    })


def verify_reset_token(token: str) -> Optional[str]:
    """Verify a password reset token. Returns email if valid."""
    payload = _verify_token(token, "password_reset")
    return payload.get("email") if payload else None


def _smtp_configured() -> bool:
    """Check if SMTP is properly configured."""
    return all([SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL])


def _send_email(to_email: str, subject: str, html_body: str) -> bool:
    """
    Send an email via SMTP.
    Returns True on success, False on failure (never raises).
    """
    if not _smtp_configured():
        logger.warning(
            "SMTP not configured — email not sent. "
            "Set SMTP_HOST, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_EMAIL in environment."
        )
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
        msg["To"] = to_email
        msg["Subject"] = subject
        # Security headers
        msg["X-Mailer"] = "BharatDoc-Secure"
        msg["X-Priority"] = "1"

        # Plain text fallback
        plain_text = f"Visit {FRONTEND_URL} to complete this action."
        msg.attach(MIMEText(plain_text, "plain"))
        msg.attach(MIMEText(html_body, "html"))

        if SMTP_USE_TLS:
            server = smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=10)
            server.ehlo()
            server.starttls()
            server.ehlo()
        else:
            server = smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, timeout=10)

        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_FROM_EMAIL, to_email, msg.as_string())
        server.quit()

        logger.info(f"Email sent successfully to {to_email}: {subject}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False


# ── Email Templates ──

def _base_template(title: str, content: str) -> str:
    """Wrap content in a professional HTML email template."""
    return f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"></head>
<body style="margin:0;padding:0;background-color:#f1f5f9;font-family:'Segoe UI',Tahoma,Geneva,Verdana,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#f1f5f9;padding:40px 0;">
<tr><td align="center">
<table width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
  <!-- Header -->
  <tr><td style="background:linear-gradient(135deg,#8b5cf6,#7c3aed);padding:32px 40px;text-align:center;">
    <h1 style="margin:0;color:#ffffff;font-size:24px;font-weight:700;letter-spacing:-0.5px;">🛡️ BharatDoc</h1>
    <p style="margin:4px 0 0;color:rgba(255,255,255,0.85);font-size:13px;">Intelligent Document Intelligence Platform</p>
  </td></tr>
  <!-- Content -->
  <tr><td style="padding:40px;">
    <h2 style="margin:0 0 16px;color:#1e293b;font-size:20px;font-weight:600;">{title}</h2>
    {content}
  </td></tr>
  <!-- Footer -->
  <tr><td style="padding:24px 40px;background-color:#f8fafc;border-top:1px solid #e2e8f0;text-align:center;">
    <p style="margin:0;color:#94a3b8;font-size:12px;">This is an automated message from BharatDoc. Do not reply to this email.</p>
    <p style="margin:4px 0 0;color:#94a3b8;font-size:11px;">© 2026 BharatDoc. All Rights Reserved.</p>
  </td></tr>
</table>
</td></tr></table>
</body></html>"""


def send_verification_email(to_email: str, token: str) -> bool:
    """Send the email verification email after registration."""
    verify_url = f"{FRONTEND_URL}/verify-email?token={token}"
    content = f"""
    <p style="color:#475569;font-size:15px;line-height:1.7;">
      Thank you for registering with BharatDoc. To activate your account and ensure the security
      of your data, please verify your email address by clicking the button below.
    </p>
    <div style="text-align:center;margin:32px 0;">
      <a href="{verify_url}" style="display:inline-block;padding:14px 36px;background:linear-gradient(135deg,#8b5cf6,#7c3aed);color:#ffffff;text-decoration:none;border-radius:12px;font-weight:600;font-size:15px;box-shadow:0 4px 12px rgba(139,92,246,0.35);">
        Verify My Email
      </a>
    </div>
    <p style="color:#64748b;font-size:13px;">
      This link expires in <strong>24 hours</strong>. If you did not create this account, you can safely ignore this email.
    </p>
    <div style="margin-top:24px;padding:16px;background-color:#fef3c7;border:1px solid #fbbf24;border-radius:8px;">
      <p style="margin:0;color:#92400e;font-size:12px;font-weight:600;">⚠️ Security Notice</p>
      <p style="margin:4px 0 0;color:#92400e;font-size:12px;">
        Never share this link with anyone. BharatDoc staff will never ask for your verification link or password.
      </p>
    </div>
    """
    return _send_email(to_email, "Verify Your BharatDoc Account", _base_template("Verify Your Email", content))


def send_password_reset_email(to_email: str, token: str) -> bool:
    """Send the password reset email."""
    reset_url = f"{FRONTEND_URL}/reset-password?token={token}"
    content = f"""
    <p style="color:#475569;font-size:15px;line-height:1.7;">
      We received a request to reset the password for your BharatDoc account. Click the button below
      to set a new password.
    </p>
    <div style="text-align:center;margin:32px 0;">
      <a href="{reset_url}" style="display:inline-block;padding:14px 36px;background:linear-gradient(135deg,#ef4444,#dc2626);color:#ffffff;text-decoration:none;border-radius:12px;font-weight:600;font-size:15px;box-shadow:0 4px 12px rgba(239,68,68,0.35);">
        Reset My Password
      </a>
    </div>
    <p style="color:#64748b;font-size:13px;">
      This link expires in <strong>15 minutes</strong> for your security. If you did not request this reset, your account is safe —
      no changes have been made. However, we recommend changing your password if you believe someone else may have access.
    </p>
    <div style="margin-top:24px;padding:16px;background-color:#fee2e2;border:1px solid #fca5a5;border-radius:8px;">
      <p style="margin:0;color:#991b1b;font-size:12px;font-weight:600;">🔐 Security Alert</p>
      <p style="margin:4px 0 0;color:#991b1b;font-size:12px;">
        If you did not request this password reset, someone may be trying to access your account.
        Consider changing your password immediately.
      </p>
    </div>
    """
    return _send_email(to_email, "Reset Your BharatDoc Password", _base_template("Password Reset Request", content))


def send_password_changed_notification(to_email: str) -> bool:
    """Notify user that their password was successfully changed."""
    content = """
    <p style="color:#475569;font-size:15px;line-height:1.7;">
      Your BharatDoc account password has been successfully changed. If you made this change, no further action is needed.
    </p>
    <div style="margin-top:24px;padding:16px;background-color:#dcfce7;border:1px solid #86efac;border-radius:8px;">
      <p style="margin:0;color:#166534;font-size:13px;font-weight:600;">✅ Password Updated Successfully</p>
      <p style="margin:4px 0 0;color:#166534;font-size:12px;">
        Your new password is now active. You can sign in with your new password immediately.
      </p>
    </div>
    <div style="margin-top:16px;padding:16px;background-color:#fee2e2;border:1px solid #fca5a5;border-radius:8px;">
      <p style="margin:0;color:#991b1b;font-size:12px;font-weight:600;">⚠️ Didn't make this change?</p>
      <p style="margin:4px 0 0;color:#991b1b;font-size:12px;">
        If you did not change your password, your account may have been compromised. Contact support immediately.
      </p>
    </div>
    """
    return _send_email(to_email, "Your BharatDoc Password Was Changed", _base_template("Password Changed", content))


def send_account_locked_notification(to_email: str) -> bool:
    """Notify user that their account has been temporarily locked due to failed login attempts."""
    content = """
    <p style="color:#475569;font-size:15px;line-height:1.7;">
      Your BharatDoc account has been temporarily locked due to multiple failed login attempts.
      This is a security measure to protect your account from unauthorized access.
    </p>
    <div style="margin-top:24px;padding:16px;background-color:#fee2e2;border:1px solid #fca5a5;border-radius:8px;">
      <p style="margin:0;color:#991b1b;font-size:13px;font-weight:600;">🔒 Account Temporarily Locked</p>
      <p style="margin:4px 0 0;color:#991b1b;font-size:12px;">
        Your account will automatically unlock in <strong>30 minutes</strong>. If this was you, simply wait and try again.
        If this was not you, consider resetting your password immediately.
      </p>
    </div>
    """
    return _send_email(to_email, "BharatDoc Account Locked — Security Alert", _base_template("Account Locked", content))
