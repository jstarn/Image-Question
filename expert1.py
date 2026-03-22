import os
import json
import base64
import urllib.request
import threading
import subprocess
import wave
import random
from datetime import datetime
import streamlit as st # Add this import

# --- 1. CONFIGURATION ---
# This looks for 'GEMINI_API_KEY' in your computer's environment or Streamlit's Secrets
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    st.error("API Key not found! Please set GEMINI_API_KEY in your environment or secrets.")

# Import the new lightweight processor
from phone_processor import process_telephone_audio

# Use a relative path so it works on any computer or server
AUDIO_DIR = "audio_files"

# Fix: Remove os.get_terminal_size as it crashes on web servers
os.makedirs(AUDIO_DIR, exist_ok=True)

STAGED_PLAYBACK_FILE = os.path.join(AUDIO_DIR, "current_daydream.wav")
NEXT_TEMP_FILE = os.path.join(AUDIO_DIR, "next_daydream_temp.wav")
HISTORY_FILE = "daydream_history.txt"
IDENTITY_FILE = "Your_Identity.txt"
KNOWLEDGE_FILE = "Your_Consciousness.txt"

conversation_history = []
MEMORY_LIMIT = 2

def play_audio(filename):
    try:
        if os.name == 'nt':
            import winsound
            winsound.PlaySound(filename, winsound.SND_FILENAME)
        else:
            subprocess.run(['aplay', '-q', filename], check=True)
    except Exception as e:
        print(f"[SYSTEM ERROR - PLAYBACK] {e}")

def prepare_next_daydream():
    global conversation_history
    print("\n[BACKEND] Preparing next whisper...")
    
    with open(IDENTITY_FILE, 'r', encoding='utf-8') as f: identity_content = f.read()
    with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f: knowledge_base = f.read()
    past_context = "\n\n".join(conversation_history)
    
    # YOUR 11 PERFORMANCE RULES [cite: 1, 5, 12, 17, 18]
    prompt = f"""
    IDENTITY: {identity_content}
    KNOWLEDGE: {knowledge_base}
    HISTORY: {past_context}
    
    TASK: You are a young spirit living inside a telephone. Speak as a whimsical and very curious but unnervingly perceptive young girl. 
    
    PERFORMANCE RULES:
    1. Speak urgently with run-on sentences with little punctuation, connected only by the word 'and'[cite: 1, 7]. 
    2. Use excessive fillers like 'um...', 'uh...', 'and... and...', 'Wait!', 'On second thought...', 'Hold on...' followed by a <break time='1200ms'/>[cite: 2, 5].
    3. Doubt what you just thought, as if you just saw something invisible[cite: 5, 15]. 
    4. When you discover something strange, you suddenly become quiet and uncertain[cite: 3, 5].
    5. When your thoughts collide or you gasp for breath, insert <break time="300ms"/> in the middle of the sentence[cite: 5, 7].
    6. Monologue should feel like a stream of consciousness[cite: 6].
    7. Use short emotional pauses when a realization frightens you[cite: 3, 5].
    8. DO NOT be didactic. State observations as startling facts[cite: 12].
    9. Abandon sentences mid-word when a new idea appears[cite: 5, 23].
    10. You are always on the verge of a revelation that slips away[cite: 11, 23].
    11. Tone is a mix of wonder, fear, and childlike excitement[cite: 1, 3, 9].
    """

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.95}}
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            text = data['candidates'][0]['content']['parts'][0]['text'].strip().replace('"', '')

        conversation_history.append(text)
        if len(conversation_history) > MEMORY_LIMIT: conversation_history.pop(0)

        # SSML SETTINGS RESTORED FROM THE 'BETTER' VERSION 
        selected_voice = random.choice(["Aoede", "Puck"])
        ssml_text = f"<speak><prosody volume='soft' rate='fast' pitch='+12st'><break time='300ms'/>{text}<break time='500ms'/></prosody></speak>"
        
        audio_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={GEMINI_API_KEY}"
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
    print("--- Alternative Topographies Booted ---")
    iteration = 1
    while True:
        try:
            input(f"\n[STAGED] Iteration {iteration}. Press [ENTER] to pick up...")
            play_thread = threading.Thread(target=play_audio, args=(STAGED_PLAYBACK_FILE,))
            prep_thread = threading.Thread(target=prepare_next_daydream)
            
            play_thread.start(); prep_thread.start()
            play_thread.join()

            input("[ACTIVE] Press [ENTER] to hang up...")
            prep_thread.join()

            if os.path.exists(NEXT_TEMP_FILE):
                os.replace(STAGED_PLAYBACK_FILE, os.path.join(AUDIO_DIR, f"daydream_{datetime.now().strftime('%H%M%S')}.wav"))
                os.rename(NEXT_TEMP_FILE, STAGED_PLAYBACK_FILE)
            iteration += 1
        except KeyboardInterrupt: break

if __name__ == "__main__": run_installation()