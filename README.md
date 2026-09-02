# 🤖 JARVIS AI — Advanced Personal AI Assistant & Computer Use System (Phase 5)

An extensible, voice-first, proactive personal AI assistant built in Python (Target: **Python 3.14.7**). JARVIS features **Controlled Computer Vision & Desktop Perception**, **Bounded Mouse & Keyboard Control**, **Native Window Management**, **Multi-Tier Safety Guardrails**, **Global Emergency Stop**, **Modular Skill Architecture** (`SKILLS/`), **Contextual Dynamic Tool Discovery**, **Advanced Task Planner with Failure Recovery**, **Task Manager**, **Multi-Channel Notification Engine**, **4-Tier SQLite Memory 2.0**, and an **Optional Live Web Dashboard**.

---

## 🏛️ System Architecture

```
USER (Voice: English / Hindi / Hinglish / CLI)
  │
  ▼
AGENT CORE & CONVERSATION MANAGER (Bounded Context + State Tracking + Ordinal Resolver)
  │
  ▼
INTELLIGENT ROUTER (Zero-Latency Local Intent Classification)
  │
  ├─► INTERRUPT / EMERGENCY STOP ─► EMERGENCY STOP CONTROLLER & VOICE ENGINE (Instant Abort)
  │
  ├─► SIMPLE COMMAND ─────────────► DIRECT LOCAL TOOLS (0 LLM API calls, Instant Spoken Response)
  │
  ├─► CAPABILITIES / STATUS ──────► SKILL REGISTRY & SYSTEM STATUS (Introspection)
  │
  ├─► MEMORY COMMAND ─────────────► MEMORY 2.0 (Remember, Recall, Forget, Importance Scoring)
  │
  ├─► MULTI-STEP TASK ────────────► ADVANCED TASK PLANNER & TASK MANAGER (Structured steps, retries)
  │
  └─► COMPUTER USE & REASONING ───► CONTEXTUAL DYNAMIC TOOL DISCOVERY (Filters tools by topic)
                                      │
                                      ▼
                              LLM PROVIDER LAYER (OpenAI / Gemini / Groq / Ollama / Offline)
                                      │
                                      ▼
                              COMPUTER CONTROL & VISION ENGINE (`BRAIN/COMPUTER/`)
                                ├── SCREEN    : On-Demand Capture & Multi-Monitor Topology
                                ├── INPUT     : Bounded Mouse & Whitelisted Keyboard Execution
                                ├── WINDOW    : Native Window Management & Application Awareness
                                ├── VISION    : Gemini / OpenAI / Ollama / Offline Heuristic Analyzer
                                ├── SAFETY    : Risk Tiers (LOW/MED/HIGH), Sensitive UI & Action Budgets
                                └── AGENT     : Visual Perception-Action-Verification Loop
                                      │
                                      ▼
                              SAFETY MANAGER & CONFIRMATION CENTER (Voice/CLI Safety Guard)
                                      │
                                      ▼
                              ACTION LOGGER & METRICS (Audit Log in SQLite with Secret Redaction)
                                      │
                                      ▼
                              VOICE 3.0 / CLI STREAMING / LIVE WEB DASHBOARD
```

---

## 👁️ Key Phase 5 Computer Vision & Computer Control Capabilities

### 1. 🖥️ On-Demand Screen Perception & Multi-Monitor Awareness (`BRAIN/COMPUTER/screen/`)
- **Interactive Desktop Attachment**: Uses native Windows `OpenInputDesktop` and `SetThreadDesktop` context managers to guarantee captures and inputs function smoothly across all desktop sessions.
- **Multi-Monitor Topology**: Discovers monitors, primary display, resolutions, coordinate offsets, and DPI scaling.
- **Privacy & Storage Guardrails**: Captures screenshots strictly on-demand. Never captures continuously in the background and avoids persistent storage leaks by using temporary files and in-memory PIL images.
- **Bandwidth & Cost Optimization**: Automatically resizes (max 1280px) and compresses screenshots to JPEG before external transmission.

