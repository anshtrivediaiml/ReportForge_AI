# Complete Authentication Guide - Step by Step

## 🎯 Goal
Get authentication working in Swagger UI and save files to user-specific directories.

---

## Step 1: Create a Fresh Test User

Run this command to create a new test user:

```powershell
python api/create_test_user.py
```

This will create:
- **Email:** `testuser@example.com`
- **Password:** `TestPass123!`
- **User ID:** (will be shown)

---

## Step 2: Start Your Server

Make sure your FastAPI server is running:

```powershell
cd api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## Step 3: Test Token Endpoint Directly

### Method A: Using Swagger UI (Recommended)

1. **Open Swagger UI:** `http://localhost:8000/docs`

2. **Find the endpoint:** `POST /api/v1/auth/token`

3. **Click "Try it out"**

4. **Enter credentials:**
   - `username`: `testuser@example.com`
   - `password`: `TestPass123!`

5. **Click "Execute"**

6. **Check the response:**
   ```json
   {
     "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
     "token_type": "bearer"
   }
   ```

7. **Copy the `access_token` value** - you'll need this!

---

## Step 4: Authorize in Swagger UI

Since the lock icon method isn't working, use **Manual Token Entry**:

### Option 1: Use Bearer Token (Works 100%)

1. **In Swagger UI**, find any endpoint that needs auth (e.g., `GET /api/v1/auth/me`)

2. **Click "Try it out"**

3. **Look for "Authorize" button** or **"Bearer" section**

4. **If you see a "Bearer" field:**
   - Paste your token (without "Bearer " prefix)
   - Click "Authorize"

5. **If you don't see a Bearer field:**
   - Click the **lock icon** at the top
   - Look for **"Bearer"** scheme (not OAuth2PasswordBearer)
   - Paste your token
   - Click "Authorize"

### Option 2: Add Authorization Header Manually

1. **In Swagger UI**, expand any endpoint

2. **Look for "Parameters" or "Headers" section**

3. **Add a header:**
   - Name: `Authorization`
   - Value: `Bearer <your_token_here>`
   - (Replace `<your_token_here>` with the actual token)

---

## Step 5: Test Authentication

1. **Go to:** `GET /api/v1/auth/me`

2. **Click "Try it out"**

3. **Make sure you've authorized** (see Step 4)

4. **Click "Execute"**

5. **You should see:**
   ```json
   {
     "id": 1,
     "email": "testuser@example.com",
     "username": null,
     "full_name": "Test User",
     ...
   }
   ```

✅ **If you see your user info, authentication is working!**

---

## Step 6: Upload File with Authentication

1. **Go to:** `POST /api/v1/upload/file`

2. **Click "Try it out"**

3. **Make sure you're authorized** (token is set)

4. **Choose a file** (PDF or ZIP)

5. **Click "Execute"**

6. **Check the server console** - you should see:
   ```
   DEBUG: Authenticated as user 1
   ```

7. **Check the file location:**
   - File should be in: `inputs/user_1/` (not `inputs/anonymous/`)

---

## Step 7: Verify File Location

Check where your file was saved:

```powershell
# Check if file is in user directory
dir api\inputs\user_1\

# Or check anonymous directory (should be empty if auth worked)
dir api\inputs\anonymous\
```

---

## Troubleshooting

### ❌ "Not authenticated" error

**Solution:**
1. Get a fresh token from `/api/v1/auth/token`
2. Make sure you're pasting the FULL token
3. Don't include "Bearer " prefix when pasting in Swagger UI

### ❌ File still going to `anonymous/` directory

**Solution:**
1. Check server console for "DEBUG: Authenticated as user X"
2. If you see "DEBUG: No user authenticated", the token isn't being sent
3. Try adding Authorization header manually (see Step 4, Option 2)

### ❌ Token expired

**Solution:**
1. Get a new token from `/api/v1/auth/token`
2. Tokens expire after 24 hours (default)

### ❌ Lock icon still locked

**Solution:**
- **Don't worry about the lock icon!**
- Use manual token entry (Step 4)
- The lock icon is a Swagger UI bug, but manual auth works perfectly

---

## Quick Test Script

Save this as `test_auth.ps1`:

```powershell
# Get token
$response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/token" `
    -Method Post `
    -ContentType "application/x-www-form-urlencoded" `
    -Body @{
        username = "testuser@example.com"
        password = "TestPass123!"
    }

$token = $response.access_token
Write-Host "Token: $token"

# Test /me endpoint
$headers = @{
    Authorization = "Bearer $token"
}

$userInfo = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/me" `
    -Method Get `
    -Headers $headers

Write-Host "User Info:"
$userInfo | ConvertTo-Json
```

Run it:
```powershell
.\test_auth.ps1
```

---

## Summary

1. ✅ Create test user: `python api/create_test_user.py`
2. ✅ Get token from `/api/v1/auth/token`
3. ✅ Authorize manually in Swagger UI (Bearer token)
4. ✅ Test with `/api/v1/auth/me`
5. ✅ Upload file - should go to `user_1/` directory

**The key is: Don't rely on the lock icon. Use manual token entry!**

