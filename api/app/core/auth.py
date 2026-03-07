"""
Authentication utilities
Password hashing, JWT tokens, email validation, password strength
"""
import bcrypt
from jose import JWTError, jwt
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
import re
import secrets
from app.config import settings

# Bcrypt configuration
BCRYPT_ROUNDS = 12

# Temporary email domain blacklist
TEMPORARY_EMAIL_DOMAINS = [
    "tempmail.com", "10minutemail.com", "guerrillamail.com", "mailinator.com",
    "throwaway.email", "temp-mail.org", "getnada.com", "fakeinbox.com",
    "trashmail.com", "maildrop.cc", "mohmal.com", "yopmail.com",
    "tempail.com", "sharklasers.com", "guerrillamailblock.com"
]


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a bcrypt hash
    Note: bcrypt has a 72-byte limit, so we truncate if necessary
    """
    try:
        if not plain_password or not hashed_password:
            return False
        
        # Bcrypt has a 72-byte limit, truncate if necessary
        if isinstance(plain_password, str):
            password_bytes = plain_password.encode('utf-8')
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
            
            # Ensure hashed_password is bytes
            if isinstance(hashed_password, str):
                hashed_bytes = hashed_password.encode('utf-8')
            else:
                hashed_bytes = hashed_password
            
            # Use bytes directly with bcrypt
            result = bcrypt.checkpw(password_bytes, hashed_bytes)
            return result
        return False
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Password verification error: {e}", exc_info=True)
        return False


def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt directly
    Note: bcrypt has a 72-byte limit, so we truncate if necessary
    """
    try:
        # Bcrypt has a 72-byte limit, truncate if necessary
        if isinstance(password, str):
            password_bytes = password.encode('utf-8')
            if len(password_bytes) > 72:
                password_bytes = password_bytes[:72]
            
            # Generate salt and hash using bcrypt directly
            salt = bcrypt.gensalt(rounds=BCRYPT_ROUNDS)
            hashed = bcrypt.hashpw(password_bytes, salt)
            return hashed.decode('utf-8')
        raise ValueError("Password must be a string")
    except Exception as e:
        # Fallback: if bcrypt fails, raise a more helpful error
        raise ValueError(f"Password hashing failed: {str(e)}")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT refresh token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token"""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except JWTError:
        return None


def is_valid_email(email: str) -> bool:
    """Validate email format using regex"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_temporary_email(email: str) -> bool:
    """Check if email is from a temporary email service"""
    if not email:
        return False
    domain = email.split('@')[-1].lower()
    return domain in TEMPORARY_EMAIL_DOMAINS


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength
    Returns: (is_valid, error_message)
    Rules:
    - Minimum 8 characters
    - At least 1 uppercase letter
    - At least 1 lowercase letter
    - At least 1 digit
    - At least 1 special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"
    
    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"
    
    if not re.search(r'\d', password):
        return False, "Password must contain at least one digit"
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, "Password must contain at least one special character"
    
    return True, ""


def generate_verification_token() -> str:
    """Generate a secure verification token"""
    return secrets.token_urlsafe(32)


def generate_password_reset_token() -> str:
    """Generate a secure password reset token"""
    return secrets.token_urlsafe(32)

