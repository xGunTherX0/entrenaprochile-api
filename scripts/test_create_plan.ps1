$token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoyLCJyb2xlIjoiYWRtaW4iLCJub21icmUiOiJBZG1pbmlzdHJhZG9yIiwiZXhwIjoxNzYyNjYxNzcwfQ.jlfh9NA4BNt-GkLyaYDu47uTHWlo2Lk83XJqMPCxR0M'
$body = @{ nombre='Plan automatizado'; descripcion='Prueba e2e'; ejercicios = @() } | ConvertTo-Json -Depth 5
try {
    $r = Invoke-RestMethod -Uri 'https://entrenaprochile-api.onrender.com/api/planes' -Method Post -Headers @{ Authorization = "Bearer $token"; 'Content-Type' = 'application/json' } -Body $body -UseBasicParsing -ErrorAction Stop
    $r | ConvertTo-Json -Depth 5 | Out-File -Encoding utf8 .\scripts\create_plan_test_response.json
    Write-Output 'Saved scripts\\create_plan_test_response.json'
} catch {
    Write-Output "Request failed: $_"
}
