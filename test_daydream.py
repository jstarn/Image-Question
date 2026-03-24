import os
from expert1 import prepare_next_daydream, AUDIO_DIR, LATEST_FILE_NAME

print("\n--- DAYDREAM SHELL TEST ---\n")

# Trigger generation
print("[1] Generating next daydream...")
success = prepare_next_daydream()
print("[2] Generation complete:", success)

# Check local temp file
temp_path = os.path.join(AUDIO_DIR, "next_daydream_temp.wav")
print(f"[3] Local temp file exists: {os.path.exists(temp_path)} ({temp_path})")

# Check latest staged file if it exists
staged_path = os.path.join(AUDIO_DIR, "current_daydream.wav")
print(f"[4] Current staged file exists: {os.path.exists(staged_path)} ({staged_path})")

# Optional: list files in your cloud bucket (requires gsutil configured)
print("[5] Listing audio files in cloud bucket...")
os.system("gsutil ls gs://image-qustion-bucket/audio/")

with urllib.request.urlopen(req) as response:
    raw_response = response.read().decode('utf-8')
    print("[DEBUG] Raw API response:", raw_response)  # <-- see what actually comes back
    data = json.loads(raw_response)

print("\n--- TEST COMPLETE ---\n")
