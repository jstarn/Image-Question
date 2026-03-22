import streamlit as st
import os
import time
from expert1 import prepare_next_daydream, STAGED_PLAYBACK_FILE, AUDIO_DIR

st.set_page_config(page_title="Alternative Topographies", page_icon="☎️")

st.title("Alternative Topographies")
st.caption("A multi-sensory installation by Jeremy Starn")

# --- KEY CHECKER DIAGNOSTIC ---
st.sidebar.header("System Diagnostics")

# Check if the Secret exists in Streamlit
if "GEMINI_API_KEY" in st.secrets:
    key_found = True
    # Basic validation: API keys usually start with 'AIza'
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
        with st.spinner("The line is quiet... summoning a whisper. This takes about 15 seconds."):
            success = prepare_next_daydream()
            if success:
                st.rerun()
            else:
                st.error("Failed to summon a whisper. Check the 'Manage App' logs for the specific error.")
    else:
        with open(STAGED_PLAYBACK_FILE, "rb") as f:
            st.audio(f.read(), format="audio/wav", autoplay=True)
        st.info("The spirit is whispering...")
        
        # Prepare next in background
        prepare_next_daydream()

if st.button("🔌 Hang Up", use_container_width=True):
    st.write("Line disconnected...")
    st.rerun()
