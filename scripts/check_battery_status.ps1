# Monitoreo de batería E1–E8 en curso
$root = Join-Path (Split-Path $PSScriptRoot -Parent) "experiments\results\battery_10k_gpu"
if (-not (Test-Path $root)) {
    $root = Join-Path (Split-Path $PSScriptRoot -Parent) "experiments\results\battery_10k_full"
}
Write-Host "Directorio: $root" -ForegroundColor Cyan
if (Test-Path $root) {
    Get-ChildItem $root -Filter "*.csv" | Sort-Object LastWriteTime -Descending | Select-Object -First 12 Name, LastWriteTime, Length
    $report = Join-Path $root "battery_full_report.json"
    if (Test-Path $report) {
        Write-Host "`nReporte final:" -ForegroundColor Green
        Get-Content $report -Raw | ConvertFrom-Json | ConvertTo-Json -Depth 4
    } else {
        Write-Host "`nBatería aún en curso (sin battery_full_report.json)" -ForegroundColor Yellow
    }
} else {
    Write-Host "Aún no existe $root" -ForegroundColor Yellow
}
