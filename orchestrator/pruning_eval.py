"""
AEGIS-0 Pruning Retrieval-Quality Evaluation

Compression alone can be gamed: stubbing everything gives ~100% "savings".
This harness measures whether the pruned context still contains the code a
developer would actually need to answer each question (recall@budget),
alongside the compression achieved at that budget.

Each case is a natural-language question over this repository plus the
symbols whose full implementation is required to answer it. A symbol counts
as retrieved only if its complete body appears in the pruned buffer (stubs
don't count). The check is granularity-agnostic, so it stays fair whether the
pruner keeps whole classes or individual methods.
"""

import ast
import os
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Tuple

from orchestrator.ast_pruner import ASTPruner
from orchestrator.pathway_stream import StreamingASTIndex

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


@dataclass
class EvalCase:
    repo: str
    query: str
    required: List[str]


# Questions intentionally avoid naming the target symbol where possible, so
# seeds can't trivially be read off the query.
EVAL_CASES: List[EvalCase] = [
    EvalCase("orchestrator",
             "How does the ledger decide to down-route to a cheaper model tier when the budget would be exceeded?",
             ["BudgetLedger.compute_preflight_cost"]),
    EvalCase("orchestrator",
             "How is the realized cost deducted after a model call completes, and when does the session halt?",
             ["BudgetLedger.commit_turn_cost"]),
    EvalCase("orchestrator",
             "What happens when a provider returns HTTP 429 and requests fail over to the next model?",
             ["BifrostClient.dispatch"]),
    EvalCase("orchestrator",
             "When does a tripped circuit breaker become available again?",
             ["CircuitBreaker.is_available"]),
    EvalCase("orchestrator",
             "Which files get re-parsed when the repository changes on disk?",
             ["StreamingASTIndex.index_repository"]),
    EvalCase("orchestrator",
             "How are unselected functions and classes collapsed into one-line stubs?",
             ["ASTPruner.generate_1line_stub"]),
    EvalCase("orchestrator",
             "How are quarantined actions protected against replay and expiry when approved?",
             ["approve_action"]),
    EvalCase("security-gate",
             "How is Shannon entropy computed for candidate secret tokens?",
             ["PrivacyGuard.calculate_shannon_entropy"]),
    EvalCase("security-gate",
             "How does the guard detect base64 or hex encoded secret smuggling?",
             ["PrivacyGuard.scan_base64_and_hex_smuggling"]),
    EvalCase("security-gate",
             "How is the audit hash chain verified to detect tampering?",
             ["TamperEvidentAuditLedger.verify_chain_integrity"]),
    EvalCase("security-gate",
             "How does rollback revert the most recently approved diff?",
             ["TamperEvidentAuditLedger.rollback_last_diff"]),
    EvalCase("tavily-freshness",
             "How is the empirical freshness score computed from time decay and semantic agreement?",
             ["FreshnessEngine.calculate_empirical_freshness"]),
    EvalCase("tavily-freshness",
             "How does the engine decide whether Tavily search results show a deprecation?",
             ["FreshnessEngine._query_tavily_api"]),
    EvalCase("tavily-freshness",
             "How are stale openai ChatCompletion calls rewritten to the v1 client?",
             ["FreshnessEngine._patch_openai_v0"]),
]


def default_budget(raw_tokens: int) -> int:
    """Same calibrated budget the orchestrator and CLI use (~25% of raw)."""
    return min(8000, max(1200, int(raw_tokens * 0.25)))


def _normalized_lines(text: str) -> List[str]:
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def _symbol_sources(repo_dir: str) -> Dict[str, str]:
    """Maps 'func' and 'Class.method' names to their original source text."""
    out: Dict[str, str] = {}
    for root, dirs, files in os.walk(repo_dir):
        dirs[:] = [d for d in dirs if d not in StreamingASTIndex.DEFAULT_SKIP_DIRS]
        for fname in sorted(files):
            if not fname.endswith(".py"):
                continue
            path = os.path.join(root, fname)
            with open(path, encoding="utf-8", errors="ignore") as fh:
                src = fh.read()
            try:
                tree = ast.parse(src)
            except SyntaxError:
                continue
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    out.setdefault(node.name, ast.get_source_segment(src, node) or "")
                elif isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            out.setdefault(
                                f"{node.name}.{item.name}", ast.get_source_segment(src, item) or ""
                            )
    return out


def body_present(symbol_source: str, pruned_buffer: str) -> bool:
    """True if every non-blank line of the symbol appears, in order, in the buffer."""
    needle = "\n".join(_normalized_lines(symbol_source))
    haystack = "\n".join(_normalized_lines(pruned_buffer))
    return bool(needle) and needle in haystack


@dataclass
class CaseResult:
    case: EvalCase
    recall: float
    retrieved: List[str]
    missed: List[str]
    raw_tokens: int
    pruned_tokens: int
    budget: int
    seeds: List[str] = field(default_factory=list)

    @property
    def compression(self) -> float:
        return 1.0 - (self.pruned_tokens / self.raw_tokens) if self.raw_tokens else 0.0


def run_eval(
    pruner: Optional[ASTPruner] = None,
    cases: Optional[List[EvalCase]] = None,
    budget_fn: Callable[[int], int] = default_budget,
) -> Tuple[List[CaseResult], Dict[str, float]]:
    pruner = pruner or ASTPruner()
    indexer = StreamingASTIndex(pruner=pruner)
    cases = cases or EVAL_CASES
    results: List[CaseResult] = []
    source_cache: Dict[str, Dict[str, str]] = {}

    for case in cases:
        repo_dir = os.path.join(REPO_ROOT, case.repo)
        nodes, _ = indexer.index_repository(repo_dir)
        if case.repo not in source_cache:
            source_cache[case.repo] = _symbol_sources(repo_dir)
        sources = source_cache[case.repo]

        raw = sum(n.token_cost for n in nodes)
        budget = budget_fn(raw)
        seeds = pruner.select_seeds(case.query, nodes)
        buffer, metrics = pruner.prune_context(nodes, case.query, seeds, budget)

        retrieved, missed = [], []
        for sym in case.required:
            src = sources.get(sym)
            if src is None:
                raise KeyError(f"Eval case references unknown symbol {sym!r} in {case.repo}")
            (retrieved if body_present(src, buffer) else missed).append(sym)

        results.append(CaseResult(
            case=case,
            recall=len(retrieved) / len(case.required),
            retrieved=retrieved,
            missed=missed,
            raw_tokens=metrics["raw_tokens"],
            pruned_tokens=metrics["total_tokens"],
            budget=budget,
            seeds=seeds,
        ))

    n = len(results) or 1
    summary = {
        "cases": len(results),
        "mean_recall": sum(r.recall for r in results) / n,
        "mean_compression": sum(r.compression for r in results) / n,
        "mean_pruned_tokens": sum(r.pruned_tokens for r in results) / n,
    }
    return results, summary


if __name__ == "__main__":
    res, summ = run_eval()
    for r in res:
        status = "HIT " if r.recall == 1.0 else "MISS"
        print(f"{status} recall={r.recall:.2f} comp={r.compression:6.1%} tok={r.pruned_tokens:5d} "
              f"seeds={r.seeds} :: {r.case.query[:70]}")
    print(f"\nmean recall@budget = {summ['mean_recall']:.1%}   "
          f"mean compression = {summ['mean_compression']:.1%}")
