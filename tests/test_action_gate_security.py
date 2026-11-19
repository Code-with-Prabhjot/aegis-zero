"""
AEGIS-0 Action Gate Security Regression Tests
Covers forgery with a client-chosen secret, replay, unknown action IDs,
and approval expiry on POST /api/action/approve.
"""

import os
import sys
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for sub in ("", "security-gate", "tavily-freshness"):
    path = os.path.join(REPO_ROOT, sub)
    if path not in sys.path:
        sys.path.insert(0, path)

import orchestrator.main as main_mod
from orchestrator.main import app, bifrost
from privacy_guard import PrivacyGuard


def _quarantine(client: TestClient, session_id: str, target: str = "gate_target.py") -> dict:
    bifrost.mock_mode = True
    bifrost.clear_chaos_fault()
    bifrost.reset_circuit_breakers()
    res = client.post(
        "/api/orchestrate",
        json={
            "session_id": session_id,
            "prompt": f"write patch to {target}",
            "proposed_action": "write_file",
            "proposed_target": target,
        },
    )
    assert res.status_code == 200
    action = res.json()["action_quarantine"]
    assert action is not None
    assert action["signed_payload"]
    assert action["expires_at"]
    return action


def _approve(client: TestClient, action: dict, **overrides):
    body = {
        "action_id": action["action_id"],
        "hmac_token": action["hmac_token"],
        "payload": action["signed_payload"],
    }
    body.update(overrides)
    return client.post("/api/action/approve", json=body)


def test_client_supplied_secret_cannot_forge_approval():
    """An attacker who signs with their own secret must be rejected, even if they send it."""
    client = TestClient(app)
    action = _quarantine(client, "gate_forge")

    attacker_secret = "attacker-chosen-secret"
    malicious_payload = "write:/etc/passwd:" + "0" * 64
    forged = PrivacyGuard().generate_hmac_action_token(
        action_id=action["action_id"], payload=malicious_payload, secret_key=attacker_secret
    )

    res = _approve(
        client,
        action,
        hmac_token=forged,
        payload=malicious_payload,
        secret_key=attacker_secret,
    )
    assert res.status_code == 403
    assert "INVALID_HMAC_SIGNATURE" in res.json()["detail"]

    # Forged signature over the *real* payload with the attacker secret is also rejected.
    forged_same_payload = PrivacyGuard().generate_hmac_action_token(
        action_id=action["action_id"], payload=action["signed_payload"], secret_key=attacker_secret
    )
    res = _approve(client, action, hmac_token=forged_same_payload, secret_key=attacker_secret)
    assert res.status_code == 403

    # The legitimate approval still works afterwards.
    assert _approve(client, action).status_code == 200


def test_approval_cannot_be_replayed():
    client = TestClient(app)
    action = _quarantine(client, "gate_replay")

    first = _approve(client, action)
    assert first.status_code == 200
    assert first.json()["status"] == "EXECUTED"

    replay = _approve(client, action)
    assert replay.status_code == 409
    assert "ACTION_ALREADY_CONSUMED" in replay.json()["detail"]


def test_unknown_action_id_is_rejected_even_with_valid_server_signature():
    """Self-signed actions the server never quarantined must not execute."""
    client = TestClient(app)
    action_id = "act_never_quarantined"
    payload = "write:anything.py:" + "a" * 64
    token = PrivacyGuard().generate_hmac_action_token(
        action_id=action_id, payload=payload, secret_key=main_mod.AEGIS_SECRET_KEY
    )
    res = client.post(
        "/api/action/approve",
        json={"action_id": action_id, "hmac_token": token, "payload": payload},
    )
    assert res.status_code == 404
    assert "UNKNOWN_ACTION" in res.json()["detail"]


def test_expired_approval_is_rejected():
    client = TestClient(app)
    action = _quarantine(client, "gate_expiry")

    # Simulate the approval window elapsing.
    main_mod.pending_action_signatures[action["action_id"]]["expires_at"] = (
        datetime.now(timezone.utc) - timedelta(seconds=1)
    )

    res = _approve(client, action)
    assert res.status_code == 410
    assert "ACTION_EXPIRED" in res.json()["detail"]

    # Once expired, the action is gone for good.
    assert _approve(client, action).status_code == 404


def test_rejections_are_recorded_in_audit_ledger():
    client = TestClient(app)
    action = _quarantine(client, "gate_audit")
    _approve(client, action, hmac_token="0" * 64)

    ledger = client.get("/api/audit/export").json()
    assert ledger["chain_valid"] is True
    rejected = [
        e for e in ledger["ledger"]
        if e["event_type"] == "HMAC_REJECTED"
    ]
    assert rejected, "403 rejections must leave an audit trail"


def test_cors_only_allows_configured_origins():
    client = TestClient(app)
    allowed = client.options(
        "/api/telemetry",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"},
    )
    assert allowed.headers.get("access-control-allow-origin") == "http://localhost:3000"
    evil = client.options(
        "/api/action/approve",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert evil.headers.get("access-control-allow-origin") is None
