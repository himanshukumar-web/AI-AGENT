# 🤖 JARVIS AI — Modern LLM-Powered Personal AI Agent

An advanced, voice- and text-controlled personal AI agent upgraded with a **Layered Intelligence Architecture**, **Multi-Provider LLM Abstraction** (OpenAI, Google Gemini, Groq, and Local Offline Ollama), **Tool & Action Registry**, **SQLite Long/Short-Term Memory**, **Voice 2.0 Engine**, and **Strict Safety Guardrails**—built for Python 3.14.7.

---

## ✨ Modern Architecture Highlights

```
USER (Voice / CLI)
  │
  ▼
CONVERSATION MANAGER (Bounded Context Window + State Tracking)
  │
  ├─► FAST DETERMINISTIC ROUTER (Instant zero-latency execution for basic commands)
  │
  ├─► LEGACY ML & QA PRE-LAYER (TF-IDF + Naive Bayes Intent Classifier)
  │
  └─► LLM REASONING LAYER (OpenAI / Gemini / Groq / Local Ollama)
        │
        ▼
      TOOL / ACTION ROUTER (Allowlisted, Typed Schemas)
        │
        ▼
      SAFETY & RISK LEVEL GUARD (Low / Medium / High Risk Confirmation)
        │
        ▼
      AUTOMATION SUBSYSTEMS (YouTube, Browser, Windows Apps, Power, CRUD Automations)
        │
        ▼
      STRUCTURED RESULT OBSERVATION ({"success": true, "data": ...})
        │
        ▼
      MEMORY SYSTEM (SQLite Long-Term Facts & Preferences)
        │
        ▼
      GROUNDED RESPONSE SYNTHESIS (Natural, concise, non-robotic)
        │
        ▼
      VOICE 2.0 ENGINE / STREAMING CLI (Thread-safe, Barge-in interruptible TTS)
```

---

## 🚀 Key Upgraded Subsystems

### 1. 🧠 Layered Intelligence Brain
- **Fast Deterministic Path**: Executes high-frequency commands (*"what time is it"*, *"tell me a joke"*, *"open youtube"*, *"battery status"*) locally with zero LLM API latency.
- **LLM Reasoning Layer**: Handles complex natural language reasoning, multi-step actions, and situational queries (*"Search YouTube for relaxing lofi music and create an automation to run it daily at 8 PM"*).
- **Graceful Fallbacks**: Automatically falls back to internal ML models (`modal_1`, `modal_2`), Q&A datasets, and offline rule handling if cloud APIs or networks are offline.

### 2. 🔌 LLM Provider Abstraction
- Unified provider interface (`BRAIN/LLM/`):
  - **OpenAI**: GPT-4o, GPT-4o-mini with tool calling.
  - **Google Gemini**: Gemini 2.0 Flash, Gemini 1.5 Pro via REST & SDK.
  - **Groq**: Ultra-fast Llama-3.3-70B inference.
  - **Ollama**: 100% private, local offline models (`llama3:latest`, `mistral`, `deepseek-r1`).
- **Dynamic Configuration**: Switch providers via `.env` (`LLM_PROVIDER=auto|openai|gemini|groq|ollama`) without editing code.

### 3. 🛠️ Controlled Tool & Action System
- Strictly typed, sandboxed action router (`BRAIN/TOOLS/tool_registry.py`):
  - `open_website(url)`
  - `search_google(query)`
  - `youtube_play(query)`, `youtube_pause()`, `youtube_volume(direction)`
  - `launch_application(app_name)`, `close_application(app_name)`
  - `get_battery_status()`
  - `get_weather(city)`
  - `get_time()`, `get_ip()`, `check_internet()`
  - `create_automation(...)`, `list_automations()`, `delete_automation(id)`, `run_automation(name)`
  - `remember_memory(key, value)`, `recall_memory(query)`
- **Structured Outputs**: Every tool returns `{"success": bool, "data": Any, "error": str | None}` to eliminate hallucinations.
- **Zero Arbitrary Execution**: Arbitrary shell/bash or python execution is strictly forbidden.

### 4. 🛡️ Safety & Action Risk Guard
- **Three-Tier Risk Levels** (`BRAIN/TOOLS/safety_manager.py`):
  - **LOW**: Read-only queries (time, weather, battery, search, info).
  - **MEDIUM**: App launches, media playback, automation creation.
  - **HIGH**: Deleting automations, terminating apps, clearing memory (requires user confirmation).

### 5. 💾 Memory Architecture (Short & Long-Term)
- **SQLite Storage** (`DATA/jarvis_memory.db`):
  - Persistent user preferences, traits, and facts (*"Remember that my favorite artist is Hans Zimmer"*).
  - Multi-turn conversation logs and session history.
  - Safe storage with no credential or password saving.
- **Conversation Context**: Bounded sliding window with situational state tracking (active app, current topic, follow-up resolution).

