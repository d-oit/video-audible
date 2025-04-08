import json
import argparse
import numpy as np
import os
import sys
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path

from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip

# Add src directory to Python path for direct script execution
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.detectors.silence_detector import SilenceDetector
from src.detectors.speech_detector import SpeechDetector
from src.detectors.music_detector import MusicDetector
from src.detectors.background_detector import BackgroundDetector
from src.detectors.base_detector import AudioSegment
from src.config import Config
from src.logger import setup_logger

logger = setup_logger()

class AudioPipeline:
    """
    Pipeline for extracting, processing, and reporting on audio from video files.
    """

    def __init__(self) -> None:
        """
        Initialize the AudioPipeline with all detectors.
        """
        self.silence_detector = SilenceDetector()
        self.speech_detector = SpeechDetector()
        self.music_detector = MusicDetector()
        self.background_detector = BackgroundDetector()

        # Configure detectors from environment variables
        self.silence_detector.enabled = os.getenv('ENABLE_SILENCE_DETECTOR', 'true').lower() == 'true'
        self.speech_detector.enabled = os.getenv('ENABLE_SPEECH_DETECTOR', 'true').lower() == 'true'
        self.music_detector.enabled = os.getenv('ENABLE_MUSIC_DETECTOR', 'true').lower() == 'true'
        self.background_detector.enabled = os.getenv('ENABLE_BACKGROUND_DETECTOR', 'true').lower() == 'true'

        logger.info("Audio pipeline initialized with detectors configured from environment")

    def extract_audio(self, video_path: str) -> Tuple[np.ndarray, int]:
        """
        Extract audio from video file using MoviePy and return audio data and sample rate.

        Args:
            video_path (str): Path to the video file.

        Returns:
            Tuple[np.ndarray, int]: Audio data and sample rate.

        Raises:
            RuntimeError: If extraction fails.
        """
        logger.info(f"Extracting audio from video: {video_path}")
        try:
            with VideoFileClip(str(video_path)) as video:
                audio = video.audio
                if audio is None:
                    raise ValueError("Video file contains no audio track")

                audio_array = audio.to_soundarray()

                if len(audio_array.shape) > 1 and audio_array.shape[1] > 1:
                    audio_array = audio_array.mean(axis=1)

                audio_array = np.clip(audio_array * 32768, -32768, 32767)
                audio_array = audio_array.astype(np.int16)

                logger.info(f"Audio extracted successfully: shape {audio_array.shape}, {Config.SAMPLE_RATE}Hz")
                return audio_array, Config.SAMPLE_RATE

        except Exception as e:
            logger.error(f"Failed to extract audio: {str(e)}")
            raise RuntimeError(f"Failed to extract audio: {str(e)}")

    def extract_audio_to_file(self, video_path: str, output_path: str) -> None:
        """
        Extract audio from a video file and save it directly as MP3.

        Args:
            video_path (str): Path to the input video file.
            output_path (str): Path where to save the MP3 file.

        Raises:
            RuntimeError: If extraction fails.
        """
        logger.info(f"Extracting audio from video: {video_path} to {output_path}")
        try:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with VideoFileClip(str(video_path)) as video:
                if video.audio is None:
                    raise ValueError("Video file contains no audio track")

                video.audio.write_audiofile(str(output_path))

            logger.info(f"Audio extracted and saved successfully to: {output_path}")

        except Exception as e:
            logger.error(f"Failed to extract audio to file: {str(e)}")
            raise RuntimeError(f"Failed to extract audio to file: {str(e)}")

    def process_audio(self, audio_array: np.ndarray, sample_rate: int) -> Dict[str, List[Dict]]:
        """
        Process audio data through all enabled detectors and return combined results.

        Args:
            audio_array (np.ndarray): Audio data.
            sample_rate (int): Sample rate.

        Returns:
            Dict[str, List[Dict]]: Detection results.
        """
        logger.info(f"Incoming sample_rate argument: {sample_rate}")
        logger.info(f"Existing self.sample_rate attribute: {getattr(self, 'sample_rate', 'Not set')}")
        self.sample_rate = sample_rate
        logger.info("Starting audio analysis")
        logger.info("Detector status:")
        logger.info(f"  - Silence detection: {'enabled' if self.silence_detector.enabled else 'disabled'}")
        logger.info(f"  - Speech detection: {'enabled' if self.speech_detector.enabled else 'disabled'}")
        logger.info(f"  - Music detection: {'enabled' if self.music_detector.enabled else 'disabled'}")
        logger.info(f"  - Background detection: {'enabled' if self.background_detector.enabled else 'disabled'}")

        import scipy.signal
        if sample_rate not in (8000, 16000):
            logger.info(f"Resampling audio from {self.sample_rate}Hz to 16000Hz for VAD compatibility")
            num_samples = int(audio_array.shape[0] * 16000 / sample_rate)
            audio_array = audio_array.astype(np.float32) / 32768.0
            audio_array = librosa.resample(
                audio_array,
                orig_sr=sample_rate,
                target_sr=16000,
                res_type='kaiser_best',
                fix=True
            )
            audio_array = (audio_array * 32768.0).astype(np.int16)
            sample_rate = 16000

        silence_segments = self.silence_detector.detect(audio_array)
        speech_segments = self.speech_detector.detect(audio_array)
        music_segments = self.music_detector.detect(audio_array)
        background_segments = self.background_detector.detect(audio_array)

        results = {
            "silence": [seg.to_dict() for seg in silence_segments],
            "speech": [seg.to_dict() for seg in speech_segments],
            "music": [seg.to_dict() for seg in music_segments],
            "background": [seg.to_dict() for seg in background_segments]
        }

        return results

    def generate_report(self, results: Dict[str, List[Dict]], output_path: str) -> None:
        """
        Generate a detailed Markdown report of the audio analysis.

        Args:
            results (Dict[str, List[Dict]]): Detection results.
            output_path (str): Path to save the report.
        """
        logger.info(f"Generating report at: {output_path}")

        def format_time(seconds: float) -> str:
            minutes = int(seconds // 60)
            seconds = int(seconds % 60)
            return f"{minutes:02d}:{seconds:02d}"

        with open(output_path, "w") as f:
            f.write("# Audio Analysis Report\n\n")

            for label, segments in results.items():
                f.write(f"## {label.title()} Segments\n\n")
                if not segments:
                    f.write("No segments detected.\n\n")
                    continue

                f.write("| Start | End | Duration | Confidence |\n")
                f.write("|-------|-----|----------|------------|\n")

                total_duration = 0
                for segment in segments:
                    start = format_time(segment["start_time"])
                    end = format_time(segment["end_time"])
                    duration = segment["duration"]
                    confidence = f"{segment['confidence']:.2f}"

                    f.write(f"| {start} | {end} | {duration:.2f}s | {confidence} |\n")
                    total_duration += duration

                f.write(f"\nTotal {label} duration: {total_duration:.2f} seconds\n\n")

            f.write("\n## Summary\n\n")
            for label, segments in results.items():
                total_duration = sum(seg["duration"] for seg in segments)
                f.write(f"- Total {label} time: {total_duration:.2f} seconds\n")

    def process_and_report(self, video_path: str, output_dir: str = "reports") -> Tuple[str, str]:
        """
        Process video file, extract audio, analyze it, and generate reports.

        Args:
            video_path (str): Path to the video file.
            output_dir (str): Directory to save reports.

        Returns:
            Tuple[str, str]: Paths to JSON and Markdown reports.

        Raises:
            FileNotFoundError: If video file not found.
            ValueError: If unsupported video format.
            RuntimeError: If processing fails.
        """
        video_path = Path(os.path.normpath(os.path.abspath(video_path)))

        if not video_path.exists():
            logger.error(f"Video file not found: {video_path}")
            raise FileNotFoundError(f"Video file not found: {video_path}")

        if video_path.suffix.lower() not in ['.mp4', '.mkv', '.avi', '.mov']:
            raise ValueError(f"Unsupported video format: {video_path.suffix}. Supported formats: .mp4, .mkv, .avi, .mov")

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        base_name = video_path.stem

        try:
            logger.info(f"Processing video: {video_path}")
            print(f"\n--- Starting processing of {base_name} ---")

            print("Step 1/3: Extracting audio...")
            audio_data, sample_rate = self.extract_audio(video_path)

            print("Step 2/3: Analyzing audio for voice segments...")
            results = self.process_audio(audio_data, sample_rate)

            print("Step 3/3: Generating reports...")
            json_path = output_dir / f"{base_name}_analysis.json"
            with open(json_path, "w") as f:
                json.dump(results, f, indent=2)
            logger.info(f"JSON analysis saved to: {json_path}")

            md_path = output_dir / f"{base_name}_report.md"
            self.generate_report(results, str(md_path))
            logger.info(f"Markdown report saved to: {md_path}")

            print(f"\n--- Processing complete! ---")
            print(f"Reports saved to: {output_dir}")

            return str(json_path), str(md_path)

        except Exception as e:
            logger.error(f"Processing failed: {str(e)}")
            raise
