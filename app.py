import streamlit as st
import os
import time
from expert1 import prepare_next_daydream, STAGED_PLAYBACK_FILE, AUDIO_DIR

st.set_page_config(page_title="Alternative Topographies", page_icon="☎️")

st.title("Alternative Topographies")
st.caption("A multi-sensory installation by Jeremy Starn")

# Sidebar Diagnostics
st.sidebar.header("System Status")
st.sidebar.write(f"Audio Folder: {'✅ Found' if os.path.exists(AUDIO_DIR) else '❌ Missing'}")
if os.path.exists(STAGED_PLAYBACK_FILE):
    st.sidebar.success("Staged Whisper: Ready")
else:
    st.sidebar.warning("Staged Whisper: Missing")

# Main Interface
if st.button("📞 Pick Up Receiver", use_container_width=True):
    if not os.path.exists(STAGED_PLAYBACK_FILE):
        with st.spinner("The line is dead... summoning a whisper. Please wait 15 seconds."):
            success = prepare_next_daydream()
            if success:
                st.rerun()
            else:
                st.error("Failed to summon a whisper. Check your Gemini API Key.")
    else:
        # File exists, play it
        with open(STAGED_PLAYBACK_FILE, "rb") as f:
            audio_bytes = f.read()
            st.audio(audio_bytes, format="audio/wav", autoplay=True)
        st.info("The spirit is whispering...")
        
        # Start preparing the next one automatically
        st.cache_data.clear() # Ensure the browser doesn't cache the old audio
        prepare_next_daydream()

if st.button("🔌 Hang Up", use_container_width=True):
    st.write("Line disconnected...")
    st.rerun()
