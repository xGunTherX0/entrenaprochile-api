param(
    [string]$DeployId = 'dep-d48239hr0fns73fp43n0'
)
$h = @{ Authorization = 'Bearer ' + $env:RENDER_API_KEY }
try {
    $r = Invoke-RestMethod -Uri ("https://api.render.com/v1/deploys/$DeployId") -Headers $h -UseBasicParsing -ErrorAction Stop
    $r | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 .\scripts\render_deploy_status.json
    Write-Output "Saved .\\scripts\\render_deploy_status.json"
} catch {
    Write-Output "Failed to fetch deploy: $_"
}
