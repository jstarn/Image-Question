import os
import json
from expert1 import prepare_next_daydream, AUDIO_DIR

print("\n--- DAYDREAM SHELL TEST ---\n")

# --- 1. Trigger generation with debug ---
print("[1] Generating next daydream...")
success = prepare_next_daydream(debug=True)  # <-- Add debug=True to get raw API output
print("[2] Generation complete:", success)

# --- 2. Check local temp file ---
temp_wav = os.path.join(AUDIO_DIR, "next_daydream_temp_8khz.wav")
temp_mp3 = os.path.join(AUDIO_DIR, "next_daydream_temp.mp3")
print(f"[3] Local temp WAV exists: {os.path.exists(temp_wav)} ({temp_wav})")
print(f"[3b] Local temp MP3 exists: {os.path.exists(temp_mp3)} ({temp_mp3})")

# --- 3. Check staged playback ---
staged_wav = os.path.join(AUDIO_DIR, "current_daydream.wav")
staged_mp3 = os.path.join(AUDIO_DIR, "current_daydream.mp3")
print(f"[4] Current staged WAV exists: {os.path.exists(staged_wav)} ({staged_wav})")
print(f"[4b] Current staged MP3 exists: {os.path.exists(staged_mp3)} ({staged_mp3})")

# --- 4. List files in cloud bucket ---
print("[5] Listing audio files in cloud bucket...")
os.system("gsutil ls gs://image-qustion-bucket/audio/")

print("\n--- TEST COMPLETE ---\n")
