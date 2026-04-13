"""
audio_extractor.py
------------------
Extracts audio from a video file using ffmpeg.

Why ffmpeg?
- Industry-standard media processing tool
- Handles virtually any video format (mp4, mov, avi, webm, etc.)
- We output 16kHz mono WAV — the format Whisper is optimized for
"""

import ffmpeg
import os


def extract_audio(video_path: str, output_dir: str = "output") -> str:
    """
    Extract audio from a video file and save it as a WAV file.

    Args:
        video_path  : Path to the input video (e.g., "input/my_video.mp4")
        output_dir  : Directory where the .wav file will be saved

    Returns:
        Path to the extracted audio file (e.g., "output/audio.wav")

    Raises:
        FileNotFoundError : If the video file doesn't exist
        RuntimeError      : If ffmpeg fails to extract audio
    """

    # --- Validate input ---
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    # --- Prepare output path ---
    os.makedirs(output_dir, exist_ok=True)
    audio_filename = os.path.splitext(os.path.basename(video_path))[0] + "_audio.wav"
    audio_path = os.path.join(output_dir, audio_filename)

    print(f"[AudioExtractor] Extracting audio from: {video_path}")
    print(f"[AudioExtractor] Output audio file   : {audio_path}")

    try:
        (
            ffmpeg
            .input(video_path)                   # Load the video file
            .output(
                audio_path,
                ac=1,                            # Mono channel (Whisper works best with mono)
                ar=16000,                        # 16kHz sample rate (Whisper's native rate)
                format="wav",                    # WAV format
                loglevel="error",                # Suppress ffmpeg's verbose output
            )
            .overwrite_output()                  # Overwrite if file already exists
            .run()
        )
    except ffmpeg.Error as e:
        raise RuntimeError(
            f"ffmpeg failed to extract audio.\n"
            f"Stderr: {e.stderr.decode() if e.stderr else 'No error details'}"
        ) from e

    print(f"[AudioExtractor] ✅ Audio extracted successfully!")
    return audio_path
