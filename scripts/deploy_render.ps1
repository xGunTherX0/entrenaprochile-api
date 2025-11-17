param(
  [string]$ServiceId = $env:RENDER_SERVICE_ID,
  [string]$ApiKey = $env:RENDER_API_KEY
)

if (-not $ServiceId -or -not $ApiKey) {
  Write-Error "Please set RENDER_SERVICE_ID and RENDER_API_KEY environment variables (or pass as parameters)."
  exit 1
}

$uri = "https://api.render.com/v1/services/$ServiceId/deploys"
$body = "{}"
$headers = @{ Authorization = "Bearer $ApiKey"; "Content-Type" = "application/json" }

Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body $body
Write-Output "Triggered deploy for service $ServiceId. Check Render dashboard."
