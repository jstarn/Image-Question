import os
from expert1 import prepare_next_daydream, AUDIO_DIR, LATEST_FILE_NAME

print("\n--- DAYDREAM SHELL TEST ---\n")

# --- 1. Generate next daydream ---
print("[1] Generating next daydream...")
success = prepare_next_daydream()
print("[2] Generation complete:", success)

# --- 2. Check local temp file ---
temp_wav = os.path.join(AUDIO_DIR, "next_daydream_temp_8khz.wav")
print(f"[3] Local temp WAV exists: {os.path.exists(temp_wav)} ({temp_wav})")

temp_mp3 = os.path.join(AUDIO_DIR, "next_daydream_temp.mp3")
print(f"[4] Local temp MP3 exists: {os.path.exists(temp_mp3)} ({temp_mp3})")

# --- 3. Check staged playback ---
staged_file = os.path.join(AUDIO_DIR, "current_daydream.mp3")
print(f"[5] Staged playback exists: {os.path.exists(staged_file)} ({staged_file})")

# --- 4. List files in Cloud Bucket ---
print("[6] Listing audio files in cloud bucket...")
os.system("gsutil ls gs://image-qustion-bucket/audio/")

print("\n--- TEST COMPLETE ---\n")
