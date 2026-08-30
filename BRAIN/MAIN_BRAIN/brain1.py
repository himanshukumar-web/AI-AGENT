"""
JARVIS AI — Main Brain
Central command processor and intelligence hub.
Routes voice input through normalized intent detection, system utilities,
custom automations, Q&A datasets, ML classification, and search engines.

Routing Priority:
1. Wake greetings & conversational courtesies ("hello", "hey jarvis", "how are you")
2. Goodbye & shutdown commands ("goodbye", "exit", "go to sleep")
3. Time-based greetings ("good morning", "good evening")
4. System utilities (time, weather, IP address, speed, online status, joke, advice)
5. Automation engine (YouTube, Browser, Apps, Battery, Automation Manager)
6. Q&A dataset exact matches
7. ML Model 2 (Multinomial Naive Bayes Intent Classifier)
8. ML Model 1 (TF-IDF & Cosine Similarity QA Engine)
9. Web search / summarization fallbacks
"""

import importlib.util
import os
import random
import re


def import_module_from_path(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load module from {file_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ── Path Resolution ──────────────────────────────────────────────────────────
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, '..', '..'))

# ── Load Sub-Modules ─────────────────────────────────────────────────────────
# Speak module
try:
    speak_module = import_module_from_path(
        'speak', os.path.join(project_root, 'FUNCTION', 'JARVIS_SPEAK', 'speak.py'))
    speak = speak_module.speak
except Exception:
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
except Exception:
    res1 = ["Hello sir, Jarvis is online."]
    res_bye = ["Goodbye sir. Have a wonderful day."]
    stopdlg = ["Going to sleep sir."]
    cmd1 = ["hello", "hi", "jarvis", "hey jarvis"]
    stopcmd = ["stop listening", "go to sleep", "sleep"]
    bye_key_word = ["goodbye", "bye", "exit", "quit"]

# Automation integration
try:
    automation_module = import_module_from_path(
        'automation_intregation',
        os.path.join(project_root, 'AUTOMATION', 'MAIN_INTREGATION', 'automation_intregation.py'))
    process_automation = automation_module.process_automation
except Exception:
    process_automation = lambda x: False

# Clock
try:
    clock_module = import_module_from_path(
        'clock', os.path.join(project_root, 'FUNCTION', 'CLOCK', 'clock.py'))
    what_is_the_time = clock_module.what_is_the_time
except Exception:
    what_is_the_time = lambda: speak("Clock module offline.")

# Temperature
try:
    temp_module = import_module_from_path(
        'temp', os.path.join(project_root, 'FUNCTION', 'CHECK_TEMPEATURE', 'temp.py'))
    Temp = temp_module.Temp
except Exception:
    Temp = lambda: speak("Weather module offline.")

# IP Finder
try:
    ip_module = import_module_from_path(
        'find_my_ip', os.path.join(project_root, 'FUNCTION', 'FIND_MY_IP', 'find_my_ip.py'))
    find_my_ip = ip_module.find_my_ip
except Exception:
    find_my_ip = lambda: "IP module offline"

# Internet Speed
try:
    speed_module = import_module_from_path(
        'check_internet_speed',
        os.path.join(project_root, 'FUNCTION', 'CHECK_INTERNET_SPEED', 'check_internet_speed.py'))
    check_internet_speed = speed_module.check_internet_speed
except Exception:
    check_internet_speed = lambda: speak("Speed check module offline.")

# Online Status
try:
    online_module = import_module_from_path(
        'check_online_offline_status',
        os.path.join(project_root, 'FUNCTION', 'CHECK_ONLINE_OFFLINE_STATUS', 'check_online_offline_status.py'))
    internet_status = online_module.internet_status
except Exception:
    internet_status = lambda: speak("Online status module offline.")

# Joke
try:
    joke_module = import_module_from_path(
        'joke', os.path.join(project_root, 'BRAIN', 'ACTIVITY', 'JOKE', 'joke.py'))
    get_random_joke = joke_module.get_random_joke
