# Implementation Plan: Transcription Processing Tool

## Overview
Build a Python desktop application for processing audio files into formatted transcripts using faster-whisper for transcription and Groq API for formatting.

---

## Task 1: Project Setup and Dependencies

### Description
Set up the Python project structure and install all required dependencies.

### Steps

1. **Create project directory structure**
```
d:\Transcription\
├── main.py
├── requirements.txt
├── transcripts\          # JSON storage
├── completed\            # Final .docx outputs
├── config.json           # Stores Groq API key
└── README.md
```

2. **Create requirements.txt**
```txt
faster-whisper==1.0.3
groq==0.11.0
python-docx==1.1.2
tk
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

### Verification
- Run `pip list` and confirm all packages are installed
- Verify folders `transcripts\` and `completed\` exist

---

## Task 2: Implement Configuration Management

### Description
Create a simple config system to store and retrieve the Groq API key.

### Implementation

**File: `d:\Transcription\config_manager.py`**
```python
import json
import os

CONFIG_FILE = "config.json"

def load_config():
    """Load configuration from JSON file."""
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {"groq_api_key": ""}

def save_config(config):
    """Save configuration to JSON file."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def get_groq_api_key():
    """Get the Groq API key from config."""
    config = load_config()
    return config.get("groq_api_key", "")

def set_groq_api_key(api_key):
    """Save the Groq API key to config."""
    config = load_config()
    config["groq_api_key"] = api_key
    save_config(config)
```

### Verification
- Create a test script that calls `set_groq_api_key("test")` and `get_groq_api_key()`
- Verify `config.json` is created with the correct structure

---

## Task 3: Implement Transcription Module

### Description
Create the audio transcription functionality using faster-whisper.

### Implementation

**File: `d:\Transcription\transcription.py`**
```python
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
```

### Verification
- Test with a sample audio file
- Verify JSON is created in `transcripts\` folder with correct structure
- Check that `full_transcript` and `segments` are populated

---

## Task 4: Implement Groq Formatting Module

### Description
Create the formatting functionality using Groq API.

### Implementation

**File: `d:\Transcription\formatter.py`**
```python
from groq import Groq
import json
import os
from datetime import datetime
from docx import Document

def format_transcript(json_filepath, api_key, progress_callback=None):
    """
    Format transcript using Groq API.

    Args:
        json_filepath: Path to transcript JSON file
        api_key: Groq API key
        progress_callback: Optional callback for progress updates

    Returns:
        Formatted transcript text
    """
    if progress_callback:
        progress_callback("Loading transcript...")

    # Load transcript
    with open(json_filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    transcript_text = data["full_transcript"]

    if progress_callback:
        progress_callback("Sending to Groq API...")

    # Initialize Groq client
    client = Groq(api_key=api_key)

    # Format using Groq
    prompt = """Format this podcast transcript for YouTube subtitles. Clean up verbal tics (um, uh, like), add proper punctuation, break into subtitle-sized segments with timestamps. Keep all spoken content accurate.

