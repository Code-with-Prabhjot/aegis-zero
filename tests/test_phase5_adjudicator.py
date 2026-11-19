"""
AEGIS-0 Phase 5 Hackathon Adjudicator & Stress Hardening Test Suite
Verifies:
1. Multi-session financial budget isolation (concurrent session integrity).
2. Pathway reactive streaming AST cache and incremental delta updates.
3. Multi-library simultaneous stale API detection and auto-patching.
4. Bifrost multi-level circuit breaker failover chain resilience.
5. Cryptographic audit ledger Merkle continuity after atomic rollback.
6. Standalone CLI benchmark, audit-export, rollback, and verify-integrity execution.
7. FastAPI Pathway streaming index telemetry endpoint (/api/stream/index).
"""

import ast
import os
import subprocess
import sys
import tempfile
import pytest
from fastapi.testclient import TestClient

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

SECURITY_GATE_DIR = os.path.join(REPO_ROOT, "security-gate")
if SECURITY_GATE_DIR not in sys.path:
    sys.path.insert(0, SECURITY_GATE_DIR)

TAVILY_DIR = os.path.join(REPO_ROOT, "tavily-freshness")
if TAVILY_DIR not in sys.path:
    sys.path.insert(0, TAVILY_DIR)

from orchestrator.schemas import ModelTier
from orchestrator.main import app, bifrost, AEGIS_SECRET_KEY
from orchestrator.budget_ledger import BudgetLedger
from orchestrator.ast_pruner import ASTPruner
from orchestrator.pathway_stream import StreamingASTIndex
from freshness_engine import FreshnessEngine
from audit_trail import TamperEvidentAuditLedger


# ==============================================================================
# 1. Multi-Session Financial Budget Isolation Test
# ==============================================================================
def test_multi_session_budget_isolation():
    """
    Guarantees strict mathematical isolation between separate user and session budgets.
    Deductions in Session A must never drain liquidity from Session B.
    """
    ledger = BudgetLedger(default_user_budget_usd=1.00, default_session_budget_usd=0.20)

    # Register two concurrent sessions
    session_a = ledger.register_session(session_id="session_alpha", session_limit_usd=0.05)
    session_b = ledger.register_session(session_id="session_beta", session_limit_usd=0.50)

    assert session_a.cumulative_cost_usd == 0.0
    assert session_b.cumulative_cost_usd == 0.0

    # Commit heavy token cost in Session A that breaches its $0.05 limit
    ledger.commit_turn_cost(
        session_id="session_alpha",
        actual_input_tokens=10000,
        actual_output_tokens=3000,
        tier=ModelTier.TIER_2_FRONTIER,
    )

    state_a = ledger.get_session("session_alpha")
    state_b = ledger.get_session("session_beta")

    # Session A must be halted
    assert state_a.is_halted is True
    assert state_a.cumulative_cost_usd > 0.05

    # Session B must remain completely intact and unhalted with 0 spend
    assert state_b.is_halted is False
    assert state_b.cumulative_cost_usd == 0.0
    assert state_b.session_limit_usd == 0.50

    # Pre-flight check on Session B must still be approved
    estimate_b = ledger.compute_preflight_cost(
        session_id="session_beta",
        input_tokens=500,
        target_tier=ModelTier.TIER_2_FRONTIER,
    )
    assert estimate_b.can_dispatch is True


