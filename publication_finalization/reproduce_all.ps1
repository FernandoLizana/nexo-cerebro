# Reproduce Adaptive Behavior finalization package (Windows)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
if (-not $Root) { $Root = (Resolve-Path "$PSScriptRoot\..").Path }
Set-Location $Root
$env:CEREBRO_OLLAMA = "0"
$env:CEREBRO_SKIP_PROCESS_GUARD = "1"
$Py = Join-Path $Root ".venv\Scripts\python.exe"
if (-not (Test-Path $Py)) { $Py = "python" }
& $Py -u publication_finalization\scripts\run_publication_experiments.py --phase all --seeds 10 --steps 100 --profile compact
try {
  & $Py -u publication_finalization\scripts\run_motor_audit.py
} catch {
  Write-Warning "Motor audit pytest returned non-zero; see raw_results/motor_audit_E/"
}
& $Py -u publication_finalization\scripts\build_stats.py
& $Py -u publication_finalization\figure_scripts\plot_publication_figures.py
& $Py -u publication_finalization\scripts\pack_final.py
Write-Host "Done. See publication_finalization/FINAL_VALIDATION_REPORT.md"
