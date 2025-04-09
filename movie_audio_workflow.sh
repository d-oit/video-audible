#!/bin/bash
set -e

# Check for input file
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 <audio_file.mp3>"
    exit 1
fi

AUDIO_FILE="$1"
BASE_DIR="movie_project_$(date +%Y%m%d_%H%M%S)"
SEGMENTS_DIR="$BASE_DIR/segments"
VOICEOVERS_DIR="$BASE_DIR/voiceovers"
FINAL_OUTPUT="$BASE_DIR/final_movie_with_descriptions.mp3"

echo "=== Movie Audio Enhancement Workflow ==="
echo "Input file: $AUDIO_FILE"
echo "Project directory: $BASE_DIR"

# Step 1: Extract movie segments
echo -e "\n=== Step 1: Extracting movie segments ==="
./extract_movie_segments.sh "$AUDIO_FILE" "$SEGMENTS_DIR"

# Step 2: Prompt user to edit the script
echo -e "\n=== Step 2: Complete the voiceover script ==="
echo "Please edit the voiceover script at: $SEGMENTS_DIR/voiceover_script.md"
echo "Add detailed descriptions for each scene."
echo "Press Enter when you're done..."
read -p ""

# Step 3: Generate voiceovers
echo -e "\n=== Step 3: Generating AI voiceovers ==="
if [ -z "$ELEVENLABS_API_KEY" ]; then
    echo "Please enter your ElevenLabs API key:"
    read -s ELEVENLABS_API_KEY
    export ELEVENLABS_API_KEY
fi

python src/generate_voiceovers.py "$SEGMENTS_DIR/voiceover_script.md" --output-dir "$VOICEOVERS_DIR"

# Step 4: Combine everything
echo -e "\n=== Step 4: Combining segments with voiceovers ==="
python src/combine_with_voiceovers.py "$SEGMENTS_DIR" "$VOICEOVERS_DIR" --output "$FINAL_OUTPUT"

echo -e "\n=== Workflow Complete! ==="
echo "Final audio file: $FINAL_OUTPUT"
echo "You can now listen to your enhanced movie audio with AI descriptions."