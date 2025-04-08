#!/bin/bash

# Set up error handling
set -e

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

# Upgrade pip and install test dependencies if needed
python -m pip install --upgrade pip
pip install -r requirements-test.txt

# Set PYTHONPATH to include the project root
export PYTHONPATH="$PYTHONPATH:$(pwd)"

# Run the tests
echo "Running tests..."
python -m pytest "$@"

# Check if any tests failed
if [ $? -eq 0 ]; then
    echo "All tests passed!"
    exit 0
else
    echo "Some tests failed."
    exit 1
fi