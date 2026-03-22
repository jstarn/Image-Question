import os
import json
import base64
import urllib.request
import wave
import random
import time
import streamlit as st 

# --- 1. CONFIGURATION ---
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY")

from phone_processor import process_telephone_audio

# Detect the server environment path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "audio_files")
os.makedirs(AUDIO_DIR, exist_ok=True)

STAGED_PLAYBACK_FILE = os.path.join(AUDIO_DIR, "current_daydream.wav")
NEXT_TEMP_FILE = os.path.join(AUDIO_DIR, "next_daydream_temp.wav")
IDENTITY_FILE = os.path.join(BASE_DIR, "Your_Identity.txt")
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "Your_Consciousness.txt")

conversation_history = []

def prepare_next_daydream():
    """Summons the whisper using stable 1.5 Pro and Flash models."""
    print("\n[BACKEND] Summoning whisper...")
    
    if not os.path.exists(IDENTITY_FILE):
        print(f"[ERROR] Missing {IDENTITY_FILE}")
        return False

    with open(IDENTITY_FILE, 'r') as f: identity = f.read()
    with open(KNOWLEDGE_FILE, 'r') as f: knowledge = f.read()
    
    prompt = f"IDENTITY: {identity}\nKNOWLEDGE: {knowledge}\nTASK: speak as the spirit."

    try:
        # Step 1: Text (Stable 1.5 Pro)
        text_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={GEMINI_API_KEY}"
        text_payload = {"contents": [{"parts": [{"text": prompt}]}]}
        
        req_text = urllib.request.Request(text_url, data=json.dumps(text_payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req_text) as response:
            data = json.loads(response.read().decode('utf-8'))
            whisper_text = data['candidates'][0]['content']['parts'][0]['text'].strip()

        # Step 2: Audio (Stable 1.5 Flash)
        selected_voice = random.choice(["Aoede", "Puck"])
        ssml = f"<speak><prosody rate='fast' pitch='+12st'>{whisper_text}</prosody></speak>"
        
        audio_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        audio_payload = {
            "contents": [{"parts": [{"text": ssml}]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": selected_voice}}}}
        }
        
        req_audio = urllib.request.Request(audio_url, data=json.dumps(audio_payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req_audio) as response:
            audio_data = json.loads(response.read().decode('utf-8'))
            audio_bytes = base64.b64decode(audio_data['candidates'][0]['content']['parts'][0]['inlineData']['data'])

        # Step 3: Write File
        with wave.open(NEXT_TEMP_FILE, "wb") as wav_file:
            wav_file.setnchannels(1); wav_file.setsampwidth(2); wav_file.setframerate(24000); wav_file.writeframes(audio_bytes)

        # Step 4: Process and Move
        process_telephone_audio(NEXT_TEMP_FILE)
        
        # If the playback file is missing (first run), move it there now
        if not os.path.exists(STAGED_PLAYBACK_FILE):
            os.replace(NEXT_TEMP_FILE, STAGED_PLAYBACK_FILE)
            
        return True
    except Exception as e:
        print(f"[API ERROR] {e}")
        return False
