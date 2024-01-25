import json
import speech_recognition as sr
import pyttsx3
import re
import requests
import sys
# from pydub import AudioSegment
# from pydub.playback import play
import pygame


def load_speech_data():
    with open("speech.json", "r") as file:
        speech_data = json.load(file)
    return speech_data.get("responses", [])


def recognize_speech():
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        print("Say something:")
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source, timeout=20)

    try:
        print("Recognizing...")
        text = recognizer.recognize_google(audio)
        print("You said:", text)
        return text.lower()
    except sr.UnknownValueError:
        play_audio("incorrect_prompt.wav")
        text_to_speech("Sorry, I do not understand your request.")
        return None
    except sr.RequestError as e:
        print(
            f"Could not request results from Google Speech Recognition service; {e}")
        return None


def play_audio(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)


def ask_for_city():
    text_to_speech("What city would you like to know about the weather?")
    city = recognize_speech()
    return city


def extract_city_from_text(text):
    city_match = re.search(r"\b(?:in|for|at|)(?:\s+)?(\w+)\b", text)
    return city_match.group(1) if city_match else None


def get_weather():
    city = ask_for_city()

    # Replace 'your_api_key' with your actual OpenWeatherMap API key
    api_key = 'be3a37d022d011b59dec7faecfc49d42'
    units = 'metric'

    weather_api_url = f'http://api.openweathermap.org/data/2.5/weather?q={
        city}&units={units}&appid={api_key}'

    try:
        response = requests.get(weather_api_url)
        data = response.json()

        if response.status_code == 200:
            temperature = data.get("main", {}).get("temp")
            description = data.get("weather", [{}])[0].get("description")

            if temperature and description:
                play_audio("data_fetched.mp3")
                text_to_speech(f"The current temperature in {city} is {
                    temperature}°C, and the weather is {description}.")
            else:
                return "I'm sorry, I couldn't retrieve the weather information at the moment."
        else:
            return "I'm sorry, there was an issue fetching the weather information."

    except Exception as e:
        print(f"Error fetching weather data: {e}")
        text_to_speech(
            "I'm sorry, there was an error fetching the weather information.")


def get_news():
    api_key = 'e4c15d637e9e4768991cd2e894963687'
    country = 'NG'
    news_api_url = 'https://newsapi.org/v2/top-headlines'
    params = {
        'country': country,
        'apiKey': api_key,
    }

    try:
        response = requests.get(news_api_url, params=params)
        data = response.json()

        if response.status_code == 200:
            articles = data.get("articles", [])

            if articles:
                play_audio("data_fetched.mp3")
                headlines = [article.get("title") for article in articles[:3]]
                text_to_speech("Here are the latest headlines:\n" +
                               "\n".join(headlines))
            else:
                return "I'm sorry, I couldn't retrieve the latest news at the moment."
        else:
            return "I'm sorry, there was an issue fetching the latest news."

    except Exception as e:
        print(f"Error fetching news data: {e}")
        text_to_speech(
            "I'm sorry, there was an error fetching the latest news.")


def handle_no_input():
    play_audio("incorrect_prompt.wav")
    text_to_speech("Sorry, I didn't hear anything. Please try again.")


def get_user_name(intent):
    user_name_match = re.search(
        r"\b(?:my name is|i am|)(?:\s+)?(\w+)\b", intent)
    return user_name_match.group(1) if user_name_match else None


def get_response(intent, prompts):
    closing_words = ["goodbye", "bye", "exit"]

    for item in prompts:
        if "prompt" in item and "response" in item:
            if any(prompt in intent for prompt in item["prompt"]):
                if "{user_name}" in item["response"]:
                    play_audio("data_fetched.mp3")
                    user_name = get_user_name(intent)
                    return item["response"].format(user_name=user_name) if user_name else "I'm sorry, I didn't catch your name."
                elif any(category in item["prompt"] for category in ["weather", "temperature", "forecast"]):
                    return get_weather()
                elif any(category in item["prompt"] for category in ["news", "headlines", "current events"]):
                    return get_news()
                elif any(word in intent for word in closing_words):
                    goodbye()
                else:
                    return item["response"]
    play_audio("incorrect_prompt.wav")
    text_to_speech("I'm not sure how to respond to that. Could you please ask me something else?")


def text_to_speech(response):
    engine = pyttsx3.init(driverName='sapi5')
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)  # Index 1 corresponds to a female voice
    engine.say(response)
    engine.runAndWait()


def goodbye():
    play_audio("close_app.wav")
    text_to_speech(
        "Goodbye! If you have more questions in the future, feel free to ask.")
    sys.exit()


def run_assistant():
    speech_data = load_speech_data()

    play_audio("start_app.wav")

    while True:
        try:
            user_input = recognize_speech()

            if not user_input:
                handle_no_input()
                continue

            if user_input == "exit":
                goodbye()
            else:
                assistant_response = get_response(user_input, speech_data)
                # print("Licia:", assistant_response)
                text_to_speech(assistant_response)

        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":
    run_assistant()
