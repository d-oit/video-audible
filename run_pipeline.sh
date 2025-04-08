#!/bin/bash

set -e

if [ $# -lt 1 ]; then
  echo "Usage: ./run_pipeline.sh path/to/video.mp4"
  exit 1
fi

# Convert relative paths that start with / to be relative to current directory
if [[ "$1" == /* && ! "$1" == /[A-Za-z]:/* ]]; then
  # If path starts with / but is not a Windows absolute path like /C:/
  VIDEO_FILE=".${1}"
  echo "Converting path to: ${VIDEO_FILE}"
else
  VIDEO_FILE="$1"
fi

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
  echo "Creating virtual environment..."
  python -m venv .venv
fi

# Detect OS and activate virtual environment accordingly
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" || "$OSTYPE" == "win32" ]]; then
  # Windows Git Bash or similar
  ACTIVATE_SCRIPT=".venv/Scripts/activate"
else
  # Linux/macOS
  ACTIVATE_SCRIPT=".venv/bin/activate"
fi

if [ ! -f "$ACTIVATE_SCRIPT" ]; then
  echo "Activation script not found: $ACTIVATE_SCRIPT"
  exit 1
fi

# Activate virtual environment
source "$ACTIVATE_SCRIPT"

# Upgrade pip using python -m to avoid Windows permission issues
python -m pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Check if ffmpeg is installed and in PATH (required by MoviePy)
if ! command -v ffmpeg &> /dev/null; then
    echo "Error: ffmpeg is not installed or not found in PATH."
    echo "MoviePy requires ffmpeg for video processing."
    echo "Please install ffmpeg:"
    echo "  - Windows (Chocolatey): choco install ffmpeg"
    echo "  - macOS (Homebrew): brew install ffmpeg"
    echo "  - Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg"
    echo "  - Manual download: https://ffmpeg.org/download.html"
    exit 1
fi

# Set default values for feature flags
SILENCE_DETECTOR=${ENABLE_SILENCE_DETECTOR:-true}
SPEECH_DETECTOR=${ENABLE_SPEECH_DETECTOR:-true}
MUSIC_DETECTOR=${ENABLE_MUSIC_DETECTOR:-true}
BACKGROUND_DETECTOR=${ENABLE_BACKGROUND_DETECTOR:-true}

# Ensure PYTHONPATH includes the project root
export PYTHONPATH="$PYTHONPATH:$(pwd)"

# Run the modular pipeline
python -m src "$VIDEO_FILE"
