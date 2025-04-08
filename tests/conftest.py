import pytest
import numpy as np
import torch
from src.detectors.base_detector import AudioSegment
from src.config import Config

@pytest.fixture
def sample_audio_data():
    """Create sample PCM audio data for testing"""
    duration_seconds = 1.0
    samples = np.zeros(int(Config.SAMPLE_RATE * duration_seconds), dtype=np.int16)
    return samples.tobytes()

@pytest.fixture
def sample_audio_segment():
    """Create a sample AudioSegment for testing"""
    return AudioSegment(1.0, 2.0, "test", 0.8)

@pytest.fixture
def sample_tensor():
    """Create a sample audio tensor for testing"""
    return torch.zeros(1000, dtype=torch.float32)

@pytest.fixture
def create_test_audio():
    """Factory fixture to create test audio with specific characteristics"""
    def _create_audio(duration_seconds=1.0, amplitude=0):
        samples = np.full(
            int(Config.SAMPLE_RATE * duration_seconds),
            amplitude,
            dtype=np.int16
        )
        return samples.tobytes()
    return _create_audio