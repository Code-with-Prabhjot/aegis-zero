"""
AEGIS-0 Method-Level Pruning & Top-Level Statement Tests
"""

import ast
import os
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from orchestrator.ast_pruner import ASTPruner


SERVICE = '''"""Billing service."""
import math

TAX_RATE = 0.2
REGION_TABLE = {
    "eu": {"vat": 0.21, "currency": "EUR", "rounding": "half_even", "notes": "standard rate"},
    "us": {"vat": 0.0, "currency": "USD", "rounding": "half_up", "notes": "state taxes apply"},
    "uk": {"vat": 0.2, "currency": "GBP", "rounding": "half_up", "notes": "standard rate"},
}


class Invoice:
    """An invoice with line items."""

    currency = "USD"

    def __init__(self, items):
        self.items = list(items)

    def subtotal(self):
        total = 0
        for price, qty in self.items:
            total += price * qty
        return total

    def total_with_tax(self):
        return math.floor(self.subtotal() * (1 + TAX_RATE))

    def render_pdf(self, path):
        lines = []
        for price, qty in self.items:
            lines.append(f"{qty} x {price}")
        with open(path, "w") as fh:
            fh.write("\\n".join(lines))
        return path


if __name__ == "__main__":
    print(Invoice([(1, 2)]).total_with_tax())
'''


def _prune(seed, budget=10_000_000, query="tax"):
    pruner = ASTPruner()
    nodes = pruner.parse_source("billing.py", SERVICE)
    code, metrics = pruner.prune_context(nodes, query, [seed], budget)
    return nodes, code, metrics


def test_class_is_split_into_header_and_methods():
    nodes, _, _ = _prune("Invoice.subtotal")
    by_name = {n.name: n for n in nodes}
    assert by_name["Invoice"].node_type == "class"
    for m in ("__init__", "subtotal", "total_with_tax", "render_pdf"):
        node = by_name[f"Invoice.{m}"]
        assert node.node_type == "method"
        assert node.parent_id == "billing.py::Invoice"
    # Class header carries attributes and docstring, not method bodies.
    assert 'currency = "USD"' in by_name["Invoice"].raw_source
    assert "def subtotal" not in by_name["Invoice"].raw_source


def test_single_method_kept_without_rest_of_class():
    pruner = ASTPruner()
    nodes = pruner.parse_source("billing.py", SERVICE)
    seed_cost = next(n for n in nodes if n.name == "Invoice.total_with_tax").token_cost
    stub_floor = sum(n.stub_token_cost for n in nodes) + seed_cost
    code, metrics = pruner.prune_context(nodes, "tax", ["Invoice.total_with_tax"], stub_floor + 5)

    ast.parse(code)
    assert "Invoice.total_with_tax" in metrics["selected_nodes"]
    assert "math.floor(self.subtotal() * (1 + TAX_RATE))" in code
    # The unrelated method is reduced to its signature.
    assert "def render_pdf(self, path): ..." in code
    assert "fh.write" not in code


def test_self_calls_link_sibling_methods():
    pruner = ASTPruner()
    nodes = pruner.parse_source("billing.py", SERVICE)
    pruner.construct_call_graph(nodes)
    dist = pruner.compute_hop_distances(nodes, ["Invoice.total_with_tax"])
    assert dist["billing.py::Invoice.subtotal"] == 1.0   # self.subtotal()
    assert dist["billing.py::Invoice"] == 1.0            # parent class
    assert dist["billing.py::TAX_RATE"] == 1.0           # module constant used


def test_attribute_call_resolves_to_unique_method_across_files():
    pruner = ASTPruner()
    caller = "def checkout(inv):\n    return inv.render_pdf('out.pdf')\n"
    nodes = pruner.parse_source("billing.py", SERVICE) + pruner.parse_source("app.py", caller)
    pruner.construct_call_graph(nodes)
    dist = pruner.compute_hop_distances(nodes, ["checkout"])
    assert dist["billing.py::Invoice.render_pdf"] == 1.0


def test_constants_and_statements_are_kept_or_stubbed_validly():
    pruner = ASTPruner()
    nodes = pruner.parse_source("billing.py", SERVICE)
    by_name = {n.name: n for n in nodes}

    assert by_name["TAX_RATE"].node_type == "constant"
    assert by_name["TAX_RATE"].stub_source == "TAX_RATE = 0.2"  # small: kept verbatim
    assert by_name["REGION_TABLE"].stub_source.startswith("REGION_TABLE = ...")
    main_block = next(n for n in nodes if n.node_type == "statement" and "__main__" in n.raw_source)
    assert main_block.stub_source.startswith("# [AST-STUB:")

    # Everything stubbed must still parse.
    code, _ = pruner.prune_context(nodes, "unrelated query", ["nothing_matches"], 1)
    ast.parse(code)


def test_nonstandard_indentation_mixes_full_and_stubbed_methods():
    two_space = (
        "class Box:\n"
        "  size = 1\n"
        "  def grow(self):\n"
        "    self.size += 1\n"
        "    return self.size\n"
        "  def shrink(self):\n"
        "    self.size -= 1\n"
        "    return self.size\n"
    )
    pruner = ASTPruner()
    nodes = pruner.parse_source("box.py", two_space)
    grow_cost = next(n for n in nodes if n.name == "Box.grow").token_cost
    budget = sum(n.stub_token_cost for n in nodes) + grow_cost
    code, metrics = pruner.prune_context(nodes, "grow", ["Box.grow"], budget)
    ast.parse(code)
    assert "self.size += 1" in code
    assert "self.size -= 1" not in code  # shrink stubbed alongside a full method


def test_stub_never_costs_more_than_source():
    pruner = ASTPruner()
    for n in pruner.parse_source("billing.py", SERVICE):
        assert n.stub_token_cost <= n.token_cost, n.name
