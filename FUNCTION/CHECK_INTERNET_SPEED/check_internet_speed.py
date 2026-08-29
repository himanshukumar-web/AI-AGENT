import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import importlib.util
import os

def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

speak_path = os.path.join(project_root, 'FUNCTION', 'JARVIS_SPEAK', 'speak.py')

try:
    speak_module = import_module_from_path('speak', speak_path)
    speak = speak_module.speak
except Exception as e:
    print(f"Error importing speak in check_internet_speed: {e}")
    speak = print

# M A I N   C O D E

def get_internet_speed():
    driver = None
    try:
        # Set the path to your ChromeDriver executable
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--log-level=3")
        chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        # Initialize Chrome browser
        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)

        # Open the website
        driver.get('https://fast.com/')
        speak("Checking your Internet speed")
        time.sleep(11)

        # Wait for the speed test to complete (adjust the timeout as needed)
        WebDriverWait(driver, 60).until(EC.presence_of_element_located((By.ID, 'speed-value')))

        # Find the element with the speed value
        speed_element = driver.find_element(By.ID, 'speed-value')

        # Get the text value from the element
        speed_value = speed_element.text

        return speed_value
    except Exception as e:
        print(f"Error: {e}")
        return None
    finally:
        # Close the browser window
        if driver:
            driver.quit()

def check_internet_speed():
    speed_result = get_internet_speed()

    if speed_result is not None:
        speak(f"Sir, your internet speed is: {speed_result} Mbps")
    else:
        speak("Error: Unable to retrieve internet speed.")
