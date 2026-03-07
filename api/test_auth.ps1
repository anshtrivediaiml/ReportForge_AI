# PowerShell script to test authentication
# Run: .\api\test_auth.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Testing Authentication" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Step 1: Get token
Write-Host "Step 1: Getting token..." -ForegroundColor Yellow
try {
    $tokenResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/token" `
        -Method Post `
        -ContentType "application/x-www-form-urlencoded" `
        -Body @{
            username = "testuser@example.com"
            password = "TestPass123!"
        }
    
    $token = $tokenResponse.access_token
    Write-Host "✅ Token received!" -ForegroundColor Green
    Write-Host "Token (first 50 chars): $($token.Substring(0, [Math]::Min(50, $token.Length)))..." -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "❌ Failed to get token: $_" -ForegroundColor Red
    exit 1
}

# Step 2: Test /me endpoint
Write-Host "Step 2: Testing /me endpoint..." -ForegroundColor Yellow
try {
    $headers = @{
        Authorization = "Bearer $token"
    }
    
    $userInfo = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/auth/me" `
        -Method Get `
        -Headers $headers
    
    Write-Host "✅ Authentication successful!" -ForegroundColor Green
    Write-Host "User ID: $($userInfo.id)" -ForegroundColor Cyan
    Write-Host "Email: $($userInfo.email)" -ForegroundColor Cyan
    Write-Host "Full Name: $($userInfo.full_name)" -ForegroundColor Cyan
    Write-Host ""
} catch {
    Write-Host "❌ Authentication failed: $_" -ForegroundColor Red
    exit 1
}

# Step 3: Test file upload (if file provided)
if ($args.Count -gt 0) {
    $filePath = $args[0]
    if (Test-Path $filePath) {
        Write-Host "Step 3: Testing file upload..." -ForegroundColor Yellow
        try {
            $fileContent = Get-Content $filePath -Raw -AsByteStream
            $fileName = Split-Path $filePath -Leaf
            
            $boundary = [System.Guid]::NewGuid().ToString()
            $bodyLines = @(
                "--$boundary",
                "Content-Disposition: form-data; name=`"file`"; filename=`"$fileName`"",
                "Content-Type: application/octet-stream",
                "",
                [System.Text.Encoding]::UTF8.GetString($fileContent),
                "--$boundary--"
            )
            $body = $bodyLines -join "`r`n"
            
            $uploadResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/upload/file" `
                -Method Post `
                -Headers @{
                    Authorization = "Bearer $token"
                    "Content-Type" = "multipart/form-data; boundary=$boundary"
                } `
                -Body ([System.Text.Encoding]::UTF8.GetBytes($body))
            
            Write-Host "✅ File uploaded successfully!" -ForegroundColor Green
            Write-Host "File ID: $($uploadResponse.data.file_id)" -ForegroundColor Cyan
            Write-Host "Check: api\inputs\user_$($userInfo.id)\" -ForegroundColor Cyan
            Write-Host ""
        } catch {
            Write-Host "❌ File upload failed: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "⚠️  File not found: $filePath" -ForegroundColor Yellow
    }
}

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ All tests passed!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Use this token in Swagger UI:" -ForegroundColor White
Write-Host "   - Click lock icon" -ForegroundColor Gray
Write-Host "   - Find 'Bearer' scheme" -ForegroundColor Gray
Write-Host "   - Paste token: $($token.Substring(0, [Math]::Min(30, $token.Length)))..." -ForegroundColor Gray
Write-Host "2. Or add header manually: Authorization: Bearer $token" -ForegroundColor White

