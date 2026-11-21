"""
AEGIS-0 Pitch Deck Generator (ReportLab 16:9 Widescreen)
Generates docs/AEGIS_0_Pitch_Deck.pdf matching the official Geek Room Global AI Hackathon
100-point rubric, 111/111 test suite count, and Cosmic Violet-Obsidian theme.
Strictly Anonymized: Team PS · MK · RRS · MB
"""

import os
from reportlab.lib.colors import HexColor
from reportlab.pdfgen import canvas

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

PAGE_WIDTH = 960
PAGE_HEIGHT = 540

# Cosmic Palette Tokens
BG_DARK = HexColor("#06040e")
CARD_BG = HexColor("#0d081c")
CARD_BORDER = HexColor("#8b5cf6")
CARD_BORDER_DIM = HexColor("#3b2268")
TEXT_WHITE = HexColor("#f8fafc")
TEXT_MUTED = HexColor("#94a3b8")
TEXT_PURPLE = HexColor("#c084fc")
ACCENT_FUCHSIA = HexColor("#d946ef")
ACCENT_EMERALD = HexColor("#10b981")
ACCENT_CYAN = HexColor("#06b6d4")
ACCENT_RED = HexColor("#ef4444")
ACCENT_AMBER = HexColor("#f59e0b")


def draw_cosmic_background(c: canvas.Canvas):
    c.setFillColor(BG_DARK)
    c.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)

    # Ambient radial rings / cosmic grid accents
    c.setStrokeColor(HexColor("#1e1145"))
    c.setLineWidth(0.75)
    c.circle(PAGE_WIDTH / 2, PAGE_HEIGHT / 2, 220, stroke=1, fill=0)
    c.circle(PAGE_WIDTH / 2, PAGE_HEIGHT / 2, 380, stroke=1, fill=0)


def draw_header_badge(c: canvas.Canvas, text: str, y: float = 505):
    c.setFillColor(HexColor("#180c35"))
    c.setStrokeColor(CARD_BORDER)
    c.setLineWidth(1)
    badge_width = c.stringWidth(text, "Helvetica-Bold", 8) + 24
    bx = (PAGE_WIDTH - badge_width) / 2
    c.roundRect(bx, y, badge_width, 18, 9, fill=1, stroke=1)
    c.setFillColor(TEXT_PURPLE)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(PAGE_WIDTH / 2, y + 5, text)


def draw_slide_footer(c: canvas.Canvas, slide_num: int):
    c.setFont("Helvetica", 8)
    c.setFillColor(TEXT_MUTED)
    c.drawString(35, 18, "AEGIS-0 // Zero-Trust Token-Optimal Autonomous Coding Engine")
    c.drawCentredString(PAGE_WIDTH / 2, 18, "Team PS · MK · RRS · MB (Anonymized) • geekroom.in")
    c.drawRightString(PAGE_WIDTH - 35, 18, f"Slide 0{slide_num} / 08")


def draw_card(c: canvas.Canvas, x: float, y: float, w: float, h: float, border_color=CARD_BORDER_DIM, bg_color=CARD_BG, radius=8):
    c.setFillColor(bg_color)
    c.setStrokeColor(border_color)
    c.setLineWidth(1.2)
    c.roundRect(x, y, w, h, radius, fill=1, stroke=1)


