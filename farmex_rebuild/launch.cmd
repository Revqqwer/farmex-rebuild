@echo off
cd /d "%~dp0"
if exist "%LOCALAPPDATA%\Programs\Python\Python39\python.exe" (
  "%LOCALAPPDATA%\Programs\Python\Python39\python.exe" app.py
) else (
  py -3 app.py
)
if errorlevel 1 pause
