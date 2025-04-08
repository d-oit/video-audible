from abc import ABC, abstractmethod
import numpy as np
import torch
from typing import List, Tuple, Union
from ..config import Config
from ..logger import logger

class AudioSegment:
    def __init__(self, start_time: float, end_time: float, label: str, confidence: float = 1.0):
        self.start_time = start_time
        self.end_time = end_time
        self.label = label
        self.confidence = confidence

    def duration(self) -> float:
        return self.end_time - self.start_time

    def to_dict(self) -> dict:
        return {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "label": self.label,
            "confidence": self.confidence,
            "duration": self.duration()
        }

class BaseDetector(ABC):
    def __init__(self):
        self.sample_rate = Config.SAMPLE_RATE
        self.frame_duration_ms = Config.FRAME_DURATION_MS
        self.enabled = True

    def _bytes_to_tensor(self, audio_bytes: bytes) -> torch.Tensor:
        """Convert PCM bytes to normalized float32 tensor in range [-1, 1].
        
        Args:
            audio_bytes: Raw audio data as bytes
            
        Returns:
            Normalized float32 tensor
            
        Raises:
            ValueError: If audio_bytes is empty or invalid
        """
        if not audio_bytes:
            raise ValueError("Empty audio data provided")
            
        try:
            audio_np = np.frombuffer(audio_bytes, dtype=np.int16).astype(np.float32)
            if audio_np.size == 0:
                raise ValueError("No audio samples found in data")
            return torch.from_numpy(audio_np / 32768.0)  # Normalize to [-1, 1]
        except Exception as e:
            raise ValueError(f"Failed to convert audio bytes to tensor: {str(e)}")

    def _get_audio_bytes(self, audio_data: Union[np.ndarray, bytes]) -> bytes:
        """Convert audio data to bytes for processing.
        
        Args:
            audio_data: Either numpy array or raw bytes
            
        Returns:
            Audio data as bytes
        """
        if isinstance(audio_data, np.ndarray):
            return audio_data.tobytes()
        elif isinstance(audio_data, bytes):
            return audio_data
        else:
            raise ValueError(f"Unsupported audio data type: {type(audio_data)}")

    def _calculate_total_frames(self, audio_bytes: bytes) -> int:
        """Calculate total number of frames for progress tracking"""
        frame_size = int(self.sample_rate * (self.frame_duration_ms / 1000.0) * 2)
        return len(audio_bytes) // frame_size

    def frame_generator(self, audio_bytes: bytes):
        """Generate frames from audio data with progress tracking.
        
        Args:
            audio_bytes: Raw audio data as bytes
            
        Yields:
            Tuple[bytes, float]: Frame data and its start time in seconds
            
        Raises:
            ValueError: If audio_bytes is empty
        """
        # Handle empty input by returning empty generator
        if not audio_bytes:
            return
            
        # Calculate frame size in bytes (16-bit samples = 2 bytes per sample)
        n = int(self.sample_rate * (self.frame_duration_ms / 1000.0) * 2)
        if n == 0:
            logger.warning("Frame duration too small, no frames generated")
            return
            
        total_frames = self._calculate_total_frames(audio_bytes)
        current_frame = 0
        offset = 0
        
        while offset + n <= len(audio_bytes):
            frame_data = audio_bytes[offset:offset + n]
            # Calculate exact time in seconds (account for 16-bit samples)
            start_time = round(offset / (self.sample_rate * 2), 3)
            yield frame_data, start_time
            offset += n
            current_frame += 1
            
            # Log progress every 5% if we have enough frames
            if total_frames >= 20 and current_frame % (total_frames // 20) == 0:
                progress = int((current_frame / total_frames) * 100)
                logger.info(f"Processing {progress}% complete")

    def detect(self, audio_data: Union[np.ndarray, bytes]) -> List[AudioSegment]:
        """Process audio data and return segments if detector is enabled.
        
        Args:
            audio_data: Either numpy array or raw bytes of audio data
            
        Returns:
            List of detected AudioSegment objects
        """
        if not self.enabled:
            return []

        # Convert input to bytes if needed
        if isinstance(audio_data, np.ndarray):
            audio_bytes = audio_data.tobytes()
        elif isinstance(audio_data, bytes):
            audio_bytes = audio_data
        else:
            raise ValueError(f"Unsupported audio data type: {type(audio_data)}")

        total_frames = self._calculate_total_frames(audio_bytes)
        
        if total_frames > 0:
            logger.info(f"Starting audio analysis ({total_frames} frames total)")
            
        segments = self._detect(audio_bytes)
        
        if total_frames > 0:
            logger.info("Analysis completed successfully")
            
        return segments

    @abstractmethod
    def _detect(self, audio_bytes: bytes) -> List[AudioSegment]:
        """Internal detection method to be implemented by subclasses.
        
        Args:
            audio_bytes: Raw audio data as bytes
            
        Returns:
            List of detected AudioSegment objects
        """
        pass


    def merge_adjacent_segments(self, segments: List[AudioSegment],
                               gap_threshold: float = 0.5) -> List[AudioSegment]:
        """Merge segments that are close together.
        
        Args:
            segments: List of AudioSegment objects to merge
            gap_threshold: Maximum gap in seconds between segments to merge
            
        Returns:
            List of merged AudioSegment objects
        """
        if not segments:
            return []
            
        # Sort segments by start time to ensure proper merging
        segments = sorted(segments, key=lambda x: x.start_time)
        
        merged = []
        current = segments[0]

        for segment in segments[1:]:
            gap = segment.start_time - current.end_time
            if gap <= gap_threshold:
                # Update end time and recalculate confidence as weighted average
                duration1 = current.duration()
                duration2 = segment.duration()
                total_duration = duration1 + duration2
                current.end_time = max(current.end_time, segment.end_time)
                # Use duration-weighted average for confidence
                current.confidence = round(
                    (current.confidence * duration1 +
                     segment.confidence * duration2) / total_duration,
                    3  # Round to 3 decimal places for consistent comparisons
                )
            else:
                merged.append(current)
                current = segment

        merged.append(current)
        return merged
