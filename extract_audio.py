import sys
import os
import logging

# Add project root to PYTHONPATH explicitly
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.audio_pipeline import AudioPipeline

def main() -> None:
    """
    Main function to extract audio from an input video file and save it to an output audio file.
    """
    if len(sys.argv) < 3:
        logging.error("Usage: python extract_audio.py input.mp4 output.mp3")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    try:
        pipeline = AudioPipeline()
        pipeline.extract_audio_to_file(input_path, output_path)
        logging.info(f"Successfully extracted audio to: {output_path}")
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()