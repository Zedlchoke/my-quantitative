"""Global V8 trial ledger tools (A4 finalizer/statistics owner).

Sprint V8 -- PLAN section 7.2: "DSR uses daily returns and the entire
global trial ledger; PBO is only computed within the comparable cohort.
Unavailable must fail-closed, never fabricated."

This module is the machine-readable view over the append-only experiment
registry (``results/registry/experiments.jsonl``, see
:mod:`research.protocol.registry`):

* :func:`snapshot`      -- read-only ``{rows, count, sha256, existed}``.
* :func:`digest`        -- canonical sha256 over a row list / snapshot.
* :func:`verify_append_only` -- monotonic ``appended_at`` re-check (fail closed).
* :func:`append_verified`    -- append ONLY after the existing file verifies;
  nothing is written on any violation (no rewrite, no delete, ever).
* :func:`cohort_of` / :func:`cohort_split` -- map every ledger row to its
  sprint cohort by ``matrix_id`` prefix.  Recognised prefixes:
  ``v6* -> V6``, ``v7* -> V7``, ``v8* -> V8``, ``v8x* -> V8X``.
  V8X breadth rows are kept OUT of the V8 core cohort on purpose (PLAN
  section 8 forbids pooling V8 and V8X in one statistical cohort).
  Anything else lands in ``UNMAPPED`` so it can never be silently dropped
  from an honest denominator.

Design rules inherited from the V7 finalizer:

* **No silent defaults** -- thresholds/paths come from the caller.
* **Fail closed** -- corrupt lines raise; unmapped rows are surfaced, not
  hidden; appends are refused when the existing file fails verification.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Mapping, Sequence

from research.protocol.registry import (
    DEFAULT_REGISTRY_PATH,
    append as _registry_append,
    verify_append_only as _registry_verify_append_only,
)

GLOBAL_LEDGER_SCHEMA_VERSION = 1

#: Ordered prefix rules: first match wins (V8X must be tested before V8).
#: Keys are the regex capture values of ``_MATRIX_ID_RE``.
_COHORT_RULES: tuple[tuple[str, str], ...] = (
    ("8x", "V8X"),
    ("6", "V6"),
    ("7", "V7"),
    ("8", "V8"),
)

_MATRIX_ID_RE = re.compile(r"^\s*v(8x|[678])(?![0-9])", re.IGNORECASE)

COHORT_KEYS = ("V6", "V7", "V8", "V8X", "UNMAPPED")


# --------------------------------------------------------------------------- #
# snapshot + digest
# --------------------------------------------------------------------------- #
def _sha256_file(path: Path) -> str | None:
    try:
        digest = hashlib.sha256()
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError:
        return None


def snapshot(path: str | Path | None = None) -> dict[str, Any]:
    """Read-only snapshot of a global-ledger JSONL file.

    Returns ``{"path", "rows", "count", "sha256", "existed"}``.  A missing
    file yields an empty honest snapshot (``count=0``, ``sha256=None``,
    ``existed=False``); a present-but-corrupt line raises ``ValueError``
    instead of returning partial data (fail closed).
    """
    target = Path(path) if path is not None else DEFAULT_REGISTRY_PATH
    if not target.exists():
        return {
            "path": str(target),
            "rows": [],
            "count": 0,
            "sha256": None,
            "existed": False,
            "schema_version": GLOBAL_LEDGER_SCHEMA_VERSION,
        }
    rows: list[dict] = []
    with open(target, "r", encoding="utf-8") as handle:
        for lineno, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
            except ValueError as exc:
                raise ValueError(
                    f"global_ledger_corrupt_line:{lineno}:{exc}") from exc
            if not isinstance(doc, Mapping):
                raise ValueError(f"global_ledger_line_not_object:{lineno}")
            rows.append(dict(doc))
    return {
        "path": str(target),
        "rows": rows,
        "count": len(rows),
        "sha256": _sha256_file(target),
        "existed": True,
        "schema_version": GLOBAL_LEDGER_SCHEMA_VERSION,
    }


def digest(payload: Mapping[str, Any] | Sequence[Mapping[str, Any]]) -> str:
    """Canonical sha256 over ledger rows (snapshot mapping or bare sequence).

    Canonicalisation: ``json.dumps(rows, sort_keys=True, separators=(",", ":"))``
    encoded UTF-8, so the digest is independent of key order on disk.
    """
    if isinstance(payload, Mapping):
        rows = payload.get("rows")
        if not isinstance(rows, Sequence) or isinstance(rows, (str, bytes)):
            raise ValueError("snapshot_payload_missing_rows")
    else:
        rows = payload
    canonical = json.dumps(list(rows), sort_keys=True,
                           separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# --------------------------------------------------------------------------- #
# verified append (the only writer)
# --------------------------------------------------------------------------- #
def verify_append_only(path: str | Path | None = None) -> bool:
    """True iff ``appended_at`` timestamps are monotonically non-decreasing."""
    return bool(_registry_verify_append_only(
        Path(path) if path is not None else None))


def append_verified(entry: Mapping[str, Any],
                    path: str | Path | None = None) -> dict:
    """Verify-then-append one entry; nothing is written on any violation.

    Checks, in order, all fail-closed (raise before touching the file):

    1. the entry must be a mapping with the registry-required non-null
       ``experiment_id`` / ``verdict`` fields (re-checked here so callers
       get one error site even though :func:`research.protocol.registry.append`
       would also reject);
    2. the EXISTING ledger must pass the monotonic ``appended_at``
       append-only verification (an out-of-order file indicates an
       out-of-band rewrite and blocks every further append).

    The write itself delegates to :func:`research.protocol.registry.append`
    (single-line JSON, fsync, kind-contract validation).
    """
    if not isinstance(entry, Mapping):
        raise ValueError("global_ledger_entry_must_be_mapping")
    for field in ("experiment_id", "verdict"):
        value = entry.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValueError(f"global_ledger_entry_requires_non_null:{field}")
    target = Path(path) if path is not None else DEFAULT_REGISTRY_PATH
    if target.exists() and not verify_append_only(target):
        raise ValueError(
            f"global_ledger_append_refused_append_only_violation:{target}")
    return dict(_registry_append(dict(entry), target))


# --------------------------------------------------------------------------- #
# cohort split (comparable-cohort statistics scoping)
# --------------------------------------------------------------------------- #
def cohort_of(row: Mapping[str, Any]) -> str:
    """Cohort label for one ledger row by ``matrix_id`` prefix.

    ``v8x...`` maps to ``V8X`` BEFORE the general ``v8`` rule so breadth
    rows can never contaminate the V8 core comparable cohort.  Rows with
    no recognisable prefix return ``UNMAPPED`` (never dropped silently).
    """
    matrix_id = row.get("matrix_id") if isinstance(row, Mapping) else None
    token = str(matrix_id or "").strip().lower()
    match = _MATRIX_ID_RE.match(token) if token else None
    if match is None:
        return "UNMAPPED"
    prefix = match.group(1).lower()
    for rule_prefix, cohort in _COHORT_RULES:
        if prefix == rule_prefix:
            return cohort
    return "UNMAPPED"


def cohort_split(rows: Sequence[Mapping[str, Any]]) -> dict[str, list[dict]]:
    """Partition ledger rows into sprint cohorts (plus honest leftovers).

    Returns all keys ``("V6", "V7", "V8", "V8X", "UNMAPPED")`` always, in
    encounter order within each cohort.  ``UNMAPPED`` is deliberately part
    of the payload: ``len(V6)+len(V7)+len(V8)+len(V8X)+len(UNMAPPED) ==
    len(rows)`` is an invariant callers can assert.
    """
    split: dict[str, list[dict]] = {key: [] for key in COHORT_KEYS}
    for row in (rows or []):
        if not isinstance(row, Mapping):
            split["UNMAPPED"].append({"_unmapped_reason": "row_not_a_mapping"})
            continue
        split[cohort_of(row)].append(dict(row))
    return split
