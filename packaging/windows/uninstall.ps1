# Clean uninstall helper for NEXO Node (S13)
# No Windows Service was registered — only remove the install tree.

param(
    [Parameter(Mandatory = $true)]
    [string]$InstallRoot,
    [switch]$Execute
)

$ErrorActionPreference = "Stop"
Write-Host "Kill switch reminder: run NEXO-Node.exe stop before uninstall."

if (-not $Execute) {
    Write-Host "Dry-run only. Pass -Execute to delete: $InstallRoot"
    Get-ChildItem -Path $InstallRoot -Recurse -ErrorAction SilentlyContinue | Select-Object FullName
    exit 0
}

if (Test-Path $InstallRoot) {
    Remove-Item -LiteralPath $InstallRoot -Recurse -Force
    Write-Host "Removed $InstallRoot"
} else {
    Write-Host "Nothing to remove at $InstallRoot"
}

# S13: assert we never created these services
$Forbidden = @("NEXONode", "NEXO-Node", "nexo-node", "NexoLabService")
foreach ($name in $Forbidden) {
    $svc = Get-Service -Name $name -ErrorAction SilentlyContinue
    if ($svc) {
        Write-Error "Unexpected leftover service: $name"
        exit 1
    }
}
Write-Host "No leftover NEXO Windows services detected."
