@echo off
setlocal enabledelayedexpansion

echo ========================================
echo PDF ToUnicode Repair Script (Python)
echo ========================================

:: --- Find Python without requiring PATH ---
set "PYTHON_EXE="

for %%P in (
    "%LocalAppData%\Programs\Python\Python313\python.exe"
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python310\python.exe"
    "%LocalAppData%\Programs\Python\Python39\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
    "C:\Python311\python.exe"
    "C:\Python310\python.exe"
    "C:\Python39\python.exe"
) do (
    if exist %%~P (
        set "PYTHON_EXE=%%~P"
        goto found_python
    )
)

py --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON_EXE=py"
    goto found_python
)

echo [ERROR] Python is not installed or could not be found.
echo Install Python from https://www.python.org/downloads/
pause
exit /b 1

:found_python
echo Using Python: %PYTHON_EXE%

:: --- Install dependencies ---
echo.
echo Installing required Python packages...
%PYTHON_EXE% -m pip install --upgrade pip >nul 2>&1
%PYTHON_EXE% -m pip install pikepdf fonttools

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    pause
    exit /b 1
)

echo Dependencies installed successfully.
echo.

:: --- Check script exists ---
if not exist repair_tounicode.py (
    echo [ERROR] repair_tounicode.py not found in this folder.
    echo Make sure the Python script is in the same directory.
    pause
    exit /b 1
)

:: --- Handle input ---
if "%~1"=="" (
    echo Drag and drop PDF files onto this .bat file
    echo OR run: repair_pdf.bat file1.pdf file2.pdf
    pause
    exit /b 0
)

:: --- Process all passed files ---
:loop
if "%~1"=="" goto done

set "input=%~1"
set "output=%~dpn1_repaired.pdf"

echo ----------------------------------------
echo Processing: %input%
echo Output: %output%
echo ----------------------------------------

%PYTHON_EXE% repair_tounicode.py "%input%" "%output%"

if errorlevel 1 (
    echo [WARNING] Failed to process %input%
) else (
    echo [OK] Finished %input%
)

shift
goto loop

:done
echo.
echo All files processed.
pause