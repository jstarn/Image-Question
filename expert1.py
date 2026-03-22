import os
import json
import base64
import urllib.request
import wave
import io
import subprocess
import streamlit as st

# --- CONFIGURATION ---
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IDENTITY_FILE = os.path.join(BASE_DIR, "Your_Identity.txt")


def generate_whisper():
    """
    Generates a whisper and returns processed audio as bytes (WAV).
    Returns None on any failure — check Streamlit logs for [ERROR] lines.
    """
    if not GEMINI_API_KEY:
        print("[ERROR] No GEMINI_API_KEY in Streamlit Secrets.")
        return None

    try:
        # --- Step 1: Generate whisper text ---
        text_url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/gemini-1.5-pro:generateContent?key={GEMINI_API_KEY}"
        )
        with open(IDENTITY_FILE, "r") as f:
            identity = f.read()

        prompt = f"IDENTITY: {identity}\nTASK: speak as a spirit inside a phone."
        req_text = urllib.request.Request(
            text_url,
            data=json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_text) as resp:
            whisper_text = (
                json.loads(resp.read().decode("utf-8"))
                ["candidates"][0]["content"]["parts"][0]["text"]
            )
        print(f"[OK] Whisper text generated ({len(whisper_text)} chars)")

        # --- Step 2: Generate audio ---
        audio_url = (
            "https://generativelanguage.googleapis.com/v1beta/"
            f"models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        )
        audio_payload = {
            "contents": [{"parts": [{"text": f"<speak>{whisper_text}</speak>"}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Puck"}}
                },
            },
        }
        req_audio = urllib.request.Request(
            audio_url,
            data=json.dumps(audio_payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req_audio) as resp:
            raw_pcm = base64.b64decode(
                json.loads(resp.read().decode("utf-8"))
                ["candidates"][0]["content"]["parts"][0]["inlineData"]["data"]
            )
        print(f"[OK] Raw audio received ({len(raw_pcm)} bytes)")

        # --- Step 3: Wrap PCM in WAV (in memory) ---
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(raw_pcm)
        raw_wav_bytes = wav_buffer.getvalue()

        # --- Step 4: Apply telephone effect via FFmpeg (stdin → stdout, no files) ---
        cmd = [
            "ffmpeg", "-y",
            "-f", "wav", "-i", "pipe:0",
            "-filter_complex",
            (
                "[0:a]highpass=f=600,lowpass=f=4500,"
                "compand=attacks=0:points=-80/-80|-20/-10|0/0,"
                "volume=18dB[voice];"
                "sine=f=350:d=3[s1];"
                "sine=f=440:d=3[s2];"
                "[s1][s2]amix=inputs=2,volume=-30dB[dial];"
                "[dial][voice][dial]concat=n=3:v=0:a=1[out]"
            ),
            "-map", "[out]",
            "-ar", "8000", "-ac", "1",
            "-f", "wav", "pipe:1",
        ]
        result = subprocess.run(
            cmd,
            input=raw_wav_bytes,
            capture_output=True,
            check=True,
        )
        print(f"[OK] FFmpeg finished ({len(result.stdout)} bytes)")
        return result.stdout

    except subprocess.CalledProcessError as e:
        print(f"[FFMPEG ERROR] {e.stderr.decode('utf-8', errors='replace')}")
        return None
    except Exception as e:
        print(f"[ERROR] {type(e).__name__}: {e}")
        return None
