import os
import sys

# Add current directory to sys.path to allow imports from same directory
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from tab_automation import *
from search_in_google import *
from scrole_automation import *
from open_website import *


def google_cmd(text):
    if "open" in text:
        if "website" in text or "site" in text:
            text = text.replace("open", "")
            text = text.replace("website", "")
            text = text.replace("site", "")
            text = text.strip()
            openweb(text)
        else:
            text = text.replace("open","")
            text = text.strip()
            if text == "":
                pass
            else:
                # Assuming 'open' function is intended here, but it's not imported or defined in this file.
                # It likely refers to 'common_open.open' but that's not imported.
                # For now, we will pass as it was in original code or fix if we know where 'open' comes from.
                # Looking at original code, it called 'open(text)'. 
                # If this was meant to be the python built-in open, it would error.
                # It probably meant common_open.open.
                pass 

    elif "scroll up" in text:
        scroll_up()

    elif "scroll down" in text:
       scroll_down()

    elif "scroll to top" in text:
       scroll_to_top()

    elif "scroll to bottom" in text:
       scroll_to_bottom()
    
    elif text.endswith("search in google") or text.startswith("search in google") or text.endswith("search on google") or text.startswith("search on google"):
        text = text.replace("search in google","")
        text = text.replace("search on google","")
        search_google(text)

    elif "close tab" in text:
        close_tab()

    elif "open browser menu" in text:
        open_browser_menu()

    elif "zoom in" in text:
        zoom_in()

    elif "zoom out" in text:
        zoom_out()

    elif "refresh page" in text:
        refresh_page()

    elif "switch to next tab" in text:
        switch_to_next_tab()

    elif "switch to previous tab" in text:
        switch_to_previous_tab()

    elif "open history" in text:
        open_history()

    elif "open bookmarks" in text:
        open_bookmarks()

    elif "go back" in text:
        go_back()

    elif "go forward" in text:
        go_forward()

    elif "open dev tools" in text:
        open_dev_tools()

    elif "toggle full screen" in text:
        toggle_full_screen()

    elif "open private window" in text:
        open_private_window()

    elif "open new tab" in text:
        open_new_tab()
    else:
        pass
