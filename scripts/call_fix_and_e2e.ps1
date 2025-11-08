# Call fix_schema_v2 then run E2E
Set-Location 'c:\Users\carlo\U\EntrenaProChile'
$ApiUrl = 'https://entrenaprochile-api.onrender.com'

Write-Host 'Logging in as admin...'
$body = @{ email = 'admin@test.local'; password = 'admin123' } | ConvertTo-Json
try {
    $login = Invoke-RestMethod -Uri ($ApiUrl + '/api/usuarios/login') -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 30
} catch {
    Write-Host 'Login failed:'
    Write-Host $_.Exception.Message
    exit 1
}

Write-Host ('Login success. role=' + $login.role + ' user_id=' + $login.user_id)
$token = $login.token
$headers = @{ Authorization = 'Bearer ' + $token }

Write-Host 'Calling /api/admin/fix_schema_v2 (POST) ...'
try {
    $fix = Invoke-RestMethod -Uri ($ApiUrl + '/api/admin/fix_schema_v2') -Method Post -Headers $headers -ContentType 'application/json' -TimeoutSec 300
    Write-Host 'fix_schema_v2 response:'
    $fix | ConvertTo-Json -Depth 5
} catch {
    Write-Host 'fix_schema_v2 call failed:'
    Write-Host $_.Exception.Message
    exit 1
}

if (Test-Path '.\scripts\e2e.js') {
    Write-Host 'Running E2E script...'
    $env:API_URL = $ApiUrl
    $env:ADMIN_EMAIL = 'admin@test.local'
    $env:ADMIN_PASSWORD = 'admin123'
    try {
        node .\scripts\e2e.js
    } catch {
        Write-Host 'E2E script failed to run:'
        Write-Host $_.Exception.Message
        exit 1
    }
} else {
    Write-Host 'No e2e script found; skipping.'
}

Write-Host 'Completed.'
