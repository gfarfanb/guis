# Build a standalone executable with PyInstaller.
#
#   pwsh -File scripts/build.ps1

$ErrorActionPreference = 'Stop'

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path $Python)) {
    $Python = 'python'
}

Write-Host '==> Running PyInstaller'
& $Python -m PyInstaller --noconfirm --clean mupen64plus_gui.spec

Write-Host ''
Write-Host "Build complete: $ProjectRoot\dist\mupen64plus_gui.exe"
