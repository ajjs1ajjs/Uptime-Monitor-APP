@echo off
chcp 65001 >nul
echo =========================================
echo    Install Uptime Monitor (Task Scheduler)
echo =========================================
echo.

cd /d "%~dp0"

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Must run as Administrator!
    pause
    exit /b 1
)

if not exist "UptimeMonitor.exe" (
    echo ERROR: UptimeMonitor.exe not found!
    echo Please build the EXE first using: pyinstaller main.spec
    pause
    exit /b 1
)

set "INSTALL_PATH=%CD%"

echo Stopping any existing services...
net stop UptimeMonitor >nul 2>&1
sc delete UptimeMonitor >nul 2>&1
schtasks /delete /tn "UptimeMonitor" /f >nul 2>&1

echo.
echo Creating scheduled task with proper working directory...

:: Create XML task definition with working directory
(
echo ^<?xml version="1.0" encoding="UTF-16"?^>
echo ^<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task"^>
echo   ^<RegistrationInfo^>
echo     ^<Description^>Uptime Monitor - Website monitoring service^</Description^>
echo   ^</RegistrationInfo^>
echo   ^<Triggers^>
echo     ^<BootTrigger^>
echo       ^<Enabled^>true^</Enabled^>
echo     ^</BootTrigger^>
echo   ^</Triggers^>
echo   ^<Principals^>
echo     ^<Principal id="Author"^>
echo       ^<UserId^>SYSTEM^</UserId^>
echo       ^<LogonType^>S4U^</LogonType^>
echo       ^<RunLevel^>HighestAvailable^</RunLevel^>
echo     ^</Principal^>
echo   ^</Principals^>
echo   ^<Settings^>
echo     ^<MultipleInstancesPolicy^>IgnoreNew^</MultipleInstancesPolicy^>
echo     ^<DisallowStartIfOnBatteries^>false^</DisallowStartIfOnBatteries^>
echo     ^<StopIfGoingOnBatteries^>false^</StopIfGoingOnBatteries^>
echo     ^<AllowHardTerminate^>true^</AllowHardTerminate^>
echo     ^<StartWhenAvailable^>true^</StartWhenAvailable^>
echo     ^<RunOnlyIfNetworkAvailable^>false^</RunOnlyIfNetworkAvailable^>
echo     ^<IdleSettings^>
echo       ^<StopOnIdleEnd^>true^</StopOnIdleEnd^>
echo       ^<RestartOnIdle^>false^</RestartOnIdle^>
echo     ^</IdleSettings^>
echo     ^<AllowStartOnDemand^>true^</AllowStartOnDemand^>
echo     ^<Enabled^>true^</Enabled^>
echo     ^<Hidden^>false^</Hidden^>
echo     ^<RunOnlyIfIdle^>false^</RunOnlyIfIdle^>
echo     ^<WakeToRun^>false^</WakeToRun^>
echo     ^<ExecutionTimeLimit^>PT0S^</ExecutionTimeLimit^>
echo     ^<Priority^>7^</Priority^>
echo   ^</Settings^>
echo   ^<Actions Context="Author"^>
echo     ^<Exec^>
echo       ^<Command^>wscript.exe^</Command^>
echo       ^<Arguments^>"%INSTALL_PATH%\UptimeMonitor.vbs"^</Arguments^>
echo       ^<WorkingDirectory^>%INSTALL_PATH%^</WorkingDirectory^>
echo     ^</Exec^>
echo   ^</Actions^>
echo ^</Task^>
) > "%TEMP%\UptimeMonitor_Task.xml"

schtasks /create /tn "UptimeMonitor" /xml "%TEMP%\UptimeMonitor_Task.xml" /f

if %errorLevel% neq 0 (
    echo ERROR: Failed to create task!
    del "%TEMP%\UptimeMonitor_Task.xml" >nul 2>&1
    pause
    exit /b 1
)

del "%TEMP%\UptimeMonitor_Task.xml" >nul 2>&1

echo.
echo Creating sites.db if not exists...
if not exist "%INSTALL_PATH%\sites.db" (
    echo Database will be created automatically on first run.
)

echo.
echo Creating port configuration...
echo 8080 > "%INSTALL_PATH%\port.txt"

echo.
echo Starting service...
schtasks /run /tn "UptimeMonitor"
timeout /t 5 >nul

echo.
echo =========================================
echo    Installation Complete!
echo =========================================
echo.
echo Access: http://localhost:8080
echo Install Path: %INSTALL_PATH%
echo.
echo To check status: schtasks /query /tn "UptimeMonitor"
echo To stop: schtasks /end /tn "UptimeMonitor"
echo To start: schtasks /run /tn "UptimeMonitor"
echo To uninstall: schtasks /delete /tn "UptimeMonitor" /f
echo.
pause
