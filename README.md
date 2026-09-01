# 🤖 JARVIS AI — Advanced Personal AI Assistant & Skill System (Phase 4)

An extensible, voice-first, proactive personal AI assistant built in Python (Target: **Python 3.14.7**). JARVIS is built with **Modular Skill Architecture** (`SKILLS/`), **Contextual Dynamic Tool Discovery**, **Advanced Task Planner with Failure Recovery**, **Task Manager**, **Multi-Channel Notification Engine**, **4-Tier SQLite Memory 2.0 with Importance Scoring & Pruning**, **Configurable Personality Engine**, **Centralized Confirmation Center**, and an **Optional Live Web Dashboard**.

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
  ├─► CAPABILITIES / STATUS ──► SKILL REGISTRY & SYSTEM STATUS (Zero-latency introspection)
  │
  ├─► MEMORY COMMAND ─────────► MEMORY 2.0 (Remember, Recall, Forget, Importance & Cleanup)
  │
  ├─► MULTI-STEP TASK ────────► ADVANCED TASK PLANNER & TASK MANAGER (Structured steps, retry, recovery)
  │
  └─► REASONING / CHAT ───────► CONTEXTUAL DYNAMIC TOOL DISCOVERY (Filters tools by topic)
                                      │
                                      ▼
                              LLM PROVIDER LAYER (OpenAI / Gemini / Groq / Ollama / Offline)
                                      │
                                      ▼
                              MODULAR SKILL SYSTEM (System, Browser, YouTube, Weather, Automation, Memory, Research)
                                      │
                                      ▼
                              CENTRALIZED CONFIRMATION CENTER (Voice/CLI Safety Guard)
                                      │
                                      ▼
                              PROACTIVE NOTIFICATION ENGINE (Console / Toast / Voice alerts)
                                      │
                                      ▼
                              ACTION LOGGER & METRICS (Audit Log in SQLite without secrets)
                                      │
                                      ▼
                              PERSONALITY ENGINE (Default, Professional, Friendly, Concise, Technical)
                                      │
                                      ▼
                              VOICE 3.0 / CLI STREAMING / LIVE WEB DASHBOARD
```

---

## 🚀 Key Phase 4 Capabilities

### 1. 🧩 Extensible Skill & Plugin Architecture (`SKILLS/`)
- **Modular Design**: Individual capabilities organized into self-contained domain skills:
  - `SystemSkill`: Time, battery, IP, internet, jokes, advice, apps, diagnostics, status.
  - `BrowserSkill`: Website launching and Google web search.
  - `YouTubeSkill`: Search, direct playback, pause/resume, volume controls.
  - `WeatherSkill`: Real-time atmospheric conditions and temperature.
  - `AutomationSkill`: Scheduling, CRUD operations, lifecycle, and history.
  - `MemorySkill`: Fact storage, recall, forgetting, and history cleanup.
  - `ResearchSkill`: Deep research and action audit trail.
- **Skill Discovery**:
  - Voice query: *"Jarvis, what can you do?"* / *"Show skills"* returns a clean, categorized capabilities summary.
  - Dynamic enabling/disabling via `SkillRegistry`.

### 2. 🎯 Dynamic Tool Discovery & Contextual Selection
- Context-aware filtering passes only relevant tool definitions to the LLM (e.g. YouTube queries only receive media tools, automations only receive scheduling tools).
- Drastically reduces LLM prompt token consumption and completely prevents hallucinated tool invocations.

### 3. 📋 Advanced Task Planner & Task Manager
- **Task Lifecycle**: Tracks `TaskRecord` with status (`PENDING`, `RUNNING`, `WAITING_CONFIRMATION`, `COMPLETED`, `FAILED`, `CANCELLED`), step progress %, result, and errors.
- **Plan Visibility**: Explains high-level steps before executing (*"Sure, I'll: 1. Search for courses, 2. Compare top results, 3. Summarize"*).
- **Failure Recovery & Retries**: Automatically retries transient step failures up to 2 times and falls back safely if a non-critical step cannot be completed.
- **Task Queries**: *"Show my current task"*, *"What are you doing?"*, *"Cancel the task"*.

### 4. 🔔 Proactive Assistant & Multi-Channel Notification Engine
- **Channels**: `Console`, `Windows Desktop Toast`, `Voice TTS`.
- **Proactive Alerts**:
  - Scheduled automation execution and failures.
  - Low battery warnings (<=20%) and fully charged notifications.
  - Background task completions.
  - Configurable & easily silenced via settings.

### 5. 🗄️ Enhanced Memory 2.0 with Importance Scoring & Pruning
- **Structured Categorization**: `conversation`, `preference`, `task`, `automation`.
- **Metadata**: `source`, `importance` (1 to 5), `created_at`, `updated_at`.
- **Automated Memory Cleanup**: `cleanup_old_history(days=30)` prunes low-priority dialogue turns while preserving high-priority preferences permanently.
- **Proactive Secret Redaction**: Rejects raw passwords, API keys, and sensitive tokens.

### 6. 🎭 Personality System & Multilingual Adaptation
- **Personality Modes**: `DEFAULT`, `PROFESSIONAL`, `FRIENDLY`, `CONCISE`, `TECHNICAL`.
- **Multilingual Tone**: Automatically detects English, Hindi, and Hinglish (*"youtube kholo"*, *"mausam batao"*, *"open youtube"*) and adapts response phrasing.
- **Voice Sanitizer**: Cleans stack traces and technical jargon into spoken messages (*"I couldn't do that. The browser isn't available."*).

### 7. 🛡️ Centralized Confirmation Center
- Unified confirmation pipeline for medium/high-risk actions.
- Supports voice confirmation (*"Yes"*, *"Do it"*, *"Cancel"*, *"No"*, *"Haan"*) and CLI prompt (`[y/N]`).

### 8. 📊 Live Local Status Dashboard (`python main.py --dashboard`)
- Zero-dependency local web dashboard running on `http://127.0.0.1:7860/`.
- Displays real-time subsystem diagnostics, active task progress, memory records, and tool audit logs without exposing secrets.

