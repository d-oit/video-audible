import sys
import subprocess

# Try importing required packages, install if missing
try:
    # Import directly from moviepy instead of moviepy.editor
    import moviepy
    from moviepy.video.io.VideoFileClip import VideoFileClip
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    # Create an alias for backward compatibility
    mpy = moviepy
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install",
                         "moviepy", "numpy", "scipy", "torch", "librosa"])
    import moviepy
    from moviepy.video.io.VideoFileClip import VideoFileClip
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    mpy = moviepy

from .audio_pipeline import AudioPipeline
from .config import Config
from .logger import setup_logger

__all__ = ['AudioPipeline', 'Config', 'setup_logger', 'mpy', 'VideoFileClip', 'AudioFileClip']
