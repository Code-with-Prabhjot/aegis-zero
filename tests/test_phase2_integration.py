"""
AEGIS-0 Phase 2 Integration Test Suite
Verifies:
1. test_bifrost_circuit_breaker_failover: Simulates HTTP 429 outage and verifies sub-180ms switch to secondary model.
2. test_tavily_freshness_scoring_and_autopatch: Injects deprecated SDK pattern, validates F(c) < 70, and confirms auto-patch.
3. test_end_to_end_orchestrate_pipeline: Executes /api/orchestrate through pruner, budget, gateway, freshness, quarantine.
4. test_action_approval_gate_lifecycle: Validates quarantined write payload rejection on invalid token and execution on valid HMAC.
5. test_zero_trust_airgap_lock_on_tainted_context: Verifies automatic lockdown to TIER_0_LOCAL when secrets/taint detected.
6. test_orchestrator_budget_cap_hard_halt: Verifies clean hard halt prior to dispatch when budget cap is breached.
"""

import ast
import asyncio
import hashlib
import os
import sys
import tempfile
import pytest
from fastapi.testclient import TestClient

# Ensure repo root and sub-modules are on Python path
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
    CircuitBreakerState,
)
from orchestrator.bifrost_client import BifrostClient
from freshness_engine import (
    FreshnessEngine,
    extract_code_claims,
    verify_claim_freshness,
    auto_patch_code,
)
from privacy_guard import PrivacyGuard
from orchestrator.main import app, bifrost, ledger, AEGIS_SECRET_KEY
from tests.test_phase1_core import SAMPLE_200_LINE_SOURCE


# Large sample code for AST pruning integration
SAMPLE_PRUNING_SOURCE = '''"""
High-Frequency Trading FIX Protocol Order Routing Engine
"""
from typing import Dict, List, Optional
from decimal import Decimal
import time
import math


class MarketDataStreamer:
    """Consumes L3 orderbook feeds and calculates VWAP."""
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.bids: Dict[Decimal, Decimal] = {}
        self.asks: Dict[Decimal, Decimal] = {}

    def update_book(self, side: str, price: Decimal, qty: Decimal) -> None:
        if side == "bid":
            self.bids[price] = qty
        else:
            self.asks[price] = qty

    def get_midpoint(self) -> Decimal:
        if not self.bids or not self.asks:
            return Decimal("0.0")
        best_bid = max(self.bids.keys())
        best_ask = min(self.asks.keys())
        return (best_bid + best_ask) / Decimal("2.0")


class RiskGovernor:
    """Pre-trade risk compliance and capital allocation checks."""
    def __init__(self, max_notional_usd: Decimal = Decimal("500000.0")):
        self.max_notional_usd = max_notional_usd
        self.current_exposure = Decimal("0.0")

    def check_margin_limit(self, order_notional: Decimal) -> bool:
        projected = self.current_exposure + order_notional
        return projected <= self.max_notional_usd

    def record_fill(self, fill_notional: Decimal) -> None:
        self.current_exposure += fill_notional


class OrderRouter:
    """Core DMA routing engine connecting to exchange matching engines."""
    def __init__(self, risk_governor: RiskGovernor):
        self.risk = risk_governor
        self.seq_num = 0

    def calculate_margin(self, order_qty: Decimal, unit_price: Decimal) -> Decimal:
        """Calculates margin requirement with haircut."""
        notional = order_qty * unit_price
        haircut = Decimal("0.15")
        return notional * (Decimal("1.0") + haircut)

    def route_order(self, symbol: str, side: str, qty: Decimal, price: Decimal) -> Dict:
        notional = qty * price
        if not self.risk.check_margin_limit(notional):
            return {"status": "REJECTED", "reason": "RISK_MARGIN_EXCEEDED"}
        self.seq_num += 1
        return {
            "status": "ROUTED",
            "clordid": f"ORD_{symbol}_{self.seq_num}",
            "notional": notional,
        }
'''


