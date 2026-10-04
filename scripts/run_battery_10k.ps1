# Batería E1–E8 @10k — Nexo/cerebro
# Uso:
#   .\scripts\run_battery_10k.ps1              # smoke (2 seeds, ~minutos)
#   .\scripts\run_battery_10k.ps1 -Mode full   # paper (20 seeds, horas)
#   .\scripts\run_battery_10k.ps1 -Only E1,E2  # subset

param(
    [ValidateSet("smoke", "full")]
    [string]$Mode = "smoke",

    [int]$Seeds = 0,

    [string]$Out = "",

    [string]$Profile = "10k",

    [int]$ParallelSeeds = 2,

    [string]$Only = "",

    [switch]$ManifestOnly,

    [switch]$SkipAudit
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$env:CEREBRO_OLLAMA = "0"
$env:CEREBRO_SKIP_PROCESS_GUARD = "1"

$argsList = @("-m", "experiments.run_battery_10k", "--mode", $Mode, "--profile", $Profile, "--parallel-seeds", "$ParallelSeeds")

if ($Seeds -gt 0) { $argsList += @("--seeds", "$Seeds") }
if ($Out) { $argsList += @("--out", $Out) }
if ($Only) { $argsList += @("--only", $Only) }
if ($ManifestOnly) { $argsList += "--manifest-only" }
if ($SkipAudit) { $argsList += "--skip-audit" }

Write-Host "==> python $($argsList -join ' ')" -ForegroundColor Cyan
python @argsList
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
