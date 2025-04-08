@echo off
setlocal EnableDelayedExpansion

REM Check if input files are provided
if "%~1"=="" (
    echo Usage: %0 input.mp3 segments.md [output_dir]
    echo If output directory is not specified, it will be created as 'segments'
    exit /b 1
)

if "%~2"=="" (
    echo Usage: %0 input.mp3 segments.md [output_dir]
    echo If output directory is not specified, it will be created as 'segments'
    exit /b 1
)

REM Get input files and verify they exist
set "AUDIO_FILE=%~1"
set "MD_FILE=%~2"

if not exist "!AUDIO_FILE!" (
    echo Error: Audio file '!AUDIO_FILE!' not found
    exit /b 1
)

if not exist "!MD_FILE!" (
    echo Error: Markdown file '!MD_FILE!' not found
    exit /b 1
)

REM Set output directory - either from argument or default
if not "%~3"=="" (
    set "OUTPUT_DIR=%~3"
) else (
    set "OUTPUT_DIR=segments"
)

REM Create virtual environment if it doesn't exist
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\Scripts\activate.bat
if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    exit /b 1
)

REM Get Python executable path
for /f "tokens=*" %%i in ('%PYTHON_CMD% -c "import sys; print(sys.executable)"') do set PYTHON_EXEC=%%i
echo Using Python executable: %PYTHON_EXEC%

REM Force reinstall dependencies
"%PYTHON_EXEC%" -m pip install --upgrade pip
"%PYTHON_EXEC%" -m pip install --no-cache-dir -r requirements.txt
"%PYTHON_EXEC%" -m pip install --no-cache-dir --force-reinstall moviepy

REM Verify moviepy installation
"%PYTHON_EXEC%" -c "from moviepy.editor import AudioFileClip; print('MoviePy import successful')" || (
    echo Failed to import MoviePy after installation
    exit /b 1
)

REM Set PYTHONPATH to project root
set "PYTHONPATH=%PYTHONPATH%;%CD%"

REM Create output directory
if not exist "!OUTPUT_DIR!" mkdir "!OUTPUT_DIR!"

REM Find Python executable
where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PYTHON_CMD=py"
) else (
    where python >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set "PYTHON_CMD=python"
    ) else (
        echo Error: Python not found. Please install Python 3 from https://www.python.org/downloads/
        echo Make sure to check "Add Python to PATH" during installation.
        exit /b 1
    )
)

echo Using Python command: %PYTHON_CMD%

REM Call the segments extraction script using the verified Python executable
"%PYTHON_EXEC%" extract_segments.py "%AUDIO_FILE%" "%MD_FILE%" "%OUTPUT_DIR%"
set RESULT=%ERRORLEVEL%

REM Check if any output files were created
dir /b "%OUTPUT_DIR%\*" >nul 2>&1
if %ERRORLEVEL% equ 0 if %RESULT% equ 0 (
    echo Audio segments extraction completed successfully
    echo Output files are in: %OUTPUT_DIR%
    exit /b 0
) else (
    echo Error: Failed to create output files
    exit /b 1
)