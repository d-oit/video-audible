import os
import sys
import argparse
import logging
from pathlib import Path

from src.movie_segment_extractor import MovieSegmentExtractor

def main():
    parser = argparse.ArgumentParser(description="Extract movie segments from audio file")
    parser.add_argument("audio_file", help="Path to input audio file (MP3)")
    parser.add_argument("--output-dir", default="movie_segments", help="Directory to save extracted segments")
    args = parser.parse_args()
    
    # Validate input file
    if not os.path.isfile(args.audio_file):
        logging.error(f"Input file not found: {args.audio_file}")
        sys.exit(1)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        extractor = MovieSegmentExtractor()
        
        # Step 1: Identify movie segments
        print("Analyzing audio for movie segments...")
        segments = extractor.identify_movie_segments(args.audio_file)
        print(f"Found {len(segments)} movie segments")
        
        # Save segments metadata
        segments_json = output_dir / "segments.json"
        import json
        with open(segments_json, "w") as f:
            json.dump(segments, f, indent=2)
        print(f"Saved segments metadata to {segments_json}")
        
        # Step 2: Extract segments to separate files
        print("Extracting segments to separate files...")
        extracted_files = extractor.extract_segments(args.audio_file, segments, output_dir)
        print(f"Extracted {len(extracted_files)} segments")
        
        # Step 3: Prepare script for AI voiceover
        script_file = output_dir / "voiceover_script.md"
        extractor.prepare_for_voiceover(segments, script_file)
        print(f"Created voiceover script: {script_file}")
        
        print("\nNext steps:")
        print("1. Review the extracted segments")
        print("2. Edit the voiceover script to add scene descriptions")
        print("3. Use an AI voice generation tool to create voiceovers")
        print("4. Combine segments with voiceovers into final audio")
        
    except Exception as e:
        logging.error(f"Error processing audio: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()