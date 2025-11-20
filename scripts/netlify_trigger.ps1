if (-not $env:NETLIFY_AUTH_TOKEN) {
    Write-Error "NETLIFY_AUTH_TOKEN environment variable not set. Set it in your shell or in CI secrets before running this script."
    exit 1
}

Try {
    $sites = Invoke-RestMethod -Uri 'https://api.netlify.com/api/v1/sites' -Headers @{ Authorization = "Bearer $env:NETLIFY_AUTH_TOKEN" }
    $sites | Select-Object name,id,ssl_url | ConvertTo-Json -Depth 4 | Out-File -Encoding utf8 .\scripts\netlify_sites.json
    $match = $sites | Where-Object { $_.name -like '*entrenapro*' -or ($_.ssl_url -like '*entrenapro*') } | Select-Object -First 1
    if ($match) {
        Write-Output "FOUND_SITE: $($match.name) -> $($match.id)"
        $resp = Invoke-RestMethod -Method Post -Uri "https://api.netlify.com/api/v1/sites/$($match.id)/builds" -Headers @{ Authorization = "Bearer $env:NETLIFY_AUTH_TOKEN" } -Body '{}' -ContentType 'application/json'
        $resp | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 .\scripts\netlify_build_response.json
        Write-Output "Build triggered: $($resp.id)"
    }
    else {
        Write-Output "NO_SITE_MATCHED - saved list to scripts\netlify_sites.json"
    }
} Catch {
    Write-Error "Netlify API call failed: $_"
}
