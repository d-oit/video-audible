#!/bin/bash

# Check if input files are provided
if [ -z "$1" ] || [ -z "$2" ]; then
    echo "Usage: $0 input.mp3 segments.md [output_dir]"
    echo "If output directory is not specified, it will be created as 'segments'"
    exit 1
fi

# Get input files and verify they exist
AUDIO_FILE="$1"
MD_FILE="$2"

if [ ! -f "$AUDIO_FILE" ]; then
    echo "Error: Audio file '$AUDIO_FILE' not found"
    exit 1
fi

if [ ! -f "$MD_FILE" ]; then
    echo "Error: Markdown file '$MD_FILE' not found"
    exit 1
fi

# Set output directory - either from argument or default
if [ -n "$3" ]; then
    OUTPUT_DIR="$3"
else
    OUTPUT_DIR="segments"
fi

# Convert relative paths that start with / to be relative to current directory (Windows Git Bash quirk)
if [[ "$1" == /* && ! "$1" == /[A-Za-z]:/* ]]; then
    AUDIO_FILE=".$1"
    echo "Converting audio path to: ${AUDIO_FILE}"
fi

if [[ "$2" == /* && ! "$2" == /[A-Za-z]:/* ]]; then
    MD_FILE=".$2"
    echo "Converting markdown path to: ${MD_FILE}"
fi

# Check if ffmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed. Please install it:"
    echo "  - Windows (Chocolatey): choco install ffmpeg"
    echo "  - macOS (Homebrew): brew install ffmpeg"
    echo "  - Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg"
    exit 1
fi

# Find Python executable based on OS
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    # Windows - try py launcher first, then python
    if command -v py &> /dev/null; then
        PYTHON_CMD="py"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else 
        echo "Error: Python not found. Please install Python 3 from https://www.python.org/downloads/"
        exit 1
    fi
else
    # Unix-like systems - try python3 first, then python
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo "Error: Python not found. Please install Python 3 using your system's package manager."
        exit 1
    fi
fi

echo "Using Python command: $PYTHON_CMD"

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    "$PYTHON_CMD" -m venv .venv
fi

# Detect OS and activate virtual environment accordingly
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "win32" ]]; then
    ACTIVATE_SCRIPT=".venv/Scripts/activate"
else
    ACTIVATE_SCRIPT=".venv/bin/activate"
fi

if [ ! -f "$ACTIVATE_SCRIPT" ]; then
    echo "Activation script not found: $ACTIVATE_SCRIPT"
    exit 1
fi

source "$ACTIVATE_SCRIPT"

# Verify Python executable after activation
PYTHON_EXEC=$(which python)
echo "Using Python executable: $PYTHON_EXEC"

# Install dependencies
echo "Installing dependencies..."
"$PYTHON_EXEC" -m pip install --upgrade pip
"$PYTHON_EXEC" -m pip install --no-cache-dir -r requirements.txt

# Verify ffmpeg-python installation
echo "Verifying ffmpeg-python installation..."
if ! "$PYTHON_EXEC" -c "import ffmpeg; print('ffmpeg-python import successful')"; then
    echo "Failed to import ffmpeg-python"
    exit 1
fi

# Set PYTHONPATH to project root
export PYTHONPATH="$PYTHONPATH:$(pwd)"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Call the segments extraction script using the verified Python executable
"$PYTHON_EXEC" extract_segments.py "$AUDIO_FILE" "$MD_FILE" "$OUTPUT_DIR"
RESULT=$?

# Check if any output files were created
if [ $RESULT -eq 0 ] && [ -d "$OUTPUT_DIR" ] && [ "$(ls -A "$OUTPUT_DIR")" ]; then
    echo "Audio segments extraction completed successfully"
    echo "Output files are in: $OUTPUT_DIR"
    exit 0
else
    echo "Error: Failed to create output files"
    exit 1
fi