import speech_recognition as sr   #pip install SpeechRecognition
import os                         # no need to install
import threading                  # no need to install
from mtranslate import translate  #pip install mtranslate
from colorama import Fore,Style,init #pip install colorama

init(autoreset=True) #Automatically reset Style After Each print

def Trans_hindi_to_english(txt):
    english_txt = translate(txt,"en-us")
    return english_txt

def listen():
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True
    recognizer.energy_threshold = 4000
    recognizer.dynamic_energy_adjustment_damping = 0.15
    recognizer.dynamic_energy_ratio = 1.5
    recognizer.pause_threshold = 0.3
    recognizer.operation_timeout = None
    recognizer.pause_threshold = 0.2
    recognizer.non_speaking_duration = 0.1

    with sr.Microphone() as source:
        # print("Microphone initialized.") # Reduced spam
        recognizer.adjust_for_ambient_noise(source)
        while True:
            print(Fore.LIGHTGREEN_EX + "I am Listening...", end="\r", flush=True)
            try:
                # Wait up to 5 seconds for speech to start, and max 10 seconds for a phrase
                audio = recognizer.listen(source, timeout=5, phrase_time_limit=10)
                print(Fore.LIGHTYELLOW_EX + "Got it, Now Recognizing...", end="\r", flush=True)
                recognized_txt = recognizer.recognize_google(audio).lower()
                if recognized_txt:
                    translated_txt = Trans_hindi_to_english(recognized_txt)
                    print(Fore.BLUE + "Mr STARK : " + translated_txt)
                    return translated_txt
                else:
                    return ""
            except sr.WaitTimeoutError:
                pass # Just loop back and listen again
            except sr.UnknownValueError:
                recognized_txt = ""
            finally:
                pass

def hearing():
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = False
    recognizer.energy_threshold = 34500
    recognizer.dynamic_energy_adjustment_damping = 0.011  # less more active
    recognizer.dynamic_energy_ratio = 1.9
    recognizer.pause_threshold = 0.3
    recognizer.operation_timeout = None
    recognizer.pause_threshold = 0.2
    recognizer.non_speaking_duration = 0.1
    
  
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        while True:
            try:
                audio = recognizer.listen(source,timeout=None)
                recognized_txt = recognizer.recognize_google(audio).lower()
                if recognized_txt:
                    translated_txt = Trans_hindi_to_english(recognized_txt)
                    return translated_txt
                else:
                    return ""
            except sr.UnknownValueError:
                recognized_txt = ""
            finally:
                print("\r",end="",flush=True)

if __name__ == "__main__":
    while True:
        listen()
