@echo off
chcp 65001 >nul
echo ==========================================
echo    Uptime Monitor - Custom Port
echo ==========================================
echo.

set PORT=%1
if "%PORT%"=="" set PORT=8000

echo Starting on port %PORT%...
echo.
echo The application will be available at:
echo http://localhost:%PORT%
echo.
echo Press Ctrl+C to stop
echo.

python main.py %PORT%

pause
