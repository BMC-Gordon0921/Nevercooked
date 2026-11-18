@echo off
rem 2D MCP group: aseprite 8770 / 8bit-music 8771 / soundbox 17494
setlocal
if not exist "%~dp0_sb\start_mcp_2d.ps1" (
  echo [!] _sb\start_mcp_2d.ps1 is missing - this entry needs the local _sb toolchain.
  echo     See README section "MCP 工具栈（2D 组）".
  if "%~1"=="" pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0_sb\start_mcp_2d.ps1" %*
set RC=%ERRORLEVEL%
if "%~1"=="" pause
exit /b %RC%
