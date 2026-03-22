import os
import json
import base64
import urllib.request
import threading
import subprocess
import wave
import random
from datetime import datetime
import streamlit as st 

# --- 1. CONFIGURATION ---
# This looks for 'GEMINI_API_KEY' in Streamlit's Secrets dashboard first
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") or os.environ.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("API Key not found! Please add GEMINI_API_KEY to your Streamlit Secrets.")

# Import the new lightweight processor
from phone_processor import process_telephone_audio

# Use a relative path so it works on the Linux web server
AUDIO_DIR = "audio_files"
os.makedirs(AUDIO_DIR, exist_ok=True)

STAGED_PLAYBACK_FILE = os.path.join(AUDIO_DIR, "current_daydream.wav")
NEXT_TEMP_FILE = os.path.join(AUDIO_DIR, "next_daydream_temp.wav")
HISTORY_FILE = "daydream_history.txt"
IDENTITY_FILE = "Your_Identity.txt"
KNOWLEDGE_FILE = "Your_Consciousness.txt"

conversation_history = []
MEMORY_LIMIT = 2

def play_audio(filename):
    """
    On a web server, the browser handles playback via app.py.
    This function is kept for logic compatibility but won't trigger server speakers.
    """
    print(f"[WEB-READY] Audio staged for browser: {filename}")

def prepare_next_daydream():
    global conversation_history
    print("\n[BACKEND] Preparing next whisper...")
    
    # Ensure files exist before reading to avoid FileNotFoundError
    if not os.path.exists(IDENTITY_FILE) or not os.path.exists(KNOWLEDGE_FILE):
        print(f"[ERROR] Missing {IDENTITY_FILE} or {KNOWLEDGE_FILE} in repository.")
        return False

    with open(IDENTITY_FILE, 'r', encoding='utf-8') as f: identity_content = f.read()
    with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f: knowledge_base = f.read()
    past_context = "\n\n".join(conversation_history)
    
    # YOUR 11 PERFORMANCE RULES
    prompt = f"""
    IDENTITY: {identity_content}
    KNOWLEDGE: {knowledge_base}
    HISTORY: {past_context}
    
    TASK: You are a young spirit living inside a telephone. Speak as a whimsical and very curious but unnervingly perceptive young girl. 
    
    PERFORMANCE RULES:
    1. Speak urgently with run-on sentences connected only by 'and'. 
    2. Use excessive fillers like 'um...', 'Wait!', 'On second thought...' followed by <break time='1200ms'/>.
    3. Doubt what you just thought. 
    4. When you discover something strange, you suddenly become quiet and uncertain.
    5. Insert <break time="300ms"/> when your thoughts collide or you gasp for breath.
    6. Monologue should feel like a stream of consciousness.
    7. Use short emotional pauses when a realization frightens you.
    8. State observations as startling facts, not lessons.
    9. Abandon sentences mid-word when a new idea appears.
    10. You are always on the verge of a revelation that slips away.
    11. Tone is a mix of wonder, fear, and childlike excitement.
    """

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
        ssml_text = f"<speak><prosody volume='soft' rate='fast' pitch='+12st'><break time='300ms'/>{text}<break time='500ms'/></prosody></speak>"
        
        audio_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash-exp:generateContent?key={GEMINI_API_KEY}"
        audio_payload = {
            "contents": [{"parts": [{"text": ssml_text}]}],
            "generationConfig": {"responseModalities": ["AUDIO"], "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": selected_voice}}}}
        }
        
        req_audio = urllib.request.Request(audio_url, data=json.dumps(audio_payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req_audio) as response:
            audio_bytes = base64.b64decode(json.loads(response.read().decode('utf-8'))['candidates'][0]['content']['parts'][0]['inlineData']['data'])

        with wave.open(NEXT_TEMP_FILE, "wb") as wav_file:
            wav_file.setnchannels(1); wav_file.setsampwidth(2); wav_file.setframerate(24000); wav_file.writeframes(audio_bytes)

        process_telephone_audio(NEXT_TEMP_FILE)
        return True
    except Exception as e:
        print(f"[BACKEND ERROR] {e}"); return False

def run_installation():
    """
    On Streamlit, the main loop is handled by app.py's buttons.
    This remains for local terminal testing if needed.
    """
    print("--- Alternative Topographies Web-Ready Booted ---")
    if not os.path.exists(STAGED_PLAYBACK_FILE):
        prepare_next_daydream()

if __name__ == "__main__": 
    run_installation()
