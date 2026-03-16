"""
Authentication Router - Clean Rebuild
Simple, clear, and working implementation
"""
from fastapi import APIRouter, Depends, HTTPException, status, Form, Request as FastAPIRequest
from fastapi.responses import JSONResponse, RedirectResponse
from typing import Optional, Annotated
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone
from app.database import get_db
from app.models import User, AuthProvider
from app.dependencies.auth import get_current_active_user
from app.core.auth import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    is_valid_email,
    is_temporary_email,
    validate_password_strength,
    generate_verification_token,
    generate_password_reset_token
)
from app.core.oauth import oauth, verify_google_email
from app.schemas.auth import (
    UserRegister,
    AuthResponse,
    UserResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    ProfileUpdate,
    PasswordChange,
    PasswordResetRequest,
    PasswordResetConfirm
)
from app.config import settings
from app.services.email_service import email_service
import httpx
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


# ============================================================================
# TOKEN ENDPOINT - For Swagger UI OAuth2 Authorization
# ============================================================================
@router.post("/token", 
             summary="Get OAuth2 Token",
             description="OAuth2 token endpoint for Swagger UI authorization. Returns access token.",
             response_model=dict,
             responses={
                 200: {
                     "description": "Successful response",
                     "content": {
                         "application/json": {
                             "example": {
                                 "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                                 "token_type": "bearer"
                             }
                         }
                     }
                 }
             })
