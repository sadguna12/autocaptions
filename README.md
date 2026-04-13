# 🎬 Auto Caption Agent

An AI agent that generates **word-by-word styled captions** from videos — like Instagram Reels and YouTube Shorts.

---

## 📁 Project Structure

```
captions-agent/
│
├── input/                  ← Put your video files here
├── output/                 ← Generated audio & captions saved here
│
├── agent/
│   ├── __init__.py
│   ├── audio_extractor.py  ← Extracts audio from video (ffmpeg)
│   └── transcriber.py      ← Transcribes audio to text (Whisper)
│
├── main.py                 ← CLI entry point
├── requirements.txt        ← Python dependencies
└── README.md               ← This file
```

---

## ⚙️ Setup

### 1. Install ffmpeg (required)

| OS | Command |
|---|---|
| Windows | Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to `PATH` |
| macOS | `brew install ffmpeg` |
| Ubuntu | `sudo apt install ffmpeg` |

Verify: `ffmpeg -version`

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

> ⚠️ PyTorch is required by Whisper. If not installed automatically, run:
> `pip install torch`

---

## 🚀 Usage

### Phase 1 — Transcribe a video

```bash
python main.py --video input/your_video.mp4
```

**With options:**
```bash
python main.py --video input/your_video.mp4 --model small --lang en
```

| Flag | Default | Description |
|---|---|---|
| `--video` | *(required)* | Path to your video file |
| `--model` | `base` | Whisper model: `tiny`, `base`, `small`, `medium`, `large` |
| `--lang` | auto-detect | Language code: `en`, `hi`, `es`, etc. |
| `--output` | `output/` | Where to save results |

### Expected output

```json
[
  { "start": 0.0,  "end": 2.5, "text": "Hello bro welcome" },
  { "start": 2.5,  "end": 5.1, "text": "to the auto caption agent" }
]
```

Files saved to `output/`:
- `*_audio.wav` — extracted audio
- `segments.json` — timestamped transcript

---

## 🧱 Whisper Model Guide

| Model | Speed | Accuracy | RAM |
|---|---|---|---|
| `tiny` | ⚡⚡⚡ | ⭐ | ~1 GB |
| `base` | ⚡⚡ | ⭐⭐ | ~1 GB |
| `small` | ⚡ | ⭐⭐⭐ | ~2 GB |
| `medium` | 🐢 | ⭐⭐⭐⭐ | ~5 GB |
| `large` | 🐢🐢 | ⭐⭐⭐⭐⭐ | ~10 GB |

**Recommendation:** Start with `base` for testing, switch to `small` for production.

---

## 🗺️ Roadmap

| Phase | Feature | Status |
|---|---|---|
| 1 | Audio extraction + Whisper transcription | ✅ Done |
| 2 | Word-level timestamp distribution | 🔜 Next |
| 3 | `.srt` and styled `.ass` caption export | 🔜 Planned |
| 4 | Streamlit UI for upload + preview + download | 🔜 Planned |
