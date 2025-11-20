param(
    [string]$SiteId = $env:NETLIFY_SITE_ID,
    [string]$Token = $env:NETLIFY_AUTH_TOKEN
)

if (-not $SiteId -or -not $Token) {
    Write-Error "Please set NETLIFY_SITE_ID and NETLIFY_AUTH_TOKEN environment variables (or pass as parameters)."
    exit 1
}

$dist = Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Definition) "..\frontend\dist"
$dist = (Get-Item $dist).FullName
Write-Output "Using dist folder: $dist"

# Collect files and compute SHA1
$files = Get-ChildItem -Path $dist -Recurse -File | ForEach-Object {
    $rel = $_.FullName.Substring($dist.Length + 1) -replace '\\','/'
    $sha = (Get-FileHash -Algorithm SHA1 -Path $_.FullName).Hash.ToLower()
    @{ path = $rel; sha = $sha; full = $_.FullName }
}

$filesMap = @{}
$shaToLocal = @{}
foreach ($f in $files) { $filesMap[$f.path] = $f.sha; $shaToLocal[$f.sha] = $f.full }

$body = @{ files = $filesMap } | ConvertTo-Json -Depth 12

Write-Output "Creating deploy... (this may take a moment)"
$deploy = Invoke-RestMethod -Method Post -Uri "https://api.netlify.com/api/v1/sites/$SiteId/deploys" -Headers @{ Authorization = "Bearer $Token"; 'Content-Type' = 'application/json' } -Body $body

$deploy | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 .\scripts\netlify_manual_deploy_response.json
Write-Output "Deploy created: id=$($deploy.id); state=$($deploy.state); deploy_state=$($deploy.deploy_state)"

# If there are files to upload, the API includes "required" array and "upload_url" attributes under "files" or provides upload_urls mapping.
# Inspect response to find upload urls.

# Newer Netlify responses include "required" (array of paths) and "files" map. The API may also return "upload_urls".

# Try to use deploy.upload_urls (map path->url) if present, else build upload urls using deploy.id

$uploadMap = @{}
if ($deploy.PSObject.Properties.Name -contains 'upload_urls') {
    $uploadMap = $deploy.upload_urls
} elseif ($deploy.PSObject.Properties.Name -contains 'files') {
    # files map may indicate existing files; find keys where value is null or missing?
    # In practice, Netlify returns 'required' list of paths to upload.
    if ($deploy.PSObject.Properties.Name -contains 'required') {
        foreach ($p in $deploy.required) { $uploadMap[$p] = ("https://api.netlify.com/api/v1/deploys/$($deploy.id)/files/$p") }
    }
}

if ($uploadMap.Count -eq 0 -and $deploy.PSObject.Properties.Name -contains 'required') {
    foreach ($p in $deploy.required) { $uploadMap[$p] = ("https://api.netlify.com/api/v1/deploys/$($deploy.id)/files/$p") }
}

if ($uploadMap.Count -eq 0) {
    Write-Output "No files to upload or upload URLs not provided. Final state: $($deploy.state) / $($deploy.deploy_state)"
} else {
    Write-Output "Uploading $($uploadMap.Count) files..."
    $i = 0
    foreach ($key in $uploadMap.Keys) {
        $i++
        $url = $uploadMap[$key]
        # Determine local file path: key may be a relative path or a sha
        $local = Join-Path $dist ($key -replace '/','\\')
        if (-Not (Test-Path $local)) {
            if ($shaToLocal.ContainsKey($key)) { $local = $shaToLocal[$key] }
            elseif ($key.Length -eq 40 -and $shaToLocal.ContainsKey($key.ToLower())) { $local = $shaToLocal[$key.ToLower()] }
        }
        if (-Not (Test-Path $local)) { Write-Output "Skipping missing $key (local file not found)"; continue }
        Write-Output "[$i/$($uploadMap.Count)] Uploading $key -> $url"
        # Use PUT with binary content
        try {
            Invoke-RestMethod -Uri $url -Method Put -InFile $local -Headers @{ Authorization = "Bearer $Token"; 'Content-Type' = 'application/octet-stream' }
        } catch {
            Write-Output ("Upload failed for {0}: {1}" -f $key, $_.Exception.Message)
            throw $_
        }
    }
    # After uploads, check deploy status
    Start-Sleep -Seconds 2
    $final = Invoke-RestMethod -Uri "https://api.netlify.com/api/v1/deploys/$($deploy.id)" -Headers @{ Authorization = "Bearer $Token" }
    $final | ConvertTo-Json -Depth 6 | Out-File -Encoding utf8 .\scripts\netlify_manual_deploy_final.json
    Write-Output "Upload complete. Deploy state: $($final.state) / $($final.deploy_state) ; url: $($final.deploy_url)"
}
