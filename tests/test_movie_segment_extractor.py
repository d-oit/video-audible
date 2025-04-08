import pytest
import json
from unittest.mock import patch, Mock, MagicMock
import numpy as np
from pathlib import Path

from src.movie_segment_extractor import MovieSegmentExtractor
from src.detectors.base_detector import AudioSegment
from src.config import Config

class TestMovieSegmentExtractor:
    @pytest.fixture
    def mock_audio_pipeline(self):
        with patch('src.audio_pipeline.AudioPipeline') as mock_pipeline_class:
            # Create a mock instance
            mock_pipeline = mock_pipeline_class.return_value

            # Mock the extract_audio method
            mock_pipeline.extract_audio.return_value = (
                np.zeros(16000, dtype=np.int16),  # 1 second of silence
                16000  # Sample rate
            )

            # Mock the process_audio method
            mock_pipeline.process_audio.return_value = {
                "speech": [
                    {"start_time": 0.1, "end_time": 0.5, "label": "speech", "confidence": 0.8}
                ],
                "music": [
                    {"start_time": 0.6, "end_time": 0.9, "label": "music", "confidence": 0.7}
                ],
                "silence": [
                    {"start_time": 0.0, "end_time": 0.1, "label": "silence", "confidence": 0.9},
                    {"start_time": 0.5, "end_time": 0.6, "label": "silence", "confidence": 0.9},
                    {"start_time": 0.9, "end_time": 1.0, "label": "silence", "confidence": 0.9}
                ],
                "background": []
            }

            # Mock the silence_detector
            mock_pipeline.silence_detector = MagicMock()
            mock_pipeline.silence_detector.merge_adjacent_segments.side_effect = lambda segments, gap_threshold: segments

            yield mock_pipeline

    @pytest.fixture
    def extractor(self, mock_audio_pipeline):
        with patch('src.movie_segment_extractor.AudioPipeline', return_value=mock_audio_pipeline):
            extractor = MovieSegmentExtractor()
            yield extractor

    def test_init(self):
        """Test that the extractor initializes correctly."""
        with patch('src.movie_segment_extractor.AudioPipeline') as mock_pipeline_class:
            extractor = MovieSegmentExtractor()
            assert extractor.pipeline == mock_pipeline_class.return_value

    def test_identify_movie_segments(self, extractor, mock_audio_pipeline):
        """Test that identify_movie_segments calls extract_audio and process_audio correctly."""
        # Call the method
        segments = extractor.identify_movie_segments("test_audio.mp3")

        # Verify extract_audio was called with the correct path
        mock_audio_pipeline.extract_audio.assert_called_once_with("test_audio.mp3")

        # Verify process_audio was called with the correct data
        mock_audio_pipeline.process_audio.assert_called_once()
        args, kwargs = mock_audio_pipeline.process_audio.call_args
        assert args[0].shape == (16000,)  # Audio data
        assert args[1] == 16000  # Sample rate

        # Verify the returned segments
        assert len(segments) == 2  # One speech and one music segment
        assert segments[0]["type"] == "speech"
        assert segments[1]["type"] == "music"

    def test_extract_segments(self, extractor, tmp_path):
        """Test that extract_segments correctly extracts segments to files."""
        with patch('extract_segments.extract_audio_segment') as mock_extract:
            # Set up the mock to return success
            mock_extract.return_value = True

            # Create test segments
            segments = [
                {"start_time": 0.1, "end_time": 0.5, "type": "speech"},
                {"start_time": 0.6, "end_time": 0.9, "type": "music"}
            ]

            # Call the method
            output_dir = tmp_path / "segments"
            extracted_files = extractor.extract_segments("test_audio.mp3", segments, str(output_dir))

            # Verify extract_audio_segment was called for each segment
            assert mock_extract.call_count == 2

            # Verify the returned file paths
            assert len(extracted_files) == 2
            assert all(str(output_dir) in file for file in extracted_files)

    def test_prepare_for_voiceover(self, extractor, tmp_path):
        """Test that prepare_for_voiceover creates a script file."""
        # Create test segments
        segments = [
            {"start_time": 0.1, "end_time": 0.5, "type": "speech"},
            {"start_time": 0.6, "end_time": 0.9, "type": "music"}
        ]

        # Call the method
        output_path = tmp_path / "script.md"
        extractor.prepare_for_voiceover(segments, str(output_path))

        # Verify the file was created
        assert output_path.exists()

        # Verify the content
        content = output_path.read_text()
        assert "# Movie Segments for AI Voiceover" in content
        assert "## Segment 1" in content
        assert "## Segment 2" in content
        assert "- Type: speech" in content
        assert "- Type: music" in content
