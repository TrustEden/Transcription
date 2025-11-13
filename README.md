# Transcription Processing Tool

A Python desktop application for processing audio files into formatted transcripts.

## Requirements

- Python 3.10+
- Groq API key (get from https://console.groq.com)

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python main.py
```

2. **First Time Setup**
   - Go to Settings tab
   - Enter your Groq API key
   - Click "Save API Key"

3. **Transcription Workflow**
   - Go to "1. Transcription" tab
   - Enter project/client name
   - Browse and select audio file (MP3, WAV, M4A, MP4)
   - Click "Transcribe"
   - Wait for completion

4. **Formatting Workflow**
   - Go to "2. Formatting & Review" tab
   - Select a transcript from dropdown
   - Click "Format"
   - Review the formatted text
   - Click "Save to Completed" to export as Word document

## Output Locations

- Transcripts (JSON): `transcripts\`
- Completed documents (DOCX): `completed\`
- Configuration: `config.json`

## Supported Audio Formats

- MP3
- WAV
- M4A
- MP4
