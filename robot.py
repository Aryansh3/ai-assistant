import re
import requests
import speech_recognition as sr
import pyttsx3
import json
import time
import threading
import keyboard

# ======================
# SHARED RESOURCES for pyttsx3
# ======================
is_speaking = False
engine = pyttsx3.init()
engine.setProperty('rate', 160)
engine.setProperty('volume', 1.0)

# Callback function for when speech finishes
def on_end(name, completed):
    global is_speaking
    is_speaking = False

engine.connect('finished-utterance', on_end)

# ======================
# CONFIGURATION
# ======================
PERPLEXITY_API_KEY = "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"  # Replace with your actual Perplexity API key
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
MODEL_NAME = "sonar-pro"

# ======================
# HELPER FUNCTIONS
# ======================
def animate_listening(stop_event):
    animation_chars = ['|', '/', '-', '\\']
    idx = 0
    while not stop_event.is_set():
        char = animation_chars[idx % len(animation_chars)]
        print(f"Listening... {char}", end="\r")
        idx += 1
        time.sleep(0.1)
    print(" " * 20, end="\r")

def clean_text(text):
    text = re.sub(r'[\*#_`\\]', '', text)
    text = re.sub(r'\[\d+\]', '', text)
    return text.strip()

# ======================
# SPEAK FUNCTIONS (using a consistent, non-blocking method)
# ======================
def speak_uninterruptible(text):
    """
    Speaks a short message using the consistent, non-blocking event loop.
    """
    global is_speaking
    clean_text_full = clean_text(text)
    if not clean_text_full:
        return

    print(f"AI says: {clean_text_full}")
    
    is_speaking = True
    engine.say(clean_text_full)
    engine.startLoop(False)
    while is_speaking:
        engine.iterate()
        time.sleep(0.1)
    engine.endLoop()

def speak(text):
    """
    Speaks a long response that can be interrupted by the 'esc' key.
    Returns True if interrupted, False otherwise.
    """
    global is_speaking
    clean_text_full = clean_text(text)
    if not clean_text_full:
        return False

    print(f"AI says: {clean_text_full}")
    interrupted = False
    
    is_speaking = True
    engine.say(clean_text_full)
    
    engine.startLoop(False)
    
    while is_speaking:
        if keyboard.is_pressed('esc'):
            engine.stop()
            print("\n--- Speech Interrupted by User ---")
            interrupted = True
            is_speaking = False # Manually end the loop
        engine.iterate()
        time.sleep(0.1)

    engine.endLoop()
    
    return interrupted

# ======================
# MAIN LISTEN FUNCTION
# ======================
def listen():
    """Waits for a user command, starting with a verbal cue."""
    speak_uninterruptible("Listening")

    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("\nPreparing to listen...")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
        
        stop_animation_event = threading.Event()
        animation_thread = threading.Thread(target=animate_listening, args=(stop_animation_event,))
        animation_thread.start()

        try:
            audio = recognizer.listen(source)
            stop_animation_event.set()
            animation_thread.join()
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text.strip()
        except (sr.UnknownValueError, sr.RequestError) as e:
            stop_animation_event.set()
            animation_thread.join()
            if isinstance(e, sr.RequestError):
                speak_uninterruptible("Sorry, my speech service is down.")
            return ""

# ======================
# API AND MAIN LOGIC
# ======================
def query_perplexity(prompt):
    headers = {"Authorization": f"Bearer {PERPLEXITY_API_KEY}", "Content-Type": "application/json"}
    data = {"model": MODEL_NAME, "messages": [{"role": "system", "content": "Be a helpful and brief assistant."}, {"role": "user", "content": prompt}]}
    try:
        response = requests.post(PERPLEXITY_API_URL, headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"Sorry, there was an error: {e}"

def main():
    speak_uninterruptible("Hello! I am your AI assistant. Press Escape at any time to interrupt me. How can I help you today?")
    
    while True:
        user_input = listen()
        if not user_input:
            continue
            
        if user_input.lower() in ["exit", "stop", "quit", "bye", "goodbye"]:
            speak_uninterruptible("Goodbye! Have a great day.")
            time.sleep(1)
            break

        answer = query_perplexity(user_input)
        
        was_interrupted = speak(answer)

        if was_interrupted:
            continue

if __name__ == "__main__":
    main()

'''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'''



'''
import RPi.GPIO as GPIO
import time

# --- Setup the GPIO Pin ---
# Use the BCM pin numbering scheme
GPIO.setmode(GPIO.BCM) 
BUTTON_PIN = 17 
# Set up the pin as an input with a pull-up resistor
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP) 
#--------------------------

# In your speak() function, replace the keyboard check with a GPIO check:
while is_speaking:
    # GPIO.input will be 0 (False) when the button is pressed
    if not GPIO.input(BUTTON_PIN): 
        engine.stop()
        print("\n--- Speech Interrupted by Switch ---")
        interrupted = True
        is_speaking = False
    engine.iterate()
    time.sleep(0.1)

# At the end of your script, you'd add a cleanup line:
# GPIO.cleanup()
'''