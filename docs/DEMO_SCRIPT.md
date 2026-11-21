# AEGIS-0: 3-Minute Demo Video Recording Cue Sheet
**Track: PS-01 Bifrost + PS-06 Tavily Dual-Stack Grand Slam Architecture**  
**Team: PS · MK · RRS · MB (Anonymized)**  
**Total Target Run Time: Exactly 180 Seconds (03:00)**

---

## Cue Sheet & Master Timeline

### Segment 1: The Agent Trilemma & Cosmic Landing Page
- **Timecode**: `0:00 – 0:30` (30 seconds)
- **Visual Focus**: Fullscreen browser displaying `http://localhost:3000/`. Mouse hovers over the interactive 3D WebGL Cosmic Orb and dual-stack architecture badges (`PS-01 Bifrost` + `PS-06 Tavily`).
- **Presenter Audio**:
  > *"Every autonomous coding agent in production today faces a fatal trilemma: massive token bloat exceeding 50,000 tokens per turn, broken outdated SDK code from parametric cutoffs, and prompt injection vulnerabilities leaking confidential credentials.*
  >
  > *Welcome to **AEGIS-0**: the first zero-trust, token-optimal autonomous software engineering engine combining submodular AST pruning, Bifrost's resilient gateway, Tavily's empirical freshness verification, and cryptographic voice gates. Let’s enter Mission Control."*
- **Action**: Click the primary gradient button **`[Launch Mission Control]`** $\to$ transitions seamlessly into `/workbench`.

---

### Segment 2: Live Agent Run & Stage 01 Submodular AST Knapsack Pruning
- **Timecode**: `0:30 – 1:05` (35 seconds)
- **Visual Focus**: `/workbench` Stage 01 view. The live agent command bar is visible at the top.
- **Presenter Audio**:
  > *"Here in Mission Control, AEGIS-0 dogfoods itself on its own codebase. Notice our Live Agent Command Bar. We select `./orchestrator` as our ingestion target and click **`[Run Live Agent]`**.*
  >
  > *In Stage 01, AEGIS-0 doesn’t dump dumb text files into LLM context. Instead, it extracts the AST call-graph and solves a budgeted submodular knapsack problem: promoting seed symbols and caller/callee dependencies into full context, while collapsing unselected classes and methods into 1-line type-safe stubs.*
  >
  > *Look at the telemetry: our raw repository modules are compressed down from 48,253 tokens to 12,405 tokens—a **74.3% average token reduction** (-74.4% on orchestrator, -74.3% on Tavily freshness, -73.9% on security-gate) with **92.9% retrieval recall @ budget**, while remaining 100% syntactically valid Python code."*
- **Action**: Click **`[Run Live Agent]`**. Point cursor at Stage 01 flamegraph and AST node inspector showing 1-line stubs. Press `2` to toggle to Stage 02.

---

### Segment 3: Stage 02 Deterministic Budget Ledger & Bifrost `<180ms` Circuit-Breaker Failover
- **Timecode**: `1:05 – 1:40` (35 seconds)
- **Visual Focus**: Stage 02 (Bifrost AI Gateway & Financial Ledger).
- **Presenter Audio**:
  > *"Stage 02 addresses the core of PS-01: deterministic financial discipline and high-availability routing.*
  >
  > *First, our Pre-Call Budget Ledger calculates worst-case token costs prior to any network dispatch. If we drag the session ceiling slider down, notice how AEGIS-0 dynamically down-routes from Frontier to Micro tier, and executes an automated hard-halt when limits are breached with zero financial overrun.*
  >
  > *Now watch our Bifrost AI Gateway integration. Under primary operation, traffic flows to Claude 3.5 Sonnet. When we trigger a simulated HTTP 429 provider outage via our 1-click chaos button, Bifrost’s circuit breaker trips to OPEN and seamlessly diverts execution to OpenAI GPT-4o in just **138 milliseconds** without losing a single token of session state."*
- **Action**: Move Budget Slider to demonstrate dynamic down-routing $\to$ Click crimson **`[Inject HTTP 429 Outage]`** button $\to$ Show instant toast and node badge switching to `gpt-4o (138ms)` $\to$ Press `3` to toggle to Stage 03.

---

### Segment 4: Stage 03 Tavily Freshness Auto-Patch (PS-06) & Red-Team Air-Gap Containment
- **Timecode**: `1:40 – 2:20` (40 seconds)
- **Visual Focus**: Stage 03 (Left column: Tavily Scorecard; Top: Red-Team trigger).
- **Presenter Audio**:
  > *"In Stage 03, we conquer PS-06: detecting and healing stale API code. Frontier LLMs routinely hallucinate deprecated calls like `openai.ChatCompletion.create`.*
  >
  > *AEGIS-0 decomposes generated code into atomic API claims and queries Tavily Search in real-time. Using Equation 5, our empirical freshness metric penalizes temporal decay and deprecation flags. Notice this claim scores 22 out of 100—flagged as STALE. With one click, Tavily's self-healing patch upgrades the code to the modern OpenAI v1 client syntax.*
  >
  > *Now watch our adversarial defense. If an attacker injects prompt injection or high-entropy credentials, clicking **`[Test Injection Attack]`** demonstrates how PrivacyGuard calculates Shannon entropy $H \ge 4.5$, immediately locks hardware routing to our local air-gapped enclave, and guarantees zero data exfiltration."*
- **Action**: Click **`[Apply Tavily Fresh Patch]`** on claim 01 $\to$ Click **`[Test Injection Attack]`** button $\to$ Highlight toast `ATTACK CONTAINED: Entropy H=5.12 -> Hardware Locked to Local Ollama Enclave`.

---

### Segment 5: Omnidimension Voice Gate Approval, Terminal CLI & Closing
- **Timecode**: `2:20 – 3:00` (40 seconds)
- **Visual Focus**: Monaco Visual Diff Editor (Stage 03 right column), audio waveform visualizer, and quick switch to Terminal CLI window.
- **Presenter Audio**:
  > *"Finally, zero-trust means agents never write code unchecked. Destructive actions are quarantined behind an HMAC-SHA256 signature.*
  >
  > *Operators review the color-coded Monaco side-by-side diff and authorize deployment vocally via our Omnidimension Voice AI gate: 'Approve Alpha-7'. The cryptographic hash verifies and the patch is safely committed to main.*
  >
  > *The exact same pipeline runs via our standalone Terminal CLI Agent: `python aegis_cli.py`. With 110 passing tests, a 74.3% average token reduction (92.9% recall @ budget), and dual-track sponsor integration across Bifrost, Tavily, Omnidimension, and Pathway, AEGIS-0 delivers the enterprise gold standard for autonomous coding. Thank you."*
- **Action**: Click **`[Voice Confirm: "Approve Alpha-7"]`** $\to$ Monaco editor flashes verified green $\to$ Show Terminal window running `python aegis_cli.py --dry-run` with passing tables $\to$ Fade to final title slide.

---

## Technical Checklist for Recording Setup
- [x] Backend running on `http://localhost:8000` (`python -m uvicorn orchestrator.main:app --port 8000`)
- [x] Mission Control running on `http://localhost:3000` (`cd mission-control && npm run dev`)
- [x] Screen resolution: 1920x1080 (16:9 widescreen)
- [x] Audio input: Clear microphone input calibrated for Voice Gate demonstration
- [x] Terminal split-screen ready for `aegis_cli.py` demonstration