# ==============================================================================
# 2. Pathway Reactive Streaming AST Cache & Incremental Delta Test
# ==============================================================================
def test_pathway_streaming_ast_cache_and_delta_update():
    """
    Validates Pathway reactive stream indexing:
    - Parses files into cache.
    - Modifies a single file and verifies ONLY that file is reparsed (delta update).
    - Unmodified files produce cache hits with zero reparsing.
    - Deleted files are evicted cleanly.
    """
    pruner = ASTPruner()
    stream_indexer = StreamingASTIndex(pruner=pruner)

    with tempfile.TemporaryDirectory() as temp_dir:
        file1 = os.path.join(temp_dir, "service_a.py")
        file2 = os.path.join(temp_dir, "service_b.py")

        with open(file1, "w", encoding="utf-8") as f:
            f.write("def compute_tax(amount: float) -> float:\n    return amount * 0.15\n")

        with open(file2, "w", encoding="utf-8") as f:
            f.write("from service_a import compute_tax\ndef generate_invoice() -> float:\n    return compute_tax(100.0)\n")

        # Initial indexing run
        nodes_initial, metrics_initial = stream_indexer.index_repository(temp_dir)
        assert len(nodes_initial) >= 2
        assert metrics_initial["added_count"] == 2
        assert metrics_initial["cache_hit_count"] == 0
        assert metrics_initial["delta_files_reparsed"] == 2

        # Second indexing run without file changes (100% cache hit)
        nodes_cached, metrics_cached = stream_indexer.index_repository(temp_dir)
        assert len(nodes_cached) == len(nodes_initial)
        assert metrics_cached["added_count"] == 0
        assert metrics_cached["modified_count"] == 0
        assert metrics_cached["cache_hit_count"] == 2
        assert metrics_cached["delta_files_reparsed"] == 0

        # Modify ONLY file1
        with open(file1, "w", encoding="utf-8") as f:
            f.write("def compute_tax(amount: float) -> float:\n    return amount * 0.20 # UPDATED\n")

        nodes_modified, metrics_mod = stream_indexer.index_repository(temp_dir)
        assert metrics_mod["modified_count"] == 1
        assert metrics_mod["cache_hit_count"] == 1
        assert metrics_mod["delta_files_reparsed"] == 1

        # Delete file2
        os.remove(file2)
        nodes_after_del, metrics_del = stream_indexer.index_repository(temp_dir)
        assert metrics_del["deleted_count"] == 1
        assert len(nodes_after_del) == 1
        assert nodes_after_del[0].name == "compute_tax"


# ==============================================================================
# 3. Multi-Library Simultaneous Stale API Detection & Auto-Patching Test
# ==============================================================================
def test_tavily_multi_library_simultaneous_autopatch():
    """
    Verifies that a code snippet containing deprecated patterns across multiple libraries
    (both legacy openai.ChatCompletion AND langchain.chat_models) is audited and healed
    in a single pass with valid Python AST syntax.
    """
    engine = FreshnessEngine()

    multi_stale_code = """
import openai
from langchain.chat_models import ChatOpenAI

def execute_multi_agent_workflow(prompt: str):
    llm = ChatOpenAI(temperature=0.0)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content
"""
    result = engine.audit_and_patch(multi_stale_code)

    assert result["all_fresh"] is False
    assert len(result["patches_applied"]) >= 2
    patched_code = result["patched_code"]

    # Verify both legacy patterns replaced
    assert "openai.ChatCompletion.create" not in patched_code
    assert "client.chat.completions.create" in patched_code
    assert "from langchain.chat_models import ChatOpenAI" not in patched_code
    assert "from langchain_openai import ChatOpenAI" in patched_code

    # Verify 100% syntactically valid Python
    parsed = ast.parse(patched_code)
    assert parsed is not None


# ==============================================================================
# 4. Bifrost Multi-Level Circuit Breaker Failover Resilience Test
# ==============================================================================
@pytest.mark.anyio
async def test_bifrost_circuit_breaker_multi_model_failover_resilience():
    """
    Tests cascading failover across provider tiers when primary provider experiences
    HTTP 429/503 outages, measuring failover latency SLA < 180ms.
    """
    client = bifrost
    client.reset_circuit_breakers()
    client.clear_chaos_fault()

    # Normal healthy call
    res_healthy = await client.dispatch(
        messages=[{"role": "user", "content": "Ping"}],
        budget_remaining_usd=0.50,
        privacy_lock=False,
        target_tier=ModelTier.TIER_2_FRONTIER,
    )
    assert res_healthy.failover_occurred is False
    assert res_healthy.model == "claude-opus-5-5"

    # Inject HTTP 429 outage on primary
    client.inject_chaos_fault(status_code=429, target_model="claude-opus-5-5")

    res_failover = await client.dispatch(
        messages=[{"role": "user", "content": "Ping under chaos"}],
        budget_remaining_usd=0.50,
        privacy_lock=False,
        target_tier=ModelTier.TIER_2_FRONTIER,
    )

    assert res_failover.failover_occurred is True
    assert res_failover.model == "gpt-5.6"
    assert res_failover.latency_ms < 180.0, f"Expected failover latency <180ms, got {res_failover.latency_ms}ms"

    # Reset
    client.clear_chaos_fault()
    client.reset_circuit_breakers()


