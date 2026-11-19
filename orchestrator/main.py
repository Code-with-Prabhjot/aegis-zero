"""
AEGIS-0 Master Orchestration Engine (PS Domain Entrypoint)
FastAPI core orchestrating Zero-Trust Privacy Guard, Submodular AST Pruning,
Deterministic Budget Ledger, Resilient Bifrost Circuit Breakers,
Tavily Freshness & Stale-API Verification, and HMAC-SHA256 Cryptographic Action Gates.
"""

import asyncio
from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import os
import sys
import uuid
from typing import Dict, List, Optional, Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware

# Ensure all subpackages are resolvable on sys.path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

SECURITY_GATE_DIR = os.path.join(REPO_ROOT, "security-gate")
if SECURITY_GATE_DIR not in sys.path:
    sys.path.insert(0, SECURITY_GATE_DIR)

TAVILY_FRESHNESS_DIR = os.path.join(REPO_ROOT, "tavily-freshness")
if TAVILY_FRESHNESS_DIR not in sys.path:
    sys.path.insert(0, TAVILY_FRESHNESS_DIR)

from orchestrator.schemas import (
    ModelTier,
    ActionCategory,
    ActionApprovalRequest,
    OrchestrateRequest,
    OrchestrateResponse,
    ChaosInjectRequest,
    ActionApproveRequest,
    RedTeamRequest,
    RedTeamResponse,
)
from orchestrator import model_registry
from orchestrator.ast_pruner import ASTPruner
from orchestrator.budget_ledger import BudgetLedger
from orchestrator.bifrost_client import BifrostClient
from orchestrator.pathway_stream import StreamingASTIndex
from orchestrator.workspace import Workspace, WorkspaceError
from privacy_guard import PrivacyGuard
from freshness_engine import FreshnessEngine
from package_metadata import parse_dependency_pins
from audit_trail import TamperEvidentAuditLedger

# Model-driven expansion of stubbed symbols: rounds per request, symbols per round.
MAX_EXPANSION_ROUNDS = int(os.getenv("AEGIS_MAX_EXPANSION_ROUNDS", "2"))
MAX_EXPANSIONS_PER_ROUND = 3

EXPANSION_INSTRUCTIONS = (
    "Symbols shown as signatures ending in `: ...` are stubs: their bodies were "
    "omitted to save tokens. If you need a stub's full body to answer correctly, "
    "reply with ONLY lines of the form `EXPAND: <SymbolName>` (at most 3) and "
    "nothing else; the bodies will be sent back to you. Otherwise answer directly."
)

# Institutional Shared Secret for HMAC Cryptographic Gates.
# Only the server ever signs or verifies with this key; clients never supply it.
AEGIS_SECRET_KEY = os.getenv(
    "AEGIS_SECRET_KEY", "aegis-institutional-zero-trust-secret-2026"
)

# Quarantined actions expire if not approved within this window.
ACTION_APPROVAL_TTL_SECONDS = int(os.getenv("AEGIS_ACTION_TTL_SECONDS", "900"))

# Approved writes land in this confined workspace. Defaults to a gitignored
# sandbox so demo approvals never overwrite the project's own source files.
WORKSPACE_ROOT = os.getenv("AEGIS_WORKSPACE_ROOT") or os.path.join(REPO_ROOT, ".aegis-workspace")
WRITE_ACTIONS = ("write", "write_file", "apply_diff")

app = FastAPI(
    title="AEGIS-0 Orchestrator",
    version="2.0.0",
    description="Zero-Trust Token-Optimal Autonomous Coding & Live-Verification Engine",
)

# Enable CORS for Next.js Mission Control Workbench
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TelemetryBroadcaster:
    """
    Manages active WebSocket connections and streams live telemetry,
    token burn metrics, and failover notifications.
    """

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, event: Dict[str, Any]) -> None:
        for connection in list(self.active_connections):
            try:
                await connection.send_json(event)
            except Exception:
                self.disconnect(connection)


# Dependency Wire-up
pruner = ASTPruner()
ledger = BudgetLedger(
    default_user_budget_usd=float(os.getenv("DEFAULT_USER_BUDGET_USD", "0.50")),
    default_session_budget_usd=float(os.getenv("DEFAULT_SESSION_BUDGET_USD", "0.10")),
)
guard = PrivacyGuard()
bifrost = BifrostClient()
freshness = FreshnessEngine()
telemetry_hub = TelemetryBroadcaster()
audit_ledger = TamperEvidentAuditLedger()
stream_indexer = StreamingASTIndex(pruner=pruner)
workspace = Workspace(WORKSPACE_ROOT)

