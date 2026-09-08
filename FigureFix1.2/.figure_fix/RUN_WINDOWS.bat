@echo off
setlocal
cd /d "%~dp0"

set "SCRIPT=%~dp0process_folder.py"

where py >nul 2>nul
if %errorlevel%==0 (
    py -3 "%SCRIPT%"
    set "EXITCODE=%errorlevel%"
    goto finished
)

where python >nul 2>nul
if %errorlevel%==0 (
    python "%SCRIPT%"
    set "EXITCODE=%errorlevel%"
    goto finished
)

echo ============================================================
echo FIGURE FIX - PYTHON NOT FOUND
echo ============================================================
echo.
echo Python 3 is required to run Figure Fix.
echo Install Python 3.12 from Company Portal, then run Figure Fix.exe again.
echo.
set "EXITCODE=1"

:finished
echo.
echo Press any key to close...
pause >nul
exit /b %EXITCODE%
