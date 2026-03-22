import os
import json
import base64
import urllib.request
import urllib.error
import wave
import io
import subprocess
import streamlit as st

# --- CONFIGURATION ---
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IDENTITY_FILE = os.path.join(BASE_DIR, "Your_Identity.txt")

# Correct TTS model — gemini-2.0-flash does NOT support audio output
TTS_MODEL = "gemini-2.5-flash-preview-tts"
TTS_URL = (
    "https://generativelanguage.googleapis.com/v1beta/"
    f"models/{TTS_MODEL}:generateContent"
)

# PCM output from Gemini TTS: 16-bit signed, mono, 24000 Hz
SAMPLE_RATE = 24000
CHANNELS = 1
SAMPLE_WIDTH = 2  # bytes (16-bit)


def _read_identity():
    try:
        with open(IDENTITY_FILE, "r") as f:
            return f.read().strip()
    except Exception:
        return "You are a ghost haunting an old telephone exchange."


def _pcm_to_wav(pcm_bytes):
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(SAMPLE_WIDTH)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_bytes)
    return buf.getvalue()


def _apply_telephone_effect(wav_bytes):
    cmd = [
        "ffmpeg", "-y",
        "-f", "wav", "-i", "pipe:0",
        "-af", "highpass=f=300,lowpass=f=3400,aecho=0.8:0.88:60:0.4,volume=2.0",
        "-f", "wav", "pipe:1"
    ]
    try:
        result = subprocess.run(cmd, input=wav_bytes, capture_output=True, timeout=30)
        if result.returncode == 0 and len(result.stdout) > 44:
            print("[OK] FFmpeg telephone effect applied")
            return result.stdout
        else:
            print(f"[FFMPEG ERROR] rc={result.returncode} stderr={result.stderr[:300]}")
            return wav_bytes
    except Exception as e:
        print(f"[FFMPEG ERROR] {e}")
        return wav_bytes


def generate_whisper():
    if not GEMINI_API_KEY:
        print("[ERROR] No GEMINI_API_KEY in Streamlit Secrets.")
        return None

    identity = _read_identity()

    prompt = (
        "Say the following in a slow, haunting, barely audible whisper, "
        "like a ghost speaking through an old telephone:\n\n"
        f"{identity}"
    )

    payload = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseModalities": ["AUDIO"],
            "speechConfig": {
                "voiceConfig": {
                    "prebuiltVoiceConfig": {"voiceName": "Charon"}
                }
            }
        }
    }).encode("utf-8")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={GEMINI_API_KEY}"

    try:
        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = json.loads(resp.read())

        audio_b64 = body["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
        pcm_bytes = base64.b64decode(audio_b64)
        print(f"[OK] TTS audio received: {len(pcm_bytes)} PCM bytes")

        wav_bytes = _pcm_to_wav(pcm_bytes)
        print(f"[OK] WAV created: {len(wav_bytes)} bytes")

        return _apply_telephone_effect(wav_bytes)

    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        print(f"[ERROR] HTTP {e.code}: {e.reason} — {body[:500]}")
        return None
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        return None
