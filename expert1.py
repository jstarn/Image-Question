import os
import json
import base64
import urllib.request
import wave
import random
import time
import streamlit as st 

# --- 1. CONFIGURATION ---
# Get API Key from Streamlit Secrets
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")

from phone_processor import process_telephone_audio

# Use absolute paths to ensure the server finds the files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "audio_files")

# --- CRITICAL: Create folder if missing ---
if not os.path.exists(AUDIO_DIR):
    os.makedirs(AUDIO_DIR, exist_ok=True)

STAGED_PLAYBACK_FILE = os.path.join(AUDIO_DIR, "current_daydream.wav")
NEXT_TEMP_FILE = os.path.join(AUDIO_DIR, "next_daydream_temp.wav")
IDENTITY_FILE = os.path.join(BASE_DIR, "Your_Identity.txt")
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "Your_Consciousness.txt")

def prepare_next_daydream():
    """Summons the whisper using stable 1.5 models."""
    if not GEMINI_API_KEY:
        print("[ERROR] No API Key found in Secrets.")
        return False
        
    try:
        # Use the most stable Pro model available for text
        text_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={GEMINI_API_KEY}"
        
        # Load identity
        with open(IDENTITY_FILE, 'r') as f: identity = f.read()
        prompt = f"IDENTITY: {identity}\nTASK: speak as a spirit inside a phone."

        req_text = urllib.request.Request(text_url, data=json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req_text) as response:
            whisper_text = json.loads(response.read().decode('utf-8'))['candidates'][0]['content']['parts'][0]['text']

        # Audio Generation (Stable 1.5 Flash)
        audio_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        audio_payload = {
            "contents": [{"parts": [{"text": f"<speak>{whisper_text}</speak>"}]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": "Puck"}}}}
        }
        
        req_audio = urllib.request.Request(audio_url, data=json.dumps(audio_payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req_audio) as response:
            audio_bytes = base64.b64decode(json.loads(response.read().decode('utf-8'))['candidates'][0]['content']['parts'][0]['inlineData']['data'])

        # Write to temporary file first
        with wave.open(NEXT_TEMP_FILE, "wb") as wav_file:
            wav_file.setnchannels(1); wav_file.setsampwidth(2); wav_file.setframerate(24000); wav_file.writeframes(audio_bytes)

        # Apply telephone effect
        process_telephone_audio(NEXT_TEMP_FILE)
        
        # If no playback file exists, move temp to current
        if not os.path.exists(STAGED_PLAYBACK_FILE):
            os.replace(NEXT_TEMP_FILE, STAGED_PLAYBACK_FILE)
            
        return True
    except Exception as e:
        print(f"[API ERROR] {str(e)}")
        return False