# ==============================================================================
# 5. Cryptographic Audit Ledger Merkle Continuity Post-Rollback Test
# ==============================================================================
def test_audit_ledger_merkle_continuity_post_rollback():
    """
    Verifies that the SHA-256 Merkle hash chain retains 100% mathematical integrity
    after appending multiple events, recording snapshots, and executing rollback.
    """
    ledger = TamperEvidentAuditLedger()

    # Append sequential events
    ledger.append_entry("STARTUP", actor="kernel", payload={"version": "2.0"})
    ledger.append_entry("CONFIG_LOCKED", actor="security", payload={"cipher": "aes-gcm"})

    # Record diff snapshot
    ledger.record_diff_snapshot(
        action_id="act_test_001",
        target_path="src/router.py",
        original_code="def route(): pass",
        patched_code="def route(): return 200",
        actor="operator",
    )

    # Rollback
    rollback_res = ledger.rollback_last_diff(actor="operator")
    assert rollback_res is not None
    assert rollback_res["status"] == "ROLLED_BACK"

    # Verify chain integrity
    is_valid, message = ledger.verify_chain_integrity()
    assert is_valid is True
    assert "CHAIN_VALID" in message
    assert len(ledger.chain) == 3


# ==============================================================================
# 6. Standalone CLI Benchmark, Audit-Export, and Rollback Test
# ==============================================================================
def test_cli_benchmark_and_audit_modes():
    """
    Executes aegis_cli.py with --benchmark, --audit-export, and --verify-integrity flags,
    verifying clean exit code 0 and table rendering.
    """
    python_bin = sys.executable
    cli_script = os.path.join(REPO_ROOT, "aegis_cli.py")

    # 1. Benchmark flag
    res_bench = subprocess.run(
        [python_bin, cli_script, "--benchmark"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res_bench.returncode == 0
    assert "Mathematical Context Optimization Benchmarks" in res_bench.stdout
    assert "AVERAGE REPOSITORY COMPRESSION" in res_bench.stdout

    # 2. Audit export flag
    res_audit = subprocess.run(
        [python_bin, cli_script, "--audit-export"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res_audit.returncode == 0
    assert "SHA-256 Merkle-Chained Audit Ledger" in res_audit.stdout
    assert "CHAIN_VALID" in res_audit.stdout

    # 3. Verify integrity flag
    res_verify = subprocess.run(
        [python_bin, cli_script, "--verify-integrity"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=15,
    )
    assert res_verify.returncode == 0
    assert "CRYPTOGRAPHIC INTEGRITY VERIFICATION" in res_verify.stdout


# ==============================================================================
# 7. FastAPI Pathway Streaming Index Telemetry Endpoint Test
# ==============================================================================
def test_streaming_index_api_endpoint():
    """
    Tests GET /api/stream/index endpoint returning Pathway reactive stream index telemetry.
    """
    client = TestClient(app)
    res = client.get("/api/stream/index")
    assert res.status_code == 200
    data = res.json()

    assert data["engine"] == "Pathway Reactive Streaming AST Indexer"
    assert data["partner"] == "Pathway (pathway.com)"
    assert data["amortized_complexity"] == "O(k log |V|)"
    assert "total_tracked_files" in data
    assert "lifetime_cache_hits" in data
