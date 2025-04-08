# Video Audible

## Overview
Video Audible is a project designed to convert video content into audible formats. This tool aims to make video content accessible to visually impaired individuals by providing audio descriptions and transcriptions.

## Features

- **Video to Audio Conversion**: Converts video files into audio files.
  - Direct MP4 to MP3 extraction
  - Batch processing support
- **Transcription**: Generates text transcriptions of video content.
- **Audio Descriptions**: Provides audio descriptions for visual content.
- **Voice Detection**: Identifies voice segments in audio.
- **Non-Voice Segment Analysis**: Generates reports of silent or non-voice segments.

## Requirements

- Python 3.x
- FFmpeg (required for audio/video processing)
- Dependencies listed in `requirements.txt`

## Installation

To get started with Video Audible, follow these steps:

1. Install Python 3.x:
   - **Windows**: Download from [python.org](https://www.python.org/downloads/)
     - ⚠️ Important: Check "Add Python to PATH" during installation
     - After installation, you may need to disable the Python App Installer in Windows:
       1. Open Windows Settings
       2. Go to Apps > Advanced app settings > App execution aliases
       3. Turn off "python.exe" and "python3.exe"
   - **Linux/Mac**: Use your system's package manager or download from python.org

2. Install FFmpeg:
   - **Windows**: `choco install ffmpeg` (using Chocolatey)
   - **macOS**: `brew install ffmpeg` (using Homebrew)
   - **Ubuntu/Debian**: `sudo apt update && sudo apt install ffmpeg`
   - Or download from [ffmpeg.org](https://ffmpeg.org/download.html)

3. Clone the repository:
   ```bash
   git clone https://github.com/d-oit/video-audible.git
   ```

4. Navigate to the project directory:
   ```bash
   cd video-audible
   ```

5. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Quick Audio Extraction

#### Windows Users
Use the batch file:
```cmd
extract_audio.bat input.mp4 [output.mp3]
```

#### Linux/Mac Users
Use the shell script:
```bash
./extract_audio.sh input.mp4 [output.mp3]
```

Examples:
```bash
# Windows
extract_audio.bat video/movie.mp4              # Creates video/movie.mp3
extract_audio.bat video/movie.mp4 audio.mp3    # Creates audio.mp3

# Linux/Mac
./extract_audio.sh video/movie.mp4             # Creates video/movie.mp3
./extract_audio.sh video/movie.mp4 audio.mp3   # Creates audio.mp3
```

### Full Pipeline Processing

To use the complete Video Audible pipeline with all features:

```bash
# Windows/Linux/Mac
python -m src path/to/video.mp4
```

Or use the provided shell script:

```bash
# Linux/Mac
./run_pipeline.sh path/to/video.mp4

# Windows (Git Bash or similar)
./run_pipeline.sh path/to/video.mp4
```

### Complete Audio Description Workflow

For a guided, interactive workflow that takes you through all steps of creating audio descriptions:

```bash
# Linux/Mac/Windows (Git Bash)
./movie_audio_workflow.sh path/to/video.mp4
```

This all-in-one script will:
1. Extract audio from the video
2. Identify non-voice segments
3. Help you create descriptions
4. Generate AI voiceovers
5. Combine everything into a final audio file
6. Optionally merge with the original video

The processed audio and analysis reports will be saved in a timestamped project directory.

### Extract Non-Voice Segments

To analyze a video/audio file and generate a report of non-voice segments:

```bash
# Linux/Mac
./extract_segments.sh path/to/audio.mp3 [output_report.md]
```

## Configuration

### Environment Variables

The application uses environment variables for configuration. You can set these in a `.env` file:

- `ENABLE_SILENCE_DETECTOR`: Enable/disable silence detection (default: true)
- `ENABLE_SPEECH_DETECTOR`: Enable/disable speech detection (default: true)
- `ENABLE_MUSIC_DETECTOR`: Enable/disable music detection (default: true)
- `ENABLE_BACKGROUND_DETECTOR`: Enable/disable background noise detection (default: true)
- `NON_VOICE_DURATION_THRESHOLD`: Minimum duration (seconds) for non-voice segments

### Configuration File

You can also configure the tool by modifying the `config.json` file. The configuration options include:

- `input_directory`: The directory where input video files are stored.
- `output_directory`: The directory where output audio files will be saved.
- `transcription_enabled`: Enable or disable transcription.
- `audio_description_enabled`: Enable or disable audio descriptions.

## Testing

The project uses pytest for testing. To run tests:

```bash
pytest
```

For test coverage reports:

```bash
pytest --cov=src --cov-report=html
```

Coverage reports will be generated in the `htmlcov` directory.

## Troubleshooting

### Python Not Found

If you get a "Python was not found" error:
1. Make sure Python is installed and added to PATH
2. Disable Windows Python App Installer aliases (see Installation instructions)
3. Try using the full Python path: `C:\Python3x\python.exe extract_audio.py`

### Audio Extraction Failed

1. Verify the input video file exists and is readable
2. Ensure you have write permissions in the output directory
3. Check that MoviePy and its dependencies are properly installed
4. Try using an absolute path for input/output files

### FFmpeg Issues

If you encounter FFmpeg-related errors:
1. Verify FFmpeg is installed and available in your PATH
2. On Windows, you may need to restart your terminal after installing FFmpeg
3. Try reinstalling the ffmpeg-python package: `pip install --upgrade ffmpeg-python`

## License

This project is licensed under the Apache License 2.0. See the `LICENSE` file for more details.

