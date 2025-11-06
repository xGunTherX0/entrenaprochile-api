# PowerShell helper to check deployed backend health and login
param(
    [string]$BaseUrl = 'https://entrenaprochile-api.onrender.com',
    [string]$LoginEmail = 'admin@test.local',
    [string]$LoginPass = 'admin123'
)

Write-Output "Checking base URL: $BaseUrl/"
try {
    $r = Invoke-WebRequest -Uri "$BaseUrl/" -Method Get -ErrorAction Stop
    Write-Output "--- ROOT OK ---"
    Write-Output "Status: $($r.StatusCode)"
    Write-Output "Body:"
    Write-Output $r.Content
} catch {
    Write-Output "--- ROOT ERROR ---"
    if ($_.Exception.Response) {
        $resp = $_.Exception.Response
        $sr = New-Object System.IO.StreamReader($resp.GetResponseStream())
        $content = $sr.ReadToEnd()
        Write-Output "Status: $($resp.StatusCode)"
        Write-Output "Body:`n$content"
    } else { Write-Output "ERROR: $($_.Exception.Message)" }
}

Write-Output "`nChecking API root: $BaseUrl/api"
try {
    $r = Invoke-WebRequest -Uri "$BaseUrl/api" -Method Get -ErrorAction Stop
    Write-Output "--- /api OK ---"
    Write-Output "Status: $($r.StatusCode)"
    Write-Output "Body:"
    Write-Output $r.Content
} catch {
    Write-Output "--- /api ERROR ---"
    if ($_.Exception.Response) {
        $resp = $_.Exception.Response
        $sr = New-Object System.IO.StreamReader($resp.GetResponseStream())
        $content = $sr.ReadToEnd()
        Write-Output "Status: $($resp.StatusCode)"
        Write-Output "Body:`n$content"
    } else { Write-Output "ERROR: $($_.Exception.Message)" }
}

Write-Output "`nTrying login POST to /api/usuarios/login"
$body = @{ email = $LoginEmail; password = $LoginPass } | ConvertTo-Json
try {
    $res = Invoke-RestMethod -Uri "$BaseUrl/api/usuarios/login" -Method Post -Body $body -ContentType 'application/json' -ErrorAction Stop
    Write-Output "--- LOGIN OK ---"
    $res | ConvertTo-Json -Depth 5
} catch {
    Write-Output "--- LOGIN ERROR ---"
    if ($_.Exception.Response) {
        $resp = $_.Exception.Response
        $sr = New-Object System.IO.StreamReader($resp.GetResponseStream())
        $content = $sr.ReadToEnd()
        Write-Output "Status: $($resp.StatusCode)"
        Write-Output "Body:`n$content"
    } else { Write-Output "ERROR: $($_.Exception.Message)" }
}

Write-Output "`nDone. Copy the entire output and paste it in the chat so I can analyze results."
