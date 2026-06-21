@echo off
REM Double-click this to launch the GetYourGuide LOB Forecasting app locally.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0run_local.ps1"
pause
