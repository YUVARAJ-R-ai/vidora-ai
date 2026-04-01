"""
Audio Analysis Service.

1. FFmpeg extracts audio track as 16kHz mono WAV
2. Whisper tiny transcribes speech with timestamps
3. librosa computes RMS amplitude for shouting detection
"""
import os
import subprocess
from typing import List, Dict, Any, Optional

# Lazy-load heavy modules
_whisper_model = None
_librosa = None


def _get_whisper():
    global _whisper_model
    if _whisper_model is None:
        import whisper
        _whisper_model = whisper.load_model("tiny")
    return _whisper_model


def _get_librosa():
    global _librosa
    if _librosa is None:
        import librosa as lib
        _librosa = lib
    return _librosa


def extract_audio(video_path: str, output_dir: str) -> Optional[str]:
    """
    Extract audio from video as 16kHz mono WAV using FFmpeg.

    Returns:
        Path to the extracted WAV file, or None if no audio track.
    """
    audio_path = os.path.join(output_dir, "audio.wav")

    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn",                # no video
        "-acodec", "pcm_s16le",  # 16-bit PCM
        "-ar", "16000",       # 16kHz sample rate (Whisper expects this)
        "-ac", "1",           # mono
        audio_path,
        "-y",                 # overwrite
    ]

    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    if result.returncode != 0 or not os.path.exists(audio_path):
        # Video might have no audio track — that's fine
        return None

    # Check if file is too small (no actual audio)
    if os.path.getsize(audio_path) < 1000:
        os.remove(audio_path)
        return None

    return audio_path


def transcribe_audio(audio_path: str) -> List[Dict[str, Any]]:
    """
    Transcribe audio using Whisper tiny model.

    Returns:
        List of segments: [{"start": 0.0, "end": 2.5, "text": "Hello"}, ...]
    """
    try:
        model = _get_whisper()
        result = model.transcribe(audio_path, language=None, fp16=False)

        segments = []
        for seg in result.get("segments", []):
            text = seg.get("text", "").strip()
            if text:
                segments.append({
                    "start": round(seg["start"], 2),
                    "end": round(seg["end"], 2),
                    "text": text,
                })

        return segments

    except Exception as e:
        print(f"Whisper transcription error: {e}")
        return []


def analyze_amplitude(audio_path: str, segments: List[Dict]) -> List[Dict[str, Any]]:
    """
    Analyze audio amplitude per segment to detect shouting/loudness.

    Adds 'is_loud' and 'amplitude_db' to each segment.
    Loud = segment RMS is > 1.5x the overall mean RMS.
    """
    try:
        librosa = _get_librosa()
        import numpy as np

        y, sr = librosa.load(audio_path, sr=16000, mono=True)
        duration = len(y) / sr

        # Compute overall mean RMS
        overall_rms = np.sqrt(np.mean(y ** 2))
        if overall_rms < 1e-8:
            # Silence — mark nothing as loud
            for seg in segments:
                seg["is_loud"] = False
                seg["amplitude_db"] = -60.0
            return segments

        overall_db = 20 * np.log10(overall_rms + 1e-10)
        loud_threshold = overall_rms * 1.5

        enriched = []
        for seg in segments:
            start_sample = int(seg["start"] * sr)
            end_sample = min(int(seg["end"] * sr), len(y))

            if end_sample <= start_sample:
                seg["is_loud"] = False
                seg["amplitude_db"] = overall_db
                enriched.append(seg)
                continue

            segment_audio = y[start_sample:end_sample]
            seg_rms = np.sqrt(np.mean(segment_audio ** 2))
            seg_db = round(float(20 * np.log10(seg_rms + 1e-10)), 1)

            seg["is_loud"] = bool(seg_rms > loud_threshold)
            seg["amplitude_db"] = seg_db
            enriched.append(seg)

        return enriched

    except Exception as e:
        print(f"Amplitude analysis error: {e}")
        # Return segments without amplitude data
        for seg in segments:
            seg["is_loud"] = False
            seg["amplitude_db"] = 0.0
        return segments


def analyze_audio(video_path: str, output_dir: str) -> List[Dict[str, Any]]:
    """
    Full audio analysis pipeline:
    1. Extract audio from video
    2. Transcribe with Whisper
    3. Analyze amplitude for shouting detection

    Returns:
        List of enriched segments with text, timestamps, loudness.
        Returns empty list if video has no audio.
    """
    audio_path = extract_audio(video_path, output_dir)
    if audio_path is None:
        return []

    segments = transcribe_audio(audio_path)
    if not segments:
        return []

    segments = analyze_amplitude(audio_path, segments)

    # Clean up WAV file
    try:
        os.remove(audio_path)
    except OSError:
        pass

    return segments
