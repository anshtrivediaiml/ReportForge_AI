"""
Email Service - SMTP integration for transactional emails
Supports Gmail, Brevo, and other SMTP providers
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
from app.config import settings
from dotenv import load_dotenv
import logging

# Load .env file explicitly
load_dotenv()

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending transactional emails via SMTP"""
    
    def __init__(self):
        # Load from environment (dotenv handles .env file)
        self.smtp_host = os.getenv("SMTP_HOST")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", "noreply@reportforge.ai")
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        
        self.enabled = bool(self.smtp_host and self.smtp_username and self.smtp_password)
        
        if not self.enabled:
            logger.warning("SMTP credentials not found. Email service disabled.")
        else:
            logger.info(f"Email service enabled. SMTP: {self.smtp_host}:{self.smtp_port}")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """Send an email via SMTP"""
        if not self.enabled:
            logger.warning(f"Email service disabled. Would send to {to_email}: {subject}")
            # In development, print to console
            print(f"\n{'='*60}")
            print(f"EMAIL (SMTP disabled):")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Content: {html_content[:200]}...")
            print(f"{'='*60}\n")
            return False
        
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email
            
            # Add text and HTML parts
            if text_content:
                part1 = MIMEText(text_content, 'plain')
                msg.attach(part1)
            
            part2 = MIMEText(html_content, 'html')
            msg.attach(part2)
            
            # Connect to SMTP server
            if self.use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)
            
            # Login and send
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent successfully to {to_email}")
            return True
                
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False
    
    def send_verification_email(self, to_email: str, verification_token: str) -> bool:
        """Send email verification link"""
        verification_url = f"{settings.FRONTEND_URL}/verify-email?token={verification_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Verify Your Email - ReportForge AI</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #1e293b;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    padding: 20px;
                }}
                .email-wrapper {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: #ffffff;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                }}
                .header {{
                    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a855f7 100%);
                    padding: 40px 30px;
                    text-align: center;
                    color: white;
                }}
                .logo {{
                    font-size: 32px;
                    font-weight: 700;
                    margin-bottom: 10px;
                    letter-spacing: -0.5px;
                }}
                .header-subtitle {{
                    font-size: 16px;
                    opacity: 0.95;
                    font-weight: 300;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .icon-container {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .icon-circle {{
                    display: inline-block;
                    width: 80px;
                    height: 80px;
                    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 40px;
                    color: white;
                    box-shadow: 0 10px 30px rgba(99, 102, 241, 0.4);
                }}
                h1 {{
                    font-size: 28px;
                    font-weight: 700;
                    color: #1e293b;
                    margin-bottom: 15px;
                    text-align: center;
                }}
                .welcome-text {{
                    font-size: 16px;
                    color: #475569;
                    margin-bottom: 30px;
                    text-align: center;
                    line-height: 1.7;
                }}
                .button-container {{
                    text-align: center;
                    margin: 35px 0;
                }}
                .button {{
                    display: inline-block;
                    padding: 16px 40px;
                    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
                    color: white !important;
                    text-decoration: none;
                    border-radius: 12px;
                    font-weight: 600;
                    font-size: 16px;
                    box-shadow: 0 8px 20px rgba(99, 102, 241, 0.4);
                    transition: all 0.3s ease;
                    letter-spacing: 0.3px;
                }}
                .button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 12px 30px rgba(99, 102, 241, 0.5);
                }}
                .link-container {{
                    background: #f8fafc;
                    border-left: 4px solid #6366f1;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 30px 0;
                }}
                .link-label {{
                    font-size: 13px;
                    color: #64748b;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 10px;
                }}
                .link-text {{
                    word-break: break-all;
                    color: #6366f1;
                    font-size: 13px;
                    font-family: 'Courier New', monospace;
                }}
                .expiry-notice {{
                    background: #fef3c7;
                    border-left: 4px solid #f59e0b;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 25px 0;
                }}
                .expiry-notice p {{
                    color: #92400e;
                    font-size: 14px;
                    margin: 0;
                }}
                .footer {{
                    background: #f8fafc;
                    padding: 30px;
                    text-align: center;
                    border-top: 1px solid #e2e8f0;
                }}
                .footer-text {{
                    font-size: 13px;
                    color: #64748b;
                    line-height: 1.6;
                }}
                .footer-text a {{
                    color: #6366f1;
                    text-decoration: none;
                }}
                .divider {{
                    height: 1px;
                    background: #e2e8f0;
                    margin: 30px 0;
                }}
                @media only screen and (max-width: 600px) {{
                    .content {{
                        padding: 30px 20px;
                    }}
                    .header {{
                        padding: 30px 20px;
                    }}
                    h1 {{
                        font-size: 24px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="email-wrapper">
                <div class="header">
                    <div class="logo">ReportForge AI</div>
                    <div class="header-subtitle">Intelligent Report Generation</div>
                </div>
                
                <div class="content">
                    <div class="icon-container">
                        <div class="icon-circle" style="font-size: 32px;">✉</div>
                    </div>
                    
                    <h1>Verify Your Email Address</h1>
                    
                    <p class="welcome-text">
                        Welcome to ReportForge AI!<br>
                        We're excited to have you on board. To get started, please verify your email address by clicking the button below.
                    </p>
                    
                    <div class="button-container">
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </div>
                    
                    <div class="link-container">
                        <div class="link-label">Or copy this link:</div>
                        <div class="link-text">{verification_url}</div>
                    </div>
                    
                    <div class="expiry-notice">
                        <p><strong>Important:</strong> This verification link will expire in 24 hours.</p>
                    </div>
                    
                    <div class="divider"></div>
                    
                    <p style="font-size: 14px; color: #64748b; text-align: center; line-height: 1.7;">
                        If you didn't create an account with ReportForge AI, you can safely ignore this email. 
                        Your email address won't be used for anything else.
                    </p>
                </div>
                
                <div class="footer">
                    <p class="footer-text">
                        <strong>ReportForge AI</strong><br>
                        Transform your documents into professional reports with AI<br>
                        <a href="{settings.FRONTEND_URL}">Visit our website</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Verify Your Email Address
        
        Thank you for signing up for ReportForge AI!
        
        Please verify your email address by visiting:
        {verification_url}
        
        This link will expire in 24 hours.
        
        If you didn't create an account, please ignore this email.
        """
        
        return self.send_email(
            to_email=to_email,
            subject="Verify Your Email Address - ReportForge AI",
            html_content=html_content,
            text_content=text_content
        )
    
    def send_password_reset_email(self, to_email: str, reset_token: str) -> bool:
        """Send password reset link"""
        reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
        
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Reset Your Password - ReportForge AI</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                    line-height: 1.6;
                    color: #1e293b;
                    background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
                    padding: 20px;
                }}
                .email-wrapper {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: #ffffff;
                    border-radius: 16px;
                    overflow: hidden;
                    box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                }}
                .header {{
                    background: linear-gradient(135deg, #f59e0b 0%, #ef4444 50%, #dc2626 100%);
                    padding: 40px 30px;
                    text-align: center;
                    color: white;
                }}
                .logo {{
                    font-size: 32px;
                    font-weight: 700;
                    margin-bottom: 10px;
                    letter-spacing: -0.5px;
                }}
                .header-subtitle {{
                    font-size: 16px;
                    opacity: 0.95;
                    font-weight: 300;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .icon-container {{
                    text-align: center;
                    margin-bottom: 30px;
                }}
                .icon-circle {{
                    display: inline-block;
                    width: 80px;
                    height: 80px;
                    background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
                    border-radius: 50%;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 40px;
                    color: white;
                    box-shadow: 0 10px 30px rgba(239, 68, 68, 0.4);
                }}
                h1 {{
                    font-size: 28px;
                    font-weight: 700;
                    color: #1e293b;
                    margin-bottom: 15px;
                    text-align: center;
                }}
                .intro-text {{
                    font-size: 16px;
                    color: #475569;
                    margin-bottom: 30px;
                    text-align: center;
                    line-height: 1.7;
                }}
                .button-container {{
                    text-align: center;
                    margin: 35px 0;
                }}
                .button {{
                    display: inline-block;
                    padding: 16px 40px;
                    background: linear-gradient(135deg, #f59e0b 0%, #ef4444 100%);
                    color: white !important;
                    text-decoration: none;
                    border-radius: 12px;
                    font-weight: 600;
                    font-size: 16px;
                    box-shadow: 0 8px 20px rgba(239, 68, 68, 0.4);
                    transition: all 0.3s ease;
                    letter-spacing: 0.3px;
                }}
                .button:hover {{
                    transform: translateY(-2px);
                    box-shadow: 0 12px 30px rgba(239, 68, 68, 0.5);
                }}
                .link-container {{
                    background: #f8fafc;
                    border-left: 4px solid #ef4444;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 30px 0;
                }}
                .link-label {{
                    font-size: 13px;
                    color: #64748b;
                    font-weight: 600;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                    margin-bottom: 10px;
                }}
                .link-text {{
                    word-break: break-all;
                    color: #ef4444;
                    font-size: 13px;
                    font-family: 'Courier New', monospace;
                }}
                .warning-box {{
                    background: #fef2f2;
                    border-left: 4px solid #ef4444;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 25px 0;
                }}
                .warning-box p {{
                    color: #991b1b;
                    font-size: 14px;
                    margin: 5px 0;
                    line-height: 1.6;
                }}
                .warning-box strong {{
                    color: #dc2626;
                }}
                .security-notice {{
                    background: #eff6ff;
                    border-left: 4px solid #3b82f6;
                    padding: 20px;
                    border-radius: 8px;
                    margin: 25px 0;
                }}
                .security-notice p {{
                    color: #1e40af;
                    font-size: 14px;
                    margin: 0;
                    line-height: 1.6;
                }}
                .footer {{
                    background: #f8fafc;
                    padding: 30px;
                    text-align: center;
                    border-top: 1px solid #e2e8f0;
                }}
                .footer-text {{
                    font-size: 13px;
                    color: #64748b;
                    line-height: 1.6;
                }}
                .footer-text a {{
                    color: #ef4444;
                    text-decoration: none;
                }}
                .divider {{
                    height: 1px;
                    background: #e2e8f0;
                    margin: 30px 0;
                }}
                @media only screen and (max-width: 600px) {{
                    .content {{
                        padding: 30px 20px;
                    }}
                    .header {{
                        padding: 30px 20px;
                    }}
                    h1 {{
                        font-size: 24px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="email-wrapper">
                <div class="header">
                    <div class="logo">ReportForge AI</div>
                    <div class="header-subtitle">Password Reset Request</div>
                </div>
                
                <div class="content">
                    <div class="icon-container">
                        <div class="icon-circle" style="font-size: 32px;">🔑</div>
                    </div>
                    
                    <h1>Reset Your Password</h1>
                    
                    <p class="intro-text">
                        We received a request to reset the password for your ReportForge AI account.<br>
                        Click the button below to create a new password.
                    </p>
                    
                    <div class="button-container">
                        <a href="{reset_url}" class="button">Reset My Password</a>
                    </div>
                    
                    <div class="link-container">
                        <div class="link-label">Or copy this link:</div>
                        <div class="link-text">{reset_url}</div>
                    </div>
                    
                    <div class="warning-box">
                        <p><strong>Time Sensitive:</strong> This password reset link will expire in 1 hour.</p>
                        <p style="margin-top: 10px;">If you didn't request a password reset, please ignore this email. Your password will remain unchanged and your account is secure.</p>
                    </div>
                    
                    <div class="security-notice">
                        <p><strong>Security Tip:</strong> For your protection, never share this link with anyone. ReportForge AI will never ask for your password via email.</p>
                    </div>
                    
                    <div class="divider"></div>
                    
                    <p style="font-size: 14px; color: #64748b; text-align: center; line-height: 1.7;">
                        If you continue to have problems, please contact our support team for assistance.
                    </p>
                </div>
                
                <div class="footer">
                    <p class="footer-text">
                        <strong>ReportForge AI</strong><br>
                        Transform your documents into professional reports with AI<br>
                        <a href="{settings.FRONTEND_URL}">Visit our website</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_content = f"""
        Reset Your Password
        
        We received a request to reset your password for your ReportForge AI account.
        
        Reset your password by visiting:
        {reset_url}
        
        This link will expire in 1 hour.
        
        If you didn't request a password reset, please ignore this email. Your password will remain unchanged.
        
        For security reasons, never share this link with anyone.
        """
        
        return self.send_email(
            to_email=to_email,
            subject="Reset Your Password - ReportForge AI",
            html_content=html_content,
            text_content=text_content
        )


# Create global email service instance
# Wrap in try-except to prevent import errors from blocking the app
try:
    email_service = EmailService()
except Exception as e:
    logger.error(f"Failed to initialize email service: {e}")
    # Create a dummy service that does nothing
    class DummyEmailService:
        enabled = False
        def send_email(self, *args, **kwargs): return False
        def send_verification_email(self, *args, **kwargs): return False
        def send_password_reset_email(self, *args, **kwargs): return False
    email_service = DummyEmailService()