# ==============================================================================
# 1. Bifrost Circuit Breaker & Failover Test
# ==============================================================================
def test_bifrost_circuit_breaker_failover():
    """
    Simulates HTTP 429 Rate Limit outage on primary model (Claude 3.5 Sonnet)
    and verifies sub-180ms automatic failover to secondary model (GPT-4o)
    with zero loss of conversation context or AST state.
    """
    async def _run():
        client = BifrostClient(mock_mode=True)
        messages = [
            {"role": "system", "content": "You are AEGIS-0 coding assistant."},
            {"role": "user", "content": "Write a high-performance Fibonacci generator."},
        ]

        # Baseline call: Primary model (Claude 3.5 Sonnet) succeeds
        baseline_resp = await client.dispatch(messages=messages)
        assert baseline_resp.model == "claude-opus-5-5"
        assert baseline_resp.failover_occurred is False
        assert client.breakers["claude-opus-5-5"].state == CircuitBreakerState.CLOSED

        # Inject Chaos Fault: HTTP 429 on Claude 3.5 Sonnet
        client.inject_chaos_fault(status_code=429, target_model="claude-opus-5-5")

        # Dispatch: Should trip primary breaker and failover to GPT-4o in <180ms
        failover_resp = await client.dispatch(messages=messages)

        # 1. Verification of target model switch to secondary
        assert failover_resp.model == "gpt-5.6", f"Expected secondary model gpt-5.6, got {failover_resp.model}"
        assert failover_resp.tier == ModelTier.TIER_2_FRONTIER
        assert failover_resp.failover_occurred is True
        assert "claude-opus-5-5" in failover_resp.failover_chain

        # 2. SLA Verification: Switch must occur in < 180 ms
        assert failover_resp.latency_ms < 180.0, f"Failover SLA breached: {failover_resp.latency_ms} ms >= 180 ms"

        # 3. State verification: Primary breaker must be OPEN
        assert client.breakers["claude-opus-5-5"].state == CircuitBreakerState.OPEN
        assert len(client.failover_events) >= 1
        recent_event = client.failover_events[-1]
        assert recent_event.from_model == "claude-opus-5-5"
        assert recent_event.to_model == "gpt-5.6"
        assert recent_event.status_code == 429
        assert recent_event.latency_ms < 180.0

        # 4. Content preservation: Generated code must still be returned
        assert "fibonacci" in failover_resp.content.lower()
        assert failover_resp.total_tokens > 0

        # 5. Clear chaos fault and reset breakers
        client.clear_chaos_fault()
        client.reset_circuit_breakers()
        assert client.breakers["claude-opus-5-5"].state == CircuitBreakerState.CLOSED

        recovery_resp = await client.dispatch(messages=messages)
        assert recovery_resp.model == "claude-opus-5-5"
        assert recovery_resp.failover_occurred is False

    asyncio.run(_run())


# ==============================================================================
# 2. Tavily Freshness Scoring & Auto-Patch Test (PS-06)
# ==============================================================================
def test_tavily_freshness_scoring_and_autopatch():
    """
    Injects known deprecated SDK patterns (e.g. openai.ChatCompletion.create),
    validates that Empirical Freshness Score F(c_j) < 70,
    and confirms automatic self-healing code patch generation.
    """
    engine = FreshnessEngine()

    legacy_code = (
        "import openai\n\n"
        "def generate_summary(prompt: str) -> str:\n"
        "    response = openai.ChatCompletion.create(\n"
        "        model='gpt-3.5-turbo',\n"
        "        messages=[{'role': 'user', 'content': prompt}]\n"
        "    )\n"
        "    return response.choices[0].message.content\n"
    )

    # 1. Claims extraction via AST / regex
    claims = engine.extract_code_claims(legacy_code)
    claim_names = [c["claim"] for c in claims]
    assert "openai.ChatCompletion.create" in claim_names

    # 2. Verify freshness score calculation F(c_j) using Equation 5
    # w1 = 0.35, w2 = 0.45, w3 = 0.20, mu = 0.0038
    verification = engine.verify_claim_freshness("openai.ChatCompletion.create")

    assert verification["is_stale"] is True
    assert verification["status"] == "STALE"
    assert verification["freshness_score"] < 70.0, f"Expected F(c) < 70, got {verification['freshness_score']}"
    assert verification["deprecation_indicator"] == 1
    assert verification["patch"] is not None

    # 3. Verify patch payload
    patch = verification["patch"]
    assert patch["deprecated_pattern"] == "openai.ChatCompletion.create"
    assert "client.chat.completions.create" in patch["replacement_pattern"]
    assert len(verification["documentation_snippets"]) > 0

    # 4. Auto-patch execution
    audit_result = engine.audit_and_patch(legacy_code)
    patched_code = audit_result["patched_code"]

    assert "openai.ChatCompletion.create" not in patched_code
    assert "client.chat.completions.create" in patched_code
    assert "OpenAI" in patched_code
    assert len(audit_result["patches_applied"]) >= 1

    # 5. Syntactic validity of self-healed code
    parsed = ast.parse(patched_code)
    assert parsed is not None, "Auto-patched code must be valid Python AST syntax"

    # 6. Verify modern API scores >= 70 (FRESH)
    modern_verification = engine.verify_claim_freshness("client.chat.completions.create")
    assert modern_verification["is_stale"] is False
    assert modern_verification["status"] == "FRESH"
    assert modern_verification["freshness_score"] >= 70.0


