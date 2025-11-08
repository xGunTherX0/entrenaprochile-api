# Remote fix + E2E runner (PowerShell)
# Usage: powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_remote_fix_and_e2e.ps1

Set-Location 'c:\Users\carlo\U\EntrenaProChile'
Write-Host 'Checking git status...'
$changes = git status --porcelain
if ($changes) {
    Write-Host 'Changes detected, committing...'
    git add backend/app.py
    git commit -m 'feat(admin): add fix_schema_v2 endpoint'
    git push origin master
} else {
    Write-Host 'No changes to commit'
}

$ApiUrl = 'https://entrenaprochile-api.onrender.com'
Write-Host "Waiting for API to be reachable at $ApiUrl"
$max = 30
$i = 0
while ($i -lt $max) {
    try {
        $r = Invoke-RestMethod -Uri ($ApiUrl + '/api') -Method Get -TimeoutSec 30
        Write-Host 'API reachable'
        break
    } catch {
        Write-Host ('Attempt ' + $i + ': API not yet reachable: ' + $_.Exception.Message)
        Start-Sleep -Seconds 6
        $i = $i + 1
    }
}
if ($i -ge $max) { Write-Host 'API did not become reachable in time'; exit 1 }

Write-Host 'Logging in as admin...'
$body = @{ email = 'admin@test.local'; password = 'admin123' } | ConvertTo-Json
$login = Invoke-RestMethod -Uri ($ApiUrl + '/api/usuarios/login') -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 30
Write-Host ('Login success. role=' + $login.role + ' user_id=' + $login.user_id)
$token = $login.token

Write-Host 'Calling fix_schema_v2...'
$headers = @{ Authorization = "Bearer $token" }
try {
    $fix = Invoke-RestMethod -Uri ($ApiUrl + '/api/admin/fix_schema_v2') -Method Post -Headers $headers -ContentType 'application/json' -TimeoutSec 120
    Write-Host 'fix_schema_v2 response:'
    $fix | ConvertTo-Json -Depth 5
} catch {
    Write-Host 'fix_schema_v2 call failed:'
    Write-Host $_.Exception.Message
    exit 1
}

Write-Host 'Running E2E (node scripts/e2e.js) if present...'
if (Test-Path '.\scripts\e2e.js') {
    $env:API_URL = $ApiUrl
    $env:ADMIN_EMAIL = 'admin@test.local'
    $env:ADMIN_PASSWORD = 'admin123'
    node .\scripts\e2e.js
} else {
    Write-Host 'E2E script not found. Skipping.'
}

Write-Host 'Done.'
