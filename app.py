import streamlit as st
import os
import threading
from expert1 import prepare_next_daydream, STAGED_PLAYBACK_FILE, NEXT_TEMP_FILE

st.set_page_config(page_title="Alternative Topographies", page_icon="☎️")

st.title("Alternative Topographies")
st.caption("A multi-sensory installation by Jeremy Starn")

# Initialize session state to track if we are ready
if 'ready' not in st.session_state:
    st.session_state.ready = os.path.exists(STAGED_PLAYBACK_FILE)

# UI Layout
st.write("---")
if st.button("📞 Pick Up Receiver", use_container_width=True):
    if os.path.exists(STAGED_PLAYBACK_FILE):
        with open(STAGED_PLAYBACK_FILE, 'rb') as f:
            st.audio(f.read(), format="audio/wav", autoplay=True)
        
        st.info("The spirit is whispering...")
        
        # Prepare the next file in the background while user listens
        thread = threading.Thread(target=prepare_next_daydream)
        thread.start()
    else:
        st.warning("The line is quiet. Generating the first whisper...")
        prepare_next_daydream()
        st.rerun()

if st.button("🔌 Hang Up", use_container_width=True):
    if os.path.exists(NEXT_TEMP_FILE):
        # Swap the files just like the run_installation loop
        os.replace(STAGED_PLAYBACK_FILE, f"archive_{os.path.basename(STAGED_PLAYBACK_FILE)}")
        os.rename(NEXT_TEMP_FILE, STAGED_PLAYBACK_FILE)
        st.success("Line disconnected. Next whisper staged.")
    else:
        st.write("Nothing to hang up yet.")

st.write("---")
st.sidebar.header("Installation Status")
st.sidebar.write(f"Staged file: {'✅ Ready' if st.session_state.ready else '❌ Missing'}")