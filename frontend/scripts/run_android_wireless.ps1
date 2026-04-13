param(
  [Parameter(Mandatory = $true)]
  [string]$BackendIp,

  [string]$DeviceId,

  [int]$Port = 5001
)

$ErrorActionPreference = "Stop"

$appRoot = Split-Path -Parent $PSScriptRoot
$apiBaseUrl = "http://${BackendIp}:$Port"

Write-Host "Starting Flutter app with API_BASE_URL=$apiBaseUrl"
Set-Location $appRoot

$flutterArgs = @(
  "run"
  "--dart-define=API_BASE_URL=$apiBaseUrl"
)

if ($DeviceId) {
  $flutterArgs += @("-d", $DeviceId)
}

& flutter @flutterArgs
