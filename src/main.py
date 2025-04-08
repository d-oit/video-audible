import sys
from voice_detection import process_video
from logger import setup_logger

log = setup_logger()

def main():
    if len(sys.argv) < 2:
        log.error("Usage: python src/main.py <video_file.mp4>")
        sys.exit(1)
    
    mp4_file = sys.argv[1]
    try:
        process_video(mp4_file)
    except Exception as e:
        log.error("Processing failed: %s", e)
        sys.exit(1)

if __name__ == "__main__":
    main()