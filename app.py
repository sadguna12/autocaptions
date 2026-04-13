"""
app.py — Auto Caption Agent: Streamlit UI
------------------------------------------
Phase 4: Web interface for the full caption generation pipeline.

Run with:
    streamlit run app.py
"""

import os
import sys
import time
import tempfile
import streamlit as st

# Add project root to path so agent.* imports work
sys.path.insert(0, os.path.dirname(__file__))

from agent.audio_extractor import extract_audio
from agent.transcriber import transcribe
from agent.word_timer import get_word_timestamps
from agent.caption_generator import generate_srt, generate_ass


# ─────────────────────────────────────────────────────────────────────────────
# Page Config & Custom CSS
# ─────────────────────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Auto Caption Agent",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
/* ── Google Font ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

/* ── Global ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── Background ── */
.stApp {
    background: linear-gradient(135deg, #0f0f1a 0%, #1a1030 50%, #0d1a2e 100%);
    min-height: 100vh;
}

/* ── Main container ── */
.main .block-container {
    max-width: 760px;
    padding: 2.5rem 2rem 3rem;
}

/* ── Hero title ── */
.hero-title {
    font-size: 2.8rem;
    font-weight: 700;
    text-align: center;
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.3rem;
    line-height: 1.1;
}
.hero-sub {
    text-align: center;
    color: #9ca3af;
    font-size: 1rem;
    margin-bottom: 2.5rem;
}

/* ── Card ── */
.card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 16px;
    padding: 1.8rem 2rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(12px);
}

/* ── Section label ── */
.section-label {
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #a78bfa;
    margin-bottom: 0.6rem;
}

/* ── Step badge ── */
.step-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(167,139,250,0.15);
    border: 1px solid rgba(167,139,250,0.3);
    border-radius: 99px;
    padding: 0.35rem 0.9rem;
    font-size: 0.85rem;
    color: #c4b5fd;
    margin-bottom: 0.5rem;
}

