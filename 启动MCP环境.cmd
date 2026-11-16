@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
set "PS=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
set "SCRIPT=%~dp0_sb\start_mcp_stack.ps1"

if /i "%~1"=="stop" (
    "%PS%" -NoProfile -ExecutionPolicy Bypass -File "!SCRIPT!" -Stop
    goto :done
)
if /i "%~1"=="probe" (
    "%PS%" -NoProfile -ExecutionPolicy Bypass -File "!SCRIPT!" -Probe
    goto :done
)
"%PS%" -NoProfile -ExecutionPolicy Bypass -File "!SCRIPT!"

:done
echo.
echo Tip: this window can be closed. Logs: _sb\gw\logs\
pause
