# 🤖 JARVIS AI — Personal Voice Assistant

An intelligent, voice-controlled personal AI assistant built in Python. JARVIS can understand natural language commands, perform web automations, manage custom automations, tell jokes, check weather, play music, and much more — all through voice interaction.

---

## ✨ Features

### 🧠 AI Assistant
- Natural language command understanding
- QNA dataset with 1876+ question-answer pairs
- ML-based intent classification (Naive Bayes)
- Google search fallback for unknown questions
- Deep search with text summarization
- Hindi-to-English translation support
- Context-aware greetings (time-based)

### 🎙️ Voice Interaction
- Speech recognition via Google Speech API
- Text-to-speech using pyttsx3 (offline, reliable)
- Hindi + English voice input support
- Wake word activation ("Jarvis")
- Continuous listening mode

### ⚡ Automation Engine
- **YouTube Control**: Play music, search videos, volume, playback speed, subtitles, theater mode, and more
- **Browser Control**: Open/close tabs, scroll, zoom, navigate, bookmarks, history, dev tools
- **Website Launcher**: 169+ pre-configured websites with fuzzy matching
- **App Launcher**: Open any Windows application via voice
- **Battery Monitor**: Automatic alerts for low/full battery, charger detection
- **Custom Automations**: Create, edit, delete, enable/disable, and schedule automations
- **Automation History**: Execution logs with timestamps and status

### 🔧 Utilities
- 🕐 Tell the current time
- 🌡️ Check weather/temperature (OpenWeatherMap API)
- 🌐 Find public IP address
- 📶 Check internet speed
- 🔌 Check online/offline status
- 😂 Tell random jokes
- 💡 Give random advice

---

## 🏗️ Architecture

```
HB_JARVIS_F3/
├── MAIN/
│   └── main.py                    # Entry point — voice loop
├── BRAIN/
│   ├── MAIN_BRAIN/
│   │   ├── brain1.py              # Central command processor
│   │   ├── google_big_data.py     # Deep Google search + summarization
│   │   └── google_small_data.py   # Quick Google search
│   ├── ACTIVITY/
│   │   ├── ADVICE/advice.py       # Random advice API
│   │   ├── JOKE/joke.py           # Random joke API
│   │   ├── WELCOME_GREATINGS/     # Welcome greetings
│   │   └── WISH_GREATINGS/        # Time-based wishes
│   ├── BRAIN_DATA/QNA_DATA/       # QNA training data
│   └── TRANING BRAIN/             # ML models (TF-IDF, Naive Bayes)
├── FUNCTION/
│   ├── JARVIS_LISTEN/listen.py    # Speech recognition
│   ├── JARVIS_SPEAK/speak.py      # Text-to-speech (pyttsx3)
│   ├── CLOCK/clock.py             # Time utility
│   ├── CHECK_TEMPEATURE/temp.py   # Weather API
│   ├── FIND_MY_IP/find_my_ip.py   # IP finder
│   ├── CHECK_INTERNET_SPEED/      # Speed test
│   └── CHECK_ONLINE_OFFLINE_STATUS/ # Connectivity check
├── AUTOMATION/
│   ├── automation_manager.py      # Automation CRUD + scheduler
│   ├── MAIN_INTREGATION/          # Central automation dispatcher
│   ├── JARVIS_YOUTUBE_AUTOMATION/ # YouTube controls
│   ├── JARVIS_GOOGLE_AUTOMATION/  # Browser controls
│   ├── JARVIS_COMMON_AUTOMATION/  # App open/close
│   └── JARVIS_BATTERY_ANIMATION/  # Battery monitoring
├── DATA/
│   ├── DLG.py                     # Dialog dataset (responses)
│   └── automations.json           # Custom automations storage
├── config.py                      # Centralized configuration
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variable template
└── .gitignore                     # Git ignore rules
```

---

## 🛠️ Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.10+ |
| Speech Recognition | `SpeechRecognition` + Google Speech API |
| Text-to-Speech | `pyttsx3` (offline) |
| Translation | `mtranslate` (Hindi → English) |
| NLP/ML | `scikit-learn`, `nltk` |
| Web Automation | `selenium`, `pywhatkit` |
| GUI Automation | `pyautogui` |
| Web Scraping | `BeautifulSoup4` |
| Text Summarization | `sumy` |
| System Info | `psutil` |
| Scheduling | `schedule` |

---

## 🚀 Installation

### Prerequisites
- Python 3.10 or higher
- Microphone (for voice input)
- Speakers (for voice output)
- Google Chrome (for web automations)
- Windows OS (for pyautogui system shortcuts)

### Steps

