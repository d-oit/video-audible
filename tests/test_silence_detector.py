import pytest
import numpy as np
import torch
from src.detectors.silence_detector import SilenceDetector
from src.config import Config
from src.detectors.base_detector import AudioSegment

class TestSilenceDetector:
    @pytest.fixture
    def detector(self):
        return SilenceDetector()

    def create_audio_data(self, amplitudes, sample_rate=None):
        """Helper to create test audio data"""
        if sample_rate is None:
            sample_rate = Config.SAMPLE_RATE
        samples = np.repeat(amplitudes, sample_rate // len(amplitudes))
        return samples.astype(np.int16).tobytes()

    def test_calculate_db(self, detector):
        # Test silence (-inf dB)
        silence = torch.zeros(1000, dtype=torch.float32)
        assert detector._calculate_db(silence) == -100.0

        # Test full scale (0 dB)
        full_scale = torch.ones(1000, dtype=torch.float32)
        assert detector._calculate_db(full_scale) == pytest.approx(0.0, abs=0.1)

        # Test half scale (-6 dB)
        half_scale = torch.ones(1000, dtype=torch.float32) * 0.5
        assert detector._calculate_db(half_scale) == pytest.approx(-6.0, abs=0.1)

        # Test very small values
        tiny = torch.ones(1000, dtype=torch.float32) * 1e-10
        assert detector._calculate_db(tiny) == -100.0  # Should clip to minimum

    def test_calculate_db_invalid_input(self, detector):
        # Test empty tensor
        with pytest.raises(ValueError):
            detector._calculate_db(torch.tensor([]))

        # Test negative values
        negative = torch.ones(1000, dtype=torch.float32) * -1
        with pytest.raises(ValueError):
            detector._calculate_db(negative)

    def test_detect_continuous_silence(self, detector):
        # Create 1 second of silence
        audio_data = np.zeros(Config.SAMPLE_RATE, dtype=np.int16).tobytes()
        
        segments = detector.detect(audio_data)
        assert len(segments) == 1
        assert segments[0].label == "silence"
        assert segments[0].start_time == pytest.approx(0.0)
        assert segments[0].end_time == pytest.approx(1.0)
        assert segments[0].confidence > 0.9  # Should be very confident about silence

    def test_detect_no_silence(self, detector):
        # Create 1 second of loud audio
        loud_signal = np.ones(Config.SAMPLE_RATE, dtype=np.int16) * 16384  # Half full-scale
        segments = detector.detect(loud_signal.tobytes())
        assert len(segments) == 0

    def test_detect_alternating_silence(self, detector):
        # Create alternating pattern of 0.2s silence and 0.2s sound
        pattern = np.concatenate([
            np.zeros(int(Config.SAMPLE_RATE * 0.2)),  # silence
            np.ones(int(Config.SAMPLE_RATE * 0.2)) * 16384,  # sound
            np.zeros(int(Config.SAMPLE_RATE * 0.2)),  # silence
            np.ones(int(Config.SAMPLE_RATE * 0.2)) * 16384,  # sound
        ])
        
        segments = detector.detect(pattern.astype(np.int16).tobytes())
        
        # Should detect two silence segments if they meet minimum duration
        if Config.MIN_SILENCE_DURATION <= 0.2:
            assert len(segments) > 0
            for segment in segments:
                assert segment.label == "silence"
                assert segment.duration() >= Config.MIN_SILENCE_DURATION

    def test_minimum_duration_filter(self, detector):
        # Create pattern with short silence (below minimum duration)
        short_silence_duration = Config.MIN_SILENCE_DURATION / 2
        pattern = np.concatenate([
            np.ones(int(Config.SAMPLE_RATE * 0.2)) * 16384,  # sound
            np.zeros(int(Config.SAMPLE_RATE * short_silence_duration)),  # short silence
            np.ones(int(Config.SAMPLE_RATE * 0.2)) * 16384,  # sound
        ])
        
        segments = detector.detect(pattern.astype(np.int16).tobytes())
        assert len(segments) == 0  # Short silence should be filtered out

    def test_segment_merging(self, detector):
        # Create pattern with two silence segments separated by short noise
        pattern = np.concatenate([
            np.zeros(int(Config.SAMPLE_RATE * 0.3)),  # silence
            np.ones(int(Config.SAMPLE_RATE * 0.1)) * 16384,  # short sound
            np.zeros(int(Config.SAMPLE_RATE * 0.3)),  # silence
        ])
        
        segments = detector.detect(pattern.astype(np.int16).tobytes())
        
        # If gap is less than GAP_MERGE_THRESHOLD, segments should be merged
        if Config.GAP_MERGE_THRESHOLD >= 0.1:
            assert len(segments) == 1
            assert segments[0].duration() == pytest.approx(0.7, abs=0.1)
        else:
            assert len(segments) == 2

    def test_confidence_calculation(self, detector):
        # Create test data with varying amplitude levels
        pattern = np.concatenate([
            np.zeros(int(Config.SAMPLE_RATE * 0.3)),  # perfect silence
            np.ones(int(Config.SAMPLE_RATE * 0.3)) * 100,  # very quiet
            np.ones(int(Config.SAMPLE_RATE * 0.3)) * 1000  # moderate sound
        ])
        
        segments = detector.detect(pattern.astype(np.int16).tobytes())
        
        # Perfect silence should have highest confidence
        silence_segments = [s for s in segments if s.start_time < 0.3]
        if silence_segments:
            assert silence_segments[0].confidence > 0.95
            
        # Very quiet sections should have lower but still high confidence
        quiet_segments = [s for s in segments if 0.3 <= s.start_time < 0.6]
        if quiet_segments:
            assert quiet_segments[0].confidence > 0.7

    def test_detector_disabled(self, detector):
        audio_data = np.zeros(Config.SAMPLE_RATE, dtype=np.int16).tobytes()
        
        # Test enabled (default)
        segments = detector.detect(audio_data)
        assert len(segments) > 0
        
        # Test disabled
        detector.enabled = False
        segments = detector.detect(audio_data)
        assert len(segments) == 0

    def test_invalid_audio_data(self, detector):
        with pytest.raises(ValueError):
            detector.detect(b"invalid audio data")

    def test_sample_rate_validation(self, detector):
        # Create audio data with incorrect sample rate
        wrong_rate = Config.SAMPLE_RATE * 2
        audio_data = self.create_audio_data([0], sample_rate=wrong_rate)
        
        segments = detector.detect(audio_data)
        # Should still process but might affect segment timing
        if len(segments) > 0:
            assert segments[0].start_time >= 0
            assert segments[0].end_time <= len(audio_data) / (2 * Config.SAMPLE_RATE)