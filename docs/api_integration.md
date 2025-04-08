# AI Voice Service Integration

This document explains how to integrate different AI voice services with the Video Audible audio description workflow.

## ElevenLabs Integration

[ElevenLabs](https://elevenlabs.io/) provides high-quality, natural-sounding AI voices that are ideal for audio descriptions.

### Setup

1. Create an account at [elevenlabs.io](https://elevenlabs.io/)
2. Navigate to your profile and copy your API key
3. Set the API key as an environment variable:

```bash
# Linux/Mac
export ELEVENLABS_API_KEY="your-api-key-here"

# Windows
set ELEVENLABS_API_KEY=your-api-key-here
```

### Voice Selection

The default script uses a specific voice ID. To change the voice:

1. Visit the ElevenLabs voice library
2. Select a voice you prefer
3. Copy the voice ID
4. Modify the `VOICE_ID` variable in the `generate_voiceovers.py` script

### API Limits

Be aware of your subscription limits:
- Free tier: Limited character count per month
- Paid tiers: Higher limits and priority access

## Amazon Polly Integration

To use [Amazon Polly](https://aws.amazon.com/polly/) instead of ElevenLabs:

### Setup

1. Create an AWS account if you don't have one
2. Set up AWS CLI and configure credentials
3. Install the boto3 library: `pip install boto3`

### Implementation

Replace the `generate_voiceover` function in `generate_voiceovers.py` with:

```python
import boto3

def generate_voiceover(text, output_file, voice_id="Joanna"):
    """Generate voiceover using Amazon Polly"""
    polly_client = boto3.client('polly')
    
    response = polly_client.synthesize_speech(
        Text=text,
        OutputFormat='mp3',
        VoiceId=voice_id,
        Engine='neural'
    )
    
    if "AudioStream" in response:
        with open(output_file, 'wb') as file:
            file.write(response["AudioStream"].read())
        return True
    else:
        print(f"Error: Failed to generate audio")
        return False
```

## Google Text-to-Speech Integration

To use [Google Text-to-Speech](https://cloud.google.com/text-to-speech):

### Setup

1. Create a Google Cloud account
2. Set up a project and enable the Text-to-Speech API
3. Create and download a service account key
4. Set the environment variable: `export GOOGLE_APPLICATION_CREDENTIALS="path/to/key.json"`
5. Install the library: `pip install google-cloud-texttospeech`

### Implementation

Replace the `generate_voiceover` function with:

```python
from google.cloud import texttospeech

def generate_voiceover(text, output_file, voice_name="en-US-Neural2-F"):
    """Generate voiceover using Google Text-to-Speech"""
    client = texttospeech.TextToSpeechClient()
    
    synthesis_input = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="en-US",
        name=voice_name
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    
    with open(output_file, "wb") as out:
        out.write(response.audio_content)
    return True
```

## Open-Source Alternatives

For users who prefer not to use cloud services, several open-source options are available:

### Coqui TTS

[Coqui TTS](https://github.com/coqui-ai/TTS) is a high-quality open-source text-to-speech system.

#### Setup

```bash
pip install TTS
```

#### Implementation

```python
from TTS.api import TTS

def generate_voiceover(text, output_file, model_name="tts_models/en/ljspeech/tacotron2-DDC"):
    """Generate voiceover using Coqui TTS"""
    tts = TTS(model_name=model_name)
    tts.tts_to_file(text=text, file_path=output_file)
    return True
```

### Mozilla TTS

[Mozilla TTS](https://github.com/mozilla/TTS) is another excellent open-source option.

#### Setup

```bash
pip install TTS
```

The implementation is similar to Coqui TTS as they share the same API.

## Comparing Voice Services

| Service | Quality | Cost | Ease of Setup | Offline Use |
|---------|---------|------|---------------|-------------|
| ElevenLabs | Excellent | $$ | Easy | No |
| Amazon Polly | Very Good | $ | Moderate | No |
| Google TTS | Very Good | $ | Moderate | No |
| Coqui TTS | Good | Free | Complex | Yes |
| Mozilla TTS | Good | Free | Complex | Yes |

Choose the service that best fits your needs based on quality requirements, budget, and whether you need offline capability.