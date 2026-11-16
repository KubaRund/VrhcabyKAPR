@echo off
setlocal
cd /d "%~dp0"
if exist "runtime\python.exe" (
    "runtime\python.exe" -X utf8 web.py %*
    goto :result
)
where py >nul 2>&1
if errorlevel 1 (
    python -X utf8 web.py %*
) else (
    py -3 -X utf8 web.py %*
)
:result
if errorlevel 1 pause
