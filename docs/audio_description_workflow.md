# Audio Description Workflow

This document outlines the complete process for creating audio descriptions for video content using Video Audible.

## Automated Workflow (Recommended)

The easiest way to create audio descriptions is to use our all-in-one workflow script:

```bash
./movie_audio_workflow.sh path/to/video.mp4
```

This interactive script will guide you through all steps of the process:
1. Extract audio from the video
2. Identify non-voice segments
3. Help you create descriptions (with your preferred text editor)
4. Generate AI voiceovers (using ElevenLabs or your preferred service)
5. Combine everything into a final audio file
6. Optionally merge with the original video

All files will be saved in a timestamped project directory for easy organization.

## Manual Workflow

If you prefer more control over each step, you can follow the manual process below:

### 1. Extract Non-Voice Segments

First, extract segments from your video or audio file where there is no speech:

#### Using the Command Line Scripts

#### On Linux/Mac:
```bash
./extract_segments.sh path/to/video.mp4 segments.md segments_output
```

#### On Windows:
```batch
extract_segments.bat path/to/video.mp4 segments.md segments_output
```

This will:
- Extract audio from the video file
- Identify segments without speech
- Create individual audio files for each segment
- Generate a template script file (`voiceover_script.md`)

### 2. Review and Adjust Segments

After extraction, you should review the segments to ensure they're correctly identified:

1. Listen to each extracted segment in the output directory
2. Check if any segments need to be trimmed or merged
3. For trimming segments, use the included utility script:

```bash
# Usage: ./trim_segment.sh input.mp3 output.mp3 start_time duration
./trim_segment.sh segment_001.mp3 segment_001_trimmed.mp3 0.5 10.0
```

### 3. Complete the Voiceover Script

The extraction process creates a template markdown file (`voiceover_script.md`) that you need to complete.

### 4. Generate AI Voiceovers

Once you've completed the script, generate voiceovers using an AI voice service:

### Using the Included Script

```bash
# Set your API key as an environment variable
export ELEVENLABS_API_KEY="your-api-key-here"

# Generate voiceovers
python src/generate_voiceovers.py segments_output/voiceover_script.md --output-dir voiceovers
```

This script:
- Extracts descriptions from your completed script
- Calls the ElevenLabs API to generate natural-sounding voiceovers
- Saves each voiceover as an MP3 file

### Alternative Voice Services

If you prefer not to use ElevenLabs, other options include:
- Amazon Polly
- Google Text-to-Speech
- Microsoft Azure Speech Service
- Open-source options like Coqui TTS or Mozilla TTS

### 5. Combine Segments with Voiceovers

The final step is to combine the original audio segments with the voiceovers:

```bash
python src/combine_with_voiceovers.py segments_output voiceovers --output final_audio.mp3
```

This will:
- Load each segment and its corresponding voiceover
- Combine them using audio ducking (lowering the original audio during voiceovers)
- Export a single MP3 file with the complete audio description

## Tips for Quality Audio Descriptions

1. **Be objective**: Describe what you see without interpretation
2. **Be concise**: Use clear, simple language
3. **Be timely**: Ensure descriptions fit within the available time gaps
4. **Be relevant**: Focus on elements essential to understanding the content
5. **Avoid redundancy**: Don't describe what's already clear from the audio

## Troubleshooting

### Common Issues

1. **Segment extraction fails**:
   - Ensure FFmpeg is properly installed
   - Check that the video file is not corrupted
   - Try converting the video to a different format first

2. **API calls to voice service fail**:
   - Verify your API key is correct
   - Check your internet connection
   - Ensure you haven't exceeded API rate limits

3. **Final audio has timing issues**:
   - Trim voiceovers to be shorter if they overlap with speech
   - Adjust the ducking level in the combine script
   - Consider re-recording problematic voiceovers manually
