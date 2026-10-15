# Create the local virtual environment and install every dependency.
#
#   pwsh -File scripts/setup_env.ps1

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$VenvDir = Join-Path $ProjectRoot '.venv'

if (-not (Test-Path $VenvDir)) {
    Write-Host '==> Creating virtual environment (.venv)'
    python -m venv $VenvDir
}

$Python = Join-Path $VenvDir 'Scripts\python.exe'

Write-Host '==> Upgrading pip'
& $Python -m pip install --upgrade pip

Write-Host '==> Installing dependencies (PySide6, PyInstaller)'
& $Python -m pip install -r requirements.txt

Write-Host ''
Write-Host 'Environment ready.'
Write-Host "  Activate : .\.venv\Scripts\Activate.ps1"
Write-Host "  Run      : python mupen64plus_gui.py"
Write-Host "  Build    : pyinstaller mupen64plus_gui.spec"
