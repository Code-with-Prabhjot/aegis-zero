"""
AEGIS-0 Pruning Retrieval-Quality Harness Tests
"""

import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from evals.pruning_eval import EVAL_CASES, body_present, run_eval, _symbol_sources


def test_body_present_ignores_indentation_but_not_stubs():
    src = "def f(x):\n    y = x + 1\n    return y\n"
    reindented = "class A:\n    def f(x):\n        y = x + 1\n        return y\n"
    stubbed = "def f(x): ...  # [AST-STUB: 5 tokens saved]\n"
    assert body_present(src, reindented)
    assert not body_present(src, stubbed)


def test_every_eval_case_references_a_real_symbol():
    for case in EVAL_CASES:
        sources = _symbol_sources(os.path.join(REPO_ROOT, case.repo))
        for sym in case.required:
            assert sym in sources, f"{sym} not found in {case.repo}"


def test_run_eval_reports_recall_and_compression():
    results, summary = run_eval()
    assert summary["cases"] == len(EVAL_CASES)
    assert 0.0 <= summary["mean_recall"] <= 1.0
    assert 0.0 <= summary["mean_compression"] <= 1.0
    for r in results:
        assert r.pruned_tokens > 0
        assert r.raw_tokens >= r.pruned_tokens


def test_retrieval_quality_floor():
    """Regression guard: pruning must keep the code questions need, not just shrink."""
    _, summary = run_eval()
    assert summary["mean_recall"] >= 0.85, summary
    assert summary["mean_compression"] >= 0.70, summary
