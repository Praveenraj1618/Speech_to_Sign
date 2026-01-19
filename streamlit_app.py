# import streamlit as st
import streamlit as st
import speech_recognition as sr
from deep_translator import GoogleTranslator
import spacy
import re
import os
import cv2
import time
from PIL import Image

# --- Page Config ---
st.set_page_config(
    page_title="Speech to ISL Converter",
    page_icon="🤟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS ---
st.markdown("""
<style>
    /* Main Background and Text */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* Title Styling */
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(90deg, #4ef0e9 0%, #a25dc9 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Card Container Styling */
    .css-1r6slb0, .css-12oz5g7 { 
        padding: 1.5rem;
        border-radius: 12px;
        background-color: #1A1C24;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    
    /* Live Status Badge */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 999px;
        font-size: 0.875rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .status-listening {
        background-color: rgba(74, 222, 128, 0.2);
        color: #4ade80;
        border: 1px solid #4ade80;
        animation: pulse 2s infinite;
    }
    .status-idle {
        background-color: rgba(148, 163, 184, 0.2);
        color: #94a3b8;
        border: 1px solid #475569;
    }
    
    @keyframes pulse {
        0% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0.4); }
        70% { box-shadow: 0 0 0 10px rgba(74, 222, 128, 0); }
        100% { box-shadow: 0 0 0 0 rgba(74, 222, 128, 0); }
    }
    
    /* Chat/Result Bubble Styling */
    .chat-bubble {
        padding: 1rem;
        border-radius: 12px;
        margin-bottom: 15px;
        max-width: 90%;
    }
    .user-bubble {
        background-color: #2E3346;
        border-left: 4px solid #6366F1;
        margin-right: auto;
    }
    .bot-bubble {
        background-color: #1F2937;
        border-left: 4px solid #10B981;
        margin-right: auto;
    }
    .gloss-box {
        background-color: #111827;
        font-family: 'Courier New', monospace;
        padding: 1rem;
        border: 1px dashed #4B5563;
        border-radius: 8px;
        margin-top: 10px;
        color: #E5E7EB;
    }
    
    /* Instructions List */
    .instruction-step {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;
        padding: 8px;
        border-radius: 6px;
        background: rgba(255,255,255,0.05);
    }
    .step-num {
        background: #6366F1;
        color: white;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        border-radius: 50%;
        font-weight: bold;
        font-size: 12px;
    }

</style>
""", unsafe_allow_html=True)

# --- Load Resources (Cached) ---
@st.cache_resource
def load_spacy_model():
    try:
        return spacy.load("en_core_web_sm")
    except OSError:
        os.system("python -m spacy download en_core_web_sm")
        return spacy.load("en_core_web_sm")

nlp = load_spacy_model()
# translator = Translator() # Removed googletrans
recognizer = sr.Recognizer()

# --- Constants & Mappings ---
LANGUAGE_MAP = {
    "English": "en-IN",
    "Tamil": "ta-IN",
    "Telugu": "te-IN",
    "Hindi": "hi-IN"
}

# --- Helper Functions ---
def preprocess(text):
    return re.sub(r'[^\w\s]', '', text.lower())

def isl_gloss_spacy(text):
    doc = nlp(text)
    important_words = []
    tense_marker = ""
    keep_words = {"left", "right", "back", "forward", "up", "down", "near", "on", "in", "under", "to", "from"}

    for token in doc:
        if token.text.lower() in keep_words:
            important_words.append(token.text.lower())
        elif token.pos_ == "AUX" and token.lemma_ == "will":
            tense_marker = "FUTURE"
        elif token.pos_ in {"AUX", "DET", "ADP"}:
            continue
        elif token.tag_ in {"VBD", "VBN"}:
            tense_marker = "PAST"
            important_words.append(token.lemma_)
        else:
            important_words.append(token.lemma_)

    if tense_marker:
        important_words.append(tense_marker)

    return ' '.join(important_words).lower()

def get_video_sequence(gloss_sentence, base_dir='datasets'):
    full_word_dir = os.path.join(base_dir, 'full_word_videos')
    letter_dir = os.path.join(base_dir, 'letters')
    video_sequence = []

    for word in gloss_sentence.lower().split():
        word_video = os.path.join(full_word_dir, f"{word}.mp4")
        if os.path.exists(word_video):
            video_sequence.append(word_video)
        else:
            for letter in word:
                letter_video = os.path.join(letter_dir, f"{letter}.mp4")
                if os.path.exists(letter_video):
                    video_sequence.append(letter_video)
    return video_sequence

def play_video_sequence(video_paths, placeholder):
    if not video_paths:
        placeholder.warning("No matching videos found for the generated gloss.")
        return

    for video_path in video_paths:
        cap = cv2.VideoCapture(video_path)
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            # Convert BGR to RGB
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            placeholder.image(frame, channels="RGB", use_container_width=True)
            time.sleep(0.04) # Adjust speed slightly smoother
        cap.release()

# --- Main App ---
def main():
    # Sidebar
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/2620/2620619.png", width=80) 
        st.markdown("## **Speech2Sign**")
        st.caption("AI-Powered Sign Language Interpreter")
        
        st.markdown("---")
        
        st.markdown("### 🌐 Settings")
        selected_lang = st.selectbox("Speech Language", list(LANGUAGE_MAP.keys()))
        lang_code = LANGUAGE_MAP[selected_lang]
        
        st.markdown("---")
        st.markdown("### 📝 Quick Guide")
        
        guides = [
            "Select your spoken language.",
            "Click **Start Listening**.",
            "Speak clearly into the mic.",
            "Watch the ISL translation!"
        ]
        
        for i, guide in enumerate(guides, 1):
            st.markdown(f'''
            <div class="instruction-step">
                <div class="step-num">{i}</div>
                <div>{guide}</div>
            </div>
            ''', unsafe_allow_html=True)

        st.markdown("---")
        st.caption("v1.0.0 | Built with Streamlit")

    # Main Area
    st.markdown('<div class="main-title">Speech to Indian Sign Language</div>', unsafe_allow_html=True)

    # State management
    if 'listening' not in st.session_state:
        st.session_state.listening = False

    # Control Bar
    col_status, col_controls = st.columns([2, 1])
    
    with col_status:
        status_placeholder = st.empty()
        if st.session_state.listening:
            status_placeholder.markdown('<div class="status-badge status-listening">Listening...</div>', unsafe_allow_html=True)
        else:
            status_placeholder.markdown('<div class="status-badge status-idle">Idle (Ready)</div>', unsafe_allow_html=True)

    with col_controls:
        # Toggle Button Logic
        if st.session_state.listening:
            if st.button("⏹ Stop Listening", type="primary", use_container_width=True):
                st.session_state.listening = False
                st.rerun()
        else:
            if st.button("🎙 Start Listening", type="primary", use_container_width=True):
                st.session_state.listening = True
                st.rerun()

    st.markdown("---")

    # Content Grid
    col_content, col_video = st.columns([1.5, 1], gap="large")

    with col_content:
        st.markdown("### 💬 Conversation")
        
        # Placeholders for dynamic content
        transcript_container = st.empty()
        
        # Initial State Message
        if not st.session_state.listening:
             transcript_container.info("Click 'Start Listening' to begin...")

    with col_video:
        st.markdown("### 🎥 Visual Output")
        video_placeholder = st.empty()
        
        # Default placeholder image or message
        video_placeholder.markdown(
            """
            <div style="background: #1F2937; height: 300px; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #6B7280; border: 2px dashed #374151;">
                Waiting for input...
            </div>
            """, unsafe_allow_html=True
        )

    # Logic Loop
    if st.session_state.listening:
        try:
            with sr.Microphone() as source:
                recognizer.adjust_for_ambient_noise(source)
                
                # Processing loop (Single phrase per loop iteration to allow UI refresh on re-run)
                while st.session_state.listening:
                    try:
                        # Listen
                        audio = recognizer.listen(source, timeout=1, phrase_time_limit=5)
                        
                        # Recognize
                        recognized_text = recognizer.recognize_google(audio, language=lang_code)
                        
                        # Translate
                        src_lang = lang_code.split('-')[0]
                        translated_text = GoogleTranslator(source='auto', target='en').translate(recognized_text)
                        
                        # Gloss
                        processed_text = preprocess(translated_text)
                        gloss_text = isl_gloss_spacy(processed_text)
                        
                        # Update UI with "Chat" bubbles
                        transcript_container.markdown(f"""
                        <div class="chat-bubble user-bubble">
                            <div style="font-size: 0.8rem; color: #A5B4FC; margin-bottom: 4px;">You said ({selected_lang})</div>
                            <div style="font-size: 1.1rem;">"{recognized_text}"</div>
                        </div>
                        <div class="chat-bubble bot-bubble">
                            <div style="font-size: 0.8rem; color: #6EE7B7; margin-bottom: 4px;">Translation & ISL Gloss</div>
                            <div style="font-size: 1rem; margin-bottom: 8px;">{translated_text}</div>
                            <div class="gloss-box">GLOSS: {gloss_text.upper()}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Play Video
                        video_seq = get_video_sequence(gloss_text)
                        play_video_sequence(video_seq, video_placeholder)
                        
                        # Reset Video Placeholder after playing
                        video_placeholder.markdown(
                            """
                            <div style="background: #1F2937; height: 300px; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #6B7280; border: 2px dashed #374151;">
                                Ready for next phrase...
                            </div>
                            """, unsafe_allow_html=True
                        )
                        
                    except sr.WaitTimeoutError:
                        continue 
                    except sr.UnknownValueError:
                        # Optional: Show visual feedback for "Listening..." silence, or ignore
                        pass
                    except sr.RequestError as e:
                        st.error(f"API Error: {e}")
                        st.session_state.listening = False
                        st.rerun()
                        break
                    
                    # Check if button was clicked using session state (not robust in loop, but loop is short)
                    # Ideally, we break loop to check state, but that stops listening.
                    # We rely on Streamlit's "Stop" button triggering a hard rerun.
                    pass

        except Exception as e:
            st.error(f"Microphone Error: {e}")
            st.session_state.listening = False 

if __name__ == "__main__":
    main()