async def get_token(
    username: str = Form(..., description="Email address (used as username)"),
    password: str = Form(..., description="User password"),
    grant_type: Optional[str] = Form("password", description="OAuth2 grant type"),
    db: Session = Depends(get_db)
):
    """
    OAuth2 token endpoint for Swagger UI
    
    This endpoint is used by Swagger UI's "Authorize" button.
    Returns: {"access_token": "...", "token_type": "bearer"}
    """
    # Normalize email to lowercase for case-insensitive comparison
    normalized_email = username.lower().strip()
    print(f"🔐 Token request - Email: {normalized_email}")
    
    # Find user by email (case-insensitive)
    user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if not user:
        print(f"❌ User not found: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not user.hashed_password or not verify_password(password, user.hashed_password):
        print(f"❌ Invalid password for: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    # Update last login
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    # Generate access token
    access_token = create_access_token(data={"sub": user.email})
    
    print(f"✅ Token generated for user: {user.email} (ID: {user.id})")
    
    # Return OAuth2 standard format - Swagger UI requires this exact format
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ============================================================================
# REGISTRATION
# ============================================================================
@router.post("/register", 
             response_model=AuthResponse, 
             status_code=status.HTTP_201_CREATED,
             summary="Register New User",
             description="Create a new user account")
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
):
    """Register a new user account"""
    try:
        # Normalize email to lowercase for consistency
        normalized_email = user_data.email.lower().strip()
        logger.info(f"Registration attempt for email: {normalized_email}")
        
        # Validate email
        if not is_valid_email(normalized_email):
            logger.warning(f"Invalid email format: {normalized_email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
        
        if is_temporary_email(normalized_email):
            logger.warning(f"Temporary email rejected: {normalized_email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Temporary email addresses are not allowed"
            )
        
        # Check if email already exists (case-insensitive comparison)
        existing_user = db.query(User).filter(
            func.lower(User.email) == normalized_email
        ).first()
        if existing_user:
            logger.warning(f"Email already registered: {normalized_email} (found: {existing_user.email})")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Validate password strength
        is_valid, error_msg = validate_password_strength(user_data.password)
        if not is_valid:
            logger.warning(f"Password validation failed for: {normalized_email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Create new user with normalized email
        logger.info(f"Creating new user: {normalized_email}")
        new_user = User(
            email=normalized_email,
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            auth_provider=AuthProvider.EMAIL,
            is_verified=False,
            verification_token=generate_verification_token()
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"User created successfully with ID: {new_user.id}")
        
        # Send verification email (non-blocking - don't fail registration if email fails)
        try:
            logger.info(f"Attempting to send verification email to: {new_user.email}")
            email_service.send_verification_email(new_user.email, new_user.verification_token)
            logger.info(f"Verification email sent successfully to: {new_user.email}")
        except Exception as e:
            logger.error(f"Failed to send verification email to {new_user.email}: {e}", exc_info=True)
            # Continue with registration even if email fails
        
        # Generate tokens
        logger.info(f"Generating tokens for user: {normalized_email}")
        access_token = create_access_token(data={"sub": normalized_email})
        refresh_token = create_refresh_token(data={"sub": normalized_email})
        
        logger.info(f"Registration successful for: {normalized_email}")
        return AuthResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(
                id=new_user.id,
                email=new_user.email,
                username=new_user.username,
                full_name=new_user.full_name,
                profile_picture=new_user.profile_picture,
                auth_provider=new_user.auth_provider.value,
                is_verified=new_user.is_verified,
                storage_used=new_user.storage_used,
                reports_generated=new_user.reports_generated,
                created_at=new_user.created_at
            )
        )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error during registration: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


# ============================================================================
# LOGIN (Alternative endpoint that returns full user info)
# ============================================================================
@router.post("/login", 
             response_model=AuthResponse,
             summary="Login",
             description="Login with email and password, returns tokens and user info")
async def login(
    username: str = Form(..., description="Email address"),
    password: str = Form(..., description="User password"),
    db: Session = Depends(get_db)
):
    """Login with email and password"""
    # Normalize email to lowercase for case-insensitive comparison
    normalized_email = username.lower().strip()
    logger.info(f"Login attempt for email: {normalized_email} (original: {username})")
    
    user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    
    if not user:
        logger.warning(f"Login attempt failed: user not found for email {normalized_email}")
        # Check if user exists with different case
        all_users = db.query(User).all()
        matching_emails = [u.email for u in all_users if u.email.lower() == normalized_email]
        if matching_emails:
            logger.warning(f"Found user with different case: {matching_emails}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.info(f"User found: {user.email}, has_password: {bool(user.hashed_password)}, is_active: {user.is_active}")
    
    if not user.hashed_password:
        logger.warning(f"Login attempt failed: user {normalized_email} has no password (OAuth user?)")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    password_valid = verify_password(password, user.hashed_password)
    logger.info(f"Password verification result: {password_valid}")
    
    if not password_valid:
        logger.warning(f"Login attempt failed: invalid password for email {normalized_email}")
        # Log more details for debugging
        logger.debug(f"Password length: {len(password)}, Hash length: {len(user.hashed_password) if user.hashed_password else 0}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        logger.warning(f"Login attempt failed: inactive user {normalized_email}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    logger.info(f"Login successful for user: {user.email} (ID: {user.id})")
    user.last_login = datetime.now(timezone.utc)
    db.commit()
    
    # Use normalized email for token generation
    access_token = create_access_token(data={"sub": user.email.lower()})
    refresh_token = create_refresh_token(data={"sub": user.email.lower()})
    
    logger.info(f"Tokens generated successfully for user: {user.email}")
    
    return AuthResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse(
            id=user.id,
            email=user.email,
            username=user.username,
            full_name=user.full_name,
            profile_picture=user.profile_picture,
            auth_provider=user.auth_provider.value,
            is_verified=user.is_verified,
            storage_used=user.storage_used,
            reports_generated=user.reports_generated,
            created_at=user.created_at
        )
    )


# ============================================================================
# GET CURRENT USER
# ============================================================================
@router.get("/me", 
            response_model=UserResponse,
            summary="Get Current User",
            description="Get information about the currently authenticated user")
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Get current authenticated user information"""
    from app.services.job_service import sync_user_storage_usage

    storage_used = sync_user_storage_usage(db, current_user.id)

    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        profile_picture=current_user.profile_picture,
        auth_provider=current_user.auth_provider.value,
        is_verified=current_user.is_verified,
        storage_used=storage_used,
        reports_generated=current_user.reports_generated,
        created_at=current_user.created_at
    )


# ============================================================================
# TOKEN REFRESH
# ============================================================================
@router.post("/refresh", 
             response_model=RefreshTokenResponse,
             summary="Refresh Token",
             description="Get a new access token using a refresh token")
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """Refresh access token"""
    payload = verify_token(request.refresh_token)
    
    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    email = payload.get("sub")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    # Normalize email from token for case-insensitive lookup
    normalized_email = email.lower().strip()
    user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    access_token = create_access_token(data={"sub": user.email.lower()})
    return RefreshTokenResponse(access_token=access_token)


# ============================================================================
# EMAIL VERIFICATION
# ============================================================================
@router.post("/verify-email/{token}",
             summary="Verify Email",
             description="Verify user email address using verification token")
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """Verify user email"""
    user = db.query(User).filter(User.verification_token == token).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification token"
        )
    
    user.is_verified = True
    user.verification_token = None
    db.commit()
    
    return {"message": "Email verified successfully"}


# ============================================================================
# LOGOUT
# ============================================================================
@router.post("/logout",
             summary="Logout",
             description="Logout the current user")
async def logout(
    current_user: Annotated[User, Depends(get_current_active_user)]
):
    """Logout user"""
    return {"message": "Logged out successfully"}


# ============================================================================
# GOOGLE OAUTH (if configured)
# ============================================================================
@router.get("/google/login",
            summary="Google OAuth Login",
            description="Initiate Google OAuth login flow")
async def google_login(request: FastAPIRequest):
    """Initiate Google OAuth login"""
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in environment variables."
        )
    
    # Construct redirect URI - must match exactly what's in Google Console
    # Use the request's base URL to handle both http and https correctly
    base_url = str(request.base_url).rstrip('/')
    redirect_uri = f"{base_url}/api/v1/auth/google/callback"
    
    # Debug: Print redirect URI for troubleshooting
    print(f"🔐 Google OAuth redirect URI: {redirect_uri}")
    
    return await oauth.google.authorize_redirect(request, redirect_uri)


@router.get("/google/callback",
            summary="Google OAuth Callback",
            description="Handle Google OAuth callback")
async def google_callback(
    request: FastAPIRequest,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback"""
    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        
        if not user_info:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    'https://www.googleapis.com/oauth2/v1/userinfo',
                    headers={'Authorization': f'Bearer {token["access_token"]}'}
                )
                user_info = response.json()
        
        email = user_info.get('email')
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not retrieve email from Google"
            )
        
        if not await verify_google_email(email, token['access_token']):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not verified by Google"
            )
        
        # Normalize email to lowercase for consistency
        normalized_email = email.lower().strip()
        user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
        
        if not user:
            user = User(
                email=normalized_email,
                full_name=user_info.get('name'),
                profile_picture=user_info.get('picture'),
                auth_provider=AuthProvider.GOOGLE,
                oauth_id=user_info.get('sub'),
                is_verified=True,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            user.last_login = datetime.now(timezone.utc)
            if not user.profile_picture:
                user.profile_picture = user_info.get('picture')
            db.commit()
        
        access_token = create_access_token(data={"sub": user.email.lower()})
        refresh_token = create_refresh_token(data={"sub": user.email.lower()})
        
        return RedirectResponse(
            url=f"{settings.FRONTEND_URL}/auth/callback?access_token={access_token}&refresh_token={refresh_token}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OAuth error: {str(e)}"
        )


# ============================================================================
# PROFILE MANAGEMENT
# ============================================================================
@router.patch("/profile",
              response_model=UserResponse,
              summary="Update Profile",
              description="Update user profile information (name, username)")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Update user profile"""
    from app.services.job_service import sync_user_storage_usage

    if profile_data.full_name is not None:
        current_user.full_name = profile_data.full_name
    
    if profile_data.username is not None:
        # Check if username is already taken
        existing_user = db.query(User).filter(
            User.username == profile_data.username,
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        current_user.username = profile_data.username
    
    db.commit()
    db.refresh(current_user)
    storage_used = sync_user_storage_usage(db, current_user.id)
    
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        full_name=current_user.full_name,
        profile_picture=current_user.profile_picture,
        auth_provider=current_user.auth_provider.value,
        is_verified=current_user.is_verified,
        storage_used=storage_used,
        reports_generated=current_user.reports_generated,
        created_at=current_user.created_at
    )


@router.post("/change-password",
             summary="Change Password",
             description="Change user password. Only available for email/password users.")
async def change_password(
    password_data: PasswordChange,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Change user password - only for email/password users"""
    # Check if user has password (not OAuth user)
    if current_user.auth_provider != AuthProvider.EMAIL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password change is only available for email/password accounts"
        )
    
    if not current_user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No password set for this account"
        )
    
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Current password is incorrect"
        )
    
    # Validate new password strength
    is_valid, error_msg = validate_password_strength(password_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}


