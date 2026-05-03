"""
Phase 18: Auth Hardening — Core Authentication Module
Enterprise-grade security features:
  1. Bcrypt password hashing with automatic salt
  2. JWT token creation with iat (issued-at) claim
  3. Account lockout after MAX_FAILED_ATTEMPTS (brute-force protection)
  4. Password change timestamp validation (invalidate old tokens)
  5. Email verification enforcement
"""

import os
import logging
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from database import get_db
import models, schemas

logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey12345")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# ── Brute-Force Protection ──
MAX_FAILED_ATTEMPTS = 5  # Lock after 5 consecutive failures
LOCKOUT_DURATION_MINUTES = 30  # 30-minute lockout

# ── Email Verification Toggle ──
# Set to "false" to allow login without email verification (dev mode)
REQUIRE_EMAIL_VERIFICATION = os.getenv("REQUIRE_EMAIL_VERIFICATION", "true").lower() == "true"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=15)
    to_encode.update({
        "exp": expire,
        "iat": now,  # Issued-at claim for password-change invalidation
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def check_account_lockout(user: models.User) -> None:
    """
    Check if account is locked due to failed login attempts.
    Raises HTTP 423 (Locked) if the lockout is still active.
    Automatically unlocks if the lockout period has passed.
    """
    if user.locked_until and user.locked_until > datetime.now(timezone.utc):
        remaining = (user.locked_until - datetime.now(timezone.utc)).seconds // 60
        raise HTTPException(
            status_code=423,  # HTTP 423 Locked
            detail=f"Account temporarily locked due to too many failed login attempts. "
                   f"Try again in {remaining + 1} minutes.",
        )


def record_failed_login(user: models.User, db: Session) -> None:
    """
    Increment failed login counter. Lock account if threshold is reached.
    Sends a notification email on lockout.
    """
    user.failed_login_attempts = (user.failed_login_attempts or 0) + 1

    if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
        logger.warning(f"Account locked: {user.email} — {user.failed_login_attempts} failed attempts")

        # Send lockout notification (non-blocking — failures are logged, not raised)
        try:
            from email_service import send_account_locked_notification
            send_account_locked_notification(user.email)
        except Exception as e:
            logger.error(f"Failed to send lockout notification: {e}")

    db.commit()


def record_successful_login(user: models.User, db: Session) -> None:
    """Reset failed login counter on successful authentication."""
    if user.failed_login_attempts > 0 or user.locked_until is not None:
        user.failed_login_attempts = 0
        user.locked_until = None
        db.commit()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
        token_data = schemas.TokenData(email=email)
    except JWTError:
        raise credentials_exception
    
    user = db.query(models.User).filter(models.User.email == token_data.email).first()
    if user is None:
        raise credentials_exception

    # ── Password-change invalidation ──
    # If the user changed their password AFTER this token was issued,
    # this token is no longer valid (prevents stolen-token reuse).
    token_iat = payload.get("iat")
    if token_iat and user.password_changed_at:
        token_issued = datetime.fromtimestamp(token_iat, tz=timezone.utc)
        if token_issued < user.password_changed_at:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Password has been changed. Please log in again.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    return user
