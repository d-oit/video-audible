import os
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple

from .audio_pipeline import AudioPipeline
from .detectors.base_detector import AudioSegment
from .logger import setup_logger

logger = setup_logger()

class MovieSegmentExtractor:
    def __init__(self):
        self.pipeline = AudioPipeline()

    def identify_movie_segments(self, audio_path: str) -> List[Dict[str, Any]]:
        """
        Identify movie-like segments from audio file.

        Args:
            audio_path: Path to the audio file

        Returns:
            List of movie segments with start/end times
        """
        logger.info(f"Analyzing audio file: {audio_path}")

        # Extract audio data
        audio_data, sample_rate = self.pipeline.extract_audio(audio_path)

        # Process audio with all detectors
        results = self.pipeline.process_audio(audio_data, sample_rate)

        # Identify movie segments (non-silence areas with either speech or music)
        movie_segments = []

        # Get speech and music segments
        # Filter out 'duration' field which is not accepted by AudioSegment constructor
        def create_segment(seg_dict):
            # Create a copy of the dictionary without the 'duration' field
            filtered_dict = {k: v for k, v in seg_dict.items() if k != 'duration'}
            return AudioSegment(**filtered_dict)

        speech_segments = [create_segment(seg) for seg in results["speech"]]
        music_segments = [create_segment(seg) for seg in results["music"]]
        silence_segments = [create_segment(seg) for seg in results["silence"]]

        # Combine speech and music segments
        content_segments = speech_segments + music_segments
        content_segments.sort(key=lambda x: x.start_time)

        # Merge adjacent content segments
        merged_segments = self.pipeline.silence_detector.merge_adjacent_segments(
            content_segments,
            gap_threshold=2.0  # Merge segments with gaps less than 2 seconds
        )

        # Convert to dictionary format
        for segment in merged_segments:
            movie_segments.append({
                "start_time": segment.start_time,
                "end_time": segment.end_time,
                "duration": segment.duration(),
                "type": segment.label
            })

        return movie_segments

    def extract_segments(self, audio_path: str, segments: List[Dict[str, Any]], output_dir: str) -> List[str]:
        """
        Extract identified segments to separate files.

        Args:
            audio_path: Path to the audio file
            segments: List of segment dictionaries
            output_dir: Directory to save extracted segments

        Returns:
            List of paths to extracted segment files
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        extracted_files = []

        for i, segment in enumerate(segments):
            output_file = output_dir / f"segment_{i+1:03d}.mp3"

            # Use existing extraction function
            from extract_segments import extract_audio_segment
            success = extract_audio_segment(
                audio_path,
                segment["start_time"],
                segment["end_time"],
                str(output_file)
            )

            if success:
                extracted_files.append(str(output_file))
                logger.info(f"Extracted segment {i+1}/{len(segments)} to {output_file}")

        return extracted_files

    def prepare_for_voiceover(self, segments: List[Dict[str, Any]], output_path: str) -> None:
        """
        Generate a script file for AI voiceover integration.

        Args:
            segments: List of segment dictionaries
            output_path: Path to save the script file
        """
        with open(output_path, "w") as f:
            f.write("# Movie Segments for AI Voiceover\n\n")

            for i, segment in enumerate(segments):
                f.write(f"## Segment {i+1}\n")
                f.write(f"- Start: {self._format_time(segment['start_time'])}\n")
                f.write(f"- End: {self._format_time(segment['end_time'])}\n")
                # Calculate duration if not provided
                duration = segment.get('duration', segment['end_time'] - segment['start_time'])
                f.write(f"- Duration: {duration:.2f} seconds\n")
                f.write(f"- Type: {segment['type']}\n")
                f.write("- Description: [AI to generate description of this scene]\n\n")

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds as MM:SS.ms"""
        minutes = int(seconds // 60)
        seconds_remainder = seconds % 60
        return f"{minutes:02d}:{seconds_remainder:06.3f}"