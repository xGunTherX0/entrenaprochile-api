$Url='https://entrenaprochile-api.onrender.com'
for ($i=0;$i -lt 40;$i++) {
    try {
        $r=Invoke-RestMethod -Uri "$Url/api" -UseBasicParsing -TimeoutSec 5
        if ($r.api -eq 'ok') { Write-Output "API ready"; break }
    } catch {
        Write-Output ("attempt {0}: not ready" -f $i)
    }
    Start-Sleep -Seconds 5
}

try {
    $login=Invoke-RestMethod -Method Post -Uri "$Url/api/usuarios/login" -Body (ConvertTo-Json @{email='admin@test.local';password='admin123'}) -ContentType 'application/json' -UseBasicParsing
    $token=$login.token
    Write-Output "GOT_TOKEN: $($token.Substring(0,20))..."
} catch {
    Write-Output 'login failed'
    $_ | Out-File .\scripts\create_plan_error_login.txt
    exit 0
}

$payload = @{ nombre='Plan desde script'; descripcion='Prueba via deploy'; contenido='Contenido de ejemplo'; es_publico=$true } | ConvertTo-Json
try {
    $res = Invoke-RestMethod -Method Post -Uri "$Url/api/planes" -Headers @{ Authorization = "Bearer $token" } -Body $payload -ContentType 'application/json' -UseBasicParsing
    $res | ConvertTo-Json -Depth 6 | Out-File .\scripts\create_plan_response.json -Encoding utf8
    Write-Output 'Created plan response saved to scripts/create_plan_response.json'
} catch {
    $_ | Out-File .\scripts\create_plan_error.txt
    Write-Output 'create plan error saved to scripts/create_plan_error.txt'
}