"""Per-arm refusal registry for TAKER-SAT (p3_freeze_amendment_1).

Every refused decision is recorded -- per (metrics date, symbol) feature
refusals (window hole fraction exceeded, churn endpoint missing/undefined,
non-finite feature) and per-date cycle-level refusals (fewer than 10
available names -> the cycle stays flat).  A refused decision never becomes
a fill and never synthesizes data; the registry is append-once (an
identical refusal is deduplicated, never double-counted) and its canonical
digest (sha256 over the sorted entry set) travels inside every cell payload
so the scored driver and audits can pin the refusal surface.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping, Optional

from research.adapter_v10.protocol import ContractViolation

SCHEMA_VERSION = "v15i.taker_sat.refusals.v1"


def _canonical_entry(entry: Mapping[str, Any]) -> str:
    return json.dumps(dict(entry), sort_keys=True, separators=(",", ":"))


def _canonical(entries) -> str:
    return "[" + ",".join(sorted(_canonical_entry(entry) for entry in entries)) + "]"


class RefusalRegistry:
    """Append-once registry of refused decisions (deterministic digest)."""

    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []
        self._keys: set[tuple] = set()

    def record(
        self,
        date: str,
        symbol: str,
        reason: str,
        *,
        detail: Optional[Mapping[str, Any]] = None,
    ) -> bool:
        """Record one refusal; returns False when it was already present."""
        entry = {
            "date": str(date),
            "symbol": "" if symbol is None else str(symbol),
            "reason": str(reason),
            "detail": dict(sorted(dict(detail or {}).items())),
        }
        key = (
            entry["date"],
            entry["symbol"],
            entry["reason"],
            _canonical_entry(entry["detail"]),
        )
        if key in self._keys:
            return False
        self._keys.add(key)
        self._entries.append(entry)
        return True

    def entries(self) -> list[dict[str, Any]]:
        """All recorded refusals, deterministically sorted."""
        return sorted(self._entries, key=_canonical_entry)

    def __len__(self) -> int:
        return len(self._entries)

    def count_by_reason(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for entry in self._entries:
            counts[entry["reason"]] = counts.get(entry["reason"], 0) + 1
        return dict(sorted(counts.items()))

    def digest(self) -> str:
        """sha256 over the canonical sorted entry set (registry identity)."""
        return hashlib.sha256(_canonical(self.entries()).encode()).hexdigest()

    def to_payload(self) -> dict[str, Any]:
        return {
            "schema": SCHEMA_VERSION,
            "count": len(self._entries),
            "by_reason": self.count_by_reason(),
            "digest": self.digest(),
            "entries": self.entries(),
        }

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "RefusalRegistry":
        registry = cls()
        for entry in list(payload.get("entries") or []):
            registry.record(
                entry.get("date", ""),
                entry.get("symbol", ""),
                entry.get("reason", ""),
                detail=dict(entry.get("detail") or {}),
            )
        return registry


__all__ = ["RefusalRegistry", "SCHEMA_VERSION"]