### 9. 🛠️ Developer Mode (`python main.py --debug`)
- Verbose execution mode displaying tool durations, LLM token metrics, and task IDs.

---

## 💻 Installation & Setup

### 1. Prerequisites
- Python 3.10+ (Tested on Python 3.14.7 / 3.13 / 3.12 / 3.11)
- Windows OS (Default desktop audio and automation targets)

### 2. Setup Virtual Environment
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Environment Configuration
Copy `.env.example` to `.env`:
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

### Run Self-Diagnostics Health Check
```bash
python main.py --doctor
```

### Run Live Local Status Dashboard
```bash
python main.py --dashboard
```

### Run in Developer / Debug Mode
```bash
python main.py --debug --cli
```

### Run in Voice-First Mode
```bash
python main.py
```

### Run the Full Verification Suite
```bash
python test_suite.py
```

---

## 🗣️ Voice Command Reference

| Command Category | Example Voice Prompt | Description |
| :--- | :--- | :--- |
| **Capabilities** | *"Jarvis, what can you do?"* | Introspects and lists active skills |
| **Status** | *"Jarvis, status"* | Summarizes subsystem health and active task |
| **Active Task** | *"Show my current task"* | Reports active planner progress |
| **Cancel Task** | *"Cancel the task"* / *"Ruko"* | Halts active task safely |
| **Website Launch** | *"Jarvis, open YouTube"* / *"YouTube kholo"* | Opens YouTube in browser |
| **YouTube Search** | *"Search YouTube for Python tutorials"* | Searches YouTube & saves result list |
| **Follow-up Selection** | *"Play the second result"* | Resolves index 1 and plays video |
| **Memory Store** | *"Remember that I prefer dark mode"* | Stores preference with importance |
| **Memory Recall** | *"What do you remember about my preferences?"* | Retrieves facts from SQLite memory |
| **Memory Cleanup** | *"Clean up old memory"* | Prunes old low-importance conversation turns |
| **Automation** | *"Create morning news automation at 9 AM"* | Registers scheduled task |
| **Multi-Step Plan** | *"Find Python courses and summarize results"* | Multi-step task planner execution |
| **Interruption** | *"Jarvis stop"* / *"Cancel"* / *"Chup"* | Cancels speech and active task |
