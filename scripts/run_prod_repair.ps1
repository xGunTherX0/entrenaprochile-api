# Script para verificar y reparar producción (PowerShell)
# Uso: Ejecutar desde la raíz del repo en Windows PowerShell
# Requisitos: PowerShell, Node (para scripts/e2e.js), npm deps instalados

param(
    [string]$ApiUrl = 'https://entrenaprochile-api.onrender.com',
    [string]$AdminEmail = 'admin@test.local',
    [string]$AdminPassword = 'admin123'
)

Write-Host "API URL: $ApiUrl"

function Try-Invoke($scriptblock, $errmsg) {
    try {
        & $scriptblock
    } catch {
        Write-Host "ERROR: $errmsg" -ForegroundColor Red
        Write-Host $_.Exception.Message
        exit 1
    }
}

# 1) Ping /ping
Write-Host "==> Checking health: $ApiUrl/ping"
try {
    $ping = Invoke-RestMethod -Uri "$ApiUrl/ping" -Method Get -TimeoutSec 120
    Write-Host "Ping response:"; $ping
} catch {
    Write-Host "Failed to reach $ApiUrl/ping" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

# 2) API root
Write-Host "==> Checking API root: $ApiUrl/api"
try {
    $root = Invoke-RestMethod -Uri "$ApiUrl/api" -Method Get -TimeoutSec 120
    Write-Host "API root response:"; $root
} catch {
    Write-Host "Failed to reach $ApiUrl/api" -ForegroundColor Yellow
    Write-Host $_.Exception.Message
    # Not fatal, continue
}

# 3) Login to obtain JWT
Write-Host "==> Logging in as $AdminEmail"
$loginBody = @{ email = $AdminEmail; password = $AdminPassword } | ConvertTo-Json
try {
    $loginResp = Invoke-RestMethod -Uri "$ApiUrl/api/usuarios/login" -Method Post -Body $loginBody -ContentType 'application/json' -TimeoutSec 120
    Write-Host "Login success. role=$($loginResp.role) user_id=$($loginResp.user_id)"
    $global:Token = $loginResp.token
    if (-not $global:Token) { throw "no token returned" }
    Write-Host "Token (first 40 chars): $($global:Token.Substring(0,[Math]::Min(40,$global:Token.Length)))"
} catch {
    Write-Host "Login failed" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 1
}

# 4) Call /api/admin/fix_schema
Write-Host "==> Calling /api/admin/fix_schema"
try {
    $headers = @{ Authorization = "Bearer $global:Token" }
    $fix = Invoke-RestMethod -Uri "$ApiUrl/api/admin/fix_schema" -Method Post -Headers $headers -ContentType 'application/json' -TimeoutSec 300
    Write-Host "fix_schema response:"; $fix
} catch {
    Write-Host "fix_schema call failed" -ForegroundColor Red
    Write-Host $_.Exception.Message
    # Not exiting automatically — you may still want to run E2E, but we exit to be safe
    exit 1
}

# 5) Run Node E2E script (if exists)
$e2ePath = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Definition) '..\scripts\e2e.js' | Resolve-Path -Relative
$e2eFull = Join-Path (Get-Location) "scripts\e2e.js"
if (Test-Path $e2eFull) {
    Write-Host "==> Running Node E2E script: node scripts/e2e.js"
    # Export environment variables for the Node script
    $env:API_URL = $ApiUrl
    $env:ADMIN_EMAIL = $AdminEmail
    $env:ADMIN_PASSWORD = $AdminPassword
    # Run node and capture exit code
    $proc = Start-Process -FilePath node -ArgumentList ".\scripts\e2e.js" -NoNewWindow -Wait -PassThru
    if ($proc.ExitCode -eq 0) {
        Write-Host "E2E script finished successfully." -ForegroundColor Green
    } else {
        Write-Host "E2E script exited with code $($proc.ExitCode)" -ForegroundColor Yellow
    }
} else {
    Write-Host "No scripts/e2e.js found in repo. Skipping E2E run." -ForegroundColor Yellow
}

Write-Host "==> Done. Revisa la salida anterior para errores o resultados." -ForegroundColor Cyan