# ==============================================================================
# 3. End-to-End Orchestrate Pipeline Test
# ==============================================================================
def test_end_to_end_orchestrate_pipeline():
    """
    Executes POST /api/orchestrate through all 7 pipeline stages:
    1. Zero-trust scan (untainted -> Frontier tier)
    2. AST call-graph pruning (>= 75% token reduction)
    3. Pre-call financial check (reserves worst-case margin)
    4. Bifrost dispatch
    5. Tavily claim extraction & verification
    6. Destructive write action quarantine with HMAC-SHA256 token
    7. Budget cost commitment
    """
    bifrost.mock_mode = True
    bifrost.clear_chaos_fault()
    bifrost.reset_circuit_breakers()

    client = TestClient(app)

    session_id = "test-e2e-pipeline-session"
    payload = {
        "session_id": session_id,
        "user_id": "architect_lead",
        "prompt": "Format execution report with format_execution_report under FIX protocol and write patch to report.py",
        "file_context": {
            "report.py": SAMPLE_200_LINE_SOURCE,
        },
        "target_tier": "tier-2-frontier",
        "budget_limit_usd": 0.50,
        "proposed_action": "write_file",
        "proposed_target": "report.py",
    }

    response = client.post("/api/orchestrate", json=payload)
    assert response.status_code == 200

    data = response.json()

    # 1. Status & Routing
    assert data["session_id"] == session_id
    assert data["status"] == "QUARANTINED"
    assert data["model_used"] in ("claude-opus-5-5", "gpt-5.6")
    assert data["model_tier"] == "tier-2-frontier"
    assert data["privacy_tainted"] is False
    assert data["airgap_locked"] is False

    # 2. Token compression >= 75% on multi-class sample
    assert data["raw_tokens"] > 0
    assert data["pruned_tokens"] < data["raw_tokens"]
    assert data["tokens_saved"] > 0
    assert (
        data["compression_ratio"] >= 0.75
    ), f"Expected >= 75% token reduction, got {data['compression_ratio'] * 100:.1f}%"

    # 3. Action Quarantine
    quarantine = data["action_quarantine"]
    assert quarantine is not None
    assert quarantine["category"] == "write"
    assert quarantine["command_or_path"] == "report.py"
    assert quarantine["is_quarantined"] is True
    assert quarantine["is_approved"] is False
    assert len(quarantine["hmac_token"]) == 64  # SHA-256 hex length

    # 4. Budget Ledger Deduction
    assert data["cost_usd"] > 0.0
    assert data["budget_remaining_usd"] < 0.50

    # 5. Telemetry endpoint verification
    telem_res = client.get("/api/telemetry")
    assert telem_res.status_code == 200
    telem = telem_res.json()
    assert telem["cumulative_tokens_saved"] > 0
    assert telem["total_requests"] >= 1


# ==============================================================================
# 4. Cryptographic Action Approval Gate Lifecycle Test
# ==============================================================================
def test_action_approval_gate_lifecycle():
    """
    Validates that quarantined write/shell payloads cannot execute without
    a cryptographically valid HMAC-SHA256 signature, and execute cleanly when approved.
    """
    client = TestClient(app)
    bifrost.mock_mode = True
    bifrost.clear_chaos_fault()
    bifrost.reset_circuit_breakers()

    file_path = "sensitive_service.py"
    orch = client.post(
        "/api/orchestrate",
        json={
            "session_id": "test_gate_lifecycle",
            "prompt": "write security patch to sensitive_service.py",
            "proposed_action": "write_file",
            "proposed_target": file_path,
        },
    )
    assert orch.status_code == 200
    quarantine = orch.json()["action_quarantine"]
    action_id = quarantine["action_id"]
    valid_token = quarantine["hmac_token"]
    hmac_payload = quarantine["signed_payload"]
    payload_hash = hashlib.sha256(orch.json()["generated_code"].encode("utf-8")).hexdigest()
    assert hmac_payload == f"write:{file_path}:{payload_hash}"

    # 1. Negative Test: Forged / Tampered HMAC signature must return 403 Forbidden
    forged_token = "deadbeef" * 8
    reject_res = client.post(
        "/api/action/approve",
        json={
            "action_id": action_id,
            "hmac_token": forged_token,
            "payload": hmac_payload,
            "target_path": file_path,
        },
    )
    assert reject_res.status_code == 403
    assert "INVALID_HMAC_SIGNATURE" in reject_res.json()["detail"]

    # 2. Negative Test: Tampered payload with valid token must also be rejected
    tampered_payload = f"write:{file_path}:tampered_hash_123"
    reject_tamper_res = client.post(
        "/api/action/approve",
        json={
            "action_id": action_id,
            "hmac_token": valid_token,
            "payload": tampered_payload,
            "target_path": file_path,
        },
    )
    assert reject_tamper_res.status_code == 403

    # 3. Positive Test: Valid cryptographic HMAC approval executes cleanly
    approve_res = client.post(
        "/api/action/approve",
        json={
            "action_id": action_id,
            "hmac_token": valid_token,
            "payload": hmac_payload,
            "target_path": file_path,
        },
    )
    assert approve_res.status_code == 200
    data = approve_res.json()
    assert data["approved"] is True
    assert data["action_id"] == action_id
    assert data["status"] == "EXECUTED"


