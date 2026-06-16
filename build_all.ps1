# One-shot build of the whole warehouse on Windows.
#   powershell -ExecutionPolicy Bypass -File build_all.ps1
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host "==> 1/5 Generating synthetic Olist data" -ForegroundColor Cyan
& "$root\.venv\Scripts\python.exe" "$root\scripts\generate_olist_data.py"

$env:DBT_PROFILES_DIR = "$root\olist_dbt"
Set-Location "$root\olist_dbt"
$dbt = "$root\.venv\Scripts\dbt.exe"

Write-Host "==> 2/5 dbt run" -ForegroundColor Cyan
& $dbt run

Write-Host "==> 3/5 dbt test" -ForegroundColor Cyan
& $dbt test

Write-Host "==> 4/5 dbt docs generate" -ForegroundColor Cyan
& $dbt docs generate

Set-Location $root
Write-Host "==> 5/5 Done. Launch the dashboard with:" -ForegroundColor Green
Write-Host "    .\.venv\Scripts\streamlit.exe run dashboard\streamlit_app.py"
