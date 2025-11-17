param(
  [string]$NetlifySiteId = $env:NETLIFY_SITE_ID,
  [string]$NetlifyAuthToken = $env:NETLIFY_AUTH_TOKEN,
  [string]$RenderServiceId = $env:RENDER_SERVICE_ID,
  [string]$RenderApiKey = $env:RENDER_API_KEY,
  [string]$ViteApiBase = $env:VITE_API_BASE
)

function Abort($msg) {
  Write-Error $msg
  exit 1
}

$missing = @()
if (-not $NetlifySiteId) { $missing += 'NETLIFY_SITE_ID' }
if (-not $NetlifyAuthToken) { $missing += 'NETLIFY_AUTH_TOKEN' }
if (-not $RenderServiceId) { $missing += 'RENDER_SERVICE_ID' }
if (-not $RenderApiKey) { $missing += 'RENDER_API_KEY' }

if ($missing.Count -gt 0) {
  Abort "Missing required environment variables: $($missing -join ', ').\nSet them in your session or pass as parameters to the script."
}

Write-Output "Starting combined deploy: frontend -> Netlify, backend -> Render"

# Ensure we run from repository root
Set-Location -Path (Split-Path -Path $PSScriptRoot -Parent)

# If user provided a Netlify URL instead of site id, convert to site name
if ($NetlifySiteId -and $NetlifySiteId -match '^https?://') {
  try {
    $u = [System.Uri]$NetlifySiteId
    $uriHost = $u.Host
  } catch {
    $uriHost = $NetlifySiteId
  }
  $siteName = $uriHost -replace '\.netlify\.app$',''
  Write-Output "Detected Netlify URL; using site name '$siteName' (will resolve to site id via Netlify CLI)"
  # Try to resolve site name to site id (GUID) via Netlify CLI
  try {
    $sitesJson = npx netlify sites:list --auth $NetlifyAuthToken --json 2>$null
    $sites = $sitesJson | ConvertFrom-Json
    $match = $sites | Where-Object { $_.name -eq $siteName }
    if ($match) {
      $resolvedId = $match.id
      Write-Output "Found site id: $resolvedId for site name $siteName"
      $NetlifySiteId = $resolvedId
    } else {
      Write-Output "Could not resolve site name to an id via Netlify CLI; using site name as-is"
      $NetlifySiteId = $siteName
    }
  } catch {
    Write-Output "Unable to call Netlify CLI to resolve site id: $_. Proceeding with provided value."
    $NetlifySiteId = $siteName
  }
}

try {
  Write-Output "Building frontend..."
  Push-Location -Path "frontend"
  # Prevent installation of optional dependencies that may target another OS/CPU
  $env:NPM_CONFIG_OPTIONAL = "false"
  if (Test-Path package-lock.json) {
    npm ci --omit=optional
  } else {
    npm install --omit=optional
  }

  # Ensure esbuild platform binary is installed (some optional deps were omitted)
  try {
    $arch = $env:PROCESSOR_ARCHITECTURE
    $os = $env:OS
    if ($os -like '*Windows*' -or $env:OS -eq 'Windows_NT') {
      if ($arch -match 'AMD64|x86_64') { $esbuildPkg = '@esbuild/win32-x64' }
      elseif ($arch -match 'ARM64') { $esbuildPkg = '@esbuild/win32-arm64' }
      else { $esbuildPkg = '@esbuild/win32-x64' }
    } else {
      # Fallback to linux x64/darwin depending on platform
      if ($IsLinux) { $esbuildPkg = '@esbuild/linux-x64' }
      elseif ($IsMacOS) { $esbuildPkg = '@esbuild/darwin-x64' } else { $esbuildPkg = '@esbuild/linux-x64' }
    }
    Write-Output "Ensuring esbuild platform package $esbuildPkg is installed (no-save)..."
    npm install $esbuildPkg --no-save
  } catch {
    Write-Output "Warning: failed to install esbuild platform binary: $_" 
  }

  if ($ViteApiBase) {
    Write-Output "Writing VITE_API_BASE to frontend/.env"
    "VITE_API_BASE=$ViteApiBase" | Out-File -Encoding UTF8 -FilePath .env
  }

  npm run build
  if ($LASTEXITCODE -ne 0) { Abort "Frontend build failed (npm run build returned $LASTEXITCODE)" }

  Write-Output "Deploying frontend to Netlify (site: $NetlifySiteId)..."
  # Use npx so global install is not required
  npx netlify deploy --dir=dist --prod --site $NetlifySiteId --auth $NetlifyAuthToken
  if ($LASTEXITCODE -ne 0) { Abort "Netlify deploy failed (exit code $LASTEXITCODE)" }
  Pop-Location

  Write-Output "Triggering backend deploy on Render (service: $RenderServiceId)..."
  $uri = "https://api.render.com/v1/services/$RenderServiceId/deploys"
  $headers = @{ Authorization = "Bearer $RenderApiKey"; "Content-Type" = "application/json" }
  $resp = Invoke-RestMethod -Method Post -Uri $uri -Headers $headers -Body '{}' -ErrorAction Stop
  Write-Output "Render response: $(ConvertTo-Json $resp -Depth 2)"

  Write-Output "Combined deploy finished successfully. Check Netlify and Render dashboards for progress/details."
} catch {
  Write-Error "Error during deploy: $_"
  exit 1
}
