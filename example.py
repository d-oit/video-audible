import os
from pathlib import Path
from src.audio_pipeline import AudioPipeline
from dotenv import load_dotenv

def main():
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
        
        print("\nAudio analysis completed successfully!")
        print(f"JSON analysis saved to: {json_path}")
        print(f"Markdown report saved to: {md_path}")
        
        # Optional: Open the markdown report
        try:
            os.system(f"start {md_path}" if os.name == 'nt' else f"open {md_path}")
        except Exception as e:
            print(f"Could not open report automatically: {e}")
            
    except Exception as e:
        print(f"Error processing audio: {e}")

if __name__ == "__main__":
    main()