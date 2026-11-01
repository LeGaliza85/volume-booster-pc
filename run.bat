@echo off
setlocal
cd /d "%~dp0"

where pythonw >nul 2>nul
if errorlevel 1 goto try_console
start "" pythonw "app.py"
exit /b 0

:try_console
where python >nul 2>nul
if errorlevel 1 goto try_py
start "" python "app.py"
exit /b 0

:try_py
where py >nul 2>nul
if errorlevel 1 goto no_python
start "" py "app.py"
exit /b 0

:no_python
echo Python 3.10 or newer is required: https://www.python.org/downloads/
pause
exit /b 1
