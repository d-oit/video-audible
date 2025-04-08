# Video Audible Documentation

Welcome to the Video Audible documentation. This collection of guides will help you understand and use the Video Audible system for creating accessible audio versions of video content.

## Contents

### Core Documentation

- [Main README](../README.md) - Project overview and basic setup
- [Audio Description Workflow](audio_description_workflow.md) - Complete process for creating audio descriptions
- [Script Reference](script_reference.md) - Detailed information about included scripts
- [API Integration](api_integration.md) - How to use different AI voice services
- [Best Practices](best_practices.md) - Guidelines for creating effective audio descriptions

### Getting Started

The easiest way to get started is to use our all-in-one workflow script:

```bash
./movie_audio_workflow.sh path/to/video.mp4
```

This interactive script will guide you through the entire process of creating audio descriptions for your video content.

For more detailed information about each step, refer to the [Audio Description Workflow](audio_description_workflow.md) guide.

### Script Reference

For detailed information about all available scripts and their parameters, see the [Script Reference](script_reference.md) document.

Key scripts include:
- `movie_audio_workflow.sh` - All-in-one interactive workflow
- `extract_segments.sh` - Extract non-voice segments from video
- `generate_voiceovers.py` - Create AI voiceovers from descriptions
- `combine_with_voiceovers.py` - Combine original audio with voiceovers