except Exception:
    get_random_joke = lambda: "Why do programmers prefer dark mode? Because light attracts bugs."

# Advice
try:
    advice_module = import_module_from_path(
        'advice', os.path.join(project_root, 'BRAIN', 'ACTIVITY', 'ADVICE', 'advice.py'))
    get_random_advice = advice_module.get_random_advice
except Exception:
    get_random_advice = lambda: "Keep learning and building consistently."

# Wish (time-based greetings)
try:
    wish_module = import_module_from_path(
        'wish', os.path.join(project_root, 'BRAIN', 'ACTIVITY', 'WISH_GREATINGS', 'wish.py'))
    Greating = wish_module.Greating
except Exception:
    Greating = lambda x: None

# ML Model 2 (Naive Bayes Intent Classifier)
try:
    modal2_module = import_module_from_path(
        'modal_2', os.path.join(project_root, 'BRAIN', 'TRANING BRAIN', 'MODAL_2', 'modal_2.py'))
    get_ml2_response = modal2_module.get_response
except Exception:
    get_ml2_response = None

# ML Model 1 (TF-IDF QA Model)
try:
    modal1_module = import_module_from_path(
        'modal_1', os.path.join(project_root, 'BRAIN', 'TRANING BRAIN', 'MODAL_1', 'modal_1.py'))
    get_ml1_response = modal1_module.mind
except Exception:
    get_ml1_response = None

# Search modules
try:
    google_big = import_module_from_path(
        'google_big_data', os.path.join(current_dir, 'google_big_data.py'))
    deep_search = google_big.deep_search
except Exception:
    deep_search = lambda x: ""

try:
    google_small = import_module_from_path(
        'google_small_data', os.path.join(current_dir, 'google_small_data.py'))
    search_brain = google_small.search_brain
except Exception:
    search_brain = lambda x: ""


# ── QNA Dataset ──────────────────────────────────────────────────────────────
qa_file_path = os.path.join(project_root, 'BRAIN', 'BRAIN_DATA', 'QNA_DATA', 'qna.txt')


def load_qa_data(file_path):
    """Load Q&A dataset into dictionary."""
    qa_dict = {}
    if not os.path.exists(file_path):
        return qa_dict

    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line or ':' not in line:
                continue
            parts = line.split(":", 1)
            q = parts[0].strip().lower()
            a = parts[1].strip()
            qa_dict[q] = a
    return qa_dict


qa_dict = load_qa_data(qa_file_path)


# ── Natural Language Command Normalizer ──────────────────────────────────────
def normalize_command(text):
    """
    Strips polite prefixes, filler words, and wake-word variants.
    e.g. "Jarvis please open youtube for me" -> "open youtube"
    """
    if not text:
        return ""

    t = text.lower().strip()

    # Remove wake words
    t = re.sub(r'\b(jarvis|hey jarvis|ok jarvis|hello jarvis)\b', '', t).strip()

    # Remove common conversational prefixes
    prefixes = [
        "could you please", "can you please", "would you please",
        "could you", "can you", "would you", "will you",
        "please", "kindly", "i want you to",
        "help me to", "help me", "do me a favor and",
    ]
    for p in sorted(prefixes, key=len, reverse=True):
        if t.startswith(p + " "):
            t = t[len(p):].strip()

    # Remove common conversational suffixes
    suffixes = [
        "for me please", "for me", "please", "right now",
        "now", "quickly", "asap",
    ]
    for s in sorted(suffixes, key=len, reverse=True):
        if t.endswith(" " + s):
            t = t[:-len(s)].strip()

    return t


