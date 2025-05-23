import os
import wave
import contextlib

import ffmpeg
import torch
import numpy as np
from dotenv import load_dotenv

from .logger import setup_logger
from .config import Config

# Load environment variables from .env file
load_dotenv()

logger = setup_logger()

def extract_audio(mp4_path: str, output_wav: str) -> None:
    """
    Extract audio from an MP4 file and save as mono WAV (default 16kHz).

    Args:
        mp4_path (str): Path to input MP4 video.
        output_wav (str): Path to output WAV file.

    Raises:
        RuntimeError: If extraction fails.
    """
    try:
        sample_rate = int(os.getenv('SAMPLE_RATE', '16000'))
        logger.info("Extracting audio from %s", mp4_path)
        (
            ffmpeg
            .input(mp4_path)
            .output(output_wav, ac=1, ar=sample_rate, format='wav')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        logger.info("Audio extracted to %s", output_wav)
    except Exception as e:
        logger.error("Failed to extract audio: %s", e)
        raise
def extract_lossless_audio(mp4_path: str, output_path: str, format: str = 'flac') -> None:
    """
    Extract original audio from MP4 and save as lossless FLAC or copy AAC without re-encoding.

    Args:
        mp4_path (str): Path to input MP4 video.
        output_path (str): Path to output audio file.
        format (str): 'flac' for lossless compression, 'aac' to copy AAC stream.

    Raises:
        ValueError: If unsupported format.
        RuntimeError: If extraction fails.
    """
    try:
        sample_rate = int(os.getenv('SAMPLE_RATE', '16000'))
        logger.info("Extracting lossless audio from %s", mp4_path)
        stream = ffmpeg.input(mp4_path)
        if format == 'flac':
            stream = stream.output(output_path, ac=1, ar=sample_rate, format='flac')
        elif format == 'aac':
            stream = stream.output(output_path, acodec='copy', format='m4a')
        else:
            raise ValueError(f"Unsupported format: {format}")
        (
            stream
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True)
        )
        logger.info("Lossless audio extracted to %s", output_path)
    except Exception as e:
        logger.error("Failed to extract lossless audio: %s", e)
        raise


def read_wave(path: str) -> Tuple[bytes, int]:
    """
    Read a mono WAV file.

    Args:
        path (str): Path to WAV file.

    Returns:
        Tuple[bytes, int]: PCM audio data and sample rate.

    Raises:
        AssertionError: If audio is not mono.
    """
    with contextlib.closing(wave.open(path, "rb")) as wf:
        num_channels = wf.getnchannels()
        assert num_channels == 1, "Audio must be mono"
        _ = wf.getsampwidth()
        sample_rate = wf.getframerate()
        pcm_data = wf.readframes(wf.getnframes())
        return pcm_data, sample_rate

def frame_generator(frame_duration_ms: int, audio: bytes, sample_rate: int):
    """
    Generate audio frames from PCM audio data.

    Args:
        frame_duration_ms (int): Frame size in milliseconds.
        audio (bytes): PCM audio data.
        sample_rate (int): Sample rate.

    Yields:
        Tuple[bytes, float]: Frame bytes and start time in seconds.
    """
    n = int(sample_rate * (frame_duration_ms / 1000.0) * 2)  # 2 bytes per sample (16-bit)
    offset = 0
    while offset + n < len(audio):
        yield audio[offset:offset + n], offset / (sample_rate * 2)
        offset += n

def detect_voice(audio: bytes, sample_rate: int, frame_duration_ms=30):
    """
    Uses Silero VAD to determine voice activity for each frame.
    Returns a list of tuples with (frame_start_time, voice_boolean).
    """
    # Lazy load Silero VAD model and utils
    if not hasattr(detect_voice, "model"):
        detect_voice.model, utils = torch.hub.load(
            repo_or_dir='snakers4/silero-vad',
            model='silero_vad',
            force_reload=False,
            trust_repo=True  # Suppress warning about untrusted repo
        )
        (detect_voice.get_speech_timestamps,
         _, _, _, _) = utils

    # Convert PCM bytes to float32 tensor normalized to [-1,1]
    audio_np = np.frombuffer(audio, dtype=np.int16).astype(np.float32) / 32768.0
    audio_tensor = torch.from_numpy(audio_np)

    # Get speech segments as list of dicts with 'start' and 'end' sample indices
    speech_timestamps = detect_voice.get_speech_timestamps(audio_tensor, detect_voice.model, sampling_rate=sample_rate)

    results = []
    for frame, start_time in frame_generator(frame_duration_ms, audio, sample_rate):
        frame_len_samples = int(sample_rate * (frame_duration_ms / 1000.0))
        start_sample = int(start_time * sample_rate)
        end_sample = start_sample + frame_len_samples

        # Check if frame overlaps any speech segment
        is_speech = False
        for seg in speech_timestamps:
            if end_sample < seg['start']:
                break  # segments are sorted
            if start_sample > seg['end']:
                continue
            # Overlaps
            is_speech = True
            break

        results.append((start_time, is_speech))

    return results