/* ── Status row ── */
.status-row {
    display: flex;
    align-items: center;
    gap: 0.7rem;
    padding: 0.55rem 0;
    border-bottom: 1px solid rgba(255,255,255,0.06);
    font-size: 0.9rem;
    color: #e5e7eb;
}
.status-row:last-child { border-bottom: none; }
.status-done   { color: #34d399; }
.status-active { color: #fbbf24; animation: pulse 1.2s infinite; }
.status-wait   { color: #4b5563; }
@keyframes pulse { 0%,100%{opacity:1} 50%{opacity:.4} }

/* ── Success banner ── */
.success-banner {
    background: linear-gradient(90deg, rgba(52,211,153,0.15), rgba(96,165,250,0.15));
    border: 1px solid rgba(52,211,153,0.35);
    border-radius: 12px;
    padding: 1.2rem 1.5rem;
    text-align: center;
    color: #6ee7b7;
    font-size: 1.05rem;
    font-weight: 600;
    margin-bottom: 1.2rem;
}

/* ── Download cards ── */
.dl-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.dl-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 12px;
    padding: 1.1rem 1.2rem;
    text-align: center;
}
.dl-icon  { font-size: 2rem; margin-bottom: 0.4rem; }
.dl-label { font-size: 0.8rem; color: #9ca3af; margin-bottom: 0.6rem; }
.dl-desc  { font-size: 0.72rem; color: #6b7280; }

/* ── Streamlit file uploader ── */
[data-testid="stFileUploader"] {
    border: 2px dashed rgba(167,139,250,0.4) !important;
    border-radius: 12px !important;
    background: rgba(167,139,250,0.05) !important;
    padding: 0.5rem !important;
    transition: border-color 0.2s;
}
[data-testid="stFileUploader"]:hover {
    border-color: rgba(167,139,250,0.7) !important;
}

/* ── Generate button ── */
div[data-testid="stButton"] > button {
    width: 100%;
    background: linear-gradient(90deg, #7c3aed, #4f46e5) !important;
    color: white !important;
    font-weight: 600 !important;
    font-size: 1.05rem !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.75rem 1.5rem !important;
    cursor: pointer !important;
    transition: opacity 0.2s, transform 0.15s !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 4px 24px rgba(124,58,237,0.35) !important;
}
div[data-testid="stButton"] > button:hover {
    opacity: 0.88 !important;
    transform: translateY(-1px) !important;
}

/* ── Expander / settings ── */
details summary {
    color: #9ca3af !important;
    font-size: 0.85rem !important;
    cursor: pointer !important;
}

/* ── Select / slider ── */
.stSelectbox label, .stSlider label { color: #d1d5db !important; font-size: 0.85rem !important; }
.stColorPicker label { color: #d1d5db !important; font-size: 0.85rem !important; }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def hex_to_rgb_str(hex_color: str) -> str:
    """Streamlit color picker returns '#RRGGBB' — strip the # for our functions."""
    return hex_color.lstrip("#").upper()


def run_pipeline(video_path: str, output_dir: str, settings: dict, status_slots: dict) -> dict:
    """
    Run the full 4-step caption pipeline and return paths to output files.

    Args:
        video_path   : Path to the saved uploaded video
        output_dir   : Where to save all output files
        settings     : Dict of UI settings (model, style, colors, etc.)
        status_slots : Dict of st.empty() placeholders for live step updates

    Returns:
        Dict with keys: 'srt_path', 'ass_path', 'word_count', 'segment_count'
    """

    def _mark(slot_key: str, icon: str, text: str, cls: str = "status-done"):
        status_slots[slot_key].markdown(
            f'<div class="status-row {cls}">{icon} {text}</div>',
            unsafe_allow_html=True
        )

    # Step 1 — Extract Audio
    _mark("audio", "⏳", "Extracting audio from video...", "status-active")
    audio_path = extract_audio(video_path, output_dir=output_dir)
    _mark("audio", "✅", "Audio extracted")

    # Step 2 — Transcribe
    _mark("transcribe", "⏳", "Transcribing speech with Whisper...", "status-active")
    segments, whisper_result = transcribe(
        audio_path,
        model_size=settings["model"],
        language=settings["lang"] or None,
        output_dir=output_dir,
    )
    _mark("transcribe", "✅", f"Transcription done — {len(segments)} segments")

    # Step 3 — Word timestamps
    _mark("words", "⏳", "Building word-level timestamps...", "status-active")
    words = get_word_timestamps(
        whisper_result=whisper_result,
        segments=segments,
        output_dir=output_dir,
        strategy="auto",
    )
    _mark("words", "✅", f"Word timestamps ready — {len(words)} words")

    # Step 4 — Caption files
    _mark("captions", "⏳", "Generating caption files...", "status-active")
    srt_path = os.path.join(output_dir, "captions.srt")
    ass_path = os.path.join(output_dir, "captions.ass")

    generate_srt(
        words=words,
        output_path=srt_path,
        words_per_chunk=settings["words_per_chunk"],
    )
    generate_ass(
        words=words,
        output_path=ass_path,
        style=settings["style"],
        font_name=settings["font"],
        font_size=settings["font_size"],
        text_color=settings["text_color"],
        highlight_color=settings["highlight_color"],
        window_size=settings["window"],
    )
    _mark("captions", "✅", "Caption files generated")

    return {
        "srt_path":      srt_path,
        "ass_path":      ass_path,
        "word_count":    len(words),
        "segment_count": len(segments),
    }


# ─────────────────────────────────────────────────────────────────────────────
# UI Layout
# ─────────────────────────────────────────────────────────────────────────────

# ── Hero ──
st.markdown('<div class="hero-title">🎬 Auto Caption Agent</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="hero-sub">Upload a video · Get word-by-word captions · Download .srt & .ass</div>',
    unsafe_allow_html=True
)

# ── Upload card ──
st.markdown('<div class="card">', unsafe_allow_html=True)
st.markdown('<div class="section-label">📁 Upload Video</div>', unsafe_allow_html=True)
uploaded_file = st.file_uploader(
    label="",
    type=["mp4", "mov", "mkv", "webm", "avi"],
    help="Supported formats: MP4, MOV, MKV, WEBM, AVI",
    label_visibility="collapsed",
)
st.markdown('</div>', unsafe_allow_html=True)

# ── Settings (collapsible) ──
with st.expander("⚙️  Settings  (optional)", expanded=False):
    col1, col2 = st.columns(2)
    with col1:
        model_choice = st.selectbox(
            "Whisper Model",
            ["tiny", "base", "small", "medium", "large"],
            index=1,
            help="Larger = more accurate but slower",
        )
        style_choice = st.selectbox(
            "Caption Style",
            ["reels", "minimal"],
            help="reels = center bold  |  minimal = lower smaller",
        )
        lang_input = st.text_input(
            "Language (optional)",
            placeholder="en / hi / es — leave blank to auto-detect",
            help="ISO 639-1 language code. Leave empty for auto-detection.",
        )
    with col2:
        font_size  = st.slider("Font Size (pt)", 28, 96, 48, step=4)
        window     = st.slider("Word Window", 2, 7, 4,
                               help="Words visible per ASS caption event")
        words_per_chunk = st.slider("SRT Chunk Size", 1, 6, 3,
                                    help="Max words per SRT line")

    col3, col4 = st.columns(2)
    with col3:
        text_color_raw = st.color_picker("Text Color", "#FFFFFF")
    with col4:
        highlight_raw  = st.color_picker("Highlight Color", "#FFFF00")

    font_choice = st.selectbox(
        "Font",
        ["Arial", "Helvetica", "Montserrat", "Impact", "Roboto"],
        help="Font must be installed on the system playing the .ass file",
    )

# Collect settings dict
settings = {
    "model":         model_choice,
    "style":         style_choice,
    "lang":          lang_input.strip(),
    "font":          font_choice,
    "font_size":     font_size,
    "text_color":    hex_to_rgb_str(text_color_raw),
    "highlight_color": hex_to_rgb_str(highlight_raw),
    "window":        window,
    "words_per_chunk": words_per_chunk,
}

# ── Generate button ──
st.markdown("")   # spacer
generate_btn = st.button("🚀 Generate Captions", disabled=(uploaded_file is None))

# ─────────────────────────────────────────────────────────────────────────────
# Pipeline Execution
# ─────────────────────────────────────────────────────────────────────────────

if generate_btn and uploaded_file is not None:

    # Save uploaded video to input/
    input_dir  = os.path.join(os.path.dirname(__file__), "input")
    output_dir = os.path.join(os.path.dirname(__file__), "output")
    os.makedirs(input_dir,  exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    video_path = os.path.join(input_dir, uploaded_file.name)
    with open(video_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    # ── Progress card ──
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-label">⚡ Processing</div>', unsafe_allow_html=True)

    # Pre-render all 4 status rows as "waiting"
    slot_audio     = st.empty()
    slot_transcribe = st.empty()
    slot_words     = st.empty()
    slot_captions  = st.empty()

    for slot, text in [
        (slot_audio,      "Extract audio"),
        (slot_transcribe, "Transcribe speech"),
        (slot_words,      "Build word timestamps"),
        (slot_captions,   "Generate caption files"),
    ]:
        slot.markdown(
            f'<div class="status-row status-wait">○ {text}</div>',
            unsafe_allow_html=True,
        )

    status_slots = {
        "audio":      slot_audio,
        "transcribe": slot_transcribe,
        "words":      slot_words,
        "captions":   slot_captions,
    }

    st.markdown('</div>', unsafe_allow_html=True)

    # ── Run pipeline ──
    try:
        with st.spinner(""):
            result = run_pipeline(video_path, output_dir, settings, status_slots)

        # ── Success banner ──
        st.markdown(
            f'<div class="success-banner">'
            f'🎉 Done!  &nbsp;|&nbsp;  {result["segment_count"]} segments  &nbsp;·&nbsp;  {result["word_count"]} words'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Download buttons ──
        st.markdown('<div class="section-label">📥 Download Captions</div>', unsafe_allow_html=True)
        col_srt, col_ass = st.columns(2)

        with open(result["srt_path"], "rb") as srt_file:
            srt_bytes = srt_file.read()
        with open(result["ass_path"], "rb") as ass_file:
            ass_bytes = ass_file.read()

        with col_srt:
            st.markdown(
                '<div class="dl-card">'
                '<div class="dl-icon">📋</div>'
                '<div class="dl-label">Standard Subtitles</div>'
                '<div class="dl-desc">VLC · Premiere · CapCut · YouTube</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            st.download_button(
                label="⬇️  Download .srt",
                data=srt_bytes,
                file_name="captions.srt",
                mime="text/plain",
                use_container_width=True,
            )

        with col_ass:
            st.markdown(
                '<div class="dl-card">'
                '<div class="dl-icon">🔥</div>'
                '<div class="dl-label">Styled Reels Captions</div>'
                '<div class="dl-desc">VLC · DaVinci Resolve · After Effects</div>'
                '</div>',
                unsafe_allow_html=True,
            )
            st.download_button(
                label="⬇️  Download .ass",
                data=ass_bytes,
                file_name="captions.ass",
                mime="text/plain",
                use_container_width=True,
            )

        # ── Word preview ──
        words_json_path = os.path.join(output_dir, "words.json")
        if os.path.exists(words_json_path):
            with st.expander("🔤 Word Timestamps Preview (first 10)", expanded=False):
                import json
                with open(words_json_path, encoding="utf-8") as wf:
                    all_words = json.load(wf)
                preview_md = "\n".join(
                    f"| `{w['word']}` | {w['start']:.3f}s | {w['end']:.3f}s |"
                    for w in all_words[:10]
                )
                st.markdown(
                    "| Word | Start | End |\n|---|---|---|\n" + preview_md,
                    unsafe_allow_html=True,
                )

    except Exception as e:
        st.error(f"❌ Pipeline failed: {e}")
        st.info("💡 Make sure **ffmpeg** is installed and in your system PATH.")

# ── Footer ──
st.markdown("---")
st.markdown(
    '<p style="text-align:center;color:#4b5563;font-size:0.78rem;">'
    'Auto Caption Agent · Built with Whisper + ffmpeg · '
    '<a href="https://github.com" style="color:#6b7280;">GitHub</a>'
    '</p>',
    unsafe_allow_html=True,
)
