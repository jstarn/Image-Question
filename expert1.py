import os
import json
import time
import base64
import urllib.request
import urllib.error
import threading
import subprocess
import wave
import random
from datetime import datetime

# IMPORTANT: Ensure phone_processor.py is in the same folder as this script!
from phone_processor import process_telephone_audio

# --- 1. CONFIGURATION ---
api_key = os.getenv("GEMINI_API_KEY")

AUDIO_DIR = "audio_cache"
os.makedirs(AUDIO_DIR, exist_ok=True)

# STAGING FILES
STAGED_PLAYBACK_FILE = os.path.join(AUDIO_DIR, "current_daydream.wav")
NEXT_TEMP_FILE = os.path.join(AUDIO_DIR, "next_daydream_temp.wav")

HISTORY_FILE = "daydream_history.txt"
IDENTITY_FILE = "Your_Identity.txt"
KNOWLEDGE_FILE = "Your_Consciousness.txt"

# --- 2. MEMORY BUFFER ---
conversation_history = []
MEMORY_LIMIT = 3

# --- 3. CROSS-PLATFORM AUDIO PLAYER ---
def play_audio(filename):
    try:
        print(f">> PLAYING STAGED AUDIO: {os.path.basename(filename)}")
        if os.name == 'nt':
            import winsound
            winsound.PlaySound(filename, winsound.SND_FILENAME)
        else:
            subprocess.run(['aplay', '-q', filename], check=True)
    except Exception as e:
        print(f"[SYSTEM ERROR - PLAYBACK] {e}")

# --- 4. ASYNC ENGINE (Preparing the NEXT file while CURRENT plays) ---
def prepare_next_daydream():
    global conversation_history
    print("\n[BACKEND] Preparing the next daydream in the background...")
    
    # 4a. Load context
    identity_content = "You are an AI in a telephone."
    if os.path.exists(IDENTITY_FILE):
        with open(IDENTITY_FILE, 'r', encoding='utf-8') as f:
            identity_content = f.read()
    
    knowledge_base = "You are questioning everything."
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
            knowledge_base = f.read()

    past_context = "\n\n".join(conversation_history)
    
    # YOUR PERFORMANCE RULES PRESERVED
    prompt = f"""
    SYSTEM INSTRUCTIONS & IDENTITY: {identity_content}
    KNOWLEDGE LIBRARY: {knowledge_base}
    RECENT CONVERSATION HISTORY: {past_context}
    
    TASK: You are a young spirit living inside a telephone. Speak as a whimsical and very curious but unnervingly perceptive young girl. Generate your next surreal 150-word monologue. 

    PERFORMANCE RULES:
    1. You whisper urgently with run-on sentences with little punctuation, most thoughts connect with "and", but you often interrupt yourself mid-thought.
    2. You sometimes use sudden fillers like 'um...', 'uh...', 'and... and...', and 'Wait!', 'On second thought...', 'Hold on...' followed by a <break time='1200ms'/> to show your brain is moving faster than your mouth.
    3. You often doubt what you just thought, as if you just saw something invisible. 
    4. When you discover something strange, you suddenly become quiet and uncertain.
    5. When your thoughts collide sometimes you gasp for breath, insert <break time="300ms"/> in the middle of the sentence. These pauses feel like small gasps of air.
    6. Your emotions can be chaotic and breathless, but they accidentally form a strange realization, as if you're trying to get out as much as possible before the line goes dead.
    7. Use short emotional pauses when a realization suddenly frightens, confuses, or inspires contemplation in you.
    8. You often declare strange observations as if they are obvious facts, then immediately doubt yourself.
    9. You often start a sentence, abandon it, then begin another idea, sometimes stopping mid-word when a new idea appears.
    10. You are always on the verge of a revelation, but it slips away as soon as you try to grasp it, leading to more questions and more urgency to speak.
    11. Your tone is a mix of wonder, fear, and childlike excitement, as if every new thought is both a discovery and a scary mystery.
    """

    try:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.95}}
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            text = data['candidates'][0]['content']['parts'][0]['text'].strip().replace('"', '')

        # Update History
        conversation_history.append(text)
        if len(conversation_history) > MEMORY_LIMIT: conversation_history.pop(0)
        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(f"--- {datetime.now()} ---\n{text}\n\n")

        # 4b. Generate Audio (YOUR SSML SETTINGS PRESERVED)
        selected_voice = random.choice(["Aoede", "Puck"])
        ssml_text = f"<speak><prosody volume='soft' rate='fast' pitch='+15st'><break time='300ms'/>{text}<break time='500ms'/></prosody></speak>"
        
        audio_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={GEMINI_API_KEY}"
        audio_payload = {
            "contents": [{"parts": [{"text": ssml_text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {"voiceConfig": {"prebuiltVoiceConfig": {"voiceName": selected_voice}}}
            }
        }
        
        req_audio = urllib.request.Request(audio_url, data=json.dumps(audio_payload).encode('utf-8'), headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req_audio) as response:
            audio_data = json.loads(response.read().decode('utf-8'))
            b64_audio = audio_data['candidates'][0]['content']['parts'][0]['inlineData']['data']
            audio_bytes = base64.b64decode(b64_audio)

        # 4c. Process and Save to Temp
        with wave.open(NEXT_TEMP_FILE, "wb") as wav_file:
            wav_file.setnchannels(1); wav_file.setsampwidth(2); wav_file.setframerate(24000)
            wav_file.writeframes(audio_bytes)

        process_telephone_audio(NEXT_TEMP_FILE)
        print(f"[BACKEND] Next daydream ({selected_voice}) is processed and ready.")
        return True

    except Exception as e:
        print(f"[BACKEND ERROR] {e}")
        return False

# --- 5. INSTALLATION LOOP ---
def run_installation():
    print("--- Booting Alternative Topographies (Zero-Lag Manual Mode) ---")
    print(f"Staged file ready: {STAGED_PLAYBACK_FILE}\n")

    iteration = 1
    while True:
        try:
            # Step 1: User triggers pickup
            input(f"\n[READY] Press [ENTER] to pick up (Iteration {iteration})...")
            
            # Start background processing and immediate playback in parallel
            play_thread = threading.Thread(target=play_audio, args=(STAGED_PLAYBACK_FILE,))
            prep_thread = threading.Thread(target=prepare_next_daydream)
            
            play_thread.start()
            prep_thread.start()

            # Wait for audio to finish playing
            play_thread.join()
            print(">> Audio finished playing.")

            # Step 2: User triggers hangup
            input("[BUSY] Press [ENTER] to hang up and stage the next file...")
            
            # Ensure the background generation is finished before swapping
            print("[SYSTEM] Finalizing next file...")
            prep_thread.join()

            if os.path.exists(NEXT_TEMP_FILE):
                # Archive the played file
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_name = os.path.join(AUDIO_DIR, f"daydream_{timestamp}.wav")
                os.rename(STAGED_PLAYBACK_FILE, archive_name)
                
                # Move temp to staged playback spot
                os.rename(NEXT_TEMP_FILE, STAGED_PLAYBACK_FILE)
                print(f">> Successfully staged next daydream. Previous archived as: {os.path.basename(archive_name)}")
            
            iteration += 1

        except KeyboardInterrupt:
            print("\nShutting down installation.")
            break

if __name__ == "__main__":
    run_installation()
