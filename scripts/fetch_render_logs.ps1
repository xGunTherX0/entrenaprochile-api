$sid = 'srv-d3ltfm1r0fns73ea3qmg'
$h = @{ Authorization = "Bearer $env:RENDER_API_KEY" }
try {
    $logs = Invoke-RestMethod -Uri "https://api.render.com/v1/services/$sid/logs" -Headers $h -UseBasicParsing -ErrorAction Stop
    $logs | ConvertTo-Json -Depth 6 | Out-File .\scripts\render_service_logs.json -Encoding utf8
    Write-Output "Saved render_service_logs.json"
} catch {
    Write-Output "Failed to fetch logs: $_"
}
