import tkinter as tk
from tkinter import ttk
import threading
import app  # Ensure app.py and gui.py are in the same directory

class ISLTranslatorApp:
    def _init_(self, root):
        self.root = root
        self.root.title("Speech-to-ISL Translator")
        self.root.geometry("400x250")
        self.root.resizable(False, False)

        self.lang_code = tk.StringVar(value="en-IN")
        self.stop_flag = {"stop": False}
        self.listener_thread = None

        self.build_gui()

    def build_gui(self):
        ttk.Label(self.root, text="Select Language:", font=("Segoe UI", 12)).pack(pady=10)

        language_choices = {
            "English": "en-IN",
            "Hindi": "hi-IN",
            "Tamil": "ta-IN",
            "Telugu": "te-IN"
        }

        self.combo = ttk.Combobox(
            self.root, values=list(language_choices.keys()), state="readonly", font=("Segoe UI", 10)
        )
        self.combo.current(0)
        self.combo.pack(pady=5)

        def on_lang_change(event):
            selected = self.combo.get()
            self.lang_code.set(language_choices[selected])
        self.combo.bind("<<ComboboxSelected>>", on_lang_change)

        self.start_btn = ttk.Button(self.root, text="🎙 Start Listening", command=self.start_listening)
        self.start_btn.pack(pady=15)

        self.stop_btn = ttk.Button(self.root, text="⏹ Stop", command=self.stop_listening, state="disabled")
        self.stop_btn.pack(pady=5)

        self.status_label = ttk.Label(self.root, text="", font=("Segoe UI", 10))
        self.status_label.pack(pady=10)

    def start_listening(self):
        if not self.listener_thread or not self.listener_thread.is_alive():
            self.stop_flag = {"stop": False}
            self.listener_thread = threading.Thread(
                target=app.continuous_listen,
                args=(self.lang_code.get(), self.stop_flag),
                daemon=True
            )
            self.listener_thread.start()
            self.status_label.config(text="🟢 Listening...", foreground="green")
            self.start_btn.config(state="disabled")
            self.stop_btn.config(state="normal")

    def stop_listening(self):
        self.stop_flag["stop"] = True
        self.status_label.config(text="🛑 Stopped.", foreground="red")
        self.start_btn.config(state="normal")
        self.stop_btn.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app_gui = ISLTranslatorApp()
    root.mainloop()