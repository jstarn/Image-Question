import streamlit as st
import os
from expert1 import generate_whisper, BASE_DIR, IDENTITY_FILE

st.set_page_config(page_title="Alternative Topographies", page_icon="☎️")

st.title("Alternative Topographies")
st.caption("A multi-sensory installation by Jeremy Starn")

# --- DIAGNOSTICS SIDEBAR ---
st.sidebar.header("System Diagnostics")

if "GEMINI_API_KEY" in st.secrets:
    is_valid_format = st.secrets["GEMINI_API_KEY"].startswith("AIza")
    st.sidebar.success(f"API Key: {'✅ Connected' if is_valid_format else '⚠️ Format Error'}")
    key_found = True
else:
    st.sidebar.error("API Key: ❌ Not Found in Secrets")
    key_found = False

st.sidebar.write(f"Identity File: {'✅ Found' if os.path.exists(IDENTITY_FILE) else '❌ Missing'}")

# --- MAIN INTERFACE ---
st.write("")

if st.button("📞 Pick Up Receiver", use_container_width=True):
    if not key_found:
        st.error("Cannot connect. The GEMINI_API_KEY is missing from Streamlit Secrets.")
    else:
        with st.spinner("The line crackles... summoning a whisper (~15 seconds)"):
            audio_bytes = generate_whisper()

        if audio_bytes:
            st.audio(audio_bytes, format="audio/wav", autoplay=True)
            st.info("The spirit is whispering...")
        else:
            st.error(
                "The line went dead. Check the **Manage App → Logs** panel for "
                "[ERROR] or [FFMPEG ERROR] lines."
            )

if st.button("🔌 Hang Up", use_container_width=True):
    st.rerun()
