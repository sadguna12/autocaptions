"""
main.py — Auto Caption Agent Entry Point
-----------------------------------------
Full pipeline: Video → Audio → Transcription → Word Timestamps → Captions

Usage:
    python main.py --video input/your_video.mp4
    python main.py --video input/your_video.mp4 --phase 3 --style reels --model small

Optional flags:
    --phase         1 | 2 | 3           (default: 3)
    --model         tiny | base | small | medium | large  (default: base)
    --lang          en | hi | es | ...  (default: auto-detect)
    --output        output folder path  (default: output/)
    --strategy      auto | native | even (default: auto)
    --style         reels | minimal     (default: reels)
    --font          font name           (default: Arial)
    --font-size     integer             (default: 48)
    --text-color    RGB hex             (default: FFFFFF = white)
    --highlight     RGB hex             (default: 00FFFF = yellow)
    --window        integer words       (default: 4)
    --words-per-chunk integer           (default: 3)
"""

import argparse
import json
import os
import sys

from agent.audio_extractor import extract_audio
from agent.transcriber import transcribe
from agent.word_timer import get_word_timestamps
from agent.caption_generator import generate_srt, generate_ass


def main():
    # ────────────────────────────────────────────────
    # 1. Parse CLI arguments
    # ────────────────────────────────────────────────
    parser = argparse.ArgumentParser(
        description="🎬 Auto Caption Agent — Full Pipeline (Phases 1–3)"
    )

    # Core
    parser.add_argument("--video",    required=True, help="Input video file path")
    parser.add_argument("--output",   default="output", help="Output directory (default: output/)")
    parser.add_argument("--phase",    default=3, type=int, choices=[1, 2, 3],
                        help="Pipeline phase to run (default: 3)")

    # Phase 1 — Whisper
    parser.add_argument("--model",    default="base",
                        choices=["tiny", "base", "small", "medium", "large"],
                        help="Whisper model size (default: base)")
    parser.add_argument("--lang",     default=None,
                        help="Language code (e.g. 'en', 'hi'). Default: auto-detect")

    # Phase 2 — Word timing
    parser.add_argument("--strategy", default="auto", choices=["auto", "native", "even"],
                        help="Word timing strategy (default: auto)")

    # Phase 3 — Caption style
    parser.add_argument("--style",    default="reels", choices=["reels", "minimal"],
                        help="ASS caption style (default: reels)")
    parser.add_argument("--font",     default="Arial",
                        help="Font family for ASS captions (default: Arial)")
    parser.add_argument("--font-size",dest="font_size", default=48, type=int,
                        help="Font size for ASS captions (default: 48)")
    parser.add_argument("--text-color",   dest="text_color",   default="FFFFFF",
                        help="Normal word color as RGB hex (default: FFFFFF = white)")
    parser.add_argument("--highlight",    dest="highlight",     default="00FFFF",
                        help="Highlighted word color as RGB hex (default: 00FFFF = yellow)")
    parser.add_argument("--window",   default=4, type=int,
                        help="Words visible per ASS event (default: 4)")
    parser.add_argument("--words-per-chunk", dest="words_per_chunk", default=3, type=int,
                        help="Words per SRT caption chunk (default: 3)")

    args = parser.parse_args()

    # ────────────────────────────────────────────────
    # Banner
    # ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  🎬 Auto Caption Agent")
    print("=" * 60)
    print(f"  Video     : {args.video}")
    print(f"  Phase     : {args.phase}")
    print(f"  Model     : {args.model}")
    print(f"  Lang      : {args.lang or 'auto-detect'}")
    print(f"  Output    : {args.output}/")
    if args.phase >= 2:
        print(f"  Strategy  : {args.strategy}")
    if args.phase >= 3:
        print(f"  Style     : {args.style}")
        print(f"  Font      : {args.font} {args.font_size}pt")
        print(f"  Colors    : text=#{args.text_color}  highlight=#{args.highlight}")
        print(f"  Window    : {args.window} words  |  SRT chunk: {args.words_per_chunk} words")
    print("=" * 60 + "\n")

    # ────────────────────────────────────────────────
    # STEP 1 — Extract Audio
    # ────────────────────────────────────────────────
    print("📥 STEP 1: Extracting audio...\n")
    try:
        audio_path = extract_audio(args.video, output_dir=args.output)
    except (FileNotFoundError, RuntimeError) as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)

    # ────────────────────────────────────────────────
    # STEP 2 — Transcribe
    # ────────────────────────────────────────────────
    print("\n🎙️  STEP 2: Transcribing with Whisper...\n")
    try:
        segments, whisper_result = transcribe(
            audio_path,
            model_size=args.model,
            language=args.lang,
            output_dir=args.output,
        )
    except (FileNotFoundError, RuntimeError) as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)

    print("\n" + "-" * 60)
    print("  📝 Segments")
    print("-" * 60)
    print(json.dumps(segments, indent=2, ensure_ascii=False))
    print(f"\n  💾 Saved → {args.output}/segments.json")

    if args.phase == 1:
        print("\n✅ Phase 1 complete.\n")
        return

    # ────────────────────────────────────────────────
    # STEP 3 — Word-Level Timestamps
    # ────────────────────────────────────────────────
    print("\n🔤 STEP 3: Generating word-level timestamps...\n")
    try:
        words = get_word_timestamps(
            whisper_result=whisper_result,
            segments=segments,
            output_dir=args.output,
            strategy=args.strategy,
        )
    except (ValueError, RuntimeError) as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)

    print("\n" + "-" * 60)
    print("  🔤 Word Timestamps (preview: first 8)")
    print("-" * 60)
    print(json.dumps(words[:8], indent=2, ensure_ascii=False))
    if len(words) > 8:
        print(f"  ... and {len(words) - 8} more words")
    print(f"\n  💾 Saved → {args.output}/words.json")

    if args.phase == 2:
        print("\n✅ Phase 2 complete.\n")
        return

    # ────────────────────────────────────────────────
    # STEP 4 — Generate Caption Files (Phase 3)
    # ────────────────────────────────────────────────
    print("\n🎨 STEP 4: Generating caption files...\n")

    srt_path = os.path.join(args.output, "captions.srt")
    ass_path = os.path.join(args.output, "captions.ass")

    try:
        generate_srt(
            words=words,
            output_path=srt_path,
            words_per_chunk=args.words_per_chunk,
        )
        generate_ass(
            words=words,
            output_path=ass_path,
            style=args.style,
            font_name=args.font,
            font_size=args.font_size,
            text_color=args.text_color,
            highlight_color=args.highlight,
            window_size=args.window,
        )
    except (ValueError, RuntimeError) as e:
        print(f"\n❌ ERROR: {e}")
        sys.exit(1)

    # ────────────────────────────────────────────────
    # Final Summary
    # ────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  🎉 PHASE 3 COMPLETE — All Caption Files Generated!")
    print("=" * 60)
    print(f"  📄 segments.json  → {args.output}/segments.json")
    print(f"  🔤 words.json     → {args.output}/words.json")
    print(f"  📋 captions.srt   → {srt_path}")
    print(f"  🔥 captions.ass   → {ass_path}")
    print()
    print("  📌 Tips:")
    print("    • Open captions.ass in VLC  → Subtitles → Add Subtitle File")
    print("    • Import captions.srt in Premiere Pro / CapCut / DaVinci")
    print("    • Use --highlight FFFF00 for golden yellow, 00FFFF for cyan")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