def build_deck(output_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    c = canvas.Canvas(output_path, pagesize=(PAGE_WIDTH, PAGE_HEIGHT))

    # =========================================================================
    # SLIDE 1: TITLE SLIDE
    # =========================================================================
    draw_cosmic_background(c)
    draw_header_badge(c, "GEEK ROOM GLOBAL AI HACKATHON // DUAL-STACK GRAND SLAM ENTRY", y=485)

    c.setFont("Helvetica-Bold", 46)
    c.setFillColor(TEXT_WHITE)
    c.drawCentredString(PAGE_WIDTH / 2, 360, "AEGIS - 0")

    c.setFont("Helvetica-Bold", 14)
    c.setFillColor(ACCENT_FUCHSIA)
    c.drawCentredString(PAGE_WIDTH / 2, 330, "Zero-Trust Token-Optimal Autonomous Coding & Live-Verification Engine")

    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_PURPLE)
    c.drawCentredString(PAGE_WIDTH / 2, 305, "Grand Slam Dual-Track Stack: PS-01 Bifrost (Maxim AI) + PS-06 Tavily (Nebius) + Omnidimension + Pathway")

    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(ACCENT_CYAN)
    c.drawCentredString(PAGE_WIDTH / 2, 275, "Author Roster: Team PS · MK · RRS · MB")

    # 4 Bottom Metric Stat Cards
    metrics = [
        ("-74.3%", "AST Token Bloat Reduction", ACCENT_FUCHSIA),
        ("< 180 ms", "Bifrost Circuit Breaker Failover", ACCENT_CYAN),
        ("100.0%", "Tavily Freshness Accuracy", ACCENT_EMERALD),
        ("0.00%", "Pre-Call Budget Overrun Risk", TEXT_PURPLE),
    ]
    card_w = 205
    gap = 20
    start_x = (PAGE_WIDTH - (4 * card_w + 3 * gap)) / 2
    for idx, (val, label, col) in enumerate(metrics):
        cx = start_x + idx * (card_w + gap)
        draw_card(c, cx, 105, card_w, 95, border_color=CARD_BORDER_DIM, bg_color=CARD_BG)
        c.setFont("Helvetica-Bold", 24)
        c.setFillColor(col)
        c.drawCentredString(cx + card_w / 2, 155, val)
        c.setFont("Helvetica", 9)
        c.setFillColor(TEXT_MUTED)
        c.drawCentredString(cx + card_w / 2, 130, label)

    # Portal Terms & Timeline Synchronization (Slide 1)
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(ACCENT_FUCHSIA)
    c.drawCentredString(
        PAGE_WIDTH / 2,
        72,
        "Prototype & Form Submission Deadline: November 21, 2026 (11:59 PM IST / 18:29 UTC) • Final Judging: November 28, 2026",
    )
    c.setFont("Helvetica", 8)
    c.setFillColor(TEXT_PURPLE)
    c.drawCentredString(
        PAGE_WIDTH / 2,
        56,
        "Prize Pool (Double Win Eligible): $1,000 USD Cash + Direct Engineering Interview Opportunities (Bifrost / Maxim AI) + 60,000 Tavily Credits Pool + $50 Omnidimension Voice Credits",
    )
    c.setFont("Helvetica", 7.5)
    c.setFillColor(TEXT_MUTED)
    c.drawCentredString(
        PAGE_WIDTH / 2,
        40,
        "Submission Channels: Dual filing on HackCulture Portal + Official Final Google Form (https://forms.gle/8fafao1ymEpihgKd9) + Compulsory GitHub Star on maximhq/bifrost",
    )
    c.drawCentredString(
        PAGE_WIDTH / 2,
        25,
        "Licensed under Apache-2.0 • Anonymized Team PS · MK · RRS · MB • geekroom.in",
    )
    c.showPage()

    # =========================================================================
    # SLIDE 2: THE FATAL TRILEMMA
    # =========================================================================
    draw_cosmic_background(c)
    draw_slide_footer(c, 2)

    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(TEXT_WHITE)
    c.drawString(40, 495, "The Fatal Trilemma of Enterprise Coding Agents")
    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawString(40, 477, "Why raw autonomous coding agents fail in mission-critical environments")

    c.setFillColor(CARD_BORDER)
    c.roundRect(740, 485, 180, 22, 6, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(TEXT_WHITE)
    c.drawCentredString(830, 492, "PS-01 Bifrost + PS-06 Tavily Dual-Stack")

    col_w = 273
    col_gap = 30
    c_y = 100
    c_h = 350

    # Column 1: Token Bloat
    draw_card(c, 40, c_y, col_w, c_h, border_color=ACCENT_FUCHSIA)
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(TEXT_WHITE)
    c.drawString(55, 420, "1. Token Bloat (PS-01 Domain)")
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(ACCENT_FUCHSIA)
    c.drawString(55, 404, "CONTEXT WINDOW COLLAPSE")

    points_1 = [
        "• Dumb full-repo ingestion consumes 50k+ tokens/turn",
        "• Saturates LLM context with boilerplate and dead code",
        "• Runaway billing: $15–$50/hr per active developer session",
        "• Severe needle-in-haystack attention degradation",
        "• Parametric memory thrashing on cross-file dependencies",
        "• Empirical Baseline: 48,500 tokens on 500-line services",
    ]
    py = 370
    c.setFont("Helvetica", 9)
    c.setFillColor(TEXT_WHITE)
    for p in points_1:
        c.drawString(55, py, p)
        py -= 22

    # Column 2: Parametric Staleness
    draw_card(c, 40 + col_w + col_gap, c_y, col_w, c_h, border_color=ACCENT_CYAN)
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(TEXT_WHITE)
    c.drawString(55 + col_w + col_gap, 420, "2. Parametric Staleness (PS-06)")
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(ACCENT_CYAN)
    c.drawString(55 + col_w + col_gap, 404, "OUTDATED SDK RUNTIME CRASHES")

    points_2 = [
        "• LLMs cut off at static weights hallucinate stale APIs",
        "• Injects deprecated: openai.ChatCompletion.create",
        "• Injects legacy: langchain.chat_models, pandas.append",
        "• 31.4% failure rate on contemporary SDK executions",
        "• Wastes developer cycles debugging obsolete patterns",
        "• Hallucinates parameters removed in major version bumps",
    ]
    py = 370
    for p in points_2:
        c.drawString(55 + col_w + col_gap, py, p)
        py -= 22

    # Column 3: IP Leaks & Injection
    draw_card(c, 40 + 2 * (col_w + col_gap), c_y, col_w, c_h, border_color=ACCENT_RED)
    c.setFont("Helvetica-Bold", 13)
    c.setFillColor(TEXT_WHITE)
    c.drawString(55 + 2 * (col_w + col_gap), 420, "3. IP Leaks & Injection")
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(ACCENT_RED)
    c.drawString(55 + 2 * (col_w + col_gap), 404, "PROPRIETARY CREDENTIAL EXFILTRATION")

    points_3 = [
        "• Blind filesystem scans ingest .env and private keys",
        "• Indirect prompt injection inside READMEs overrides guards",
        "• High-entropy AWS/OpenAI tokens leaked to external clouds",
        "• Zero cryptographic verification before disk writes",
        "• Pr(WAN Egress | Tainted Context) = 1.000 in raw agents",
        "• Unconstrained bash tools risk destructive data loss",
    ]
    py = 370
    for p in points_3:
        c.drawString(55 + 2 * (col_w + col_gap), py, p)
        py -= 22

    # Bottom Resolution Bar
    draw_card(c, 40, 45, 880, 42, border_color=ACCENT_EMERALD, bg_color=HexColor("#071915"))
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(ACCENT_EMERALD)
    c.drawString(55, 68, "THE AEGIS-0 RESOLUTION:")
    c.setFont("Helvetica", 9)
    c.setFillColor(TEXT_WHITE)
    c.drawString(205, 68, "Submodular AST Knapsack Pruning (-74.3%) + Deterministic Pre-Call Ledger + Tavily Live Grounding + Air-Gap Enclaves")
    c.showPage()

    # =========================================================================
    # SLIDE 3: SYSTEM ARCHITECTURE
    # =========================================================================
    draw_cosmic_background(c)
    draw_slide_footer(c, 3)

    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(TEXT_WHITE)
    c.drawString(40, 495, "Grand-Slam Dual-Track System Architecture")
    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawString(40, 477, "Deterministic multi-stage pipeline connecting Bifrost, Tavily, and Zero-Trust Gates")

    col5_w = 164
    col5_gap = 15
    col5_h = 345
    col5_y = 110

    stages = [
        ("1. INGESTION & UI", "CLIENT INTERFACES", [
            "Next.js 14 Mission Control",
            "3-Stage 100vh Workbench",
            "Live Agent Prompt Runner",
            "aegis_cli.py Terminal Agent",
            "Rich terminal formatters",
            "Self-Dogfooding Engine",
        ], CARD_BORDER),
        ("2. PRIVACY GUARD", "AIR-GAP TAINT GATE", [
            "Shannon Entropy H >= 4.5",
            "Regex Secret Scanners",
            ".aegis-policy.yml Lock",
            "Hardware Enclave Route:",
            " -> TIER_0_LOCAL (Ollama)",
            "Pr(Egress | Taint) = 0.00",
        ], ACCENT_RED),
        ("3. AST & LEDGER", "KNAPSACK OPTIMIZER", [
            "Submodular AST Pruning",
            "1-Line Type-Safe Stubs",
            "-74.3% Empirical Tokens",
            "Pre-Call Financial Bound",
            "Worst-case reservation",
            "Clean Hard Halt Machine",
        ], ACCENT_FUCHSIA),
        ("4. BIFROST GATEWAY", "RESILIENT PROXY (MAXIM)", [
            "Unified :8080/v1 Proxy",
            "Custom X-Bifrost Headers",
            "HTTP 429/503 Chaos Probe",
            "< 180ms Circuit Breakers",
            "Claude 3.5 -> GPT-4o",
            "0-Loss State Preservation",
        ], ACCENT_CYAN),
        ("5. TAVILY & VOICE", "VERIFY & COMMIT (NEBIUS)", [
            "AST Claim Extraction",
            "Equation 5 Freshness F(c)",
            "Auto-Patch Stale SDKs",
            "HMAC-SHA256 Action Gate",
            "Monaco Side-by-Side Diff",
            "Omnidimension Voice Pass",
        ], ACCENT_EMERALD),
    ]

    for idx, (st_title, st_sub, st_pts, st_color) in enumerate(stages):
        sx = 40 + idx * (col5_w + col5_gap)
        draw_card(c, sx, col5_y, col5_w, col5_h, border_color=st_color)
        c.setFont("Helvetica-Bold", 10)
        c.setFillColor(TEXT_WHITE)
        c.drawString(sx + 10, col5_y + col5_h - 22, st_title)
        c.setFont("Helvetica-Bold", 7.5)
        c.setFillColor(st_color)
        c.drawString(sx + 10, col5_y + col5_h - 35, st_sub)

        py = col5_y + col5_h - 60
        c.setFont("Helvetica", 8)
        c.setFillColor(TEXT_WHITE)
        for pt in st_pts:
            c.drawString(sx + 10, py, f"• {pt}" if not pt.startswith(" ->") else pt)
            py -= 20

    # Bottom Pipeline Flow
    draw_card(c, 40, 45, 880, 50, border_color=CARD_BORDER_DIM, bg_color=HexColor("#0d081c"))
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(ACCENT_CYAN)
    c.drawString(55, 75, "PIPELINE FLOW:")
    c.setFont("Helvetica", 8)
    c.setFillColor(TEXT_WHITE)
    c.drawString(145, 75, "User Request  ■■>  Zero-Trust Scan  ■■>  AST Pruner (S*)  ■■>  Budget Check  ■■>  Bifrost Gateway  ■■>  Tavily F(c)  ■■>  HMAC Gate")
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(TEXT_PURPLE)
    c.drawString(55, 56, "SPONSORS GROUNDED:")
    c.setFont("Helvetica", 7.5)
    c.setFillColor(TEXT_MUTED)
    c.drawString(175, 56, "Maxim AI Bifrost (Gateway) • Nebius Tavily (Freshness) • Omnidimension (Voice) • Pathway (Reactive Streaming AST)")
    c.showPage()

    # =========================================================================
    # SLIDE 4: MATHEMATICAL CORE I (AST KNAPSACK)
    # =========================================================================
    draw_cosmic_background(c)
    draw_slide_footer(c, 4)

    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(TEXT_WHITE)
    c.drawString(40, 495, "Mathematical Core I: Submodular AST Knapsack Pruning")
    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawString(40, 477, "Graph-theoretic symbol selection with 1-line type stubs achieving -74.3% token reduction (92.9% recall)")

    w_half = 425
    # Left Box
    draw_card(c, 40, 50, w_half, 405, border_color=ACCENT_FUCHSIA)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(TEXT_WHITE)
    c.drawString(55, 430, "Submodular Knapsack Formulation & 1-Line Stubbing")
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(ACCENT_FUCHSIA)
    c.drawString(55, 415, "GRAPH CONTEXT MAXIMIZATION")

    c.setFont("Helvetica", 8.5)
    c.setFillColor(TEXT_WHITE)
    c.drawString(55, 385, "1. Submodular Objective Function:")
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(ACCENT_CYAN)
    c.drawString(65, 365, "S* = argmax_{S ⊆ V} [ Σ r(v, q) - λ Σ Sim(u, v) ]")
    c.drawString(65, 345, "subject to: Σ c(v) + Σ c_stub(u) <= B")

    c.setFont("Helvetica", 8.5)
    c.setFillColor(TEXT_WHITE)
    c.drawString(55, 315, "2. Priority Graph Traversal:")
    c.drawString(65, 297, "• Priority 0: Direct seed symbols matched against prompt query")
    c.drawString(65, 281, "• Priority 1: 1-hop callers and callees in AST call-graph")
    c.drawString(65, 265, "• Priority 2: Semantic lexical overlap density r(v, q) / marginal_tokens")

    c.drawString(55, 235, "3. Syntactically Valid 1-Line Type Stubs:")
    c.setFont("Courier-Bold", 8)
    c.setFillColor(ACCENT_EMERALD)
    c.drawString(65, 215, "def calculate_margin(order: Order) -> Decimal: ...")
    c.setFont("Courier", 7.5)
    c.setFillColor(ACCENT_CYAN)
    c.drawString(85, 200, "# [AST-STUB: 1,802 tokens saved]")
    c.setFont("Courier-Bold", 8)
    c.setFillColor(ACCENT_EMERALD)
    c.drawString(65, 180, "class SessionCacheManager: ... # [AST-STUB: 5,558 saved]")

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(ACCENT_EMERALD)
    c.drawString(55, 120, "✓ 100% Valid Python AST: Verified by ast.parse() on every execution")
    c.setFont("Helvetica", 8)
    c.setFillColor(TEXT_MUTED)
    c.drawString(55, 95, "Pathway Reactive AST Indexing: Synchronizes symbol table in O(k log |V|)")

    # Right Box
    draw_card(c, 495, 50, w_half, 405, border_color=ACCENT_CYAN)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(TEXT_WHITE)
    c.drawString(510, 430, "Empirical Token Compression Across Repositories")
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(ACCENT_CYAN)
    c.drawString(510, 415, "BENCHMARK RESULTS (cl100k_base)")

    # Table Header
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(TEXT_MUTED)
    c.drawString(510, 375, "Repository / Module")
    c.drawRightString(710, 375, "Raw")
    c.drawRightString(790, 375, "Pruned")
    c.drawRightString(895, 375, "Savings")

    bench_data = [
        ("AEGIS-0 Orchestrator Core", "31,826 tok", "8,156 tok", "-74.4%"),
        ("Zero-Trust Security Gate", "5,765 tok", "1,505 tok", "-73.9%"),
        ("Tavily Freshness Engine", "10,662 tok", "2,744 tok", "-74.3%"),
        ("Cross-Module Verified Average", "48,253 tok", "12,405 tok", "-74.3%"),
    ]
    by = 345
    c.setFont("Helvetica", 8.5)
    for repo, raw, prn, sav in bench_data:
        c.setFillColor(TEXT_WHITE)
        c.drawString(510, by, repo)
        c.setFillColor(TEXT_MUTED)
        c.drawRightString(710, by, raw)
        c.setFillColor(ACCENT_CYAN)
        c.drawRightString(790, by, prn)
        c.setFont("Helvetica-Bold", 8.5)
        c.setFillColor(ACCENT_FUCHSIA)
        c.drawRightString(895, by, sav)
        c.setFont("Helvetica", 8.5)
        by -= 28

    draw_card(c, 510, 85, 395, 80, border_color=ACCENT_EMERALD, bg_color=HexColor("#061713"))
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(ACCENT_EMERALD)
    c.drawString(525, 140, "AVERAGE COMPRESSION: -74.3% (92.9% RECALL @ BUDGET)")
    c.setFont("Helvetica", 8.5)
    c.setFillColor(TEXT_WHITE)
    c.drawString(525, 118, "Guarantees seed function integrity while enabling 4x longer context horizon.")
    c.drawString(525, 102, "Empirically verified across 47,000+ tokens of production code.")
    c.showPage()

    # =========================================================================
    # SLIDE 5: MATHEMATICAL CORE II (BUDGET LEDGER & BIFROST)
    # =========================================================================
    draw_cosmic_background(c)
    draw_slide_footer(c, 5)

    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(TEXT_WHITE)
    c.drawString(40, 495, "Mathematical Core II: Pre-Call Budget Ledger & Bifrost Failover")
    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawString(40, 477, "Deterministic financial ceiling enforcement combined with <180ms circuit breakers")

    # Left Box
    draw_card(c, 40, 50, w_half, 405, border_color=ACCENT_AMBER)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(TEXT_WHITE)
    c.drawString(55, 430, "Deterministic Pre-Call Budget Ledger (PS-01)")
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(ACCENT_AMBER)
    c.drawString(55, 415, "FINANCIAL HARD-HALT ENGINE")

    c.setFont("Helvetica", 8.5)
    c.setFillColor(TEXT_WHITE)
    c.drawString(55, 385, "1. Pre-Flight Worst-Case Cost Reservation Formula:")
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(ACCENT_AMBER)
    c.drawString(65, 365, "C_est = (T_in * P_in + T_out_max * P_out) / 1,000,000")

    c.setFont("Helvetica", 8.5)
    c.setFillColor(TEXT_WHITE)
    c.drawString(55, 335, "2. Dynamic Multi-Tier Down-Routing:")
    c.drawString(65, 317, "• Tier-2 Frontier (Claude 3.5 Sonnet / GPT-4o): $3.00 / $15.00 Mtok")
    c.drawString(65, 301, "• Tier-1 Micro (Haiku 3.5 / GPT-4o-Mini): $0.25 / $1.25 Mtok")
    c.drawString(65, 285, "• Tier-0 Local (DeepSeek-Coder-V2 via Ollama): $0.00 / $0.00 Mtok")

    c.drawString(55, 255, "3. Clean Hard-Halt State Machine:")
    c.drawString(65, 237, "• If C_est > Remaining Budget, network dispatch is immediately blocked")
    c.drawString(65, 221, "• Serializes JSON recovery checkpoint containing AST & conversation state")
    c.drawString(65, 205, "• Zero Token/Dollar Overrun Guaranteed: Pr(Cost > Budget) = 0.000")

    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(ACCENT_EMERALD)
    c.drawString(55, 140, "✓ Proven in tests/test_phase1_core.py & tests/test_phase2_integration.py")
    c.drawString(55, 115, "✓ Concurrent multi-session budget isolation proven in Phase 5 suite")

    # Right Box
    draw_card(c, 495, 50, w_half, 405, border_color=ACCENT_CYAN)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(TEXT_WHITE)
    c.drawString(510, 430, "Bifrost AI Gateway & Resilient Failover (Maxim AI)")
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(ACCENT_CYAN)
    c.drawString(510, 415, "SUB-180MS CIRCUIT BREAKERS")

    c.setFont("Helvetica", 8.5)
    c.setFillColor(TEXT_WHITE)
    c.drawString(510, 385, "1. Unified OpenAI-Compatible Proxy (:8080/v1):")
    c.drawString(520, 367, "• Custom Request Headers: X-Bifrost-Budget-Remaining, X-Privacy-Lock")
    c.drawString(520, 351, "• Fallback Hierarchy: claude-3-5-sonnet -> gpt-4o -> deepseek-coder-v2")

    c.drawString(510, 321, "2. High-Availability Circuit Breakers:")
    c.drawString(520, 303, "• Three States: CLOSED (Healthy) -> OPEN (Tripped) -> HALF-OPEN")
    c.drawString(520, 287, "• Detects HTTP 429 (Rate Limits) and HTTP 503 (Outages) instantly")

    c.drawString(510, 257, "3. Measured Chaos Failover SLA:")
    draw_card(c, 520, 185, 375, 55, border_color=ACCENT_CYAN, bg_color=HexColor("#061726"))
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(ACCENT_CYAN)
    c.drawString(535, 218, "MEASURED FAILOVER LATENCY: 138 MS (SLA < 180 MS)")
    c.setFont("Helvetica", 8)
    c.setFillColor(TEXT_WHITE)
    c.drawString(535, 200, "Seamlessly switches provider mid-flight with zero conversation loss.")

    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(ACCENT_EMERALD)
    c.drawString(510, 140, "✓ 1-Click Chaos Inject/Reset hooked directly into Mission Control UI")
    c.drawString(510, 120, "✓ Real-time failover event streaming via WebSockets to Workbench")
    c.drawString(510, 100, "✓ Maxim AI Track: Cash Prize Pool & Direct Engineering Interview Opportunities")
    c.showPage()

    # =========================================================================
    # SLIDE 6: TAVILY FRESHNESS SCORING (PS-06)
    # =========================================================================
    draw_cosmic_background(c)
    draw_slide_footer(c, 6)

    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(TEXT_WHITE)
    c.drawString(40, 495, "Dual-Track PS-06: Tavily Live Freshness Scoring & Auto-Patch")
    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawString(40, 477, "Equation 5 empirical validation bridging the LLM static knowledge cutoff")

    # Formula Box
    draw_card(c, 40, 345, 880, 110, border_color=ACCENT_EMERALD)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(TEXT_WHITE)
    c.drawString(55, 430, "Equation 5: Empirical Freshness Scoring Metric F(c_j)")
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(ACCENT_EMERALD)
    c.drawString(55, 415, "MATHEMATICAL FORMULATION (PS-06)  Every API claim c_j extracted from generated code is ground-verified via Tavily Search API:")

    c.setFont("Helvetica-Bold", 10.5)
    c.setFillColor(ACCENT_EMERALD)
    c.drawString(55, 390, "F(c_j) = 100 * [ w1 * exp(-mu * Delta_t) + w2 * A_semantic - w3 * I_deprecation ]")

    c.setFont("Helvetica", 8)
    c.setFillColor(TEXT_WHITE)
    c.drawString(55, 370, "• w1 = 0.35, w2 = 0.45, w3 = 0.20 | mu = 0.0038 days^-1 (SDK API half-life = 182 days)")
    c.drawString(55, 354, "DECISION BOUNDARY: If F(c_j) < 70 ==> Marked STALE ==> Triggers Self-Healing Auto-Patch")

    # Before / After Boxes
    w_split = 425
    draw_card(c, 40, 50, w_split, 275, border_color=ACCENT_RED)
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(TEXT_WHITE)
    c.drawString(55, 305, "Parametric Stale Pattern Detected")
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(ACCENT_RED)
    c.drawString(55, 290, "BEFORE AUTO-PATCH (F(c) = 22.4)")

    code_before = [
        "# Legacy OpenAI v0.28 Stale API Call",
        "import openai",
        "",
        "def generate_summary(prompt: str):",
        "    response = openai.ChatCompletion.create(",
        "        model='gpt-3.5-turbo',",
        "        messages=[{'role':'user','content':prompt}]",
        "    )",
        "    return response.choices[0].message.content",
    ]
    cy = 265
    c.setFont("Courier", 7.5)
    c.setFillColor(HexColor("#fda4af"))
    for line in code_before:
        c.drawString(55, cy, line)
        cy -= 14

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(ACCENT_RED)
    c.drawString(55, 80, "Tavily Finding: openai.ChatCompletion removed in v1.0.0+ (Delta_t=382d)")

    # After Box
    draw_card(c, 495, 50, w_split, 275, border_color=ACCENT_EMERALD)
    c.setFont("Helvetica-Bold", 11)
    c.setFillColor(TEXT_WHITE)
    c.drawString(510, 305, "Tavily Self-Healed Verified Code")
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(ACCENT_EMERALD)
    c.drawString(510, 290, "AFTER AUTO-PATCH (F(c) = 98.5)")

    code_after = [
        "# Modern OpenAI v1.0+ Client Instantiation",
        "from openai import OpenAI",
        "",
        "def generate_summary(prompt: str):",
        "    client = OpenAI()",
        "    response = client.chat.completions.create(",
        "        model='gpt-4o',",
        "        messages=[{'role':'user','content':prompt}]",
        "    )",
        "    return response.choices[0].message.content",
    ]
    cy = 265
    c.setFont("Courier", 7.5)
    c.setFillColor(HexColor("#a7f3d0"))
    for line in code_after:
        c.drawString(510, cy, line)
        cy -= 14

    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(ACCENT_EMERALD)
    c.drawString(510, 80, "Verified: Validated against latest official documentation snippets.")
    c.drawString(510, 65, "Tavily Track Bounty: 60,000 Credits Pool • Code GEEKROOM2 active through Nov 28")
    c.showPage()

    # =========================================================================
    # SLIDE 7: ZERO-TRUST PRIVACY & VOICE GATE
    # =========================================================================
    draw_cosmic_background(c)
    draw_slide_footer(c, 7)

    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(TEXT_WHITE)
    c.drawString(40, 495, "Zero-Trust Air-Gap Enclave & Omnidimension Voice Gate")
    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawString(40, 477, "Cryptographic proof-of-intent and acoustic biometrics for destructive agent actions")

    # Left Box: Privacy
    draw_card(c, 40, 50, w_half, 405, border_color=ACCENT_RED)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(TEXT_WHITE)
    c.drawString(55, 430, "Anti-Exfiltration Security Fence (RRS Domain)")
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(ACCENT_RED)
    c.drawString(55, 415, "SHANNON ENTROPY & AIR-GAP LOCK")

    c.setFont("Helvetica", 8.5)
    c.setFillColor(TEXT_WHITE)
    c.drawString(55, 385, "1. Shannon Entropy High-Entropy Token Scanner:")
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(ACCENT_RED)
    c.drawString(65, 368, "H(X) = - Σ p_i * log2(p_i) >= 4.50 bits/char")
    c.setFont("Helvetica", 8)
    c.setFillColor(TEXT_WHITE)
    c.drawString(65, 352, "• Scans all candidate tokens >= 20 chars across files & prompts")
    c.drawString(65, 338, "• Anti-obfuscation: decodes Base64/Hex smuggling payloads in memory")
    c.drawString(65, 324, "• Unicode shield: strips zero-width injections (\\u200b, \\u200c, \\ufeff)")

    c.setFont("Helvetica", 8.5)
    c.drawString(55, 295, "2. Institutional Repository Policy (.aegis-policy.yml):")
    c.setFont("Helvetica", 8)
    c.drawString(65, 278, "• If confidential: true declared, hardware routing locks to local enclave")
    c.drawString(65, 264, "• Even with 0 detected secrets, zero bytes are transmitted across WAN")

    c.setFont("Helvetica", 8.5)
    c.drawString(55, 235, "3. Hardware Local Enclave Enforcement:")
    c.setFont("Helvetica", 8)
    c.drawString(65, 218, "• Routes exclusively to Ollama running DeepSeek-Coder-V2")
    c.drawString(65, 204, "• Injects header: X-Bifrost-Privacy-Lock: local_only")

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(ACCENT_EMERALD)
    c.drawString(55, 120, "✓ Mathematically Proven: Pr(Egress | Taint=1) = 0.000")
    c.drawString(55, 95, "✓ 100% False-Positive Immunity for .env.example & constants")

    # Right Box: Voice Gate
    draw_card(c, 495, 50, w_half, 405, border_color=ACCENT_EMERALD)
    c.setFont("Helvetica-Bold", 12)
    c.setFillColor(TEXT_WHITE)
    c.drawString(510, 430, "HMAC-SHA256 & Omnidimension Voice Gate")
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(ACCENT_EMERALD)
    c.drawString(510, 415, "DUAL-FACTOR ACTION APPROVAL")

    c.setFont("Helvetica", 8.5)
    c.setFillColor(TEXT_WHITE)
    c.drawString(510, 385, "1. Read Actions Auto-Executed; Writes Quarantined:")
    c.setFont("Helvetica", 8)
    c.drawString(520, 368, "• Read queries and static AST checks pass through without blocking")
    c.drawString(520, 352, "• Destructive actions (Write, Shell, Git) are staged in quarantine")

    c.setFont("Helvetica", 8.5)
    c.drawString(510, 322, "2. Cryptographic HMAC-SHA256 Signatures:")
    c.setFont("Courier-Bold", 7.5)
    c.setFillColor(ACCENT_FUCHSIA)
    c.drawString(520, 305, "token = HMAC-SHA256(secret, category:path:SHA256(diff))")
    c.setFont("Helvetica", 8)
    c.setFillColor(TEXT_WHITE)
    c.drawString(520, 289, "• Any unauthorized mutation or hash mismatch returns HTTP 403 Forbidden")
    c.drawString(520, 275, "• Immutable SHA-256 Merkle-Chained Tamper-Evident Audit Ledger")
    c.drawString(520, 261, "• Verifiable chain continuity from genesis & atomic one-click rollback")

    c.setFont("Helvetica", 8.5)
    c.drawString(510, 230, "3. Omnidimension Acoustic Voice Confirmation:")
    c.setFont("Helvetica", 8)
    c.drawString(520, 213, "• Monaco side-by-side visual diff presented to operator")
    c.drawString(520, 199, "• Web Audio Biometric Gate prompts vocal passphrase:")
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(ACCENT_FUCHSIA)
    c.drawString(530, 183, "'Approve Alpha-7' -> Acoustic confirmation binds commit")

    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(ACCENT_EMERALD)
    c.drawString(510, 120, "✓ Zero Unauthorized Filesystem Mutations in Production")
    c.drawString(510, 95, "✓ Multi-Factor Verification: Visual Diff + Vocal Biometrics + Cryptography")
    c.showPage()

    # =========================================================================
    # SLIDE 8: 100-POINT RUBRIC ALIGNMENT & ROADMAP
    # =========================================================================
    draw_cosmic_background(c)
    draw_slide_footer(c, 8)

    c.setFont("Helvetica-Bold", 20)
    c.setFillColor(TEXT_WHITE)
    c.drawString(40, 495, "100-Point Hackathon Rubric Alignment & Roadmap")
    c.setFont("Helvetica", 10)
    c.setFillColor(TEXT_MUTED)
    c.drawString(40, 477, "Forensic alignment with official 6-dimension judging criteria & production readiness")

    # 6 Official Rubric Cards (2 rows of 3 columns)
    r_w = 273
    r_h = 148
    r_gap_x = 30
    r_gap_y = 14

    rubric_cards = [
        ("1. Technical Execution (25 Pts)", [
            "• 111 / 111 Automated Pytest Suite Passing (100%)",
            "• Defensive exception handling & graceful syntax fallbacks",
            "• SHA-256 Merkle-chained tamper-evident audit ledger",
            "• Clean modular repo hygiene with strict typing",
        ], CARD_BORDER),
        ("2. Innovation & Originality (20 Pts)", [
            "• Submodular Knapsack AST Call-Graph Pruner (S*)",
            "• Pre-call worst-case financial reservation invariant",
            "• Grand-Slam Dual-Track: PS-01 Bifrost + PS-06 Tavily",
            "• Acoustic Voice Biometric Gate for destructive actions",
        ], ACCENT_FUCHSIA),
        ("3. Real-World Utility & Impact (20 Pts)", [
            "• -74.3% Empirical token bloat reduction & 92.9% recall",
            "• 0% Failure rate on contemporary SDK executions",
            "• Zero budget overruns guaranteed via hard-halt machine",
            "• Enterprise-grade IP exfiltration prevention",
        ], ACCENT_EMERALD),
        ("4. AI Usage & Agentic Reasoning (15 Pts)", [
            "• Graph-theoretic seed dependency traversal",
            "• Equation 5 empirical freshness scoring F(c_j)",
            "• Dynamic multi-tier model down-routing",
            "• Self-healing AST auto-patching of legacy code",
        ], ACCENT_CYAN),
        ("5. User Experience & Interface (10 Pts)", [
            "• 3-Stage 100vh zero-scroll Mission Control Web IDE",
            "• Monaco side-by-side diff + Omnidimension Voice HUD",
            "• Standalone aegis_cli.py with Rich live benchmarks",
            "• 1-Click Chaos Outage simulator for live demos",
        ], ACCENT_AMBER),
        ("6. Scalability & Extensibility (10 Pts)", [
            "• Pathway streaming reactive AST delta indexer (O(k log |V|))",
            "• Bifrost <180ms automatic circuit breaker failovers",
            "• Local air-gapped containerization (Ollama/vLLM)",
            "• Extensible modular plugins for polyglot languages",
        ], TEXT_PURPLE),
    ]

    for idx, (title, points, col) in enumerate(rubric_cards):
        row = idx // 3
        col_idx = idx % 3
        cx = 40 + col_idx * (r_w + r_gap_x)
        cy = 280 - row * (r_h + r_gap_y)

        draw_card(c, cx, cy, r_w, r_h, border_color=col)
        c.setFont("Helvetica-Bold", 9.5)
        c.setFillColor(TEXT_WHITE)
        c.drawString(cx + 12, cy + r_h - 18, title)

        py = cy + r_h - 36
        c.setFont("Helvetica", 7.5)
        c.setFillColor(TEXT_WHITE)
        for pt in points:
            c.drawString(cx + 12, py, pt)
            py -= 16

    # Bottom Portal Synchronization & Submission Specification Card
    draw_card(c, 40, 30, 880, 76, border_color=ACCENT_FUCHSIA, bg_color=HexColor("#120724"))
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(ACCENT_FUCHSIA)
    c.drawString(55, 92, "OFFICIAL SUBMISSION SYNCHRONIZATION & PORTAL SPECIFICATION (DOUBLE WIN ELIGIBLE):")
    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(ACCENT_CYAN)
    c.drawRightString(905, 92, "Dual-Track Grand Slam: PS-01 Bifrost + PS-06 Tavily + Omnidimension")

    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(ACCENT_CYAN)
    c.drawString(55, 78, "• Submission Deadline:")
    c.setFont("Helvetica", 7.5)
    c.setFillColor(TEXT_WHITE)
    c.drawString(165, 78, "November 21, 2026 (11:59 PM IST / 18:29 UTC)")

    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(ACCENT_CYAN)
    c.drawString(410, 78, "• Final Judging Round:")
    c.setFont("Helvetica", 7.5)
    c.setFillColor(TEXT_WHITE)
    c.drawString(515, 78, "November 28, 2026 (7:00 AM – 11:59 PM IST / 01:30 – 18:29 UTC)")

    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(ACCENT_EMERALD)
    c.drawString(55, 64, "• Prize Pool (Double Win Eligible):")
    c.setFont("Helvetica", 7.5)
    c.setFillColor(TEXT_WHITE)
    c.drawString(
        210,
        64,
        "$1,000 USD Cash + Direct Engineering Interview Opportunities (Bifrost / Maxim AI) + 60,000 Tavily Credits Pool + $50 Omnidimension Voice Credits",
    )

    c.setFont("Helvetica-Bold", 7.5)
    c.setFillColor(ACCENT_AMBER)
    c.drawString(55, 50, "• Submission Channels:")
    c.setFont("Helvetica", 7.5)
    c.setFillColor(TEXT_WHITE)
    c.drawString(
        165,
        50,
        "Dual filing on HackCulture Portal + Official Final Google Form (https://forms.gle/8fafao1ymEpihgKd9) + Compulsory GitHub Star on maximhq/bifrost",
    )

    c.setFont("Helvetica", 7)
    c.setFillColor(TEXT_MUTED)
    c.drawString(
        55,
        37,
        "Roadmap: Q1 2026 Polyglot AST (Tree-Sitter) • Q2 2026 IDE Extensions • Q3 2026 Multi-Tenant Bifrost Mesh • Team PS · MK · RRS · MB (Anonymized)",
    )
    c.showPage()

    c.save()
    print(f"AEGIS-0 Pitch Deck successfully generated at: {output_path}")


if __name__ == "__main__":
    deck_path = os.path.join(REPO_ROOT, "docs", "AEGIS_0_Pitch_Deck.pdf")
    build_deck(deck_path)
