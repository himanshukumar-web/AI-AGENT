# 🤖 JARVIS AI — Personal Voice & Automation Assistant

An intelligent, voice-controlled personal AI assistant built in Python (Target: **Python 3.14.7**). JARVIS understands natural language commands, performs browser and YouTube automation, executes Windows actions, monitors battery/power, provides system utilities, and manages custom scheduled automations.

---

## ✨ Key Capabilities

### 🧠 Intelligence & Intent Core
- **Natural Language Understanding**: Normalizes conversational variations (e.g., *"Jarvis please open YouTube for me"* → *"open youtube"*).
- **Dual ML / NLP Models**:
  - **Model 1**: TF-IDF vectorization with Cosine Similarity for knowledge retrieval.
  - **Model 2**: Multinomial Naive Bayes intent classifier trained on intent patterns.
- **Q&A Knowledge Base**: 1,870+ structured response pairs.
- **Deep Research Engine**: Automated web extraction and LSA text summarization.
- **Multilingual Support**: Real-time Hindi-to-English translation.

### 🎙️ Resilient Voice Subsystem
- **Dual Audio Backend**: Native Python 3.14 audio capture using `sounddevice` with automatic `PyAudio` fallback—no external C++ build toolchain required on fresh installs.
- **Speech Recognition**: Google Speech API with adaptive noise suppression.
- **Offline TTS Engine**: SAPI5 via `pyttsx3` with thread-safe locking and console fallbacks.
- **Dual Interaction Modes**: Voice-driven with wake word (*"Jarvis"*) or interactive CLI mode (`--cli`).

### ⚡ Automation Engine & Scheduler
- **YouTube Playback & Navigation**: Play songs, adjust volume, toggle captions, seek forward/backward, speed up/slow down, and switch theater/fullscreen modes.
- **Browser Automation**: Open/close tabs, scroll, zoom, navigate history, and launch 169+ pre-configured websites with fuzzy string matching.
- **Windows System Control**: Safe application launching and window closing via keyboard shortcuts.
- **Power & Battery Daemon**: Real-time percentage tracking, charger connect/disconnect detection, and low/full battery alerts.
- **Custom Automation Manager**: Full CRUD (Create, Read, Update, Delete), manual execution, daily scheduling, and execution history logging.
- **Strict Security Allowlist**: Sandboxed action registry preventing arbitrary command execution.

### 🔧 System Utilities
- 🕐 Current time reporting (`what_is_the_time`)
- 🌡️ Weather & temperature querying (OpenWeatherMap API)
- 🌐 Public IP address detection (`api64.ipify.org`)
- 📶 Internet speed testing (Fast.com)
- 🔌 Network online/offline status checks
- 😂 Random programming/dad jokes
- 💡 Motivational advice

---

## 🏗️ Project Architecture

```
HB_JARVIS_F3/
├── main.py                        # Root entry point launcher
├── config.py                      # Centralized configuration & path resolver
├── test_suite.py                  # Automated verification test suite
├── requirements.txt               # Modernized Python 3.14+ dependencies
├── .python-version                # Declares Python 3.14.7 target
├── .env.example                   # Environment configuration template
├── .gitignore                     # Git exclusion rules
├── MAIN/
│   └── main.py                    # Core assistant lifecycle & background daemons
├── BRAIN/
│   ├── MAIN_BRAIN/
│   │   ├── brain1.py              # Central command router & intent dispatcher
│   │   ├── google_big_data.py     # Deep research & summarization engine
│   │   └── google_small_data.py   # Quick search extractor
│   ├── ACTIVITY/                  # Advice, jokes, welcome, and temporal greetings
│   ├── BRAIN_DATA/QNA_DATA/       # Training datasets (qna.json, qna.txt)
│   └── TRANING BRAIN/             # ML Models (TF-IDF & Naive Bayes classifiers)
├── FUNCTION/
│   ├── JARVIS_LISTEN/listen.py    # Speech recognition (sounddevice + pyaudio)
│   ├── JARVIS_SPEAK/speak.py      # SAPI5 Text-to-speech engine
│   ├── CLOCK/clock.py             # Time utility
│   ├── CHECK_TEMPEATURE/temp.py   # Weather service
│   ├── FIND_MY_IP/find_my_ip.py   # IP locator
│   ├── CHECK_INTERNET_SPEED/      # Speed testing
│   └── CHECK_ONLINE_OFFLINE_STATUS/ # Connectivity checker
├── AUTOMATION/
│   ├── automation_manager.py      # Custom automations CRUD & scheduler
│   ├── MAIN_INTREGATION/          # Automation subsystem dispatcher
│   ├── JARVIS_YOUTUBE_AUTOMATION/ # YouTube playback & controls
│   ├── JARVIS_GOOGLE_AUTOMATION/  # Browser navigation & website launcher
│   ├── JARVIS_COMMON_AUTOMATION/  # App launcher & window controls
│   └── JARVIS_BATTERY_ANIMATION/  # Battery & power monitors
└── DATA/
    ├── DLG.py                     # Dialog dataset
    ├── automations.json           # Runtime automation store
    └── automation_logs.json       # Execution history logs
```

