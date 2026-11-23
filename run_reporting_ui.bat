@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv-science\Scripts\python.exe" (
  echo Missing .venv-science environment. See docs\PROGRESS_REPORTING_BUILD.md.
  exit /b 1
)
".venv-science\Scripts\python.exe" -m streamlit run reporting_app.py
endlocal
