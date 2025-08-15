

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
# TEXT-TO-SPEECH SETUP
# ======================
'''
engine = pyttsx3.init()
engine.setProperty('rate', 160)    # Slightly faster speech rate
engine.setProperty('volume', 1.0)  # Maximum 
'''

def speak(text):
    """
    Creates a new TTS engine instance and adds a leading pause to prevent clipping.
    """
    # 1. Initialize a new engine instance INSIDE the function
    engine = pyttsx3.init()

    # 2. Set properties for this new instance
    engine.setProperty('rate', 160)
    engine.setProperty('volume', 1.0)
    
    # This creates the string with the needed pause
    text_to_say = f". {text}"

    # 3. Speak and wait
    print(f"Alexa says: {text}")
    
    # Use the MODIFIED variable here
    engine.say(text_to_say) 
    
    engine.runAndWait()
    # 4. The engine instance is automatically discarded when the function ends
#hello
# ======================
# SPEECH RECOGNITION SETUP
# ======================
def listen():
    """Listen from the microphone and convert speech to text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening... Please speak now.")
        recognizer.adjust_for_ambient_noise(source, duration=1)
        audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            print(f"You said: {text}")
            return text.strip()
        except sr.UnknownValueError:
            speak("Sorry, I did not catch that. Please try again.")
            return ""
        except sr.RequestError:
            speak("Sorry, I am having trouble connecting to the speech service.")
            return ""

# ======================
# PERPLEXITY API QUERY FUNCTION
# ======================
def query_perplexity(prompt):
    """Send prompt to Perplexity API, wait for response, return text."""
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
        "stream": False  # Non-streaming for simplicity and clear replies
    }

    try:
        response = requests.post(PERPLEXITY_API_URL, headers=headers, json=data)
        response.raise_for_status()
        result = response.json()
        answer = result["choices"][0]["message"]["content"].strip()
        return answer
    except Exception as e:
        return f"Sorry, there was an error getting the answer: {e}"
    
import re

def clean_text(text):
    """Remove special characters and citation markers for TTS compatibility."""
    # First, remove markdown characters like *, #, _, `
    text = re.sub(r'[\*#_`\\]', '', text)
    
    # Second, remove citation markers like [1], [2], [5], etc.
    text = re.sub(r'\[\d+\]', '', text)
    
    return text.strip()

# ======================
# MAIN FUNCTION
# ======================
def main():
    speak("Hello! I am your Alexa-style AI assistant. How can I help you today?")
    while True:
        user_input = listen()
        if not user_input:
            continue
        if user_input.lower() in ["exit", "stop", "quit", "bye", "goodbye","stop responding"]:
            speak("Goodbye! Have a great day.")
            break

        # Get the original answer from the API
        answer = query_perplexity(user_input)
        
        # Clean the answer before speaking it
        speakable_answer = clean_text(answer)
        
        # Pass the cleaned text to your speak function
        speak(speakable_answer)

if __name__ == "__main__":
    main()



#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