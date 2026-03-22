import os
import subprocess

# --- LIGHTWEIGHT SLIDERS ---
# These match your "Child-Whisper" calibration 
LOW_CUT = 600           
HIGH_CUT = 4500         
COMPRESS_RATIO = "8:1"    # Magnifies tiny gasps and whispers [cite: 5]
OVERALL_GAIN = "18dB"     # Boosts the 'soft' SSML volume for the receiver
DIAL_TONE_DUR = 3         

def process_telephone_audio(filepath: str):
    temp_output = filepath.replace(".wav", "_processed.wav")
    
    # FFmpeg Pipeline: 
    # 1. Bandpass filter (600-4500Hz) to shrink the voice 
    # 2. Compand (Compression) to make the gasps urgent [cite: 5]
    # 3. Sine generation for the 1990s dial tone 
    cmd = [
        'ffmpeg', '-y', '-i', filepath,
        '-filter_complex', 
        f"[0:a]highpass=f={LOW_CUT},lowpass=f={HIGH_CUT},compand=attacks=0:points=-80/-80|-20/-10|0/0,volume={OVERALL_GAIN}[voice]; "
        f"sine=f=350:d={DIAL_TONE_DUR}[s1]; sine=f=440:d={DIAL_TONE_DUR}[s2]; [s1][s2]amix=inputs=2,volume=-30dB[dial]; "
        f"[dial][voice][dial]concat=n=3:v=0:a=1[out]",
        '-map', '[out]', '-ar', '8000', '-ac', '1', temp_output
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.replace(temp_output, filepath)
        print(f"[PI-OPTIMIZED] FFmpeg processed: {os.path.basename(filepath)}")
    except Exception as e:
        print(f"[ERROR] FFmpeg failed: {e}. Make sure ffmpeg is installed (sudo apt install ffmpeg).")

    return filepath