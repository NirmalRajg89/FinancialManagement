import streamlit as st
import speech_recognition as sr
import pyttsx3

# ---------------------- VOICE UTILS ---------------------- #

# Initialize text-to-speech engine
engine = pyttsx3.init()

def speak_text(text):
    """Speak assistant response using TTS"""
    engine.say(text)
    engine.runAndWait()

def transcribe_audio():
    """Transcribe user's voice input"""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎙️ Listening... Please speak.")
        try:
            audio = recognizer.listen(source, timeout=5)
            text = recognizer.recognize_google(audio)
            st.success(f"🗣️ You said: {text}")
            return text
        except sr.WaitTimeoutError:
            st.error("⏱️ Timeout. Please try again.")
        except sr.UnknownValueError:
            st.error("❌ Could not understand audio.")
        except sr.RequestError:
            st.error("⚠️ Could not reach speech service.")
        return ""
