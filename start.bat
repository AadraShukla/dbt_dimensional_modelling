@echo off
setlocal EnableDelayedExpansion
cd /d "%~dp0"

REM ── Already set up? Skip straight to dashboard ──────────────────────────────
if exist ".venv\Scripts\streamlit.exe" if exist "data\olist.duckdb" goto :run

echo.
echo  First-run setup — takes a few minutes, won't repeat.
echo  ─────────────────────────────────────────────────────
echo.

REM ── Step 1: Make sure uv is on PATH ─────────────────────────────────────────
where uv >nul 2>&1
if %errorlevel% equ 0 goto :uv_ok

REM Check common locations for prior standalone or pip installs
for %%P in (
    "%USERPROFILE%\.local\bin\uv.exe"
    "%APPDATA%\uv\bin\uv.exe"
    "%USERPROFILE%\.cargo\bin\uv.exe"
) do (
    if exist %%P (
        set "PATH=%%~dP%%~pP;!PATH!"
        goto :uv_ok
    )
)

REM Not found — install the official standalone uv (puts itself on PATH permanently)
echo  [1/4] uv not on PATH — installing standalone uv ...
powershell -ExecutionPolicy Bypass -Command "irm https://astral.sh/uv/install.ps1 | iex"
set "PATH=%USERPROFILE%\.local\bin;%PATH%"
where uv >nul 2>&1
if !errorlevel! neq 0 (
    echo.
    echo  ERROR: uv install failed.
    echo  Install manually: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)
echo  uv installed OK.
goto :uv_step_done

:uv_ok
echo  [1/4] uv already available.

:uv_step_done
uv --version

REM ── Step 2: Create .venv + install deps (uv auto-downloads Python 3.12) ──────
echo.
echo  [2/4] Creating .venv and installing dependencies ...
uv sync
if !errorlevel! neq 0 (
    echo  ERROR: uv sync failed.
    pause
    exit /b 1
)

REM ── Step 3: Generate data + dbt run + dbt test + docs ───────────────────────
echo.
echo  [3/4] Building dbt warehouse ...
powershell -ExecutionPolicy Bypass -File "%~dp0build_all.ps1"
if !errorlevel! neq 0 (
    echo  ERROR: build_all.ps1 failed.
    pause
    exit /b 1
)

echo.
echo  [4/4] Setup complete!
echo.

REM ── Start dashboard ──────────────────────────────────────────────────────────
:run
echo  Starting Streamlit dashboard ...
echo  (Press Ctrl+C to stop)
echo.
.venv\Scripts\streamlit.exe run dashboard\streamlit_app.py