### 6. 🎙️ Voice System 2.0
- **Interruptible TTS (Barge-in)**: Thread-safe voice engine allowing speech interruption when new commands are issued.
- **Configurable Wake Words**: Supports *"Jarvis"*, *"Hey Jarvis"*, *"Okay Jarvis"*, and custom words via `WAKE_WORDS` in `.env`.
- **Dual Audio Backend**: Native `sounddevice` with `PyAudio` fallback and multilingual translation.

---

## 📂 Project Structure

```
HB_JARVIS_F3/
├── main.py                        # Root launcher
├── config.py                      # Centralized configuration & environment loader
├── test_suite.py                  # Automated 23-point verification test suite
├── requirements.txt               # Dependencies
├── .env.example                   # Environment variable template
├── .gitignore                     # Git ignore rules
├── MAIN/
│   └── main.py                    # Assistant lifecycle & background services
├── BRAIN/
│   ├── CORE_AGENT/
│   │   └── agent_brain.py         # Modern layered AI agent orchestrator
│   ├── LLM/
│   │   ├── base_provider.py       # Abstract Base LLM Provider & ToolCall dataclass
│   │   ├── openai_provider.py     # OpenAI API integration
│   │   ├── gemini_provider.py     # Google Gemini API integration
│   │   ├── groq_provider.py       # Groq API integration
│   │   ├── ollama_provider.py     # Local offline Ollama integration
│   │   └── provider_manager.py    # Auto-detection, routing, and fallback chain
│   ├── TOOLS/
│   │   ├── tool_registry.py       # Validated tool schemas & structured dispatcher
│   │   └── safety_manager.py      # Risk level policies & confirmation guard
│   ├── MEMORY/
│   │   ├── memory_manager.py      # SQLite persistent long-term storage
│   │   └── conversation_manager.py# Multi-turn state & sliding context window
│   ├── PROMPTS/
│   │   └── system_prompt.py       # Centralized persona & grounding prompt
│   ├── MAIN_BRAIN/
│   │   └── brain1.py              # Backward-compatible bridge to agent brain
│   ├── ACTIVITY/                  # Advice, jokes, greetings
│   ├── BRAIN_DATA/QNA_DATA/       # Training datasets (qna.json, qna.txt)
│   └── TRANING BRAIN/             # ML Models (TF-IDF & Naive Bayes classifiers)
├── VOICE/
│   └── voice_engine.py            # Modern thread-safe interruptible TTS engine
├── FUNCTION/
│   ├── JARVIS_LISTEN/listen.py    # Speech recognition & wake word detection
│   ├── JARVIS_SPEAK/speak.py      # TTS caller
│   ├── CLOCK/clock.py             # Time utility
│   ├── CHECK_TEMPEATURE/temp.py   # Weather service
│   ├── FIND_MY_IP/find_my_ip.py   # IP finder
│   ├── CHECK_INTERNET_SPEED/      # Speed testing
│   └── CHECK_ONLINE_OFFLINE_STATUS/ # Connectivity checker
├── AUTOMATION/
│   ├── automation_manager.py      # Custom automations CRUD & scheduler
│   ├── MAIN_INTREGATION/          # Subsystem dispatcher
│   ├── JARVIS_YOUTUBE_AUTOMATION/ # YouTube playback & controls
│   ├── JARVIS_GOOGLE_AUTOMATION/  # Browser navigation
│   ├── JARVIS_COMMON_AUTOMATION/  # Windows application controls
│   └── JARVIS_BATTERY_ANIMATION/  # Battery & power monitors
└── DATA/
    ├── jarvis_memory.db           # SQLite long-term memory & history
    ├── automations.json           # Custom automation configurations
    └── automation_logs.json       # Automation execution logs
```

---

## ⚙️ Configuration & Setup

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
Copy `.env.example` to `.env` and fill in your settings:
```ini
# General
JARVIS_NAME=Jarvis
JARVIS_USER_NAME=Sir
WAKE_WORDS=jarvis,hey jarvis,ok jarvis,okay jarvis

# LLM Selection (auto, openai, gemini, groq, ollama)
LLM_PROVIDER=auto
LLM_ROUTING_MODE=hybrid

# API Keys (Optional if running Ollama or Offline mode)
OPENAI_API_KEY=your_openai_key
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key

# Local Ollama (Optional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:latest

# Weather
OPENWEATHERMAP_API_KEY=your_weather_key
WEATHER_CITY=New Delhi, India
```

---

## 💻 Usage

### Run in Interactive CLI Mode (Text Only)
```powershell
python main.py --cli
```

### Run in Voice Mode (Microphone + Speaker)
```powershell
python main.py
```

---

## 🧪 Automated Verification Suite

To run the complete 23-point verification test suite covering LLM providers, tool schemas, SQLite memory, safety checks, ML models, and automations:
```powershell
python test_suite.py
```

---

## 🔒 Security & Privacy
- **Zero Arbitrary Execution**: The agent cannot execute arbitrary Python code or shell commands.
- **Strict Parameter Validation**: Only allowlisted functions with typed schemas can be executed.
- **Local Memory**: User preferences and facts are stored locally in SQLite (`DATA/jarvis_memory.db`) with no sensitive passwords captured.
- **Offline Capable**: Fully functional offline via local Ollama models or rule-based fallback.
