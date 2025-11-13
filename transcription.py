from faster_whisper import WhisperModel
import json
import os
from datetime import datetime

# Initialize model (base model for speed/accuracy balance)
model = WhisperModel("base", device="cpu", compute_type="int8")

def transcribe_audio(audio_file_path, project_name, progress_callback=None):
    """
    Transcribe audio file and save as JSON.

    Args:
        audio_file_path: Path to audio file (MP3, WAV, M4A, MP4)
        project_name: Name of the project/client
        progress_callback: Optional callback function for progress updates

    Returns:
        Path to saved JSON file
    """
    if progress_callback:
        progress_callback("Starting transcription...")

    # Transcribe
    segments, info = model.transcribe(audio_file_path, beam_size=5)

    if progress_callback:
        progress_callback("Processing segments...")

    # Collect all segments
    transcript_data = {
        "project_name": project_name,
        "timestamp": datetime.now().isoformat(),
        "full_transcript": "",
        "segments": []
    }

    full_text = []
    for segment in segments:
        segment_data = {
            "start": segment.start,
            "end": segment.end,
            "text": segment.text.strip(),
            "speaker": "Speaker"  # faster-whisper doesn't do speaker diarization by default
        }
        transcript_data["segments"].append(segment_data)
        full_text.append(segment.text.strip())

    transcript_data["full_transcript"] = " ".join(full_text)

    # Save to JSON
    os.makedirs("transcripts", exist_ok=True)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_filename = f"transcripts/{project_name}_{timestamp_str}.json"

    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(transcript_data, f, indent=2, ensure_ascii=False)

    if progress_callback:
        progress_callback("Transcription complete!")

    return json_filename

def get_saved_transcripts():
    """Get list of saved transcript JSON files."""
    if not os.path.exists("transcripts"):
        return []

    files = []
    for filename in os.listdir("transcripts"):
        if filename.endswith(".json"):
            filepath = os.path.join("transcripts", filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                files.append({
                    "filename": filename,
                    "filepath": filepath,
                    "project_name": data.get("project_name", "Unknown"),
                    "timestamp": data.get("timestamp", "")
                })

    # Sort by timestamp, newest first
    files.sort(key=lambda x: x["timestamp"], reverse=True)
    return files
