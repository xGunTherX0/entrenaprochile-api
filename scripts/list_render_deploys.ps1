$ServiceId = 'srv-d3ltfm1r0fns73ea3qmg'
$h = @{ Authorization = 'Bearer ' + $env:RENDER_API_KEY }
try {
    $r = Invoke-RestMethod -Uri ("https://api.render.com/v1/services/$ServiceId/deploys") -Headers $h -UseBasicParsing -ErrorAction Stop
    $r | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 .\scripts\render_deploys_list.json
    Write-Output "Saved .\\scripts\\render_deploys_list.json"
} catch {
    Write-Output "Failed to list deploys: $_"
}
