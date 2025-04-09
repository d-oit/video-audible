import os
import json
import argparse
from pathlib import Path
from pydub import AudioSegment

def main():
    parser = argparse.ArgumentParser(description="Combine movie segments with voiceovers")
    parser.add_argument("segments_dir", help="Directory containing movie segments")
    parser.add_argument("voiceovers_dir", help="Directory containing voiceovers")
    parser.add_argument("--output", default="final_audio.mp3", help="Output file path")
    parser.add_argument("--fade", type=float, default=0.5, help="Fade duration in seconds")
    args = parser.parse_args()
    
    segments_dir = Path(args.segments_dir)
    voiceovers_dir = Path(args.voiceovers_dir)
    
    # Load segments metadata
    with open(segments_dir / "segments.json", "r") as f:
        segments_data = json.load(f)
    
    # Initialize final audio
    final_audio = AudioSegment.empty()
    
    # Process each segment
    for i, segment_data in enumerate(segments_data):
        segment_num = i + 1
        segment_file = segments_dir / f"segment_{segment_num:03d}.mp3"
        voiceover_file = voiceovers_dir / f"voiceover_{segment_num}.mp3"
        
        if not segment_file.exists():
            print(f"Warning: Segment file {segment_file} not found, skipping")
            continue
            
        # Load segment audio
        print(f"Processing segment {segment_num}...")
        segment_audio = AudioSegment.from_file(str(segment_file))
        
        # Add voiceover if available
        if voiceover_file.exists():
            voiceover = AudioSegment.from_file(str(voiceover_file))
            
            # Option 1: Add voiceover before segment
            # final_audio += voiceover
            # final_audio += segment_audio
            
            # Option 2: Overlay voiceover at the beginning of segment (with ducking)
            segment_with_voiceover = segment_audio.overlay(
                voiceover, 
                position=0,
                gain_during_overlay=-6  # Reduce segment volume during voiceover
            )
            final_audio += segment_with_voiceover
        else:
            print(f"Warning: No voiceover found for segment {segment_num}")
            final_audio += segment_audio
        
        # Add a short silence between segments
        final_audio += AudioSegment.silent(duration=500)  # 500ms silence
    
    # Export final audio
    print(f"Exporting final audio to {args.output}...")
    final_audio.export(args.output, format="mp3")
    print("Done!")

if __name__ == "__main__":
    main()