"""
Script to create a fresh test user for authentication testing
Run this to create a new user: python api/create_test_user.py
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal, Base, engine
from app.models import User, AuthProvider, Job  # Import all models
from app.core.auth import get_password_hash, is_valid_email, validate_password_strength
from datetime import datetime, timezone

def create_test_user():
    """Create a fresh test user"""
    import sys
    import io
    # Fix encoding for Windows console
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    # Ensure tables exist
    print("Creating database tables if they don't exist...")
    Base.metadata.create_all(bind=engine)
    print("[OK] Database tables ready")
    
    db = SessionLocal()
    
    try:
        # Test user credentials
        email = "testuser@example.com"
        password = "TestPass123!"
        full_name = "Test User"
        
        # Validate email
        if not is_valid_email(email):
            print("[ERROR] Invalid email format")
            return
        
        # Validate password
        is_valid, error_msg = validate_password_strength(password)
        if not is_valid:
            print(f"[ERROR] Password validation failed: {error_msg}")
            return
        
        # Check if user exists
        existing_user = db.query(User).filter(User.email == email).first()
        if existing_user:
            print(f"[WARNING] User {email} already exists. Deleting old user...")
            db.delete(existing_user)
            db.commit()
        
        # Create new user
        hashed_password = get_password_hash(password)
        new_user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            auth_provider=AuthProvider.EMAIL,
            is_verified=True,  # Skip verification for testing
            is_active=True
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        print("=" * 60)
        print("[SUCCESS] TEST USER CREATED SUCCESSFULLY!")
        print("=" * 60)
        print(f"Email:    {email}")
        print(f"Password: {password}")
        print(f"User ID:  {new_user.id}")
        print("=" * 60)
        print("\n[INFO] Use these credentials to test authentication:")
        print(f"   - In Swagger UI: username={email}, password={password}")
        print(f"   - Or use the /api/v1/auth/token endpoint")
        print("=" * 60)
        
    except Exception as e:
        print(f"[ERROR] Error creating user: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    create_test_user()

