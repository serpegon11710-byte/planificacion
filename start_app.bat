
@echo off
rem Wrapper to run the PowerShell starter script. Use this file if you want to
rem double-click the project file in Explorer or run from cmd.
cd /d %~dp0
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_app.ps1"

rem To stop the app use stop_app.bat

