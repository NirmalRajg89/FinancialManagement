import streamlit as st
import speech_recognition as sr
import pyttsx3
import threading
import time


# ---------------------- VOICE UTILS ---------------------- #

# Initialize text-to-speech engine
engine = pyttsx3.init()

def speak_text(text):
    """Speak the given text using text-to-speech with human-like settings"""
    try:
        # Set voice properties for more human-like speech
        engine.setProperty('rate', 180)  # Faster, more natural speed
        engine.setProperty('volume', 0.9)  # Slightly louder for clarity
        engine.setProperty('pitch', 0.1)  # Slightly higher pitch for warmth
        
        # Get available voices and select the most human-like one
        voices = engine.getProperty('voices')
        if voices:
            # Prioritize voices that sound more human
            preferred_voices = ['samantha', 'alex', 'victoria', 'daniel', 'zira', 'female']
            for preferred in preferred_voices:
                for voice in voices:
                    if preferred in voice.name.lower():
                        engine.setProperty('voice', voice.id)
                        break
                else:
                    continue
                break
        
        # Add natural pauses and emphasis
        text = text.replace('.', '. ')  # Add slight pause after periods
        text = text.replace('!', '! ')  # Add slight pause after exclamations
        text = text.replace('?', '? ')  # Add slight pause after questions
        
        engine.say(text)
        engine.runAndWait()
    except Exception as e:
        st.error(f"Error with text-to-speech: {str(e)}")

def speak_text_async(text, delay=0):
    """Speak text asynchronously without blocking the UI"""
    def speak():
        if delay > 0:
            time.sleep(delay)
        speak_text(text)
    
    thread = threading.Thread(target=speak)
    thread.daemon = True
    thread.start()

def speak_welcome_message(user_name):
    """Speak a conversational welcome message when user enters their name"""
    welcome_text = f"Hi {user_name}! Great to meet you. I'm going to analyze your financial situation and help you with investment recommendations. Let me take a look at your profile."
    speak_text_async(welcome_text)
    return welcome_text

def speak_risk_tolerance_summary(risk_tolerance, credit_score, dti_ratio, savings_condition):
    """Generate and speak a conversational summary about risk tolerance"""
    # Create a conversational summary based on risk tolerance
    if risk_tolerance == "High":
        summary = f"Based on your financial profile, you have a high risk tolerance. This means you're in a great position to consider growth investments like stocks and real estate. Your strong financial foundation allows you to take on more risk for potentially higher returns."
    elif risk_tolerance == "Moderate":
        summary = f"Looking at your financial situation, you have a moderate risk tolerance. This suggests a balanced approach would work best for you. I'd recommend a mix of growth and conservative investments to build wealth steadily while managing risk."
    else:  # Low
        summary = f"After analyzing your profile, you have a low risk tolerance. This is perfectly fine! I'd suggest focusing on conservative investments like bonds and high-yield savings accounts. Let's build a solid foundation first before considering riskier options."
    
    # Add a delay so it flows naturally after the welcome message
    speak_text_async(summary, delay=3)
    return summary

def speak_investment_plan_summary(plan_type, goals, risk_tolerance, monthly_contribution, goal_amount, tenure):
    """Generate and speak a conversational summary about the investment plan"""
    # Create a conversational summary of the investment plan
    goals_text = ", ".join(goals) if isinstance(goals, list) else str(goals)
    
    summary = f"Perfect! I've created your personalized {plan_type.lower()} investment plan. You'll be investing ${monthly_contribution} each month to reach your goal of ${goal_amount:,} for {goals_text}. This {tenure} {'month' if plan_type == 'Short-term' else 'year'} timeline with your {risk_tolerance} risk tolerance gives us a great foundation to work with. The strategy I've designed will help you reach your financial goals while staying comfortable with the level of risk."
    
    speak_text_async(summary)
    return summary

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
