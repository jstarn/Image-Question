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

# CLOUD STORAGE IMPORT
from google.cloud import storage

# IMPORTANT: Ensure phone_processor.py is in the same folder as this script!
from phone_processor import process_telephone_audio

# --- 1. CONFIGURATION ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# CLOUD BUCKET
BUCKET_NAME = "image-qustion-bucket"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

AUDIO_DIR = os.path.join(BASE_DIR, "../audio_cache")
os.makedirs(AUDIO_DIR, exist_ok=True)

LATEST_FILE_NAME = "audio/latest_daydream.wav"

# STAGING FILES
STAGED_PLAYBACK_FILE = os.path.join(AUDIO_DIR, "current_daydream.wav")
NEXT_TEMP_FILE = os.path.join(AUDIO_DIR, "next_daydream_temp.wav")

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
        # Set correct MIME type for web playback
        blob.content_type = "audio/wav"
        blob.upload_from_filename(local_path)
        # Make public so the web app can fetch
        blob.make_public()
        print(f"[CLOUD] Uploaded {remote_path} (public URL: {blob.public_url})")
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
            subprocess.run(['aplay', '-q', filename], check=True)
    except Exception as e:
        print(f"[SYSTEM ERROR - PLAYBACK] {e}")

# --- 5. ASYNC ENGINE ---
def prepare_next_daydream():
    global conversation_history
    print("\n[BACKEND] Preparing the next daydream in the background...")
    
    identity_content = "You are an AI in a telephone."
    if os.path.exists(IDENTITY_FILE):
        with open(IDENTITY_FILE, 'r', encoding='utf-8') as f:
            identity_content = f.read()
    
    knowledge_base = "You are questioning everything."
    if os.path.exists(KNOWLEDGE_FILE):
        with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
            knowledge_base = f.read()

    past_context = "\n\n".join(conversation_history)
    
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
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-pro:generateContent?key={GEMINI_API_KEY}"

        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.95}
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))
            text = data['candidates'][0]['content']['parts'][0]['text'].strip().replace('"', '')

        # Update memory
        conversation_history.append(text)
        if len(conversation_history) > MEMORY_LIMIT:
            conversation_history.pop(0)

        with open(HISTORY_FILE, "a", encoding="utf-8") as f:
            f.write(f"--- {datetime.now()} ---\n{text}\n\n")

        # Upload updated memory to cloud
        upload_to_bucket(HISTORY_FILE, "memory/daydream_history.txt")

        # TTS
        selected_voice = random.choice(["Aoede", "Puck"])

        ssml_text = f"<speak><prosody volume='soft' rate='fast' pitch='+15st'><break time='300ms'/>{text}<break time='500ms'/></prosody></speak>"

        audio_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-tts:generateContent?key={GEMINI_API_KEY}"

        audio_payload = {
            "contents": [{"parts": [{"text": ssml_text}]}],
            "generationConfig": {
                "responseModalities": ["AUDIO"],
                "speechConfig": {
                    "voiceConfig": {
                        "prebuiltVoiceConfig": {"voiceName": selected_voice}
                    }
                }
            }
        }

        req_audio = urllib.request.Request(
            audio_url,
            data=json.dumps(audio_payload).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req_audio) as response:
            audio_data = json.loads(response.read().decode('utf-8'))
            b64_audio = audio_data['candidates'][0]['content']['parts'][0]['inlineData']['data']
            audio_bytes = base64.b64decode(b64_audio)

        with wave.open(NEXT_TEMP_FILE, "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(24000)
            wav_file.writeframes(audio_bytes)

        process_telephone_audio(NEXT_TEMP_FILE)

        print(f"[BACKEND] Next daydream ({selected_voice}) processed.")

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

            input(f"\n[READY] Press [ENTER] to pick up (Iteration {iteration})...")

            play_thread = threading.Thread(target=play_audio, args=(STAGED_PLAYBACK_FILE,))
            prep_thread = threading.Thread(target=prepare_next_daydream)

            play_thread.start()
            prep_thread.start()

            play_thread.join()

            input("[BUSY] Press [ENTER] to hang up and stage the next file...")

            prep_thread.join()

            if os.path.exists(NEXT_TEMP_FILE):

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                archive_name = os.path.join(AUDIO_DIR, f"daydream_{timestamp}.wav")

                # Archive the current staged file
                os.rename(STAGED_PLAYBACK_FILE, archive_name)

                # Upload archived audio to cloud (with MIME type + public)
                upload_to_bucket(archive_name, f"audio/{os.path.basename(archive_name)}")

                # ALSO update the latest_daydream.wav in cloud (with MIME type + public)
                upload_to_bucket(archive_name, LATEST_FILE_NAME)

                # Move next temp file to staged playback
                os.rename(NEXT_TEMP_FILE, STAGED_PLAYBACK_FILE)

                print(f">> Staged next daydream. Archived: {os.path.basename(archive_name)} (latest_daydream.wav updated)")

            iteration += 1

        except KeyboardInterrupt:
            print("\nShutting down installation.")
            break

if __name__ == "__main__":
    run_installation()
