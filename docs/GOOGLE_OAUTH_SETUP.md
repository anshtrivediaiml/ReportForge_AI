# Google OAuth Setup Guide

This guide will help you set up Google OAuth authentication for ReportForge AI.

## Step 1: Create Google OAuth Credentials

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/
   - Sign in with your Google account

2. **Create a New Project** (or select existing)
   - Click on the project dropdown at the top
   - Click "New Project"
   - Enter project name: "ReportForge AI" (or any name)
   - Click "Create"

3. **Enable Google+ API**
   - Go to "APIs & Services" > "Library"
   - Search for "Google+ API" or "People API"
   - Click on it and click "Enable"

4. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "OAuth client ID"
   - If prompted, configure the OAuth consent screen first:
     - User Type: External (for testing) or Internal (for Google Workspace)
     - App name: "ReportForge AI"
     - User support email: Your email
     - Developer contact: Your email
     - Click "Save and Continue"
     - Scopes: Click "Add or Remove Scopes"
       - Select: `userinfo.email`, `userinfo.profile`, `openid`
     - Click "Save and Continue"
     - Test users: Add your email (for external apps in testing)
     - Click "Save and Continue"
     - Click "Back to Dashboard"

5. **Create OAuth Client ID**
   - Application type: "Web application"
   - Name: "ReportForge AI Web Client"
   - Authorized JavaScript origins:
     - `http://localhost:8000` (for development)
     - `http://localhost:5173` (for frontend dev server)
     - Add your production URLs when deploying
   - Authorized redirect URIs:
     - `http://localhost:8000/api/v1/auth/google/callback` (for development)
     - Add your production callback URL when deploying
   - Click "Create"
   - **IMPORTANT**: Copy the **Client ID** and **Client Secret** - you'll need these!

## Step 2: Configure Environment Variables

1. **Open your `.env` file** in the `api/` directory
   - If it doesn't exist, create it from `.env.example`

2. **Add Google OAuth credentials:**
   ```env
   GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-client-secret-here
   FRONTEND_URL=http://localhost:5173
   ```

3. **Example `.env` file:**
   ```env
   # Database
   DATABASE_URL=sqlite:///./reportforge.db
   
   # Redis
   REDIS_URL=redis://localhost:6379/0
   
   # JWT
   JWT_SECRET_KEY=your-secret-key-here
   SESSION_SECRET_KEY=your-session-secret-here
   
   # OAuth
   GOOGLE_CLIENT_ID=123456789-abcdefghijklmnop.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=GOCSPX-abcdefghijklmnopqrstuvwxyz
   
   # Frontend
   FRONTEND_URL=http://localhost:5173
   ```

## Step 3: Restart Your Backend Server

After adding the credentials, restart your FastAPI server:

```bash
# Stop the current server (Ctrl+C)
# Then restart it
cd api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Step 4: Test Google OAuth

1. **Start your frontend** (if not already running):
   ```bash
   cd web
   npm run dev
   ```

2. **Test the flow:**
   - Go to `http://localhost:5173/login`
   - Click "Sign in with Google"
   - You should be redirected to Google's login page
   - After logging in, you'll be redirected back to the app
   - You should be automatically logged in!

## Troubleshooting

### Error: "Google OAuth not configured"
- Make sure `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set in your `.env` file
- Restart the FastAPI server after adding credentials
- Check that the `.env` file is in the `api/` directory

### Error: "redirect_uri_mismatch"
- Make sure the redirect URI in Google Console matches exactly:
  - `http://localhost:8000/api/v1/auth/google/callback`
- Check for trailing slashes or typos
- The redirect URI must match exactly (case-sensitive)

### Error: "access_denied"
- If using "External" app type, make sure you added your email as a test user
- Check that the OAuth consent screen is configured
- Wait a few minutes after making changes in Google Console (propagation delay)

### Error: "invalid_client"
- Double-check your `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
- Make sure there are no extra spaces or quotes in the `.env` file
- Regenerate the client secret if needed

### OAuth works but user not created
- Check backend logs for errors
- Verify database connection
- Check that the email is verified by Google

## Production Deployment

When deploying to production:

1. **Update Google OAuth Credentials:**
   - Add production URLs to "Authorized JavaScript origins"
   - Add production callback URL: `https://yourdomain.com/api/v1/auth/google/callback`
   - Update `FRONTEND_URL` in your production `.env` file

2. **Security:**
   - Never commit `.env` file to version control
   - Use environment variables in your hosting platform
   - Keep your `GOOGLE_CLIENT_SECRET` secure

## Additional Resources

- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Authlib Documentation](https://docs.authlib.org/)

