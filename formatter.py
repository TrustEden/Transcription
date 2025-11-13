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
