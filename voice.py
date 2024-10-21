import speech_recognition as sr
import threading
import time
import pyttsx3
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.layout import Layout
from rich.live import Live
from rich.spinner import Spinner

try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

class LiveSpeechRecognition:
    def __init__(self, trigger_word="Hey"):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = False
        self.thread = None
        self.console = Console()
        self.groq_client = None
        self.layout = Layout()
        self.trigger_word = trigger_word.lower()  # Set the trigger word
        self.tts_engine = pyttsx3.init()  # Initialize TTS engine
        self.initialize_layout()
        self.initialize_ai_client()

    def initialize_layout(self):
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main", ratio=1),
            Layout(name="footer", size=3)
        )
        self.layout["main"].split_row(
            Layout(name="input", ratio=1),
            Layout(name="output", ratio=1)
        )

    def initialize_ai_client(self):
        if GROQ_AVAILABLE:
            try:
                api_key = "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"
                if not api_key:
                    raise ValueError("GROQ_API_KEY environment variable not set.")
                self.groq_client = Groq(api_key=api_key)
                self.console.print("Groq client initialized successfully.", style="bold green")
            except Exception as e:
                self.console.print(f"Error initializing Groq client: {e}", style="bold red")
                self.console.print("Falling back to echo mode. Please set the GROQ_API_KEY environment variable to enable AI features.", style="yellow")
        else:
            self.console.print("Groq library not available. Running in echo mode.", style="yellow")

    def start_listening(self):
        self.is_listening = True
        self.thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.thread.start()

    def stop_listening(self):
        self.is_listening = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)
        self.console.print("Stopped listening.", style="bold green")

    def _listen_loop(self):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
        
        with Live(self.layout, refresh_per_second=4) as live:
            while self.is_listening:
                try:
                    self.layout["footer"].update(Panel("Listening...", style="bold blue"))
                    with self.microphone as source:
                        audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)
                    
                    try:
                        text = self.recognizer.recognize_google(audio)
                        self.process_input(text, live)  # Call process_input without stopping
                    except sr.UnknownValueError:
                        self.layout["footer"].update(Panel("Could not understand audio", style="yellow"))
                    except sr.RequestError as e:
                        self.layout["footer"].update(Panel(f"Could not request results; {e}", style="red"))
                
                except sr.WaitTimeoutError:
                    self.layout["footer"].update(Panel("Listening timed out, continuing...", style="yellow"))
                
                time.sleep(0.1)  # Small delay to prevent excessive CPU usage

    def process_input(self, user_input, live):
        user_input_lower = user_input.lower()
        if self.trigger_word in user_input_lower:
            # Process AI response in a separate thread to avoid blocking
            threading.Thread(target=self.process_with_ai, args=(user_input, live), daemon=True).start()
        elif "stop listening" in user_input_lower:
                threading.Thread(target=self.echo_response, args=(user_input,), daemon=True).start()
        else:
            # Process echo response in a separate thread to avoid blocking
            threading.Thread(target=self.echo_response, args=(user_input,), daemon=True).start()

    def process_with_ai(self, user_input, live):
        self.layout["footer"].update(Panel("Processing with AI...", style="bold cyan"))
        try:
            spinner = Spinner("dots")
            self.layout["output"].update(Panel(spinner, title="AI Response"))
            
            completion = self.groq_client.chat.completions.create(
                model="mixtral-8x7b-32768",
                messages=[{"role": "user", "content": user_input}],
                temperature=0.7,
                max_tokens=1024,
                top_p=1,
                stream=False,
            )

            ai_response = completion.choices[0].message.content
            self.layout["output"].update(Panel(Text(ai_response, style="cyan"), title="AI Response"))
            self.speak_text(ai_response)  # Use TTS to speak AI response

        except Exception as e:
            self.layout["footer"].update(Panel(f"Error processing with AI: {e}", style="bold red"))
           

        self.continue_listening()  # Ensure it goes back to listening

    def echo_response(self, user_input):
        self.layout["output"].update(Panel(Text(f"Echo: {user_input}", style="cyan"), title="Echo Response"))
        self.speak_text(user_input)  # Use TTS to speak echoed input
        self.continue_listening()  # Ensure it goes back to listening

    def continue_listening(self):
        """Make the system return to the listening loop after processing."""
        self.layout["footer"].update(Panel("Returning to listening mode...", style="bold blue"))
        time.sleep(1)  # Optional small delay to indicate the transition

    def speak_text(self, text):
        """Convert text to speech using TTS engine."""
        # Run TTS in a separate thread to avoid blocking
        threading.Thread(target=self._run_tts, args=(text,), daemon=True).start()

    def _run_tts(self, text):
        """Internal method to handle TTS separately in a thread."""
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

if __name__ == "__main__":
    console = Console()
    console.print(Panel.fit("Speech Recognition AI Conversation System", style="bold green"))
    
    speech_recognition = LiveSpeechRecognition()
    speech_recognition.start_listening()
    
    console.print("System is running. Speak into your microphone. Press Ctrl+C to exit.", style="bold yellow")

    try:
        while True:
            time.sleep(0.1)
    except KeyboardInterrupt:
        console.print("\nStopping the system...", style="bold red")
        speech_recognition.stop_listening()
        console.print("System stopped. Goodbye!", style="bold green")
