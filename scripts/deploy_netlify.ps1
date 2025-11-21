param(
  [string]$SiteId = $env:NETLIFY_SITE_ID,
  [string]$AuthToken = $env:NETLIFY_AUTH_TOKEN
)

if (-not $SiteId -or -not $AuthToken) {
  Write-Error "Please set NETLIFY_SITE_ID and NETLIFY_AUTH_TOKEN environment variables (or pass as parameters)."
  exit 1
}

Push-Location -Path (Split-Path -Path $PSScriptRoot -Parent)
Set-Location -Path "frontend"


# If user passed a Netlify URL as SiteId, extract site name (avoid reserved variable names)
if ($SiteId -and $SiteId -match '^https?://') {
  try { $u = [System.Uri]$SiteId; $uriHost = $u.Host } catch { $uriHost = $SiteId }
  $siteName = $uriHost -replace '\.netlify\.app$',''
  Write-Output "Detected Netlify URL; using site name '$siteName' (will resolve to site id via Netlify CLI)"
  try {
    $sitesJson = npx netlify sites:list --auth $AuthToken --json 2>$null
    $sites = $sitesJson | ConvertFrom-Json
    $match = $sites | Where-Object { $_.name -eq $siteName }
    if ($match) {
      $resolvedId = $match.id
      Write-Output "Found site id: $resolvedId for site name $siteName"
      $SiteId = $resolvedId
    } else {
      Write-Output "Could not resolve site name to an id via Netlify CLI; using site name as-is"
      $SiteId = $siteName
    }
  } catch {
    Write-Output "Unable to call Netlify CLI to resolve site id: $_. Proceeding with provided value."
    $SiteId = $siteName
  }
}

# Prevent installation of optional dependencies that may target another OS/CPU
$env:NPM_CONFIG_OPTIONAL = "false"
if (Test-Path package-lock.json) { npm ci --omit=optional } else { npm install --omit=optional }

# Ensure esbuild is available when needed, but do NOT install platform-specific @esbuild/* packages.
# Installing platform-specific @esbuild binaries can cause EBADPLATFORM on CI (Linux) if a Windows-only
# package is present in package-lock.json. The preinstall script now deletes package-lock.json on Linux,
# so a normal `npm install` will pull the correct platform binary.
try {
  if ($env:OS -like '*Windows*' -or $env:OS -eq 'Windows_NT') {
    Write-Output "On Windows: ensure generic 'esbuild' package is installed (no-save)..."
    npm install esbuild --no-save
  } else {
    Write-Output "Non-Windows environment detected: skipping explicit esbuild platform install."
  }
} catch {
  Write-Output "Warning: failed to ensure esbuild availability: $_"
}

npm run build

npx netlify deploy --dir=dist --prod --site $SiteId --auth $AuthToken

Pop-Location
