import os
import re
import json
import requests
import argparse
from pathlib import Path
import markdown_parser  # You'll need to implement this or use a library

# ElevenLabs API settings
API_KEY = os.environ.get("ELEVENLABS_API_KEY")
VOICE_ID = "21m00Tcm4TlvDq8ikWAM"  # Default voice ID, you can change this

def extract_descriptions(markdown_file):
    """Extract segment descriptions from markdown file"""
    with open(markdown_file, 'r') as f:
        content = f.read()
    
    # Simple regex to extract segment info
    segments = []
    pattern = r'## Segment (\d+)\n- Start: ([^\n]+)\n- End: ([^\n]+)\n- Duration: ([^\n]+)\n- Type: ([^\n]+)\n- Description: ([^\n]+)'
    matches = re.finditer(pattern, content, re.MULTILINE)
    
    for match in matches:
        segments.append({
            'segment_id': match.group(1),
            'description': match.group(6).strip()
        })
    
    return segments

def generate_voiceover(text, output_file, voice_id=VOICE_ID):
    """Generate voiceover using ElevenLabs API"""
    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.5
        }
    }
    
    response = requests.post(url, json=data, headers=headers)
    
    if response.status_code == 200:
        with open(output_file, 'wb') as f:
            f.write(response.content)
        return True
    else:
        print(f"Error: {response.status_code} - {response.text}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Generate AI voiceovers from script")
    parser.add_argument("script_file", help="Path to voiceover script markdown file")
    parser.add_argument("--output-dir", default="voiceovers", help="Directory to save voiceovers")
    args = parser.parse_args()
    
    if not API_KEY:
        print("Error: ELEVENLABS_API_KEY environment variable not set")
        return
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Extract descriptions from markdown
    segments = extract_descriptions(args.script_file)
    
    # Generate voiceovers
    for segment in segments:
        output_file = output_dir / f"voiceover_{segment['segment_id']}.mp3"
        print(f"Generating voiceover for segment {segment['segment_id']}...")
        
        if generate_voiceover(segment['description'], output_file):
            print(f"  Success! Saved to {output_file}")
        else:
            print(f"  Failed to generate voiceover for segment {segment['segment_id']}")

if __name__ == "__main__":
    main()