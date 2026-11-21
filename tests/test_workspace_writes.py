"""
AEGIS-0 Approved-Write Workspace Tests
Approval writes the patch to disk inside a confined workspace; rollback
restores the original bytes; path escapes and stale diffs are refused.
"""

import os
import sys

import pytest
from fastapi.testclient import TestClient

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
for sub in ("", "security-gate", "tavily_freshness"):
    path = os.path.join(REPO_ROOT, sub)
    if path not in sys.path:
        sys.path.insert(0, path)

import orchestrator.main as main_mod
from orchestrator.main import app, bifrost
from orchestrator.workspace import Workspace, WorkspaceError


@pytest.fixture
def client():
    bifrost.mock_mode = True
    bifrost.clear_chaos_fault()
    bifrost.reset_circuit_breakers()
    # Drain any snapshots left by other tests so rollback targets ours.
    while main_mod.audit_ledger.peek_last_diff():
        main_mod.audit_ledger.rollback_last_diff()
    main_mod.applied_writes.clear()
    return TestClient(app)


def _quarantine(client, target, session):
    res = client.post("/api/orchestrate", json={
        "session_id": session,
        "prompt": f"write patch to {target}",
        "proposed_action": "write_file",
        "proposed_target": target,
    })
    assert res.status_code == 200, res.text
    return res.json()


def _approve(client, action):
    return client.post("/api/action/approve", json={
        "action_id": action["action_id"],
        "hmac_token": action["hmac_token"],
        "payload": action["signed_payload"],
    })


def _path(rel):
    return os.path.join(main_mod.workspace.root, rel)


def test_workspace_is_isolated_for_tests():
    assert main_mod.workspace.root != os.path.realpath(REPO_ROOT)
    assert "aegis-test-workspace-" in main_mod.workspace.root


def test_approval_writes_file_and_rollback_restores_original(client):
    rel = "pkg/existing_module.py"
    os.makedirs(os.path.dirname(_path(rel)), exist_ok=True)
    original = "# original contents\r\nVALUE = 1\n"
    with open(_path(rel), "w", encoding="utf-8", newline="") as fh:
        fh.write(original)

    data = _quarantine(client, rel, "ws_existing")
    res = _approve(client, data["action_quarantine"])
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "EXECUTED"
    assert body["written_path"] == rel

    with open(_path(rel), encoding="utf-8", newline="") as fh:
        assert fh.read() == data["generated_code"]

    rb = client.post("/api/action/rollback").json()
    assert rb["status"] == "ROLLED_BACK"
    assert rb["file_restored"] is True
    with open(_path(rel), encoding="utf-8", newline="") as fh:
        assert fh.read() == original  # byte-exact, including CRLF


def test_rollback_of_new_file_deletes_it(client):
    rel = "brand_new_file.py"
    assert not os.path.exists(_path(rel))
    data = _quarantine(client, rel, "ws_new")
    assert _approve(client, data["action_quarantine"]).status_code == 200
    assert os.path.isfile(_path(rel))

    client.post("/api/action/rollback")
    assert not os.path.exists(_path(rel))


@pytest.mark.parametrize("target", [
    "../escape.py",
    "nested/../../escape.py",
    "/etc/passwd",
    "C:\\Windows\\system.ini",
    ".git/config",
])
def test_targets_outside_workspace_are_rejected_before_dispatch(client, target):
    before = bifrost.total_requests
    res = client.post("/api/orchestrate", json={
        "session_id": "ws_escape",
        "prompt": "write something",
        "proposed_action": "write_file",
        "proposed_target": target,
    })
    assert res.status_code == 400
    assert "TARGET_OUTSIDE_WORKSPACE" in res.json()["detail"]
    assert bifrost.total_requests == before, "no tokens may be spent on a rejected target"


def test_stale_diff_is_refused_if_file_changed_after_quarantine(client):
    rel = "stale_target.py"
    data = _quarantine(client, rel, "ws_stale")
    with open(_path(rel), "w", encoding="utf-8") as fh:
        fh.write("# someone else edited this meanwhile\n")

    res = _approve(client, data["action_quarantine"])
    assert res.status_code == 409
    assert "TARGET_CHANGED" in res.json()["detail"]
    with open(_path(rel), encoding="utf-8") as fh:
        assert "someone else" in fh.read()


def test_rollback_refuses_to_clobber_later_edits(client):
    rel = "edited_after_apply.py"
    data = _quarantine(client, rel, "ws_later_edit")
    assert _approve(client, data["action_quarantine"]).status_code == 200
    with open(_path(rel), "a", encoding="utf-8") as fh:
        fh.write("\n# manual follow-up edit\n")

    res = client.post("/api/action/rollback")
    assert res.status_code == 409
    assert "TARGET_MODIFIED_SINCE_APPLY" in res.json()["detail"]
    with open(_path(rel), encoding="utf-8") as fh:
        assert "manual follow-up edit" in fh.read()


def test_shell_actions_are_approved_but_never_executed(client):
    res = client.post("/api/orchestrate", json={
        "session_id": "ws_shell",
        "prompt": "run cleanup",
        "proposed_action": "exec_shell",
        "proposed_target": "rm -rf /",
    })
    assert res.status_code == 200
    body = _approve(client, res.json()["action_quarantine"]).json()
    assert body["status"] == "APPROVED"
    assert body["written_path"] is None


def test_symlink_escape_is_rejected(tmp_path):
    root = tmp_path / "ws"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    try:
        os.symlink(outside, root / "link", target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not permitted on this platform/user")
    with pytest.raises(WorkspaceError):
        Workspace(str(root)).resolve("link/evil.py")
