"""
OAuth Configuration for Google
"""
from authlib.integrations.starlette_client import OAuth
from app.config import settings
import httpx

# Initialize OAuth (no init_app needed for Starlette/FastAPI)
# OAuth clients are registered directly and work with request objects
oauth = OAuth()

# Google OAuth
if settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET:
    oauth.register(
        name='google',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    print(f"[OK] Google OAuth configured with Client ID: {settings.GOOGLE_CLIENT_ID[:20]}...")

# GitHub OAuth - Disabled (user preference)
# if settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET:
#     oauth.register(
#         name='github',
#         client_id=settings.GITHUB_CLIENT_ID,
#         client_secret=settings.GITHUB_CLIENT_SECRET,
#         access_token_url='https://github.com/login/oauth/access_token',
#         authorize_url='https://github.com/login/oauth/authorize',
#         api_base_url='https://api.github.com/',
#         client_kwargs={
#             'scope': 'user:email'
#         }
#     )


async def verify_google_email(email: str, access_token: str) -> bool:
    """
    Verify Google email is legitimate
    Calls Google API to verify email
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                'https://www.googleapis.com/oauth2/v1/userinfo',
                headers={'Authorization': f'Bearer {access_token}'}
            )
            if response.status_code == 200:
                data = response.json()
                return data.get('verified_email', False) and data.get('email') == email
    except Exception:
        pass
    return False

