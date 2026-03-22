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
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("API Key not found! Add it to Streamlit Secrets.")

from phone_processor import process_telephone_audio

# Use a relative path from the script's directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "audio_files")
os.makedirs(AUDIO_DIR, exist_ok=True)

STAGED_PLAYBACK_FILE = os.path.join(AUDIO_DIR, "current_daydream.wav")
NEXT_TEMP_FILE = os.path.join(AUDIO_DIR, "next_daydream_temp.wav")
HISTORY_FILE = os.path.join(BASE_DIR, "daydream_history.txt")
IDENTITY_FILE = os.path.join(BASE_DIR, "Your_Identity.txt")
KNOWLEDGE_FILE = os.path.join(BASE_DIR, "Your_Consciousness.txt")

conversation_history = []
MEMORY_LIMIT = 2

def play_audio(filename):
    print(f"[WEB-READY] Audio ready for browser: {filename}")

def prepare_next_daydream():
    global conversation_history
    print("\n[BACKEND] Generating whisper...")
    
    if not os.path.exists(IDENTITY_FILE) or not os.path.exists(KNOWLEDGE_FILE):
        print(f"[ERROR] Missing identity/knowledge files.")
        return False

    with open(IDENTITY_FILE, 'r', encoding='utf-8') as f: identity_content = f.read()
    with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f: knowledge_base = f.read()
    past_context = "\n\n".join(conversation_history)
    
    prompt = f"IDENTITY: {identity_content}\nKNOWLEDGE: {knowledge_base}\nHISTORY: {past_context}\nTASK: monlogue as the child spirit."

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-pro-exp-02-05:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.95}}
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            text = data['candidates'][0]['content']['parts'][0]['text'].strip().replace('"', '')

        conversation_history.append(text)
        if len(conversation_history) > MEMORY_LIMIT: conversation_history.pop(0)

        selected_voice = random.choice(["Aoede", "Puck"])
        ssml_text = f"<speak><prosody volume='soft' rate='fast' pitch='+12st'>{text}</speak>"
        
        audio_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}"
        audio_payload = {
            "contents": [{"parts": [{"text": ssml_text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": selected_voice}}}}
        }
        
        req_audio = urllib.request.Request(audio_url, data=json.dumps(audio_payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req_audio) as response:
            audio_bytes = base64.b64decode(json.loads(response.read().decode('utf-8'))['candidates'][0]['content']['parts'][0]['inlineData']['data'])

        # WRITING THE FILE
        with wave.open(NEXT_TEMP_FILE, "wb") as wav_file:
            wav_file.setnchannels(1); wav_file.setsampwidth(2); wav_file.setframerate(24000); wav_file.writeframes(audio_bytes)

        # PROCESS WITH FFMEG
        process_telephone_audio(NEXT_TEMP_FILE)
        
        # LOGIC FIX: Move temp to staged immediately if staged is missing
        if not os.path.exists(STAGED_PLAYBACK_FILE):
            os.rename(NEXT_TEMP_FILE, STAGED_PLAYBACK_FILE)
            
        return True
    except Exception as e:
        print(f"[BACKEND ERROR] {e}"); return False

def run_installation():
    if not os.path.exists(STAGED_PLAYBACK_FILE):
        prepare_next_daydream()

if __name__ == "__main__": 
    run_installation()
