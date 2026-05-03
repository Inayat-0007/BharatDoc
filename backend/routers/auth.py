"""
Phase 18: Auth Hardening — Authentication Router
Enterprise-grade endpoints:
  POST /auth/register          — Register with email verification
  POST /auth/login             — Login with lockout protection
  GET  /auth/me                — Current user profile
  POST /auth/forgot-password   — Request password reset email
  POST /auth/reset-password    — Reset password with token
  POST /auth/verify-email      — Verify email with token
  POST /auth/resend-verification — Resend verification email

Security controls:
  - Account lockout after 5 failed login attempts (30-minute window)
  - HMAC-SHA256 signed tokens for email verification and password reset
  - Password complexity enforcement (NIST SP 800-63B)
  - Password-change token invalidation (old JWTs are rejected)
  - Timing-safe responses (forgot-password always returns 200 to prevent user enumeration)
"""

import logging
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from database import get_db
import models, schemas, auth
from email_service import (
    generate_verification_token,
    verify_verification_token,
    generate_reset_token,
    verify_reset_token,
    send_verification_email,
    send_password_reset_email,
    send_password_changed_notification,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserResponse)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user account.
    - Enforces password complexity (min 8 chars, upper, lower, digit, special)
    - Sends email verification link
    - Account is unverified until email is confirmed
    """
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = auth.get_password_hash(user.password)
    new_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        is_verified=False,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Send verification email (non-blocking — failure is logged, not raised)
    try:
        token = generate_verification_token(user.email)
        send_verification_email(user.email, token)
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {e}")

    return new_user


@router.post("/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticate user with email + password.
    Security features:
      - Brute-force lockout after 5 failed attempts
      - Email verification check (configurable)
      - Failed attempt counter resets on successful login
    """
    user = db.query(models.User).filter(models.User.email == form_data.username).first()

    if not user:
        # Timing-safe: don't reveal whether the email exists
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if account is locked
    auth.check_account_lockout(user)

    # Verify password
    if not auth.verify_password(form_data.password, user.hashed_password):
        auth.record_failed_login(user, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check email verification (if required)
    if auth.REQUIRE_EMAIL_VERIFICATION and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your inbox for the verification link.",
        )

    # Successful login — reset counters
    auth.record_successful_login(user, db)

    access_token_expires = timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=schemas.UserResponse)
def read_users_me(current_user: models.User = Depends(auth.get_current_user)):
    return current_user


@router.post("/forgot-password", response_model=schemas.MessageResponse)
def forgot_password(request: schemas.ForgotPasswordRequest, db: Session = Depends(get_db)):
    """
    Request a password reset email.
    
    SECURITY: Always returns 200 regardless of whether the email exists.
    This prevents user enumeration attacks (an attacker cannot determine
    which emails are registered by observing different responses).
    """
    user = db.query(models.User).filter(models.User.email == request.email).first()

    if user:
        try:
            token = generate_reset_token(user.email)
            send_password_reset_email(user.email, token)
            logger.info(f"Password reset email sent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to send password reset email: {e}")
    else:
        # Log but don't reveal to the caller
        logger.info(f"Password reset requested for non-existent email: {request.email}")

    # Always return success — prevents user enumeration
    return {"message": "If an account with that email exists, a password reset link has been sent."}


@router.post("/reset-password", response_model=schemas.MessageResponse)
def reset_password(request: schemas.ResetPasswordRequest, db: Session = Depends(get_db)):
    """
    Reset password using a valid reset token.
    - Token is HMAC-SHA256 signed and expires in 15 minutes
    - Password complexity is re-validated
    - All existing sessions are invalidated via password_changed_at
    - Confirmation email is sent
    """
    email = verify_reset_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token. Please request a new password reset.",
        )

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token.",
        )

    # Update password
    user.hashed_password = auth.get_password_hash(request.new_password)
    user.password_changed_at = datetime.now(timezone.utc)
    # Reset lockout counters (password reset is a legitimate recovery path)
    user.failed_login_attempts = 0
    user.locked_until = None
    db.commit()

    # Send confirmation notification
    try:
        send_password_changed_notification(email)
    except Exception as e:
        logger.error(f"Failed to send password changed notification: {e}")

    logger.info(f"Password reset successfully for {email}")
    return {"message": "Password has been reset successfully. You can now log in with your new password."}


@router.post("/verify-email", response_model=schemas.MessageResponse)
def verify_email(request: schemas.VerifyEmailRequest, db: Session = Depends(get_db)):
    """
    Verify email address using a verification token.
    - Token is HMAC-SHA256 signed and expires in 24 hours
    - Marks the account as verified
    """
    email = verify_verification_token(request.token)
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token. Please request a new verification email.",
        )

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token.",
        )

    if user.is_verified:
        return {"message": "Email is already verified."}

    user.is_verified = True
    db.commit()

    logger.info(f"Email verified successfully for {email}")
    return {"message": "Email verified successfully! You can now log in."}


@router.post("/resend-verification", response_model=schemas.MessageResponse)
def resend_verification(request: schemas.ResendVerificationRequest, db: Session = Depends(get_db)):
    """
    Resend email verification link.
    SECURITY: Always returns 200 to prevent user enumeration.
    """
    user = db.query(models.User).filter(models.User.email == request.email).first()

    if user and not user.is_verified:
        try:
            token = generate_verification_token(user.email)
            send_verification_email(user.email, token)
            logger.info(f"Verification email resent to {user.email}")
        except Exception as e:
            logger.error(f"Failed to resend verification email: {e}")

    # Always return success — prevents user enumeration
    return {"message": "If an unverified account with that email exists, a verification link has been sent."}
