import os
import pytest
from pathlib import Path
from src.audio_pipeline import AudioPipeline

def test_extract_audio_to_file(tmp_path):
    # Create test pipeline
    pipeline = AudioPipeline()
    
    # Mock video path (you'll need to provide a real test video)
    video_path = "test_data/sample.mp4"
    output_path = tmp_path / "output.mp3"
    
    # Skip test if test video doesn't exist
    if not os.path.exists(video_path):
        pytest.skip("Test video file not found")
    
    # Extract audio
    pipeline.extract_audio_to_file(video_path, str(output_path))
    
    # Verify output file exists and has content
    assert output_path.exists()
    assert output_path.stat().st_size > 0