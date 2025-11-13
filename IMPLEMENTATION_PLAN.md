# Implementation Plan: Transcription App Enhancement for Fiverr Work

## Project Overview
Enhance the existing transcription application to support professional transcription services on Fiverr. The app will handle audio/video transcription with speaker diarization, confidence score visualization, customizable formatting options, and multiple output templates.

## Target Use Cases
- Podcast transcription
- YouTube video transcription
- Interview transcription

---

## Phase 1: Video File Support & Audio Extraction

### Goals
- Support common video formats (MP4, MOV, AVI, MKV, WEBM)
- Extract audio from video files for transcription
- Ensure ffmpeg dependency is properly handled

### Implementation Tasks

#### Task 1.1: Update File Type Support
**File**: [main.py](main.py#L176-L178)

**Changes**:
```python
# Current:
filetypes = [
    ("Audio Files", "*.mp3 *.wav *.m4a *.mp4"),
    ("All Files", "*.*")
]

# Updated:
filetypes = [
    ("Audio/Video Files", "*.mp3 *.wav *.m4a *.mp4 *.mov *.avi *.mkv *.webm"),
    ("All Files", "*.*")
]
```

#### Task 1.2: Add ffmpeg Dependency Check
**File**: [main.py](main.py)

**New Function** (add near top of TranscriptionApp class):
```python
def check_ffmpeg(self):
    """Check if ffmpeg is available."""
    import subprocess
    try:
        subprocess.run(['ffmpeg', '-version'],
                      capture_output=True,
                      check=True,
                      creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
```

**Update __init__** to call check on startup:
```python
def __init__(self, root):
    self.root = root
    # ... existing code ...

    # Check ffmpeg availability
    if not self.check_ffmpeg():
        messagebox.showwarning(
            "ffmpeg Not Found",
            "ffmpeg is required for video file processing.\n"
            "Please install ffmpeg and add it to your system PATH.\n"
            "Download from: https://ffmpeg.org/download.html"
        )
```

#### Task 1.3: Test Video File Handling
**Action**: Test with sample video files (MP4, MOV, etc.)

WhisperX's `load_audio()` function uses ffmpeg internally, so this should work automatically once ffmpeg is installed.

### Verification
- [ ] Video files can be selected in file browser
- [ ] ffmpeg warning appears if not installed
- [ ] Video files successfully transcribe (audio extracted automatically)
- [ ] No errors with various video formats

---

## Phase 2: Confidence Score Visualization

### Goals
- Extract segment-level confidence scores from WhisperX
- Store confidence data in JSON
- Display low-confidence segments with visual indicators (red squiggly underlines)
- Make confidence threshold configurable

### Implementation Tasks

#### Task 2.1: Capture Confidence Scores
**File**: [transcription.py](transcription.py)

**Update `transcribe_audio()` function** (around lines 35-72):

WhisperX provides `avg_logprob` which can be converted to a confidence proxy:

```python
# After alignment (around line 43), segments will have avg_logprob
aligned_result = whisperx.align(
    result["segments"],
    align_model,
    align_metadata,
    audio,
    device,
    return_char_alignments=False
)

# When building segment data (around lines 87-101):
for segment in aligned_result["segments"]:
    # Convert avg_logprob to percentage (approximate confidence)
    # avg_logprob typically ranges from -2 to 0, where 0 is perfect
    avg_logprob = segment.get("avg_logprob", -1.0)
    confidence = min(100, max(0, int((1 + avg_logprob) * 100)))

    segment_data = {
        "start": segment["start"],
        "end": segment["end"],
        "text": segment["text"].strip(),
        "speaker": segment.get("speaker", "Speaker"),
        "confidence": confidence  # NEW FIELD
    }
    transcript_data["segments"].append(segment_data)
```

#### Task 2.2: Add Confidence Threshold Setting
**File**: [config_manager.py](config_manager.py)

**Add new functions**:
```python
def get_confidence_threshold():
    """Get the confidence threshold from config."""
    config = load_config()
    return config.get("confidence_threshold", 70)  # Default 70%

def set_confidence_threshold(threshold):
    """Save the confidence threshold to config."""
    config = load_config()
    config["confidence_threshold"] = int(threshold)
    save_config(config)
```

#### Task 2.3: Update Settings Tab UI
**File**: [main.py](main.py)

**Update `create_settings_section()` method** (around lines 139-172):

```python
def create_settings_section(self, parent):
    # ... existing Groq API key UI ...

    # ... existing HuggingFace token UI ...

    # NEW: Confidence Threshold Setting
    ttk.Label(parent, text="Confidence Threshold (%):").pack(pady=(20, 0))

    threshold_frame = ttk.Frame(parent)
    threshold_frame.pack(pady=5)

    self.confidence_threshold_var = tk.StringVar(value=str(get_confidence_threshold()))
    confidence_spinbox = ttk.Spinbox(
        threshold_frame,
        from_=0,
        to=100,
        textvariable=self.confidence_threshold_var,
        width=10
    )
    confidence_spinbox.pack(side="left", padx=5)

    ttk.Label(threshold_frame, text="(Segments below this will be highlighted in Review)").pack(side="left")

    ttk.Button(parent, text="Save Threshold", command=self.save_confidence_threshold).pack(pady=10)

def save_confidence_threshold(self):
    """Save confidence threshold to config."""
    try:
        threshold = int(self.confidence_threshold_var.get())
        if 0 <= threshold <= 100:
            set_confidence_threshold(threshold)
            messagebox.showinfo("Success", "Confidence threshold saved!")
        else:
            messagebox.showerror("Error", "Threshold must be between 0 and 100")
    except ValueError:
        messagebox.showerror("Error", "Please enter a valid number")
```

#### Task 2.4: Add Confidence Highlighting to Review Tab
**File**: [main.py](main.py)

**Update `create_review_section()` method** (around lines 68-99):

Add tag configuration for low confidence:
```python
def create_review_section(self, parent):
    # ... existing code for dropdown and buttons ...

    # Text editor with scrollbar
    text_frame = ttk.Frame(parent)
    text_frame.pack(fill="both", expand=True, padx=10, pady=5)

    self.review_text = tk.Text(text_frame, wrap="word", height=20)
    self.review_text.pack(side="left", fill="both", expand=True)

    # Configure tag for low confidence highlighting
    self.review_text.tag_configure("low_confidence",
                                   foreground="red",
                                   underline=True,
                                   underlinefg="red")

    # ... rest of existing code ...
```

**Update `load_transcript_for_review()` method** (around lines 308-315):

```python
def load_transcript_for_review(self):
    """Load selected transcript into review text editor."""
    selected_index = self.review_dropdown.current()
    if selected_index < 0:
        return

    filepath = self.transcript_files[selected_index]['filepath']

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    self.current_review_file = filepath
    self.review_text.delete(1.0, tk.END)

    # Get confidence threshold
    threshold = get_confidence_threshold()

    # Display segments with confidence highlighting
    for i, segment in enumerate(data.get("segments", [])):
        speaker = segment.get("speaker", "Speaker")
        text = segment.get("text", "")
        confidence = segment.get("confidence", 100)  # Default to 100 if not present

        # Insert speaker label
        self.review_text.insert(tk.END, f"[{speaker}] ", "")

        # Insert text with highlighting if low confidence
        start_pos = self.review_text.index(tk.END + "-1c")
        self.review_text.insert(tk.END, text, "")
        end_pos = self.review_text.index(tk.END + "-1c")

        # Apply low confidence tag if below threshold
        if confidence < threshold:
            self.review_text.tag_add("low_confidence", start_pos, end_pos)

        self.review_text.insert(tk.END, "\n\n", "")
```

### Verification
- [ ] Confidence scores are captured and stored in JSON
- [ ] Settings tab has confidence threshold field (default 70%)
- [ ] Low-confidence segments show with red squiggly underline in Review tab
- [ ] Threshold changes are saved and persist across sessions
- [ ] Existing JSON files without confidence field still load (backward compatibility)

---

## Phase 3: Speaker Name Replacement

### Goals
- Detect unique speakers from transcript
- Provide UI fields to replace "Speaker 1", "Speaker 2" with custom names
- Apply replacements in formatting stage

### Implementation Tasks

#### Task 3.1: Add Speaker Detection
**File**: [main.py](main.py)

**Add new method** to TranscriptionApp class:

```python
def get_unique_speakers(self, json_filepath):
    """Get list of unique speakers from transcript."""
    with open(json_filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    speakers = set()
    for segment in data.get("segments", []):
        speaker = segment.get("speaker", "Speaker")
        speakers.add(speaker)

    return sorted(list(speakers))
```

#### Task 3.2: Add Speaker Name Fields to Format Tab
**File**: [main.py](main.py)

**Update `create_format_section()` method** (around lines 101-137):

```python
def create_format_section(self, parent):
    # Transcript selector
    ttk.Label(parent, text="Select Transcript:").pack(pady=(10, 0))

    select_frame = ttk.Frame(parent)
    select_frame.pack(pady=5)

    self.format_dropdown = ttk.Combobox(select_frame, width=40, state="readonly")
    self.format_dropdown.pack(side="left", padx=5)
    self.format_dropdown.bind("<<ComboboxSelected>>", self.on_transcript_selected_for_format)

    ttk.Button(select_frame, text="Refresh", command=self.refresh_format_transcripts).pack(side="left")

    # NEW: Speaker name replacement section
    self.speaker_frame = ttk.LabelFrame(parent, text="Speaker Names (Optional)", padding=10)
    self.speaker_frame.pack(fill="x", padx=10, pady=10)

    self.speaker_entries = {}  # Dictionary to hold speaker name entries

    # ... rest of existing format tab code (checkboxes, templates, etc.) ...

def on_transcript_selected_for_format(self, event=None):
    """When transcript is selected, populate speaker name fields."""
    selected_index = self.format_dropdown.current()
    if selected_index < 0:
        return

    filepath = self.transcript_files[selected_index]['filepath']
    speakers = self.get_unique_speakers(filepath)

    # Clear existing speaker entries
    for widget in self.speaker_frame.winfo_children():
        widget.destroy()
    self.speaker_entries.clear()

    # Create entry fields for each speaker
    if speakers:
        ttk.Label(self.speaker_frame,
                 text=f"{len(speakers)} speaker(s) detected",
                 font=("", 9, "bold")).pack(anchor="w", pady=(0, 10))

        for speaker in speakers:
            row = ttk.Frame(self.speaker_frame)
            row.pack(fill="x", pady=2)

            ttk.Label(row, text=f"{speaker}:", width=15).pack(side="left")
            entry = ttk.Entry(row, width=30)
            entry.pack(side="left", padx=5)
            entry.insert(0, "")  # Empty by default

            self.speaker_entries[speaker] = entry
    else:
        ttk.Label(self.speaker_frame, text="No speakers detected").pack()
```

#### Task 3.3: Apply Speaker Name Replacements in Formatting
**File**: [formatter.py](formatter.py)

**Update `format_transcript()` function signature and logic** (around lines 7-67):

```python
def format_transcript(json_filepath, api_key, speaker_mapping=None,
                     formatting_options=None, template="standard",
                     progress_callback=None):
    """
    Format transcript using Groq API.

    Args:
        json_filepath: Path to transcript JSON file
        api_key: Groq API key
        speaker_mapping: Dict mapping speaker labels to custom names (e.g., {"SPEAKER_00": "John"})
        formatting_options: Dict of formatting options (checkboxes)
        template: Template name to use
        progress_callback: Optional callback for progress updates

    Returns:
        Formatted transcript text
    """
    # ... existing code to load transcript ...

    # Build speaker replacement instructions
    speaker_instructions = ""
    if speaker_mapping:
        replacements = [f"'{old}' should be '{new}'"
                       for old, new in speaker_mapping.items() if new.strip()]
        if replacements:
            speaker_instructions = "\nSpeaker name replacements:\n" + "\n".join(replacements) + "\n"

    # Build prompt with speaker instructions
    # (will be enhanced in Phase 4 with formatting options and templates)
    prompt = f"""Format this transcript.
{speaker_instructions}
Transcript:
{transcript_text}"""

    # ... rest of existing Groq API call ...
```

**Update calling code in main.py** (around line 237-254):

```python
def start_formatting(self):
    # ... existing validation code ...

    # Build speaker mapping from entries
    speaker_mapping = {}
    for speaker_label, entry in self.speaker_entries.items():
        custom_name = entry.get().strip()
        if custom_name:
            speaker_mapping[speaker_label] = custom_name

    # Run formatting in background thread
    def format_text():
        try:
            def update_progress(msg):
                self.format_progress_label.config(text=msg)

            self.formatted_text = format_transcript(
                self.selected_json_file,
                api_key,
                speaker_mapping=speaker_mapping,  # NEW
                progress_callback=update_progress
            )

            # ... rest of existing code ...
```

### Verification
- [ ] Speaker fields appear when transcript is selected
- [ ] Correct number of speaker fields shown
- [ ] Custom names are applied in formatted output
- [ ] Empty speaker name fields are ignored
- [ ] Speaker labels update in formatted transcript

---

## Phase 4: Dynamic Formatting Options (Checkboxes)

### Goals
- Add checkboxes for common formatting transformations
- Build dynamic prompts based on selected options
- Options: filter swears, remove fillers, punctuation, grammar, timestamps, formal tone

### Implementation Tasks

#### Task 4.1: Add Checkbox UI to Format Tab
**File**: [main.py](main.py)

**Update `create_format_section()` method**:

```python
def create_format_section(self, parent):
    # ... existing transcript selector ...
    # ... existing speaker name section ...

    # NEW: Formatting Options Section
    options_frame = ttk.LabelFrame(parent, text="Formatting Options", padding=10)
    options_frame.pack(fill="x", padx=10, pady=10)

    # Create checkbox variables
    self.filter_swears_var = tk.BooleanVar(value=False)
    self.remove_fillers_var = tk.BooleanVar(value=False)
    self.improve_punctuation_var = tk.BooleanVar(value=True)  # Default ON
    self.clean_grammar_var = tk.BooleanVar(value=False)
    self.add_timestamps_var = tk.BooleanVar(value=False)
    self.formal_tone_var = tk.BooleanVar(value=False)

    # Create checkboxes (2 columns)
    left_col = ttk.Frame(options_frame)
    left_col.pack(side="left", fill="both", expand=True)

    right_col = ttk.Frame(options_frame)
    right_col.pack(side="left", fill="both", expand=True)

    ttk.Checkbutton(left_col, text="Filter swear words",
                   variable=self.filter_swears_var).pack(anchor="w", pady=2)
    ttk.Checkbutton(left_col, text="Remove filler words (um, uh, like)",
                   variable=self.remove_fillers_var).pack(anchor="w", pady=2)
    ttk.Checkbutton(left_col, text="Improve punctuation",
                   variable=self.improve_punctuation_var).pack(anchor="w", pady=2)

    ttk.Checkbutton(right_col, text="Clean up grammar",
                   variable=self.clean_grammar_var).pack(anchor="w", pady=2)
    ttk.Checkbutton(right_col, text="Add timestamps",
                   variable=self.add_timestamps_var).pack(anchor="w", pady=2)
    ttk.Checkbutton(right_col, text="Use formal/technical tone",
                   variable=self.formal_tone_var).pack(anchor="w", pady=2)

    # ... rest of format tab (templates section, format button, etc.) ...
```

#### Task 4.2: Create Dynamic Prompt Builder
**File**: [formatter.py](formatter.py)

**Add new function**:

```python
def build_formatting_instructions(formatting_options):
    """
    Build formatting instructions from options dict.

    Args:
        formatting_options: Dict with boolean flags for each option

    Returns:
        String with formatting instructions
    """
    instructions = []

    if formatting_options.get("filter_swears"):
        instructions.append("- Replace swear words and profanity with appropriate alternatives")

    if formatting_options.get("remove_fillers"):
        instructions.append("- Remove filler words (um, uh, like, you know, sort of)")

    if formatting_options.get("improve_punctuation"):
        instructions.append("- Add proper punctuation and capitalization")

    if formatting_options.get("clean_grammar"):
        instructions.append("- Fix grammatical errors while preserving meaning")

    if formatting_options.get("add_timestamps"):
        instructions.append("- Include timestamps from the original segments")

    if formatting_options.get("formal_tone"):
        instructions.append("- Convert to formal/technical tone where appropriate")
    else:
        instructions.append("- Preserve the original conversational tone")

    return "\n".join(instructions) if instructions else "- Preserve text as-is with minimal changes"
```

**Update `format_transcript()` to use options**:

```python
def format_transcript(json_filepath, api_key, speaker_mapping=None,
                     formatting_options=None, template="standard",
                     progress_callback=None):
    # ... existing code ...

    # Build formatting instructions
    format_instructions = build_formatting_instructions(formatting_options or {})

    # Build complete prompt (will be enhanced in Phase 5 with templates)
    prompt = f"""Format this transcript according to the following instructions:

{format_instructions}

{speaker_instructions}

Transcript:
{transcript_text}"""

    # ... existing Groq API call ...
```

#### Task 4.3: Update Format Button Handler
**File**: [main.py](main.py)

**Update `start_formatting()` method**:

```python
def start_formatting(self):
    # ... existing validation ...

    # Build speaker mapping
    speaker_mapping = {}
    for speaker_label, entry in self.speaker_entries.items():
        custom_name = entry.get().strip()
        if custom_name:
            speaker_mapping[speaker_label] = custom_name

    # NEW: Build formatting options
    formatting_options = {
        "filter_swears": self.filter_swears_var.get(),
        "remove_fillers": self.remove_fillers_var.get(),
        "improve_punctuation": self.improve_punctuation_var.get(),
        "clean_grammar": self.clean_grammar_var.get(),
        "add_timestamps": self.add_timestamps_var.get(),
        "formal_tone": self.formal_tone_var.get()
    }

    # Run formatting
    def format_text():
        try:
            def update_progress(msg):
                self.format_progress_label.config(text=msg)

            self.formatted_text = format_transcript(
                self.selected_json_file,
                api_key,
                speaker_mapping=speaker_mapping,
                formatting_options=formatting_options,  # NEW
                progress_callback=update_progress
            )

            # ... rest of existing code ...
```

### Verification
- [ ] All checkboxes appear in Format tab
- [ ] Checkbox states are correctly captured
- [ ] Prompts change based on selected options
- [ ] Each option produces expected formatting behavior
- [ ] Multiple options can be combined

---

## Phase 5: Multiple Format Templates

### Goals
- Create 4 output templates: Standard, Q&A, Clean Text, Timestamped Captions
- Add template selector to Format tab
- Implement template-specific prompt logic

### Implementation Tasks

#### Task 5.1: Create Template System
**File**: [formatter.py](formatter.py)

**Add template definitions**:

```python
TEMPLATES = {
    "standard": {
        "name": "Standard Transcript",
        "description": "Speaker labels, timestamps, paragraph breaks",
        "system_prompt": """Format this as a standard transcript with:
- Clear speaker labels (use custom names if provided)
- Timestamps at the start of each speaker's turn
- Natural paragraph breaks for readability
- Preserve the conversational flow"""
    },

    "qa": {
        "name": "Q&A Format",
        "description": "Question/Answer structure",
        "system_prompt": """Format this as a Q&A transcript with:
- Clear Q: and A: labels for questions and answers
- Use speaker names if provided to identify questioner/responder
- Group related exchanges together
- Remove timestamps unless specifically requested"""
    },

    "clean": {
        "name": "Clean Text",
        "description": "No timestamps or speaker labels, flowing paragraphs",
        "system_prompt": """Format this as clean flowing text with:
- NO speaker labels or timestamps
- Smooth transitions between speakers
- Natural paragraph structure
- Read like a written article or story"""
    },

    "captions": {
        "name": "Timestamped Captions",
        "description": "SRT/VTT caption style",
        "system_prompt": """Format this as caption-style segments with:
- Precise timestamps for each caption block
- Short segments (2-3 lines max per segment)
- Proper line breaks for readability on screen
- Format: [HH:MM:SS] Caption text"""
    }
}

def get_template_prompt(template_name):
    """Get the system prompt for a template."""
    template = TEMPLATES.get(template_name, TEMPLATES["standard"])
    return template["system_prompt"]
```

**Update `format_transcript()` to use templates**:

```python
def format_transcript(json_filepath, api_key, speaker_mapping=None,
                     formatting_options=None, template="standard",
                     progress_callback=None):
    # ... existing code to load transcript ...

    # Get template prompt
    template_prompt = get_template_prompt(template)

    # Build formatting instructions
    format_instructions = build_formatting_instructions(formatting_options or {})

    # Build speaker instructions
    speaker_instructions = ""
    if speaker_mapping:
        replacements = [f"'{old}' should be '{new}'"
                       for old, new in speaker_mapping.items() if new.strip()]
        if replacements:
            speaker_instructions = "\nSpeaker name replacements:\n" + "\n".join(replacements) + "\n"

    # Build complete prompt
    prompt = f"""{template_prompt}

Additional formatting instructions:
{format_instructions}

{speaker_instructions}

Transcript:
{transcript_text}"""

    # ... existing Groq API call ...
```

#### Task 5.2: Add Template Selector to UI
**File**: [main.py](main.py)

**Update `create_format_section()` method**:

```python
def create_format_section(self, parent):
    # ... existing transcript selector ...
    # ... existing speaker name section ...
    # ... existing formatting options checkboxes ...

    # NEW: Template Selection Section
    template_frame = ttk.LabelFrame(parent, text="Output Template", padding=10)
    template_frame.pack(fill="x", padx=10, pady=10)

    ttk.Label(template_frame, text="Select format template:").pack(anchor="w", pady=(0, 5))

    self.template_var = tk.StringVar(value="standard")

    templates = [
        ("standard", "Standard Transcript - Speaker labels, timestamps, paragraphs"),
        ("qa", "Q&A Format - Question/Answer structure"),
        ("clean", "Clean Text - No labels/timestamps, flowing text"),
        ("captions", "Timestamped Captions - SRT/VTT style")
    ]

    for template_id, description in templates:
        ttk.Radiobutton(
            template_frame,
            text=description,
            variable=self.template_var,
            value=template_id
        ).pack(anchor="w", pady=2)

    # ... existing format button and result display ...
```

#### Task 5.3: Update Format Handler
**File**: [main.py](main.py)

**Update `start_formatting()` method**:

```python
def start_formatting(self):
    # ... existing validation ...
    # ... existing speaker mapping ...
    # ... existing formatting options ...

    # Get selected template
    template = self.template_var.get()

    # Run formatting
    def format_text():
        try:
            def update_progress(msg):
                self.format_progress_label.config(text=msg)

            self.formatted_text = format_transcript(
                self.selected_json_file,
                api_key,
                speaker_mapping=speaker_mapping,
                formatting_options=formatting_options,
                template=template,  # NEW
                progress_callback=update_progress
            )

            # ... rest of existing code ...
```

### Verification
- [ ] All 4 template options appear as radio buttons
- [ ] Selected template affects the output format
- [ ] Standard template includes speakers and timestamps
- [ ] Q&A template properly identifies questions and answers
- [ ] Clean template removes all labels and timestamps
- [ ] Captions template creates short, timestamped segments
- [ ] Templates work correctly with formatting options and speaker names

---

## Phase 6: Enhanced Data Flow & Integration

### Goals
- Send structured segment data (not just full_transcript) to Groq when needed
- Update Review tab to show speaker labels more prominently
- Ensure backward compatibility with existing JSON files

### Implementation Tasks

#### Task 6.1: Update Formatter to Use Segment Data
**File**: [formatter.py](formatter.py)

**Update `format_transcript()` to optionally use segments**:

```python
def format_transcript(json_filepath, api_key, speaker_mapping=None,
                     formatting_options=None, template="standard",
                     progress_callback=None):
    if progress_callback:
        progress_callback("Loading transcript...")

    with open(json_filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Build transcript with speaker structure if segments available
    segments = data.get("segments", [])

    if segments and template in ["standard", "qa", "captions"]:
        # Use structured segments for templates that need speaker info
        transcript_text = build_structured_transcript(segments, formatting_options)
    else:
        # Use simple full transcript for clean template
        transcript_text = data["full_transcript"]

    # ... rest of existing function ...

def build_structured_transcript(segments, formatting_options=None):
    """Build transcript with speaker labels and timestamps from segments."""
    lines = []

    for segment in segments:
        speaker = segment.get("speaker", "Speaker")
        text = segment.get("text", "")
        start = segment.get("start", 0)

        # Format timestamp
        minutes = int(start // 60)
        seconds = int(start % 60)
        timestamp = f"[{minutes:02d}:{seconds:02d}]"

        # Build line with speaker and timestamp
        if formatting_options and formatting_options.get("add_timestamps"):
            lines.append(f"{timestamp} {speaker}: {text}")
        else:
            lines.append(f"{speaker}: {text}")

    return "\n".join(lines)
```

#### Task 6.2: Enhance Review Tab Display
**File**: [main.py](main.py)

**Update `load_transcript_for_review()` to show more info**:

```python
def load_transcript_for_review(self):
    """Load selected transcript into review text editor with enhanced display."""
    selected_index = self.review_dropdown.current()
    if selected_index < 0:
        return

    filepath = self.transcript_files[selected_index]['filepath']

    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)

    self.current_review_file = filepath
    self.review_text.delete(1.0, tk.END)

    # Configure additional tags for better display
    self.review_text.tag_configure("speaker", foreground="blue", font=("", 10, "bold"))
    self.review_text.tag_configure("timestamp", foreground="gray")

    threshold = get_confidence_threshold()

    # Display segments with enhanced formatting
    for segment in data.get("segments", []):
        speaker = segment.get("speaker", "Speaker")
        text = segment.get("text", "")
        confidence = segment.get("confidence", 100)
        start = segment.get("start", 0)

        # Format timestamp
        minutes = int(start // 60)
        seconds = int(start % 60)
        timestamp = f"[{minutes:02d}:{seconds:02d}]"

        # Insert timestamp
        self.review_text.insert(tk.END, f"{timestamp} ", "timestamp")

        # Insert speaker label
        self.review_text.insert(tk.END, f"[{speaker}] ", "speaker")

        # Insert text with confidence highlighting
        start_pos = self.review_text.index(tk.END + "-1c")
        self.review_text.insert(tk.END, text, "")
        end_pos = self.review_text.index(tk.END + "-1c")

        if confidence < threshold:
            self.review_text.tag_add("low_confidence", start_pos, end_pos)

        self.review_text.insert(tk.END, "\n\n", "")
```

#### Task 6.3: Backward Compatibility Check
**Action**: Ensure all file loading handles missing fields gracefully

**Files to check**:
- [main.py](main.py) - segment loading with `.get()` for confidence
- [formatter.py](formatter.py) - handle segments without confidence
- [transcription.py](transcription.py) - existing JSON structure preserved

**Pattern to use everywhere**:
```python
confidence = segment.get("confidence", 100)  # Default 100% if not present
speaker = segment.get("speaker", "Speaker")  # Default "Speaker" if not present
```

### Verification
- [ ] Existing JSON files (without confidence) still load and work
- [ ] Review tab shows timestamps, speakers, and confidence
- [ ] Segment structure is used for appropriate templates
- [ ] Clean template still works with full_transcript
- [ ] No errors when loading old transcripts

---

## Testing Checklist

### End-to-End Testing

#### Test 1: Video File Transcription
- [ ] Select a video file (MP4, MOV, etc.)
- [ ] Verify transcription completes successfully
- [ ] Check JSON has all required fields (segments, speakers, confidence)

#### Test 2: Confidence Score Workflow
- [ ] Set confidence threshold to 80% in Settings
- [ ] Load a transcript in Review tab
- [ ] Verify low-confidence segments are highlighted with red underline
- [ ] Change threshold to 50% and reload - verify fewer highlights

#### Test 3: Speaker Name Replacement
- [ ] Load transcript with multiple speakers in Format tab
- [ ] Verify speaker fields appear automatically
- [ ] Enter custom names (e.g., "John", "Sarah")
- [ ] Format the transcript
- [ ] Verify custom names appear in output instead of "SPEAKER_00", "SPEAKER_01"

#### Test 4: Formatting Options
- [ ] Test each checkbox individually (filter swears, remove fillers, etc.)
- [ ] Test multiple checkboxes together
- [ ] Verify each option produces expected changes in output

#### Test 5: Format Templates
- [ ] Test Standard template - verify speakers and timestamps appear
- [ ] Test Q&A template - verify question/answer structure
- [ ] Test Clean template - verify no speakers or timestamps
- [ ] Test Captions template - verify short timestamped segments

#### Test 6: Complete Workflow
- [ ] Upload video file → transcribe
- [ ] Review with confidence highlighting
- [ ] Set speaker names
- [ ] Select formatting options
- [ ] Choose template
- [ ] Format
- [ ] Save to DOCX
- [ ] Open DOCX and verify all settings applied correctly

#### Test 7: Backward Compatibility
- [ ] Load old JSON file (without confidence scores)
- [ ] Verify no errors in Review tab
- [ ] Verify formatting still works
- [ ] Verify DOCX export still works

---

## File Structure Summary

```
d:\Transcription\
├── main.py                    # Main GUI application (HEAVILY MODIFIED)
├── transcription.py           # Transcription logic (MODIFIED - add confidence)
├── formatter.py               # Formatting logic (HEAVILY MODIFIED - templates, options)
├── config_manager.py          # Config management (MODIFIED - add threshold)
├── requirements.txt           # Dependencies (NO CHANGE)
├── config.json               # User config (MODIFIED - new threshold field)
├── transcripts\              # JSON transcripts (MODIFIED - new confidence field)
├── completed\                # Output DOCX files
└── IMPLEMENTATION_PLAN.md    # This file

Modified Files:
- main.py (Lines: 68-99, 101-137, 139-172, 176-178, 237-254, 308-315 + many new methods)
- transcription.py (Lines: 35-72, 87-101 - add confidence capture)
- formatter.py (Entire file restructured for templates and options)
- config_manager.py (Add confidence threshold functions)
```

---

## Estimated Implementation Time

| Phase | Estimated Time | Complexity |
|-------|---------------|------------|
| Phase 1: Video Support | 1-2 hours | Low |
| Phase 2: Confidence Scores | 3-4 hours | Medium |
| Phase 3: Speaker Names | 2-3 hours | Medium |
| Phase 4: Formatting Checkboxes | 2-3 hours | Medium |
| Phase 5: Templates | 3-4 hours | Medium-High |
| Phase 6: Integration | 2-3 hours | Medium |
| Testing & Debugging | 3-4 hours | - |
| **TOTAL** | **16-23 hours** | - |

---

## Next Steps for Implementation

1. **Start with Phase 1** (Video Support) - easiest to verify and test
2. **Then Phase 2** (Confidence Scores) - foundational for review workflow
3. **Phases 3-5** can be done in any order - they're largely independent
4. **Phase 6** should be done last - it integrates everything
5. **Test thoroughly** after each phase before moving to the next

---

## Notes for Claude Code (Web)

When implementing this plan:

1. **Windows Commands**: Remember to use Windows path syntax (backslashes) and commands (`dir` not `ls`, etc.)

2. **Test Incrementally**: After each phase, run the app and test the new features before proceeding

3. **Backup**: Consider creating a git branch for this work:
   ```bash
   git checkout -b feature/fiverr-enhancements
   ```

4. **Dependencies**: No new pip packages needed - all features use existing libraries

5. **Error Handling**: Add try/except blocks around all new features to handle edge cases gracefully

6. **UI Layout**: The Format tab will be quite busy - consider using a scrollable frame if needed

7. **Prompt Engineering**: You may need to iterate on the template prompts to get optimal results from Groq

Good luck with implementation! This will transform the app into a professional transcription tool suitable for Fiverr work.
