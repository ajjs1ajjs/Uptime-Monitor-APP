@echo off
chcp 65001 >nul
echo =========================================
echo    Uptime Monitor - Manual Start
echo =========================================
echo.

cd /d "%~dp0"

if not exist "UptimeMonitor.exe" (
    echo ERROR: UptimeMonitor.exe not found!
    echo Please run build_exe.bat first
    pause
    exit /b 1
)

echo Starting Uptime Monitor...
echo Working directory: %CD%
echo.
echo Access: http://localhost:8080
echo Press Ctrl+C to stop
echo.

UptimeMonitor.exe console

pause
