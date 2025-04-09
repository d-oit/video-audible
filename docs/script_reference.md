# Script Reference

This document provides detailed information about the scripts included in the Video Audible audio description workflow.

## movie_audio_workflow.sh

### Purpose
All-in-one interactive script that guides users through the complete audio description workflow.

### Usage
```bash
./movie_audio_workflow.sh path/to/video.mp4
```

### Parameters
- `path/to/video.mp4`: Path to the video file to process

### Process
1. Creates a timestamped project directory
2. Extracts audio from the video
3. Identifies non-voice segments
4. Helps you create descriptions with your preferred text editor
5. Generates AI voiceovers (using ElevenLabs)
6. Combines everything into a final audio file
7. Optionally merges with the original video

### Environment Variables
- `ELEVENLABS_API_KEY`: Your ElevenLabs API key (can also be entered interactively)
- `EDITOR`: Your preferred text editor (defaults to nano, vim, or vi if available)

### Output
- A project directory containing all intermediate files and the final output
- Segments report in markdown format
- Voiceover script template
- Individual audio segments
- AI-generated voiceovers
- Final audio file with descriptions
- Optional final video file with descriptions

## extract_segments.sh / extract_segments.bat

### Purpose
Extracts non-voice segments from a video or audio file and prepares them for audio description.

### Usage
```bash
# Linux/Mac
./extract_segments.sh input_file.mp4 output_report.md [output_directory]

# Windows
extract_segments.bat input_file.mp4 output_report.md [output_directory]
```

### Parameters
- `input_file.mp4`: Path to the video or audio file to analyze
- `output_report.md`: Path where the segment report will be saved
- `output_directory`: (Optional) Directory where extracted segments will be saved (default: "segments")

### Output
- Individual MP3 files for each non-voice segment
- A markdown report listing all segments
- A template voiceover script file

## trim_segment.sh

### Purpose
Trims an audio segment to a specific duration.

### Usage
```bash
./trim_segment.sh input.mp3 output.mp3 start_time duration
```

### Parameters
- `input.mp3`: Path to the input audio file
- `output.mp3`: Path where the trimmed audio will be saved
- `start_time`: Start time in seconds (can use decimal points)
- `duration`: Duration in seconds (can use decimal points)

### Example
```bash
./trim_segment.sh segment_001.mp3 segment_001_trimmed.mp3 0.5 10.0
```

## generate_voiceovers.py

### Purpose
Generates AI voiceovers from a completed script file.

### Usage
```bash
python src/generate_voiceovers.py script_file.md --output-dir voiceovers
```

### Parameters
- `script_file.md`: Path to the completed voiceover script
- `--output-dir`: (Optional) Directory where voiceovers will be saved (default: "voiceovers")

### Environment Variables
- `ELEVENLABS_API_KEY`: Your ElevenLabs API key

### Output
- MP3 files for each voiceover, named according to segment numbers

## combine_with_voiceovers.py

### Purpose
Combines original audio segments with AI voiceovers into a final audio file.

### Usage
```bash
python src/combine_with_voiceovers.py segments_dir voiceovers_dir --output final_audio.mp3 --fade 0.5
```

### Parameters
- `segments_dir`: Directory containing the extracted audio segments
- `voiceovers_dir`: Directory containing the generated voiceovers
- `--output`: (Optional) Path for the final audio file (default: "final_audio.mp3")
- `--fade`: (Optional) Fade duration in seconds (default: 0.5)

### Output
- A single MP3 file containing the original audio with voiceovers inserted

## merge_audio_video.py

### Purpose
Merges the final audio file with the original video.

### Usage
```bash
python merge_audio_video.py original_video.mp4 final_audio.mp3 output_video.mp4
```

### Parameters
- `original_video.mp4`: Path to the original video file
- `final_audio.mp3`: Path to the final audio file with descriptions
- `output_video.mp4`: Path where the output video will be saved

### Output
- A video file with the original visuals and the new audio track containing descriptions
