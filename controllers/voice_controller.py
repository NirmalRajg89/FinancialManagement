# import streamlit as st
# import speech_recognition as sr
# import pyttsx3
# import threading
# import time
# import uuid
# import tempfile
# import os
# from streamlit.components.v1 import html as st_html


# # ---------------------- VOICE UTILS ---------------------- #

# # Initialize text-to-speech engine
# #engine = pyttsx3.init()
# engine = pyttsx3.init()

# def speak_text(text):
#     """Speak assistant response using TTS"""
#     #engine.say(text)
#     #engine.runAndWait()
#     """Speak the given text using text-to-speech with human-like settings"""
#     try:
#         # Set voice properties for more human-like speech
#         engine.setProperty('rate', 190)  # Faster, more natural speed
#         engine.setProperty('volume', 0.9)  # Slightly louder for clarity
#         engine.setProperty('pitch', 0.1)  # Slightly higher pitch for warmth
        
#         # Get available voices and select the most human-like one
#         voices = engine.getProperty('voices')
#         if voices:
#             # Prioritize voices that sound more human
#             preferred_voices = ['samantha', 'alex', 'victoria', 'daniel', 'zira', 'female']
#             for preferred in preferred_voices:
#                 for voice in voices:
#                     if preferred in voice.name.lower():
#                         engine.setProperty('voice', voice.id)
#                         break
#                 else:
#                     continue
#                 break
        
#         # Add natural pauses and emphasis
#         text = text.replace('.', '. ')  # Add slight pause after periods
#         text = text.replace('!', '! ')  # Add slight pause after exclamations
#         text = text.replace('?', '? ')  # Add slight pause after questions
        
#         engine.say(text)
#         engine.runAndWait()
#     except Exception as e:
#         st.error(f"Error with text-to-speech: {str(e)}")

# def speak_text_async(text, delay=0):
#     """Speak text asynchronously without blocking the UI"""
#     # Check if voice is muted in session state
#     if st.session_state.get("tts_muted", False):
#         print("🔇 Voice is muted, skipping speech")
#         return
        
#     def speak():
#         try:
#             if delay > 0:
#                 time.sleep(delay)
#             print(f"🔊 Starting to speak: {text[:50]}...")
#             speak_text(text)
#             print("✅ Speech completed")
#         except Exception as e:
#             print(f"❌ Speech error: {e}")
    
#     thread = threading.Thread(target=speak)
#     thread.daemon = True
#     thread.start()

# def speak_welcome_message(user_name):
#     """Speak a conversational welcome message when user enters their name"""
#     welcome_text = f"Hi {user_name}! Great to meet you. I'm going to analyze your financial situation and help you with investment recommendations."
#     speak_text_async(welcome_text)
#     return welcome_text

# def speak_risk_tolerance_summary(risk_tolerance, credit_score, dti_ratio, savings_condition):
#     """Generate and speak a conversational summary about risk tolerance"""
#     # Create a conversational summary based on risk tolerance
#     if risk_tolerance == "High":
#         summary = f"Based on your financial profile, you have a high risk tolerance. This means you're in a great position to consider growth investments like stocks and real estate. Your strong financial foundation allows you to take on more risk for potentially higher returns."
#     elif risk_tolerance == "Moderate":
#         summary = f"Looking at your financial situation, you have a moderate risk tolerance. This suggests a balanced approach would work best for you. I'd recommend a mix of growth and conservative investments to build wealth steadily while managing risk."
#     else:  # Low
#         summary = f"After analyzing your profile, you have a low risk tolerance. This is perfectly fine! I'd suggest focusing on conservative investments like bonds and high-yield savings accounts. Let's build a solid foundation first before considering riskier options."
    
#     # Add a delay so it flows naturally after the welcome message
#     speak_text_async(summary, delay=3)
#     return summary

# def speak_investment_summary(plan_type, goals, risk_tolerance, monthly_contribution, goal_amount, tenure):
#     """Generate and speak a short, crisp summary about the investment plan"""
#     goals_text = ", ".join(goals) if isinstance(goals, list) else str(goals)
    
#     # Format currency as whole dollars (no decimals) with thousand separators
#     def to_int(val):
#         try:
#             return int(round(float(val)))
#         except Exception:
#             return val
#     mc_int = to_int(monthly_contribution)
#     ga_int = to_int(goal_amount)
#     mc_str = f"{mc_int:,}" if isinstance(mc_int, int) else str(monthly_contribution)
#     ga_str = f"{ga_int:,}" if isinstance(ga_int, int) else str(goal_amount)
#     unit = "month" if plan_type == "Short-term" else "year"
#     tenure_int = to_int(tenure)
#     tenure_str = str(tenure_int) if isinstance(tenure_int, int) else str(tenure)

#     summary = (
#         f"Plan ready! Invest ${mc_str} monthly for ${ga_str} goal over {tenure_str} {unit}{'' if tenure_str == '1' else 's'}. "
#         f"Portfolio includes equity funds, bonds, and gold for balanced growth."
#     )    
#     speak_text_async(summary)
#     return summary

# def speak_investment_analysis_summary(investment_table_text):
#     """Speak a summary of the investment analysis table."""
#     try:
#         lines = investment_table_text.strip().split('\n')
#         options_found = []
        
