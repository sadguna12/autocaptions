"""
word_timer.py
-------------
Phase 2: Convert segment-level transcription into word-level timestamps.

Two strategies are supported:

1. WHISPER NATIVE  (preferred)
   Whisper already returns per-word timestamps when word_timestamps=True.
   We extract them directly from the raw Whisper result — perfect accuracy.

2. EVEN DISTRIBUTION  (fallback)
   If native word data isn't available, we split each segment's duration
   evenly across its words. Less accurate but still useful.

Why both?
- The native mode is always better, but sometimes you may load a
  pre-existing segments.json that doesn't have word data.
  The fallback keeps the pipeline flexible.
"""

import json
import os
from typing import Optional


# ──────────────────────────────────────────────────────────────
# Strategy 1: Extract word timestamps directly from Whisper output
# ──────────────────────────────────────────────────────────────

def extract_words_from_whisper(whisper_result: dict) -> list[dict]:
    """
    Pull per-word timestamps directly from a raw Whisper result object.

    Whisper returns a 'segments' list. Each segment has a 'words' list:
        [
            { "word": "Hello", "start": 0.0, "end": 0.42, "probability": 0.99 },
            ...
        ]

    Args:
        whisper_result : The raw dict returned by model.transcribe(...)

    Returns:
        List of word dicts: [{ "word", "start", "end" }, ...]
    """
    words = []

    for segment in whisper_result.get("segments", []):
        for w in segment.get("words", []):
            # Clean up the word text (Whisper sometimes adds leading spaces)
            word_text = w["word"].strip()
            if not word_text:
                continue

            words.append({
                "word":  word_text,
                "start": round(w["start"], 3),
                "end":   round(w["end"],   3),
            })

    return words


# ──────────────────────────────────────────────────────────────
# Strategy 2: Even distribution fallback
# ──────────────────────────────────────────────────────────────

def distribute_words_evenly(segments: list[dict]) -> list[dict]:
    """
    Distribute word timestamps evenly within each segment.

    For a segment: { "start": 0.0, "end": 3.0, "text": "Hello bro welcome" }
    Duration = 3.0s, 3 words → each word gets 1.0s

    Result:
        { "word": "Hello",   "start": 0.0, "end": 1.0 }
        { "word": "bro",     "start": 1.0, "end": 2.0 }
        { "word": "welcome", "start": 2.0, "end": 3.0 }

    Args:
        segments : List of segment dicts with "start", "end", "text" keys

    Returns:
        List of word dicts: [{ "word", "start", "end" }, ...]
    """
    words = []

    for seg in segments:
        start = seg["start"]
        end   = seg["end"]
        text  = seg["text"].strip()

        # Split the segment text into individual words
        seg_words = text.split()
        if not seg_words:
            continue

        # Calculate how much time each word gets
        duration     = end - start
        word_duration = duration / len(seg_words)

        for i, word in enumerate(seg_words):
            word_start = round(start + i * word_duration, 3)
            word_end   = round(start + (i + 1) * word_duration, 3)

            words.append({
                "word":  word,
                "start": word_start,
                "end":   word_end,
            })

    return words


# ──────────────────────────────────────────────────────────────
# Main function: auto-pick the best strategy
# ──────────────────────────────────────────────────────────────

def get_word_timestamps(
    whisper_result: Optional[dict] = None,
    segments: Optional[list] = None,
    output_dir: str = "output",
    strategy: str = "auto",
) -> list:
    """
    Get word-level timestamps using the best available strategy.

    Priority:
        "auto"   → use Whisper native if available, else fallback to even
        "native" → force Whisper native word data
        "even"   → force even distribution

    Args:
        whisper_result : Raw Whisper transcription result (for native mode)
        segments       : List of segment dicts (for even-distribution mode)
        output_dir     : Folder to save words.json
        strategy       : "auto" | "native" | "even"

    Returns:
        List of word dicts: [{ "word", "start", "end" }, ...]
    """

    words = []

    if strategy in ("auto", "native") and whisper_result is not None:
        # Check if Whisper actually returned word-level data
        has_word_data = any(
            seg.get("words") for seg in whisper_result.get("segments", [])
        )

        if has_word_data:
            print("[WordTimer] ✨ Using Whisper native word timestamps (most accurate)")
            words = extract_words_from_whisper(whisper_result)
        elif strategy == "native":
            raise ValueError(
                "Strategy is 'native' but Whisper result has no word-level data. "
                "Make sure word_timestamps=True was passed to model.transcribe()."
            )
        else:
            print("[WordTimer] ⚠️  No native word data — falling back to even distribution")
            words = distribute_words_evenly(segments or [])

    elif strategy == "even" or (strategy == "auto" and segments is not None):
        print("[WordTimer] 📐 Using even distribution across segments")
        words = distribute_words_evenly(segments or [])

    else:
        raise ValueError(
            "Provide either 'whisper_result' (for native mode) "
            "or 'segments' (for even-distribution mode)."
        )

    print(f"[WordTimer] ✅ Generated {len(words)} word timestamps")

    # Save to JSON
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "words.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(words, f, indent=2, ensure_ascii=False)

    print(f"[WordTimer] 💾 Saved to: {output_path}")

    return words
