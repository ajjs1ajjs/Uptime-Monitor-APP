@echo off
chcp 65001 >nul
echo =========================================
echo    Install Uptime Monitor (Simple)
echo =========================================
echo.

cd /d "%~dp0"

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Must run as Administrator!
    pause
    exit /b 1
)

echo Stopping any existing tasks...
schtasks /end /tn "UptimeMonitor" >nul 2>&1
schtasks /delete /tn "UptimeMonitor" /f >nul 2>&1

echo.
echo Creating scheduled task...

:: Create task using command line (no XML)
schtasks /create /tn "UptimeMonitor" /tr "wscript.exe \"%CD%\UptimeMonitor.vbs\"" /sc onstart /ru SYSTEM /f

if %errorLevel% neq 0 (
    echo ERROR: Failed to create task!
    pause
    exit /b 1
)

echo.
echo Task created successfully!
echo.
echo Starting task...
schtasks /run /tn "UptimeMonitor"
timeout /t 5 >nul

echo.
echo Checking if process started...
tasklist | find "UptimeMonitor"
if %errorLevel% equ 0 (
    echo.
    echo =========================================
    echo    SUCCESS! Service is running!
    echo =========================================
    echo.
    echo Access: http://localhost:8080
) else (
    echo.
    echo WARNING: Process not found. Check logs:
    echo %CD%\uptime_monitor.log
)

echo.
echo To manage:
echo   Check: schtasks /query /tn "UptimeMonitor"
echo   Stop:  schtasks /end /tn "UptimeMonitor"
echo   Start: schtasks /run /tn "UptimeMonitor"
echo   Remove:schtasks /delete /tn "UptimeMonitor" /f
echo.
pause
