@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   Uptime Monitor - Installation
echo ========================================
echo.

set /p PORT="Enter port (default 8000): "
if "%PORT%"=="" set PORT=8000

echo.
echo Installing Uptime Monitor on port %PORT%...
echo.

cd /d "%~dp0"

echo %PORT% > port.txt

python main.py install

sc config UptimeMonitor start= auto
net start UptimeMonitor

echo.
echo ========================================
echo   Installation complete!
echo ========================================
echo.
echo Service: UptimeMonitor
echo Port: %PORT%
echo.
echo To manage service:
echo   net stop UptimeMonitor
echo   net start UptimeMonitor
echo   sc delete UptimeMonitor
echo.
echo To access: http://localhost:%PORT%
echo.

pause