def group_silence_frames(
    vad_results: list, frame_duration_ms: int = 30
) -> list:
    """
    Group consecutive frames with no speech into silence segments.

    Args:
        vad_results (list): List of tuples (start_time_seconds, is_speech).
        frame_duration_ms (int): Frame duration in milliseconds.

    Returns:
        list: List of (start_time, end_time) silence segments.
    """
    silence_segments = []
    segment_start = None

    for start_time, is_speech in vad_results:
        if not is_speech:
            if segment_start is None:
                segment_start = start_time
        else:
            if segment_start is not None:
                end_time = start_time
                silence_segments.append((segment_start, end_time))
                segment_start = None

    # If file ends on silence
    if segment_start is not None:
        last_time = vad_results[-1][0] + frame_duration_ms / 1000.0
        silence_segments.append((segment_start, last_time))

    return silence_segments


def filter_by_duration(
    segments: list, threshold: float
) -> list:
    """
    Filter segments shorter than a duration threshold.

    Args:
        segments (list): List of (start_time, end_time) tuples.
        threshold (float): Minimum duration in seconds.

    Returns:
        list: Filtered list of segments.
    """
    return [seg for seg in segments if (seg[1] - seg[0]) >= threshold]


def seconds_to_mmss(seconds: float) -> str:
    """
    Convert seconds to MM:SS string.

    Args:
        seconds (float): Time in seconds.

    Returns:
        str: Time formatted as MM:SS.
    """
    m, s = divmod(int(seconds), 60)
    return f"{m:02d}:{s:02d}"


def generate_markdown_report(
    segments: list, output_md: str
) -> None:
    """
    Create a Markdown report listing non-voice segments.

    Args:
        segments (list): List of (start_time, end_time) tuples.
        output_md (str): Path to output Markdown file.

    Raises:
        RuntimeError: If report generation fails.
    """
    try:
        logger.info("Generating Markdown report: %s", output_md)
        with open(output_md, "w") as md:
            md.write("# Non-Voice Segments Report\n\n")
            md.write("| From | To | Duration (s) |\n")
            md.write("|-------|-------|--------------|\n")
            for start, end in segments:
                duration = end - start
                md.write(f"| {seconds_to_mmss(start)} | {seconds_to_mmss(end)} | {duration:.2f} |\n")
        logger.info("Report generated successfully.")
    except Exception as e:
        logger.error("Error generating report: %s", e)
        raise


def process_video(
    mp4_path: str, output_dir: str = "audio", keep_temp_wav: bool = False
) -> None:
    """
    Process a video file: extract audio, detect silence, and generate report.

    Args:
        mp4_path (str): Path to input MP4 video.
        output_dir (str): Directory to save outputs.
        keep_temp_wav (bool): Whether to keep intermediate WAV file.
    """
    logger.debug("Received mp4_path argument: %s", mp4_path)
    import os
    import pathlib

    # Define output directory and ensure it exists
    audio_dir = pathlib.Path(output_dir)
    audio_dir.mkdir(parents=True, exist_ok=True)

    # Get base name of the video file (without extension)
    video_stem = pathlib.Path(mp4_path).stem

    # Define output file paths using the video stem
    temp_wav = audio_dir / f"{video_stem}.wav"
    output_md = audio_dir / f"{video_stem}_report.md"
    # Handle Windows paths correctly
    parts = []
    path_remainder = mp4_path
    
    # Handle drive letter specially
    if ':' in path_remainder:
        drive, path_remainder = path_remainder.split(':', 1)
        parts.append(drive + ':')
    
    # Split remaining path and filter empty parts
    parts.extend(p for p in path_remainder.split('\\') if p)
    
    # Rejoin with proper separators
    mp4_path = os.path.join(*parts)
    mp4_path = os.path.normpath(mp4_path)
    logger.debug("Normalized mp4_path: %s", mp4_path)
    try:
        if not os.path.isfile(mp4_path):
            logger.error("Input video file does not exist: %s", mp4_path)
            raise FileNotFoundError(f"Input video file not found: {mp4_path}")

        extract_audio(mp4_path, str(temp_wav))
        audio, sample_rate = read_wave(str(temp_wav))
        logger.info("Starting voice detection...")
        vad_results = detect_voice(audio, sample_rate)
        silence_segments = group_silence_frames(vad_results)
        filtered_segments = filter_by_duration(silence_segments, float(os.getenv('NON_VOICE_DURATION_THRESHOLD')))
        generate_markdown_report(filtered_segments, str(output_md))
        logger.info("Process completed. Check %s for the report.", str(output_md))
    except Exception as err:
        logger.error("An error occurred: %s", err)
        raise
    finally:
        # Cleanup temporary WAV file if keep_temp_wav is False
        if not keep_temp_wav and temp_wav.exists():
            os.remove(temp_wav)
            logger.info("Temporary file %s removed.", str(temp_wav))