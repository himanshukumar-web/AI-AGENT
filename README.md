# 🤖 JARVIS AI — Production-Grade Personal AI Assistant (Phase 3)

An intelligent, voice-first, layered personal AI assistant built in Python (Target: **Python 3.14.7**). JARVIS features **Voice System 3.0** (English, Hindi, Hinglish with thread-safe barge-in interruption), **Brain 3.0** (fast local deterministic routing + LLM delegation), **Provider-Agnostic LLM Architecture** (OpenAI, Gemini, Ollama, Groq, Offline Fallback), **Namespaced Tool Registry & Action Logger**, **3-Tier SQLite Memory 2.0**, **Lightweight Task Planner**, **Safety Boundaries & Secret Redaction**, and **Self-Diagnostics Doctor**.

---

## 🏛️ System Architecture

```
USER (Voice: English / Hindi / Hinglish / CLI)
  │
  ▼
CONVERSATION MANAGER (Bounded Context Window + Situational State + Ordinal Resolver)
  │
  ▼
INTELLIGENT ROUTER (Zero-Latency Local Intent Classification)
  │
  ├─► INTERRUPT ──────────────► TASK STATE & VOICE ENGINE (Instant Stop & Speech Cancellation)
  │
  ├─► SIMPLE COMMAND ─────────► DIRECT LOCAL TOOLS (0 LLM API calls, Instant Spoken Response)
  │
  ├─► MEMORY COMMAND ─────────► MEMORY 2.0 (Remember, Recall, Forget, Secret Filtering)
  │
  ├─► MULTI-STEP TASK ────────► TASK PLANNER (Structured Tool Steps & Safe Execution)
  │
  └─► REASONING / CHAT ───────► LLM PROVIDER LAYER (OpenAI / Gemini / Groq / Ollama / Offline)
                                      │
                                      ▼
                              TOOL REGISTRY (Namespaced, Validated Schemas)
                                      │
                                      ▼
                              SAFETY POLICY & RISK GUARD (Low / Medium / High Risk Tiers)
                                      │
                                      ▼
                              AUTOMATION SUBSYSTEMS (YouTube, Browser, Apps, Battery, Alarms)
                                      │
                                      ▼
                              ACTION LOGGER & METRICS (Audit Log in SQLite without secrets)
                                      │
                                      ▼
                              EPISODIC & LONG-TERM MEMORY (Persistent State Observation)
                                      │
                                      ▼
                              GROUNDED RESPONSE SYNTHESIS (Natural, concise, non-robotic)
                                      │
                                      ▼
                              VOICE 3.0 ENGINE (Pyttsx3 + Barge-In) / CLI STREAMING
```

---

## 🚀 Key Phase 3 Capabilities

### 1. 🎙️ Voice System 3.0 & Interruption Engine
- **Multilingual & Hinglish Recognition**: Interprets English, Hindi, and natural Hinglish commands (e.g., *"Jarvis YouTube kholo"*, *"Jarvis mujhe weather batao"*, *"Jarvis search karo Python tutorials"*, *"Jarvis battery kitni hai"*).
- **Thread-Safe Barge-In Interruption**: Saying *"Jarvis stop"*, *"stop"*, *"cancel"*, *"ruko"*, or *"chup"* immediately cancels active speech and task plans without leaving the system in a broken state.
- **Natural, Concise Spoken Phrasing**: Avoids robotic jargon (*"Sure, opening YouTube."*, *"The time is 10:20 PM."*, *"Done."*).
- **Spoken Text Sanitizer**: Cleans markdown asterisks, URLs, and code blocks before feeding into the TTS engine.
- **Microphone Resilience**: Dual-backend support with PyAudio and SoundDevice fallback with ambient noise calibration.

### 2. 🧭 Brain 3.0 & Layered Intent Routing
- **Zero-Latency Dispatch**:
  - Deterministic queries (Time, Battery, Weather, Jokes, Advice, System status, App launches) execute locally with **0 ms LLM latency**.
  - Ambiguous / complex reasoning requests are seamlessly delegated to the active LLM provider.
- **Local Fallback Layers**: Retains fast TF-IDF and Naive Bayes models for local rule classification.
- **Offline Mode**: Operates autonomously when internet or cloud LLMs are unreachable (*"LLM is currently offline, but I can still handle basic commands."*).

### 3. 🧠 Provider-Agnostic LLM Layer
- **Unified Interface**: `BaseLLMProvider` ensures JARVIS code is decoupled from specific providers.
- **Supported Providers**:
  - **OpenAI** (`gpt-4o`, `gpt-4o-mini`)
  - **Google Gemini** (`gemini-2.0-flash`, `gemini-1.5-pro`)
  - **Ollama Local Models** (`llama3`, `tinyllama`, `phi3`, `mistral`, `qwen2.5`)
  - **Groq** (`llama-3.3-70b-versatile`)
  - **Offline Rule Fallback**
