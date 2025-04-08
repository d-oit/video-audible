import pytest
import numpy as np
import torch
from src.detectors.base_detector import AudioSegment, BaseDetector
from src.config import Config

class TestAudioSegment:
    def test_audio_segment_creation(self):
        segment = AudioSegment(1.0, 2.0, "speech", 0.8)
        assert segment.start_time == 1.0
        assert segment.end_time == 2.0
        assert segment.label == "speech"
        assert segment.confidence == 0.8

    def test_duration_calculation(self):
        segment = AudioSegment(1.0, 3.5, "music", 0.9)
        assert segment.duration() == 2.5

    def test_to_dict_conversion(self):
        segment = AudioSegment(0.5, 1.5, "silence", 0.95)
        expected = {
            "start_time": 0.5,
            "end_time": 1.5,
            "label": "silence",
            "confidence": 0.95,
            "duration": 1.0
        }
        assert segment.to_dict() == expected

class MockDetector(BaseDetector):
    def __init__(self):
        super().__init__()
        self._detect_called = False
        self._mock_segments = []

    def set_mock_segments(self, segments):
        self._mock_segments = segments

    def _detect(self, audio):
        self._detect_called = True
        return self._mock_segments

class TestBaseDetector:
    @pytest.fixture
    def detector(self):
        return MockDetector()

    def test_bytes_to_tensor_conversion(self, detector):
        # Create sample PCM data (16-bit integers)
        sample_data = np.array([0, 32767, -32768], dtype=np.int16).tobytes()
        tensor = detector._bytes_to_tensor(sample_data)
        
        assert isinstance(tensor, torch.Tensor)
        assert tensor.dtype == torch.float32
        # Check normalization to [-1, 1] range
        assert torch.allclose(tensor, torch.tensor([0.0, 1.0, -1.0], dtype=torch.float32))

    def test_frame_generator(self, detector):
        # Create 0.1 seconds of audio data at 16kHz (16-bit)
        duration_samples = int(0.1 * Config.SAMPLE_RATE)
        audio_data = np.zeros(duration_samples, dtype=np.int16).tobytes()
        
        frames = list(detector.frame_generator(audio_data))
        assert len(frames) > 0
        
        # Check that each frame has correct duration
        frame_size = int(Config.SAMPLE_RATE * (Config.FRAME_DURATION_MS / 1000.0) * 2)
        for frame, timestamp in frames[:-1]:  # Exclude last frame which might be partial
            assert len(frame) == frame_size
            
        # Verify timestamps are increasing correctly
        timestamps = [t for _, t in frames]
        assert all(t2 > t1 for t1, t2 in zip(timestamps, timestamps[1:]))
        
        # Verify first timestamp starts at 0
        assert timestamps[0] == 0.0

    def test_frame_generator_empty_audio(self, detector):
        frames = list(detector.frame_generator(bytes()))
        assert len(frames) == 0

    def test_frame_generator_short_audio(self, detector):
        # Create audio shorter than one frame
        frame_size = int(Config.SAMPLE_RATE * (Config.FRAME_DURATION_MS / 1000.0))
        short_audio = np.zeros(frame_size // 2, dtype=np.int16).tobytes()
        frames = list(detector.frame_generator(short_audio))
        assert len(frames) == 0

    def test_merge_adjacent_segments(self, detector):
        segments = [
            AudioSegment(0.0, 1.0, "speech", 0.8),
            AudioSegment(1.3, 2.0, "speech", 0.9),  # Should not merge (gap > 0.5)
            AudioSegment(2.0, 3.0, "speech", 0.7),  # Should merge with previous
        ]
        
        merged = detector.merge_adjacent_segments(segments, gap_threshold=0.5)
        assert len(merged) == 2
        assert merged[0].start_time == 0.0
        assert merged[0].end_time == 1.0
        assert merged[1].start_time == 1.3
        assert merged[1].end_time == 3.0
        assert merged[1].confidence == 0.8  # Average of 0.9 and 0.7

    def test_merge_adjacent_segments_empty_list(self, detector):
        assert detector.merge_adjacent_segments([]) == []

    def test_merge_adjacent_segments_single_segment(self, detector):
        segment = AudioSegment(0.0, 1.0, "speech", 0.8)
        merged = detector.merge_adjacent_segments([segment])
        assert len(merged) == 1
        assert merged[0] == segment

    def test_merge_segments_with_zero_gap(self, detector):
        segments = [
            AudioSegment(0.0, 1.0, "speech", 0.8),
            AudioSegment(1.0, 2.0, "speech", 0.9),  # Exactly adjacent
        ]
        merged = detector.merge_adjacent_segments(segments)
        assert len(merged) == 1
        assert merged[0].start_time == 0.0
        assert merged[0].end_time == 2.0
        assert merged[0].confidence == 0.85

    def test_detector_enabled_state(self, detector):
        # Setup mock segments
        mock_segments = [AudioSegment(0.0, 1.0, "test", 0.8)]
        detector.set_mock_segments(mock_segments)
        
        # Test enabled state (default)
        audio_data = np.zeros(1000, dtype=np.int16).tobytes()
        results = detector.detect(audio_data)
        assert len(results) == 1
        assert detector._detect_called
        
        # Test disabled state
        detector._detect_called = False
        detector.enabled = False
        results = detector.detect(audio_data)
        assert len(results) == 0
        assert not detector._detect_called

    def test_abstract_detect_method(self):
        # Verify that instantiating BaseDetector directly raises TypeError
        with pytest.raises(TypeError):
            BaseDetector()