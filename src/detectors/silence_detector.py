import numpy as np
from typing import List
import torch

from .base_detector import BaseDetector, AudioSegment
from ..config import Config

class SilenceDetector(BaseDetector):
    def __init__(self):
        super().__init__()
        self.db_threshold = Config.SILENCE_DB_THRESHOLD
        self.min_duration = Config.MIN_SILENCE_DURATION

    def _calculate_db(self, audio_tensor: torch.Tensor) -> float:
        """Calculate decibel level of audio frame relative to full scale.
        
        Args:
            audio_tensor: Audio data as normalized float32 tensor (-1 to 1)
            
        Returns:
            float: Decibel level (negative value, where 0 dB is full scale)
            
        Raises:
            ValueError: If tensor is empty or contains invalid values
        """
        if audio_tensor.numel() == 0:
            raise ValueError("Empty audio tensor provided")
            
        if torch.any(torch.abs(audio_tensor) > 1.0):
            raise ValueError("Audio tensor contains values outside [-1, 1] range")
            
        # Calculate RMS value with epsilon to avoid log(0)
        rms = torch.sqrt(torch.mean(audio_tensor ** 2) + 1e-10)
        
        # Calculate dB relative to full scale and clip to minimum
        db = 20.0 * torch.log10(rms)
        return float(torch.clamp(db, min=-100.0))

    def _detect(self, audio: bytes) -> List[AudioSegment]:
        """
        Detect silence segments in audio data.
        Returns list of AudioSegment objects representing silent periods.
        """
        audio_tensor = self._bytes_to_tensor(audio)
        segments = []
        current_segment = None

        for frame, start_time in self.frame_generator(audio):
            frame_tensor = self._bytes_to_tensor(frame)
            db_level = self._calculate_db(frame_tensor)
            
            is_silence = db_level < self.db_threshold
            
            if is_silence:
                if current_segment is None:
                    current_segment = AudioSegment(
                        start_time=round(start_time, 3),  # Round to 3 decimal places
                        end_time=round(start_time + self.frame_duration_ms/1000, 3),
                        label="silence",
                        confidence=min(1.0, abs(db_level / self.db_threshold))  # Scale confidence by threshold
                    )
                else:
                    current_segment.end_time = start_time + self.frame_duration_ms/1000
            elif current_segment is not None:
                if current_segment.duration() >= self.min_duration:
                    segments.append(current_segment)
                current_segment = None

        # Handle last segment
        if current_segment is not None and current_segment.duration() >= self.min_duration:
            segments.append(current_segment)

        # Merge adjacent silence segments
        merged_segments = self.merge_adjacent_segments(
            segments,
            gap_threshold=Config.GAP_MERGE_THRESHOLD
        )

        return merged_segments
