# AEGIS-0: Submission Handoff & Final Submission Guide

> **Confidential Team Handoff Document**  
> **Prepared for:** `MK` (Team Lead) & Team (`PS`, `MK`, `RRS`, `MB`)  
> **Submission Deadline:** November 21, 2026 (11:59 PM IST / 18:29 UTC)  
> **Hackathon:** Geek Room & HackCulture AI Global Hackathon  

---

## 🌟 Verified Live Production Deployments
* **Live Mission Control App (Vercel):** `https://aegis-zero-core.vercel.app`
* **Live Orchestrator API (Render):** `https://aegis-zero.onrender.com`
* **Interactive Swagger API Docs:** `https://aegis-zero.onrender.com/docs`

---

## 1. Mandatory Pre-Submission Gates

Before opening either submission form, complete and verify the following gates:

- [ ] **Gate 1: Repository Visibility**  
  Confirm `https://github.com/Code-with-Prabhjot/aegis-zero` is set to **Public** on GitHub (`Settings` &rarr; `Change repository visibility` &rarr; `Make public`).
- [ ] **Gate 2: Mandatory Bifrost Repository Stars ⭐**  
  All four team members must navigate to [https://github.com/maximhq/bifrost](https://github.com/maximhq/bifrost) and click **Star ⭐**.  
  Collect the 4 exact GitHub usernames:
  - `PS` GitHub Username: `________________`
  - `MK` GitHub Username: `________________`
  - `RRS` GitHub Username: `________________`
  - `MB` GitHub Username: `________________`
- [ ] **Gate 3: Verify Automated Test Suite & Build**  
  Run locally or check GitHub Actions:
  ```bash
  .venv\Scripts\python.exe -m pytest tests/ -v
  cd mission-control && npm run build && cd ..
  ```
  Ensure all 111 tests pass (111/111 passing in Linux CI · 110 passed / 1 skipped on Windows) and frontend builds with 0 errors.

---

## 2. 3-Minute Demo Video Recording Guide

Follow the exact timestamped cues in [`docs/DEMO_SCRIPT.md`](DEMO_SCRIPT.md) (`0:00 – 3:00` / 180 seconds total).

### Launching the Environment for Recording:
- **Option A (Live Production Cloud):**  
  Open your live deployed frontend on Vercel (`https://aegis-zero-core.vercel.app`) connected to the Render backend API (`https://aegis-zero.onrender.com`).
- **Option B (Local 1-Click Launch):**  
  Run in terminal:
  - Windows: `.\start_aegis.ps1`
  - macOS/Linux: `./start_aegis.sh`  
  Mission Control will be live at `http://localhost:3000/workbench` and the FastAPI orchestrator at `http://localhost:8000`.

### Master 3-Minute Recording Cue Sheet Summary:
1. **`0:00 – 0:30` | The Agent Trilemma & Cosmic Landing Page:**  
   Introduce the fatal trilemma: 50,000+ token bloat, parametric SDK staleness, and credential injection. Click **`[Launch Mission Control]`** into the Cosmic Workbench.
2. **`0:30 – 1:05` | Stage 01 Submodular AST Knapsack Pruning (PS-01):**  
   Click **`[Run Live Agent]`** on `./orchestrator`. Highlight the 74.3% token compression (-74.4% orchestrator, -74.3% Tavily freshness, 92.9% retrieval recall @ budget) with 100% syntactically valid Python ASTs.
3. **`1:05 – 1:40` | Stage 02 Budget Ledger & Bifrost Circuit-Breaker Failover (PS-01):**  
   Drag the budget slider to show dynamic tier down-routing. Click **`[Inject HTTP 429 Outage]`** to demonstrate Bifrost's instantaneous `<180ms` (138ms measured) failover from Claude 3.5 Sonnet to GPT-4o.
4. **`1:40 – 2:20` | Stage 03 Tavily Freshness Auto-Patch (PS-06) & Adversarial Defense:**  
   Show Tavily freshness scorecard ($F(c_j) = 22$, STALE). Click **`[Apply Tavily Fresh Patch]`** to auto-upgrade legacy `openai.ChatCompletion.create`. Click **`[Test Injection Attack]`** to trigger PrivacyGuard Shannon entropy quarantine ($H \ge 4.5$) into the local air-gapped enclave.
5. **`2:20 – 3:00` | Omnidimension Voice Gate Approval, Terminal CLI & Closing:**  
   Review Monaco side-by-side diff. Vocally authorize: *"Approve Alpha-7"*. Show terminal CLI (`python aegis_cli.py --benchmark`). Fade to title slide.

Upload the finished 1080p recording to YouTube (Unlisted or Public) or Google Drive (set to *"Anyone with the link can view"*).

---

## 3. Exact Copy-Paste Fields for Mandatory Submission Forms

Both forms are mandatory and must be submitted before **November 21, 2026, 11:59 PM IST**.

### Form A: HackCulture Portal
**URL:** [https://hackculture.io/hackathons/ai-global-hackathon](https://hackculture.io/hackathons/ai-global-hackathon)

| Form Field | Exact Value to Copy-Paste |
| :--- | :--- |
| **Project Title** | `AEGIS-0: Zero-Trust Token-Optimal Autonomous Coding & Live-Verification Engine` |
| **Primary Problem Statement** | `PS-01` (Bifrost &mdash; Coding Agent on Fewest Tokens) |
| **Tavily Integration Checkbox** | **CHECKED** &check; *(Combined Project Double Win: \$1,000 cash + 60,000 Tavily credits + Maxim AI interview opportunities)* |
| **GitHub Repository URL** | `https://github.com/Code-with-Prabhjot/aegis-zero` |
| **Live Demo URL** | `https://aegis-zero-core.vercel.app` *(Live API: `https://aegis-zero.onrender.com`)* |
| **Pitch Deck File** | Upload `docs/AEGIS_0_Pitch_Deck.pdf` (8 slides, 16:9 widescreen) |
| **Demo Video Link** | `https://youtu.be/<your-video-id>` *(or Google Drive link)* |
| **Short Description** | *AEGIS-0 combines submodular AST knapsack pruning (-74.3% token reduction, 92.9% recall @ budget), Bifrost <180ms circuit-breaker failover, Tavily real-time freshness verification & auto-patching, and HMAC voice-gated authorization for zero-trust autonomous coding.* |

---

### Form B: Official Final Google Form
**URL:** [https://forms.gle/8fafao1ymEpihgKd9](https://forms.gle/8fafao1ymEpihgKd9)

| Form Field | Exact Value to Copy-Paste |
| :--- | :--- |
| **Project Title** | `AEGIS-0: Zero-Trust Token-Optimal Autonomous Coding & Live-Verification Engine` |
| **Track / Problem Statement Selection** | `PS-01` + `PS-06` Combined (Bifrost + Tavily Dual-Track) |
| **GitHub Repository URL** | `https://github.com/Code-with-Prabhjot/aegis-zero` |
| **Live Demo URL** | `https://aegis-zero-core.vercel.app` *(Live API: `https://aegis-zero.onrender.com`)* |
| **Demo Video URL** | `https://youtu.be/<your-video-id>` *(or Google Drive link)* |
| **Team Initial Roster** | `PS`, `MK`, `RRS`, `MB` |
| **Starred Bifrost GitHub Usernames** | List the 4 GitHub handles of `PS`, `MK`, `RRS`, `MB` who starred [https://github.com/maximhq/bifrost](https://github.com/maximhq/bifrost) |

---

## 4. Key Assets Reference

| Asset | Repository Path / Link |
| :--- | :--- |
| **Live Mission Control (Vercel)** | [`https://aegis-zero-core.vercel.app`](https://aegis-zero-core.vercel.app) |
| **Live Orchestrator API (Render)** | [`https://aegis-zero.onrender.com`](https://aegis-zero.onrender.com) &bull; [API Docs](https://aegis-zero.onrender.com/docs) |
| **Pitch Deck (PDF)** | [`docs/AEGIS_0_Pitch_Deck.pdf`](AEGIS_0_Pitch_Deck.pdf) |
| **Architecture Blueprint (PDF)** | [`docs/Aegis_Zero_Master_Architecture_Blueprint.pdf`](Aegis_Zero_Master_Architecture_Blueprint.pdf) |
| **Demo Recording Cue Sheet** | [`docs/DEMO_SCRIPT.md`](DEMO_SCRIPT.md) |
| **Benchmark Empirical Results** | [`docs/BENCHMARK_RESULTS.md`](BENCHMARK_RESULTS.md) |
| **Render Blueprint** | [`render.yaml`](../render.yaml) |
| **Frontend Configuration** | [`mission-control/.env.example`](../mission-control/.env.example) |
