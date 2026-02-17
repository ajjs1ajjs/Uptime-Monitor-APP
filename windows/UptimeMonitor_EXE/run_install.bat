@echo off
cd /d "%~dp0"
install_task.bat > install_output.txt 2>&1
echo Exit code: %ERRORLEVEL% >> install_output.txt
