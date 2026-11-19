"""
AEGIS-0 Freshness Engine Precision Regression Tests
Covers false positives on builtins/stdlib, syntax-safe auto-patching,
live Tavily deprecation detection, and live-query caching.
"""

import ast
import os
import sys

import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TAVILY_DIR = os.path.join(REPO_ROOT, "tavily-freshness")
if TAVILY_DIR not in sys.path:
    sys.path.insert(0, TAVILY_DIR)

from freshness_engine import FreshnessEngine


PLAIN_PYTHON = '''import json
import os

def collect(rows):
    out = []
    for r in rows:
        out.append(r)
    cfg = dict(a=1)
    print(len(out), cfg.keys(), os.getcwd())
    return json.dumps(out)
'''


def test_builtins_and_stdlib_produce_no_claims():
    engine = FreshnessEngine(tavily_api_key="mock")
    assert engine.extract_code_claims(PLAIN_PYTHON) == []


def test_plain_list_append_is_never_rewritten():
    engine = FreshnessEngine(tavily_api_key="mock")
    result = engine.audit_and_patch(PLAIN_PYTHON)
    assert result["patched_code"] == PLAIN_PYTHON
    assert result["patches_applied"] == []
    assert result["all_fresh"] is True


def test_bare_import_is_not_stale():
    engine = FreshnessEngine(tavily_api_key="mock")
    assert engine.verify_claim_freshness("openai")["status"] == "FRESH"
    assert engine.verify_claim_freshness("dict")["status"] == "FRESH"
    assert engine.verify_claim_freshness("stripe")["status"] == "FRESH"


def test_pandas_append_only_patched_on_dataframes():
    engine = FreshnessEngine(tavily_api_key="mock")
    code = '''import pandas as pd

def build(rows):
    df = pd.DataFrame(rows)
    df = df.append({"a": 1}, ignore_index=True)
    names = []
    names.append("x")
    return df, names
'''
    result = engine.audit_and_patch(code)
    patched = result["patched_code"]
    ast.parse(patched)
    assert 'df = pd.concat([df, pd.DataFrame([{"a": 1}])], ignore_index=True)' in patched
    assert 'names.append("x")' in patched


def test_pydantic_methods_patched_only_when_pydantic_imported():
    engine = FreshnessEngine(tavily_api_key="mock")
    with_pydantic = '''from pydantic import BaseModel

class Item(BaseModel):
    x: int

def load(raw):
    item = Item.parse_obj(raw)
    return item.dict()
'''
    patched = engine.audit_and_patch(with_pydantic)["patched_code"]
    assert "Item.model_validate(raw)" in patched
    assert "item.model_dump()" in patched
    ast.parse(patched)

    without_pydantic = "def f(obj):\n    return obj.dict()\n"
    assert engine.audit_and_patch(without_pydantic)["patched_code"] == without_pydantic


def test_openai_patch_keeps_module_import_and_scopes_client():
    engine = FreshnessEngine(tavily_api_key="mock")
    code = '''import openai

openai.api_key = "set-elsewhere"

def helper():
    return 1

def ask(prompt):
    """Ask the model."""
    return openai.ChatCompletion.create(model="m", messages=[prompt])
'''
    patched = engine.audit_and_patch(code)["patched_code"]
    tree = ast.parse(patched)
    assert "import openai\n" in patched  # other openai.* usages still resolve
    assert "from openai import OpenAI" in patched

    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    helper_src = ast.unparse(funcs["helper"])
    ask_src = ast.unparse(funcs["ask"])
    assert "OpenAI()" not in helper_src, "client must be created where it's used"
    assert "client = OpenAI()" in ask_src
    assert "client.chat.completions.create" in ask_src


def test_patch_that_breaks_syntax_is_rolled_back():
    engine = FreshnessEngine(tavily_api_key="mock")
    # A replacement that would produce invalid code must be discarded.
    verifications = [{
        "claim": "custom",
        "is_stale": True,
        "patch": {
            "claim": "custom",
            "deprecated_pattern": "from broken import thing",
            "replacement_pattern": "from broken import (",
        },
    }]
    src = "from broken import thing\n"
    patched, applied = engine.auto_patch_code(src, verifications)
    assert patched == src
    assert applied == []


class _FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


class _FakeClient:
    calls = 0
    payload = {}
    last_headers = None
    last_json = None

    def __init__(self, *a, **kw):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def post(self, url, json=None, headers=None):
        _FakeClient.calls += 1
        _FakeClient.last_headers = headers
        _FakeClient.last_json = json
        return _FakeResponse(_FakeClient.payload)


@pytest.fixture
def fake_tavily(monkeypatch):
    import freshness_engine

    _FakeClient.calls = 0
    monkeypatch.setattr(freshness_engine.httpx, "Client", _FakeClient)
    return _FakeClient


def test_live_tavily_detects_deprecated_wording(fake_tavily):
    fake_tavily.payload = {"results": [
        {"title": "Migration guide", "url": "u1",
         "content": "ChatCompletion.create is deprecated since openai 1.0; use client.chat.completions."},
        {"title": "Changelog", "url": "u2",
         "content": "The ChatCompletion interface was removed in v1.0.0 (deprecation notice)."},
        {"title": "Unrelated", "url": "u3", "content": "General overview of the SDK."},
    ]}
    engine = FreshnessEngine(tavily_api_key="tvly-real-key")
    result = engine._query_tavily_api("openai.ChatCompletion.create", "tvly-real-key")
    assert result["deprecation_indicator"] == 1
    # API key goes in the Authorization header, never the JSON body.
    assert fake_tavily.last_headers["Authorization"] == "Bearer tvly-real-key"
    assert "api_key" not in fake_tavily.last_json


def test_live_tavily_ignores_unrelated_legacy_wording(fake_tavily):
    fake_tavily.payload = {"results": [
        {"title": "Chat completions", "url": "u1",
         "content": "client.chat.completions.create is the current API. Legacy docs are archived."},
        {"title": "Other library", "url": "u2", "content": "SomethingElse is deprecated."},
    ]}
    engine = FreshnessEngine(tavily_api_key="tvly-real-key")
    result = engine._query_tavily_api("openai.chat.completions.create", "tvly-real-key")
    assert result["deprecation_indicator"] == 0


def test_live_queries_are_cached(fake_tavily):
    fake_tavily.payload = {"results": [{"title": "t", "url": "u", "content": "requests.get docs"}]}
    engine = FreshnessEngine(tavily_api_key="tvly-real-key")
    for _ in range(3):
        engine.verify_claim_freshness("requests.get")
    assert fake_tavily.calls == 1
    assert engine.live_queries_made == 1
    assert engine.live_cache_hits == 2


def test_builtins_never_reach_tavily(fake_tavily):
    fake_tavily.payload = {"results": []}
    engine = FreshnessEngine(tavily_api_key="tvly-real-key")
    engine.audit_and_patch(PLAIN_PYTHON)
    assert fake_tavily.calls == 0
