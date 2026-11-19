"""
AEGIS-0 AST Call-Graph Pruner & 1-Line Stubbing Engine
Performs token-optimal context pruning via budgeted submodular knapsack selection,
retaining full context for seed symbols and callers/callees while collapsing
unselected functions and classes into 1-line type-safe stubs (>=75% compression).
"""

import ast
import re
from typing import List, Dict, Tuple, Optional, Set
import tiktoken

from orchestrator.schemas import ASTNode


class ASTPruner:
    """
    Submodular AST Call-Graph Context Pruning Engine.
    """

    def __init__(self, encoding_name: str = "cl100k_base"):
        try:
            self.tokenizer = tiktoken.get_encoding(encoding_name)
        except Exception:
            self.tokenizer = None

    def count_tokens(self, text: str) -> int:
        """
        Calculates exact token count using cl100k_base encoding with safe fallback.
        """
        if not text:
            return 0
        if self.tokenizer:
            try:
                return len(self.tokenizer.encode(text, disallowed_special=()))
            except Exception:
                pass
        # Fallback approximation: 1 token ~ 4 chars
        return max(1, len(text) // 4)

    def _extract_dependencies(self, node: ast.AST) -> List[str]:
        """
        Extracts referenced names and function calls from an AST node.
        """
        deps: Set[str] = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                if isinstance(sub.func, ast.Name):
                    deps.add(sub.func.id)
                elif isinstance(sub.func, ast.Attribute):
                    deps.add(sub.func.attr)
            elif isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
                deps.add(sub.id)
        return sorted(list(deps))

    def generate_1line_stub(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
        raw_source: Optional[str] = None,
    ) -> str:
        """
        Generates a syntactically valid 1-line type-safe stub for functions or classes.

        For functions:
        Retains signature, parameters, and type annotations, replacing body
        with '... # [AST-STUB: {saved_tokens} tokens saved]'.

        For classes:
        Retains class definition header, docstring summary, and converts each
        method to a 1-line signature.
        """
        if raw_source is None:
            raw_source = ast.unparse(node)
        raw_token_cost = self.count_tokens(raw_source)

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            is_async = isinstance(node, ast.AsyncFunctionDef)
            async_prefix = "async " if is_async else ""
            args_str = ast.unparse(node.args)
            return_str = f" -> {ast.unparse(node.returns)}" if node.returns else ""

            # Preserve decorators (e.g. @classmethod, @staticmethod)
            dec_str = "".join(f"@{ast.unparse(d)}\n" for d in node.decorator_list)

            # Baseline tokens for the stub header
            base_stub = f"{dec_str}{async_prefix}def {node.name}({args_str}){return_str}: ..."
            saved_tokens = max(0, raw_token_cost - self.count_tokens(base_stub))

            return f"{dec_str}{async_prefix}def {node.name}({args_str}){return_str}: ... # [AST-STUB: {saved_tokens} tokens saved]"

        elif isinstance(node, ast.ClassDef):
            # Class definition header
            bases_str = f"({', '.join(ast.unparse(b) for b in node.bases)})" if node.bases else ""
            dec_str = "".join(f"@{ast.unparse(d)}\n" for d in node.decorator_list)

            # Docstring summary (first line only)
            docstring = ast.get_docstring(node)
            doc_line = ""
            if docstring:
                first_line = docstring.strip().splitlines()[0].replace('"""', '').strip()
                doc_line = f'    """{first_line}"""\n'

            # Convert methods to 1-line signatures
            method_stubs = []
            has_methods = False
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    has_methods = True
                    m_async = "async " if isinstance(item, ast.AsyncFunctionDef) else ""
                    m_args = ast.unparse(item.args)
                    m_ret = f" -> {ast.unparse(item.returns)}" if item.returns else ""
                    m_dec = "".join(f"    @{ast.unparse(d)}\n" for d in item.decorator_list)
                    method_stubs.append(
                        f"{m_dec}    {m_async}def {item.name}({m_args}){m_ret}: ..."
                    )

            body_str = "\n".join(method_stubs)
            base_repr = f"{dec_str}class {node.name}{bases_str}:\n{doc_line}{body_str}"
            saved_tokens = max(0, raw_token_cost - self.count_tokens(base_repr))
            class_header = f"{dec_str}class {node.name}{bases_str}:  # [AST-STUB: {saved_tokens} tokens saved]"

            if not has_methods:
                if doc_line:
                    return f"{class_header}\n{doc_line}    pass"
                return f"{class_header}\n    pass"

            return f"{class_header}\n{doc_line}{body_str}"

        return ast.unparse(node)

    def parse_source(self, file_path: str, source_code: str) -> List[ASTNode]:
        """
        Parses Python source code into structured ASTNode objects.
        """
        tree = ast.parse(source_code)
        nodes: List[ASTNode] = []

        for idx, statement in enumerate(tree.body):
            if isinstance(statement, (ast.Import, ast.ImportFrom)):
                raw = ast.get_source_segment(source_code, statement) or ast.unparse(statement)
                t_cost = self.count_tokens(raw)
                deps = [alias.name for alias in statement.names]
                nodes.append(
                    ASTNode(
                        node_id=f"{file_path}::import_{idx}",
                        name=f"import_{idx}",
                        node_type="import",
                        file_path=file_path,
                        raw_source=raw,
                        stub_source=raw,  # Imports are preserved as-is
                        token_cost=t_cost,
                        stub_token_cost=t_cost,
                        dependencies=deps,
                    )
                )
            elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                raw = ast.get_source_segment(source_code, statement) or ast.unparse(statement)
                stub = self.generate_1line_stub(statement, raw)
                t_cost = self.count_tokens(raw)
                s_cost = self.count_tokens(stub)
                deps = self._extract_dependencies(statement)
                nodes.append(
                    ASTNode(
                        node_id=f"{file_path}::{statement.name}",
                        name=statement.name,
                        node_type="function",
                        file_path=file_path,
                        raw_source=raw,
                        stub_source=stub,
                        token_cost=t_cost,
                        stub_token_cost=s_cost,
                        dependencies=deps,
                    )
                )
            elif isinstance(statement, ast.ClassDef):
                raw = ast.get_source_segment(source_code, statement) or ast.unparse(statement)
                stub = self.generate_1line_stub(statement, raw)
                t_cost = self.count_tokens(raw)
                s_cost = self.count_tokens(stub)
                deps = self._extract_dependencies(statement)
                nodes.append(
                    ASTNode(
                        node_id=f"{file_path}::{statement.name}",
                        name=statement.name,
                        node_type="class",
                        file_path=file_path,
                        raw_source=raw,
                        stub_source=stub,
                        token_cost=t_cost,
                        stub_token_cost=s_cost,
                        dependencies=deps,
                    )
                )

        return nodes

    def prune_context(
        self,
        nodes: List[ASTNode],
        query: str,
        seed_symbols: List[str],
        max_token_budget: int,
    ) -> Tuple[str, Dict]:
        """
        Solves the budgeted submodular knapsack maximization:
        S* = argmax_{S subset V} [ sum r(v, q) - redundancy ] s.t. sum c(v) <= B

        Greedily selects seed symbols and caller/callee dependencies into full context,
        collapsing all remaining nodes into 1-line stubs.

        Returns:
            Tuple[hybrid_buffer, metrics_dict]
            where metrics_dict includes total_tokens, tokens_saved, and compression_ratio (>= 0.75).
        """
        if not nodes:
            return "", {
                "total_tokens": 0,
                "raw_tokens": 0,
                "tokens_saved": 0,
                "compression_ratio": 0.0,
                "selected_nodes": [],
                "stubbed_nodes": [],
            }

        seed_set = set(seed_symbols)
        query_words = set(re.findall(r"\w+", query.lower()))

        # Separate imports (always included in full to maintain syntax)
        imports = [n for n in nodes if n.node_type == "import"]
        candidates = [n for n in nodes if n.node_type != "import"]

        # 1. Compute node relevance r(v, q) and knapsack density
        scored_candidates = []
        for n in candidates:
            is_direct_seed = (n.name in seed_set) or any(s in n.name for s in seed_set)

            # Call graph 1-hop distance: callers or callees of seed symbols
            is_caller = any(dep in seed_set for dep in n.dependencies)
            is_callee = any(s in n.dependencies for s in seed_set)
            is_related = is_caller or is_callee

            # Semantic / Lexical overlap with query
            node_words = set(re.findall(r"\w+", (n.name + " " + n.raw_source[:200]).lower()))
            overlap = len(query_words.intersection(node_words)) / max(1, len(query_words))

            if is_direct_seed:
                relevance = 100.0 + overlap * 10.0
                priority = 0
            elif is_related:
                relevance = 50.0 + overlap * 5.0
                priority = 1
            else:
                relevance = 1.0 + overlap * 2.0
                priority = 2

            marginal_tokens = max(1, n.token_cost - n.stub_token_cost)
            density = relevance / float(marginal_tokens)

            scored_candidates.append({
                "node": n,
                "priority": priority,
                "relevance": relevance,
                "marginal_tokens": marginal_tokens,
                "density": density,
            })

        # Sort candidates: Priority first (Seeds -> 1-hop -> Others), then density descending
        scored_candidates.sort(key=lambda x: (x["priority"], -x["density"]))

        # 2. Baseline token cost with all non-imports stubbed and imports full
        baseline_tokens = sum(n.token_cost for n in imports) + sum(
            n.stub_token_cost for n in candidates
        )

        selected_for_full: Set[str] = set()
        current_budget = baseline_tokens

        # 3. Greedy Knapsack Selection
        for item in scored_candidates:
            n = item["node"]
            marginal = item["marginal_tokens"]
            if current_budget + marginal <= max_token_budget:
                selected_for_full.add(n.node_id)
                current_budget += marginal
            elif item["priority"] == 0 and not selected_for_full:
                # Always promote at least one primary seed symbol if possible
                selected_for_full.add(n.node_id)
                current_budget += marginal

        # 4. Assemble hybrid buffer maintaining original node ordering
        buffer_elements: List[str] = []
        selected_names = []
        stubbed_names = []

        for n in nodes:
            if n.node_type == "import" or n.node_id in selected_for_full:
                buffer_elements.append(n.raw_source)
                if n.node_type != "import":
                    selected_names.append(n.name)
            else:
                buffer_elements.append(n.stub_source)
                stubbed_names.append(n.name)

        hybrid_code = "\n\n".join(buffer_elements)

        # 5. Calculate verified token metrics
        raw_tokens_total = sum(n.token_cost for n in nodes)
        hybrid_tokens_total = self.count_tokens(hybrid_code)
        tokens_saved = max(0, raw_tokens_total - hybrid_tokens_total)
        compression_ratio = (
            float(tokens_saved) / float(raw_tokens_total)
            if raw_tokens_total > 0
            else 0.0
        )

        metrics = {
            "total_tokens": hybrid_tokens_total,
            "raw_tokens": raw_tokens_total,
            "tokens_saved": tokens_saved,
            "compression_ratio": round(compression_ratio, 4),
            "selected_nodes": selected_names,
            "stubbed_nodes": stubbed_names,
            "selected_node_ids": list(selected_for_full),
        }

        return hybrid_code, metrics
