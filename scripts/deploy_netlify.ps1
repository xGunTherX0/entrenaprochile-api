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

# Ensure esbuild platform binary is installed if omitted earlier
try {
  $arch = $env:PROCESSOR_ARCHITECTURE
  $os = $env:OS
  if ($os -like '*Windows*' -or $env:OS -eq 'Windows_NT') {
    if ($arch -match 'AMD64|x86_64') { $esbuildPkg = '@esbuild/win32-x64' }
    elseif ($arch -match 'ARM64') { $esbuildPkg = '@esbuild/win32-arm64' }
    else { $esbuildPkg = '@esbuild/win32-x64' }
  } else {
    if ($IsLinux) { $esbuildPkg = '@esbuild/linux-x64' }
    elseif ($IsMacOS) { $esbuildPkg = '@esbuild/darwin-x64' } else { $esbuildPkg = '@esbuild/linux-x64' }
  }
  Write-Output "Ensuring esbuild platform package $esbuildPkg is installed (no-save)..."
  npm install $esbuildPkg --no-save
} catch {
  Write-Output "Warning: failed to install esbuild platform binary: $_"
}

npm run build

npx netlify deploy --dir=dist --prod --site $SiteId --auth $AuthToken

Pop-Location
