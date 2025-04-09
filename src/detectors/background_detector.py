import numpy as np
import librosa
from typing import List
import torch

from .base_detector import BaseDetector, AudioSegment
from ..config import Config

class BackgroundDetector(BaseDetector):
    def __init__(self):
        super().__init__()
        self.threshold = Config.BACKGROUND_THRESHOLD
        self.min_duration = self.get_min_duration(Config.MIN_BACKGROUND_DURATION)

    def _calculate_background_features(self, audio_tensor: torch.Tensor) -> float:
        """
        Calculate features that characterize background sounds.
        Features used:
        - Spectral flatness (background noise tends to be more flat)
        - Spectral bandwidth (background often has wider frequency distribution)
        - Temporal stability (background tends to be more stable over time)
        """
        # Convert torch tensor to numpy array
        y = audio_tensor.numpy()
        
        # Calculate spectral flatness
        S = np.abs(librosa.stft(y, n_fft=480, hop_length=240))
        flatness = np.mean(librosa.feature.spectral_flatness(S=S))
        
        # Calculate spectral bandwidth
        bandwidth = np.mean(librosa.feature.spectral_bandwidth(y=y, sr=self.sample_rate))
        normalized_bandwidth = min(1.0, bandwidth / (self.sample_rate / 4))
        
        # Calculate temporal stability using RMS energy variance
        rms = librosa.feature.rms(y=y)[0]
        temporal_stability = 1.0 - min(1.0, np.std(rms) * 10)
        
        # Combine features
        features = np.array([
            flatness,  # Already normalized between 0 and 1
            normalized_bandwidth,
            temporal_stability
        ])
        
        # Weight the features (giving more importance to temporal stability)
        weights = np.array([0.3, 0.3, 0.4])
        return float(np.average(features, weights=weights))

    def _detect(self, audio_bytes: bytes) -> List[AudioSegment]:
        """
        Detect background sound segments in audio data.
        
        Args:
            audio_bytes: Raw audio data as bytes
            
        Returns:
            List of AudioSegment objects representing background sounds
            
        Raises:
            ValueError: If audio_bytes is empty or invalid
        """
        if not audio_bytes:
            raise ValueError("Empty audio data provided")
            
        try:
            audio_tensor = self._bytes_to_tensor(audio_bytes)
        except Exception as e:
            raise ValueError(f"Invalid audio data format: {str(e)}")
            
        segments = []
        current_segment = None

        for frame, start_time in self.frame_generator(audio_bytes):
            frame_tensor = self._bytes_to_tensor(frame)
            confidence = self._calculate_background_features(frame_tensor)
            
            is_background = confidence > self.threshold
            
            if is_background:
                if current_segment is None:
                    current_segment = AudioSegment(
                        start_time=start_time,
                        end_time=start_time + self.frame_duration_ms/1000,
                        label="background",
                        confidence=confidence
                    )
                else:
                    current_segment.end_time = start_time + self.frame_duration_ms/1000
                    # Update confidence as rolling average
                    current_segment.confidence = (
                        current_segment.confidence + confidence
                    ) / 2
            elif current_segment is not None:
                if current_segment.duration() >= self.min_duration:
                    segments.append(current_segment)
                current_segment = None

        # Handle last segment
        if current_segment is not None and current_segment.duration() >= self.min_duration:
            segments.append(current_segment)

        # Merge adjacent background segments
        merged_segments = self.merge_adjacent_segments(
            segments, 
            gap_threshold=Config.GAP_MERGE_THRESHOLD
        )

        return merged_segments

    @staticmethod
    def is_background_segment(segment: AudioSegment) -> bool:
        """Helper method to check if a segment is a background sound segment"""
        return segment.label == "background"
