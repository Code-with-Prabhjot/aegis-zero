"""
AEGIS-0 Cache-Friendly Prompt Layout Tests
The repository skeleton is a query-independent prefix; a repeat request hits
the (simulated) provider prefix cache and is billed at the cache-read rate.
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for sub in ("", "security-gate", "tavily-freshness"):
    path = os.path.join(REPO_ROOT, sub)
    if path not in sys.path:
        sys.path.insert(0, path)

from orchestrator.ast_pruner import ASTPruner
from orchestrator.budget_ledger import BudgetLedger
from orchestrator.main import app, bifrost
from orchestrator.pathway_stream import StreamingASTIndex
from orchestrator.schemas import ModelPricing, ModelTier

SECURITY_GATE = os.path.join(REPO_ROOT, "security-gate")
# Large enough that its skeleton clears providers' minimum cacheable prefix.
ORCHESTRATOR = os.path.join(REPO_ROOT, "orchestrator")


@pytest.fixture
def client():
    bifrost.mock_mode = True
    bifrost.clear_chaos_fault()
    bifrost.reset_circuit_breakers()
    bifrost._prefix_cache.clear()
    return TestClient(app)


def test_skeleton_prefix_is_query_independent():
    pruner = ASTPruner()
    nodes, _ = StreamingASTIndex(pruner).index_repository(SECURITY_GATE)
    layouts = []
    for q in ("How is Shannon entropy computed?", "How does rollback revert the last diff?"):
        seeds = pruner.select_seeds(q, nodes)
        _, m = pruner.prune_context(nodes, q, seeds, 2000, layout="cache")
        layouts.append(pruner.build_cache_layout(nodes, set(m["selected_node_ids"])))

    (prefix_a, suffix_a), (prefix_b, suffix_b) = layouts
    assert prefix_a == prefix_b
    assert suffix_a != suffix_b
    assert "def calculate_shannon_entropy" in suffix_a
    assert "def rollback_last_diff" in suffix_b


def test_cache_layout_respects_token_budget():
    pruner = ASTPruner()
    nodes, _ = StreamingASTIndex(pruner).index_repository(SECURITY_GATE)
    budget = 2000
    q = "How is Shannon entropy computed?"
    _, m = pruner.prune_context(nodes, q, pruner.select_seeds(q, nodes), budget, layout="cache")
    prefix, suffix = pruner.build_cache_layout(nodes, set(m["selected_node_ids"]))
    sent = pruner.count_tokens(prefix) + pruner.count_tokens(suffix)
    assert sent <= budget * 1.03  # joins/whitespace tokenize slightly differently


def test_repeat_request_hits_prefix_cache_and_costs_less(client):
    body = {"repo_path": ORCHESTRATOR, "budget_limit_usd": 5.0}
    first = client.post("/api/orchestrate", json={
        **body, "session_id": "cache_a", "prompt": "How does the ledger down-route tiers?",
    }).json()
    second = client.post("/api/orchestrate", json={
        **body, "session_id": "cache_b", "prompt": "How does failover pick the next provider?",
    }).json()
    assert first["prompt_cache"]["prefix_tokens"] >= 1024

    assert first["prompt_cache"]["layout"] == "skeleton_prefix"
    assert first["prompt_cache"]["prefix_sha256"] == second["prompt_cache"]["prefix_sha256"]
    assert first["prompt_cache"]["cache_hit"] is False
    assert second["prompt_cache"]["cache_hit"] is True
    assert second["prompt_cache"]["cached_prompt_tokens"] == second["prompt_cache"]["prefix_tokens"]
    # Same-sized context, but most input billed at the cache-read rate.
    assert second["cost_usd"] < first["cost_usd"]


def test_small_prefixes_are_not_cached(client):
    """Providers don't cache prefixes under ~1024 tokens; neither does the simulation."""
    for session in ("small_a", "small_b"):
        res = client.post("/api/orchestrate", json={
            "repo_path": SECURITY_GATE, "session_id": session,
            "prompt": "How is Shannon entropy computed?", "budget_limit_usd": 5.0,
        }).json()
        assert res["prompt_cache"]["prefix_tokens"] < 1024
        assert res["prompt_cache"]["cache_hit"] is False


def test_legacy_interleaved_layout_still_available(client):
    res = client.post("/api/orchestrate", json={
        "repo_path": SECURITY_GATE,
        "session_id": "cache_off",
        "prompt": "How is Shannon entropy computed?",
        "cache_layout": False,
    }).json()
    assert res["prompt_cache"]["layout"] == "interleaved"


def test_ledger_bills_cached_tokens_at_cache_read_rate():
    pricing = {
        ModelTier.TIER_2_FRONTIER: ModelPricing(
            input_per_mtok=4.0, output_per_mtok=20.0, cache_read_per_mtok=0.2,
        ),
        ModelTier.TIER_1_MICRO: ModelPricing(input_per_mtok=0.1, output_per_mtok=0.5),
        ModelTier.TIER_0_LOCAL: ModelPricing(input_per_mtok=0.0, output_per_mtok=0.0),
    }
    ledger = BudgetLedger(pricing_registry=pricing)
    full = ledger._calculate_bound_cost(10_000, 1_000, ModelTier.TIER_2_FRONTIER)
    cached = ledger._calculate_bound_cost(10_000, 1_000, ModelTier.TIER_2_FRONTIER, cached_input_tokens=8_000)
    assert full == pytest.approx((10_000 * 4.0 + 1_000 * 20.0) / 1e6)
    assert cached == pytest.approx((2_000 * 4.0 + 8_000 * 0.2 + 1_000 * 20.0) / 1e6)
    # Default cache-read rate falls back to 0.1x input when unspecified.
    assert pricing[ModelTier.TIER_1_MICRO].cache_read_rate == pytest.approx(0.01)
