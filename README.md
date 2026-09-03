# 🤖 JARVIS AI — Advanced Personal AI Assistant, Computer Use & Web Intelligence System (Phase 6)

An extensible, voice-first, proactive personal AI assistant built in Python (Target: **Python 3.14.7**). JARVIS features **Deep Research & Autonomous Web Intelligence**, **Controlled Computer Vision & Desktop Perception**, **Bounded Mouse & Keyboard Control**, **Native Window Management**, **Multi-Tier Safety Guardrails**, **Global Emergency Stop**, **Modular Skill Architecture** (`SKILLS/`), **Contextual Dynamic Tool Discovery**, **Advanced Task Planner with Failure Recovery**, **Task Manager**, **Multi-Channel Notification Engine**, **4-Tier SQLite Memory 2.0**, and an **Optional Live Web Dashboard**.

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
  ├─► WEB INTELLIGENCE & RESEARCH ─► DEEP RESEARCH ENGINE (`WEB/`)
  │                                   ├── SEARCH     : Multi-Provider Abstraction (DDG / Wiki / Browser / Mock)
  │                                   ├── EXTRACTION : Safe HTML Parser, Noise Stripper & Markdown Tables
  │                                   ├── DEDUPLICATE: Shingle 3-Gram Jaccard Near-Duplicate Filtering
  │                                   ├── SCORING    : Authority, Recency, Relevance & Evidence Depth
  │                                   ├── REASONING  : Fact Extraction, Cross-Checking & Conflict Flagging
  │                                   ├── COMPARISON : Multi-Entity Comparison Matrix Generator
  │                                   ├── CITATIONS  : Verified Grounded Numerical Citations [1]
  │                                   ├── SECURITY   : Prompt Injection Defense & Data Boundary Isolation
  │                                   ├── CONTROLS   : Rate Limiter, TTL Cache & Cancellation Token
  │                                   ├── MEMORY     : SQLite Session Store & Source Change Monitor
  │                                   └── PLANNER    : Quick, Standard & Deep Autonomous Synthesis
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

## 🌐 Deep Research & Web Intelligence System (Phase 6)

JARVIS includes an enterprise-grade autonomous Deep Research & Web Intelligence subsystem located in the `WEB/` package. It enables JARVIS to independently explore topics, collect reputable sources, detect conflicting claims, generate comparison matrices, and produce comprehensive research reports with verified citations—requiring **zero paid API keys**.

### 1. 🔍 Provider-Independent Search Abstraction (`WEB/search/`)
- **Multi-Provider Architecture**: Dynamic search layer decoupled from specific search APIs.
- **Supported Providers**:
  - `duckduckgo`: Zero-API-key HTML and Instant Answer scraper with URL unquoting.
  - `wikipedia`: Direct Wikipedia OpenSearch and Page Summary REST API.
  - `browser`: Headless Selenium browser search fallback.
  - `mock`: Deterministic in-memory provider for fast, isolated unit testing.
- **Failover Chain**: If the requested or primary search provider fails or is rate-limited, JARVIS automatically cascades through fallback providers without user interruption.
- **Configurable Active Provider**: Controlled via `DEFAULT_SEARCH_PROVIDER = "auto"` in `config.py`.

### 2. 📄 Safe Web Content Extraction (`WEB/extraction/extractor.py`)
- **Boilerplate & Noise Stripping**: Removes `<script>`, `<style>`, `<nav>`, `<footer>`, `<aside>`, cookie notices, and advertisements.
- **Structured Content**: Preserves clean document hierarchy (`h1`-`h3`), readable body text, and converts HTML tables into clean Markdown tables.
- **Metadata Extraction**: Extracts titles, meta descriptions, publication dates, and calculates word counts.
- **Timeout & Size Guards**: Enforces strict page size ceilings (1 MB max) and network timeouts (5.0s max) to prevent memory bloat or hanging threads.

### 3. 🧹 Source Normalization & Content Deduplication (`WEB/extraction/deduplicator.py`)
- **Canonical URL Normalization**: Strips tracking parameters (`utm_*`, `ref`, `fbclid`, `gclid`), fragments (`#...`), port numbers, and `www.` prefixes.
- **Near-Duplicate Detection**: Implements 3-gram word shingling and Jaccard similarity thresholding (0.70) to identify mirrored or syndicated content.
- **Highest-Authority Retention**: When duplicates are detected, JARVIS automatically retains the primary, higher-authority source and drops redundant copies.

