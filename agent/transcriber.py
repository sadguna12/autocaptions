"""
transcriber.py
--------------
Transcribes audio to text with timestamps using OpenAI Whisper.

How Whisper works:
- It's a neural network trained on 680,000 hours of audio
- It returns text split into "segments" (phrases), each with start/end times
- We use the word_timestamps=True flag to get per-word timing data too

Model sizes (speed vs accuracy tradeoff):
  tiny   → fastest, least accurate  (~39MB)
  base   → good for MVP             (~74MB)  ← DEFAULT
  small  → better accuracy          (~244MB)
  medium → great accuracy           (~769MB)
  large  → best accuracy            (~1.5GB)
"""

import whisper  # type: ignore  (installed via: pip install openai-whisper)
import json
import os
from typing import Literal, Optional, Tuple


# Type hint for valid model sizes
WhisperModel = Literal["tiny", "base", "small", "medium", "large"]


def transcribe(
    audio_path: str,
    model_size: WhisperModel = "base",
    language: Optional[str] = None,
    output_dir: str = "output",
) -> Tuple[list, dict]:
    """
    Transcribe an audio file using OpenAI Whisper.

    Args:
        audio_path  : Path to the .wav audio file
        model_size  : Whisper model to use (default: "base")
        language    : Force a language code like "en", "hi" (None = auto-detect)
        output_dir  : Where to save the output segments.json

    Returns:
        Tuple of:
        - segments       : Clean list of { "start", "end", "text" } dicts
        - whisper_result : Raw Whisper output dict (contains per-word data for Phase 2)

    Raises:
        FileNotFoundError : If the audio file doesn't exist
    """

    if not os.path.exists(audio_path):
        raise FileNotFoundError(f"Audio file not found: {audio_path}")

    print(f"[Transcriber] Loading Whisper model: '{model_size}'")
    print(f"[Transcriber] (First run will download the model — this is one-time only)")

    # Load the Whisper model (auto-downloaded on first use)
    model = whisper.load_model(model_size)

    print(f"[Transcriber] Transcribing: {audio_path}")
    if language:
        print(f"[Transcriber] Language forced: {language}")

    # Run transcription
    # word_timestamps=True tells Whisper to also return per-word timing
    result = model.transcribe(
        audio_path,
        language=language,          # None = Whisper auto-detects the language
        word_timestamps=True,       # Get word-level timestamps (used in Phase 2)
        verbose=False,              # Suppress Whisper's internal logging
    )

    # --- Parse segments into a clean list ---
    segments = []
    for seg in result["segments"]:
        segments.append({
            "start": round(seg["start"], 3),
            "end":   round(seg["end"],   3),
            "text":  seg["text"].strip(),
        })

    print(f"[Transcriber] ✅ Transcription complete! Found {len(segments)} segments.")

    # --- Save to JSON file ---
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "segments.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(segments, f, indent=2, ensure_ascii=False)

    print(f"[Transcriber] 💾 Saved to: {output_path}")

    # Return both: clean segments list + raw result (for Phase 2 word timestamps)
    return segments, result
