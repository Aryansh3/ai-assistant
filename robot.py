import threading
import re
import requests
import speech_recognition as sr
import pyttsx3
import json

# ======================
# CONFIGURATION
# ======================
PERPLEXITY_API_KEY = "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"  # Replace with your actual Perplexity API key
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
MODEL_NAME = "sonar-pro"  # Adjust model if needed

# ======================
# SPEAKING & INTERRUPT SUPPORT
# ======================
speak_thread = None
speaking_engine = None
stop_speaking_flag = False

def speak(text):
    """
    TTS in a separate thread and supports interruption.
    """
    global speaking_engine, stop_speaking_flag
    speaking_engine = pyttsx3.init()
    speaking_engine.setProperty('rate', 160)
    speaking_engine.setProperty('volume', 1.0)
    text_to_say = f". {text}"  # Leading period to help with TTS clipping
    stop_speaking_flag = False

    def check_stop(name, completed):
        if stop_speaking_flag and speaking_engine is not None:
            speaking_engine.stop()
    speaking_engine.connect('started-word', check_stop)
    print(f"AI says: {text}")
    speaking_engine.say(text_to_say)
    speaking_engine.runAndWait()
    speaking_engine = None

def stop_speaking():
    """
    Safely stop any ongoing speech immediately.
    """
    global stop_speaking_flag, speaking_engine
    stop_speaking_flag = True
    if speaking_engine is not None:
        speaking_engine.stop()

def speak_in_thread(text):
    """
    Start TTS in a background thread, joining previous if running.
    """
    global speak_thread
    if speak_thread and speak_thread.is_alive():
        stop_speaking()
        speak_thread.join()
    speak_thread = threading.Thread(target=speak, args=(text,))
    speak_thread.start()

# ======================
# SPEECH RECOGNITION WITH PROMPT
# ======================
def listen_with_interrupt():
    """
    Listen from microphone and return text, allowing TTS interruption.
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening... Please speak now.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            print(f"Your question: {text}")
            return text.strip()
        except sr.UnknownValueError:
            speak_in_thread("Sorry, say it again.")
            return ""
        except sr.RequestError:
            speak_in_thread("Sorry, I am having trouble connecting to the speech service.")
            return ""

# ======================
# PERPLEXITY API QUERY FUNCTION
# ======================
def query_perplexity(prompt):
    """
    Send prompt to Perplexity API, wait for response, return text.
    """
    headers = {
        "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": "Be a helpful and brief assistant. Keep your answers concise and to the point."},
            {"role": "user", "content": prompt}
        ],
        "stream": False
    }
    try:
        response = requests.post(PERPLEXITY_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        answer = result["choices"][0]["message"]["content"].strip()
        return answer
    except Exception as e:
        return f"Sorry, there was an error getting the answer: {e}"

# ======================
# TTS CLEANING FUNCTION
# ======================
def clean_text(text):
    """
    Remove special characters and citation markers for TTS compatibility.
    """
    text = re.sub(r'[\*\#\_\`\\]', '', text)          # Remove markdown
    text = re.sub(r'\[\d+\]', '', text)               # Remove citations like [1], 
    return text.strip()

# ======================
# MAIN LOGIC
# ======================
def main():
    global speak_thread
    speak_in_thread("Helooo! I am lixus AI assistant. How can I help you today?")
    while True:
        user_input = listen_with_interrupt()
        if not user_input:
            continue

        lower_input = user_input.lower()
        if lower_input in ["exit", "quit", "bye", "goodbye", "stop", "stop responding"]:
            stop_speaking()
            speak_in_thread("Goodbye! Have a great day.")
            if speak_thread:
                speak_thread.join()
            break

        if lower_input in ["interrupt", "cancel", "pause", "wait", "shut up"]:
            stop_speaking()
            speak_in_thread("sorry, I'll wait for your next command.")
            continue

        if lower_input in ["thanks", "thank you", "thank", "thank's"]:
            speak_in_thread("You're welcome! I am happy you got help.")
            continue

        stop_speaking()  # Ensure any ongoing TTS ends
        answer = query_perplexity(user_input)
        speakable_answer = clean_text(answer)
        speak_in_thread(speakable_answer)

if __name__ == "__main__":
    main()