1. **Clone the repository**
   ```bash
   git clone https://github.com/himanshukumar-web/AI-AGENT.git
   cd AI-AGENT
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   .venv\Scripts\activate    # Windows
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   ```bash
   copy .env.example .env
   ```
   Edit `.env` and fill in your values:
   ```
   OPENWEATHERMAP_API_KEY=your_api_key_here
   WEATHER_CITY=New Delhi, India
   JARVIS_USER_NAME=Sir
   ```

5. **Download NLTK data** (first time only)
   ```bash
   python -c "import nltk; nltk.download('punkt'); nltk.download('stopwords')"
   ```

---

## ▶️ How to Run

```bash
cd MAIN
python main.py
```

JARVIS will:
1. Initialize all modules (you'll see `[OK]` for each)
2. Greet you based on the time of day
3. Start listening for voice commands
4. Wait for the wake word **"Jarvis"** before processing commands

---

## 🎤 Available Commands

### Conversation
| Say | Action |
|-----|--------|
| "Jarvis hello" | Greet JARVIS |
| "Jarvis how are you" | Ask how JARVIS is doing |
| "Jarvis good morning" | Time-based greeting |
| "Jarvis goodbye" | Say goodbye |
| "Jarvis go to sleep" | Put JARVIS in sleep mode |

### Utilities
| Say | Action |
|-----|--------|
| "Jarvis what time is it" | Get current time |
| "Jarvis what's the weather" | Get weather info |
| "Jarvis find my IP" | Get public IP address |
| "Jarvis check internet speed" | Run speed test |
| "Jarvis am I online" | Check connectivity |
| "Jarvis tell me a joke" | Get a random joke |
| "Jarvis give me advice" | Get random advice |
| "Jarvis battery percentage" | Check battery level |

### Web & Apps
| Say | Action |
|-----|--------|
| "Jarvis open YouTube" | Open YouTube website |
| "Jarvis open Google" | Open Google |
| "Jarvis open [website name]" | Open any of 169+ websites |
| "Jarvis open [app name]" | Open a Windows application |
| "Jarvis close" | Close active window |
| "Jarvis search Python tutorial on Google" | Google search |

### YouTube
| Say | Action |
|-----|--------|
| "Jarvis play music" | Play a song (will ask for name) |
| "Jarvis search [topic] in YouTube" | Search YouTube |
| "Jarvis increase volume" | Volume up |
| "Jarvis decrease volume" | Volume down |
| "Jarvis toggle subtitles" | Toggle captions |
| "Jarvis toggle full screen" | Toggle fullscreen |
| "Jarvis stop music" | Pause playback |
| "Jarvis play again" | Resume playback |

### Browser
| Say | Action |
|-----|--------|
| "Jarvis open new tab" | New tab |
| "Jarvis close tab" | Close tab |
| "Jarvis scroll up/down" | Scroll page |
| "Jarvis zoom in/out" | Zoom control |
| "Jarvis refresh page" | Refresh |
| "Jarvis go back/forward" | Navigate history |
| "Jarvis open bookmarks" | Open bookmarks |
| "Jarvis open private window" | Incognito mode |

### Automation Management
| Say | Action |
|-----|--------|
| "Jarvis list automations" | Show all automations |
| "Jarvis run automation [name]" | Execute an automation |
| "Jarvis automation history" | View execution logs |
| "Jarvis enable/disable automation [name]" | Toggle automation |
| "Jarvis delete automation [name]" | Remove automation |

### Research
| Say | Action |
|-----|--------|
| "Jarvis define [topic]" | Deep search with summarization |
| "Jarvis research [topic]" | Research mode |
| "Jarvis [any question]" | General Q&A |

---

## 🔧 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENWEATHERMAP_API_KEY` | API key from [OpenWeatherMap](https://openweathermap.org/api) | For weather |
| `WEATHER_CITY` | Default city for weather queries | Optional |
| `JARVIS_USER_NAME` | Your name for personalized greetings | Optional |

---

## 🔒 Security Notes

- **No hardcoded API keys** — all secrets are loaded from `.env`
- **No arbitrary command execution** — automations use a whitelist of allowed actions
- **`.env` is gitignored** — secrets are never committed
- **`chromedriver.exe` is gitignored** — use `webdriver-manager` for auto-download
- Input validation on all automation parameters

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| "No module named X" | Run `pip install -r requirements.txt` |
| Microphone not working | Check Windows sound settings, allow microphone access |
| TTS not speaking | Ensure speakers/headphones are connected |
| Weather not working | Set `OPENWEATHERMAP_API_KEY` in `.env` |
| Chrome automation fails | Ensure Google Chrome is installed |
| PyAudio install fails | Install Visual C++ Build Tools, then `pip install pyaudio` |

---

## 🚧 Future Improvements

- [ ] Web-based UI dashboard
- [ ] Multi-language TTS support
- [ ] Smart home integration (IoT)
- [ ] Email/notification sending
- [ ] Calendar integration
- [ ] Persistent conversation memory
- [ ] Custom wake word training
- [ ] Plugin system for extensibility

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).

---

## 👤 Author

**Himanshu Kumar**
- GitHub: [@himanshukumar-web](https://github.com/himanshukumar-web)

---

> *"Just a rather very intelligent system."* — JARVIS
