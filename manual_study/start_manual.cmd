@echo off
cd /d "%~dp0"
if exist "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" (
  "%LOCALAPPDATA%\Programs\Python\Python314\python.exe" -B research_manual.py %*
) else (
  py -B research_manual.py %*
)
pause
