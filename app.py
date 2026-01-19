import os
import cv2
import time
import re
import threading

# import speech_recognition as sr
import speech_recognition as sr
import spacy
# from googletrans import Translator
from deep_translator import GoogleTranslator
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, LabelFrame
from PIL import Image, ImageTk

# Load spaCy English model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("⚠ Please run: python -m spacy download en_core_web_sm")
    exit()

recognizer = sr.Recognizer()
# translator = Translator()

language_map = {
    "English": "en-IN",
    "Tamil": "ta-IN",
    "Telugu": "te-IN",
    "Hindi": "hi-IN"
}

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
            letters_found = []
            for letter in word:
                letter_video = os.path.join(letter_dir, f"{letter}.mp4")
                if os.path.exists(letter_video):
                    letters_found.append(letter_video)
                else:
                    letters_found = []
                    break
            if letters_found:
                video_sequence.extend(letters_found)

    return video_sequence

def play_video_sequence_tk(video_paths, video_label):
    def update_frame(cap, video_label, remaining_paths):
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame)
            imgtk = ImageTk.PhotoImage(image=img)
            video_label.imgtk = imgtk
            video_label.config(image=imgtk)
            delay = int(1000 / cap.get(cv2.CAP_PROP_FPS)) if cap.get(cv2.CAP_PROP_FPS) > 0 else 40
            video_label.after(delay, update_frame, cap, video_label, remaining_paths)
        else:
            cap.release()
            time.sleep(0.2)
            if remaining_paths:
                next_video = remaining_paths[0]
                remaining_paths = remaining_paths[1:]
                cap_next = cv2.VideoCapture(next_video)
                if cap_next.isOpened():
                    update_frame(cap_next, video_label, remaining_paths)
                else:
                    print(f"Error: Could not open {next_video}")
            else:
                print("Video sequence finished.")

    if video_paths:
        first_video = video_paths[0]
        remaining_paths = video_paths[1:]
        cap = cv2.VideoCapture(first_video)
        if cap.isOpened():
            update_frame(cap, video_label, remaining_paths)
        else:
            print(f"Error: Could not open {first_video}")

class ISLApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Speech to ISL Gloss Player")
        self.geometry("800x600")
        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.lang_var = tk.StringVar(value="English")
        self.is_listening = False
        self.listener_thread = None
        self.stop_flag = {"stop": False}
        self.current_gloss = tk.StringVar()
        self.video_playing = False

        self.create_widgets()

    def create_widgets(self):
        # Language selection
        lang_frame = ttk.LabelFrame(self, text="Language")
        lang_frame.pack(pady=10, padx=10, fill="x")
        ttk.Label(lang_frame, text="Select Language:").pack(side="left", padx=5)
        self.lang_combo = ttk.Combobox(lang_frame, textvariable=self.lang_var, values=list(language_map.keys()), state="readonly")
        self.lang_combo.pack(side="left", padx=5, expand=True)

        # Buttons frame
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=5, padx=10, fill="x")
        self.start_btn = ttk.Button(btn_frame, text="Start Listening", command=self.start_listening)
        self.start_btn.pack(side="left", padx=5, expand=True)
        self.stop_btn = ttk.Button(btn_frame, text="Stop Listening", command=self.stop_listening, state=tk.DISABLED)
        self.stop_btn.pack(side="left", padx=5, expand=True)

        # Gloss Display
        gloss_frame = ttk.LabelFrame(self, text="ISL Gloss")
        gloss_frame.pack(pady=10, padx=10, fill="x")
        self.gloss_label = ttk.Label(gloss_frame, textvariable=self.current_gloss, font=("Arial", 14), wraplength=780)
        self.gloss_label.pack(fill="x", padx=5, pady=5)

        # Video Output
        video_frame = ttk.LabelFrame(self, text="ISL Video")
        video_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.video_output = tk.Label(video_frame)
        self.video_output.pack(fill="both", expand=True)

        # Log output
        log_frame = ttk.LabelFrame(self, text="Log")
        log_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.log_box = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, height=8, state=tk.DISABLED)
        self.log_box.pack(fill="both", expand=True)

    def log(self, msg):
        self.log_box.configure(state=tk.NORMAL)
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)
        self.log_box.configure(state=tk.DISABLED)

    def start_listening(self):
        if self.is_listening:
            return
        self.is_listening = True
        self.stop_flag["stop"] = False
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.current_gloss.set("")
        lang_code = language_map.get(self.lang_var.get(), "en-IN")
        self.log(f"🎙 Starting listening in {self.lang_var.get()} ({lang_code})...")

        self.listener_thread = threading.Thread(target=self.continuous_listen, args=(lang_code,), daemon=True)
        self.listener_thread.start()

    def stop_listening(self):
        if not self.is_listening:
            return
        self.stop_flag["stop"] = True
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.log("⏹ Stopped listening.")
        self.is_listening = False

    def continuous_listen(self, lang_code, base_dir='datasets'):
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            while not self.stop_flag["stop"]:
                try:
                    audio = recognizer.listen(source, timeout=1, phrase_time_limit=3)
                    recognized = recognizer.recognize_google(audio, language=lang_code)
                    self.log(f"🗣 Recognized: {recognized}")

                    # src = lang_code.split('-')[0]
                    # translated = translator.translate(recognized, src=src, dest="en")
                    translated_text = GoogleTranslator(source='auto', target='en').translate(recognized)
                    self.log(f"🌐 Translated: {translated_text}")

                    processed = preprocess(translated_text)
                    gloss = isl_gloss_spacy(processed)
                    self.log(f"📝 ISL Gloss: {gloss}")
                    self.current_gloss.set(gloss)

                    sequence = get_video_sequence(gloss, base_dir=base_dir)
                    if sequence and not self.video_playing:
                        self.log(f"▶ Playing video sequence for gloss...")
                        self.video_playing = True
                        # Play video in the Tkinter label using the updated function
                        threading.Thread(target=play_video_sequence_tk, args=(list(sequence), self.video_output), daemon=True).start()
                    elif not sequence:
                        self.log("⚠ No matching videos found for gloss.")

                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    self.log("🤷 Couldn't understand.")
                except sr.RequestError as e:
                    self.log(f"⚠ API error: {e}")
                except Exception as e:
                    self.log(f"💥 Unexpected error: {e}")
                finally:
                    self.video_playing = False

    def on_close(self):
        if self.is_listening:
            if messagebox.askokcancel("Quit", "Listening is active. Stop and quit?"):
                self.stop_flag["stop"] = True
                self.destroy()
        else:
            self.destroy()

if __name__ == "__main__":
    app = ISLApp()
    app.mainloop()