### 4. ⚖️ Multi-Dimensional Source Quality Scoring (`WEB/intelligence/source_scorer.py`)
- Evaluates four independent dimensions to assign a composite quality score and authority tier:
  1. **Authority Score (40%)**: Domain reputation (`.gov`, `.edu`, official documentation vs random blogs).
  2. **Relevance Score (30%)**: Semantic match between search query terms and page title/snippet/body.
  3. **Recency Score (15%)**: Distinguishes current 2026 data from legacy archives.
  4. **Evidence Depth (15%)**: Substance, structured headings, and informative body length.
- **Authority Tiers**: `High Authority` (≥0.88), `Reputable` (≥0.70), `Secondary` (≥0.50), and `Low Authority`.

### 5. 🔬 Fact Extraction & Consensus Verification (`WEB/intelligence/`)
- **Claim Extraction (`fact_extractor.py`)**: Identifies definitive factual statements, version assertions, specifications, and features.
- **Consensus & Disagreement Cross-Checking (`cross_checker.py`)**:
  - Validates assertions corroborated by 2+ independent sources as **Verified Consensus**.
  - Explicitly flags conflicting claims with clear explanations: *"Sources disagree on this point: Source A reports X while Source B reports Y."*
- **Recency Intent Detection (`recency.py`)**: Classifies queries requiring fresh information (*"latest"*, *"current"*, *"2026"*, *"new features"*).

### 6. 📊 Multi-Entity Comparison Engine (`WEB/intelligence/comparator.py`)
- Compares multiple products, frameworks, models, or technologies across standardized attributes:
  - *Core Capabilities*, *Cost / Pricing*, *Latency / Speed*, *Privacy & Data Security*, *Local / Offline Support*, *API Availability*, and *Best Use Cases*.
- Formats structured Markdown comparison tables and provides balanced architectural trade-off recommendations (e.g. Hybrid Local + Cloud).

### 7. 🔗 Verified Grounded Citations (`WEB/intelligence/citations.py`)
- **Zero Hallucination Policy**: JARVIS never fabricates URLs, sources, or citations.
- **Numbered Citation Brackets**: Claims are grounded with numerical reference brackets (`[1]`, `[2]`).
- **Verified Bibliography**: Appends a structured `## Sources` section containing verified titles, domains, and authentic URLs.

### 8. 🧠 Autonomous Research Planner (`WEB/research/planner.py`)
Executes an intelligent investigation loop:
`QUERY EXPANSION -> SOURCE RETRIEVAL -> DEDUPLICATION -> PAGE EXTRACTION -> SCORING -> CLAIM EXTRACTION -> CROSS-CHECKING -> COMPARISON -> REPORT SYNTHESIS`.
- **Modes**:
  - **Quick Mode**: Single targeted query, ultra-fast summary, 1-2 verified sources.
  - **Standard Mode**: Multi-query expansion, source deduplication, key findings, and citations.
  - **Deep Mode**: Comprehensive multi-query investigation, full cross-checking, comparison matrix, and complete Markdown report.

### 9. 💾 Persistent Research Memory & Monitoring (`WEB/research/`)
- **Research Database (`DATA/jarvis_research.db`)**: Stores research sessions, queries, findings, source URLs, and reports with SQLite indexing.
- **Follow-up Continuity**: Commands like *"save this research"* and *"continue that research"* seamlessly retrieve previous context and deepen investigations.
- **Source Change Monitor (`monitor.py`)**: Analyzes prior research findings against fresh web searches and highlights diffs (*"New information detected..."*).

### 10. 🛡️ Security, Rate Limiting & Prompt Injection Protection (`WEB/security/`)
- **Untrusted Web Data Boundary**: All external scraped web content is treated strictly as **DATA**, never as instructions.
- **Prompt Injection Defense (`sanitizer.py`)**: Scans for directive injection patterns (*"ignore previous instructions"*, *"system prompt:"*, *"delete files"*), filters them, and wraps content in inert XML containers:
  ```xml
  <untrusted_external_web_data context='evidence_only' do_not_execute='true'>
  ... sanitized web content ...
  </untrusted_external_web_data>
  ```
- **Hard Resource Quotas (`rate_limiter.py`)**:
  - `MAX_SEARCHES = 15` per session
  - `MAX_SOURCES = 12`
  - `MAX_PAGE_FETCHES = 8`
  - `MAX_RESEARCH_TIME = 90.0` seconds
