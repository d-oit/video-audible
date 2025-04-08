#!/bin/bash

# Find Python executable
# First check if we're in a virtual environment
if [ -n "$VIRTUAL_ENV" ]; then
    PYTHON_EXEC="$VIRTUAL_ENV/Scripts/python"
elif command -v python3 &>/dev/null; then
    PYTHON_EXEC=python3
elif command -v python &>/dev/null; then
    PYTHON_EXEC=python
else
    echo "Error: Python not found"
    exit 1
fi

# Print which Python we're using
echo "Using Python: $PYTHON_EXEC"

# Check for input file
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <audio_file.mp3> [output_directory]"
    exit 1
fi

AUDIO_FILE="$1"
OUTPUT_DIR="${2:-movie_segments}"

# Set PYTHONPATH to project root
export PYTHONPATH="$PYTHONPATH:$(pwd)"

# Create output directory if it doesn't exist
mkdir -p "$OUTPUT_DIR"

# Run the movie segments extraction script
"$PYTHON_EXEC" extract_movie_segments.py "$AUDIO_FILE" --output-dir "$OUTPUT_DIR"