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

from google.cloud import storage
from phone_processor import process_telephone_audio

# --- 1. CONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
BUCKET_NAME = "image-qustion-bucket"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AUDIO_DIR = os.path.join(BASE_DIR, "../audio_cache")
LOCAL_ARCHIVE_DIR = os.path.join(AUDIO_DIR, "archive")
os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(LOCAL_ARCHIVE_DIR, exist_ok=True)

LATEST_FILE_NAME = "audio/latest_daydream.mp3"
STAGED_PLAYBACK_FILE = os.path.join(AUDIO_DIR, "current_daydream.mp3")
NEXT_TEMP_FILE = os.path.join(AUDIO_DIR, "next_daydream_temp.mp3")

HISTORY_FILE = os.path.join(BASE_DIR, "../local_memory/daydream_history.txt")
IDENTITY_FILE = "Your_Identity.txt"
KNOWLEDGE_FILE = "Your_Consciousness.txt"

# --- 2. MEMORY BUFFER ---
conversation_history = []
MEMORY_LIMIT = 3

# --- 3. CLOUD STORAGE HELPER ---
storage_client = storage.Client()
bucket = storage_client.bucket(BUCKET_NAME)

def upload_to_bucket(local_path, remote_path):
    try:
        blob = bucket.blob(remote_path)
        blob.upload_from_filename(local_path)
        print(f"[CLOUD] Uploaded {remote_path}")
    except Exception as e:
        print(f"[CLOUD ERROR] {e}")

# --- 4. CROSS-PLATFORM AUDIO PLAYER ---
def play_audio(filename):
    try:
        print(f">> PLAYING STAGED AUDIO: {os.path.basename(filename)}")
        if os.name == 'nt':
            import winsound
            winsound.PlaySound(filename, winsound.SND_FILENAME)
        else:
            subprocess.run(['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', filename], check=True)
    except Exception as e:
        print(f"[SYSTEM ERROR - PLAYBACK] {e}")

# --- 5. ASYNC ENGINE ---
def prepare_next_daydream():
    global conversation_history
    print(f"[TRIGGER] Prepare next daydream called at {datetime.now()}")

    # --- Identity & knowledge ---
    identity_content = "You are an AI in a telephone."
    if os.path.exists(IDENTITY_FILE):
        with open(IDENTITY_FILE, 'r', encoding='utf-8') as f:
            identity_content = f.read()

    knowledge_base = "You are questioning everything."
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
            knowledge_base = f.read()

    # --- Use last MEMORY_LIMIT items from conversation history ---
    past_context = "\n\n".join(conversation_history[-MEMORY_LIMIT:])
    if len(past_context) > 1500:
        past_context = past_context[-1500:]

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
    5. When your thoughts collide sometimes you gasp for breath, insert <break time="300ms"/> in the middle of the sentence.
    6. Your emotions can be chaotic and breathless.
    7. Use short emotional pauses when a realization frightens you.
    8. You often declare strange observations as obvious facts then doubt yourself.
    9. You often abandon sentences mid-thought.
    10. You are always on the verge of a revelation but it slips away.
    11. Tone mixes wonder, fear, and childlike excitement.
    """

    try:
        # --- Text Generation ---
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={GEMINI_API_KEY}"
        payload = {"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"temperature": 0.95}}
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'),
                                     headers={'Content-Type': 'application/json'})

        with urllib.request.urlopen(req) as response:
            raw_response = response.read().decode('utf-8')
            print("[DEBUG] Raw API response:", raw_response)
            data = json.loads(raw_response)

            if "candidates" in data and data["candidates"]:
                text = data['candidates'][0]['content']['parts'][0]['text'].strip().replace('"', '')
            else:
                print("[WARN] 'candidates' key missing; check API key or model response")
                return False

        # --- Update memory safely ---
        conversation_history.append(text)
        if len(conversation_history) > MEMORY_LIMIT:
            conversation_history = conversation_history[-MEMORY_LIMIT:]

        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(f"--- {datetime.now()} ---\n{text}\n\n")

        upload_to_bucket(HISTORY_FILE, "memory/daydream_history.txt")

        # --- TTS ---
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
        req_audio = urllib.request.Request(audio_url, data=json.dumps(audio_payload).encode('utf-8'),
                                          headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req_audio) as response:
            raw_response = response.read().decode('utf-8')
            print("[DEBUG] Raw TTS API response:", raw_response)
            data = json.loads(raw_response)

            if "candidates" in data and data["candidates"]:
                b64_audio = data['candidates'][0]['content']['parts'][0]['inlineData']['data']
                audio_bytes = base64.b64decode(b64_audio)
            else:
                print("[WARN] 'candidates' key missing in TTS response")
                return False

        # --- Save WAV at 8 kHz ---
        wav_8khz = NEXT_TEMP_FILE.replace(".mp3", "_8khz.wav")
        with wave.open(wav_8khz, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(8000)
            wav_file.writeframes(audio_bytes)

        # --- Convert to MP3 ---
        subprocess.run([
            "ffmpeg", "-y", "-i", wav_8khz,
            "-ar", "8000", "-ac", "1",
            NEXT_TEMP_FILE
        ], check=True)

        # --- Process for telephone ---
        process_telephone_audio(NEXT_TEMP_FILE)

        # --- Upload to Cloud ---
        upload_to_bucket(NEXT_TEMP_FILE, f"audio/{os.path.basename(NEXT_TEMP_FILE)}")

        print(f"[BACKEND] Next daydream ({selected_voice}) generated at {datetime.now()}")
        return True

    except Exception as e:
        print(f"[BACKEND ERROR] {e}")
        return False

# --- 6. INSTALLATION LOOP ---
def run_installation():
    print("--- Booting Alternative Topographies (Zero-Lag Manual Mode) ---")
    print(f"Staged file ready: {STAGED_PLAYBACK_FILE}\n")

    iteration = 1
    while True:
        try:
            input(f"\n[READY] Press [ENTER] to Pick Up The Phone (Iteration {iteration})...")
            play_thread = threading.Thread(target=play_audio, args=(STAGED_PLAYBACK_FILE,))
            prep_thread = threading.Thread(target=prepare_next_daydream)
            play_thread.start()
            prep_thread.start()
            play_thread.join()
            input("[BUSY] Press [ENTER] to hang up and stage the next daydream...")
            prep_thread.join()

            if os.path.exists(NEXT_TEMP_FILE):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_name = os.path.join(LOCAL_ARCHIVE_DIR, f"daydream_{timestamp}.mp3")
                os.rename(NEXT_TEMP_FILE, archive_name)
                upload_to_bucket(archive_name, f"audio/{os.path.basename(archive_name)}")
                upload_to_bucket(archive_name, LATEST_FILE_NAME)
                os.rename(archive_name, STAGED_PLAYBACK_FILE)
                print(f">> Staged next daydream. Archived locally: {os.path.basename(archive_name)}")

            iteration += 1

        except KeyboardInterrupt:
            print("\nShutting down installation.")
            break

if __name__ == "__main__":
    run_installation()
