@echo off
setlocal
cd /d "%~dp0"

REM Prefer the Python launcher if present
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 -m pip install --user --upgrade pip
  py -3 -m pip install --user pikepdf
  py -3 process_folder.py
) else (
  python -m pip install --user --upgrade pip
  python -m pip install --user pikepdf
  python process_folder.py
)

echo.
echo Press any key to close...
pause >nul