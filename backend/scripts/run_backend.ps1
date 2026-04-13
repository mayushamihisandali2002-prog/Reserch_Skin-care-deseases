$ErrorActionPreference = "Stop"

$backendDir = Split-Path -Parent $PSScriptRoot
$repoRoot = Split-Path -Parent $backendDir
$venvPython = Join-Path $repoRoot ".venv\Scripts\python.exe"

if (Test-Path $venvPython) {
  $python = $venvPython
} else {
  $python = "python"
}

Write-Host "Using Python:" $python
$env:PORT = "5001"
Write-Host "Backend port:" $env:PORT

# Ensure timm exists in the same interpreter used to run the backend.
& $python -c "import timm" *> $null
if ($LASTEXITCODE -ne 0) {
  Write-Host "Installing timm into backend runtime..."
  & $python -m pip install --disable-pip-version-check timm
}

Set-Location $backendDir
& $python (Join-Path $backendDir "app.py")
