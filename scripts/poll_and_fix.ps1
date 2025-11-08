# Poll until fix_schema_v2 exists then call it
Set-Location 'c:\Users\carlo\U\EntrenaProChile'
$ApiUrl = 'https://entrenaprochile-api.onrender.com'
Write-Host "Polling for $ApiUrl/api/admin/fix_schema_v2 to appear..."
$max = 40
$i = 0
while ($i -lt $max) {
    try {
        $r = Invoke-WebRequest -Uri ($ApiUrl + '/api/admin/fix_schema_v2') -Method Get -TimeoutSec 10
        Write-Host 'Endpoint returned HTTP ' $r.StatusCode
        break
    } catch {
        $ex = $_.Exception
        $code = $null
        if ($null -ne $ex.Response) {
            try { $code = $ex.Response.StatusCode.Value__ } catch { $code = 'unknown' }
        }
        Write-Host ('Attempt ' + $i + ': endpoint not ready (status ' + $code + ')')
        Start-Sleep -Seconds 6
        $i = $i + 1
    }
}
if ($i -ge $max) { Write-Host 'Timeout waiting for endpoint'; exit 1 }

Write-Host 'Logging in...'
$body = @{ email = 'admin@test.local'; password = 'admin123' } | ConvertTo-Json
$login = Invoke-RestMethod -Uri ($ApiUrl + '/api/usuarios/login') -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 30
$token = $login.token
Write-Host ('Login success. role=' + $login.role + ' user_id=' + $login.user_id)

Write-Host 'Calling fix_schema_v2 now...'
$headers = @{ Authorization = 'Bearer ' + $token }
try {
    $fix = Invoke-RestMethod -Uri ($ApiUrl + '/api/admin/fix_schema_v2') -Method Post -Headers $headers -ContentType 'application/json' -TimeoutSec 120
    Write-Host 'Result:'
    $fix | ConvertTo-Json -Depth 5
} catch {
    Write-Host 'fix_schema_v2 call failed:'
    Write-Host $_.Exception.Message
    exit 1
}

Write-Host 'Done.'
