import os
import subprocess
import time

# --- LIGHTWEIGHT SLIDERS ---
LOW_CUT = 600           
HIGH_CUT = 4500         
COMPRESS_RATIO = "8:1"    
OVERALL_GAIN = "18dB"     
DIAL_TONE_DUR = 3         

def process_telephone_audio(filepath: str):
    """
    Processes audio using FFmpeg. Uses a temporary unique filename 
    to prevent file-access conflicts on the web server.
    """
    if not os.path.exists(filepath):
        print(f"[ERROR] Processor couldn't find: {filepath}")
        return filepath

    # Create a unique temporary output name
    temp_output = filepath.replace(".wav", f"_proc_{int(time.time())}.wav")
    
    # FFmpeg Pipeline for Telephone Effect
    cmd = [
        'ffmpeg', '-y', '-i', filepath,
        '-filter_complex', 
        f"[0:a]highpass=f={LOW_CUT},lowpass=f={HIGH_CUT},compand=attacks=0:points=-80/-80|-20/-10|0/0,volume={OVERALL_GAIN}[voice]; "
        f"sine=f=350:d={DIAL_TONE_DUR}[s1]; sine=f=440:d={DIAL_TONE_DUR}[s2]; [s1][s2]amix=inputs=2,volume=-30dB[dial]; "
        f"[dial][voice][dial]concat=n=3:v=0:a=1[out]",
        '-map', '[out]', '-ar', '8000', '-ac', '1', temp_output
    ]

    try:
        # Run FFmpeg
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # Atomically replace the old file with the new one
        if os.path.exists(temp_output):
            os.replace(temp_output, filepath)
            print(f"[CLOUD-READY] FFmpeg finished: {os.path.basename(filepath)}")
        
    except subprocess.CalledProcessError as e:
        print(f"[FFMPEG CRASH] {e.stderr}")
    except Exception as e:
        print(f"[PROCESSOR ERROR] {e}")

    return filepath
