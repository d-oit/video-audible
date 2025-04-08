import pytest
import numpy as np
import torch
import librosa
from unittest.mock import patch, Mock
from src.detectors.background_detector import BackgroundDetector
from src.detectors.base_detector import AudioSegment
from src.config import Config

class TestBackgroundDetector:
    @pytest.fixture
    def mock_librosa(self):
        with patch('librosa.stft') as mock_stft, \
             patch('librosa.feature.spectral_flatness') as mock_flatness, \
             patch('librosa.feature.spectral_bandwidth') as mock_bandwidth, \
             patch('librosa.feature.rms') as mock_rms:
            
            # Set up mock returns
            mock_stft.return_value = np.ones((100, 100))
            mock_flatness.return_value = np.array([0.5])  # Mid-range flatness
            mock_bandwidth.return_value = np.array([Config.SAMPLE_RATE / 8])  # Mid-range bandwidth
            mock_rms.return_value = np.array([[0.5, 0.5, 0.5]])  # Stable RMS
            
            yield {
                'stft': mock_stft,
                'flatness': mock_flatness,
                'bandwidth': mock_bandwidth,
                'rms': mock_rms
            }

    @pytest.fixture
    def detector(self):
        return BackgroundDetector()

    def create_audio_data(self, duration_seconds=1.0):
        """Helper to create test audio data"""
        samples = np.zeros(int(Config.SAMPLE_RATE * duration_seconds), dtype=np.int16)
        return samples.tobytes()

    def test_calculate_background_features(self, detector, mock_librosa):
        audio_tensor = torch.zeros(1000, dtype=torch.float32)
        confidence = detector._calculate_background_features(audio_tensor)
        
        assert 0 <= confidence <= 1  # Confidence should be normalized
        assert mock_librosa['stft'].called
        assert mock_librosa['flatness'].called
        assert mock_librosa['bandwidth'].called
        assert mock_librosa['rms'].called

    def test_feature_weighting(self, detector, mock_librosa):
        # Test if features are weighted correctly
        mock_librosa['flatness'].return_value = np.array([1.0])  # Max flatness
        mock_librosa['bandwidth'].return_value = np.array([Config.SAMPLE_RATE / 4])  # Max bandwidth
        mock_librosa['rms'].return_value = np.array([[0.5, 0.5, 0.5]])  # Perfect stability
        
        audio_tensor = torch.zeros(1000, dtype=torch.float32)
        confidence = detector._calculate_background_features(audio_tensor)
        
        # With all features at maximum and weights [0.3, 0.3, 0.4]
        assert confidence == pytest.approx(1.0)

    def test_high_confidence_background_detection(self, detector, mock_librosa):
        # Mock characteristics of typical background noise
        mock_librosa['flatness'].return_value = np.array([0.8])  # High flatness
        mock_librosa['bandwidth'].return_value = np.array([Config.SAMPLE_RATE / 5])  # Wide bandwidth
        mock_librosa['rms'].return_value = np.array([[0.5, 0.51, 0.49]])  # Very stable
        
        audio_data = self.create_audio_data(2.0)
        segments = detector.detect(audio_data)
        
        assert len(segments) > 0
        assert all(segment.label == "background" for segment in segments)
        assert all(segment.confidence > detector.threshold for segment in segments)

    def test_low_confidence_no_detection(self, detector, mock_librosa):
        # Mock characteristics unlike background noise
        mock_librosa['flatness'].return_value = np.array([0.1])  # Low flatness
        mock_librosa['bandwidth'].return_value = np.array([Config.SAMPLE_RATE / 20])  # Narrow bandwidth
        mock_librosa['rms'].return_value = np.array([[0.1, 0.9, 0.1]])  # Unstable
        
        audio_data = self.create_audio_data()
        segments = detector.detect(audio_data)
        
        assert len(segments) == 0  # Should not detect background

    def test_minimum_duration_filter(self, detector, mock_librosa):
        # Mock medium-high confidence values
        mock_librosa['flatness'].return_value = np.array([0.7])
        mock_librosa['bandwidth'].return_value = np.array([Config.SAMPLE_RATE / 6])
        mock_librosa['rms'].return_value = np.array([[0.5, 0.52, 0.51]])
        
        # Create audio shorter than minimum duration
        short_duration = Config.MIN_BACKGROUND_DURATION / 2
        audio_data = self.create_audio_data(short_duration)
        segments = detector.detect(audio_data)
        
        assert len(segments) == 0  # Should be filtered out

    def test_temporal_stability_impact(self, detector, mock_librosa):
        # Test how temporal stability affects confidence
        unstable_rms = np.array([[0.1, 0.9, 0.1, 0.9]])  # Highly variable
        stable_rms = np.array([[0.5, 0.51, 0.49, 0.5]])  # Very stable
        
        mock_librosa['flatness'].return_value = np.array([0.5])
        mock_librosa['bandwidth'].return_value = np.array([Config.SAMPLE_RATE / 8])
        
        # Test with unstable RMS
        mock_librosa['rms'].return_value = unstable_rms
        audio_tensor = torch.zeros(1000, dtype=torch.float32)
        unstable_confidence = detector._calculate_background_features(audio_tensor)
        
        # Test with stable RMS
        mock_librosa['rms'].return_value = stable_rms
        stable_confidence = detector._calculate_background_features(audio_tensor)
        
        assert stable_confidence > unstable_confidence

    def test_merge_adjacent_segments(self, detector, mock_librosa):
        # Mock consistent medium-high confidence
        mock_librosa['flatness'].return_value = np.array([0.7])
        mock_librosa['bandwidth'].return_value = np.array([Config.SAMPLE_RATE / 6])
        mock_librosa['rms'].return_value = np.array([[0.5, 0.52, 0.51]])
        
        # Create audio long enough for multiple segments
        audio_data = self.create_audio_data(3.0)
        segments = detector.detect(audio_data)
        
        if len(segments) >= 2:
            # Check if segments were properly merged based on GAP_MERGE_THRESHOLD
            for i in range(len(segments) - 1):
                gap = segments[i + 1].start_time - segments[i].end_time
                assert gap > Config.GAP_MERGE_THRESHOLD

    def test_confidence_rolling_average(self, detector, mock_librosa):
        # Mock changing confidence values
        confidences = [0.6, 0.7, 0.8]  # Increasing confidence
        mock_calls = 0
        
        def varying_flatness(*args, **kwargs):
            nonlocal mock_calls
            if mock_calls < len(confidences):
                val = confidences[mock_calls]
                mock_calls += 1
                return np.array([val])
            return np.array([0.0])
            
        mock_librosa['flatness'].side_effect = varying_flatness
        
        audio_data = self.create_audio_data(1.0)
        segments = detector.detect(audio_data)
        
        if len(segments) > 0:
            # Final confidence should be somewhere between min and max confidence values
            assert min(confidences) <= segments[0].confidence <= max(confidences)

    def test_is_background_segment(self):
        background_segment = AudioSegment(0.0, 1.0, "background", 0.9)
        speech_segment = AudioSegment(0.0, 1.0, "speech", 0.9)
        
        assert BackgroundDetector.is_background_segment(background_segment) is True
        assert BackgroundDetector.is_background_segment(speech_segment) is False