#         for line in lines:
#             if '|' in line and not line.startswith('|') and not line.startswith('-'):
#                 parts = [part.strip() for part in line.split('|')]
#                 if len(parts) >= 6:
#                     option = parts[1]
#                     monthly_contrib = parts[4]
#                     if option and monthly_contrib:
#                         options_found.append(f"{option}: {monthly_contrib}")
        
#         if options_found:
#             summary = f"Investment analysis shows {len(options_found)} options. Top recommendations include {', '.join(options_found[:2])}."
#         else:
#             summary = "Investment analysis complete with diversified portfolio options."
        
#         speak_text_async(summary)
#         return summary
#     except Exception as e:
#         print(f"❌ Voice error: {e}")
#         fallback_summary = "Investment analysis complete with portfolio recommendations."
#         speak_text_async(fallback_summary)
#         return fallback_summary

# def render_global_stop_button():
#     """Stop all TTS audio on page."""
#     btn_id = f"stop_{uuid.uuid4().hex}"
#     html_code = f"""
#     <div style="position:fixed; top:8px; right:60px; z-index:9999;">
#       <button id="{btn_id}" title="Stop all audio"
#         style="background:#e74c3c; border:none; color:white; cursor:pointer; width:30px; height:30px;
#                border-radius:6px; display:flex; align-items:center; justify-content:center;
#                box-shadow:0 2px 8px rgba(0,0,0,0.2);">
#         <svg width="16" height="16" viewBox="0 0 24 24" fill="white">
#           <rect x="6" y="6" width="12" height="12" rx="2"></rect>
#         </svg>
#       </button>
#     </div>
#     <script>
#       setTimeout(() => {{
#         const btn = document.getElementById("{btn_id}");
#         if(!btn) return;
#         btn.addEventListener('click', () => {{
#           try {{
#             const audios = Array.from(document.querySelectorAll('audio.tts-audio'));
#             audios.forEach(a => {{
#               a.pause();
#               a.currentTime = 0;
#               a.src = '';
#               a.load();
#               a.remove();
#             }});
#           }} catch(e){{ console.error(e); }}
#         }});
#       }}, 500);
#     </script>
#     """
#     st_html(html_code, height=40)

# def transcribe_audio():
#     """Transcribe user's voice input"""
#     recognizer = sr.Recognizer()
#     with sr.Microphone() as source:
#         st.info("🎙️ Listening... Please speak.")
#         try:
#             audio = recognizer.listen(source, timeout=5)
#             text = recognizer.recognize_google(audio)
#             st.success(f"🗣️ You said: {text}")
#             return text
#         except sr.WaitTimeoutError:
#             st.error("⏱️ Timeout. Please try again.")
#         except sr.UnknownValueError:
#             st.error("❌ Could not understand audio.")
#         except sr.RequestError:
#             st.error("⚠️ Could not reach speech service.")
#         return ""


import asyncio
import edge_tts
import streamlit as st
import base64

async def _speak_async(text, filename="output.mp3", voice="en-US-JennyNeural"):
    """Generate speech using edge-tts and save as MP3."""
    communicate = edge_tts.Communicate(text, voice=voice)
    await communicate.save(filename)

def speak_text(text, filename="output.mp3", voice="en-US-JennyNeural"):
    """Synchronous wrapper for Streamlit usage."""
    if st.session_state.get("mute_audio", False):
        return
    asyncio.run(_speak_async(text, filename, voice))
    
    # Play audio automatically without controls
    with open(filename, "rb") as f:
        audio_bytes = f.read()
    b64_audio = base64.b64encode(audio_bytes).decode()
    audio_html = f"""
    <audio autoplay hidden>
        <source src="data:audio/mp3;base64,{b64_audio}" type="audio/mp3">
    </audio>
    """
    st.components.v1.html(audio_html, height=0)

def speak_welcome_message(user_name):
    speak_text(f"Welcome {user_name}! Let's check your financial dashboard.")

def speak_investment_summary(plan_type, goals, risk_tolerance, monthly_contribution, goal_amount, tenure):
    """Generate and speak a conversational summary about the investment plan."""

    # Convert goals to a string if it's a list
    goals_text = ", ".join(goals) if isinstance(goals, list) else str(goals)

    # Helper to convert values to integers safely
    def to_int(val):
        try:
            return int(round(float(val)))
        except Exception:
            return val

    # Format monetary values
    mc_int = to_int(monthly_contribution)
    ga_int = to_int(goal_amount)
    mc_str = f"{mc_int:,}" if isinstance(mc_int, int) else str(monthly_contribution)
    ga_str = f"{ga_int:,}" if isinstance(ga_int, int) else str(goal_amount)

    # Determine tenure unit
    unit = "month" if plan_type == "Short-term" else "year"
    tenure_int = to_int(tenure)
    tenure_str = str(tenure_int) if isinstance(tenure_int, int) else str(tenure)

    # Construct summary text
    summary = (
        f"Perfect! I've created your personalized {plan_type.lower()} investment plan. "
        f"You'll be investing ${mc_str} each month to reach your goal of ${ga_str} "
        f"over {tenure_str} {unit}{'' if tenure_str == '1' else 's'}. "
        f"By diversifying across Equity Mutual Funds, Index Funds, and Public Provident Fund, "
        f"with optional allocations to Gold and Real Estate, your plan balances growth, safety, and hedging. "
        f"This strategy gives you a feasible path to achieve your financial goals."
    )

    # Speak the summary asynchronously
    speak_text(summary)
