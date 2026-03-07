"""
Script to reset a user's password
Usage: python reset_user_password.py <email> <new_password>
"""
import sys
import os

# Add the api directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models import User
from app.core.auth import get_password_hash
from sqlalchemy import func

def reset_password(email: str, new_password: str):
    """Reset password for a user"""
    db = SessionLocal()
    try:
        # Normalize email to lowercase
        normalized_email = email.lower().strip()
        
        # Find user (case-insensitive)
        user = db.query(User).filter(func.lower(User.email) == normalized_email).first()
        
        if not user:
            print(f"[ERROR] User not found: {email}")
            return False
        
        print(f"[SUCCESS] User found: {user.email} (ID: {user.id})")
        print(f"   Auth provider: {user.auth_provider.value}")
        print(f"   Has password: {bool(user.hashed_password)}")
        
        # Hash the new password
        new_hash = get_password_hash(new_password)
        
        # Update the password
        user.hashed_password = new_hash
        db.commit()
        
        print(f"[SUCCESS] Password reset successful for: {user.email}")
        print(f"   New password hash: {new_hash[:30]}...")
        return True
        
    except Exception as e:
        print(f"[ERROR] Error resetting password: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python reset_user_password.py <email> <new_password>")
        print("\nExample:")
        print('  python reset_user_password.py habibiii7814@gmail.com "NewPassword123!"')
        sys.exit(1)
    
    email = sys.argv[1]
    new_password = sys.argv[2]
    
    if len(new_password) < 8:
        print("[ERROR] Password must be at least 8 characters long")
        sys.exit(1)
    
    print(f"[INFO] Resetting password for: {email}")
    success = reset_password(email, new_password)
    
    if success:
        print("\n[SUCCESS] Password reset complete! You can now login with the new password.")
    else:
        print("\n[ERROR] Password reset failed. Please check the error messages above.")
        sys.exit(1)

