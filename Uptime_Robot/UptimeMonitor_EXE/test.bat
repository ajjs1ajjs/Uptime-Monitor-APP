@echo off
chcp 65001 >nul
echo =========================================
echo    TEST Uptime Monitor
echo =========================================
echo.

cd /d "%~dp0"

echo Working directory: %CD%
echo Testing in console mode...
echo Press Ctrl+C to stop
echo.
UptimeMonitor.exe console
