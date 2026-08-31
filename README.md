# 🤖 JARVIS AI — Advanced LLM-Powered Personal AI Agent (Phase 2)

An intelligent, context-aware, voice-first personal AI agent built in Python (Target: **Python 3.14.7**). JARVIS is powered by a **Central Agent Core**, **Intelligent Intent & Task Router**, **Lightweight Multi-Step Task Planner**, **Namespaced Tool Registry & Action Logger**, **SQLite Memory 2.0 (Short/Long-Term/Episodic)**, **Barge-in Voice 2.0 Engine**, and **Self-Diagnostics Doctor**.

---

## 🏛️ Comprehensive Architecture

```
USER (Voice / CLI)
  │
  ▼
CONVERSATION MANAGER (Bounded Context Window + Situational State)
  │
  ▼
INTELLIGENT ROUTER (Zero-Latency Classification)
  │
  ├─► INTERRUPT ──────────────► TASK STATE MANAGER (Stops Speech & Halts Execution)
  │
  ├─► SIMPLE COMMAND ─────────► DIRECT NAMESPACED TOOLS (0 LLM API calls)
  │
  ├─► MEMORY COMMAND ─────────► MEMORY 2.0 (Remember, Recall, Forget)
  │
  ├─► MULTI-STEP TASK ────────► TASK PLANNER (Decomposes to sequential tool steps)
  │
  └─► REASONING / QUESTION ───► LLM PROVIDER LAYER (OpenAI / Gemini / Groq / Ollama)
                                      │
                                      ▼
                              TOOL & ACTION REGISTRY (Namespaced, Validated Schemas)
                                      │
                                      ▼
                              SAFETY & RISK GUARD (Low / Medium / High Risk Policy)
                                      │
                                      ▼
                              AUTOMATION SUBSYSTEMS (YouTube, Browser, Apps, Battery)
                                      │
                                      ▼
                              ACTION LOGGER & METRICS (Audit Log in SQLite without secrets)
                                      │
                                      ▼
                              EPISODIC & LONG-TERM MEMORY (Structured Observation)
                                      │
                                      ▼
                              GROUNDED RESPONSE SYNTHESIS (Natural, concise, non-robotic)
                                      │
                                      ▼
                              VOICE 2.0 (Barge-in TTS) / CLI STREAMING
```

---

## 🚀 Key Phase 2 Features

### 1. 🧭 Intelligent Intent & Task Router
- **Zero-Latency Dispatch**: Immediately classifies requests into:
  - `INTERRUPT`: `"Jarvis stop"`, `"Cancel"`, `"Stop"` -> Instant halt.
  - `SIMPLE_COMMAND`: `"what time is it"`, `"battery status"`, `"tell me a joke"`, `"open youtube"`, `"open notepad"` -> Local execution with 0 LLM calls.
  - `MEMORY_COMMAND`: `"remember that..."`, `"forget what I told you about..."`, `"what do you remember..."` -> Direct SQLite Memory operations.
  - `MULTI_STEP_TASK`: Instructions with multiple actions (*"Find the best Python courses, compare them and summarize the result"*) -> Delegated to Planner.
  - `QUESTION_KNOWLEDGE`: Factual queries and conversational dialogue -> Grounded LLM reasoning.

### 2. 📋 Lightweight Task Planner
- **Structured Step Generation**: Decomposes complex instructions into a sequence of discrete `PlanStep(tool, arguments, description)`.
- **Sequential Execution**: Executes each step via the Tool Registry while continuously checking for user interruption.
- **Episodic Persistence**: Records completed multi-step tasks in SQLite episodic memory.
- **Strict Security**: Only registered allowlisted tools can be executed. Arbitrary shell or python code execution is strictly prohibited.

### 3. 🛠️ Namespaced Tool Registry & Action Auditing
- **Standardized Namespaces**:
  - `system.time`, `system.battery`, `system.ip`, `system.internet`, `system.joke`, `system.advice`, `system.launch_app`, `system.close_app`
  - `weather.get`
  - `browser.open`, `browser.search`
  - `youtube.play`, `youtube.search`, `youtube.pause`, `youtube.volume`
  - `automation.create`, `automation.list`, `automation.update`, `automation.delete`, `automation.run`, `automation.history`
  - `memory.remember`, `memory.recall`, `memory.forget`
  - `research.deep_search`
- **Action History Logging**: Every execution logs timestamp, tool name, sanitized parameters, duration (ms), risk level, and success/error to SQLite (`action_history` table) without saving credentials.

### 4. 🧠 Memory 2.0 (Short-Term, Long-Term, Episodic)
- **Short-Term Context**: Current session turns, active app/topic, and recent search results list (for ordinal follow-up resolution e.g. *"play the second one"*).
- **Long-Term Facts**: User preferences, traits, and explicit notes (*"Remember that my favorite artist is Hans Zimmer"*).
- **Episodic Memory**: Completed multi-step plans, summaries, and key outcomes.
- **Relevance Retrieval**: Scores and injects only relevant context for each prompt rather than sending the entire database to the LLM.
- **Natural Memory Commands**:
  - *"Remember that I prefer dark mode."*
  - *"Forget what I told you about X."*
  - *"What do you remember about my preferences?"*

### 5. 🛑 Task State & Safe Interruption
- Explicit state lifecycle: `IDLE`, `PLANNING`, `SEARCHING`, `EXECUTING`, `WAITING_CONFIRMATION`, `INTERRUPTED`, `COMPLETED`.
- User interruption: Saying *"Jarvis stop"* or typing `"stop"` immediately halts ongoing TTS speech and cancels active task plans.

### 6. 🏥 Self-Diagnostics (JARVIS Doctor)
- Command: `python main.py --doctor` or voice `"Jarvis, run diagnostics"`
- Checks:
  - Python runtime & environment
  - Microphone & SoundDevice/PyAudio
  - Offline TTS engine
  - Internet connectivity
  - Configured LLM provider & availability
  - SQLite Memory 2.0 database integrity
  - Custom Automations store

### 7. 📊 Observability, Latency & Cost Tracking
- Tracks total LLM calls, average response latency (ms), token usage estimates, and tool execution durations.

---

## ⚙️ Configuration & Setup

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 2. Configure Environment (`.env`)
Copy `.env.example` to `.env`:
```ini
JARVIS_NAME=Jarvis
JARVIS_USER_NAME=Sir
WAKE_WORDS=jarvis,hey jarvis,ok jarvis,okay jarvis

LLM_PROVIDER=auto
LLM_ROUTING_MODE=hybrid

# Optional Cloud API Keys (or run offline with Ollama/Rules)
OPENAI_API_KEY=
GEMINI_API_KEY=
GROQ_API_KEY=

# Local Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3:latest

# Weather
OPENWEATHERMAP_API_KEY=
WEATHER_CITY=New Delhi, India
```

---

## 💻 Usage

### Run Self-Diagnostics
```powershell
python main.py --doctor
```

### Run in Interactive CLI Mode
```powershell
python main.py --cli
```

### Run in Voice Mode
```powershell
python main.py
```

---

## 🧪 Verification Suite
Run the full 21-point verification suite:
```powershell
python test_suite.py
```
