import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import threading
from transcription import transcribe_audio, get_saved_transcripts
from formatter import format_transcript, save_to_docx
from config_manager import get_groq_api_key, set_groq_api_key, get_huggingface_token, set_huggingface_token

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

        # Format with speaker labels for easier review
        formatted_review = []
        for segment in data.get("segments", []):
            speaker = segment.get("speaker", "Speaker")
            text = segment.get("text", "")
            formatted_review.append(f"[{speaker}] {text}")

        review_content = "\n\n".join(formatted_review)
        self.review_text.insert(1.0, review_content)

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

if __name__ == "__main__":
    root = tk.Tk()
    app = TranscriptionApp(root)
    root.mainloop()
