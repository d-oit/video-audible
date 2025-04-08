@echo off
setlocal EnableDelayedExpansion

REM Check if input file is provided
if "%~1"=="" (
    echo Usage: %0 input.mp4 [output.mp3]
    echo If output path is not specified, it will be created from input filename
    exit /b 1
)

REM Get input file and verify it exists
set "INPUT_FILE=%~1"
if not exist "!INPUT_FILE!" (
    echo Error: Input file '!INPUT_FILE!' not found
    exit /b 1
)

REM Set output path - either from argument or derived from input filename
if not "%~2"=="" (
    set "OUTPUT_FILE=%~2"
) else (
    set "OUTPUT_FILE=%~dpn1.mp3"
)

REM Create output directory if it doesn't exist
for %%F in ("!OUTPUT_FILE!") do set "OUTPUT_DIR=%%~dpF"
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

REM Create temporary Python script
set "TEMP_SCRIPT=%TEMP%\extract_audio_%RANDOM%.py"
(
echo from src.audio_pipeline import AudioPipeline
echo.
echo try:
echo     pipeline = AudioPipeline^(^)
echo     pipeline.extract_audio_to_file^(r'%INPUT_FILE%', r'%OUTPUT_FILE%'^)
echo     print^(f"Successfully extracted audio to: {r'%OUTPUT_FILE%'}'^)
echo except Exception as e:
echo     print^(f"Error: {str^(e^)}'^)
echo     exit^(1^)
) > "%TEMP_SCRIPT%"

REM Execute the Python script
%PYTHON_CMD% "%TEMP_SCRIPT%"
set RESULT=%ERRORLEVEL%

REM Clean up temporary script
del "%TEMP_SCRIPT%" >nul 2>&1

REM Check if the output file was created
if exist "!OUTPUT_FILE!" if %RESULT% equ 0 (
    echo Audio extraction completed successfully
    exit /b 0
) else (
    echo Error: Failed to create output file
    exit /b 1
)