### 2. 🔍 UI Element Detection & Structured Grounding (`BRAIN/COMPUTER/vision/`)
- **Structured Localization**: Detects buttons, search inputs, links, tabs, dialogs, and windows.
- **Information, Not Authorization**: Vision models produce structured coordinates and confidence scores; they **never directly execute actions**.
- **Confidence Thresholding**: Enforces configurable confidence thresholds (`VISION_CONFIDENCE_THRESHOLD=0.60`). If confidence is too low, JARVIS refuses to click blindly and prompts for clarification.

### 3. 🖱️ Controlled Mouse & Keyboard Control (`BRAIN/COMPUTER/input/`)
- **Boundary Validation**: Every mouse coordinate `(x, y)` is validated against active screen dimensions before execution. Negative or out-of-bounds clicks are strictly blocked.
- **Mouse Operations**: `move_mouse`, `click`, `double_click`, `right_click`, `scroll`, and `drag` with post-action settle delays.
- **Keyboard Whitelist**: Only whitelisted keys (Enter, Escape, Tab, Backspace, Arrow keys, Modifiers, Function keys) and safe shortcuts (`ctrl+c`, `ctrl+v`, `ctrl+t`, `ctrl+w`, `ctrl+l`, `alt+tab`) are permitted.
- **Anti-Injection**: Blocks arbitrary key sequences or dangerous shortcuts (e.g. system wipes, privileged key combos).

### 4. 🪟 Window Management & Application Awareness (`BRAIN/COMPUTER/window/`)
- **Application Context**: Tracks which application is currently active (`window_manager.get_active_window()`).
- **Focus & State Control**: Automatically brings background applications to the front (`focus_window`), maximizes, minimizes, restores, and gracefully requests window closure (`close_window`).
- **Safe Closure**: Never violently terminates processes; sends standard `WM_CLOSE` signals and requests user confirmation if unsaved changes exist.

### 5. 🛡️ Multi-Tier Safety Layer & Action Budgets (`BRAIN/COMPUTER/safety/`)
- **Risk Tiers**:
  - `LOW`: Reading screen, screenshot, finding UI elements, scrolling, querying window titles.
  - `MEDIUM`: Opening applications, typing ordinary search queries, standard website navigation.
  - `HIGH`: Submitting forms, purchases/checkout, deleting files, modifying security settings, closing unsaved windows.
- **Confirmation Gating**: High-risk actions strictly require explicit user confirmation through the `confirmation_center` before execution.
- **Task Budgets & Limits**: Configurable caps prevent runaway automation:
  - `MAX_COMPUTER_ACTIONS=20`
  - `MAX_COMPUTER_RETRIES=3`
  - `MAX_COMPUTER_DURATION=60.0s`
  - `MAX_SCREENSHOTS=10`
- **Sensitive UI & Secret Redaction**: Detects password prompts, banking/payment pages, credit card numbers, and 2FA tokens. Never reads passwords aloud, never sends sensitive screens externally, and masks credentials with `[REDACTED]`.

### 6. 🛑 Immediate Global Emergency Stop
- Instant abort mechanism triggered by voice or text (*"Jarvis stop"*, *"stop everything"*, *"cancel computer task"*, *"ruko"*, *"chup"*).
- Halts computer automation loops immediately without waiting for LLM network latency.

### 7. 🔄 Visual Perception-Action-Verification Loop (`BRAIN/COMPUTER/visual_agent.py`)
- Executes the closed loop:
  `OBSERVE -> UNDERSTAND -> PLAN -> CHECK PERMISSION -> ACT -> OBSERVE AGAIN -> VERIFY -> CONTINUE/STOP`.
- **Visual Verification**: Checks whether the screen or active window changed after executing actions.
- **Fallback Hierarchy**:
  1. Dedicated API
  2. Structured Automation (Selenium / pywhatkit)
  3. Window Management
  4. Visual UI Computer Control
  5. Ask User

