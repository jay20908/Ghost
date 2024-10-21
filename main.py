import os
import subprocess
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from groq import Groq
import sorter
import re
 

# Load environment variables from .env file
load_dotenv()

# Get the API key from environment variables
api_key = os.getenv('GROQ_API_KEY')

# Initialize Groq client with the API key
client = Groq(api_key=api_key)

# Example function to execute terminal commands
def execute_terminal_command(command):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout if result.returncode == 0 else result.stderr
    except Exception as e:
        return f"Error executing command: {str(e)}"

# Example function to interact with the weather API
def get_weather(api_key, location):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return f"Error fetching weather: {response.status_code}"


def sort_files():
    other_files = sorter.scan_and_organize_downloads()
    print(f"sorted files in downloads folder")






# URL detection regex pattern
url_pattern = re.compile(r'https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)')

# AI function to generate a response
def ai_generate_response(message):
    completion = client.chat.completions.create(
        model="llama-3.2-90b-text-preview",
        messages=[
            {
                "role": "user",
                "content": message
            }
        ],
        temperature=1,
        max_tokens=1024,
        top_p=1,
        stream=True,
        stop=None,
    )

    response = ""
    for chunk in completion:
        response += chunk.choices[0].delta.content or ""
    return response

# Main function that interprets user input and executes the corresponding command
def main():
    while True:
        user_input = input("Enter your command: ")

        if user_input.lower() == "exit":
            break

        if url_pattern.search(user_input):
            url = url_pattern.search(user_input).group()
            print(f"Detected URL: {url}")
 

        elif "weather" in user_input:
            location = "London"  # You can dynamically fetch location
            weather_data = get_weather(os.getenv('WEATHER_API_KEY'), location)
            print(f"Weather in {location}: {weather_data}")

        elif "run command" in user_input:
            command = "ls"  # Example command
            terminal_output = execute_terminal_command(command)
            print(f"Command output: {terminal_output}")

            
        elif "sort" in user_input:
            sort_files()
        


        else:
            response = ai_generate_response(user_input)
            print(f"AI response: {response}")

# Run the main function
if __name__ == "__main__":
    main()
