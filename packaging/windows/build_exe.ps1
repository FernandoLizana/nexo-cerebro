# Build NEXO-Node.exe (S13)
# Requires: pip install pyinstaller
# Does NOT enable silent install. Signing is manual for release.

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..\..")
Set-Location $Root

Write-Host "NEXO Windows build — consent-first packaging"
Write-Host "Silent install flags are rejected by nexo-winpack / entrypoint."

python -m PyInstaller --noconfirm --clean "packaging\windows\nexo_node.spec"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Artifact: dist\NEXO-Node.exe"
Write-Host "Next: copy consent.json beside the EXE via nexo-winpack accept-consent"
Write-Host "Release signing: signtool sign /fd SHA256 /tr <timestamp> /td SHA256 dist\NEXO-Node.exe"
Write-Host "Kill switch: NEXO-Node.exe stop"
