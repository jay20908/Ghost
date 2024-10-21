import os
import speech_recognition as sr
from groq import Groq

# Set up the Groq API client
client = Groq(
    api_key=os.environ.get("GROQ_API_KEY"),
)

# Initialize the speech recognition engine
r = sr.Recognizer()

# Define the AI assistant's name
assistant_name = "Echo"

# Define the 5 features:
# 1. Weather
# 2. News
# 3. Jokes
# 4. Wiki search
# 5. Translate

def weather():
    print(f"Getting weather update for {assistant_name}...")

def news():
    print(f"Getting latest news for {assistant_name}...")

def jokes():
    print(f"Telling a joke for {assistant_name}...")

def wiki_search(query):
    print(f"Searching for {query} on Wikipedia for {assistant_name}...")

def translate(text, lang):
    print(f"Translating {text} to {lang} for {assistant_name}...")

# Main loop
while True:
    # Listen for user input
    with sr.Microphone() as source:
        print(f">>> {assistant_name}: What can I help you with today?")
        audio = r.listen(source, phrase_time_limit=5)

    try:
        # Recognize user input
        text = r.recognize_google(audio)  # Removed lang="en-US"
        print(f">>> User: {text}")

        # Parse user input and determine what action to take
        if "weather" in text.lower():
            weather()
        elif "news" in text.lower():
            news()
        elif "joke" in text.lower():
            jokes()
        elif "wiki" in text.lower():
            query = text.split("wiki ")[1]
            wiki_search(query)
        elif "translate" in text.lower():
            parts = text.split("translate ")[1].split(" to ")
            text_to_translate = parts[0].strip()
            lang_to_translate_to = parts[1].strip()
            translate(text_to_translate, lang_to_translate_to)
        else:
            # If none of the above, use Groq to generate a response
            completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "user",
                        "content": text,
                    }
                ],
                model="llama3-8b-8192",
            )
            print(f">>> {assistant_name}: {completion.choices[0].message.content}")

    except sr.UnknownValueError:
        print(f">>> {assistant_name}: Sorry, couldn't understand that. Can you try again?")
    except sr.RequestError as e:
        print(f">>> {assistant_name}: Error recognizing speech: {e}")
