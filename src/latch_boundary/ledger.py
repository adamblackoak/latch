from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Iterable


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def digest(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


class HashLedger:
    """Append-only JSONL ledger with a simple hash chain."""

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else None
        self._entries: list[dict[str, Any]] = []
        if self.path and self.path.exists():
            self._entries = [json.loads(line) for line in self.path.read_text(encoding="utf-8").splitlines() if line.strip()]

    @property
    def entries(self) -> tuple[dict[str, Any], ...]:
        return tuple(self._entries)

    def append(self, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
        previous_hash = self._entries[-1]["event_hash"] if self._entries else None
        body = {
            "sequence": len(self._entries) + 1,
            "event_type": event_type,
            "payload": payload,
            "previous_hash": previous_hash,
        }
        entry = {**body, "event_hash": digest(body)}
        self._entries.append(entry)
        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as f:
                f.write(canonical_json(entry) + "\n")
        return entry

    def verify(self) -> tuple[bool, str]:
        previous_hash = None
        for index, entry in enumerate(self._entries, start=1):
            if entry.get("sequence") != index:
                return False, f"sequence mismatch at event {index}"
            if entry.get("previous_hash") != previous_hash:
                return False, f"hash-chain link mismatch at event {index}"
            body = {k: entry[k] for k in ("sequence", "event_type", "payload", "previous_hash")}
            expected = digest(body)
            if entry.get("event_hash") != expected:
                return False, f"event hash mismatch at event {index}"
            previous_hash = expected
        return True, f"verified {len(self._entries)} event(s)"

    @classmethod
    def from_entries(cls, entries: Iterable[dict[str, Any]]) -> "HashLedger":
        ledger = cls()
        ledger._entries = [dict(x) for x in entries]
        return ledger
