# Speech to Sign Language (ISL) Converter

A Python application that converts spoken language into Indian Sign Language (ISL) gloss and plays corresponding sign language videos. This project helps bridge the communication gap by visualizing speech as sign language.

## Features

- **Multi-Language Support**: Supports speech input in **English, Tamil, Telugu, and Hindi**.
- **Speech-to-Text**: Utilizes Google Speech Recognition to convert spoken words into text.
- **Translation**: Translates the recognized text into English (if spoken in other languages).
- **ISL Gloss Generation**: Uses spaCy (NLP) to convert English text into ISL gloss (subject-object-verb structure, removing unnecessary words).
- **Video Playback**: Plays ISL videos corresponding to the generated gloss.
    - **Word-level**: Matches full words if videos exist.
    - **Letter-level (Finger Spelling)**: Falls back to spelling out words letter-by-letter if the full word video is missing.
- **UI**: Modern, dark-mode web interface built with **Streamlit** (Recommended) and a legacy Tkinter desktop app.

## Prerequisites

- Python 3.x
- Microphone
- Internet connection (for Google Speech and Translation APIs)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/Praveenraj1618/Speech_to_Sign.git
    cd Speech_to_Sign
    ```

2.  **Install dependencies:**
    ```bash
    pip install -r requirement.txt
    ```

3.  **Download spaCy English model:**
    ```bash
    python -m spacy download en_core_web_sm
    ```

4.  **Dataset Setup:**
    Ensure you have a `datasets` directory in the project root with the following structure:
    ```
    datasets/
    ├── full_word_videos/   # Contains videos for whole words (e.g., "hello.mp4")
    └── letters/            # Contains videos for alphabets (e.g., "a.mp4", "b.mp4")
    ```

## Usage

### Main Application (Streamlit Web UI) - **Recommended**
Run the modern web interface:
```bash
streamlit run streamlit_app.py
```
1. The app will open in your default browser.
2. Select your language from the sidebar.
3. Click **Start Listening**.
4. Speak into your microphone.

### Legacy Desktop App (Tkinter)
Run the classic desktop window:
```bash
python app.py
```

### Console Version
For a command-line interface:
```bash
python sst.py
```
Follow the on-screen prompts to select a language and speak.

## Project Structure

- `streamlit_app.py`: **Modern Web App**. The recommended entry point with a refined UI.
- `app.py`: Legacy desktop application with Tkinter GUI.
- `sst.py`: Console-based script for speech-to-sign conversion.
- `gui.py`: Alternative/Legacy GUI implementation.
- `datasets/`: Directory containing the video dataset for ISL.

## Dependencies

- `SpeechRecognition`: For converting speech to text.
- `SpeechRecognition`: For converting speech to text.
- `deep-translator`: For translating text to English.
- `spacy`: For Natural Language Processing to generate ISL gloss.
- `opencv-python` (cv2): For video playback.
- `pillow`: For image handling in GUI.
- `pillow`: For image handling in GUI.
- `streamlit`: For the modern web interface.
- `tkinter`: For the legacy desktop GUI.
