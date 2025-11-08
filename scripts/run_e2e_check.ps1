# Run end-to-end checks against the deployed API
# Usage: Open PowerShell in the repo root and run:
#   .\scripts\run_e2e_check.ps1
# You can override API base and admin creds with environment variables:
#   $env:API_BASE = 'https://entrenaprochile-api.onrender.com'
#   $env:ADMIN_EMAIL, $env:ADMIN_PASSWORD

$ErrorActionPreference = 'Stop'
$API_BASE = $env:API_BASE -or 'https://entrenaprochile-api.onrender.com'
$ADMIN_EMAIL = $env:ADMIN_EMAIL -or 'admin@test.local'
$ADMIN_PASSWORD = $env:ADMIN_PASSWORD -or 'admin123'

Write-Host "Using API base: $API_BASE"

function PrettyPrint($name, $obj) {
    Write-Host "\n=== $name ==="
    if ($null -eq $obj) { Write-Host "<null>"; return }
    $json = $obj | ConvertTo-Json -Depth 5 -Compress
    $jsonFormatted = $json | ConvertFrom-Json | ConvertTo-Json -Depth 10
    Write-Host $jsonFormatted
}

try {
    Write-Host "Logging in as $ADMIN_EMAIL..."
    $loginBody = @{ email = $ADMIN_EMAIL; password = $ADMIN_PASSWORD } | ConvertTo-Json
    $loginResp = Invoke-RestMethod -Method Post -Uri "$API_BASE/api/usuarios/login" -Body $loginBody -ContentType 'application/json' -ErrorAction Stop
    PrettyPrint 'login response' $loginResp
    $token = $loginResp.token
    if (-not $token) { throw "No token returned from login" }

    $headers = @{ Authorization = "Bearer $token" }

    # Optional: call fix_schema_v2 to be safe
    Write-Host "Calling /api/admin/fix_schema_v2 (diagnostic/repair) ..."
    try {
        $fixResp = Invoke-RestMethod -Method Post -Uri "$API_BASE/api/admin/fix_schema_v2" -Headers $headers -ErrorAction Stop
        PrettyPrint 'fix_schema_v2 response' $fixResp
    } catch {
        Write-Host "fix_schema_v2 call failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }

    # Create medicion
    Write-Host "Creating medicion..."
    $medBody = @{ peso = 70; altura = 175; cintura = 80 } | ConvertTo-Json
    $medResp = Invoke-RestMethod -Method Post -Uri "$API_BASE/api/mediciones" -Headers $headers -Body $medBody -ContentType 'application/json' -ErrorAction Stop
    PrettyPrint 'create_medicion response' $medResp

    # Create rutina
    Write-Host "Creating rutina..."
    $rutinaBody = @{ nombre = "Rutina E2E"; descripcion = "Prueba E2E"; nivel = "intermedio"; es_publica = $true } | ConvertTo-Json
    try {
        $rutinaResp = Invoke-RestMethod -Method Post -Uri "$API_BASE/api/rutinas" -Headers $headers -Body $rutinaBody -ContentType 'application/json' -ErrorAction Stop
        PrettyPrint 'create_rutina response' $rutinaResp
        $rutinaId = $rutinaResp.rutina.id -or $rutinaResp.id
    } catch {
        Write-Host "create_rutina returned error: $($_.Exception.Message)" -ForegroundColor Red
        if ($null -ne $_.Exception.Response) {
            $respText = $_.Exception.Response.GetResponseStream() | New-Object System.IO.StreamReader | ForEach-Object { $_.ReadToEnd() }
            Write-Host "Response body:\n$respText" -ForegroundColor Red
        }
        throw
    }

    if ($rutinaId) {
        # List rutinas for the authenticated entrenador (we must know user_id). The token contains user_id but parsing JWT would need external tool.
        # Instead we will call /api/rutinas/<user_id> using the user_id returned at login.
        $userId = $loginResp.user_id
        if ($userId) {
            Write-Host "Listing rutinas for entrenador user_id=$userId ..."
            try {
                $listResp = Invoke-RestMethod -Method Get -Uri "$API_BASE/api/rutinas/$userId" -Headers $headers -ErrorAction Stop
                PrettyPrint 'listar_rutinas response' $listResp
            } catch {
                Write-Host "listar_rutinas failed: $($_.Exception.Message)" -ForegroundColor Yellow
                if ($null -ne $_.Exception.Response) {
                    $respText = $_.Exception.Response.GetResponseStream() | New-Object System.IO.StreamReader | ForEach-Object { $_.ReadToEnd() }
                    Write-Host "Response body:\n$respText"
                }
            }
        }

        # Delete the created rutina if API returned an id
        Write-Host "Deleting rutina id=$rutinaId ..."
        try {
            $delResp = Invoke-RestMethod -Method Delete -Uri "$API_BASE/api/rutinas/$rutinaId" -Headers $headers -ErrorAction Stop
            PrettyPrint 'delete_rutina response' $delResp
        } catch {
            Write-Host "delete_rutina failed: $($_.Exception.Message)" -ForegroundColor Yellow
            if ($null -ne $_.Exception.Response) {
                $respText = $_.Exception.Response.GetResponseStream() | New-Object System.IO.StreamReader | ForEach-Object { $_.ReadToEnd() }
                Write-Host "Response body:\n$respText"
            }
        }
    }

    Write-Host "E2E script completed successfully." -ForegroundColor Green
} catch {
    Write-Host "E2E script failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
