#!/bin/bash

# Check if input file is provided
if [ -z "$1" ]; then
    echo "Usage: $0 input.mp4 [output.mp3]"
    echo "If output path is not specified, it will be created from input filename"
    exit 1
fi

# Get input file and verify it exists
INPUT_FILE="$1"
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: Input file '$INPUT_FILE' not found"
    exit 1
fi

# Set output path - either from argument or derived from input filename
if [ -n "$2" ]; then
    OUTPUT_FILE="$2"
else
    # Remove extension from input file and append .mp3
    OUTPUT_FILE="${INPUT_FILE%.*}.mp3"
fi

# Convert relative paths that start with / to be relative to current directory (Windows Git Bash quirk)
if [[ "$1" == /* && ! "$1" == /[A-Za-z]:/* ]]; then
    INPUT_FILE=".$1"
    echo "Converting input path to: ${INPUT_FILE}"
else
    INPUT_FILE="$1"
fi

if [ -n "$2" ]; then
    OUTPUT_FILE="$2"
else
    OUTPUT_FILE="${INPUT_FILE%.*}.mp3"
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python -m venv .venv
fi

# Detect OS and activate virtual environment accordingly
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
    ACTIVATE_SCRIPT=".venv/Scripts/activate"
else
    ACTIVATE_SCRIPT=".venv/bin/activate"
fi

if [ ! -f "$ACTIVATE_SCRIPT" ]; then
    echo "Activation script not found: $ACTIVATE_SCRIPT"
    exit 1
fi

source "$ACTIVATE_SCRIPT"

# Upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# Set PYTHONPATH to project root
export PYTHONPATH="$PYTHONPATH:$(pwd)"

# Create output directory if it doesn't exist
OUTPUT_DIR=$(dirname "$OUTPUT_FILE")
mkdir -p "$OUTPUT_DIR"

# Find Python executable based on OS
if [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
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

# Call the standalone extract_audio.py script with input and output arguments
"$PYTHON_CMD" src/extract_audio.py "$INPUT_FILE" "$OUTPUT_FILE"
RESULT=$?

# Check if the output file was created
if [ -f "$OUTPUT_FILE" ] && [ $RESULT -eq 0 ]; then
    echo "Audio extraction completed successfully"
    exit 0
else
    echo "Error: Failed to create output file"
    exit 1
fi