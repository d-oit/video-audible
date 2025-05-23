import sys
import os
import re
import logging
from datetime import datetime
import ffmpeg
import numpy as np

def parse_timestamp(timestamp: str) -> int:
    """
    Convert MM:SS or HH:MM:SS format to seconds.
    """
    try:
        parts = [int(x) for x in timestamp.strip().split(':')]
        if len(parts) == 2:  # MM:SS
            return parts[0] * 60 + parts[1]
        elif len(parts) == 3:  # HH:MM:SS
            return parts[0] * 3600 + parts[1] * 60 + parts[2]
        else:
            raise ValueError(f"Invalid timestamp format: {timestamp}")
    except Exception as e:
        raise ValueError(f"Failed to parse timestamp {timestamp}: {str(e)}")

def parse_markdown_segments(md_file: str) -> list:
    """
    Parse segment data from markdown table.
    """
    segments = []
    with open(md_file, 'r') as f:
        lines = f.readlines()

    # Skip until we find the table header
    table_start = False
    for line in lines:
        if '| From | To |' in line:
            table_start = True
            continue
        if table_start and '|---' in line:
            continue
        if table_start and '|' in line:
            # Parse table row
            parts = [x.strip() for x in line.split('|')]
            if len(parts) >= 4:  # At least From, To, Duration columns
                try:
                    start_time = parse_timestamp(parts[1])
                    end_time = parse_timestamp(parts[2])
                    segments.append((start_time, end_time))
                except ValueError as e:
                    logging.warning(f"Skipping invalid row: {line.strip()} - {str(e)}")

    return segments

def extract_audio_segment(input_file: str, start_time: int, end_time: int, output_file: str) -> bool:
    """
    Extract segment from input audio file using ffmpeg.
    """
    try:
        # Use ffmpeg-python to extract segment
        stream = ffmpeg.input(input_file, ss=start_time, t=end_time-start_time)
        stream = ffmpeg.output(stream, output_file, acodec='libmp3lame', loglevel='error')
        ffmpeg.run(stream, overwrite_output=True)
        return True
    except Exception as e:
        logging.warning(f"Failed to extract segment {start_time}-{end_time}: {str(e)}")
        return False

def main() -> None:
    """
    Main function to extract audio segments from an input audio file based on a markdown file.
    """
    if len(sys.argv) != 4:
        logging.error("Usage: python extract_segments.py input.mp3 segments.md output_dir")
        sys.exit(1)

    audio_file = sys.argv[1]
    md_file = sys.argv[2]
    output_dir = sys.argv[3]

    if not os.path.exists(audio_file):
        logging.error(f"Audio file '{audio_file}' not found")
        sys.exit(1)

    if not os.path.exists(md_file):
        logging.error(f"Markdown file '{md_file}' not found")
        sys.exit(1)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Parse segments
        logging.info("Parsing segments from markdown...")
        segments = parse_markdown_segments(md_file)
        if not segments:
            logging.error("No valid segments found in the markdown file")
            sys.exit(1)

        logging.info(f"Found {len(segments)} segments")

        # Extract audio segments
        success_count = 0
        for i, (start, end) in enumerate(segments, 1):
            duration = end - start
            output_file = os.path.join(output_dir, f"segment_{i:03d}.mp3")
            logging.info(f"Extracting segment {i}/{len(segments)} ({duration:.2f}s)...")

            if extract_audio_segment(audio_file, start, end, output_file):
                success_count += 1

        if success_count > 0:
            logging.info(f"Extracted {success_count} segments to {output_dir}")
        else:
            logging.error("No segments were successfully extracted")
            sys.exit(1)

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()