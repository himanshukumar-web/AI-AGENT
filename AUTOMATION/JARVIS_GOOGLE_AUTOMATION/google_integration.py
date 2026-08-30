"""
JARVIS AI — Google / Browser Automation Integration
Handles tab management, scrolling, zooming, searching, and opening websites.
"""

import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from tab_automation import *
from search_in_google import *
from scrole_automation import *
from open_website import *


def google_cmd(text):
    """Process browser and Google automation commands."""
    text_lower = text.lower().strip()

    if "scroll up" in text_lower or "upar scroll" in text_lower:
        scroll_up()
        return True

    elif "scroll down" in text_lower or "neeche scroll" in text_lower:
        scroll_down()
        return True

    elif "scroll to top" in text_lower or "top of page" in text_lower:
        scroll_to_top()
        return True

    elif "scroll to bottom" in text_lower or "bottom of page" in text_lower:
        scroll_to_bottom()
        return True

    elif "close tab" in text_lower or "tab close" in text_lower or "band karo tab" in text_lower:
        close_tab()
        return True

    elif "open new tab" in text_lower or "new tab" in text_lower:
        open_new_tab()
        return True

    elif "switch to next tab" in text_lower or "next tab" in text_lower:
        switch_to_next_tab()
        return True

    elif "switch to previous tab" in text_lower or "previous tab" in text_lower:
        switch_to_previous_tab()
        return True

    elif "refresh page" in text_lower or "reload page" in text_lower:
        refresh_page()
        return True

    elif "zoom in" in text_lower:
        zoom_in()
        return True

    elif "zoom out" in text_lower:
        zoom_out()
        return True

    elif "open history" in text_lower or "browser history" in text_lower:
        open_history()
        return True

    elif "open bookmarks" in text_lower:
        open_bookmarks()
        return True

    elif "go back" in text_lower or "piche jao" in text_lower:
        go_back()
        return True

    elif "go forward" in text_lower or "aage jao" in text_lower:
        go_forward()
        return True

    elif "open dev tools" in text_lower or "inspect element" in text_lower:
        open_dev_tools()
        return True

    elif "open private window" in text_lower or "incognito" in text_lower:
        open_private_window()
        return True

    elif "open browser menu" in text_lower:
        open_browser_menu()
        return True

    elif "toggle full screen" in text_lower:
        toggle_full_screen()
        return True

    elif "search in google" in text_lower or "search on google" in text_lower:
        query = text_lower.replace("search in google", "").replace("search on google", "").strip()
        if query:
            search_google(query)
            return True

    elif "open website" in text_lower or "open site" in text_lower:
        target = text_lower.replace("open website", "").replace("open site", "").strip()
        if target:
            openweb(target)
            return True

    return False
