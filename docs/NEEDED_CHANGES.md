# AEGIS-0: Needed Changes Before Submission

**Written:** Nov 19, 2026, from a review of `main` at `28650c5`
**Deadline:** Nov 21, 2026, 11:59 PM IST (judging Nov 28)

## Current state

| Check | Result |
|---|---|
| `pytest` (needs `pip install -r orchestrator/requirements.txt`) | 35/35 pass |
| `mission-control`: `tsc --noEmit` and `npm run build` | Both succeed |
| `python aegis_cli.py --benchmark` | Average **-76.8%** (docs claim -84.2%) |

---

## P0: Accuracy fixes (quick, do first)

Judges who run the code will see these numbers, so they need to match the docs.

### 1. The benchmark marks misses as passes
- **File:** `aegis_cli.py:384`
- **Bug:** the check is `comp >= 0.70`, but the label says `OPTIMAL (>=75%)`. Right now 70.2% (`./security-gate`) and 74.7% (`./orchestrator`) are both shown as OPTIMAL.
- **Fix:** change the threshold to `0.75`. Then either accept that two modules show SUB-OPTIMAL, or improve the pruning (item 2).

### 2. The headline numbers don't match the current code
Measured today against what the docs claim:

| Module | Claimed | Measured |
|---|---|---|
| `./orchestrator` | 14,474 → 3,595 (-75.2%) | 18,010 → 4,557 (-74.7%) |
| `./security-gate` | n/a | 5,178 → 1,544 (-70.2%) |
| `./tavily-freshness` | n/a | 4,989 → 425 (-91.5%) |
| **Average** | **-84.2%** | **-76.8%** |

- **Option A (fastest):** update every claim to the measured numbers.
- **Option B:** tune the pruner's token budget in `orchestrator/ast_pruner.py` so every module clears 75%, then re-measure and update the docs.
- **Places the numbers appear:**
  - `README.md` lines 9, 34, 60, 114, 250, 251
  - `docs/DEMO_SCRIPT.md` lines 29, 68
  - `scripts/build_pitch_deck.py` lines 98, 244, 285, 352, 415, 439, 750. After editing, rebuild `docs/AEGIS_0_Pitch_Deck.pdf`.
- If "48,500 → 7,660" (the README benchmark table, line 250, and deck line 415) wasn't measured with this code, remove it or label it as a projection.

### 3. The demo script contradicts itself
- `docs/DEMO_SCRIPT.md` says **75.2%** in segment 2 and **84.2%** in segment 5. Use one number throughout, measured live.

---

## P1: Demo features that are simulated

The demo video presents these as real. Each one should either be made real or be described honestly.

### 4. Voice approval is faked
- **File:** `mission-control/src/components/Panel4_MonacoVoiceGate.tsx:123-145`
- **What happens now:** a `setTimeout` waits 1.6 s and then shows "ACOUSTIC MATCH 99.8% - VERIFIED". Nothing listens to the microphone and nothing calls Omnidimension.
- **Fix (a few hours):** use the browser's Web Speech API (`webkitSpeechRecognition`), match the transcript against "approve alpha 7" (allow spelling variants), and approve only on a match. Keep a fallback button for browsers that don't support it. Wire it to Omnidimension if there's time.
- Remove the made-up "99.8%" score, or show the recognizer's real confidence.

### 5. Model calls are mocked
- `aegis_cli.py:79` hard-codes `BifrostClient(mock_mode=True)`.
- `orchestrator/bifrost_client.py:332` and `:442` silently fall back to canned responses when the gateway isn't running.
- **Fix:**
  - Add a `--live` flag to the CLI.
  - Log a clear `[MOCK]` warning whenever the fallback is used.
  - Run `gateway-infra/docker-compose.yml` once with real keys and record a real outage and fallback, so the "138 ms failover" figure is backed by a measurement.

### 6. Tavily runs offline by default
- `orchestrator/.env.example` ships `TAVILY_API_KEY=tvly-demo-key`. `tavily-freshness/freshness_engine.py:305` treats that as "use local rules".
- **Fix:** record the demo with a real key (the hackathon provides 60k credits), and show the live source URLs in the Tavily scorecard panel.
- Add a line to the README explaining that a real key is needed for live checks.

### 7. "Pathway" isn't the Pathway library
- `orchestrator/pathway_stream.py` calls itself "Pathway-inspired" and never imports `pathway`. It's a custom indexer.
- **Fix:** either integrate `pathway` for real (add it to `requirements.txt`), or describe it as a "Pathway-style reactive indexer" in the README, deck and demo script. Don't claim a sponsor integration that isn't there.

---

## P2: Cleanup (if time allows)

### 8. Outdated model names
- `claude-3-5-sonnet`, `gpt-4o` and `gpt-4o-mini` appear in:
  - `orchestrator/bifrost_client.py:83-90, 262`
  - `orchestrator/main.py:147, 178, 184, 192`
  - `README.md:36, 213`
  - the frontend panels
- Update them to current models. Put the names in one config constant instead of repeating them in several files.

### 9. Duplicate Tavily folders
- `tavily_freshness/` exists only to point at `tavily-freshness/` by editing `sys.path`.
- **Fix:** rename `tavily-freshness/` to `tavily_freshness/`, delete the redirect, and update the imports. Do the same check for `security-gate/` if it's imported the same way.

### 10. Test dependency warning
- A newer `httpx` warns that its use in the FastAPI test client is deprecated. Pin `httpx<0.28` in `orchestrator/requirements.txt`, or follow the version the warning recommends.

### 11. No automated checks
- Add `.github/workflows/ci.yml` that runs `pytest` and `npm ci && npm run build` in `mission-control/`. This backs up the "35/35 passing" README badge, which currently links to `https://github.com` instead of a real build.
- Ignore `mission-control/tsconfig.tsbuildinfo` in `.gitignore`. The build creates it and it currently shows up as untracked.

---

## Suggested order

| When | Items |
|---|---|
| Nov 19 (today) | 1, 2 (Option A), 3, 9, 11 |
| Nov 20 | 4 (real voice), 6 (real Tavily key), 5 (`--live` flag and one real gateway run) |
| Nov 21 (morning) | 7, 8, rebuild the deck PDF, record the demo, submit before 11:59 PM IST |
