import pytest
import torch
import numpy as np
from unittest.mock import patch, Mock
from src.detectors.speech_detector import SpeechDetector
from src.detectors.base_detector import AudioSegment
from src.config import Config

class TestSpeechDetector:
    @pytest.fixture
    def mock_silero_model(self):
        with patch('torch.hub.load') as mock_load:
            model = Mock()
            utils = [Mock()]  # get_speech_timestamps function
            mock_load.return_value = (model, utils)
            yield model, utils[0]

    @pytest.fixture
    def detector(self, mock_silero_model):
        return SpeechDetector()

    def create_audio_data(self, duration_seconds=1.0):
        """Helper to create test audio data"""
        samples = np.zeros(int(Config.SAMPLE_RATE * duration_seconds), dtype=np.int16)
        return samples.tobytes()

    def test_model_initialization(self, mock_silero_model):
        model, _ = mock_silero_model
        detector = SpeechDetector()
        assert detector.model == model
        assert detector.threshold == Config.SPEECH_THRESHOLD
        assert detector.min_duration == Config.MIN_SPEECH_DURATION

    def test_model_initialization_failure(self):
        with patch('torch.hub.load', side_effect=Exception("Failed to load model")):
            with pytest.raises(Exception, match="Failed to load model"):
                SpeechDetector()

    def test_detect_no_speech(self, detector, mock_silero_model):
        _, get_timestamps = mock_silero_model
        get_timestamps.return_value = []  # No speech detected
        
        audio_data = self.create_audio_data()
        segments = detector.detect(audio_data)
        
        assert len(segments) == 0

    def test_detect_single_speech_segment(self, detector, mock_silero_model):
        _, get_timestamps = mock_silero_model
        # Mock a single speech segment from 0.5s to 1.5s
        get_timestamps.return_value = [{
            'start': int(0.5 * Config.SAMPLE_RATE),
            'end': int(1.5 * Config.SAMPLE_RATE)
        }]
        
        audio_data = self.create_audio_data(2.0)
        segments = detector.detect(audio_data)
        
        assert len(segments) == 1
        assert segments[0].label == "speech"
        assert segments[0].start_time == pytest.approx(0.5)
        assert segments[0].end_time == pytest.approx(1.5)
        assert segments[0].confidence > 0

    def test_minimum_duration_filter(self, detector, mock_silero_model):
        _, get_timestamps = mock_silero_model
        # Create segment shorter than minimum duration
        short_duration = Config.MIN_SPEECH_DURATION / 2
        get_timestamps.return_value = [{
            'start': 0,
            'end': int(short_duration * Config.SAMPLE_RATE)
        }]
        
        audio_data = self.create_audio_data()
        segments = detector.detect(audio_data)
        
        assert len(segments) == 0  # Should be filtered out

    def test_merge_adjacent_segments(self, detector, mock_silero_model):
        _, get_timestamps = mock_silero_model
        # Two segments with small gap
        get_timestamps.return_value = [
            {
                'start': int(0.1 * Config.SAMPLE_RATE),
                'end': int(0.5 * Config.SAMPLE_RATE)
            },
            {
                'start': int(0.6 * Config.SAMPLE_RATE),
                'end': int(1.0 * Config.SAMPLE_RATE)
            }
        ]
        
        audio_data = self.create_audio_data(1.5)
        segments = detector.detect(audio_data)
        
        # Should merge if gap is less than GAP_MERGE_THRESHOLD
        if Config.GAP_MERGE_THRESHOLD >= 0.1:
            assert len(segments) == 1
            assert segments[0].start_time == pytest.approx(0.1)
            assert segments[0].end_time == pytest.approx(1.0)
        else:
            assert len(segments) == 2

    def test_confidence_calculation_min_duration(self, detector, mock_silero_model):
        _, get_timestamps = mock_silero_model
        # Create segment with duration exactly matching MIN_SPEECH_DURATION
        duration = Config.MIN_SPEECH_DURATION
        get_timestamps.return_value = [{
            'start': 0,
            'end': int(duration * Config.SAMPLE_RATE)
        }]
        
        audio_data = self.create_audio_data(duration + 0.5)
        segments = detector.detect(audio_data)
        
        assert len(segments) == 1
        assert segments[0].confidence == pytest.approx(1.0)

    def test_confidence_calculation_long_duration(self, detector, mock_silero_model):
        _, get_timestamps = mock_silero_model
        # Create segment with duration 2x MIN_SPEECH_DURATION
        duration = Config.MIN_SPEECH_DURATION * 2
        get_timestamps.return_value = [{
            'start': 0,
            'end': int(duration * Config.SAMPLE_RATE)
        }]
        
        audio_data = self.create_audio_data(duration + 0.5)
        segments = detector.detect(audio_data)
        
        assert len(segments) == 1
        assert segments[0].confidence == pytest.approx(1.0)  # Should cap at 1.0

    def test_is_speech_segment(self):
        speech_segment = AudioSegment(0.0, 1.0, "speech", 0.9)
        music_segment = AudioSegment(0.0, 1.0, "music", 0.9)
        
        assert SpeechDetector.is_speech_segment(speech_segment) is True
        assert SpeechDetector.is_speech_segment(music_segment) is False

    def test_model_call_parameters(self, detector, mock_silero_model):
        _, get_timestamps = mock_silero_model
        audio_data = self.create_audio_data()
        
        detector.detect(audio_data)
        
        # Verify get_speech_timestamps was called with correct parameters
        get_timestamps.assert_called_once()
        args, kwargs = get_timestamps.call_args
        assert isinstance(args[0], torch.Tensor)  # Audio tensor
        assert kwargs['sampling_rate'] == Config.SAMPLE_RATE
        assert kwargs['threshold'] == Config.SPEECH_THRESHOLD

    def test_detector_disabled(self, detector, mock_silero_model):
        _, get_timestamps = mock_silero_model
        get_timestamps.return_value = [{
            'start': int(0.5 * Config.SAMPLE_RATE),
            'end': int(1.5 * Config.SAMPLE_RATE)
        }]
        
        detector.enabled = False
        audio_data = self.create_audio_data(2.0)
        segments = detector.detect(audio_data)
        
        assert len(segments) == 0
        get_timestamps.assert_not_called()

    def test_invalid_audio_data(self, detector):
        with pytest.raises(ValueError):
            detector.detect(b"invalid audio data")