- **Dynamic Model Routing**:
  - Simple tasks -> Local brain / tool
  - Normal conversation -> Fast model
  - Complex reasoning -> Stronger model
  - Local mode -> Ollama instance with model presence check

### 4. 🛠️ Central Namespaced Tool Registry
- **Canonical Tools**:
  - **System**: `system.time`, `system.battery`, `system.ip`, `system.internet`, `system.joke`, `system.advice`, `system.launch_app`, `system.close_app`, `system.diagnostics`
  - **Weather**: `weather.get`
  - **Browser**: `browser.open`, `browser.search`
  - **YouTube**: `youtube.play`, `youtube.search`, `youtube.pause`, `youtube.volume`
  - **Automation**: `automation.create`, `automation.list`, `automation.update`, `automation.delete`, `automation.run`, `automation.history`
  - **Memory**: `memory.remember` (`memory.save`), `memory.recall` (`memory.search`), `memory.forget`
  - **Research & Actions**: `research.deep_search`, `action.history`
- **Safety Policy**: Low, Medium, and High risk tiers with strict permission validation.

### 5. 🗄️ 3-Tier SQLite Memory 2.0
- **Short-Term Context**: Tracks session turns and search result lists for ordinal resolution (*"Play the second result"*, *"Play the last one"*).
- **Long-Term Memory**: Stores user preferences, routines, and persistent facts.
- **Episodic Memory**: Stores completed multi-step plans and execution outcomes.
- **Secret Redaction**: Proactively rejects storing raw passwords, API keys, and sensitive tokens.

### 6. 📋 Multi-Step Task Planner
- Decomposes complex instructions into discrete `PlanStep` sequences using registered tools.
- Supports step-by-step execution with safety bounds and instant interruption checks.

### 7. 🏥 Self-Diagnostics (JARVIS Doctor)
- Command: `python main.py --doctor` or voice command *"Jarvis, run diagnostics"*
- Checks:
  - Python runtime (Python 3.14.7 target)
  - Microphone & audio capture backends
  - pyttsx3 offline speech engine
  - Internet connectivity
  - Active LLM provider & local Ollama tags
  - SQLite memory database integrity
  - Custom automations store
  - Registered tools count & Action history logger

---

## 💻 Installation & Setup

### 1. Prerequisites
- Python 3.10+ (Tested & compatible with Python 3.14.7 / 3.13 / 3.12 / 3.11)
- Windows OS (Default desktop audio and automation targets)

### 2. Setup Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env` and fill in your desired provider credentials:
```ini
JARVIS_NAME=Jarvis
JARVIS_USER_NAME=Sir

# LLM Provider Options: auto, openai, gemini, ollama, groq, offline_fallback
LLM_PROVIDER=auto
LLM_MODEL=

# Cloud API Keys (Optional if running offline with Ollama or local rules)
OPENAI_API_KEY=
GEMINI_API_KEY=
GROQ_API_KEY=

# Local Ollama Configuration (Optional)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=tinyllama:latest

# Voice & Speech Settings
TTS_VOICE_RATE=180
TTS_VOICE_VOLUME=1.0
```

---

## 🏃 Running JARVIS

### Self-Diagnostics Health Check
```bash
python main.py --doctor
```

### Text / CLI Mode (No Microphone Required)
```bash
python main.py --cli
```

### Full Voice-First Mode
```bash
python main.py
```

### Running the Full Test Suite
```bash
python test_suite.py
```

---

## 🗣️ Voice Command Reference

| Command Type | Example Spoken Input | Result |
| :--- | :--- | :--- |
| **Simple Info** | *"Jarvis, what time is it?"* | Local time tool (0ms LLM latency) |
| **Hinglish Info** | *"Jarvis, mausam batao"* | Local weather tool |
| **Website Launch** | *"Jarvis, open YouTube"* / *"YouTube kholo"* | Opens YouTube in browser |
| **YouTube Search** | *"Search YouTube for Python tutorials"* | Searches YouTube & saves result list |
| **Ordinal Follow-Up** | *"Play the second result"* | Resolves index 1 and plays video |
| **Memory Store** | *"Remember that I like synthwave music"* | Stores preference in SQLite memory |
| **Memory Recall** | *"What do you remember about my preferences?"* | Retrieves facts from SQLite memory |
| **Memory Forget** | *"Forget about synthwave"* | Removes matching memory records |
| **Automation** | *"Show my automations"* | Lists active custom automations |
| **Multi-Step Task** | *"Find the best Python courses and summarize"* | Task planner + Deep research + Summary |
| **Interruption** | *"Jarvis stop"* / *"Cancel"* / *"Ruko"* | Immediately stops TTS and cancels task |
| **Diagnostics** | *"Jarvis, run diagnostics"* | Runs complete health check |
