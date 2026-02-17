@echo off
chcp 65001 >nul
echo =========================================
echo    Test XML Creation
echo =========================================
echo.

cd /d "%~dp0"

net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Must run as Administrator!
    pause
    exit /b 1
)

echo Admin check PASSED!
echo.
set "INSTALL_PATH=%CD%"
echo Install path: %INSTALL_PATH%
echo.

echo Creating XML file...
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
) > "%TEMP%\Test_UptimeMonitor.xml"

if exist "%TEMP%\Test_UptimeMonitor.xml" (
    echo XML file created SUCCESSFULLY!
    echo.
    echo File size:
    dir "%TEMP%\Test_UptimeMonitor.xml" | find "Test_UptimeMonitor"
    echo.
    echo Checking for closing tag...
    find "</Task>" "%TEMP%\Test_UptimeMonitor.xml" >nul
    if %errorLevel% equ 0 (
        echo [OK] Closing tag </Task> found!
    ) else (
        echo [ERROR] Closing tag NOT found!
    )
    echo.
    echo Creating task...
    schtasks /create /tn "TestUptimeMonitor" /xml "%TEMP%\Test_UptimeMonitor.xml" /f
    if %errorLevel% equ 0 (
        echo.
        echo [SUCCESS] Task created!
        schtasks /query /tn "TestUptimeMonitor" | find "TestUptimeMonitor"
        echo.
        echo Running task...
        schtasks /run /tn "TestUptimeMonitor"
        timeout /t 3 >nul
        echo.
        tasklist | find "UptimeMonitor"
    ) else (
        echo [ERROR] Failed to create task!
    )
    
    del "%TEMP%\Test_UptimeMonitor.xml" >nul 2>&1
) else (
    echo [ERROR] Failed to create XML file!
)

echo.
pause