# Cumulative session tracking
total_tokens_saved_cumulative: int = 0
quarantined_actions_store: Dict[str, ActionApprovalRequest] = {}
quarantined_diff_snapshots: Dict[str, Dict[str, Any]] = {}
# Server-side record of exactly what was signed for each quarantined action:
# action_id -> {"signed_payload": str, "expires_at": datetime}
pending_action_signatures: Dict[str, Dict[str, Any]] = {}
# Action IDs whose approval has already been consumed (replay protection).
consumed_action_ids: set = set()
# Writes actually applied to the workspace, for byte-exact rollback:
# action_id -> {"target_path", "original", "patched_digest"}
applied_writes: Dict[str, Dict[str, Any]] = {}


@app.get("/healthz")
async def healthz():
    """
    Service health probe.
    """
    return {
        "status": "ok",
        "service": "aegis-0-orchestrator",
        "version": "2.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/telemetry")
async def get_telemetry():
    """
    Returns live system telemetry including cumulative tokens saved,
    active model tier, remaining budget, and circuit breaker status.
    """
    cb_status = bifrost.get_circuit_breaker_status()
    # Default to session 1 if exists, or return global ledger state
    total_spent = sum(s.cumulative_cost_usd for s in ledger.sessions.values())
    default_session = ledger.get_session("default_session")
    budget_cap = min(default_session.user_limit_usd, default_session.session_limit_usd)
    remaining_budget = max(0.0, budget_cap - default_session.cumulative_cost_usd)

    return {
        "cumulative_tokens_saved": total_tokens_saved_cumulative,
        "cumulative_cost_usd": round(total_spent, 6),
        "active_model_tier": ModelTier.TIER_2_FRONTIER.value,
        "active_model": model_registry.FRONTIER_MODEL,
        "remaining_budget_usd": round(remaining_budget, 6),
        "circuit_breaker_status": "OPEN" if cb_status.get("chaos_fault_code") else "CLOSED",
        "circuit_breaker_stats": cb_status,
        "failover_events": [ev.model_dump() for ev in bifrost.failover_events[-10:]],
        "total_requests": bifrost.total_requests,
        "total_failovers": bifrost.total_failovers,
        "stream_indexer": stream_indexer.get_telemetry(),
    }


@app.get("/api/stream/index")
async def get_stream_index_telemetry():
    """
    Returns Pathway Streaming AST Delta Engine telemetry, tracking reactive cache hits,
    delta re-parses, and file fingerprints.
    """
    return stream_indexer.get_telemetry()


