# Fresh Windows Installation Guide for Transcription App

## Required Software (Non-Python/Non-Pip)

### 1. **Python 3.11**
   - **Download:** https://www.python.org/downloads/
   - **Version:** Python 3.11.x (recommended for compatibility)
   - **Installation Notes:**
     - Check "Add Python to PATH" during installation
     - Choose "Install for all users" if you want system-wide access
     - Install location: Default is fine, or choose `C:\Python311`

### 2. **FFmpeg** (REQUIRED - Core dependency)
   - **Download:** https://www.gyan.dev/ffmpeg/builds/
   - **Recommended Build:** ffmpeg-release-full.7z (latest version)
   - **Installation Steps:**
     1. Download the full build
     2. Extract to a permanent location (e.g., `C:\ffmpeg` or `D:\ffmpeg`)
     3. Add FFmpeg to System PATH:
        - Right-click "This PC" → Properties → Advanced System Settings
        - Click "Environment Variables"
        - Under "System Variables", find "Path", click "Edit"
        - Click "New" and add: `C:\ffmpeg\bin` (or wherever you extracted it)
        - Click OK on all dialogs
     4. Verify installation: Open Command Prompt and type `ffmpeg -version`

### 3. **Git** (Optional but recommended)
   - **Download:** https://git-scm.com/download/win
   - **Installation Notes:**
     - Use default settings during installation
     - Recommended: Choose "Git from the command line and also from 3rd-party software"

### 4. **Visual C++ Redistributable** (Required for PyTorch/CUDA)
   - **Download:** https://aka.ms/vs/17/release/vc_redist.x64.exe
   - **Why:** Required by PyTorch and various Python packages
   - **Installation:** Just run the installer with default settings

### 5. **CUDA Toolkit** (OPTIONAL - Only if you have NVIDIA GPU)
   - **Download:** https://developer.nvidia.com/cuda-downloads
   - **Version:** CUDA 11.8 or 12.1 (check PyTorch compatibility)
   - **Installation Notes:**
     - Only install if you have an NVIDIA GPU and want GPU acceleration
     - Follow the installer wizard
     - This is a large download (~3GB)
   - **Skip if:** You only have CPU or integrated graphics (app will work fine on CPU)

### 6. **Text Editor/IDE** (Optional)
   - **VS Code:** https://code.visualstudio.com/
   - **PyCharm Community:** https://www.jetbrains.com/pycharm/download/
   - **Notepad++:** https://notepad-plus-plus.org/

---

## Python Dependencies (Install via pip)

After installing Python, open Command Prompt and run:

```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install all required packages
pip install whisperx
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
pip install groq
pip install python-docx
pip install pyannote.audio
pip install faster-whisper
```

**Note:** If you installed CUDA and have an NVIDIA GPU, use this instead for PyTorch:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

---

## API Keys & Tokens (Required for full functionality)

### 1. **Groq API Key**
   - **Get it from:** https://console.groq.com
   - **Purpose:** Required for transcript formatting with AI
   - **Free tier:** Yes, generous limits
   - **Setup:** Enter in the app's Settings tab

### 2. **HuggingFace Token**
   - **Get it from:** https://huggingface.co/settings/tokens
   - **Purpose:** Required for speaker diarization (identifying different speakers)
   - **Free tier:** Yes
   - **Setup:**
     1. Create account at HuggingFace
     2. Go to Settings → Access Tokens
     3. Create a new token (Read access is sufficient)
     4. Accept the model agreement at: https://huggingface.co/pyannote/speaker-diarization
     5. Enter token in the app's Settings tab
   - **Optional:** Skip if you don't need speaker identification

---

## Installation Order Checklist

- [ ] 1. Install Python 3.11 (add to PATH)
- [ ] 2. Install Visual C++ Redistributable
- [ ] 3. Install FFmpeg and add to PATH
- [ ] 4. (Optional) Install CUDA if you have NVIDIA GPU
- [ ] 5. (Optional) Install Git
- [ ] 6. (Optional) Install text editor/IDE
- [ ] 7. Upgrade pip: `python -m pip install --upgrade pip`
- [ ] 8. Install Python packages (see commands above)
- [ ] 9. Download/copy transcription app files
- [ ] 10. Get Groq API key
- [ ] 11. Get HuggingFace token (optional)
- [ ] 12. Run the app: `python main.py`
- [ ] 13. Configure API keys in Settings tab

---

## Verifying Installation

Open Command Prompt and run these commands to verify everything is installed:

```bash
# Check Python
python --version
# Should show: Python 3.11.x

# Check pip
pip --version
# Should show pip version

# Check FFmpeg (CRITICAL)
ffmpeg -version
# Should show FFmpeg version info

# Check if Python packages are installed
pip list | findstr whisperx
pip list | findstr torch
pip list | findstr groq
pip list | findstr python-docx
pip list | findstr pyannote
```

---

## File Structure After Installation

```
D:\Transcription\          (or wherever you put the app)
├── main.py
├── transcription.py
├── formatter.py
├── config_manager.py
├── transcripts\           (created automatically)
└── completed\             (created automatically)
```

---

## Common Issues & Solutions

### Issue: "ffmpeg is not recognized"
**Solution:** FFmpeg is not in PATH. Re-do step 2 of FFmpeg installation.

### Issue: "No module named 'whisperx'"
**Solution:** Run `pip install whisperx`

### Issue: "CUDA not available" (if you have NVIDIA GPU)
**Solution:** Install CUDA toolkit and reinstall PyTorch with CUDA support

### Issue: Speaker diarization fails
**Solution:**
1. Make sure you have a HuggingFace token
2. Accept the pyannote model agreement at: https://huggingface.co/pyannote/speaker-diarization

---

## Storage Requirements

- **Python 3.11:** ~100 MB
- **FFmpeg:** ~200 MB
- **Python packages:** ~2-3 GB (includes PyTorch, WhisperX models)
- **CUDA Toolkit (optional):** ~3-4 GB
- **Working space:** 500 MB - 1 GB for transcripts and temp files

**Total:** ~3-4 GB without CUDA, ~7-8 GB with CUDA

---

## After Fresh Install

1. Copy the transcription app folder to your D: drive
2. Run `python main.py` to start
3. The first time you transcribe, WhisperX will download AI models (~500MB)
4. These models are cached and only downloaded once

Good luck with your fresh install!
