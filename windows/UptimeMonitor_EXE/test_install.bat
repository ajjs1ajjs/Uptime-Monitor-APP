@echo off
echo Testing install_task.bat...
echo.
cd /d "%~dp0"

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Must run as Administrator!
    pause
    exit /b 1
)

echo Admin check passed!
echo.
echo Creating XML...

set "INSTALL_PATH=%CD%"

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
echo       ^<LogonType^>ServiceAccount^</LogonType^>
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

echo XML created. Testing XML validity...
type "%TEMP%\UptimeMonitor_Task.xml" | find "</Task>" >nul
if %errorLevel% neq 0 (
    echo ERROR: XML file is invalid!
    type "%TEMP%\UptimeMonitor_Task.xml"
    pause
    exit /b 1
)

echo XML is valid!
echo.
echo Creating task...
schtasks /create /tn "UptimeMonitor" /xml "%TEMP%\UptimeMonitor_Task.xml" /f
if %errorLevel% neq 0 (
    echo ERROR: Failed to create task!
    pause
    exit /b 1
)

del "%TEMP%\UptimeMonitor_Task.xml" >nul 2>&1

echo.
echo Task created successfully!
echo Starting task...
schtasks /run /tn "UptimeMonitor"
timeout /t 3 >nul

tasklist | findstr UptimeMonitor
echo.
echo Access: http://localhost:8080
pause