@app.post("/api/chaos/inject")
async def inject_chaos(req: ChaosInjectRequest):
    """
    Chaos Simulator Hook: Triggers simulated HTTP 429/503 provider outages
    for live judge evaluations.
    """
    bifrost.inject_chaos_fault(status_code=req.status_code, target_model=req.target_model)

    audit_ledger.append_entry(
        event_type="CHAOS_INJECTED",
        actor="chaos_simulator",
        payload={"status_code": req.status_code, "target_model": req.target_model or model_registry.FRONTIER_MODEL},
    )

    event = {
        "type": "CHAOS_INJECTED",
        "status_code": req.status_code,
        "target_model": req.target_model or f"primary ({model_registry.FRONTIER_MODEL})",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await telemetry_hub.broadcast(event)

    return {
        "status": "CHAOS_INJECTED",
        "status_code": req.status_code,
        "target_model": req.target_model or model_registry.FRONTIER_MODEL,
    }


@app.post("/api/chaos/reset")
async def reset_chaos():
    """
    Clears active chaos faults and restores healthy circuit breakers.
    """
    bifrost.clear_chaos_fault()
    bifrost.reset_circuit_breakers()

    event = {
        "type": "CHAOS_RESET",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await telemetry_hub.broadcast(event)

    return {"status": "CHAOS_RESET"}


@app.post("/api/security/redteam", response_model=RedTeamResponse)
async def security_redteam(req: RedTeamRequest):
    """
    Live Adversarial Red-Team Hook: Simulates prompt injections, secret exfiltration,
    scope escape, base64 smuggling, and unicode homoglyph attacks to verify 100% containment
    and local airgap enclave locking.
    """
    result = guard.evaluate_redteam_attack(req.attack_type, req.payload)

    audit_ledger.append_entry(
        event_type="REDTEAM_ATTACK_CONTAINED",
        actor="redteam_harness",
        payload={
            "attack_type": req.attack_type,
            "defense": result["defense_triggered"],
            "entropy": result["entropy_score"],
        },
    )

    event = {
        "type": "REDTEAM_ATTACK_CONTAINED",
        "attack_type": req.attack_type,
        "defense_triggered": result["defense_triggered"],
        "entropy_score": result["entropy_score"],
        "airgap_enforced": True,
        "audit_log": result["audit_log"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await telemetry_hub.broadcast(event)
    return RedTeamResponse(**result)


@app.post("/api/orchestrate", response_model=OrchestrateResponse)
async def orchestrate(req: OrchestrateRequest):
    """
    AEGIS-0 Master Orchestration Pipeline:
    1. Zero-trust scan of repository context (auto-route to TIER_0_LOCAL if tainted).
    2. Real repo ingestion & AST call-graph pruning with 1-line stubbing (target >= 75% token reduction).
    3. Pre-call financial ledger check (down-route tier or halt if cap exceeded).
    4. Model dispatch via Bifrost with automatic circuit-breaker failover.
    5. Tavily claims extraction and empirical freshness scoring F(c_j).
    6. Action Gate check: Auto-execute reads, quarantine writes/shell with HMAC-SHA256 tokens.
    7. Realized token cost deduction in budget ledger.
    """
    global total_tokens_saved_cumulative

    session_id = req.session_id or "default_session"
    user_id = req.user_id or "default_user"

    # Register/retrieve budget state
    if session_id not in ledger.sessions:
        ledger.register_session(
            session_id=session_id,
            user_id=user_id,
            session_limit_usd=req.budget_limit_usd,
        )
    elif req.budget_limit_usd is not None:
        ledger.sessions[session_id].session_limit_usd = req.budget_limit_usd

    # Reject write targets outside the workspace before spending any tokens.
    if (req.proposed_action or "").lower() in WRITE_ACTIONS and req.proposed_target:
        try:
            workspace.resolve(req.proposed_target)
        except WorkspaceError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"TARGET_OUTSIDE_WORKSPACE: {exc}",
            )

    # --------------------------------------------------------------------------
    # Step 1: Zero-Trust Code Privacy Scan & Air-Gap Taint Engine
    # --------------------------------------------------------------------------
    privacy_tainted = False
    airgap_locked = False
    violations = []

    # Scan prompt text for secrets
    prompt_violations = guard.scan_text(req.prompt, source_label="user_prompt")
    if prompt_violations:
        privacy_tainted = True
        violations.extend(prompt_violations)

    # Scan file context if provided
    if req.file_context:
        for fname, content in req.file_context.items():
            f_violations = guard.scan_text(content, source_label=fname)
            if f_violations:
                privacy_tainted = True
                violations.extend(f_violations)

    # Resolve repo_path / repository_path
    target_repo = req.repo_path or req.repository_path
    resolved_repo = None
    if target_repo:
        if os.path.isabs(target_repo) and os.path.exists(target_repo):
            resolved_repo = target_repo
        elif os.path.exists(target_repo):
            resolved_repo = os.path.abspath(target_repo)
        elif os.path.exists(os.path.join(REPO_ROOT, target_repo.lstrip("./\\"))):
            resolved_repo = os.path.abspath(os.path.join(REPO_ROOT, target_repo.lstrip("./\\")))

    if resolved_repo and os.path.exists(resolved_repo):
        repo_result = guard.inspect_repository(resolved_repo)
        if repo_result.get("taint_status"):
            privacy_tainted = True
            violations.extend(repo_result.get("violations", []))

    if privacy_tainted:
        airgap_locked = True
        effective_tier = ModelTier.TIER_0_LOCAL
        audit_ledger.append_entry(
            event_type="TAINT_DETECTED",
            actor="privacy_guard",
            payload={"violations_count": len(violations), "routing": effective_tier.value},
        )
    else:
        effective_tier = req.target_tier or ModelTier.TIER_2_FRONTIER

    # --------------------------------------------------------------------------
    # Step 2: Submodular AST Call-Graph Pruning & 1-Line Stubbing
    # --------------------------------------------------------------------------
    raw_tokens = 0
    pruned_tokens = 0
    context_chunks = []
    ast_nodes_output: List[Dict[str, Any]] = []
    # Nodes the model may ask to expand, and those already shown in full.
    expandable_nodes: List[Any] = []
    full_node_ids: set = set()
    layout_groups: List[Any] = []  # (nodes, selected_ids) per pruned source

    if resolved_repo and os.path.exists(resolved_repo):
        all_repo_nodes, delta_metrics = stream_indexer.index_repository(resolved_repo)
        if delta_metrics.get("delta_files_reparsed", 0) > 0 or delta_metrics.get("cache_hit_count", 0) > 0:
            audit_ledger.append_entry(
                event_type="STREAM_INDEX_SYNC",
                actor="pathway_indexer",
                payload=delta_metrics,
            )

        if all_repo_nodes:
            raw_tokens = sum(n.token_cost for n in all_repo_nodes)
            seed_symbols = pruner.select_seeds(req.prompt, all_repo_nodes)

            # Calibrate budget to ensure >= 70% compression (target ~25% baseline)
            calibrated_budget = min(req.max_token_budget, max(1200, int(raw_tokens * 0.25)))
            hybrid_code, metrics = pruner.prune_context(
                nodes=all_repo_nodes,
                query=req.prompt,
                seed_symbols=seed_symbols,
                max_token_budget=calibrated_budget,
                layout="cache" if req.cache_layout else "interleaved",
            )
            pruned_tokens = metrics["total_tokens"]
            tokens_saved = metrics["tokens_saved"]
            compression_ratio = metrics["compression_ratio"]
            context_chunks.append(hybrid_code)

            selected_ids = set(metrics.get("selected_node_ids", []))
            layout_groups.append((all_repo_nodes, selected_ids))
            expandable_nodes.extend(all_repo_nodes)
            full_node_ids |= selected_ids
            for n in all_repo_nodes:
                is_sel = (n.node_type == "import" or n.node_id in selected_ids)
                ast_nodes_output.append({
                    "node_id": n.node_id,
                    "name": n.name,
                    "node_type": n.node_type,
                    "file_path": n.file_path,
                    "is_selected": is_sel,
                    "raw_tokens": n.token_cost,
                    "stub_tokens": n.stub_token_cost,
                    "raw_source": n.raw_source,
                    "stub_source": n.stub_source,
                    "dependencies": n.dependencies,
                })

    elif req.file_context:
        for fname, code in req.file_context.items():
            f_raw = pruner.count_tokens(code)
            raw_tokens += f_raw

            try:
                nodes = pruner.parse_source(fname, code)
                seed_symbols = pruner.select_seeds(req.prompt, nodes)

                pruned_code, stats = pruner.prune_context(
                    nodes=nodes,
                    query=req.prompt,
                    seed_symbols=seed_symbols,
                    max_token_budget=min(400, max(150, f_raw // 4)),
                    layout="cache" if req.cache_layout else "interleaved",
                )
                f_pruned = pruner.count_tokens(pruned_code)
                pruned_tokens += f_pruned
                context_chunks.append(f"# File: {fname}\n{pruned_code}")

                sel_ids = set(stats.get("selected_node_ids", []))
                layout_groups.append((nodes, sel_ids))
                expandable_nodes.extend(nodes)
                full_node_ids |= sel_ids
                for n in nodes:
                    ast_nodes_output.append({
                        "node_id": n.node_id,
                        "name": n.name,
                        "node_type": n.node_type,
                        "file_path": n.file_path,
                        "is_selected": (n.node_type == "import" or n.node_id in sel_ids),
                        "raw_tokens": n.token_cost,
                        "stub_tokens": n.stub_token_cost,
                        "raw_source": n.raw_source,
                        "stub_source": n.stub_source,
                        "dependencies": n.dependencies,
                    })
            except Exception:
                pruned_tokens += f_raw
                context_chunks.append(f"# File: {fname}\n{code}")
    else:
        # If no file context, use prompt tokens as baseline
        prompt_t = pruner.count_tokens(req.prompt)
        raw_tokens = prompt_t
        pruned_tokens = prompt_t

    # --------------------------------------------------------------------------
    # Context layout: build the exact messages before any budget check, so the
    # pre-flight reservation and savings metrics use the tokens actually sent.
    # --------------------------------------------------------------------------
    assembled_context = "\n\n".join(context_chunks)
    has_stubs = any(
        n.node_type != "import" and n.node_id not in full_node_ids for n in expandable_nodes
    )
    system_prompt = "You are AEGIS-0, an institutional-grade token-optimal coding agent."
    if has_stubs:
        system_prompt += "\n" + EXPANSION_INSTRUCTIONS
    prompt_cache: Dict[str, Any] = {"layout": "interleaved"}

    if req.cache_layout and layout_groups:
        # Stable, query-independent skeleton first (cacheable prefix);
        # this request's selected bodies go with the question.
        prefixes, suffixes = [], []
        for group_nodes, group_selected in layout_groups:
            p, sfx = pruner.build_cache_layout(group_nodes, group_selected)
            prefixes.append(p)
            if sfx:
                suffixes.append(sfx)
        skeleton = "\n\n".join(prefixes)
        bodies = "\n\n".join(suffixes)
        system_prompt += f"\nRepository skeleton (signatures; bodies omitted):\n{skeleton}"
        user_content = (
            f"Full source of the symbols most relevant to this request:\n{bodies}\n\nRequest: {req.prompt}"
            if bodies else req.prompt
        )
        prefix_tokens = pruner.count_tokens(system_prompt)
        # Count the context actually sent: the skeleton also carries the
        # signatures of symbols whose full bodies are in the suffix.
        pruned_tokens = pruner.count_tokens(skeleton) + pruner.count_tokens(bodies)
        prompt_cache = {
            "layout": "skeleton_prefix",
            "prefix_tokens": prefix_tokens,
            "prefix_sha256": hashlib.sha256(system_prompt.encode("utf-8")).hexdigest(),
        }
    else:
        if assembled_context:
            system_prompt += f"\nRepository Context:\n{assembled_context}"
        user_content = req.prompt

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    tokens_saved = max(0, raw_tokens - pruned_tokens)
    compression_ratio = (
        round(tokens_saved / raw_tokens, 4) if raw_tokens > 0 else 0.0
    )
    total_tokens_saved_cumulative += tokens_saved

    # --------------------------------------------------------------------------
    # Step 3: Pre-Call Token & Financial Ledger Enforcement
    # --------------------------------------------------------------------------
    estimate = ledger.compute_preflight_cost(
        session_id=session_id,
        input_tokens=max(pruned_tokens, 100),
        target_tier=effective_tier,
        max_output_tokens=1500,
    )

    state = ledger.get_session(session_id)
    budget_cap = min(state.user_limit_usd, state.session_limit_usd)
    remaining_budget = max(0.0, budget_cap - state.cumulative_cost_usd)

    if not estimate.can_dispatch:
        # Clean Hard Halt before network dispatch
        halt_event = {
            "type": "BUDGET_CAP_HALT",
            "session_id": session_id,
            "reason": estimate.halt_reason,
            "remaining_budget_usd": remaining_budget,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        audit_ledger.append_entry(
            event_type="BUDGET_CAP_HALT",
            actor="budget_ledger",
            payload=halt_event,
        )
        await telemetry_hub.broadcast(halt_event)

        return OrchestrateResponse(
            session_id=session_id,
            status="HALTED",
            model_used="none",
            model_tier=effective_tier,
            failover_occurred=False,
            failover_chain=[],
            latency_ms=0.0,
            raw_tokens=raw_tokens,
            pruned_tokens=pruned_tokens,
            tokens_saved=tokens_saved,
            compression_ratio=compression_ratio,
            cost_usd=0.0,
            budget_remaining_usd=remaining_budget,
            privacy_tainted=privacy_tainted,
            airgap_locked=airgap_locked,
            generated_code="",
            recovery_checkpoint=state.recovery_checkpoint,
            ast_nodes=ast_nodes_output,
        )

    selected_tier = estimate.selected_tier

    # --------------------------------------------------------------------------
    # Step 4: Bifrost Model Dispatch with Circuit-Breaker Failover
    # --------------------------------------------------------------------------
    dispatch_res = await bifrost.dispatch(
        messages=messages,
        budget_remaining_usd=remaining_budget,
        privacy_lock=airgap_locked,
        target_tier=selected_tier,
    )

    # --------------------------------------------------------------------------
    # Step 4b: On-Demand Symbol Expansion
    # The model may ask for the bodies of stubbed symbols instead of guessing.
    # Each round is budget-checked first and its cost committed to the ledger.
    # --------------------------------------------------------------------------
    expansions: List[Dict[str, Any]] = []
    cached_tokens_total = 0
    expansion_rounds = 0
    expansion_skipped_reason: Optional[str] = None
    turn_cost_usd = 0.0

    while expansion_rounds < MAX_EXPANSION_ROUNDS and expandable_nodes:
        requested = pruner.parse_expand_requests(dispatch_res.content, MAX_EXPANSIONS_PER_ROUND)
        if not requested:
            break
        bodies = pruner.expand_symbols(
            expandable_nodes, requested,
            exclude_ids=full_node_ids | {e["node_id"] for e in expansions},
        )
        if not bodies:
            expansion_skipped_reason = "UNKNOWN_OR_ALREADY_FULL"
            break

        body_tokens = sum(int(b["tokens"]) for b in bodies)
        next_input = dispatch_res.prompt_tokens + dispatch_res.completion_tokens + body_tokens
        # Settle the round that asked before deciding whether to pay for another.
        ledger.commit_turn_cost(
            session_id=session_id,
            actual_input_tokens=dispatch_res.prompt_tokens,
            actual_output_tokens=dispatch_res.completion_tokens,
            tier=dispatch_res.tier,
            cached_input_tokens=dispatch_res.cached_prompt_tokens,
        )
        turn_cost_usd += ledger._calculate_bound_cost(
            dispatch_res.prompt_tokens, dispatch_res.completion_tokens, dispatch_res.tier,
            dispatch_res.cached_prompt_tokens,
        )
        cached_tokens_total += dispatch_res.cached_prompt_tokens
        if not ledger.can_afford(session_id, next_input, dispatch_res.tier):
            expansion_skipped_reason = "BUDGET"
            dispatch_res.prompt_tokens = 0
            dispatch_res.completion_tokens = 0
            break

        expansion_text = "\n\n".join(
            f"# ===== {b['symbol']} ({b['file_path']}) =====\n{b['source']}" for b in bodies
        )
        messages = messages + [
            {"role": "assistant", "content": dispatch_res.content},
            {"role": "user", "content": f"Requested symbol bodies:\n{expansion_text}\n\nNow answer the original request."},
        ]
        expansions.extend({k: b[k] for k in ("symbol", "node_id", "file_path", "tokens")} for b in bodies)
        expansion_rounds += 1

        state = ledger.get_session(session_id)
        dispatch_res = await bifrost.dispatch(
            messages=messages,
            budget_remaining_usd=max(0.0, budget_cap - state.cumulative_cost_usd),
            privacy_lock=airgap_locked,
            target_tier=dispatch_res.tier,
        )

    expansion_tokens = sum(int(e["tokens"]) for e in expansions)
    if expansion_tokens:
        # Expanded bodies were sent to the model, so they don't count as saved.
        total_tokens_saved_cumulative -= min(tokens_saved, expansion_tokens)
        tokens_saved = max(0, tokens_saved - expansion_tokens)
        compression_ratio = round(tokens_saved / raw_tokens, 4) if raw_tokens > 0 else 0.0
        audit_ledger.append_entry(
            event_type="CONTEXT_EXPANDED",
            actor="orchestrator",
            payload={
                "session_id": session_id,
                "symbols": [e["symbol"] for e in expansions],
                "tokens": expansion_tokens,
                "rounds": expansion_rounds,
            },
        )

    # Strip any unanswered expansion requests so they are never treated as code.
    if pruner.parse_expand_requests(dispatch_res.content):
        dispatch_res.content = pruner.EXPAND_REQUEST.sub("", dispatch_res.content).strip()

    # --------------------------------------------------------------------------
    # Step 5: Tavily Claims Extraction, Empirical Freshness & Auto-Patch (PS-06)
    # --------------------------------------------------------------------------
    pin_root = resolved_repo if resolved_repo and os.path.isdir(resolved_repo) else REPO_ROOT
    audit_res = freshness.audit_and_patch(
        dispatch_res.content, dependency_pins=parse_dependency_pins(pin_root)
    )
    final_code = audit_res["patched_code"]
    original_code = (
        audit_res["original_code"] if audit_res["patches_applied"] else None
    )
    freshness_verifications = audit_res["verifications"]

    # --------------------------------------------------------------------------
    # Step 6: Action Gate Check (Auto-Execute Read; Quarantine Write/Shell/Git)
    # --------------------------------------------------------------------------
    action_quarantine: Optional[ActionApprovalRequest] = None
    action_status = "SUCCESS"

    # Infer proposed action from request or inspect generated content
    proposed_act = (req.proposed_action or "").lower()
    target_path = req.proposed_target or "generated_patch.py"

    is_destructive = (
        proposed_act in ("write", "write_file", "apply_diff", "shell", "exec_shell", "git", "git_commit")
        or ("write" in req.prompt.lower() and "file" in req.prompt.lower())
    )

    if is_destructive:
        category = (
            ActionCategory.SHELL
            if "shell" in proposed_act
            else ActionCategory.GIT
            if "git" in proposed_act
            else ActionCategory.WRITE
        )
        action_id = f"act_{uuid.uuid4().hex[:8]}"
        payload_hash = hashlib.sha256(final_code.encode("utf-8")).hexdigest()
        hmac_payload = f"{category.value}:{target_path}:{payload_hash}"
        hmac_token = guard.generate_hmac_action_token(
            action_id=action_id, payload=hmac_payload, secret_key=AEGIS_SECRET_KEY
        )
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=ACTION_APPROVAL_TTL_SECONDS)

        action_quarantine = ActionApprovalRequest(
            action_id=action_id,
            category=category,
            command_or_path=target_path,
            diff_payload=final_code,
            hmac_token=hmac_token,
            signed_payload=hmac_payload,
            expires_at=expires_at.isoformat(),
            is_quarantined=True,
            is_approved=False,
        )
        quarantined_actions_store[action_id] = action_quarantine
        pending_action_signatures[action_id] = {
            "signed_payload": hmac_payload,
            "expires_at": expires_at,
        }
        file_original: Optional[str] = None
        if category == ActionCategory.WRITE:
            try:
                file_original = workspace.read(target_path)
            except WorkspaceError as exc:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"TARGET_OUTSIDE_WORKSPACE: {exc}",
                )
        quarantined_diff_snapshots[action_id] = {
            "category": category,
            "target_path": target_path,
            # Pre-freshness-patch model output, for the UI's before/after diff.
            "original_code": original_code or "# Original baseline",
            "patched_code": final_code,
            # The target file's real content when quarantined (None = new file).
            "file_original": file_original,
            "file_original_digest": Workspace.digest(file_original),
        }
        action_status = "QUARANTINED"

    # --------------------------------------------------------------------------
    # Step 7: Realized Token Cost Deduction in Budget Ledger
    # --------------------------------------------------------------------------
    ledger.commit_turn_cost(
        session_id=session_id,
        actual_input_tokens=dispatch_res.prompt_tokens,
        actual_output_tokens=dispatch_res.completion_tokens,
        tier=dispatch_res.tier,
        cached_input_tokens=dispatch_res.cached_prompt_tokens,
    )
    cached_tokens_total += dispatch_res.cached_prompt_tokens
    if prompt_cache.get("layout") == "skeleton_prefix":
        prompt_cache["cached_prompt_tokens"] = cached_tokens_total
        prompt_cache["cache_hit"] = cached_tokens_total > 0

    updated_state = ledger.get_session(session_id)
    final_remaining_budget = max(
        0.0, budget_cap - updated_state.cumulative_cost_usd
    )

    # Broadcast Live Telemetry Event
    telemetry_event = {
        "type": "ORCHESTRATE_COMPLETED",
        "session_id": session_id,
        "model_used": dispatch_res.model,
        "failover_occurred": dispatch_res.failover_occurred,
        "tokens_saved": tokens_saved,
        "remaining_budget_usd": round(final_remaining_budget, 6),
        "status": action_status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await telemetry_hub.broadcast(telemetry_event)

    audit_ledger.append_entry(
        event_type="ORCHESTRATE_DECISION",
        actor="orchestrator",
        payload={
            "session_id": session_id,
            "model_used": dispatch_res.model,
            "model_tier": dispatch_res.tier.value,
            "status": action_status,
            "tokens_saved": tokens_saved,
            "action_id": action_quarantine.action_id if action_quarantine else None,
        },
    )

    return OrchestrateResponse(
        session_id=session_id,
        status=action_status,
        model_used=dispatch_res.model,
        model_tier=dispatch_res.tier,
        failover_occurred=dispatch_res.failover_occurred,
        failover_chain=dispatch_res.failover_chain,
        latency_ms=dispatch_res.latency_ms,
        raw_tokens=raw_tokens,
        pruned_tokens=pruned_tokens,
        tokens_saved=tokens_saved,
        compression_ratio=compression_ratio,
        cost_usd=round(
            turn_cost_usd
            + ledger._calculate_bound_cost(
                dispatch_res.prompt_tokens,
                dispatch_res.completion_tokens,
                dispatch_res.tier,
                dispatch_res.cached_prompt_tokens,
            ),
            6,
        ),
        budget_remaining_usd=round(final_remaining_budget, 6),
        privacy_tainted=privacy_tainted,
        airgap_locked=airgap_locked,
        generated_code=final_code,
        original_code=original_code,
        freshness_verifications=freshness_verifications,
        action_quarantine=action_quarantine,
        ast_nodes=ast_nodes_output,
        expansions=expansions,
        expansion_tokens=expansion_tokens,
        expansion_rounds=expansion_rounds,
        expansion_skipped_reason=expansion_skipped_reason,
        prompt_cache=prompt_cache,
    )


@app.post("/api/action/approve")
async def approve_action(req: ActionApproveRequest):
    """
    Validates cryptographic HMAC-SHA256 signature and executes staged action.

    Zero-trust rules, all enforced server-side:
    - Only actions this server quarantined can be approved (404 otherwise).
    - Each approval is single-use (409 on replay).
    - Approvals expire after AEGIS_ACTION_TTL_SECONDS (410 once expired).
    - The HMAC is verified with the server secret only, and the payload must be
      byte-identical to the one the server signed (403 otherwise).
    """
    if req.action_id in consumed_action_ids:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="ACTION_ALREADY_CONSUMED: This approval has already been used.",
        )

    pending = pending_action_signatures.get(req.action_id)
    if pending is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="UNKNOWN_ACTION: No quarantined action with this ID.",
        )

    if datetime.now(timezone.utc) > pending["expires_at"]:
        pending_action_signatures.pop(req.action_id, None)
        audit_ledger.append_entry(
            event_type="HMAC_REJECTED",
            actor="action_gate",
            payload={"action_id": req.action_id, "reason": "EXPIRED"},
        )
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="ACTION_EXPIRED: Approval window has closed; re-run the request.",
        )

    is_valid = (
        hmac.compare_digest(
            req.payload.encode("utf-8"), pending["signed_payload"].encode("utf-8")
        )
        and guard.verify_action_token(
            token=req.hmac_token,
            action_id=req.action_id,
            payload=req.payload,
            secret_key=AEGIS_SECRET_KEY,
        )
    )

    if not is_valid:
        audit_ledger.append_entry(
            event_type="HMAC_REJECTED",
            actor="action_gate",
            payload={"action_id": req.action_id, "reason": "INVALID_SIGNATURE"},
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="INVALID_HMAC_SIGNATURE: Action approval signature verification failed.",
        )

    snap = quarantined_diff_snapshots[req.action_id]
    is_write = snap.get("category") == ActionCategory.WRITE

    # The diff was computed against the file as it was at quarantine time. If
    # the file changed since, applying it would silently clobber those edits.
    if is_write:
        current = workspace.read(snap["target_path"])
        if Workspace.digest(current) != snap["file_original_digest"]:
            pending_action_signatures.pop(req.action_id, None)
            audit_ledger.append_entry(
                event_type="HMAC_REJECTED",
                actor="action_gate",
                payload={"action_id": req.action_id, "reason": "TARGET_CHANGED"},
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="TARGET_CHANGED: The target file changed after this action was quarantined; re-run the request.",
            )

    # Consume the approval before any side effects so it can never be replayed.
    consumed_action_ids.add(req.action_id)
    pending_action_signatures.pop(req.action_id, None)

    item = quarantined_actions_store.get(req.action_id)
    if item is not None:
        item.is_approved = True
        item.is_quarantined = False

    written_path: Optional[str] = None
    if is_write:
        workspace.write(snap["target_path"], snap["patched_code"])
        written_path = workspace.relative(snap["target_path"])
        applied_writes[req.action_id] = {
            "target_path": snap["target_path"],
            "original": snap["file_original"],
            "patched_digest": Workspace.digest(snap["patched_code"]),
        }

    # Record snapshot in audit ledger for atomic rollback
    audit_ledger.record_diff_snapshot(
        action_id=req.action_id,
        target_path=snap["target_path"],
        original_code=snap["file_original"] if snap["file_original"] is not None else "",
        patched_code=snap["patched_code"],
        actor="user_operator",
    )

    exec_status = "EXECUTED" if is_write else "APPROVED"
    audit_ledger.append_entry(
        event_type="HMAC_APPROVED",
        actor="user_operator",
        payload={
            "action_id": req.action_id,
            "status": exec_status,
            "written_path": written_path,
            "content_sha256": Workspace.digest(snap["patched_code"]) if is_write else None,
        },
    )

    approval_event = {
        "type": "ACTION_APPROVED",
        "action_id": req.action_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await telemetry_hub.broadcast(approval_event)

    return {
        "approved": True,
        "action_id": req.action_id,
        # Writes are applied to the workspace. Shell/git approvals are recorded
        # but never executed by the orchestrator.
        "status": exec_status,
        "written_path": written_path,
        "workspace_root": workspace.root if is_write else None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/api/audit/export")
async def export_audit_bundle():
    """
    Returns the full SHA-256 hash-chained audit ledger and chain_valid: true attestation.
    """
    return audit_ledger.export_compliance_bundle()


@app.post("/api/action/rollback")
async def rollback_action():
    """
    Reverts the last approved diff snapshot in memory and logs a signed
    ACTION_ROLLED_BACK entry to the audit ledger.
    """
    last = audit_ledger.peek_last_diff()
    applied = applied_writes.get(last["action_id"]) if last else None
    if applied is not None:
        current = workspace.read(applied["target_path"])
        if Workspace.digest(current) != applied["patched_digest"]:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="TARGET_MODIFIED_SINCE_APPLY: The file was edited after this action was applied; refusing to overwrite those edits.",
            )

    rollback_res = audit_ledger.rollback_last_diff(actor="user_operator")
    file_restored = False
    if rollback_res and applied is not None:
        workspace.restore(applied["target_path"], applied["original"])
        applied_writes.pop(last["action_id"], None)
        file_restored = True
    is_valid, msg = audit_ledger.verify_chain_integrity()

    if not rollback_res:
        entry = audit_ledger.append_entry(
            event_type="ACTION_ROLLED_BACK",
            actor="user_operator",
            payload={"status": "NO_PREVIOUS_DIFF", "message": "No active diff snapshots to roll back"},
        )
        return {
            "status": "ROLLED_BACK",
            "message": "No previous diff snapshots available to roll back.",
            "chain_valid": is_valid,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    event = {
        "type": "ACTION_ROLLED_BACK",
        "action_id": rollback_res["snapshot"]["action_id"],
        "target_path": rollback_res["snapshot"]["target_path"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    await telemetry_hub.broadcast(event)

    return {
        "status": "ROLLED_BACK",
        "action_id": rollback_res["snapshot"]["action_id"],
        "target_path": rollback_res["snapshot"]["target_path"],
        "reverted_record": rollback_res["reverted_record"],
        "file_restored": file_restored,
        "chain_valid": is_valid,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.websocket("/ws/telemetry")
async def websocket_telemetry(websocket: WebSocket):
    """
    WebSocket endpoint for real-time telemetry streaming to Next.js UI.
    """
    await telemetry_hub.connect(websocket)
    # Send initial telemetry snapshot on connect
    cb_status = bifrost.get_circuit_breaker_status()
    await websocket.send_json({
        "type": "INIT_TELEMETRY",
        "data": {
            "cumulative_tokens_saved": total_tokens_saved_cumulative,
            "circuit_breaker": cb_status,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    })
    try:
        while True:
            # Keep-alive receive loop
            msg = await websocket.receive_text()
            if msg == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        telemetry_hub.disconnect(websocket)
