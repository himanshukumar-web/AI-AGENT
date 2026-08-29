"""
JARVIS AI — Temperature / Weather Module
Fetches weather data from OpenWeatherMap API.
API key is loaded from environment variable for security.
"""

import requests
import json
import importlib.util
import os
from dotenv import load_dotenv


def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

# Load .env
load_dotenv(os.path.join(project_root, '.env'))

speak_path = os.path.join(project_root, 'FUNCTION', 'JARVIS_SPEAK', 'speak.py')

try:
    speak_module = import_module_from_path('speak', speak_path)
    speak = speak_module.speak
except Exception as e:
    print(f"Error importing speak in temp: {e}")
    speak = print


# M A I N   C O D E

def get_temperature(city=None):
    """Fetch temperature from OpenWeatherMap API."""
    api_key = os.environ.get('OPENWEATHERMAP_API_KEY', '')
    if not api_key:
        return None, "Weather API key not configured. Please set OPENWEATHERMAP_API_KEY in your .env file."

    if not city:
        city = os.environ.get('WEATHER_CITY', 'New Delhi, India')

    endpoint = "http://api.openweathermap.org/data/2.5/weather"

    try:
        response = requests.get(
            endpoint,
            params={"q": city, "appid": api_key, "units": "metric"},
            timeout=10
        )

        if response.status_code == 200:
            data = response.json()
            if 'main' in data:
                temp = data["main"]["temp"]
                description = data.get("weather", [{}])[0].get("description", "")
                return temp, description
            else:
                return None, "Unexpected API response format."
        elif response.status_code == 401:
            return None, "Invalid weather API key. Please check OPENWEATHERMAP_API_KEY in your .env file."
        else:
            return None, f"Weather API error (status {response.status_code})."
    except requests.Timeout:
        return None, "Weather API request timed out."
    except requests.ConnectionError:
        return None, "Unable to connect to weather service. Check your internet connection."
    except Exception as e:
        return None, f"Error fetching weather: {e}"


def Temp(city=None):
    """Speak the current weather/temperature."""
    if not city:
        city = os.environ.get('WEATHER_CITY', 'New Delhi, India')

    temp, info = get_temperature(city)

    if temp is not None:
        speak(f"The weather in {city} is {temp} degrees Celsius, {info}.")
    else:
        speak(info)