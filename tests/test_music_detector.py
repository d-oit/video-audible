import pytest
import numpy as np
import torch
import librosa
from unittest.mock import patch, Mock
from src.detectors.music_detector import MusicDetector
from src.detectors.base_detector import AudioSegment
from src.config import Config

class TestMusicDetector:
    @pytest.fixture
    def mock_librosa(self):
        with patch('librosa.stft') as mock_stft, \
             patch('librosa.feature.spectral_contrast') as mock_contrast, \
             patch('librosa.onset.onset_strength') as mock_onset, \
             patch('librosa.autocorrelate') as mock_autocorr, \
             patch('librosa.feature.tonnetz') as mock_tonnetz, \
             patch('librosa.effects.harmonic') as mock_harmonic:
            
            # Set up mock returns
            mock_stft.return_value = np.ones((100, 100))
            mock_contrast.return_value = np.array([[25.0]])  # Mid-range contrast
            mock_onset.return_value = np.array([1.0, 0.5, 1.0])  # Simple rhythm pattern
            mock_autocorr.return_value = np.array([1.0, 0.8, 0.6])
            mock_tonnetz.return_value = np.array([[0.5]])  # Mid-range harmonic content
            mock_harmonic.return_value = np.ones(1000)
            
            yield {
                'stft': mock_stft,
                'contrast': mock_contrast,
                'onset': mock_onset,
                'autocorr': mock_autocorr,
                'tonnetz': mock_tonnetz,
                'harmonic': mock_harmonic
            }

    @pytest.fixture
    def detector(self):
        return MusicDetector()

    def create_audio_data(self, duration_seconds=1.0):
        """Helper to create test audio data"""
        samples = np.zeros(int(Config.SAMPLE_RATE * duration_seconds), dtype=np.int16)
        return samples.tobytes()

    def test_calculate_music_features(self, detector, mock_librosa):
        audio_tensor = torch.zeros(1000, dtype=torch.float32)
        confidence = detector._calculate_music_features(audio_tensor)
        
        assert 0 <= confidence <= 1  # Confidence should be normalized
        assert mock_librosa['stft'].called
        assert mock_librosa['contrast'].called
        assert mock_librosa['onset'].called
        assert mock_librosa['tonnetz'].called

    def test_high_confidence_music_detection(self, detector, mock_librosa):
        # Mock high music confidence values
        mock_librosa['contrast'].return_value = np.array([[40.0]])  # High contrast
        mock_librosa['autocorr'].return_value = np.array([1.0, 0.9, 0.8])  # Strong rhythm
        mock_librosa['tonnetz'].return_value = np.array([[0.8]])  # Strong harmonics
        
        audio_data = self.create_audio_data(2.0)
        segments = detector.detect(audio_data)
        
        assert len(segments) > 0
        assert all(segment.label == "music" for segment in segments)
        assert all(segment.confidence > detector.threshold for segment in segments)

    def test_low_confidence_no_detection(self, detector, mock_librosa):
        # Mock low music confidence values
        mock_librosa['contrast'].return_value = np.array([[5.0]])  # Low contrast
        mock_librosa['autocorr'].return_value = np.array([0.1, 0.1, 0.1])  # Weak rhythm
        mock_librosa['tonnetz'].return_value = np.array([[0.1]])  # Weak harmonics
        
        audio_data = self.create_audio_data()
        segments = detector.detect(audio_data)
        
        assert len(segments) == 0  # Should not detect music

    def test_minimum_duration_filter(self, detector, mock_librosa):
        # Mock medium-high confidence values
        mock_librosa['contrast'].return_value = np.array([[30.0]])
        mock_librosa['autocorr'].return_value = np.array([0.8, 0.7, 0.6])
        mock_librosa['tonnetz'].return_value = np.array([[0.6]])
        
        # Create audio shorter than minimum duration
        short_duration = Config.MIN_MUSIC_DURATION / 2
        audio_data = self.create_audio_data(short_duration)
        segments = detector.detect(audio_data)
        
        assert len(segments) == 0  # Should be filtered out

    def test_merge_adjacent_segments(self, detector, mock_librosa):
        # Mock consistent medium-high confidence
        mock_librosa['contrast'].return_value = np.array([[30.0]])
        mock_librosa['autocorr'].return_value = np.array([0.8, 0.7, 0.6])
        mock_librosa['tonnetz'].return_value = np.array([[0.6]])
        
        # Create audio long enough for multiple segments
        audio_data = self.create_audio_data(3.0)
        segments = detector.detect(audio_data)
        
        if len(segments) >= 2:
            # Check if segments were properly merged based on GAP_MERGE_THRESHOLD
            for i in range(len(segments) - 1):
                gap = segments[i + 1].start_time - segments[i].end_time
                assert gap > Config.GAP_MERGE_THRESHOLD

    def test_confidence_averaging(self, detector, mock_librosa):
        # Mock changing confidence values
        confidences = [0.7, 0.8, 0.9]  # Increasing confidence
        mock_calls = 0
        
        def varying_confidence(*args, **kwargs):
            nonlocal mock_calls
            if mock_calls < len(confidences):
                val = confidences[mock_calls]
                mock_calls += 1
                return np.array([[val * 50]])  # Scale to match spectral contrast range
            return np.array([[0.0]])
            
        mock_librosa['contrast'].side_effect = varying_confidence
        
        audio_data = self.create_audio_data(1.0)
        segments = detector.detect(audio_data)
        
        if len(segments) > 0:
            # Final confidence should be somewhere between min and max confidence values
            assert min(confidences) <= segments[0].confidence <= max(confidences)

    def test_is_music_segment(self):
        music_segment = AudioSegment(0.0, 1.0, "music", 0.9)
        speech_segment = AudioSegment(0.0, 1.0, "speech", 0.9)
        
        assert MusicDetector.is_music_segment(music_segment) is True
        assert MusicDetector.is_music_segment(speech_segment) is False

    def test_feature_normalization(self, detector, mock_librosa):
        # Test with extreme values to verify normalization
        mock_librosa['contrast'].return_value = np.array([[100.0]])  # Very high contrast
        mock_librosa['autocorr'].return_value = np.array([2.0])  # Strong autocorrelation
        mock_librosa['tonnetz'].return_value = np.array([[1.5]])  # High harmonic content
        
        audio_tensor = torch.zeros(1000, dtype=torch.float32)
        confidence = detector._calculate_music_features(audio_tensor)
        
        assert 0 <= confidence <= 1  # Should be normalized regardless of input values