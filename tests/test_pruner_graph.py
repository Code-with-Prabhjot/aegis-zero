"""
AEGIS-0 Pruner Call-Graph & Determinism Regression Tests
Covers deterministic seed selection, node_id-keyed graphs for same-named
symbols across files, and exact (non-substring) seed matching.
"""

import os
import subprocess
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from orchestrator.ast_pruner import ASTPruner


FILE_A = '''
def main():
    return helper()

def helper():
    return 1
'''

FILE_B = '''
def main():
    return unrelated_b()

def unrelated_b():
    return 2

def get_config():
    return {}

def target_widget():
    return 3
'''


def _nodes(pruner):
    nodes = pruner.parse_source("a.py", FILE_A) + pruner.parse_source("b.py", FILE_B)
    pruner.construct_call_graph(nodes)
    return nodes


def test_same_named_symbols_in_different_files_stay_separate():
    pruner = ASTPruner()
    nodes = _nodes(pruner)
    distances = pruner.compute_hop_distances(nodes, seed_symbols=["a.py::main"])

    assert distances["a.py::main"] == 0.0
    assert distances["a.py::helper"] == 1.0
    # b.py::main shares a name but is a different symbol; it must not be a seed.
    assert distances["b.py::main"] == float("inf")
    assert distances["b.py::unrelated_b"] == float("inf")


def test_calls_resolve_to_same_file_definition_first():
    pruner = ASTPruner()
    nodes = _nodes(pruner)
    adj = pruner._build_adjacency(nodes)
    assert "a.py::helper" in adj["a.py::main"]
    assert "b.py::unrelated_b" in adj["b.py::main"]
    assert "b.py::unrelated_b" not in adj["a.py::main"]


def test_short_seed_does_not_substring_match():
    pruner = ASTPruner()
    nodes = _nodes(pruner)
    distances = pruner.compute_hop_distances(nodes, seed_symbols=["get"])
    # "get" must not match get_config (or anything else containing "get").
    assert all(d != 0.0 for d in distances.values())


def test_select_seeds_prefers_exact_identifiers():
    pruner = ASTPruner()
    nodes = _nodes(pruner)
    assert pruner.select_seeds("please refactor target_widget", nodes) == ["target_widget"]


def test_select_seeds_is_deterministic_across_hash_seeds():
    """Seed selection previously used list(set)[0], which changed with PYTHONHASHSEED."""
    script = (
        "import sys; sys.path.insert(0, %r)\n"
        "from orchestrator.ast_pruner import ASTPruner\n"
        "from orchestrator.pathway_stream import StreamingASTIndex\n"
        "p = ASTPruner()\n"
        "nodes, _ = StreamingASTIndex(p).index_repository(%r)\n"
        "seeds = p.select_seeds('improve overall efficiency', nodes)\n"
        "code, m = p.prune_context(nodes, 'improve overall efficiency', seeds, 3000)\n"
        "print(seeds, m['total_tokens'], sorted(m['selected_node_ids']))\n"
    ) % (REPO_ROOT, os.path.join(REPO_ROOT, "orchestrator"))

    outputs = set()
    for hash_seed in ("1", "2", "3", "4"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed)
        res = subprocess.run(
            [sys.executable, "-c", script], capture_output=True, text=True, env=env, timeout=60
        )
        assert res.returncode == 0, res.stderr
        outputs.add(res.stdout.strip())
    assert len(outputs) == 1, f"Pruning output varied across hash seeds: {outputs}"