# ── Main Brain Command Processor ─────────────────────────────────────────────
def brain_cmd(text):
    """
    Process recognized voice command and return a response or execute action.
    """
    if not text or not str(text).strip():
        return None

    raw_text = text.lower().strip()
    norm_text = normalize_command(raw_text)

    # If empty after removing wake word, greet user
    if not norm_text:
        return random.choice(res1)

    # ── 1. Greetings & Wake Words ────────────────────────────────────────
    if raw_text in [c.lower() for c in cmd1] or norm_text in [c.lower() for c in cmd1] or norm_text in ["hi", "hello", "hey"]:
        return random.choice(res1)

    # ── 2. Goodbye / Exit Commands ───────────────────────────────────────
    if norm_text in [b.lower() for b in bye_key_word] or any(bw in norm_text for bw in ["goodbye", "bye", "exit", "quit"]):
        return random.choice(res_bye)

    # ── 3. Stop / Sleep Commands ─────────────────────────────────────────
    if norm_text in [s.lower() for s in stopcmd] or any(s in norm_text for s in ["go to sleep", "stop listening", "sleep now"]):
        return random.choice(stopdlg)

    # ── 4. Time-based Greetings ──────────────────────────────────────────
    if any(g in norm_text for g in ["good morning", "good afternoon", "good evening", "good night"]):
        Greating(norm_text)
        return None

    # ── 5. System Utilities ──────────────────────────────────────────────
    # Time
    if any(kw in norm_text for kw in ["what time", "what's the time", "current time", "tell me time", "time batao", "kitne baje"]):
        what_is_the_time()
        return None

    # Weather / Temperature
    if any(kw in norm_text for kw in ["weather", "temperature", "mausam", "taapmaan", "forecast"]):
        Temp()
        return None

    # Public IP Address
    if any(kw in norm_text for kw in ["my ip", "ip address", "find my ip", "what is my ip"]):
        ip = find_my_ip()
        return f"Your public IP address is {ip}"

    # Internet Speed
    if any(kw in norm_text for kw in ["internet speed", "check speed", "speed test", "speed check", "net speed"]):
        check_internet_speed()
        return None

    # Online / Internet Status
    if any(kw in norm_text for kw in ["am i online", "online status", "internet status", "are we online", "internet chal raha hai"]):
        internet_status()
        return None

    # Joke
    if any(kw in norm_text for kw in ["tell me a joke", "joke", "make me laugh", "funny", "mazak"]):
        return get_random_joke()

    # Advice
    if any(kw in norm_text for kw in ["give me advice", "advice", "suggestion", "motivate me", "salah"]):
        return f"Here is some advice: {get_random_advice()}"

    # ── 6. Automation Subsystem ──────────────────────────────────────────
    # Check with normalized command first, then raw text
    if process_automation(norm_text) or process_automation(raw_text):
        return None

    # ── 7. QNA Dataset (Exact match) ─────────────────────────────────────
    if norm_text in qa_dict:
        return qa_dict[norm_text]
    if raw_text in qa_dict:
        return qa_dict[raw_text]

    # ── 8. ML Model 2 (Naive Bayes Intent Classifier) ────────────────────
    if get_ml2_response is not None:
        try:
            ml2_res = get_ml2_response(norm_text)
            if ml2_res:
                return ml2_res
        except Exception:
            pass

    # ── 9. ML Model 1 (TF-IDF Cosine Similarity) ─────────────────────────
    if get_ml1_response is not None:
        try:
            ml1_res = get_ml1_response(norm_text)
            if ml1_res:
                return ml1_res
        except Exception:
            pass

    # ── 10. Deep Search (Research / Define / Teach) ──────────────────────
    if any(kw in norm_text for kw in ["define", "brief", "research", "teach me", "explain in detail"]):
        try:
            res = deep_search(norm_text)
            if res and res.strip():
                return res
        except Exception:
            pass

    # ── 11. Quick Search Fallback ────────────────────────────────────────
    try:
        res = search_brain(norm_text)
        if res and res.strip():
            return res
    except Exception:
        pass

    # ── 12. Fallback Response ────────────────────────────────────────────
    return "I am not certain about that sir. Would you like me to research it further?"