---

## 🛠️ Tech Stack & Requirements

| Component | Library / Framework | Supported Version |
|---|---|---|
| **Python Runtime** | CPython | **3.14.7** (Compatible with 3.10+) |
| **Speech Recognition** | `SpeechRecognition` + `sounddevice` | `>=3.14.0`, `>=0.5.0` |
| **Speech Synthesis** | `pyttsx3` (SAPI5) | `>=2.90` |
| **Translation** | `mtranslate` | `>=1.8` |
| **Machine Learning** | `scikit-learn`, `nltk` | `>=1.3.0`, `>=3.8.1` |
| **Web Automation** | `selenium`, `webdriver-manager`, `pywhatkit` | `>=4.15.0`, `>=4.0.0` |
| **GUI Automation** | `pyautogui` | `>=0.9.54` |
| **System Info** | `psutil` | `>=5.9.0` |
| **Job Scheduling** | `schedule` | `>=1.2.0` |
| **Environment** | `python-dotenv` | `>=1.0.0` |

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/himanshukumar-web/AI-AGENT.git
cd AI-AGENT
```

### 2. Create and Activate a Python 3.14 Virtual Environment
```powershell
# Using Python 3.14 launcher
py -3.14 -m venv .venv
.venv\Scripts\activate
```

### 3. Install Dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Configure Environment Variables
```powershell
copy .env.example .env
```
Edit `.env` to configure your credentials:
```ini
OPENWEATHERMAP_API_KEY=your_api_key_here
WEATHER_CITY=New Delhi, India
JARVIS_USER_NAME=Sir
JARVIS_NAME=Jarvis
```

---

## ▶️ Running JARVIS

### Voice Mode (Default)
```powershell
python main.py
```
JARVIS will initialize all subsystems, announce system status, and listen for the wake word **"Jarvis"** (e.g., *"Jarvis what's the weather today?"*).

### CLI / Text Mode (No Mic Required)
```powershell
python main.py --cli
```
Run JARVIS directly in an interactive terminal session by typing commands.

---

## 🧪 Running the Verification Test Suite

Verify all subsystem integrity, ML models, automation lifecycle, and intent parsers:
```powershell
python test_suite.py
```

---

## 🎤 Command Reference

| Category | Example Voice Commands | Action |
|---|---|---|
| **Conversational** | *"Jarvis hello"*, *"Good morning"*, *"How are you"* | Contextual greetings & pleasantries |
| **System Utilities**| *"What time is it"*, *"Check the weather"*, *"Find my IP"* | Real-time system queries |
| **Media & YouTube** | *"Play Bohemian Rhapsody"*, *"Increase volume"*, *"Toggle subtitles"* | YouTube playback control |
| **Browser Control** | *"Open new tab"*, *"Scroll down"*, *"Open history"*, *"Close tab"* | Chrome / Browser shortcuts |
| **Website Launcher**| *"Open GitHub"*, *"Open YouTube"*, *"Open Wikipedia"* | Launches matching URL from 169+ registry |
| **App Launcher**    | *"Open notepad"*, *"Open calculator"*, *"Close"* | Windows application control |
| **Battery Monitor** | *"Battery percentage"*, *"Is charger connected"* | Power & charging diagnostics |
| **Automations**     | *"List automations"*, *"Run automation [name]"*, *"Automation history"* | Custom task execution & logs |
| **Research & Q&A**  | *"Define quantum computing"*, *"Who created you"* | Knowledge retrieval & summarization |

---

## 🔒 Security Architecture

- **Zero Hardcoded Secrets**: All tokens and keys are loaded exclusively from `.env`.
- **Sandboxed Actions**: Custom automations must match the `ALLOWED_ACTIONS` registry; arbitrary shell execution is blocked.
- **Git Hygiene**: `.gitignore` strictly excludes credentials (`.env`), cache files, test environments, and runtime databases.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).

**Author:** [Himanshu Kumar](https://github.com/himanshukumar-web)
