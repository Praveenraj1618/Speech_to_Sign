import speech_recognition as sr
# from googletrans import Translator
from deep_translator import GoogleTranslator
import keyboard
import threading
import spacy
import re

# Load spaCy English model
try:
    nlp = spacy.load("en_core_web_sm")
except:
    print("⚠ Please run: python -m spacy download en_core_web_sm")
    exit()

# Initialize recognizer and translator
recognizer = sr.Recognizer()
# translator = Translator()

# Supported language codes
language_map = {
    "english": "en-IN",
    "tamil": "ta-IN",
    "telugu": "te-IN",
    "hindi": "hi-IN"
}

def get_language():
    print("Available: English / Tamil / Telugu / Hindi")
    lang = input("🗣 Speak in: ").strip().lower()
    return language_map.get(lang, "en-IN")

def preprocess(text):
    text = re.sub(r'[^\w\s]', '', text.lower())
    return text

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

def continuous_listen(lang_code, stop_flag):
    full_transcript = []

    print("\n🎤 Listening... Press Enter to stop.\n")
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        while not stop_flag["stop"]:
            try:
                audio = recognizer.listen(source, timeout=1, phrase_time_limit=3)
                recognized = recognizer.recognize_google(audio, language=lang_code)
                print("🗣 Recognized:", recognized)

                # src = lang_code.split('-')[0]
                # translated = translator.translate(recognized, src=src, dest="en")
                translated_text = GoogleTranslator(source='auto', target='en').translate(recognized)
                print("🌐 Translated:", translated_text)

                processed = preprocess(translated_text)
                gloss = isl_gloss_spacy(processed)
                full_transcript.append(translated_text)

                print("📝 ISL Gloss:", gloss)

            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                print("⚠ Couldn’t understand...")
            except sr.RequestError as e:
                print(f"⚠ API Error: {e}")
            except Exception as e:
                print(f"💥 Unexpected error: {e}")

    final_text = ' '.join(full_transcript)
    final_gloss = isl_gloss_spacy(preprocess(final_text))
    print("\n📄 Final Transcript:", final_text)
    print("📝 Final ISL Gloss:", final_gloss)

if __name__ == "__main__":
    lang_code = get_language()
    stop_flag = {"stop": False}

    threading.Thread(target=lambda: keyboard.wait("enter") or stop_flag.update({"stop": True}), daemon=True).start()
    continuous_listen(lang_code, stop_flag)
