@echo off
REM ============================================================
REM THE CORTEX PROTOCOL - STARTUP SCRIPT
REM ============================================================

echo.
echo ===============================================
echo    THE CORTEX PROTOCOL - STARTING ENGINE
echo ===============================================
echo.

REM Navigate to Python directory
cd /d "%~dp0\..\Python"

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo [1/3] Creating virtual environment...
    python -m venv venv
    call venv\Scripts\activate.bat
    echo [2/3] Installing dependencies...
    pip install -r requirements.txt
) else (
    echo [1/3] Activating virtual environment...
    call venv\Scripts\activate.bat
)

echo [3/3] Starting Cortex Brain...
echo.
echo ===============================================
echo    CORTEX ONLINE - WAITING FOR NINJATRADER
echo ===============================================
echo.

python cortex_server.py
