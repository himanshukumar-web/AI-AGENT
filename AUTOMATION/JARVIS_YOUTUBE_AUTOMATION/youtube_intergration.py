import os
import sys
import importlib.util
import random

# Add current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from another_automation_in_youtube import *
from caption_in_video import *
from manual_search_in_youtube import *
from play_music_in_youtube import *
from play_pause_in_youtube import *
from search_in_youtube import *
from youtube_video_playback import *

def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

listen_path = os.path.join(project_root, 'FUNCTION', 'JARVIS_LISTEN', 'listen.py')
speak_path = os.path.join(project_root, 'FUNCTION', 'JARVIS_SPEAK', 'speak.py')
dlg_path = os.path.join(project_root, 'DATA', 'DLG.py')

try:
    listen_module = import_module_from_path('listen', listen_path)
    listen = listen_module.listen
    
    speak_module = import_module_from_path('speak', speak_path)
    speak = speak_module.speak
    
    dlg_module = import_module_from_path('DLG', dlg_path)
    x = dlg_module.x
    q = dlg_module.q
    x1 = dlg_module.x1
    x2 = dlg_module.x2
except Exception as e:
    print(f"Error importing modules in youtube_integration: {e}")
    listen = lambda: ""
    speak = print
    x = []
    q = []
    x1 = []
    x2 = []

def youtube_cmd(text):
    if text in x :
        a = random.choice(q)
        speak(a)
        text = listen().lower()
        play_music_on_youtube(text)

    elif text in x1 :
        stop()
    elif text in x2 :
        play()
    elif text == "increase volume":
        volume_up()

    elif text == "decrease volume":
        volume_down()

    elif text == "seek forward":
        seek_forward()

    elif text == "seek backward":
        seek_backward()

    elif text == "seek forward 10 seconds":
        seek_forward_10s()

    elif text == "seek backward 10 seconds":
        seek_backward_10s()

    elif text == "seek backward frame":
        seek_backward_frame()

    elif text == "seek forward frame":
        seek_forward_frame()

    elif text == "seek to beginning":
        seek_to_beginning()

    elif text == "seek to end":
        seek_to_end()

    elif text == "seek to previous chapter":
        seek_to_previous_chapter()

    elif text == "seek to next chapter":
        seek_to_next_chapter()

    elif text == "decrease playback speed":
        decrease_playback_speed()

    elif text == "increase playback speed":
        increase_playback_speed()

    elif text == "move to next video":
        move_to_next_video()

    elif text == "move to previous video":
        move_to_previous_video()

    elif text == "toggle subtitles":
        toggle_subtitles()

    elif text == "increase font size":
        increase_font_size()

    elif text == "decrease font size":
        decrease_font_size()

    elif text == "rotate text opacity":
        rotate_text_opacity()

    elif text == "rotate window opacity":
        rotate_window_opacity()

    elif text == "pan up":
        pan_up()

    elif text == "pan down":
        pan_down()

    elif text == "pan left":
        pan_left()

    elif text == "pan right":
        pan_right()

    elif text == "zoom in":
        zoom_in()

    elif text == "zoom out":
        zoom_out()

    elif text == "go to search box":
        go_to_search_box()

    elif text == "toggle play/pause":
        toggle_play_pause()

    elif text == "toggle mute/unmute":
        toggle_mute_unmute()

    elif text == "toggle full screen":
        toggle_full_screen()

    elif text == "toggle theater mode":
        toggle_theater_mode()

    elif text == "toggle miniplayer mode":
        toggle_miniplayer_mode()

    elif text == "exit full screen":
        exit_full_screen()

    elif text == "toggle party mode":
        toggle_party_mode()

    elif text == "navigate forward":
        navigate_forward()

    elif text == "navigate backward":
        navigate_backward()

    elif text.endswith("search in youtube") or text.startswith("search in youtube") or text.endswith("search on youtube") or text.startswith("search on youtube"):
        text = text.replace("search in youtube","")
        text = text.replace("search on youtube","")
        youtube_search(text)

    elif text.endswith("search in current youtube window") or text.endswith("search on current youtube window") or text.endswith("search current youtube window") or text.startswith("search"):
        text.replace("search in current youtube window","")
        text.replace("search on current youtube window","")
        text.replace("search current youtube window","")
        text.replace("search current youtube window","")
        search_manual(text)
    else:
      pass