# ============================================================================
# PASSWORD RESET (Email/Password users only)
# ============================================================================
@router.post("/password-reset/request",
             summary="Request Password Reset",
             description="Request a password reset email. Only for email/password users.")
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request password reset - sends reset token (in production, would send email)"""
    # Normalize email to lowercase for case-insensitive comparison
    normalized_email = reset_request.email.lower().strip()
    user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
    
    # Don't reveal if user exists (security best practice)
    if not user:
        return {"message": "If an account exists with this email, a password reset link has been sent"}
    
    # Only allow password reset for email/password users
    if user.auth_provider != AuthProvider.EMAIL:
        return {"message": "If an account exists with this email, a password reset link has been sent"}
    
    # Generate reset token
    from datetime import timedelta
    reset_token = generate_password_reset_token()
    user.password_reset_token = reset_token
    user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)  # 1 hour expiry
    db.commit()
    
    # Send password reset email
    email_service.send_password_reset_email(user.email, reset_token)
    
    return {
        "message": "If an account exists with this email, a password reset link has been sent"
    }


@router.post("/password-reset/confirm",
             summary="Confirm Password Reset",
             description="Reset password using reset token. Only for email/password users.")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token"""
    user = db.query(User).filter(User.password_reset_token == reset_data.token).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Check if token expired
    if user.password_reset_expires:
        # Ensure both datetimes are timezone-aware for comparison
        expires_at = user.password_reset_expires
        if expires_at.tzinfo is None:
            # If database returned timezone-naive datetime, assume UTC
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        
        now = datetime.now(timezone.utc)
        if expires_at < now:
            user.password_reset_token = None
            user.password_reset_expires = None
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reset token has expired. Please request a new one."
            )
    
    # Only allow for email/password users
    if user.auth_provider != AuthProvider.EMAIL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password reset is only available for email/password accounts"
        )
    
    # Validate new password strength
    is_valid, error_msg = validate_password_strength(reset_data.new_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )
    
    # Update password and clear reset token
    user.hashed_password = get_password_hash(reset_data.new_password)
    user.password_reset_token = None
    user.password_reset_expires = None
    db.commit()
    
    return {"message": "Password reset successfully"}


# ============================================================================
# ACCOUNT DELETION
# ============================================================================
@router.delete("/account",
               summary="Delete Account",
               description="Permanently delete the authenticated user's account and all associated data")
async def delete_account(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: Session = Depends(get_db)
):
    """Delete user account and all associated data"""
    from pathlib import Path
    from app.services.job_service import cleanup_job_artifacts
    from app.models import Job
    import shutil
    
    user_id = current_user.id
    
    try:
        # 1. Delete all user's jobs (cascade will handle this, but we also need to delete files)
        user_jobs = db.query(Job).filter(Job.user_id == user_id).all()
        for job in user_jobs:
            cleanup_job_artifacts(job)
        
        # 2. Delete user's upload directory and all files
        user_upload_dir = Path(settings.UPLOAD_DIR) / f"user_{user_id}"
        if user_upload_dir.exists():
            try:
                shutil.rmtree(user_upload_dir)
            except Exception as e:
                print(f"Warning: Could not delete user upload directory: {e}")
        
        # 3. Delete user from database (cascade will delete jobs)
        db.delete(current_user)
        db.commit()
        
        return {
            "message": "Account deleted successfully",
            "success": True
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete account: {str(e)}"
        )
