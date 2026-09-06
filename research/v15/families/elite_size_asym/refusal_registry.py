"""Per-arm refusal registry for A5-V15-F1 (p3_freeze_amendment_1).

"a refused decision never becomes a fill and never synthesizes data;
refusals are recorded in a per-arm refusal registry."

The registry is append-only, deduplicated on ``(decision_date, symbol,
reason_code)`` (append-once semantics, the inherited registry convention),
ordered canonically, and digested with sha256 over the canonical JSON of its
records.  It carries NO wall-clock field: two identical runs produce
byte-identical registries and digests.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Optional, Tuple

REASON_WINDOW_HOLE = "window_hole"

SCHEMA = "v15_f1_refusal_registry_v1"


class RefusalRegistry:
    """Append-once registry of refused symbol-date decisions (one arm)."""

    def __init__(self) -> None:
        self._rows: List[Dict[str, str]] = []
        self._seen: set[Tuple[str, str, str]] = set()

    def record(
        self, decision_date: str, symbol: str, reason_code: str, detail: str
    ) -> bool:
        """Append one refusal; returns False when already present (once)."""
        key = (str(decision_date), str(symbol), str(reason_code))
        if key in self._seen:
            return False
        self._seen.add(key)
        self._rows.append(
            {
                "decision_date": key[0],
                "symbol": key[1],
                "reason_code": key[2],
                "detail": str(detail),
            }
        )
        return True

    def record_window_hole(
        self, decision_date: str, symbol: str, detail: str
    ) -> bool:
        return self.record(
            decision_date, symbol, REASON_WINDOW_HOLE, detail
        )

    def records(self) -> Tuple[Dict[str, str], ...]:
        """Canonical record order: (date, symbol, reason) ascending."""
        return tuple(sorted(self._rows, key=lambda r: (r["decision_date"], r["symbol"], r["reason_code"])))

    def __len__(self) -> int:
        return len(self._rows)

    def digest(self) -> str:
        payload = {
            "schema": SCHEMA,
            "records": list(self.records()),
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def summary(self) -> Dict[str, Any]:
        by_reason: Dict[str, int] = {}
        by_symbol: Dict[str, int] = {}
        for row in self.records():
            by_reason[row["reason_code"]] = by_reason.get(row["reason_code"], 0) + 1
            by_symbol[row["symbol"]] = by_symbol.get(row["symbol"], 0) + 1
        return {
            "schema": SCHEMA,
            "n_refusals": len(self._rows),
            "by_reason": dict(sorted(by_reason.items())),
            "by_symbol": dict(sorted(by_symbol.items())),
            "digest": self.digest(),
        }


def refusal_registry_digest(records: Optional[List[Dict[str, str]]]) -> str:
    """Digest of a canonical record list (helper for replay comparisons)."""
    payload = {"schema": SCHEMA, "records": list(records or [])}
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


__all__ = [
    "REASON_WINDOW_HOLE",
    "RefusalRegistry",
    "refusal_registry_digest",
]
