@echo off
setlocal

set SCRIPT_DIR=%~dp0
set PROJECT_ROOT=%SCRIPT_DIR%..
set RESTART_LOG=%PROJECT_ROOT%\streamlit_restart.log

powershell -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%restart_streamlit.ps1" %*
set EXIT_CODE=%ERRORLEVEL%

echo.
echo --- streamlit_restart.log ---
if exist "%RESTART_LOG%" (
    type "%RESTART_LOG%"
) else (
    echo Restart log not found: "%RESTART_LOG%"
)

exit /b %EXIT_CODE%
