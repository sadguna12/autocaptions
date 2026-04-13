"""
caption_generator.py
---------------------
Phase 3: Convert word-level timestamps into subtitle files.

Generates:
  1. .srt  — Standard subtitle format (works in VLC, Premiere, YouTube)
  2. .ass  — Advanced SubStation Alpha (styled captions with word highlighting)

The .ass file produces "reels-style" captions:
  - Bold white text centered on screen
  - Current highlighted word shown in yellow (or custom color)
  - 3-5 word context window around the highlighted word

ASS Color format: &HAABBGGRR (Alpha, Blue, Green, Red — reversed!)
  White   = &H00FFFFFF
  Yellow  = &H0000FFFF
  Cyan    = &H00FFFF00
  Custom colors are passed as hex strings like "FFFF00"
"""

import os
from typing import Literal


# ──────────────────────────────────────────────────────────────
# Shared Utility: Time Formatters
# ──────────────────────────────────────────────────────────────

def _seconds_to_srt_time(seconds: float) -> str:
    """
    Convert float seconds to SRT timestamp format: HH:MM:SS,mmm

    Example: 65.432 → "00:01:05,432"
    """
    milliseconds = int(round(seconds * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, ms = divmod(remainder, 1_000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def _seconds_to_ass_time(seconds: float) -> str:
    """
    Convert float seconds to ASS timestamp format: H:MM:SS.cc (centiseconds)

    Example: 65.432 → "0:01:05.43"
    """
    centiseconds = int(round(seconds * 100))
    hours, remainder = divmod(centiseconds, 360_000)
    minutes, remainder = divmod(remainder, 6_000)
    secs, cs = divmod(remainder, 100)
    return f"{hours}:{minutes:02d}:{secs:02d}.{cs:02d}"


# ──────────────────────────────────────────────────────────────
# PART 1: SRT Generation
# ──────────────────────────────────────────────────────────────

def generate_srt(
    words: list,
    output_path: str,
    words_per_chunk: int = 3,
    max_chunk_duration: float = 1.5,
) -> str:
    """
    Group words into small caption chunks and write a .srt subtitle file.

    Chunking rules (whichever comes first):
      - Max N words per chunk (default: 3)
      - Max duration per chunk (default: 1.5 seconds)

    Args:
        words             : List of { "word", "start", "end" } dicts
        output_path       : Where to save the .srt file
        words_per_chunk   : Max words per subtitle line (default: 3)
        max_chunk_duration: Max seconds per subtitle line (default: 1.5)

    Returns:
        Path to the generated .srt file
    """
    if not words:
        raise ValueError("Word list is empty — cannot generate SRT.")

    chunks = _chunk_words(words, words_per_chunk, max_chunk_duration)

    lines = []
    for i, chunk in enumerate(chunks, start=1):
        start_time = _seconds_to_srt_time(chunk[0]["start"])
        end_time   = _seconds_to_srt_time(chunk[-1]["end"])
        text       = " ".join(w["word"] for w in chunk)

        lines.append(str(i))
        lines.append(f"{start_time} --> {end_time}")
        lines.append(text)
        lines.append("")  # blank line between entries

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"[CaptionGen] ✅ SRT saved → {output_path}  ({len(chunks)} captions)")
    return output_path


# ──────────────────────────────────────────────────────────────
# PART 2: ASS Generation (Reels-style)
# ──────────────────────────────────────────────────────────────

def generate_ass(
    words: list,
    output_path: str,
    style: Literal["reels", "minimal"] = "reels",
    font_name: str = "Arial",
    font_size: int = 48,
    text_color: str = "FFFFFF",        # White  (RGB hex, no #)
    highlight_color: str = "00FFFF",   # Yellow (RGB hex, no #)
    window_size: int = 4,              # Words visible at once
) -> str:
    """
    Generate a styled .ass subtitle file with per-word highlighting.

    Each word gets its own timed event. The surrounding context window
    (window_size words) is shown, with the current word highlighted.

    Example output line (reels style):
      Hello {\\c&H0000FFFF&}bro{\\r} welcome here

    Args:
        words           : List of { "word", "start", "end" } dicts
        output_path     : Where to save the .ass file
        style           : "reels" (big, bold, centered) | "minimal" (small, lower)
        font_name       : Font family name (default: Arial)
        font_size       : Font size in points (default: 48)
        text_color      : Normal word color as RGB hex string (default: FFFFFF = white)
        highlight_color : Current word color as RGB hex string (default: 00FFFF = yellow)
        window_size     : Number of words visible per event (default: 4)

    Returns:
        Path to the generated .ass file
    """
    if not words:
        raise ValueError("Word list is empty — cannot generate ASS.")

    # Convert RGB hex → ASS &HAABBGGRR format
    ass_text_color      = _rgb_hex_to_ass(text_color)
    ass_highlight_color = _rgb_hex_to_ass(highlight_color)

    # Build ASS header + styles
    header  = _build_ass_header()
    styles  = _build_ass_styles(style, font_name, font_size, ass_text_color)
    events  = _build_ass_events(words, ass_text_color, ass_highlight_color, window_size)

    content = header + styles + events

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8-sig") as f:   # utf-8-sig for BOM (compatibility)
        f.write(content)

    print(f"[CaptionGen] 🔥 ASS saved → {output_path}  ({len(words)} word events)")
    return output_path


# ──────────────────────────────────────────────────────────────
# Internal helpers
# ──────────────────────────────────────────────────────────────

def _chunk_words(
    words: list,
    words_per_chunk: int,
    max_chunk_duration: float,
) -> list[list[dict]]:
    """Group a flat word list into caption chunks."""
    chunks = []
    current_chunk = []

    for word in words:
        current_chunk.append(word)

        chunk_duration = current_chunk[-1]["end"] - current_chunk[0]["start"]
        if len(current_chunk) >= words_per_chunk or chunk_duration >= max_chunk_duration:
            chunks.append(current_chunk)
            current_chunk = []

    if current_chunk:
        chunks.append(current_chunk)

    return chunks


def _rgb_hex_to_ass(rgb_hex: str) -> str:
    """
    Convert a 6-char RGB hex string to ASS color format &HAABBGGRR.

    ASS uses BGR byte order with an alpha prefix (00 = fully opaque).
    Example: "FFFF00" (yellow in RGB) → "&H0000FFFF" (yellow in ASS/BGR)
    """
    rgb_hex = rgb_hex.lstrip("#").upper()
    r = rgb_hex[0:2]
    g = rgb_hex[2:4]
    b = rgb_hex[4:6]
    return f"&H00{b}{g}{r}"   # ASS: Alpha=00, then BGR


def _build_ass_header() -> str:
    return (
        "[Script Info]\n"
        "Title: Auto Caption Agent — Reels Captions\n"
        "ScriptType: v4.00+\n"
        "WrapStyle: 0\n"
        "ScaledBorderAndShadow: yes\n"
        "PlayResX: 1080\n"
        "PlayResY: 1920\n"   # Vertical (Reels/Shorts aspect ratio)
        "YCbCr Matrix: TV.601\n"
        "\n"
    )


def _build_ass_styles(
    style: str,
    font_name: str,
    font_size: int,
    ass_text_color: str,
) -> str:
    """
    Build the [V4+ Styles] section.

    Style fields: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour,
                  OutlineColour, BackColour, Bold, Italic, Underline,
                  StrikeOut, ScaleX, ScaleY, Spacing, Angle,
                  BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR,
                  MarginV, Encoding
    """
    # Alignment: 2 = bottom-center, 5 = middle-center (reels puts text in middle)
    alignment = 5 if style == "reels" else 2

    # Outline & Shadow for readability over video
    outline = 3 if style == "reels" else 1
    shadow  = 2 if style == "reels" else 0

    bold = -1  # -1 = bold in ASS format

    style_line = (
        f"Style: Default,{font_name},{font_size},"
        f"{ass_text_color},&H000000FF,&H00000000,&H80000000,"   # Primary, Secondary, Outline, Back
        f"{bold},0,0,0,"           # Bold, Italic, Underline, StrikeOut
        f"100,100,0,0,"            # ScaleX, ScaleY, Spacing, Angle
        f"1,{outline},{shadow},"   # BorderStyle, Outline, Shadow
        f"{alignment},60,60,120,1" # Alignment, MarginL, MarginR, MarginV, Encoding
    )

    return (
        "[V4+ Styles]\n"
        "Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, "
        "OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, "
        "ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, "
        "Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"{style_line}\n"
        "\n"
    )


def _build_ass_events(
    words: list,
    ass_text_color: str,
    ass_highlight_color: str,
    window_size: int,
) -> str:
    """
    Build the [Events] section.

    For each word, generate one Dialogue line showing a window of surrounding
    words with the current word highlighted in a different color.

    ASS inline override tags used:
      {\\c&HXXXXXXXX&}  → change fill color
      {\\r}             → reset to default style
    """
    lines = [
        "[Events]\n",
        "Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n",
    ]

    half_window = window_size // 2

    for i, current_word in enumerate(words):
        # Determine the window: words visible alongside the current one
        win_start = max(0, i - half_window)
        win_end   = min(len(words), i + half_window + 1)
        window    = words[win_start:win_end]

        # Build the caption text — highlight the current word
        parts = []
        for w in window:
            if w is current_word:
                # Highlighted: switch to highlight color, then reset
                parts.append(
                    f"{{\\c{ass_highlight_color}}}{{\\b1}}{w['word']}{{\\r}}"
                )
            else:
                parts.append(w["word"])

        text = " ".join(parts)

        start_ts = _seconds_to_ass_time(current_word["start"])
        end_ts   = _seconds_to_ass_time(current_word["end"])

        # Dialogue line format (Layer, Start, End, Style, ..., Text)
        lines.append(
            f"Dialogue: 0,{start_ts},{end_ts},Default,,0,0,0,,{text}\n"
        )

    return "".join(lines)
