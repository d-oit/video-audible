import sys
import os

# Add project root to PYTHONPATH explicitly
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.audio_pipeline import AudioPipeline

def main():
    if len(sys.argv) < 3:
        print("Usage: python extract_audio.py input.mp4 output.mp3")
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    try:
        pipeline = AudioPipeline()
        pipeline.extract_audio_to_file(input_path, output_path)
        print(f"Successfully extracted audio to: {output_path}")
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()