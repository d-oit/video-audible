# Video Audible

## Overview
Video Audible is a project designed to convert video content into audible formats. This tool aims to make video content accessible to visually impaired individuals by providing audio descriptions and transcriptions.

## Features

- **Video to Audio Conversion**: Converts video files into audio files.
  - Direct MP4 to MP3 extraction
  - Batch processing support
- **Transcription**: Generates text transcriptions of video content.
- **Audio Descriptions**: Provides audio descriptions for visual content.

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

2. Clone the repository:
   ```bash
   git clone https://github.com/d-oit/video-audible.git
   ```

3. Navigate to the project directory:
   ```bash
   cd video-audible
   ```

4. Install the required dependencies:
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

1. Place your video file in the `input` directory.
2. Run the conversion script:
   ```bash
   python src/audio_pipeline.py
   ```
3. The converted audio file will be saved in the `output` directory.

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

## Configuration

You can configure the tool by modifying the `config.json` file. The configuration options include:

- `input_directory`: The directory where input video files are stored.
- `output_directory`: The directory where output audio files will be saved.
- `transcription_enabled`: Enable or disable transcription.
- `audio_description_enabled`: Enable or disable audio descriptions.

## License

This project is licensed under the Apache License 2.0. See the `LICENSE` file for more details.
