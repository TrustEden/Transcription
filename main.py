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
