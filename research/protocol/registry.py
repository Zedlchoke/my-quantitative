"""Append-only experiment registry: ``results/registry/experiments.jsonl``.

One JSON object per line.  There is deliberately **no** rewrite/delete API:
``append`` is the only writer, it creates the file when missing and never
rewrites existing content.  Every line must contain at least ``experiment_id``
and ``verdict``; ``append`` stamps ``appended_at`` (UTC ISO-8601) which
``verify_append_only`` uses to confirm line order is monotonic.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_REGISTRY_DIR = Path("results") / "registry"
DEFAULT_REGISTRY_PATH = DEFAULT_REGISTRY_DIR / "experiments.jsonl"

REQUIRED_ENTRY_FIELDS = ("experiment_id", "verdict")

#: Sprint V3 append-only entry kinds (PLAN section 11). Every entry that
#: declares a ``kind`` must satisfy the per-kind required-field contract;
#: verify/finalize entries additionally need the verification identity block.
ENTRY_KINDS = (
    "CELL_RESULT",
    "ARTIFACT_INTEGRITY_VERIFY",
    "INDEPENDENT_RERUN_VERIFY",
    "MATRIX_FINALIZE",
    # Sprint V5 (PLAN section 31.5): immutable V4 diagnostic recalculation.
    "DIAGNOSTIC_RECALC",
)
VERIFY_KIND_REQUIRED_FIELDS = (
    "schema",
    "matrix_id",
    "verified_experiment_id",
    "verification_type",
)
CELL_RESULT_REQUIRED_FIELDS = ("schema", "matrix_id")
DIAGNOSTIC_RECALC_REQUIRED_FIELDS = ("schema", "source_trial_experiment_id")


def validate_entry_kind(entry: dict) -> list[str]:
    """Reason strings for any violated registry-kind contract (empty = OK)."""
    kind = entry.get("kind")
    if kind is None:
        return []
    if kind not in ENTRY_KINDS:
        return [f"unknown_registry_kind:{kind}"]
    required = (
        CELL_RESULT_REQUIRED_FIELDS
        if kind == "CELL_RESULT"
        else DIAGNOSTIC_RECALC_REQUIRED_FIELDS
        if kind == "DIAGNOSTIC_RECALC"
        else VERIFY_KIND_REQUIRED_FIELDS
    )
    missing = [
        field for field in required
        if entry.get(field) is None or entry.get(field) == ""
    ]
    return [f"registry_missing_field:{field}" for field in missing]


def _resolve(path: str | Path | None) -> Path:
    return Path(path) if path is not None else DEFAULT_REGISTRY_PATH


def append(entry: dict, path: str | Path | None = None) -> dict:
    """Append one experiment entry as a single JSON line (create if missing).

    The entry is stamped with ``appended_at`` unless the caller supplied one.
    Raises ``ValueError`` when required fields are missing, values are not
    JSON-serialisable, or a declared entry ``kind`` violates the PLAN
    section 11 field contract (fail-closed; nothing is written).  Returns
    the stored entry.
    """
    for field in REQUIRED_ENTRY_FIELDS:
        if field not in entry or entry[field] is None:
            raise ValueError(f"registry entry requires non-null {field!r}")
    kind_reasons = validate_entry_kind(entry)
    if kind_reasons:
        raise ValueError(f"invalid registry entry kind: {kind_reasons}")
    stored = dict(entry)
    stored.setdefault("appended_at", datetime.now(timezone.utc).isoformat())
    line = json.dumps(stored, sort_keys=True, default=str)
    target = _resolve(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return stored


def load_all(path: str | Path | None = None) -> list[dict]:
    """Load every entry; every line must be valid JSON."""
    target = _resolve(path)
    if not target.exists():
        return []
    entries: list[dict] = []
    with target.open("r", encoding="utf-8") as handle:
        for lineno, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"registry line {lineno} is not valid JSON: {exc}") from exc
    return entries


def verify_append_only(path: str | Path | None = None) -> bool:
    """True iff ``appended_at`` timestamps are monotonically non-decreasing.

    Out-of-order timestamps would indicate an out-of-band rewrite of the file.
    """
    from datetime import datetime as _dt

    def _parse(value: object) -> _dt:
        return _dt.fromisoformat(str(value))

    entries = load_all(path)
    previous = None
    for index, entry in enumerate(entries):
        if "appended_at" not in entry:
            raise ValueError(f"registry line {index + 1} missing appended_at")
        stamp = _parse(entry["appended_at"])
        if previous is not None and stamp < previous:
            return False
        previous = stamp
    return True
