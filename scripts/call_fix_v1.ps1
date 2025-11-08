$base='https://entrenaprochile-api.onrender.com'
try {
    Write-Host "Logging in..."
    $login = Invoke-RestMethod -Method Post -Uri "$base/api/usuarios/login" -Body (ConvertTo-Json @{email='admin@test.local'; password='admin123'}) -ContentType 'application/json' -ErrorAction Stop
    $token = $login.token
    Write-Host "Login OK, token len=$($token.Length)"

    Write-Host "Posting fix_schema (v1)..."
    $response = Invoke-WebRequest -Method Post -Uri "$base/api/admin/fix_schema" -Headers @{ Authorization = "Bearer $token" } -Body '{}' -ContentType 'application/json' -UseBasicParsing -ErrorAction Stop

    Write-Host "Status: $($response.StatusCode)"
    Write-Host "Response:`n$($response.Content)"
} catch {
    Write-Host "ERROR"
    if ($null -ne $_.Exception.Response) {
        $r = $_.Exception.Response
        try {
            $sr = New-Object System.IO.StreamReader($r.GetResponseStream())
            $body = $sr.ReadToEnd()
            Write-Host "Status from server: $($r.StatusCode)"
            Write-Host "Body:`n$body"
        } catch {
            Write-Host "Could not read response body: $($_.Exception.Message)"
        }
    } else {
        Write-Host $_.Exception.Message
    }
}