Transcript:
""" + transcript_text

    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.3,
    )

    formatted_text = chat_completion.choices[0].message.content

    if progress_callback:
        progress_callback("Formatting complete!")

    return formatted_text

def save_to_docx(formatted_text, project_name, progress_callback=None):
    """
    Save formatted transcript to Word document.

    Args:
        formatted_text: The formatted transcript text
        project_name: Name of the project
        progress_callback: Optional callback for progress updates

    Returns:
        Path to saved .docx file
    """
    if progress_callback:
        progress_callback("Creating Word document...")

    # Create Word document
    doc = Document()
    doc.add_heading(f"Transcript: {project_name}", 0)
    doc.add_paragraph(formatted_text)

    # Save to completed folder
    os.makedirs("completed", exist_ok=True)
    timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    docx_filename = f"completed/{project_name}_{timestamp_str}.docx"

    doc.save(docx_filename)

    if progress_callback:
        progress_callback("Document saved!")

    return docx_filename
```

### Verification
- Test with a sample JSON transcript file
- Verify Groq API connection works with valid API key
- Check that .docx file is created in `completed\` folder

---

## Task 5: Build Tkinter GUI

### Description
Create the main GUI application with all three sections.

### Implementation

**File: `d:\Transcription\main.py`**
```python
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from transcription import transcribe_audio, get_saved_transcripts
from formatter import format_transcript, save_to_docx
from config_manager import get_groq_api_key, set_groq_api_key

class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Transcription Processing Tool")
        self.root.geometry("700x600")

        self.selected_audio_file = None
        self.selected_json_file = None
        self.formatted_text = ""

        self.create_widgets()

    def create_widgets(self):
        # Create notebook (tabbed interface)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Section 1: Transcription
        transcription_frame = ttk.Frame(notebook)
        notebook.add(transcription_frame, text="1. Transcription")
        self.create_transcription_section(transcription_frame)

        # Section 2: Formatting & Review
        formatting_frame = ttk.Frame(notebook)
        notebook.add(formatting_frame, text="2. Formatting & Review")
        self.create_formatting_section(formatting_frame)

        # Settings
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Settings")
        self.create_settings_section(settings_frame)

    def create_transcription_section(self, parent):
        # Project name
        ttk.Label(parent, text="Project/Client Name:").pack(pady=(10, 0))
        self.project_name_entry = ttk.Entry(parent, width=50)
        self.project_name_entry.pack(pady=5)

        # File upload
        ttk.Label(parent, text="Audio File:").pack(pady=(10, 0))
        file_frame = ttk.Frame(parent)
        file_frame.pack(pady=5)

        self.file_label = ttk.Label(file_frame, text="No file selected", width=40)
        self.file_label.pack(side="left", padx=5)

        ttk.Button(file_frame, text="Browse", command=self.browse_audio_file).pack(side="left")

        # Transcribe button
        ttk.Button(parent, text="Transcribe", command=self.start_transcription).pack(pady=20)

        # Progress indicator
        self.transcribe_progress_label = ttk.Label(parent, text="", foreground="blue")
        self.transcribe_progress_label.pack()

    def create_formatting_section(self, parent):
        # Dropdown for saved transcripts
        ttk.Label(parent, text="Select Transcript:").pack(pady=(10, 0))

        select_frame = ttk.Frame(parent)
        select_frame.pack(pady=5)

        self.transcript_dropdown = ttk.Combobox(select_frame, width=40, state="readonly")
        self.transcript_dropdown.pack(side="left", padx=5)

        ttk.Button(select_frame, text="Refresh", command=self.refresh_transcripts).pack(side="left")

        # Format button
        ttk.Button(parent, text="Format", command=self.start_formatting).pack(pady=20)

        # Progress indicator
        self.format_progress_label = ttk.Label(parent, text="", foreground="blue")
        self.format_progress_label.pack()

        # Text editor
        ttk.Label(parent, text="Formatted Result:").pack(pady=(10, 0))

        text_frame = ttk.Frame(parent)
        text_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.result_text = tk.Text(text_frame, wrap="word", height=15)
        self.result_text.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(text_frame, command=self.result_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.result_text.config(yscrollcommand=scrollbar.set)

        # Save to Completed button
        ttk.Button(parent, text="Save to Completed", command=self.save_to_completed).pack(pady=10)

        # Initialize transcript list
        self.refresh_transcripts()

    def create_settings_section(self, parent):
        ttk.Label(parent, text="Groq API Key:").pack(pady=(20, 0))

        self.api_key_entry = ttk.Entry(parent, width=50, show="*")
        self.api_key_entry.pack(pady=5)

        # Load existing API key
        api_key = get_groq_api_key()
        if api_key:
            self.api_key_entry.insert(0, api_key)

        ttk.Button(parent, text="Save API Key", command=self.save_api_key).pack(pady=10)

    def browse_audio_file(self):
        filetypes = [
            ("Audio Files", "*.mp3 *.wav *.m4a *.mp4"),
            ("All Files", "*.*")
        ]
        filename = filedialog.askopenfilename(filetypes=filetypes)
        if filename:
            self.selected_audio_file = filename
            self.file_label.config(text=filename.split("/")[-1])

    def start_transcription(self):
        project_name = self.project_name_entry.get().strip()

        if not project_name:
            messagebox.showerror("Error", "Please enter a project name")
            return

        if not self.selected_audio_file:
            messagebox.showerror("Error", "Please select an audio file")
            return

        # Run transcription in background thread
        def transcribe():
            try:
                def update_progress(msg):
                    self.transcribe_progress_label.config(text=msg)

                transcribe_audio(self.selected_audio_file, project_name, update_progress)
                messagebox.showinfo("Success", "Transcription completed!")
                self.refresh_transcripts()
            except Exception as e:
                messagebox.showerror("Error", f"Transcription failed: {str(e)}")
            finally:
                self.transcribe_progress_label.config(text="")

        threading.Thread(target=transcribe, daemon=True).start()

    def refresh_transcripts(self):
        transcripts = get_saved_transcripts()
        display_names = [f"{t['project_name']} - {t['timestamp'][:10]}" for t in transcripts]
        self.transcript_dropdown['values'] = display_names

        # Store the mapping
        self.transcript_files = transcripts

    def start_formatting(self):
        if not self.transcript_dropdown.get():
            messagebox.showerror("Error", "Please select a transcript")
            return

        api_key = get_groq_api_key()
        if not api_key:
            messagebox.showerror("Error", "Please set your Groq API key in Settings")
            return

        # Get selected transcript file
        selected_index = self.transcript_dropdown.current()
        if selected_index < 0:
            return

        self.selected_json_file = self.transcript_files[selected_index]['filepath']

        # Run formatting in background thread
        def format_text():
            try:
                def update_progress(msg):
                    self.format_progress_label.config(text=msg)

                self.formatted_text = format_transcript(self.selected_json_file, api_key, update_progress)

                # Update text editor
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(1.0, self.formatted_text)

                messagebox.showinfo("Success", "Formatting completed!")
            except Exception as e:
                messagebox.showerror("Error", f"Formatting failed: {str(e)}")
            finally:
                self.format_progress_label.config(text="")

        threading.Thread(target=format_text, daemon=True).start()

    def save_to_completed(self):
        if not self.formatted_text:
            messagebox.showerror("Error", "No formatted text to save")
            return

        if not self.selected_json_file:
            messagebox.showerror("Error", "No transcript selected")
            return

        # Get project name from selected transcript
        import json
        with open(self.selected_json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            project_name = data['project_name']

        try:
            docx_path = save_to_docx(self.formatted_text, project_name)
            messagebox.showinfo("Success", f"Saved to: {docx_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Save failed: {str(e)}")

    def save_api_key(self):
        api_key = self.api_key_entry.get().strip()
        if api_key:
            set_groq_api_key(api_key)
            messagebox.showinfo("Success", "API key saved!")
        else:
            messagebox.showerror("Error", "Please enter an API key")

if __name__ == "__main__":
    root = tk.Tk()
    app = TranscriptionApp(root)
    root.mainloop()
```

### Verification
- Run `python main.py`
- Verify all three tabs are visible
- Test navigation between tabs
- Check that all UI elements are present and properly labeled

---

## Task 6: End-to-End Testing

### Description
Test the complete workflow from audio file to Word document.

### Test Steps

1. **Test Transcription**
   - Open the app
   - Go to Settings, enter your Groq API key, click "Save API Key"
   - Go to "1. Transcription" tab
   - Enter a project name (e.g., "Test Project")
   - Click Browse and select a sample audio file (MP3, WAV, M4A, or MP4)
   - Click "Transcribe"
   - Wait for progress indicator to show completion
   - Verify JSON file is created in `transcripts\` folder

2. **Test Formatting**
   - Go to "2. Formatting & Review" tab
   - Click "Refresh" if needed
   - Select the transcript from dropdown
   - Click "Format"
   - Wait for progress indicator
   - Verify formatted text appears in the text editor
   - Click "Save to Completed"
   - Verify .docx file is created in `completed\` folder
   - Open the .docx file and verify content is properly formatted

3. **Test Settings Persistence**
   - Close the app
   - Reopen the app
   - Go to Settings
   - Verify API key is still saved (shown as asterisks)

### Expected Results
- All files created in correct locations
- No crashes or errors
- Progress indicators work correctly
- Formatted text is clean and properly punctuated

---

## Task 7: Create Documentation

### Description
Create a simple README for users.

### Implementation

**File: `d:\Transcription\README.md`**
```markdown
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
```

### Verification
- Read through README and ensure all steps are accurate

---

## Summary

This plan creates a fully functional transcription processing tool with:
- Audio transcription using faster-whisper
- Groq API integration for formatting
- Simple Tkinter GUI with tabs
- JSON intermediate storage
- Word document export
- Settings persistence

**Estimated Time**: 4-6 hours for an engineer with Python/Tkinter experience

**Order of Execution**: Tasks 1-7 should be completed sequentially as each builds on the previous.

---

## Quick Start Instructions for Web Claude

When you receive this plan, follow these steps:

1. Start with Task 1 (Project Setup)
2. Work through each task sequentially
3. After completing each task, run the verification steps
4. If you encounter errors, debug before moving to the next task
5. Complete Task 6 (End-to-End Testing) to ensure everything works together
6. Remember: All commands should use Windows syntax (backslashes for paths)
