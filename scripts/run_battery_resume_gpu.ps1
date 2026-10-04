# Resume pending battery with max GPU (1 process / 1 seed - no VRAM contention)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$env:CEREBRO_OLLAMA = "0"
$env:CEREBRO_SKIP_PROCESS_GUARD = "1"
$env:CEREBRO_USE_GPU = "1"
$env:CEREBRO_GPU_AGGRESSIVE = "1"
$env:CEREBRO_GPU_PERSIST = "1"
$env:CEREBRO_GPU_MAX_STEPS = "999999"
$env:CEREBRO_GPU_COOLDOWN = "0"
$env:CEREBRO_GPU_MIN_STEPS = "1"
$env:CEREBRO_MIN_NEURONS_GPU = "200"
$env:CEREBRO_HEADLESS_EP_STEPS = "64"

$Out = "experiments\results\battery_10k_gpu"

Write-Host "E1 pending (noaffect, noconscious, nopfc, nohippo) turbo GPU" -ForegroundColor Cyan
python -m experiments.run_e1_parallel --turbo-gpu --conditions noaffect,noconscious,nopfc,nohippo --seeds 20 --steps 200 --profile 10k --out $Out --parallel-seeds 1 --workers 1
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "E2-E8 turbo GPU" -ForegroundColor Cyan
python -m experiments.run_battery_10k --mode full --turbo-gpu --only E2,E3,E4,E5,E6,E7,E8 --seeds 20 --parallel-seeds 1 --out $Out
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Done. Report: $Out\battery_full_report.json" -ForegroundColor Green
