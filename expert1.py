import os
import json
import base64
import urllib.request
import threading
import subprocess
import wave
import random
import time
from datetime import datetime
import streamlit as st 

# --- 1. CONFIGURATION ---
# Prioritize Streamlit Secrets for the API Key
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("API Key missing! Add GEMINI_API_KEY to your Streamlit Secrets dashboard.")

from phone_processor import process_telephone_audio

# Set up paths relative to the script's home folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "audio_files")
os.makedirs(AUDIO_DIR, exist_ok=True)

STAGED_PLAYBACK_FILE = os.path.join(AUDIO_DIR, "current_daydream.wav")
NEXT_TEMP_FILE = os.path.join(AUDIO_DIR, "next_daydream_temp.wav")
IDENTITY_FILE = os.path.join(BASE_DIR, "Your_Identity.txt")
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "Your_Consciousness.txt")

conversation_history = []
MEMORY_LIMIT = 2

def prepare_next_daydream():
    """Generates the next whisper using stable 1.5 models."""
    global conversation_history
    print("\n[BACKEND] Summoning a new whisper...")
    
    if not os.path.exists(IDENTITY_FILE) or not os.path.exists(KNOWLEDGE_FILE):
        print(f"[CRITICAL ERROR] Missing identity or consciousness files.")
        return False

    with open(IDENTITY_FILE, 'r', encoding='utf-8') as f: identity_content = f.read()
    with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f: knowledge_base = f.read()
    past_context = "\n\n".join(conversation_history)
    
    prompt = f"IDENTITY: {identity_content}\nKNOWLEDGE: {knowledge_base}\nHISTORY: {past_context}"

    try:
        # Step 1: Text Generation (Stable 1.5 Pro)
        text_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-pro:generateContent?key={GEMINI_API_KEY}"
        text_payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.9}}
        
        req_text = urllib.request.Request(text_url, data=json.dumps(text_payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req_text) as response:
            data = json.loads(response.read().decode('utf-8'))
            whisper_text = data['candidates'][0]['content']['parts'][0]['text'].strip().replace('"', '')

        conversation_history.append(whisper_text)
        if len(conversation_history) > MEMORY_LIMIT: conversation_history.pop(0)

        # Step 2: TTS Generation (Stable 1.5 Flash)
        selected_voice = random.choice(["Aoede", "Puck"])
        ssml_text = f"<speak><prosody volume='soft' rate='fast' pitch='+12st'>{whisper_text}</prosody></speak>"
        
        audio_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        audio_payload = {
            "contents": [{"parts": [{"text": ssml_text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": selected_voice}}}}
        }
        
        req_audio = urllib.request.Request(audio_url, data=json.dumps(audio_payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req_audio) as response:
            audio_response = json.loads(response.read().decode('utf-8'))
            audio_bytes = base64.b64decode(audio_response['candidates'][0]['content']['parts'][0]['inlineData']['data'])

        # Step 3: Write and Process Audio
        with wave.open(NEXT_TEMP_FILE, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(24000)
            wav_file.writeframes(audio_bytes)

        process_telephone_audio(NEXT_TEMP_FILE)
        
        # Atomic Swapping: If no playback file exists, move the temp file there now
        if not os.path.exists(STAGED_PLAYBACK_FILE):
            os.replace(NEXT_TEMP_FILE, STAGED_PLAYBACK_FILE)
            print("[BACKEND] First whisper staged successfully.")
            
        return True

    except urllib.error.HTTPError as e:
        print(f"[API ERROR] HTTP {e.code}: {e.reason}")
        return False
    except Exception as e:
        print(f"[SYSTEM ERROR] {str(e)}")
        return False

def run_installation():
    """Initializes the background directory and first whisper."""
    print("--- Alternative Topographies System Active ---")
    if not os.path.exists(STAGED_PLAYBACK_FILE):
        prepare_next_daydream()

if __name__ == "__main__": 
    run_installation()
