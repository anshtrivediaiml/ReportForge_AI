"""
Authentication dependencies for FastAPI routes
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import User
from app.core.auth import verify_token
from typing import Optional

# OAuth2PasswordBearer for Swagger UI - MUST match OpenAPI schema
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    scheme_name="OAuth2PasswordBearer",  # Must match OpenAPI schema name
    auto_error=True  # Raise error if token missing (required auth)
)

# Optional auth scheme for endpoints that work with or without auth
oauth2_scheme_optional = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    scheme_name="OAuth2PasswordBearer",
    auto_error=False  # Don't raise error if token missing (for optional auth)
)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    Raises 401 if token is invalid or user not found
    
    DEBUG: Prints token validation steps for troubleshooting
    """
    # Debug: Print token received (first 20 chars for security)
    print(f"🔑 Token received: {token[:20]}..." if len(token) > 20 else f"🔑 Token received: {token}")
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify token
    payload = verify_token(token)
    if payload is None:
        print("❌ Token validation failed: Invalid token")
        raise credentials_exception
    
    # Extract email from token
    email: str = payload.get("sub")
    if email is None:
        print("❌ Token validation failed: No email in token payload")
        raise credentials_exception
    
    # Normalize email to lowercase for case-insensitive lookup
    normalized_email = email.lower().strip()
    print(f"✅ Token valid - Email: {normalized_email}")
    
    # Find user in database (case-insensitive comparison)
    user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if user is None:
        print(f"❌ User not found for email: {email}")
        raise credentials_exception
    
    print(f"✅ User found - ID: {user.id}, Email: {user.email}")
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user
    Raises 403 if user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    return current_user


async def get_current_user_optional(
    token: Optional[str] = Depends(oauth2_scheme_optional),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None
    Used for endpoints that work with or without authentication
    """
    if token is None:
        return None
    
    payload = verify_token(token)
    if payload is None:
        return None
    
    email: str = payload.get("sub")
    if email is None:
        return None
    
    # Normalize email to lowercase for case-insensitive lookup
    normalized_email = email.lower().strip()
    user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    return user
