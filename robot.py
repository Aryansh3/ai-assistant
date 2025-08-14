


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
engine = pyttsx3.init()
engine.setProperty('rate', 160)    # Slightly faster speech rate
engine.setProperty('volume', 1.0)  # Maximum volume

def speak(text):
    """Speak the given text out loud and print it."""
    print(f"Alexa says: {text}")
    engine.say(text)
    engine.runAndWait()
#hello
# ======================
# SPEECH RECOGNITION SETUP
# ======================
def listen():
    """Listen from the microphone and convert speech to text."""
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening... Please speak now.")
        recognizer.adjust_for_ambient_noise(source, duration=0.5)
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

# ======================
# MAIN FUNCTION
# ======================
def main():
    speak("Hello! I am your Alexa-style AI assistant. How can I help you today?")
    while True:
        user_input = listen()
        if not user_input:
            continue
        if user_input.lower() in ["exit", "stop", "quit", "bye", "goodbye"]:
            speak("Goodbye! Have a great day.")
            break

        answer = query_perplexity(user_input)
        speak(answer)

if __name__ == "__main__":
    main()
