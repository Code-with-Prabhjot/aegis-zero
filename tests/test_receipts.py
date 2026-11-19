"""
AEGIS-0 Per-Run Token Receipt Tests
"""

import json
import os
import subprocess
import sys

from fastapi.testclient import TestClient

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for sub in ("", "security-gate", "tavily-freshness"):
    path = os.path.join(REPO_ROOT, sub)
    if path not in sys.path:
        sys.path.insert(0, path)

from orchestrator.main import app, bifrost
from orchestrator.receipts import verify_receipt


def _client():
    bifrost.mock_mode = True
    bifrost.clear_chaos_fault()
    bifrost.reset_circuit_breakers()
    return TestClient(app)


def test_orchestrate_issues_verifiable_receipt():
    client = _client()
    res = client.post("/api/orchestrate", json={
        "session_id": "receipt_basic",
        "prompt": "Refactor ask_gpt to use openai",
        "repo_path": os.path.join(REPO_ROOT, "security-gate"),
        "proposed_action": "write_file",
        "proposed_target": "receipt_target.py",
    }).json()
    run_id = res["run_id"]
    assert run_id.startswith("run_")

    receipt = client.get(f"/api/receipts/{run_id}").json()
    assert verify_receipt(receipt)
    assert receipt["tokens"]["repository_raw"] == res["raw_tokens"]
    assert receipt["tokens"]["context_sent"] == res["pruned_tokens"]
    assert receipt["cost_usd"]["actual"] == res["cost_usd"]
    assert receipt["cost_usd"]["without_pruning_estimate"] >= receipt["cost_usd"]["actual"]
    assert receipt["action_gate"]["target"] == "receipt_target.py"
    assert receipt["audit"]["chain_valid"] is True
    assert any(f["claim"] == "openai.ChatCompletion.create" for f in receipt["freshness"])

    page = client.get(f"/api/receipts/{run_id}?format=html")
    assert page.status_code == 200
    assert page.headers["content-type"].startswith("text/html")
    assert run_id in page.text and receipt["receipt_sha256"] in page.text

    listing = client.get("/api/receipts").json()
    assert listing[0]["run_id"] == run_id


def test_tampered_receipt_fails_verification():
    client = _client()
    run_id = client.post("/api/orchestrate", json={
        "session_id": "receipt_tamper", "prompt": "fibonacci please",
    }).json()["run_id"]
    receipt = client.get(f"/api/receipts/{run_id}").json()
    receipt["cost_usd"]["actual"] = 0.0
    assert not verify_receipt(receipt)


def test_secret_bearing_prompt_is_redacted():
    client = _client()
    run_id = client.post("/api/orchestrate", json={
        "session_id": "receipt_secret",
        "prompt": "use key AKIAIOSFODNN7EXAMPLE to deploy",
    }).json()["run_id"]
    receipt = client.get(f"/api/receipts/{run_id}").json()
    assert "AKIA" not in json.dumps(receipt)
    assert receipt["prompt"].startswith("[REDACTED")
    html = client.get(f"/api/receipts/{run_id}?format=html").text
    assert "AKIA" not in html


def test_unknown_receipt_is_404():
    assert _client().get("/api/receipts/run_missing").status_code == 404


def test_html_escapes_untrusted_content():
    client = _client()
    run_id = client.post("/api/orchestrate", json={
        "session_id": "receipt_xss", "prompt": "<script>alert(1)</script> fibonacci",
    }).json()["run_id"]
    html = client.get(f"/api/receipts/{run_id}?format=html").text
    assert "<script>alert(1)</script>" not in html
    assert "&lt;script&gt;" in html


def test_cli_writes_receipt(tmp_path):
    out = tmp_path / "receipt.json"
    env = dict(os.environ, AEGIS_PYPI_OFFLINE="1")
    res = subprocess.run(
        [sys.executable, os.path.join(REPO_ROOT, "aegis_cli.py"), "Audit token efficiency",
         "--repo", "./orchestrator", "--dry-run", "--receipt", str(out)],
        cwd=REPO_ROOT, capture_output=True, text=True, timeout=60, env=env,
    )
    assert res.returncode == 0, res.stderr
    receipt = json.loads(out.read_text(encoding="utf-8"))
    assert verify_receipt(receipt)
    assert receipt["status"] == "DRY_RUN"
    assert receipt["tokens"]["repository_raw"] > receipt["tokens"]["context_sent"]
