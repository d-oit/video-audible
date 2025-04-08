import numpy as np
import librosa
from typing import List
import torch

from .base_detector import BaseDetector, AudioSegment
from ..config import Config

class MusicDetector(BaseDetector):
    def __init__(self):
        super().__init__()
        self.threshold = Config.MUSIC_THRESHOLD
        self.min_duration = Config.MIN_MUSIC_DURATION

    def _calculate_music_features(self, audio_tensor: torch.Tensor) -> float:
        """
        Calculate music-related features using librosa and return confidence score.
        Features used:
        - Spectral contrast (music tends to have higher contrast)
        - Tempo strength (music usually has strong rhythmic patterns)
        - Harmonic content (music typically has stronger harmonic structure)
        """
        # Convert torch tensor to numpy array
        y = audio_tensor.numpy()
        
        # Calculate spectral contrast
        S = np.abs(librosa.stft(y, n_fft=480, hop_length=240))
        contrast = np.mean(librosa.feature.spectral_contrast(S=S, sr=self.sample_rate))
        
        # Calculate tempo strength
        onset_env = librosa.onset.onset_strength(y=y, sr=self.sample_rate)
        tempo_score = np.max(librosa.autocorrelate(onset_env))
        
        # Calculate harmonic content
        harmonic = np.mean(librosa.feature.tonnetz(y=librosa.effects.harmonic(y), sr=self.sample_rate))
        
        # Combine and normalize features
        features = np.array([
            np.clip(contrast / 50.0, 0, 1),  # Normalize and clip spectral contrast
            np.clip(tempo_score / (np.max(onset_env) + 1e-6), 0, 1),  # Normalize tempo with epsilon
            np.clip(abs(harmonic), 0, 1)  # Clip harmonic content
        ])
        
        # Use weighted average for final confidence
        weights = np.array([0.4, 0.4, 0.2])  # Give more weight to contrast and tempo
        return float(np.clip(np.average(features, weights=weights), 0, 1))

    def _detect(self, audio_bytes: bytes) -> List[AudioSegment]:
        """
        Detect music segments in audio data.
        
        Args:
            audio_bytes: Raw audio data as bytes
            
        Returns:
            List of AudioSegment objects representing music
            
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
            confidence = self._calculate_music_features(frame_tensor)
            
            is_music = confidence > self.threshold
            
            if is_music:
                if current_segment is None:
                    current_segment = AudioSegment(
                        start_time=start_time,
                        end_time=start_time + self.frame_duration_ms/1000,
                        label="music",
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

        # Merge adjacent music segments
        merged_segments = self.merge_adjacent_segments(
            segments, 
            gap_threshold=Config.GAP_MERGE_THRESHOLD
        )

        return merged_segments

    @staticmethod
    def is_music_segment(segment: AudioSegment) -> bool:
        """Helper method to check if a segment is a music segment"""
        return segment.label == "music"