- **Thread-Safe Cancellation (`cancellation.py`)**: Immediate cooperative cancellation triggered via *"Jarvis stop research"* or *"cancel research"*.
- **In-Memory TTL Caching (`caching.py`)**: Prevents redundant searches and fetches with configurable cache expiration.

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
- Halts computer automation and research loops immediately without waiting for LLM network latency.

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

## ⚙️ Configuration (`config.py`)

```python
# Deep Research & Web Intelligence Settings
DEFAULT_SEARCH_PROVIDER = "auto"       # "auto", "duckduckgo", "wikipedia", "browser", "mock"
RESEARCH_DEPTH = "standard"             # "quick", "standard", "deep"
MAX_SEARCHES = 15                       # Max search queries per research session
MAX_SOURCES = 12                        # Max sources to collect
MAX_PAGE_FETCHES = 8                    # Max full web pages to extract
MAX_RESEARCH_TIME = 90.0                # Max research duration in seconds
RESEARCH_CACHE_TTL = 3600               # Search & extract cache TTL in seconds
RESEARCH_DB_PATH = PATHS["research_db"] # DATA/jarvis_research.db
```

---

## 🏃 Running JARVIS

### Run Self-Diagnostics Health Check (Doctor)
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

### Run the Phase 6 Web Intelligence Test Suite
```bash
python -m unittest tests/test_web_intelligence.py
```

### Run the Phase 5 Computer-Use Test Suite
```bash
python -m unittest tests/test_computer_use.py
```

### Run the Master Unified Test Suite (93+ Tests)
```bash
python test_suite.py
```

---

## 🗣️ Voice & Natural Language Command Reference

| Command Category | Example Voice Prompt | Description |
| :--- | :--- | :--- |
| **Quick Research** | *"Quick research on Python 3.14"* | Fast single-query search with direct summary & sources |
| **Deep Research** | *"Do deep research on Python AI frameworks"* | Multi-step deep investigation with structured report |
| **Comparative Analysis**| *"Compare OpenAI, Gemini and Ollama"* | Multi-entity feature matrix and trade-off recommendation |
| **Documentation Lookup**| *"Find official documentation for PyTorch"* | Locates verified official developer documentation |
| **Save Research** | *"Save this research"* | Stores current research session in SQLite research memory |
| **Continue Research** | *"Continue that research"* | Follows up on previous research with fresh updates |
| **Source Monitoring** | *"Check whether this information is still current"*| Checks for updates and highlights changes |
| **Stop Research** | *"Jarvis, stop research"* / *"Cancel research"* | Immediately halts running research session |
| **Screen Perception** | *"Jarvis, what's on my screen?"* | Analyzes visual display and summarizes open apps |
| **Application State** | *"What application is open?"* | Returns active window title and application name |
| **Element Discovery** | *"Find the search box"* | Locates UI buttons, text inputs, or tabs |
| **Computer Capabilities** | *"What can you do with my computer?"* | Summarizes vision, window, and input tools |
| **Mouse Control** | *"Click the search box"* | Locates element visually and clicks coordinates |
| **Scrolling** | *"Scroll down"* / *"Niche scroll karo"* | Scrolls the active document or web page |
| **Typing** | *"Type Python tutorials"* | Safely types text into focused application |
| **Window Management** | *"Focus Chrome"* / *"Close this window"* | Switches focus or gracefully closes window |
| **Emergency Stop** | *"Jarvis stop"* / *"Cancel computer task"* / *"Ruko"* | Immediately halts any running computer task |
| **Doctor Diagnostics**| *"Jarvis, status"* / *"Run doctor"* | Runs system diagnostic health check |
| **Website Launch** | *"Jarvis, open YouTube"* / *"YouTube kholo"* | Opens YouTube in browser |
| **YouTube Search** | *"Search YouTube for Python tutorials"* | Searches YouTube & saves result list |
| **Follow-up Selection** | *"Play the second result"* | Resolves index 1 and plays video |
| **Memory Store** | *"Remember that I prefer dark mode"* | Stores preference with importance |
| **Memory Recall** | *"What do you remember about my preferences?"* | Retrieves facts from SQLite memory |
| **Multi-Step Plan** | *"Find Python courses and summarize results"* | Multi-step task planner execution |
