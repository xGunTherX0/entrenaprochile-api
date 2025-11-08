param(
    [string]$BaseUrl = 'https://entrenaprochile-api.onrender.com',
    [int]$MaxAttempts = 30,
    [int]$DelaySeconds = 5
)

$i = 0
while ($i -lt $MaxAttempts) {
    try {
        $resp = Invoke-WebRequest -Uri "$BaseUrl/ping" -UseBasicParsing -TimeoutSec 5 -ErrorAction Stop
        $status = $resp.StatusCode
    } catch {
        $status = $null
    }
    Write-Host "Attempt $i - status=$status"
    if ($status -eq 200) { Write-Host 'API is healthy'; break }
    Start-Sleep -Seconds $DelaySeconds
    $i = $i + 1
}
if ($i -ge $MaxAttempts) { Write-Host 'Timeout waiting for API to become healthy'; exit 1 }
else { Write-Host 'Proceeding (API healthy)'; exit 0 }
