@echo off
chcp 65001 >nul
echo ==========================================
echo    Uptime Monitor - Quick Start
echo ==========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

echo Python found!
python --version
echo.

:: Check if requirements are installed
echo Checking dependencies...
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo Installing required packages...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install packages!
        pause
        exit /b 1
    )
)

echo.
echo ==========================================
echo Starting Uptime Monitor...
echo ==========================================
echo.
echo The application will be available at:
echo http://localhost:8000
echo.
echo To use a different port, run: start_port.bat [PORT]
echo Example: start_port.bat 8080
echo.
echo Press Ctrl+C to stop
echo.

python main.py

pause
