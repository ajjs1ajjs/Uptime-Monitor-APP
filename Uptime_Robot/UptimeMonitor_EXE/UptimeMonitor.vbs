Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' Get the directory where this script is located
scriptPath = WScript.ScriptFullName
installPath = FSO.GetParentFolderName(scriptPath)

' Change to the installation directory
WshShell.CurrentDirectory = installPath

' Create log file path
logFile = installPath & "\uptime_monitor.log"

' Run the exe with hidden window (0 = hidden, False = don't wait)
' Redirect stdout and stderr to log file
cmd = """" & installPath & "\UptimeMonitor.exe"" > """ & logFile & """ 2>&1"

On Error Resume Next
WshShell.Run cmd, 0, False

If Err.Number <> 0 Then
    ' Write error to log file
    Set logStream = FSO.OpenTextFile(logFile, 8, True)
    logStream.WriteLine Now & " - Error starting UptimeMonitor: " & Err.Description
    logStream.Close
End If

On Error GoTo 0

Set FSO = Nothing
Set WshShell = Nothing
