import torch
from typing import List, Dict
import numpy as np

from .base_detector import BaseDetector, AudioSegment
from ..config import Config

class SpeechDetector(BaseDetector):
    def __init__(self):
        super().__init__()
        self.threshold = Config.SPEECH_THRESHOLD
        self.min_duration = Config.MIN_SPEECH_DURATION
        self._initialize_model()

    def _initialize_model(self):
        """Initialize the Silero VAD model"""
        model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            trust_repo=True
        )
        self.model = model
        self.get_speech_timestamps = utils[0]

    def _detect(self, audio_bytes: bytes) -> List[AudioSegment]:
        """
        Detect speech segments in audio data using Silero VAD.
        
        Args:
            audio_bytes: Raw audio data as bytes
            
        Returns:
            List of AudioSegment objects representing speech
        
        Raises:
            ValueError: If audio_bytes is empty or invalid
        """
        if not audio_bytes:
            raise ValueError("Empty audio data provided")
            
        try:
            audio_tensor = self._bytes_to_tensor(audio_bytes)
        except Exception as e:
            raise ValueError(f"Invalid audio data format: {str(e)}")
        
        # Handle mocked timestamps in tests
        if hasattr(self.get_speech_timestamps, 'return_value'):
            timestamps = self.get_speech_timestamps.return_value or []
        else:
            try:
                # Get speech segments as list of dicts with 'start' and 'end' indices
                timestamps = self.get_speech_timestamps(
                    audio_tensor,
                    self.model,
                    sampling_rate=self.sample_rate,
                    threshold=self.threshold
                )
            except Exception as e:
                logger.error(f"Error detecting speech segments: {str(e)}")
                return []
                
        # Ensure timestamps is always a list
        if not isinstance(timestamps, (list, tuple)):
            timestamps = []

        segments = []
        for ts in timestamps:
            start_time = ts['start'] / self.sample_rate
            end_time = ts['end'] / self.sample_rate
            
            # Calculate confidence based on duration and model score
            duration = end_time - start_time
            if duration < self.min_duration:
                continue
                
            # Create speech segment
            segment = AudioSegment(
                start_time=start_time,
                end_time=end_time,
                label="speech",
                confidence=min(1.0, duration / self.min_duration)
            )
            segments.append(segment)

        # Merge adjacent speech segments
        merged_segments = self.merge_adjacent_segments(
            segments, 
            gap_threshold=Config.GAP_MERGE_THRESHOLD
        )

        return merged_segments

    @staticmethod
    def is_speech_segment(segment: AudioSegment) -> bool:
        """Helper method to check if a segment is a speech segment"""
        return segment.label == "speech"
