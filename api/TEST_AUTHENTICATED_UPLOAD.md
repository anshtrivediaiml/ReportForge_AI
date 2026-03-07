# Testing Authenticated File Uploads

## Method 1: Using FastAPI Docs (Swagger UI) - EASIEST

### Step 1: Register a New User

1. Open your browser and go to: **http://localhost:8000/docs**
2. Find the **`POST /api/v1/auth/register`** endpoint
3. Click "Try it out"
4. Enter the following JSON in the request body:
```json
{
  "email": "test@example.com",
  "password": "TestPass123!",
  "full_name": "Test User"
}
```
5. Click "Execute"
6. **Copy the `access_token` from the response** - you'll need this!

### Step 2: Authorize in Swagger UI

**Method A: Login directly in Swagger (EASIEST)**
1. At the top of the Swagger UI page, click the **"Authorize"** button (lock icon)
2. In the authorization modal that appears:
   - **username**: Enter your email (e.g., `test@example.com`)
   - **password**: Enter your password (e.g., `TestPass123!`)
   - Leave `client_id` and `client_secret` empty
3. Click **"Authorize"** (green button)
4. Click **"Close"**
5. ✅ You're now authenticated! The lock icon should show as unlocked

**Method B: Use token from registration**
1. At the top of the Swagger UI page, click the **"Authorize"** button (lock icon)
2. In the authorization modal:
   - **username**: Enter your email
   - **password**: Enter your password
   - OR if you have a token, look for a "Value" field and paste your `access_token` (without "Bearer " prefix)
3. Click **"Authorize"**
4. Click **"Close"**

### Step 3: Upload File with Authentication

1. Find the **`POST /api/v1/upload/file`** endpoint
2. Click "Try it out"
3. Click "Choose File" and select your PDF or ZIP file
4. Click "Execute"
5. The file will now be saved to `inputs/user_{user_id}/` directory
6. Storage limits will be enforced!

---

## Method 2: Using cURL Commands

### Step 1: Register a User

```powershell
curl -X POST "http://localhost:8000/api/v1/auth/register" `
  -H "Content-Type: application/json" `
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "full_name": "Test User"
  }'
```

**Response will look like:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": { ... }
}
```

**Copy the `access_token` value!**

### Step 2: Upload File with Token

```powershell
# Replace YOUR_ACCESS_TOKEN with the token from Step 1
curl -X POST "http://localhost:8000/api/v1/upload/file" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" `
  -H "Content-Type: multipart/form-data" `
  -F "file=@Guidelines.pdf"
```

**Or using PowerShell's Invoke-RestMethod:**

```powershell
# Set your token
$token = "YOUR_ACCESS_TOKEN_HERE"

# Upload file
$filePath = "C:\path\to\your\Guidelines.pdf"
$headers = @{
    "Authorization" = "Bearer $token"
}

$formData = @{
    file = Get-Item -Path $filePath
}

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/upload/file" `
    -Method Post `
    -Headers $headers `
    -Form $formData
```

---

## Method 3: Using Postman or Insomnia

### Step 1: Register/Login

1. Create a new POST request to: `http://localhost:8000/api/v1/auth/register`
2. Body (JSON):
```json
{
  "email": "test@example.com",
  "password": "TestPass123!",
  "full_name": "Test User"
}
```
3. Send request and copy the `access_token`

### Step 2: Upload File

1. Create a new POST request to: `http://localhost:8000/api/v1/upload/file`
2. Go to **Headers** tab:
   - Add: `Authorization` = `Bearer YOUR_ACCESS_TOKEN`
3. Go to **Body** tab:
   - Select **form-data**
   - Add key: `file` (type: File)
   - Select your PDF or ZIP file
4. Send request

---

## Verify It's Working

### Check File Location

After uploading with authentication, check:

```powershell
# List files in user directory (replace USER_ID with your user ID from registration)
Get-ChildItem "api\inputs\user_1\*"  # Replace 1 with your user ID
```

### Check User Storage

You can check the user's storage usage by calling:

```powershell
curl -X GET "http://localhost:8000/api/v1/auth/me" `
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

This will show:
- `storage_used`: Current storage in bytes
- `reports_generated`: Number of reports created

---

## Quick Test Script

Save this as `test_auth_upload.ps1`:

```powershell
# Test Authenticated Upload Script

$baseUrl = "http://localhost:8000"
$email = "test@example.com"
$password = "TestPass123!"

# Step 1: Register
Write-Host "Registering user..." -ForegroundColor Yellow
$registerResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/register" `
    -Method Post `
    -ContentType "application/json" `
    -Body (@{
        email = $email
        password = $password
        full_name = "Test User"
    } | ConvertTo-Json)

$token = $registerResponse.access_token
Write-Host "Token received: $($token.Substring(0, 20))..." -ForegroundColor Green

# Step 2: Upload file
Write-Host "`nUploading file..." -ForegroundColor Yellow
$filePath = Read-Host "Enter path to PDF or ZIP file"

if (-not (Test-Path $filePath)) {
    Write-Host "File not found!" -ForegroundColor Red
    exit
}

$headers = @{
    "Authorization" = "Bearer $token"
}

$formData = @{
    file = Get-Item -Path $filePath
}

$uploadResponse = Invoke-RestMethod -Uri "$baseUrl/api/v1/upload/file" `
    -Method Post `
    -Headers $headers `
    -Form $formData

Write-Host "Upload successful!" -ForegroundColor Green
Write-Host "File ID: $($uploadResponse.data.file_id)" -ForegroundColor Cyan
Write-Host "File saved to: inputs/user_$($registerResponse.user.id)/" -ForegroundColor Cyan

# Step 3: Check user info
Write-Host "`nChecking user storage..." -ForegroundColor Yellow
$userInfo = Invoke-RestMethod -Uri "$baseUrl/api/v1/auth/me" `
    -Method Get `
    -Headers $headers

$storageGB = [math]::Round($userInfo.storage_used / 1GB, 2)
Write-Host "Storage used: $storageGB GB" -ForegroundColor Cyan
Write-Host "Reports generated: $($userInfo.reports_generated)" -ForegroundColor Cyan
```

Run it:
```powershell
.\test_auth_upload.ps1
```

---

## Expected Results

### Without Authentication:
- File saved to: `inputs/anonymous/`
- No storage limit checks
- No user association

### With Authentication:
- File saved to: `inputs/user_{user_id}/`
- Storage limit checked (5GB default)
- User's `storage_used` updated
- File associated with user account

---

## Troubleshooting

### "Could not validate credentials"
- Token expired (tokens expire after 30 minutes)
- Token format incorrect (must be `Bearer <token>`)
- Solution: Login again to get a new token

### "Storage limit exceeded"
- User has used all 5GB storage
- Solution: Delete old files or upgrade account

### "File must be PDF or ZIP format"
- File type validation failed
- Solution: Ensure file is a valid PDF or ZIP

---

**Need help?** Check the API docs at http://localhost:8000/docs

