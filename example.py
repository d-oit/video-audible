import os
import logging
from pathlib import Path
from src.audio_pipeline import AudioPipeline
from dotenv import load_dotenv

def main() -> None:
    """
    Main function to load environment variables, initialize the audio pipeline,
    and process an example WAV file.
    """
    # Load environment variables
    load_dotenv()

    # Initialize the audio pipeline
    pipeline = AudioPipeline()

    # Example usage with a WAV file
    # Make sure your audio file is mono and has sample rate matching Config.SAMPLE_RATE (default 16000)
    wav_path = "path/to/your/audio.wav"  # Replace with your audio file path

    try:
        # Process the audio and generate reports
        json_path, md_path = pipeline.process_and_report(
            wav_path=wav_path,
            output_dir="reports"
        )

        logging.info("\nAudio analysis completed successfully!")
        logging.info(f"JSON analysis saved to: {json_path}")
        logging.info(f"Markdown report saved to: {md_path}")

        # Optional: Open the markdown report
        try:
            os.system(f"start {md_path}" if os.name == 'nt' else f"open {md_path}")
        except Exception as e:
            logging.warning(f"Could not open report automatically: {e}")

    except Exception as e:
        logging.error(f"Error processing audio: {e}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()