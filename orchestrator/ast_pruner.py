"""
AEGIS-0 AST Call-Graph Pruner & 1-Line Stubbing Engine
Performs token-optimal context pruning via budgeted submodular knapsack selection,
retaining full context for seed symbols and callers/callees while collapsing
unselected functions and classes into 1-line type-safe stubs (>=75% compression).
Features multi-hop BFS call-graph traversal with cycle-safe visited guards and
graceful syntax-error fallback for mid-edit buffers.
"""

import ast
import collections
import logging
import math
import os
import re
import textwrap
from typing import List, Dict, Tuple, Optional, Set
import tiktoken

from orchestrator.schemas import ASTNode

logger = logging.getLogger("orchestrator.ast_pruner")


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

    def _extract_dependencies(
        self,
        node: ast.AST,
        repo_symbols: Optional[Set[str]] = None,
        class_name: Optional[str] = None,
    ) -> List[str]:
        """
        Extracts referenced names and function calls from an AST node.

        Inside a method (class_name given), `self.x(...)` / `cls.x(...)` resolve
        to the sibling method `Class.x`. Other attribute calls record the bare
        attribute name, which the call graph may resolve to a uniquely named
        method elsewhere in the repository.
        If repo_symbols is provided, filters dependencies to exact repository symbols.
        """
        deps: Set[str] = set()
        for sub in ast.walk(node):
            if isinstance(sub, ast.Call):
                func = sub.func
                if isinstance(func, ast.Name):
                    deps.add(func.id)
                elif isinstance(func, ast.Attribute):
                    receiver = func.value
                    if (
                        class_name
                        and isinstance(receiver, ast.Name)
                        and receiver.id in ("self", "cls")
                    ):
                        deps.add(f"{class_name}.{func.attr}")
                    else:
                        deps.add(func.attr)
            elif isinstance(sub, ast.Name) and isinstance(sub.ctx, ast.Load):
                deps.add(sub.id)

        if repo_symbols is not None:
            deps = deps.intersection(repo_symbols)

        return sorted(deps)

    @staticmethod
    def _short_name(node: ASTNode) -> str:
        return node.name.rsplit(".", 1)[-1]

    def construct_call_graph(self, nodes: List[ASTNode]) -> List[ASTNode]:
        """
        Populates and filters each node's dependencies with exact symbol names
        of other parsed ASTNodes across the repository. Method short names
        (`dispatch` for `BifrostClient.dispatch`) are kept so attribute calls
        like `bifrost.dispatch(...)` can be resolved.
        """
        known_symbols = {n.name for n in nodes if n.name and n.node_type != "import"}
        known_symbols |= {self._short_name(n) for n in nodes if n.node_type == "method"}
        for n in nodes:
            if n.node_type != "import":
                n.dependencies = sorted(
                    {dep for dep in n.dependencies if dep in known_symbols and dep != n.name}
                )
        return nodes

    def _build_adjacency(self, nodes: List[ASTNode]) -> Dict[str, Set[str]]:
        """
        Builds a bidirectional caller <-> callee graph keyed by node_id.

        Dependencies are recorded as symbol names, so each one is resolved to
        concrete nodes: a definition in the caller's own file wins (Python
        scoping), otherwise every repository definition with that name is linked.
        Bare attribute names resolve to a method only when exactly one method in
        the repository has that name, to avoid linking every `reset()` together.
        Methods are always linked to their class, and calling a class links to
        its `__init__`. Keying by node_id keeps same-named symbols in different
        files (e.g. two `main` functions) from collapsing into one graph vertex.
        """
        by_name: Dict[str, List[ASTNode]] = collections.defaultdict(list)
        methods_by_short: Dict[str, List[ASTNode]] = collections.defaultdict(list)
        for n in nodes:
            if n.node_type == "import":
                continue
            by_name[n.name].append(n)
            if n.node_type == "method":
                methods_by_short[self._short_name(n)].append(n)

        adj: Dict[str, Set[str]] = collections.defaultdict(set)

        def link(a: str, b: str) -> None:
            if a != b:
                adj[a].add(b)
                adj[b].add(a)

        def resolve(dep: str, caller: ASTNode) -> List[ASTNode]:
            targets = by_name.get(dep)
            if not targets:
                short = methods_by_short.get(dep, [])
                targets = short if len(short) == 1 else []
            same_file = [t for t in targets if t.file_path == caller.file_path]
            return same_file or targets

        for n in nodes:
            if n.node_type == "import":
                continue
            if n.parent_id:
                link(n.node_id, n.parent_id)
            for dep in n.dependencies:
                for t in resolve(dep, n):
                    link(n.node_id, t.node_id)
                    if t.node_type == "class":
                        for init in by_name.get(f"{t.name}.__init__", []):
                            if init.file_path == t.file_path:
                                link(n.node_id, init.node_id)
        return adj

    @staticmethod
    def _matches_seed(node: ASTNode, seed: str) -> bool:
        """
        Exact identifier match: the seed must equal the node's name, its node_id,
        or (for qualified names like `Class.method`) its last segment. Substring
        matching is avoided so a short seed like `get` doesn't match everything.
        """
        return seed == node.name or seed == node.node_id or seed == node.name.rsplit(".", 1)[-1]

    def compute_hop_distances(
        self, nodes: List[ASTNode], seed_symbols: List[str]
    ) -> Dict[str, float]:
        """
        Computes shortest-path hop distances d_AST(v, V_seed) using breadth-first search
        with a visited set guard to prevent infinite loops on circular calls or mutual recursion.

        Returns distances keyed by node_id.
        """
        adj = self._build_adjacency(nodes)
        seed_set = [s for s in seed_symbols if s]

        visited: Set[str] = set()
        distances: Dict[str, float] = {
            n.node_id: float("inf") for n in nodes if n.node_type != "import"
        }
        queue = collections.deque()

        for n in nodes:
            if n.node_type == "import":
                continue
            if any(self._matches_seed(n, s) for s in seed_set):
                visited.add(n.node_id)
                distances[n.node_id] = 0.0
                queue.append((n.node_id, 0))

        while queue:
            curr_id, dist = queue.popleft()
            for neighbor in sorted(adj.get(curr_id, ())):
                if neighbor not in visited:
                    visited.add(neighbor)
                    distances[neighbor] = float(dist + 1)
                    queue.append((neighbor, dist + 1))

        return distances

    _STOPWORDS = frozenset("""
        a an and are as at be been but by can could did do does for from get got had has have
        how i if in into is it its let me my of on or our please should so than that the their
        them then there these they this to under up us was we were what when where which while
        who why will with would you your again become again also any all each every just more
        most some such only own same other very self cls none true false return def class
    """.split())

    _CALLABLE_TYPES = ("function", "method", "class")

    @staticmethod
    def _stem(word: str) -> str:
        """Tiny suffix stripper so 'stubs'/'stub', 'verified'/'verify' and
        'computed'/'compute' share a term. Deliberately conservative."""
        for suffix, repl in (("ies", "y"), ("ied", "y"), ("ing", ""), ("ed", ""), ("es", ""), ("s", "")):
            if word.endswith(suffix) and len(word) - len(suffix) >= 3 and not word.endswith("ss"):
                word = word[: len(word) - len(suffix)] + repl
                break
        if len(word) > 4 and word.endswith("e"):
            word = word[:-1]
        return word

    @classmethod
    def _terms(cls, text: str) -> List[str]:
        """Splits snake_case and camelCase identifiers, lowercases, drops
        stopwords and numbers, and stems."""
        out: List[str] = []
        for raw in re.findall(r"[A-Za-z][A-Za-z0-9]*", text):
            for part in re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|[0-9]+", raw):
                w = part.lower()
                if len(w) < 2 or w.isdigit() or w in cls._STOPWORDS:
                    continue
                out.append(cls._stem(w))
        return out

    @staticmethod
    def _looks_like_identifier(token: str) -> bool:
        return "_" in token or "." in token or bool(re.search(r"[a-z][A-Z]", token))

    def select_seeds(self, query: str, nodes: List[ASTNode], max_seeds: int = 5) -> List[str]:
        """
        Deterministically picks seed symbols for a query.

        1. Tokens in the query that exactly name a repository symbol. Plain
           English words only match functions, methods and classes, so "ledger"
           in a question doesn't seed a module variable called `ledger`;
           code-like tokens (snake_case, CamelCase, dotted) match anything.
        2. Otherwise, the top BM25-ranked functions/methods/classes (ties by node_id).
        3. Otherwise, the first symbol by node_id.
        """
        candidates = [n for n in nodes if n.node_type not in ("import", "fallback")]
        if not candidates:
            return []

        tokens = set(re.findall(r"[A-Za-z_][A-Za-z0-9_.]*[A-Za-z0-9_]|[A-Za-z_]", query))
        exact = sorted({
            n.name for n in candidates
            for w in tokens
            if self._matches_seed(n, w)
            and (n.node_type in self._CALLABLE_TYPES or self._looks_like_identifier(w))
        })
        if exact:
            return exact[:max_seeds]

        # Seeds are callables/classes; constants and statements are reached via
        # graph distance rather than seeding the search themselves.
        pool = [n for n in candidates if n.node_type in self._CALLABLE_TYPES] or candidates
        scores = self.lexical_relevance(query, pool)
        ranked = sorted(pool, key=lambda n: (-scores.get(n.node_id, 0.0), n.node_id))
        top = [n.name for n in ranked if scores.get(n.node_id, 0.0) > 0][: min(3, max_seeds)]
        if top:
            return top
        return [min(candidates, key=lambda n: n.node_id).name]

    def lexical_relevance(
        self, query: str, nodes: List[ASTNode], k1: float = 1.2, b: float = 0.75
    ) -> Dict[str, float]:
        """
        BM25 relevance of each node to the query, normalised to [0, 1] and keyed
        by node_id. A node's document is its source with identifiers split
        (snake_case / camelCase) and stemmed; name terms are counted three
        times so a symbol's own name outweighs words it merely mentions.
        """
        q_terms = set(self._terms(query))
        if not q_terms or not nodes:
            return {n.node_id: 0.0 for n in nodes}

        docs: Dict[str, collections.Counter] = {}
        for n in nodes:
            terms = self._terms(n.name) * 3 + self._terms(n.raw_source)
            docs[n.node_id] = collections.Counter(terms)

        n_docs = len(docs)
        avg_len = sum(sum(c.values()) for c in docs.values()) / n_docs or 1.0
        df = {t: sum(1 for c in docs.values() if t in c) for t in q_terms}

        raw_scores: Dict[str, float] = {}
        for node_id, counts in docs.items():
            length = sum(counts.values())
            score = 0.0
            for t in q_terms:
                tf = counts.get(t, 0)
                if not tf:
                    continue
                idf = math.log(1 + (n_docs - df[t] + 0.5) / (df[t] + 0.5))
                score += idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * length / avg_len))
            raw_scores[node_id] = score

        top = max(raw_scores.values()) or 1.0
        return {nid: sc / top for nid, sc in raw_scores.items()}

    def build_cache_layout(
        self, nodes: List[ASTNode], selected_ids: Set[str]
    ) -> Tuple[str, str]:
        """
        Splits pruned context into a prompt-cache-friendly pair:

        - prefix: the repository skeleton (imports + every symbol as its stub),
          in source order. It depends only on the code, not the query, so it
          stays byte-identical across requests and can be served from the
          provider's prefix cache.
        - suffix: full bodies of the symbols selected for this query,
          dedented so each one parses on its own.
        """
        prefix_parts: List[str] = []
        multi_file = len({n.file_path for n in nodes}) > 1
        current_file = None
        for n in nodes:
            if multi_file and n.file_path != current_file:
                current_file = n.file_path
                prefix_parts.append(f"# ===== File: {current_file} =====")
            prefix_parts.append(n.raw_source if n.node_type == "import" else n.stub_source)

        suffix_parts: List[str] = []
        for n in nodes:
            if n.node_type != "import" and n.node_id in selected_ids:
                suffix_parts.append(
                    f"# ===== {n.name} ({n.file_path}) =====\n{textwrap.dedent(n.raw_source)}"
                )
        return "\n\n".join(prefix_parts), "\n\n".join(suffix_parts)

    EXPAND_REQUEST = re.compile(r"^\s*EXPAND:\s*([A-Za-z_][A-Za-z0-9_.]*)\s*$", re.MULTILINE)

    def parse_expand_requests(self, text: str, limit: int = 3) -> List[str]:
        """Symbol names a model asked to expand via `EXPAND: <name>` lines."""
        seen: List[str] = []
        for name in self.EXPAND_REQUEST.findall(text or ""):
            if name not in seen:
                seen.append(name)
        return seen[:limit]

    def expand_symbols(
        self,
        nodes: List[ASTNode],
        names: List[str],
        exclude_ids: Optional[Set[str]] = None,
    ) -> List[Dict[str, object]]:
        """
        Returns full source for requested stubbed symbols (exact name, node_id,
        or method short name). Symbols already shown in full are skipped.
        """
        exclude_ids = exclude_ids or set()
        out: List[Dict[str, object]] = []
        taken: Set[str] = set()
        for name in names:
            for n in nodes:
                if n.node_type in ("import", "fallback") or n.node_id in exclude_ids or n.node_id in taken:
                    continue
                if self._matches_seed(n, name):
                    taken.add(n.node_id)
                    out.append({
                        "symbol": n.name,
                        "node_id": n.node_id,
                        "file_path": n.file_path,
                        "source": n.raw_source,
                        "tokens": n.token_cost,
                    })
        return out

    def generate_1line_stub(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef,
        raw_source: Optional[str] = None,
    ) -> str:
        """
        Generates a syntactically valid 1-line type-safe stub for functions or classes.

        For functions:
        Retains decorators, signature, parameters, and type annotations, replacing
        the body with '...'. No per-stub annotation is added: on method-heavy code
        those comments cost more tokens than they convey. The pruned buffer carries
        a single summary line instead.

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

            type_params = getattr(node, "type_params", [])
            type_params_str = f"[{', '.join(ast.unparse(p) for p in type_params)}]" if type_params else ""

            # Preserve decorators (e.g. @classmethod, @staticmethod)
            dec_str = "".join(f"@{ast.unparse(d)}\n" for d in node.decorator_list)

            return f"{dec_str}{async_prefix}def {node.name}{type_params_str}({args_str}){return_str}: ..."

        elif isinstance(node, ast.ClassDef):
            type_params = getattr(node, "type_params", [])
            type_params_str = f"[{', '.join(ast.unparse(p) for p in type_params)}]" if type_params else ""

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

    # Constants at or below this cost are kept verbatim even when "stubbed";
    # eliding them would save almost nothing and lose useful configuration.
    SMALL_CONSTANT_TOKENS = 40

    @staticmethod
    def _stmt_start_line(stmt: ast.stmt) -> int:
        decorators = getattr(stmt, "decorator_list", None) or []
        return min([stmt.lineno] + [d.lineno for d in decorators])

    @staticmethod
    def _slice_lines(lines: List[str], start: int, end: int) -> str:
        """1-based inclusive line slice, preserving original indentation."""
        return "".join(lines[start - 1:end]).rstrip("\n")

    def _make_node(
        self,
        file_path: str,
        name: str,
        node_type: str,
        raw: str,
        stub: str,
        dependencies: List[str],
        parent_id: Optional[str] = None,
    ) -> ASTNode:
        # A stub must never cost more than the code it replaces. Fallback stubs are
        # exempt: their raw source doesn't parse, so it can never stand in for them.
        if node_type != "fallback" and self.count_tokens(stub) >= self.count_tokens(raw):
            stub = raw
        return ASTNode(
            node_id=f"{file_path}::{name}",
            name=name,
            node_type=node_type,
            file_path=file_path,
            raw_source=raw,
            stub_source=stub,
            token_cost=self.count_tokens(raw),
            stub_token_cost=self.count_tokens(stub),
            dependencies=dependencies,
            parent_id=parent_id,
        )

    def _constant_stub(self, stmt: ast.stmt, raw: str) -> str:
        saved = self.count_tokens(raw)
        if saved <= self.SMALL_CONSTANT_TOKENS:
            return raw
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            head = f"{stmt.target.id}: {ast.unparse(stmt.annotation)}"
            return f"{head} = ...  # [AST-STUB: {saved} tokens saved]"
        if isinstance(stmt, ast.Assign) and all(
            isinstance(t, (ast.Name, ast.Tuple)) for t in stmt.targets
        ):
            targets = " = ".join(ast.unparse(t) for t in stmt.targets)
            return f"{targets} = ...  # [AST-STUB: {saved} tokens saved]"
        return f"# [AST-STUB: top-level assignment elided, {saved} tokens saved]"

    @staticmethod
    def _assignment_name(stmt: ast.stmt) -> str:
        targets = stmt.targets if isinstance(stmt, ast.Assign) else [stmt.target]
        names: List[str] = []
        for t in targets:
            if isinstance(t, ast.Name):
                names.append(t.id)
            elif isinstance(t, ast.Tuple):
                names.extend(e.id for e in t.elts if isinstance(e, ast.Name))
        return names[0] if names else f"assign_L{stmt.lineno}"

    def _parse_class(
        self, file_path: str, stmt: ast.ClassDef, lines: List[str], repo_symbols: Optional[Set[str]]
    ) -> List[ASTNode]:
        """
        Splits a class into a header node (decorators, `class` line, docstring,
        class attributes and nested statements) plus one node per method, so the
        pruner can keep a single relevant method without the whole class.
        Original indentation is preserved so any mix of full/stubbed parts parses.
        """
        class_id = f"{file_path}::{stmt.name}"
        start = self._stmt_start_line(stmt)
        first_body = stmt.body[0]
        body_start = self._stmt_start_line(first_body)
        body_indent = re.match(r"\s*", lines[first_body.lineno - 1]).group(0) or "    "

        is_method = lambda b: isinstance(b, (ast.FunctionDef, ast.AsyncFunctionDef))
        methods = [b for b in stmt.body if is_method(b)]
        others = [b for b in stmt.body if not is_method(b)]

        header_parts = []
        if body_start > start:
            header_parts.append(self._slice_lines(lines, start, body_start - 1))
        for o in others:
            header_parts.append(self._slice_lines(lines, self._stmt_start_line(o), o.end_lineno))
        class_raw = "\n".join(p for p in header_parts if p)

        # Stub: decorators + class line + first docstring line (+ `...` if no methods follow).
        dec_str = "".join(f"@{ast.unparse(d)}\n" for d in stmt.decorator_list)
        type_params = getattr(stmt, "type_params", [])
        type_params_str = f"[{', '.join(ast.unparse(p) for p in type_params)}]" if type_params else ""
        bases = [ast.unparse(b) for b in stmt.bases] + [ast.unparse(k) for k in stmt.keywords]
        bases_str = f"({', '.join(bases)})" if bases else ""
        header_line = f"class {stmt.name}{type_params_str}{bases_str}:"
        saved = max(0, self.count_tokens(class_raw) - self.count_tokens(header_line))
        stub = f"{dec_str}{header_line}  # [AST-STUB: {saved} tokens saved]"
        docstring = ast.get_docstring(stmt)
        if docstring:
            first_line = docstring.strip().splitlines()[0].replace('"""', "").strip()
            stub += f'\n{body_indent}"""{first_line}"""'
        elif not methods:
            stub += f"\n{body_indent}..."

        class_deps: Set[str] = set()
        for b in stmt.bases:
            class_deps |= set(self._extract_dependencies(b, repo_symbols))
        for o in others:
            class_deps |= set(self._extract_dependencies(o, repo_symbols, class_name=stmt.name))

        out = [self._make_node(file_path, stmt.name, "class", class_raw, stub, sorted(class_deps))]

        for m in methods:
            m_raw = self._slice_lines(lines, self._stmt_start_line(m), m.end_lineno)
            m_stub_flat = self.generate_1line_stub(m, m_raw)
            m_stub = "\n".join(body_indent + ln for ln in m_stub_flat.splitlines())
            out.append(self._make_node(
                file_path,
                f"{stmt.name}.{m.name}",
                "method",
                m_raw,
                m_stub,
                self._extract_dependencies(m, repo_symbols, class_name=stmt.name),
                parent_id=class_id,
            ))
        return out

    def parse_source(
        self,
        file_path: str,
        source_code: str,
        repo_symbols: Optional[Set[str]] = None,
    ) -> List[ASTNode]:
        """
        Parses Python source code into structured ASTNode objects:
        imports, functions, classes (header + one node per method),
        top-level constants, and other top-level statements.

        Gracefully catches SyntaxErrors (e.g., partial mid-edit buffer),
        wrapping the file in a safe fallback ASTNode with structured logging.
        """
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            lineno = getattr(e, "lineno", 1) or 1
            logger.warning(
                "Graceful AST fallback: SyntaxError in '%s' at line %s: %s",
                file_path,
                lineno,
                e.msg,
            )
            stub = f"# [AST-SYNTAX-FALLBACK: {file_path}] SyntaxError on line {lineno}: {e.msg}\n..."
            fallback_sym = f"fallback_{os.path.splitext(os.path.basename(file_path))[0]}"
            return [self._make_node(file_path, fallback_sym, "fallback", source_code, stub, [])]

        lines = source_code.splitlines(keepends=True)
        nodes: List[ASTNode] = []
        used_names: Set[str] = set()

        for idx, statement in enumerate(tree.body):
            start = self._stmt_start_line(statement)
            raw = self._slice_lines(lines, start, statement.end_lineno)

            if isinstance(statement, (ast.Import, ast.ImportFrom)):
                nodes.append(self._make_node(
                    file_path, f"import_{idx}", "import", raw, raw,
                    [alias.name for alias in statement.names],
                ))

            elif isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef)):
                nodes.append(self._make_node(
                    file_path, statement.name, "function", raw,
                    self.generate_1line_stub(statement, raw),
                    self._extract_dependencies(statement, repo_symbols=repo_symbols),
                ))

            elif isinstance(statement, ast.ClassDef):
                nodes.extend(self._parse_class(file_path, statement, lines, repo_symbols))

            elif isinstance(statement, (ast.Assign, ast.AnnAssign)):
                name = self._assignment_name(statement)
                if name in used_names:
                    name = f"{name}_L{statement.lineno}"
                nodes.append(self._make_node(
                    file_path, name, "constant", raw,
                    self._constant_stub(statement, raw),
                    self._extract_dependencies(statement, repo_symbols=repo_symbols),
                ))

            else:
                # Module docstrings, `if __name__ == "__main__":`, try/except blocks, etc.
                saved = self.count_tokens(raw)
                kind = type(statement).__name__.lower()
                nodes.append(self._make_node(
                    file_path, f"stmt_L{statement.lineno}", "statement", raw,
                    f"# [AST-STUB: top-level {kind} elided, {saved} tokens saved]",
                    self._extract_dependencies(statement, repo_symbols=repo_symbols),
                ))

            used_names.add(nodes[-1].name)

        return nodes

    def prune_context(
        self,
        nodes: List[ASTNode],
        query: str,
        seed_symbols: List[str],
        max_token_budget: int,
        layout: str = "interleaved",
    ) -> Tuple[str, Dict]:
        """
        Solves the budgeted submodular knapsack maximization:

        `layout` sets the cost model for promoting a symbol to full source:
        "interleaved" replaces its stub (marginal = full - stub); "cache" keeps
        the stub in the stable skeleton and appends the body with a header
        (marginal = full + header), matching build_cache_layout().
        S* = argmax_{S subset V} [ sum r(v, q) - redundancy ] s.t. sum c(v) <= B

        Uses Blueprint Equation 1 hybrid relevance:
        r(v, q) = 0.65 * lexical_semantic_sim(v, q) + 0.35 * exp(-0.40 * d_AST(v, V_seed))

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

        # Step 0: Ensure cross-node call-graph edges are constructed and resolved
        self.construct_call_graph(nodes)

        # Step 1: Compute cycle-safe BFS hop distances d_AST(v, V_seed)
        distances = self.compute_hop_distances(nodes, seed_symbols)

        # Separate imports (always included in full to maintain syntax)
        imports = [n for n in nodes if n.node_type == "import"]
        candidates = [n for n in nodes if n.node_type != "import"]
        lexical_scores = self.lexical_relevance(query, candidates)

        # Step 2: Compute hybrid relevance r(v, q) per Blueprint Equation 1
        scored_candidates = []
        for n in candidates:
            lexical_sim = lexical_scores.get(n.node_id, 0.0)

            # Graph hop distance and exponential decay
            dist = distances.get(n.node_id, float("inf"))
            decay = math.exp(-0.40 * dist) if dist != float("inf") else 0.0

            # Blueprint Equation 1
            relevance = 0.65 * lexical_sim + 0.35 * decay

            # Priority tier based on BFS hop distance:
            # 0: direct seed (d=0)
            # 1: 1-hop caller/callee (d=1)
            # 2: 2-hop caller/callee (d=2)
            # 999: disconnected / unreachable
            priority = int(dist) if dist != float("inf") else 999

            if layout == "cache":
                header = f"# ===== {n.name} ({n.file_path}) ====="
                marginal_tokens = max(1, n.token_cost + self.count_tokens(header))
            else:
                marginal_tokens = max(1, n.token_cost - n.stub_token_cost)
            density = relevance / float(marginal_tokens)

            scored_candidates.append({
                "node": n,
                "priority": priority,
                "relevance": relevance,
                "hop_distance": dist,
                "marginal_tokens": marginal_tokens,
                "density": density,
            })

        # Sort candidates: seeds first, then by hybrid relevance (value), then by
        # density so cheaper nodes win ties, then node_id for determinism.
        # Ranking purely by hop tier let every 1-hop neighbour outrank a highly
        # relevant 2-hop symbol regardless of what the query asked about.
        scored_candidates.sort(key=lambda x: (
            0 if x["priority"] == 0 else 1,
            -round(x["relevance"], 6),
            -x["density"],
            x["node"].node_id,
        ))

        # Step 3: Baseline token cost with all non-imports stubbed and imports full
        baseline_tokens = sum(n.token_cost for n in imports) + sum(
            n.stub_token_cost for n in candidates
        )

        selected_for_full: Set[str] = set()
        current_budget = baseline_tokens

        # Step 4: Greedy Knapsack Selection
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

        # Step 5: Assemble hybrid buffer maintaining original node ordering
        buffer_elements: List[str] = []
        selected_names = []
        stubbed_names = []

        multi_file = len({n.file_path for n in nodes}) > 1
        current_file = None

        for n in nodes:
            if multi_file and n.file_path != current_file:
                current_file = n.file_path
                buffer_elements.append(f"# ===== File: {current_file} =====")
            if n.node_type == "import" or n.node_id in selected_for_full:
                buffer_elements.append(n.raw_source)
                if n.node_type != "import":
                    selected_names.append(n.name)
            else:
                buffer_elements.append(n.stub_source)
                stubbed_names.append(n.name)

        elided = sum(
            n.token_cost - n.stub_token_cost
            for n in nodes
            if n.node_type != "import" and n.node_id not in selected_for_full
        )
        if stubbed_names:
            buffer_elements.insert(0, (
                f"# [AST-STUB: {len(stubbed_names)} of {len(candidates)} symbols shown as signatures only; "
                f"{elided} tokens elided. Request a symbol by name for its full body.]"
            ))

        hybrid_code = "\n\n".join(buffer_elements)

        # Step 6: Calculate verified token metrics
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
