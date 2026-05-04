param(
    [string]$Device = "chrome",
    [string]$BackendUrl = "http://localhost:5001"
)

$repoRoot = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $repoRoot "..\backend\.env"
$frontendDir = Resolve-Path (Join-Path $repoRoot ".")
$flutterCommand = (Get-Command flutter -ErrorAction SilentlyContinue).Source

if (-not $flutterCommand) {
    $puroFlutter = Join-Path $env:USERPROFILE ".puro\envs\stable\flutter\bin\flutter.bat"
    if (Test-Path $puroFlutter) {
        $flutterCommand = $puroFlutter
    }
}

if (-not $flutterCommand) {
    Write-Error "Flutter is not available on PATH and was not found in the Puro stable environment."
    exit 1
}

if (-not (Test-Path $envPath)) {
    Write-Error "Missing backend\.env at $envPath"
    exit 1
}

$envMap = @{}
Get-Content $envPath | ForEach-Object {
    $line = $_.Trim()
    if (-not $line -or $line.StartsWith("#")) {
        return
    }

    $parts = $line -split "=", 2
    if ($parts.Count -ne 2) {
        return
    }

    $key = $parts[0].Trim()
    $value = $parts[1].Trim()
    $envMap[$key] = $value
}

$supabaseUrl = $envMap["SUPABASE_URL"]
$supabaseAnonKey = $envMap["SUPABASE_ANON_KEY"]
$supabasePublishableKey = $envMap["SUPABASE_PUBLISHABLE_KEY"]
$frontendKey = if ($supabaseAnonKey) { $supabaseAnonKey } else { $supabasePublishableKey }

if (-not $supabaseUrl) {
    Write-Error "SUPABASE_URL is missing from backend\.env"
    exit 1
}

if (-not $frontendKey) {
    Write-Error "SUPABASE_ANON_KEY or SUPABASE_PUBLISHABLE_KEY is missing from backend\.env"
    exit 1
}

Push-Location $frontendDir
try {
    & $flutterCommand run -d $Device `
        --dart-define="SUPABASE_URL=$supabaseUrl" `
        --dart-define="SUPABASE_ANON_KEY=$frontendKey" `
        --dart-define="API_BASE_URL=$BackendUrl"
}
finally {
    Pop-Location
}
