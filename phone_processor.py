import subprocess
import os

# --- CONFIGURATION SLIDERS ---
LOW_CUT = 400           # Tighter range for that "boxy" phone sound
HIGH_CUT = 3200         # Standard 1990s POTS (Plain Old Telephone Service) limit
COMPRESS_RATIO = 8      # Keeps whispers loud against the noise floor
OVERALL_GAIN = 12       # Master boost (in dB)
HISS_VOL = 0.015        # The "Static" level (0.01 to 0.05 recommended)
SATURATION = 15         # Adds the "Analog Warmth" (harmonic distortion)
BIT_DEPTH = 8           # Lowers quality to 8-bit for digital grit

def process_telephone_audio(filepath: str):
    temp_output = filepath.replace(".wav", "_processed.wav")
    
    # VOICE CHAIN: Bandpass -> Distortion -> Bitcrush -> Compression -> Volume
    voice_chain = (
        f"highpass=f={LOW_CUT},lowpass=f={HIGH_CUT},"
        f"asoverdrive=gain={SATURATION}:dry_mix=0.6," # Harmonic warmth
        f"acrusher=bits={BIT_DEPTH}:mode=log:aa=1,"    # Digital grit/lower quality
        f"compand=attacks=0:points=-80/-80|-25/-25|-15/-5|0/0," # Whisper magnifier
        f"volume={OVERALL_GAIN}dB"
    )

    # MASTER GRAPH: 
    # 1. Generates Dial Tones
    # 2. Generates a constant White Noise "Hiss"
    # 3. Mixes Hiss into the Voice
    # 4. Concatenates: [DialTone+Hiss] -> [Voice+Hiss] -> [DialTone+Hiss]
    cmd = [
        'ffmpeg', '-y', '-i', filepath,
        '-filter_complex', 
        # Generate sources
        f"asine=f=350:d=3[t1];asine=f=440:d=3[t2];[t1][t2]amix=inputs=2[dt];" # Dial Tone
        f"anoisesrc=d=60:a={HISS_VOL}:c=white[hiss];" # The Static source
        f"asine=f=150:d=0.05[c1];asine=f=800:d=0.02[c2];[c1][c2]amix=inputs=2[clk];" # Click
        # Apply voice filters
        f"[0:a]{voice_chain}[v];"
        # Mix Hiss into everything for "Live Line" feel
        f"[dt][hiss]amix=inputs=2:duration=first[dt_hiss];"
        f"[v][hiss]amix=inputs=2:duration=first[v_hiss];"
        f"[clk][hiss]amix=inputs=2:duration=first[clk_hiss];"
        # Stitch it together
        f"[dt_hiss][v_hiss][clk_hiss][dt_hiss]concat=n=4:v=0:a=1[out]",
        '-map', '[out]', '-ac', '1', '-ar', '8000', temp_output
    ]

    try:
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        os.replace(temp_output, filepath)
        return filepath
    except Exception as e:
        print(f"[FFMPEG ERROR] {e}. Check if FFmpeg filters are supported.")
        return filepath