---

## 🚀 Existing Subsystems (Phases 1–4)

- **Modular Skill System (`SKILLS/`)**: `SystemSkill`, `BrowserSkill`, `YouTubeSkill`, `WeatherSkill`, `AutomationSkill`, `MemorySkill`, `ResearchSkill`, `ComputerSkill`.
- **Intelligent Intent Router**: Sub-millisecond local classification bypasses LLMs for simple commands.
- **Advanced Task Planner**: Decomposes complex multi-step instructions with step retries and failure recovery.
- **Proactive Notification Engine**: Console, Windows desktop toasts, and spoken voice alerts.
- **Persistent Memory 2.0**: SQLite-backed episodic and semantic memory with importance scoring and automatic pruning.
- **Centralized Confirmation Center**: Interactive voice/CLI approval workflow for medium/high-risk tasks.
- **Live Local Status Dashboard**: Zero-dependency local web dashboard on port `7860`.

---

## 💻 Installation & Setup

### 1. Prerequisites
- Python 3.10+ (Tested on **Python 3.14.7** / 3.13 / 3.12)
- Windows OS (Desktop GUI and audio targets)

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

# Computer Vision & Safety Settings
ENABLE_SCREEN_CAPTURE=true
MAX_COMPUTER_ACTIONS=20
MAX_COMPUTER_RETRIES=3
MAX_COMPUTER_DURATION=60.0
VISION_CONFIDENCE_THRESHOLD=0.60
VISION_PROVIDER=auto
EMERGENCY_STOP_KEY=esc

# Cloud API Keys (Optional if running offline)
OPENAI_API_KEY=
GEMINI_API_KEY=
GROQ_API_KEY=
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

### Run in Developer / Debug CLI Mode
```bash
python main.py --debug --cli
```

### Run in Voice-First Mode
```bash
python main.py
```

### Run the Phase 5 Computer-Use Test Suite
```bash
python -m unittest tests/test_computer_use.py
```

### Run the Full Master Verification Suite
```bash
python test_suite.py
```

---

## 🗣️ Voice & Natural Language Command Reference

| Command Category | Example Voice Prompt | Description |
| :--- | :--- | :--- |
| **Screen Perception** | *"Jarvis, what's on my screen?"* | Analyzes visual display and summarizes open apps |
| **Application State** | *"What application is open?"* | Returns active window title and application name |
| **Element Discovery** | *"Find the search box"* | Locates UI buttons, text inputs, or tabs |
| **Computer Capabilities** | *"What can you do with my computer?"* | Summarizes vision, window, and input tools |
| **Mouse Control** | *"Click the search box"* | Locates element visually and clicks coordinates |
| **Scrolling** | *"Scroll down"* / *"Niche scroll karo"* | Scrolls the active document or web page |
| **Typing** | *"Type Python tutorials"* | Safely types text into focused application |
| **Window Management** | *"Focus Chrome"* / *"Close this window"* | Switches focus or gracefully closes window |
| **Emergency Stop** | *"Jarvis stop"* / *"Cancel computer task"* / *"Ruko"* | Immediately halts any running computer task |
| **Status** | *"Jarvis, status"* | Summarizes subsystem health and active task |
| **Website Launch** | *"Jarvis, open YouTube"* / *"YouTube kholo"* | Opens YouTube in browser |
| **YouTube Search** | *"Search YouTube for Python tutorials"* | Searches YouTube & saves result list |
| **Follow-up Selection** | *"Play the second result"* | Resolves index 1 and plays video |
| **Memory Store** | *"Remember that I prefer dark mode"* | Stores preference with importance |
| **Memory Recall** | *"What do you remember about my preferences?"* | Retrieves facts from SQLite memory |
| **Multi-Step Plan** | *"Find Python courses and summarize results"* | Multi-step task planner execution |
