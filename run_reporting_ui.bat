@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Missing .venv environment.
  echo Create it and install the reporting dependencies:
  echo   py -3.11 -m venv .venv
  echo   .venv\Scripts\python.exe -m pip install -e ".[reporting]"
  exit /b 1
)
".venv\Scripts\python.exe" -m streamlit run reporting_app.py
endlocal
