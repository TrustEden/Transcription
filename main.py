import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
import subprocess
import sys
from transcription import transcribe_audio, get_saved_transcripts
from formatter import format_transcript, save_to_docx
from config_manager import get_groq_api_key, set_groq_api_key, get_huggingface_token, set_huggingface_token, get_confidence_threshold, set_confidence_threshold

class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Transcription Processing Tool")
        self.root.geometry("700x600")

        self.selected_audio_file = None
        self.selected_json_file = None
        self.formatted_text = ""

        # Check ffmpeg availability
        if not self.check_ffmpeg():
            messagebox.showwarning(
                "ffmpeg Not Found",
                "ffmpeg is required for video file processing.\n"
                "Please install ffmpeg and add it to your system PATH.\n"
                "Download from: https://ffmpeg.org/download.html"
            )

        self.create_widgets()

    def check_ffmpeg(self):
        """Check if ffmpeg is available."""
        try:
            subprocess.run(['ffmpeg', '-version'],
                          capture_output=True,
                          check=True,
                          creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def create_widgets(self):
        # Create notebook (tabbed interface)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # Section 1: Transcription
        transcription_frame = ttk.Frame(notebook)
        notebook.add(transcription_frame, text="1. Transcription")
        self.create_transcription_section(transcription_frame)

        # Section 2: Review Raw Transcript
        review_frame = ttk.Frame(notebook)
        notebook.add(review_frame, text="2. Review & Edit")
        self.create_review_section(review_frame)

        # Section 3: Formatting & Final Review
        formatting_frame = ttk.Frame(notebook)
        notebook.add(formatting_frame, text="3. Format & Save")
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

    def create_review_section(self, parent):
        """Section for reviewing and editing raw transcript before formatting."""
        # Dropdown for saved transcripts
        ttk.Label(parent, text="Select Transcript to Review:").pack(pady=(10, 0))

        select_frame = ttk.Frame(parent)
        select_frame.pack(pady=5)

        self.review_transcript_dropdown = ttk.Combobox(select_frame, width=40, state="readonly")
        self.review_transcript_dropdown.pack(side="left", padx=5)

        ttk.Button(select_frame, text="Refresh", command=self.refresh_review_transcripts).pack(side="left")
        ttk.Button(select_frame, text="Load", command=self.load_transcript_for_review).pack(side="left", padx=5)

        # Text editor for raw transcript
        ttk.Label(parent, text="Raw Transcript (editable):").pack(pady=(10, 0))

        text_frame = ttk.Frame(parent)
        text_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.review_text = tk.Text(text_frame, wrap="word", height=20)
        self.review_text.pack(side="left", fill="both", expand=True)

        # Configure tag for low confidence highlighting
        self.review_text.tag_configure("low_confidence",
                                       foreground="red",
                                       underline=True)

        scrollbar = ttk.Scrollbar(text_frame, command=self.review_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.review_text.config(yscrollcommand=scrollbar.set)

        # Save changes button
        ttk.Button(parent, text="Save Changes to Transcript", command=self.save_reviewed_transcript).pack(pady=10)

        # Initialize transcript list
        self.refresh_review_transcripts()

    def create_formatting_section(self, parent):
        # Dropdown for saved transcripts
        ttk.Label(parent, text="Select Transcript:").pack(pady=(10, 0))

        select_frame = ttk.Frame(parent)
        select_frame.pack(pady=5)

        self.transcript_dropdown = ttk.Combobox(select_frame, width=40, state="readonly")
        self.transcript_dropdown.pack(side="left", padx=5)
        self.transcript_dropdown.bind("<<ComboboxSelected>>", self.on_transcript_selected_for_format)

        ttk.Button(select_frame, text="Refresh", command=self.refresh_transcripts).pack(side="left")

        # Speaker name replacement section
        self.speaker_frame = ttk.LabelFrame(parent, text="Speaker Names (Optional)", padding=10)
        self.speaker_frame.pack(fill="x", padx=10, pady=10)

        self.speaker_entries = {}  # Dictionary to hold speaker name entries

        # Formatting Options Section
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

        # Template Selection Section
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

        ttk.Button(parent, text="Save Groq API Key", command=self.save_api_key).pack(pady=10)

        # HuggingFace Token
        ttk.Label(parent, text="HuggingFace Token (for speaker diarization):").pack(pady=(20, 0))

        self.hf_token_entry = ttk.Entry(parent, width=50, show="*")
        self.hf_token_entry.pack(pady=5)

        # Load existing HF token
        hf_token = get_huggingface_token()
        if hf_token:
            self.hf_token_entry.insert(0, hf_token)

        ttk.Button(parent, text="Save HuggingFace Token", command=self.save_hf_token).pack(pady=10)

        # Confidence Threshold Setting
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

        # Instructions
        instructions = """
Instructions:
1. Get a Groq API key from: https://console.groq.com
2. Get a HuggingFace token from: https://huggingface.co/settings/tokens
   (Required for speaker diarization - optional if you don't need it)
        """
        ttk.Label(parent, text=instructions, justify="left", foreground="gray").pack(pady=(20, 0))

    def browse_audio_file(self):
        filetypes = [
            ("Audio/Video Files", "*.mp3 *.wav *.m4a *.mp4 *.mov *.avi *.mkv *.webm"),
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

    def get_unique_speakers(self, json_filepath):
        """Get list of unique speakers from transcript."""
        import json
        with open(json_filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        speakers = set()
        for segment in data.get("segments", []):
            speaker = segment.get("speaker", "Speaker")
            speakers.add(speaker)

        return sorted(list(speakers))

    def on_transcript_selected_for_format(self, event=None):
        """When transcript is selected, populate speaker name fields."""
        selected_index = self.transcript_dropdown.current()
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

        # Build speaker mapping from entries
        speaker_mapping = {}
        for speaker_label, entry in self.speaker_entries.items():
            custom_name = entry.get().strip()
            if custom_name:
                speaker_mapping[speaker_label] = custom_name

        # Build formatting options
        formatting_options = {
            "filter_swears": self.filter_swears_var.get(),
            "remove_fillers": self.remove_fillers_var.get(),
            "improve_punctuation": self.improve_punctuation_var.get(),
            "clean_grammar": self.clean_grammar_var.get(),
            "add_timestamps": self.add_timestamps_var.get(),
            "formal_tone": self.formal_tone_var.get()
        }

        # Get selected template
        template = self.template_var.get()

        # Run formatting in background thread
        def format_text():
            try:
                def update_progress(msg):
                    self.format_progress_label.config(text=msg)

                self.formatted_text = format_transcript(
                    self.selected_json_file,
                    api_key,
                    speaker_mapping=speaker_mapping,
                    formatting_options=formatting_options,
                    template=template,
                    progress_callback=update_progress
                )

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

    def refresh_review_transcripts(self):
        """Refresh the transcript dropdown in the review section."""
        transcripts = get_saved_transcripts()
        display_names = [f"{t['project_name']} - {t['timestamp'][:10]}" for t in transcripts]
        self.review_transcript_dropdown['values'] = display_names

        # Store the mapping
        self.review_transcript_files = transcripts

    def load_transcript_for_review(self):
        """Load selected transcript into the review text editor."""
        if not self.review_transcript_dropdown.get():
            messagebox.showerror("Error", "Please select a transcript")
            return

        # Get selected transcript file
        selected_index = self.review_transcript_dropdown.current()
        if selected_index < 0:
            return

        self.current_review_file = self.review_transcript_files[selected_index]['filepath']

        # Load transcript JSON
        import json
        with open(self.current_review_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Display the full transcript in the text editor
        self.review_text.delete(1.0, tk.END)

        # Configure additional tags for better display
        self.review_text.tag_configure("speaker", foreground="blue", font=("", 10, "bold"))
        self.review_text.tag_configure("timestamp", foreground="gray")

        # Get confidence threshold
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

    def save_reviewed_transcript(self):
        """Save edited transcript back to JSON file."""
        if not hasattr(self, 'current_review_file') or not self.current_review_file:
            messagebox.showerror("Error", "No transcript loaded")
            return

        # Get edited text
        edited_text = self.review_text.get(1.0, tk.END).strip()

        # Load original JSON
        import json
        with open(self.current_review_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Parse edited text back into segments
        lines = edited_text.split("\n\n")
        segments = []

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            # Try to parse speaker label
            if line.startswith("[") and "]" in line:
                close_bracket = line.index("]")
                speaker = line[1:close_bracket]
                text = line[close_bracket + 1:].strip()
            else:
                speaker = "Speaker"
                text = line

            # Keep original timing if available
            if i < len(data["segments"]):
                segment = data["segments"][i].copy()
                segment["text"] = text
                segment["speaker"] = speaker
            else:
                segment = {
                    "start": 0,
                    "end": 0,
                    "text": text,
                    "speaker": speaker
                }
            segments.append(segment)

        # Update data
        data["segments"] = segments
        data["full_transcript"] = " ".join([s["text"] for s in segments])

        # Save back to JSON
        with open(self.current_review_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        messagebox.showinfo("Success", "Transcript updated successfully!")

    def save_api_key(self):
        api_key = self.api_key_entry.get().strip()
        if api_key:
            set_groq_api_key(api_key)
            messagebox.showinfo("Success", "Groq API key saved!")
        else:
            messagebox.showerror("Error", "Please enter an API key")

    def save_hf_token(self):
        hf_token = self.hf_token_entry.get().strip()
        if hf_token:
            set_huggingface_token(hf_token)
            messagebox.showinfo("Success", "HuggingFace token saved!")
        else:
            messagebox.showerror("Error", "Please enter a HuggingFace token")

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

if __name__ == "__main__":
    root = tk.Tk()
    app = TranscriptionApp(root)
    root.mainloop()
