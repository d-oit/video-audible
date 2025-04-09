import os
from dotenv import load_dotenv

load_dotenv()  # Load variables from .env file

class Config:
    # General audio processing settings
    # Global voice detection settings
    NON_VOICE_DURATION_THRESHOLD = float(os.getenv("NON_VOICE_DURATION_THRESHOLD", "2.0"))
    
    # Audio processing settings
    SAMPLE_RATE = int(os.getenv("SAMPLE_RATE", "16000"))
    FRAME_DURATION_MS = int(os.getenv("FRAME_DURATION_MS", "30"))
    
    # Silence detection settings
    SILENCE_DB_THRESHOLD = float(os.getenv("SILENCE_DB_THRESHOLD", "-50"))
    MIN_SILENCE_DURATION = float(os.getenv("MIN_SILENCE_DURATION", "0.5"))
    
    # Speech detection settings
    SPEECH_THRESHOLD = float(os.getenv("SPEECH_THRESHOLD", "0.5"))
    MIN_SPEECH_DURATION = float(os.getenv("MIN_SPEECH_DURATION", "0.3"))
    
    # Music detection settings
    MUSIC_THRESHOLD = float(os.getenv("MUSIC_THRESHOLD", "0.6"))
    MIN_MUSIC_DURATION = float(os.getenv("MIN_MUSIC_DURATION", "1.0"))
    
    # Background sound detection settings
    BACKGROUND_THRESHOLD = float(os.getenv("BACKGROUND_THRESHOLD", "0.4"))
    MIN_BACKGROUND_DURATION = float(os.getenv("MIN_BACKGROUND_DURATION", "1.0"))
    
    # Segment merging settings
    GAP_MERGE_THRESHOLD = float(os.getenv("GAP_MERGE_THRESHOLD", "0.5"))

if __name__ == "__main__":
    # Test config loading
    print("\nAudio Processing Settings:")
    print(f"Sample rate: {Config.SAMPLE_RATE}")
    print(f"Frame duration: {Config.FRAME_DURATION_MS}ms")
    
    print("\nDetection Thresholds:")
    print(f"Silence: {Config.SILENCE_DB_THRESHOLD}dB")
    print(f"Speech: {Config.SPEECH_THRESHOLD}")
    print(f"Music: {Config.MUSIC_THRESHOLD}")
    print(f"Background: {Config.BACKGROUND_THRESHOLD}")