# ==============================================================================
# 5. Zero-Trust Air-Gap Lock on Tainted Context Test
# ==============================================================================
def test_zero_trust_airgap_lock_on_tainted_context():
    """
    Validates that any prompt or code containing proprietary secrets / AWS keys
    is automatically locked to TIER_0_LOCAL (DeepSeek-Coder-V2) air-gapped enclave.
    """
    bifrost.mock_mode = True
    bifrost.clear_chaos_fault()
    bifrost.reset_circuit_breakers()

    client = TestClient(app)

    # Inject high-entropy AWS secret key
    tainted_prompt = "Refactor database query with key AKIAIOSFODNN7EXAMPLE and aws_secret_access_key='wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY'"

    payload = {
        "session_id": "test-taint-session",
        "prompt": tainted_prompt,
        "target_tier": "tier-2-frontier",  # Attempt to request frontier model
    }

    response = client.post("/api/orchestrate", json=payload)
    assert response.status_code == 200
    data = response.json()

    # Must be air-gap locked to TIER_0_LOCAL
    assert data["privacy_tainted"] is True
    assert data["airgap_locked"] is True
    assert data["model_tier"] == "tier-0-local"
    assert data["model_used"] == "deepseek-coder-v2"


# ==============================================================================
# 6. Budget Cap Hard Halt Test
# ==============================================================================
def test_orchestrator_budget_cap_hard_halt():
    """
    Validates that when session budget cap is exceeded, the orchestrator halts cleanly
    without network dispatch and provides a serialized recovery checkpoint.
    """
    bifrost.mock_mode = True
    client = TestClient(app)

    session_id = "test-budget-halt-session"
    # Extremely low budget of $0.0001
    payload = {
        "session_id": session_id,
        "prompt": "Write a distributed microservice architecture with complete unit tests.",
        "target_tier": "tier-2-frontier",
        "budget_limit_usd": 0.0001,
    }

    response = client.post("/api/orchestrate", json=payload)
    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "HALTED"
    assert data["recovery_checkpoint"] is not None
    assert data["cost_usd"] == 0.0
    assert data["generated_code"] == ""


# ==============================================================================
# 7. WebSocket Live Telemetry Stream Test
# ==============================================================================
def test_websocket_telemetry_stream():
    """
    Validates live bi-directional WebSocket connection on /ws/telemetry,
    verifying initial telemetry push and heartbeat ping/pong.
    """
    client = TestClient(app)
    with client.websocket_connect("/ws/telemetry") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "INIT_TELEMETRY"
        assert "circuit_breaker" in msg["data"]

        ws.send_text("ping")
        reply = ws.receive_text()
        assert reply == "pong"


# ==============================================================================
# 8. Chaos Simulator REST Endpoints Test
# ==============================================================================
def test_chaos_api_endpoints():
    """
    Validates POST /api/chaos/inject and POST /api/chaos/reset endpoints.
    """
    client = TestClient(app)

    # 1. Inject Chaos Outage
    inj_res = client.post("/api/chaos/inject", json={"status_code": 503})
    assert inj_res.status_code == 200
    assert inj_res.json()["status"] == "CHAOS_INJECTED"
    assert inj_res.json()["status_code"] == 503

    # Check telemetry reflects chaos fault
    telem = client.get("/api/telemetry").json()
    assert telem["circuit_breaker_stats"]["chaos_fault_code"] == 503

    # 2. Reset Chaos Outage
    reset_res = client.post("/api/chaos/reset")
    assert reset_res.status_code == 200
    assert reset_res.json()["status"] == "CHAOS_RESET"

    # Check telemetry reflects cleared chaos
    telem_after = client.get("/api/telemetry").json()
    assert telem_after["circuit_breaker_stats"]["chaos_fault_code"] is None

