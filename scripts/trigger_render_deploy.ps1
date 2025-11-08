param(
    [string]$ServiceId = 'srv-d3ltfm1r0fns73ea3qmg'
)

if (-not $env:RENDER_API_KEY) {
    Write-Error 'Define la variable de entorno RENDER_API_KEY antes de ejecutar. Ej: $env:RENDER_API_KEY = "<your_key>"'
    exit 1
}

$uri = "https://api.render.com/v1/services/$ServiceId/deploys"
Write-Host "Invocando deploy para servicio: $ServiceId"
try {
    $resp = Invoke-RestMethod -Method Post -Uri $uri -Headers @{ Authorization = "Bearer $env:RENDER_API_KEY" } -Body '{}' -ContentType 'application/json' -ErrorAction Stop
    Write-Host 'Deploy triggered:' ($resp | ConvertTo-Json -Depth 4)
} catch {
    Write-Error "Error al intentar crear deploy: $_"
    if ($_.Exception.Response) {
        $sr = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
        Write-Host 'Body:' $sr.ReadToEnd()
    }
    exit 1
}

# Opcional: devuelve la respuesta para que el usuario la vea
return $resp
