import threading
import re
import requests
import speech_recognition as sr
import pyttsx3
import json


# CONFIGURATION

PERPLEXITY_API_KEY = "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"  
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
MODEL_NAME = "sonar-pro"  # Adjust model if needed


# SPEAKING & INTERRUPT SUPPORT

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

# GENERAL LISTEN FUNCTION

def listen():
    """
    Standard listening - recognizes the next phrase and returns it.
    Only returns after a phrase is recognized (does not interrupt for specific commands).
    """
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening...")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text.strip()
        except sr.UnknownValueError:
            speak_in_thread("Sorry, say it again.")
            return ""
        except sr.RequestError:
            speak_in_thread("Sorry, I am having trouble connecting to the speech service.")
            return ""

# INTERRUPT LISTEN FUNCTION

def listen_with_specific_interrupt(interrupt_keywords=None):
    """
    Continuously listens for interrupt keywords.
    Returns True only when a valid interrupt word is recognized.
    All other input (including silence/noise/other words) is ignored.
    """
    if interrupt_keywords is None:
        interrupt_keywords = ["interrupt", "cancel", "pause", "wait", "shut up"]
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        print(f"Listening for interrupt words:")
        while True:
            audio = recognizer.listen(source)
            try:
                text = recognizer.recognize_google(audio).lower().strip()
                print(f"interrupt listener: {text}")
                if any(kw in text for kw in interrupt_keywords):
                    print("Interrupt keyword detected!")
                    return True
            except sr.UnknownValueError:
                continue  # Ignore unrecognized sounds (noise/silence)
            except sr.RequestError:
                print("Speech service unavailable for interruption check.")
                break
        return False


# PERPLEXITY API QUERY FUNCTION

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

# TTS CLEANING FUNCTION

def clean_text(text):
    """
    Remove special characters and citation markers for TTS compatibility.
    """
    text = re.sub(r'[\*\#\_\`\\]', '', text)          # Remove markdown
    text = re.sub(r'\[\d+\]', '', text)               # Remove citations like [1], 
    return text.strip()


# INTERRUPT WATCHER THREAD

def interrupt_watcher():
    if listen_with_specific_interrupt():
        stop_speaking()

# MAIN LOGIC

def main():
    global speak_thread

    speak_in_thread("Hello! I am Lixus AI assistant. How can I help you today?")
    while True:
        # Listen for user input (regular, not interrupt)
        user_input = listen()
        if not user_input:
            continue

        lower_input = user_input.lower()
        if lower_input in ["exit", "quit", "bye", "goodbye", "stop", "stop responding"]:
            stop_speaking()
            speak_in_thread("Goodbye! Have a great day.")
            if speak_thread:
                speak_thread.join()
            break

        if lower_input in ["thanks", "thank you", "thank", "thank's"]:
            speak_in_thread("You're welcome! I am happy you got help.")
            continue

        # Start TTS, with interrupt monitor running background
        stop_speaking()  # Ensure any ongoing TTS ends
        answer = query_perplexity(user_input)
        speakable_answer = clean_text(answer)

        # Start TTS and interrupt watcher in parallel
        tts_thread = threading.Thread(target=speak, args=(speakable_answer,))
        interrupt_thread = threading.Thread(target=interrupt_watcher)
        tts_thread.start()
        interrupt_thread.start()
        tts_thread.join()
        # Optionally, you can join interrupt_thread or just let it finish on its own

if __name__ == "__main__":
    main()
