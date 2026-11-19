"""
AEGIS-0 PyPI Freshness Grounding Tests (network-free via injected fetcher)
"""

import os
import sys
from datetime import datetime, timedelta, timezone

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TAVILY_DIR = os.path.join(REPO_ROOT, "tavily-freshness")
if TAVILY_DIR not in sys.path:
    sys.path.insert(0, TAVILY_DIR)

from freshness_engine import FreshnessEngine
from package_metadata import PyPIMetadata, parse_dependency_pins


def _iso(days_ago: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat().replace("+00:00", "Z")


FAKE_PYPI = {
    "openai": {
        "info": {"name": "openai", "version": "3.0.0"},
        "releases": {
            "0.28.1": [{"upload_time_iso_8601": _iso(1200)}],
            "1.0.0": [{"upload_time_iso_8601": _iso(1000)}],
            "3.0.0": [{"upload_time_iso_8601": _iso(5)}],
        },
    },
    "requests": {
        "info": {"name": "requests", "version": "2.34.0"},
        "releases": {
            "2.20.0": [{"upload_time_iso_8601": _iso(2700)}],
            "2.34.0": [{"upload_time_iso_8601": _iso(10)}],
        },
    },
    "pydantic": {
        "info": {"name": "pydantic", "version": "4.0.0"},
        "releases": {
            "1.10.0": [{"upload_time_iso_8601": _iso(1500)}],
            "4.0.0": [{"upload_time_iso_8601": _iso(3)}],
        },
    },
}


class _Fetcher:
    def __init__(self):
        self.calls = []

    def __call__(self, name):
        self.calls.append(name)
        return FAKE_PYPI.get(name)


def _engine():
    fetcher = _Fetcher()
    return FreshnessEngine(tavily_api_key="mock", package_metadata=PyPIMetadata(fetcher=fetcher)), fetcher


def test_known_deprecation_uses_real_release_date_for_delta_t():
    engine, _ = _engine()
    v = engine.verify_claim_freshness("openai.ChatCompletion.create")
    assert v["status"] == "STALE"
    assert 999 <= v["delta_t_days"] <= 1001  # days since openai 1.0.0, not the old 850 constant
    assert v["evidence"]["deprecated_in"] == "1.0.0"
    assert any("pypi.org/project/openai" in s["url"] for s in v["sources"])


def test_pin_predating_deprecation_is_explained():
    engine, _ = _engine()
    v = engine.verify_claim_freshness("openai.ChatCompletion.create", dependency_pins={"openai": "0.28.1"})
    assert "requires upgrading to >= 1.0.0" in v["evidence"]["note"]


def test_old_pin_without_deprecation_stays_fresh_but_is_reported():
    engine, _ = _engine()
    v = engine.verify_claim_freshness("requests.get", dependency_pins={"requests": "2.20.0"})
    assert v["status"] == "FRESH"
    assert v["evidence"]["pinned_version"] == "2.20.0"
    assert v["evidence"]["major_versions_behind"] == 0
    assert v["evidence"]["pinned_behind_latest_days"] > 2600


def test_major_versions_behind_lower_agreement():
    engine, _ = _engine()
    one_behind = engine.verify_claim_freshness("requests.get", dependency_pins={"requests": "1.0.0"})
    three_behind = engine.verify_claim_freshness("pydantic.BaseModel", dependency_pins={"pydantic": "1.10.0"})
    assert one_behind["evidence"]["major_versions_behind"] == 1
    assert one_behind["status"] == "FRESH"  # one major behind is a warning, not stale
    assert three_behind["evidence"]["major_versions_behind"] == 3
    assert three_behind["status"] == "STALE"
    assert three_behind["semantic_agreement"] < 0.95


def test_lookups_are_cached_and_failures_tolerated():
    engine, fetcher = _engine()
    for _ in range(3):
        engine.verify_claim_freshness("openai.ChatCompletion.create")
    assert fetcher.calls.count("openai") == 1

    def boom(name):
        raise RuntimeError("network down")

    broken = FreshnessEngine(tavily_api_key="mock", package_metadata=PyPIMetadata(fetcher=boom))
    v = broken.verify_claim_freshness("openai.ChatCompletion.create")
    assert v["status"] == "STALE"          # registry still decides
    assert v["evidence"] is None           # no grounding available


def test_offline_mode_makes_no_requests():
    pypi = PyPIMetadata(offline=True)
    assert pypi.package("openai") is None
    assert pypi.requests_made == 0


def test_registry_hits_do_not_spend_tavily_credits(monkeypatch):
    import freshness_engine

    calls = []
    monkeypatch.setattr(
        freshness_engine.FreshnessEngine, "_query_tavily_api",
        lambda self, claim, key: calls.append(claim) or {},
    )
    engine = FreshnessEngine(tavily_api_key="tvly-real", package_metadata=PyPIMetadata(offline=True))
    engine.verify_claim_freshness("openai.ChatCompletion.create")
    assert calls == []


def test_parse_dependency_pins(tmp_path):
    (tmp_path / "requirements.txt").write_text(
        "fastapi>=0.111.0\nuvicorn[standard]>=0.30.0\n# comment\nPyYAML==6.0.1  # pinned\nrequests\n",
        encoding="utf-8",
    )
    sub = tmp_path / "service"
    sub.mkdir()
    (sub / "pyproject.toml").write_text(
        '[project]\nname = "x"\ndependencies = ["pydantic~=2.7", "httpx>=0.27"]\n', encoding="utf-8"
    )
    pins = parse_dependency_pins(str(tmp_path))
    assert pins["fastapi"] == "0.111.0"
    assert pins["uvicorn"] == "0.30.0"
    assert pins["pyyaml"] == "6.0.1"
    assert pins["pydantic"] == "2.7"
    assert pins["httpx"] == "0.27"
    assert "requests" not in pins
