import whisperx
import json
import os
import gc
import torch
from datetime import datetime
from config_manager import get_huggingface_token

def transcribe_audio(audio_file_path, project_name, progress_callback=None):
    """
    Transcribe audio file with speaker diarization using WhisperX.

    Args:
        audio_file_path: Path to audio file (MP3, WAV, M4A, MP4)
        project_name: Name of the project/client
        progress_callback: Optional callback function for progress updates

    Returns:
        Path to saved JSON file
    """
    if progress_callback:
        progress_callback("Loading WhisperX model...")

    # Detect if CUDA is available, otherwise use CPU
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    batch_size = 16  # reduce if running out of memory

    # 1. Transcribe with WhisperX
    model = whisperx.load_model("base", device, compute_type=compute_type)

    if progress_callback:
        progress_callback("Transcribing audio...")

    audio = whisperx.load_audio(audio_file_path)
    result = model.transcribe(audio, batch_size=batch_size)

    # 2. Align whisper output
    if progress_callback:
        progress_callback("Aligning transcription...")

    model_a, metadata = whisperx.load_align_model(language_code=result["language"], device=device)
    result = whisperx.align(result["segments"], model_a, metadata, audio, device, return_char_alignments=False)

    # Clear GPU memory
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()
    del model_a

    # 3. Assign speaker labels
    if progress_callback:
        progress_callback("Running speaker diarization...")

    hf_token = get_huggingface_token()
    if hf_token and hf_token.strip():
        try:
            diarize_model = whisperx.DiarizationPipeline(use_auth_token=hf_token, device=device)
            diarize_segments = diarize_model(audio)
            result = whisperx.assign_word_speakers(diarize_segments, result)
        except Exception as e:
            # If diarization fails, continue without speaker labels
            if progress_callback:
                progress_callback(f"Diarization failed: {str(e)}. Continuing without speaker labels...")
            for segment in result["segments"]:
                segment["speaker"] = "Speaker"
    else:
        # No HuggingFace token configured
        if progress_callback:
            progress_callback("No HuggingFace token configured. Skipping diarization...")
        for segment in result["segments"]:
            segment["speaker"] = "Speaker"

    # Clear GPU memory
    gc.collect()
    if device == "cuda":
        torch.cuda.empty_cache()

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
    for segment in result["segments"]:
        segment_data = {
            "start": segment["start"],
            "end": segment["end"],
            "text": segment["text"].strip(),
            "speaker": segment.get("speaker", "Speaker")
        }
        transcript_data["segments"].append(segment_data)
        full_text.append(segment["text"].strip())

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
