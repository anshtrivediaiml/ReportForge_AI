# Google OAuth Quick Setup

## 🚀 Quick Steps

### 1. Get Google OAuth Credentials

1. Go to: https://console.cloud.google.com/apis/credentials
2. Click **"Create Credentials"** > **"OAuth client ID"**
3. If prompted, configure OAuth consent screen:
   - Choose **"External"** (for testing)
   - Fill in app name: **"ReportForge AI"**
   - Add your email as test user
   - Save and continue

4. Create OAuth Client:
   - Application type: **"Web application"**
   - Name: **"ReportForge AI"**
   - **Authorized redirect URIs**: 
     ```
     http://localhost:8000/api/v1/auth/google/callback
     ```
   - Click **"Create"**
   - **Copy the Client ID and Client Secret**

### 2. Add to `.env` File

Create or edit `api/.env` file:

```env
# Google OAuth
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here

# Frontend URL
FRONTEND_URL=http://localhost:5173
```

### 3. Restart Backend

```bash
# Stop current server (Ctrl+C)
# Then restart
cd api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Test It!

1. Go to: `http://localhost:5173/login`
2. Click **"Sign in with Google"**
3. You should be redirected to Google login
4. After login, you'll be redirected back and logged in!

## ✅ That's It!

If you see errors, check:
- Credentials are in `.env` file
- Backend server restarted
- Redirect URI matches exactly: `http://localhost:8000/api/v1/auth/google/callback`

For detailed troubleshooting, see `docs/GOOGLE_OAUTH_SETUP.md`

