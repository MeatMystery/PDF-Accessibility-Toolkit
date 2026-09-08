@echo off
setlocal EnableExtensions

rem Always work from the folder containing the launcher package.
cd /d "%~dp0.."

rem Keep the implementation files out of the way in normal Explorer views.
attrib +h ".internal" >nul 2>nul

if not exist "Input" mkdir "Input"
if not exist "Output" mkdir "Output"

echo ============================================================
echo PDF Table Header Scope Fixer
echo ============================================================
echo.
echo Input : %CD%\Input
echo Output: %CD%\Output
echo.

rem Prefer the Windows Python launcher, then fall back to python.exe.
set "PY="
where py >nul 2>nul
if not errorlevel 1 set "PY=py -3"
if not defined PY (
    where python >nul 2>nul
    if not errorlevel 1 set "PY=python"
)

if not defined PY (
    echo ERROR: Python 3 was not found.
    echo.
    echo Install Python 3.12 or newer, then run "Run Table Scope Fixer.exe" again.
    echo If you are on a Chico State managed computer, Python may be available in Company Portal.
    echo.
    pause
    exit /b 2
)

rem pypdf is bundled with this tool, so no pip install or internet connection is needed.
set "PYTHONPATH=%CD%\.internal\packages"

set "FOUND=0"
for %%F in ("Input\*.pdf") do (
    if exist "%%~fF" set "FOUND=1"
)

if "%FOUND%"=="0" (
    echo No PDF files were found in the Input folder.
    echo.
    echo Put one or more tagged PDFs in:
    echo     %CD%\Input
    echo.
    pause
    exit /b 0
)

echo Processing PDFs...
echo.
%PY% ".internal\table_scope_fixer.py" "Input" --output-dir "..\Output"
set "RESULT=%ERRORLEVEL%"

echo.
if "%RESULT%"=="0" (
    echo Finished. Corrected PDFs are in the Output folder.
    echo Opening Output...
    start "" "%CD%\Output"
) else (
    echo One or more PDFs could not be processed. Review the messages above.
)
echo.
pause
exit /b %RESULT%
