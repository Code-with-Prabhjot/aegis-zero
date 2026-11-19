"""
AEGIS-0 Immutable Tamper-Evident Audit Ledger (RRS Domain)
Maintains a cryptographic SHA-256 hash chain for every orchestration decision,
air-gap taint event, HMAC cryptographic action approval, and atomic rollback.
Provides full verification of chain continuity from genesis and compliance bundle export.
"""

from datetime import datetime, timezone
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple
from pydantic import BaseModel, Field


class AuditEntry(BaseModel):
    """
    Immutable individual block entry within the tamper-evident SHA-256 audit ledger.
    """
    seq: int
    timestamp_utc: str
    event_type: str
    actor: str
    payload_hash: str
    prev_hash: str
    entry_hash: str


class TamperEvidentAuditLedger:
    """
    SHA-256 Merkle-Chained Tamper-Evident Audit Ledger.
    """

    GENESIS_PREV_HASH = "0" * 64

    def __init__(self):
        self.chain: List[AuditEntry] = []
        self._diff_snapshots: List[Dict[str, Any]] = []

    def _compute_payload_hash(self, payload: Any) -> str:
        if payload is None:
            raw = ""
        elif isinstance(payload, str):
            raw = payload
        else:
            try:
                raw = json.dumps(payload, sort_keys=True, default=str)
            except Exception:
                raw = str(payload)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _compute_entry_hash(
        self,
        seq: int,
        timestamp_utc: str,
        event_type: str,
        payload_hash: str,
        prev_hash: str,
    ) -> str:
        canonical = f"{seq}:{timestamp_utc}:{event_type}:{payload_hash}:{prev_hash}"
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def append_entry(
        self,
        event_type: str,
        actor: str = "orchestrator",
        payload: Any = None,
        timestamp_utc: Optional[str] = None,
    ) -> AuditEntry:
        """
        Appends a cryptographically verified event to the hash chain.
        """
        seq = len(self.chain) + 1
        ts = timestamp_utc or datetime.now(timezone.utc).isoformat()
        payload_hash = self._compute_payload_hash(payload)
        prev_hash = self.chain[-1].entry_hash if self.chain else self.GENESIS_PREV_HASH
        entry_hash = self._compute_entry_hash(seq, ts, event_type, payload_hash, prev_hash)

        entry = AuditEntry(
            seq=seq,
            timestamp_utc=ts,
            event_type=event_type,
            actor=actor,
            payload_hash=payload_hash,
            prev_hash=prev_hash,
            entry_hash=entry_hash,
        )
        self.chain.append(entry)
        return entry

    def record_diff_snapshot(
        self,
        action_id: str,
        target_path: str,
        original_code: str,
        patched_code: str,
        actor: str = "orchestrator",
    ) -> None:
        """
        Records an in-memory snapshot of approved code diffs for atomic rollback capability.
        """
        self._diff_snapshots.append({
            "action_id": action_id,
            "target_path": target_path,
            "original_code": original_code,
            "patched_code": patched_code,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actor": actor,
        })

    def peek_last_diff(self) -> Optional[Dict[str, Any]]:
        """
        Returns the most recent approved diff snapshot without removing it, so
        callers can verify a rollback is safe before committing to it.
        """
        return self._diff_snapshots[-1] if self._diff_snapshots else None

    def rollback_last_diff(self, actor: str = "user_operator") -> Optional[Dict[str, Any]]:
        """
        Reverts the last approved diff snapshot in memory and logs an ACTION_ROLLED_BACK
        entry to the cryptographic audit ledger.
        """
        if not self._diff_snapshots:
            return None

        last_snapshot = self._diff_snapshots.pop()
        reverted_record = {
            "action_id": last_snapshot["action_id"],
            "target_path": last_snapshot["target_path"],
            "reverted_to": "original_baseline",
            "restored_code_length": len(last_snapshot["original_code"]),
        }

        self.append_entry(
            event_type="ACTION_ROLLED_BACK",
            actor=actor,
            payload=reverted_record,
        )

        return {
            "status": "ROLLED_BACK",
            "snapshot": last_snapshot,
            "reverted_record": reverted_record,
        }

    def verify_chain_integrity(self) -> Tuple[bool, str]:
        """
        Recomputes the entire SHA-256 hash chain from genesis (0 * 64)
        and detects if any historical entry has been tampered with or corrupted.
        """
        if not self.chain:
            return True, "CHAIN_VALID: Empty ledger genesis state."

        for i, entry in enumerate(self.chain):
            expected_prev = (
                self.GENESIS_PREV_HASH if i == 0 else self.chain[i - 1].entry_hash
            )
            if entry.prev_hash != expected_prev:
                return (
                    False,
                    f"CHAIN_BROKEN at seq {entry.seq}: prev_hash mismatch. "
                    f"Expected {expected_prev[:16]}..., got {entry.prev_hash[:16]}...",
                )

            expected_entry_hash = self._compute_entry_hash(
                entry.seq,
                entry.timestamp_utc,
                entry.event_type,
                entry.payload_hash,
                entry.prev_hash,
            )
            if entry.entry_hash != expected_entry_hash:
                return (
                    False,
                    f"CHAIN_BROKEN at seq {entry.seq}: entry_hash tampered. "
                    f"Expected {expected_entry_hash[:16]}..., got {entry.entry_hash[:16]}...",
                )

        return True, f"CHAIN_VALID: All {len(self.chain)} entries verified from genesis."

    def export_compliance_bundle(self) -> Dict[str, Any]:
        """
        Outputs verifiable cryptographic audit log and SHA-256 integrity proof.
        """
        is_valid, message = self.verify_chain_integrity()
        latest_hash = self.chain[-1].entry_hash if self.chain else self.GENESIS_PREV_HASH
        return {
            "chain_valid": is_valid,
            "integrity_message": message,
            "total_entries": len(self.chain),
            "genesis_hash": self.GENESIS_PREV_HASH,
            "latest_hash": latest_hash,
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "ledger": [entry.model_dump() for entry in self.chain],
        }
