"""
JARVIS AI — YouTube Automation Integration
Handles playback, search, volume, captions, and navigation controls on YouTube.
"""

import os
import sys
import importlib.util
import random

# Add current directory to sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
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
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module {module_name} from {file_path}")
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
except Exception:
    listen = lambda: ""

try:
    speak_module = import_module_from_path('speak', speak_path)
    speak = speak_module.speak
except Exception:
    speak = print

try:
    dlg_module = import_module_from_path('DLG', dlg_path)
    x = dlg_module.x
    q = dlg_module.q
    x1 = dlg_module.x1
    x2 = dlg_module.x2
except Exception:
    x, q, x1, x2 = [], [], [], []


def youtube_cmd(text):
    """Process YouTube commands."""
    text_lower = text.lower().strip()

    # Play song trigger from DLG
    if text_lower in [item.lower() for item in x]:
        a = random.choice(q) if q else "Which song would you like to play?"
        speak(a)
        song_name = listen().lower()
        if song_name:
            play_music_on_youtube(song_name)
        return True

    elif text_lower in [item.lower() for item in x1] or "stop music" in text_lower or "pause video" in text_lower:
        stop()
        return True

    elif text_lower in [item.lower() for item in x2] or "resume music" in text_lower or "resume video" in text_lower:
        play()
        return True

    elif "increase volume" in text_lower or "volume up" in text_lower or "awaz badhao" in text_lower:
        volume_up()
        return True

    elif "decrease volume" in text_lower or "volume down" in text_lower or "awaz kam karo" in text_lower:
        volume_down()
        return True

    elif "seek forward 10 seconds" in text_lower:
        seek_forward_10s()
        return True

    elif "seek backward 10 seconds" in text_lower:
        seek_backward_10s()
        return True

    elif "seek forward frame" in text_lower:
        seek_forward_frame()
        return True

    elif "seek backward frame" in text_lower:
        seek_backward_frame()
        return True

    elif "seek forward" in text_lower or "forward karo" in text_lower:
        seek_forward()
        return True

    elif "seek backward" in text_lower or "rewind" in text_lower:
        seek_backward()
        return True

    elif "seek to beginning" in text_lower or "start of video" in text_lower:
        seek_to_beginning()
        return True

    elif "seek to end" in text_lower:
        seek_to_end()
        return True

    elif "seek to previous chapter" in text_lower:
        seek_to_previous_chapter()
        return True

    elif "seek to next chapter" in text_lower:
        seek_to_next_chapter()
        return True

    elif "decrease playback speed" in text_lower or "slow down video" in text_lower:
        decrease_playback_speed()
        return True

    elif "increase playback speed" in text_lower or "speed up video" in text_lower:
        increase_playback_speed()
        return True

    elif "move to next video" in text_lower or "next video" in text_lower:
        move_to_next_video()
        return True

    elif "move to previous video" in text_lower or "previous video" in text_lower:
        move_to_previous_video()
        return True

    elif "toggle subtitles" in text_lower or "subtitles" in text_lower or "caption" in text_lower:
        toggle_subtitles()
        return True

    elif "increase font size" in text_lower:
        increase_font_size()
        return True

    elif "decrease font size" in text_lower:
        decrease_font_size()
        return True

    elif "rotate text opacity" in text_lower:
        rotate_text_opacity()
        return True

    elif "rotate window opacity" in text_lower:
        rotate_window_opacity()
        return True

    elif "pan up" in text_lower:
        pan_up()
        return True

    elif "pan down" in text_lower:
        pan_down()
        return True

    elif "pan left" in text_lower:
        pan_left()
        return True

    elif "pan right" in text_lower:
        pan_right()
        return True

    elif "zoom in" in text_lower:
        zoom_in()
        return True

    elif "zoom out" in text_lower:
        zoom_out()
        return True

    elif "go to search box" in text_lower:
        go_to_search_box()
        return True

    elif "toggle play" in text_lower or "toggle pause" in text_lower:
        toggle_play_pause()
        return True

    elif "toggle mute" in text_lower or "mute video" in text_lower or "unmute video" in text_lower:
        toggle_mute_unmute()
        return True

    elif "toggle full screen" in text_lower or "fullscreen" in text_lower:
        toggle_full_screen()
        return True

    elif "exit full screen" in text_lower:
        exit_full_screen()
        return True

    elif "toggle theater mode" in text_lower or "theater mode" in text_lower:
        toggle_theater_mode()
        return True

    elif "toggle miniplayer mode" in text_lower or "miniplayer" in text_lower:
        toggle_miniplayer_mode()
        return True

    elif "toggle party mode" in text_lower:
        toggle_party_mode()
        return True

    elif "navigate forward" in text_lower:
        navigate_forward()
        return True

    elif "navigate backward" in text_lower:
        navigate_backward()
        return True

    elif "search in youtube" in text_lower or "search on youtube" in text_lower:
        query = text_lower.replace("search in youtube", "").replace("search on youtube", "").strip()
        if query:
            youtube_search(query)
            return True

    elif any(k in text_lower for k in ["search in current youtube window", "search on current youtube window", "search current youtube window"]):
        query = text_lower
        for kw in ["search in current youtube window", "search on current youtube window", "search current youtube window"]:
            query = query.replace(kw, "")
        query = query.strip()
        search_manual(query)
        return True

    elif "play" in text_lower and ("music" in text_lower or "song" in text_lower or "video" in text_lower or "on youtube" in text_lower):
        song = text_lower.replace("play", "").replace("music", "").replace("song", "").replace("video", "").replace("on youtube", "").strip()
        if song:
            play_music_on_youtube(song)
            return True

    return False
