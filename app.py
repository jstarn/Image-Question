import streamlit as st
import os
import time
from expert1 import prepare_next_daydream, STAGED_PLAYBACK_FILE, AUDIO_DIR

st.set_page_config(page_title="Alternative Topographies", page_icon="☎️")

st.title("Alternative Topographies")
st.caption("A multi-sensory installation by Jeremy Starn")

# --- DIAGNOSTICS SIDEBAR ---
st.sidebar.header("System Diagnostics")

if "GEMINI_API_KEY" in st.secrets:
    key_found = True
    is_valid_format = st.secrets["GEMINI_API_KEY"].startswith("AIza")
    st.sidebar.success(f"API Key Secret: {'✅ Connected' if is_valid_format else '⚠️ Format Error'}")
else:
    key_found = False
    st.sidebar.error("API Key Secret: ❌ Not Found")

st.sidebar.write(f"Audio Folder: {'✅ Found' if os.path.exists(AUDIO_DIR) else '❌ Missing'}")
st.sidebar.write(f"Staged Whisper: {'✅ Ready' if os.path.exists(STAGED_PLAYBACK_FILE) else '❌ Missing'}")

# --- MAIN INTERFACE ---
if st.button("📞 Pick Up Receiver", use_container_width=True):
    if not key_found:
        st.error("Cannot connect to the spirit. The API Key is missing from Streamlit Secrets.")

    elif not os.path.exists(STAGED_PLAYBACK_FILE):
        # No staged file — generate one now and wait
        with st.spinner("The line is quiet... summoning a whisper. This takes about 15 seconds."):
            success = prepare_next_daydream()
        if success:
            st.rerun()
        else:
            st.error("Failed to summon a whisper. Check the 'Manage App' logs for the specific error.")

    else:
        # FIX: Read the audio into memory FIRST, then delete the file,
        # so the next button press always triggers a fresh generation.
        with open(STAGED_PLAYBACK_FILE, "rb") as f:
            audio_bytes = f.read()

        # Remove staged file before playing so the next press regenerates
        os.remove(STAGED_PLAYBACK_FILE)

        st.audio(audio_bytes, format="audio/wav", autoplay=True)
        st.info("The spirit is whispering...")

        # Pre-generate the next whisper in the background while this one plays
        with st.spinner("Preparing the next whisper..."):
            prepare_next_daydream()

if st.button("🔌 Hang Up", use_container_width=True):
    st.write("Line disconnected...")
    st.rerun()
