"""
AEGIS-0 On-Demand Symbol Expansion Tests
The model can ask for stubbed bodies with `EXPAND: <name>`; each round is
budget-checked, billed, and reported without inflating "tokens saved".
"""

import os
import sys

from fastapi.testclient import TestClient

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for sub in ("", "security-gate", "tavily-freshness"):
    path = os.path.join(REPO_ROOT, sub)
    if path not in sys.path:
        sys.path.insert(0, path)

import orchestrator.main as main_mod
from orchestrator.ast_pruner import ASTPruner
from orchestrator.main import app, bifrost


# Two sizeable functions: the tight per-file budget keeps only one in full.
def _big_fn(name: str, n: int) -> str:
    body = "\n".join(f"    total += value * {i} - {i} // 3" for i in range(n))
    return f"def {name}(value: int) -> int:\n    total = 0\n{body}\n    return total\n"


SOURCE = _big_fn("reconcile_ledger", 40) + "\n\n" + _big_fn("settle_invoices", 40)


def _run(client, session, budget_usd=None):
    bifrost.mock_mode = True
    bifrost.clear_chaos_fault()
    bifrost.reset_circuit_breakers()
    payload = {
        "session_id": session,
        "prompt": "Explain how reconcile_ledger and settle_invoices interact",
        "file_context": {"billing.py": SOURCE},
    }
    if budget_usd is not None:
        payload["budget_limit_usd"] = budget_usd
    res = client.post("/api/orchestrate", json=payload)
    assert res.status_code == 200, res.text
    return res.json()


def test_parse_and_expand_helpers():
    pruner = ASTPruner()
    assert pruner.parse_expand_requests("EXPAND: a\nEXPAND: B.c\nEXPAND: a\nnoise") == ["a", "B.c"]
    nodes = pruner.parse_source("billing.py", SOURCE)
    out = pruner.expand_symbols(nodes, ["settle_invoices"])
    assert out[0]["symbol"] == "settle_invoices"
    assert "def settle_invoices" in out[0]["source"]
    assert pruner.expand_symbols(nodes, ["settle_invoices"], exclude_ids={out[0]["node_id"]}) == []


def test_model_requests_stubbed_symbol_and_gets_its_body():
    client = TestClient(app)
    data = _run(client, "expand_happy")

    assert data["expansion_rounds"] == 1
    symbols = [e["symbol"] for e in data["expansions"]]
    assert len(symbols) == 1 and symbols[0] in ("reconcile_ledger", "settle_invoices")
    assert data["expansion_tokens"] > 0
    # The final answer is real output, not the expansion request.
    assert "EXPAND:" not in data["generated_code"]
    # Expanded tokens are not counted as saved.
    assert data["tokens_saved"] == max(0, data["raw_tokens"] - data["pruned_tokens"] - data["expansion_tokens"])

    events = client.get("/api/audit/export").json()["ledger"]
    assert any(e["event_type"] == "CONTEXT_EXPANDED" for e in events)


def test_both_rounds_are_billed():
    client = TestClient(app)
    data = _run(client, "expand_billing")
    state = main_mod.ledger.get_session("expand_billing")
    assert data["cost_usd"] > 0
    assert abs(state.cumulative_cost_usd - data["cost_usd"]) < 1e-6


def test_expansion_skipped_when_budget_cannot_cover_it(monkeypatch):
    client = TestClient(app)
    monkeypatch.setattr(main_mod.ledger, "can_afford", lambda *a, **kw: False)
    data = _run(client, "expand_budget")

    assert data["status"] != "HALTED"
    assert data["expansion_rounds"] == 0
    assert data["expansion_skipped_reason"] == "BUDGET"
    state = main_mod.ledger.get_session("expand_budget")
    assert state.is_halted is False
    # The round that asked was still billed exactly once.
    assert abs(state.cumulative_cost_usd - data["cost_usd"]) < 1e-9


def test_can_afford_is_non_mutating():
    from orchestrator.budget_ledger import BudgetLedger
    from orchestrator.schemas import ModelTier

    ledger = BudgetLedger()
    ledger.register_session("afford", user_limit_usd=0.001, session_limit_usd=0.001)
    assert ledger.can_afford("afford", 10_000_000, ModelTier.TIER_2_FRONTIER) is False
    state = ledger.get_session("afford")
    assert state.is_halted is False and state.recovery_checkpoint is None
    assert ledger.can_afford("afford", 10, ModelTier.TIER_0_LOCAL) is True


def test_no_expansion_instructions_when_nothing_is_stubbed():
    client = TestClient(app)
    small = "def tiny():\n    return 1\n"
    res = client.post("/api/orchestrate", json={
        "session_id": "expand_none",
        "prompt": "what does tiny do",
        "file_context": {"t.py": small},
    }).json()
    assert res["expansion_rounds"] == 0
    assert res["expansions"] == []
