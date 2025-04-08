import argparse
import sys
from pathlib import Path

# Add src directory to Python path for direct script execution
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.audio_pipeline import AudioPipeline
from src.logger import setup_logger

logger = setup_logger()

def main():
    parser = argparse.ArgumentParser(description="Process audio from video file")
    parser.add_argument("video_file", help="Path to the video file to process")
    args = parser.parse_args()

    # Initialize pipeline (detector settings come from .env)
    pipeline = AudioPipeline()
    
    # Set output directory to 'audio'
    output_dir = Path("audio")
    output_dir.mkdir(exist_ok=True)

    try:
        # Process video and generate reports
        json_path, md_path = pipeline.process_and_report(args.video_file, str(output_dir))
        logger.info("Processing completed successfully")
        logger.info(f"JSON analysis: {json_path}")
        logger.info(f"Markdown report: {md_path}")
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()