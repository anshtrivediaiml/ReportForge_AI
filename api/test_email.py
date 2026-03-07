"""
Test Email Functionality
Run this script to test if email service is working
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.email_service import email_service

def test_email():
    """Test sending a verification email"""
    print("=" * 60)
    print("Testing Email Service")
    print("=" * 60)
    
    # Check if email service is enabled
    if not email_service.enabled:
        print("[ERROR] Email service is DISABLED")
        print("\nPlease check your .env file and ensure these are set:")
        print("  SMTP_HOST=smtp.gmail.com")
        print("  SMTP_PORT=587")
        print("  SMTP_USERNAME=your-email@gmail.com")
        print("  SMTP_PASSWORD=your-app-password")
        print("  SMTP_FROM_EMAIL=your-email@gmail.com")
        print("  SMTP_USE_TLS=true")
        return False
    
    print(f"[OK] Email service is ENABLED")
    print(f"   SMTP Host: {email_service.smtp_host}")
    print(f"   SMTP Port: {email_service.smtp_port}")
    print(f"   From Email: {email_service.from_email}")
    print(f"   Use TLS: {email_service.use_tls}")
    print()
    
    # Get test email from user
    test_email_address = input("Enter your email address to receive test email: ").strip()
    
    if not test_email_address:
        print("[ERROR] No email address provided")
        return False
    
    print(f"\nSending test email to: {test_email_address}")
    print("   Please wait...")
    
    # Test 1: Send simple test email
    test_subject = "Test Email - ReportForge AI"
    test_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
            .container { max-width: 600px; margin: 0 auto; padding: 20px; }
            .button { display: inline-block; padding: 12px 24px; background-color: #4F46E5; color: white; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🎉 Email Service Test</h2>
            <p>Congratulations! Your email service is working correctly.</p>
            <p>This is a test email from ReportForge AI.</p>
            <p>If you received this email, your SMTP configuration is correct!</p>
        </div>
    </body>
    </html>
    """
    
    test_text = """
    Email Service Test
    
    Congratulations! Your email service is working correctly.
    This is a test email from ReportForge AI.
    If you received this email, your SMTP configuration is correct!
    """
    
    success = email_service.send_email(
        to_email=test_email_address,
        subject=test_subject,
        html_content=test_html,
        text_content=test_text
    )
    
    if success:
        print("[OK] Test email sent successfully!")
        print(f"   Check your inbox at: {test_email_address}")
        print()
        
        # Test 2: Send verification email
        print("Testing verification email...")
        verification_token = "test-token-12345"
        success2 = email_service.send_verification_email(test_email_address, verification_token)
        
        if success2:
            print("[OK] Verification email sent successfully!")
        else:
            print("[ERROR] Verification email failed")
        
        print()
        
        # Test 3: Send password reset email
        print("Testing password reset email...")
        reset_token = "test-reset-token-67890"
        success3 = email_service.send_password_reset_email(test_email_address, reset_token)
        
        if success3:
            print("[OK] Password reset email sent successfully!")
        else:
            print("[ERROR] Password reset email failed")
        
        print()
        print("=" * 60)
        print("[OK] All email tests completed!")
        print("=" * 60)
        return True
    else:
        print("[ERROR] Failed to send test email")
        print("   Check your SMTP credentials and network connection")
        return False

if __name__ == "__main__":
    try:
        test_email()
    except KeyboardInterrupt:
        print("\n\nTest cancelled by user")
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

