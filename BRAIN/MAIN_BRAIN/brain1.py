"""
JARVIS AI — Main Brain
Central command processor that routes voice input to the appropriate module.
This is the intelligence hub — it decides what JARVIS should do with each command.

Routing priority:
1. Greetings (good morning, bye, etc.)
2. System commands (time, weather, IP, speed, battery, joke, advice)
3. Automation commands (YouTube, Google, open/close, automation management)
4. QNA dataset (exact match)
5. ML model (Naive Bayes intent classifier)
6. Google search (deep/small)
"""

import importlib.util
import os
import random


def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ── Path Resolution ──────────────────────────────────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

# ── Load Sub-Modules ─────────────────────────────────────────────────────────
# Google search (small/big data)
try:
    google_big = import_module_from_path(
        'google_big_data', os.path.join(current_dir, 'google_big_data.py'))
    deep_search = google_big.deep_search
except Exception as e:
    print(f"Error loading google_big_data: {e}")
    deep_search = lambda x: "I couldn't perform a deep search right now."

try:
    google_small = import_module_from_path(
        'google_small_data', os.path.join(current_dir, 'google_small_data.py'))
    search_brain = google_small.search_brain
except Exception as e:
    print(f"Error loading google_small_data: {e}")
    search_brain = lambda x: "I couldn't search for that right now."

# Speak module
try:
    speak_module = import_module_from_path(
        'speak', os.path.join(project_root, 'FUNCTION', 'JARVIS_SPEAK', 'speak.py'))
    speak = speak_module.speak
except Exception as e:
    print(f"Error loading speak: {e}")
    speak = print

# DLG (dialog data)
try:
    dlg_module = import_module_from_path(
        'DLG', os.path.join(project_root, 'DATA', 'DLG.py'))
    res1 = dlg_module.res1
    res_bye = dlg_module.res_bye
    stopdlg = dlg_module.stopdlg
    cmd1 = dlg_module.cmd1
    stopcmd = dlg_module.stopcmd
    bye_key_word = dlg_module.bye_key_word
except Exception as e:
    print(f"Error loading DLG: {e}")
    res1 = ["Hello sir, Jarvis is here."]
    res_bye = ["Goodbye sir."]
    stopdlg = ["Going to sleep."]
    cmd1 = ["hello", "hi", "jarvis"]
    stopcmd = ["stop listening", "go to sleep"]
    bye_key_word = ["goodbye", "bye"]

# Automation integration
try:
    automation_module = import_module_from_path(
        'automation_intregation',
        os.path.join(project_root, 'AUTOMATION', 'MAIN_INTREGATION', 'automation_intregation.py'))
    process_automation = automation_module.process_automation
except Exception as e:
    print(f"Error loading automation integration: {e}")
    process_automation = lambda x: False

# Clock
try:
    clock_module = import_module_from_path(
        'clock', os.path.join(project_root, 'FUNCTION', 'CLOCK', 'clock.py'))
    what_is_the_time = clock_module.what_is_the_time
except Exception as e:
    print(f"Error loading clock: {e}")
    what_is_the_time = lambda: speak("Clock module is offline.")

# Temperature
try:
    temp_module = import_module_from_path(
        'temp', os.path.join(project_root, 'FUNCTION', 'CHECK_TEMPEATURE', 'temp.py'))
    Temp = temp_module.Temp
except Exception as e:
    print(f"Error loading temperature: {e}")
    Temp = lambda: speak("Weather module is offline.")

# IP Finder
try:
    ip_module = import_module_from_path(
        'find_my_ip', os.path.join(project_root, 'FUNCTION', 'FIND_MY_IP', 'find_my_ip.py'))
    find_my_ip = ip_module.find_my_ip
except Exception as e:
    print(f"Error loading find_my_ip: {e}")
    find_my_ip = lambda: "IP module offline"

# Internet Speed
try:
    speed_module = import_module_from_path(
        'check_internet_speed',
        os.path.join(project_root, 'FUNCTION', 'CHECK_INTERNET_SPEED', 'check_internet_speed.py'))
    check_internet_speed = speed_module.check_internet_speed
except Exception as e:
    print(f"Error loading internet speed: {e}")
    check_internet_speed = lambda: speak("Speed check module is offline.")

# Online Status
try:
    online_module = import_module_from_path(
        'check_online_offline_status',
        os.path.join(project_root, 'FUNCTION', 'CHECK_ONLINE_OFFLINE_STATUS', 'check_online_offline_status.py'))
    internet_status = online_module.internet_status
except Exception as e:
    print(f"Error loading online status: {e}")
    internet_status = lambda: speak("Online status module is offline.")

# Joke
try:
    joke_module = import_module_from_path(
        'joke', os.path.join(project_root, 'BRAIN', 'ACTIVITY', 'JOKE', 'joke.py'))
    get_random_joke = joke_module.get_random_joke
except Exception as e:
    print(f"Error loading joke: {e}")
    get_random_joke = lambda: "Why did the chicken cross the road? To get to the other side."

# Advice
try:
    advice_module = import_module_from_path(
        'advice', os.path.join(project_root, 'BRAIN', 'ACTIVITY', 'ADVICE', 'advice.py'))
    get_random_advice = advice_module.get_random_advice
except Exception as e:
    print(f"Error loading advice: {e}")
    get_random_advice = lambda: "Always do your best."

