@echo off
chcp 65001 >nul
echo =========================================
echo    Remove Uptime Monitor
echo =========================================
echo.

cd /d "%~dp0"

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Must run as Administrator!
    pause
    exit /b 1
)

echo Stopping Uptime Monitor...
schtasks /end /tn "UptimeMonitor" >nul 2>&1

echo Removing scheduled task...
schtasks /delete /tn "UptimeMonitor" /f >nul 2>&1

sc delete UptimeMonitor >nul 2>&1

echo.
echo Uptime Monitor removed.
pause