# Wish (time-based greetings)
try:
    wish_module = import_module_from_path(
        'wish', os.path.join(project_root, 'BRAIN', 'ACTIVITY', 'WISH_GREATINGS', 'wish.py'))
    Greating = wish_module.Greating
except Exception as e:
    print(f"Error loading wish: {e}")
    Greating = lambda x: None

# ML Model (Naive Bayes intent classifier)
try:
    modal2_module = import_module_from_path(
        'modal_2', os.path.join(project_root, 'BRAIN', 'TRANING BRAIN', 'MODAL_2', 'modal_2.py'))
    get_response = modal2_module.get_response
except Exception as e:
    print(f"Error loading ML model: {e}")
    get_response = None


# ── QNA Dataset ──────────────────────────────────────────────────────────────
qa_file_path = os.path.join(project_root, 'BRAIN', 'BRAIN_DATA', 'QNA_DATA', 'qna.txt')


def load_qa_data(file_path):
    """Load Q&A pairs from text file."""
    qa_dict = {}
    if not os.path.exists(file_path):
        print(f"QA file not found: {file_path}")
        return qa_dict

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split(":")
            if len(parts) >= 2:
                q = parts[0].strip().lower()
                a = ":".join(parts[1:]).strip()
                qa_dict[q] = a
    return qa_dict


qa_dict = load_qa_data(qa_file_path)


# ── Main Brain Command Processor ─────────────────────────────────────────────
def brain_cmd(text):
    """
    Process a voice command and return a response.
    This is the main intelligence function of JARVIS.
    
    Args:
        text: The recognized voice command (already lowercased)
    
    Returns:
        Response string, or None if no response is needed (action was performed)
    """
    if not text or not text.strip():
        return None

    # Strip the wake word
    original_text = text
    if "jarvis" in text:
        text = text.replace("jarvis", "").strip()

    if not text:
        # Just the wake word, respond with a greeting
        return random.choice(res1)

    text_lower = text.lower().strip()

    # ── 1. Hello / Wake Greetings ────────────────────────────────────────
    if original_text.lower().strip() in [c.lower() for c in cmd1] or text_lower in [c.lower() for c in cmd1]:
        return random.choice(res1)

    # ── 2. Goodbye Commands ──────────────────────────────────────────────
    if text_lower in [b.lower() for b in bye_key_word] or any(bw in text_lower for bw in ["goodbye", "bye", "good bye"]):
        return random.choice(res_bye)

    # ── 3. Stop / Sleep Commands ─────────────────────────────────────────
    if text_lower in [s.lower() for s in stopcmd] or "go to sleep" in text_lower or "stop listening" in text_lower:
        return random.choice(stopdlg)

    # ── 4. Time-based Greetings ──────────────────────────────────────────
    if any(g in text_lower for g in ["good morning", "good afternoon", "good evening", "good night"]):
        Greating(text_lower)
        return None  # Greating already speaks

    # ── 5. System Utility Commands ───────────────────────────────────────
    # Time
    if any(kw in text_lower for kw in ["what time", "what's the time", "tell me the time", "time batao", "kitne baje"]):
        what_is_the_time()
        return None

    # Weather / Temperature
    if any(kw in text_lower for kw in ["weather", "temperature", "mausam", "taapmaan"]):
        Temp()
        return None

    # IP Address
    if any(kw in text_lower for kw in ["my ip", "ip address", "find my ip", "what is my ip"]):
        ip = find_my_ip()
        return f"Your public IP address is {ip}"

    # Internet Speed
    if any(kw in text_lower for kw in ["internet speed", "check speed", "speed test", "speed check"]):
        check_internet_speed()
        return None

    # Online Status
    if any(kw in text_lower for kw in ["am i online", "online status", "internet status", "are we online"]):
        internet_status()
        return None

    # Joke
    if any(kw in text_lower for kw in ["tell me a joke", "joke", "make me laugh", "funny", "mazak"]):
        joke = get_random_joke()
        return joke

    # Advice
    if any(kw in text_lower for kw in ["give me advice", "advice", "suggestion", "motivate me", "salah"]):
        advice = get_random_advice()
        return f"Here's my advice: {advice}"

    # Battery
    if any(kw in text_lower for kw in ["battery", "charger", "plug"]):
        handled = process_automation(text_lower)
        if handled:
            return None

    # ── 6. Automation Commands ───────────────────────────────────────────
    if process_automation(text_lower):
        return None

    # ── 7. QNA Dataset (exact match) ─────────────────────────────────────
    if text_lower in qa_dict:
        return qa_dict[text_lower]

    # ── 8. ML Model (Naive Bayes intent classification) ──────────────────
    if get_response is not None:
        try:
            ml_response = get_response(text_lower)
            if ml_response and ml_response not in ["I didn't understand that.", "I am not trained yet."]:
                return ml_response
        except Exception as e:
            print(f"ML model error: {e}")

    # ── 9. Deep Search (for research/define/brief commands) ──────────────
    if any(kw in text_lower for kw in ["define", "brief", "research", "teach me", "explain"]):
        try:
            result = deep_search(text)
            if result and result.strip():
                return result
        except Exception as e:
            print(f"Deep search error: {e}")

    # ── 10. Google Quick Search (fallback) ───────────────────────────────
    try:
        result = search_brain(text)
        if result and result.strip():
            return result
    except Exception as e:
        print(f"Google search error: {e}")

    # ── 11. Ultimate Fallback ────────────────────────────────────────────
    return "I'm sorry sir, I wasn't able to find information about that. Could you rephrase your question?"
