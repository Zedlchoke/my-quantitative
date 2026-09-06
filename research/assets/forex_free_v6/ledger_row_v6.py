"""FOREX-FREE-V6 scored-ledger row schema (P1 kernel lane, F-TERM-4 fix).

F-TERM-4 (carried from the V5 terminal): the V5 published scored ledger
(research/control/forex_free_v5_run/scored_ledger_published.jsonl) carries
NO ``arm_config_digest`` on its rows, while the V5 execution report's arm
summaries DO — the row schema itself did not mandate it.  V6 closes that
gap fail-closed: :func:`build_scored_ledger_row` REFUSES to build a row
without a well-formed ``arm_config_digest`` and without every identity
field.

Schema tag
----------
Every row built here carries ``schema = "forex_free_v6_scored_ledger_row_v1"``.

Field baseline (measured, not invented)
---------------------------------------
``V5_BASELINE_ROW_FIELDS`` is the exact, uniform key set of the three rows
of the published V5 scored ledger (read 2026-09-06 at base 4c804ba; all
three rows share the identical 45-key schema ``forex_free_v3_scored_record_v1``).
The V6 row carries the same baseline plus the additions:

* ``arm_config_digest``   -- REQUIRED, 64-char lowercase hex; sha256 over
  the arm's frozen per-arm config projection (:func:`compute_arm_config_digest`).
* ``cycle_id``            -- REQUIRED identity (V5 carried it only inside
  ``trial_id``; V6 promotes it to an explicit column).
* ``code_freeze_sha``     -- REQUIRED identity (the W-freeze code hash the
  scored run ran under; V5 carried it only in the run report).
* ``data_snapshot_digest`` -- REQUIRED identity (sha256 of the staged data
  authority the cell was scored against).

arm_config_digest construction (inherited V5 driver pattern)
------------------------------------------------------------
research/assets/forex_free_v5/exec_driver_v5.py builds a per-arm config
dict (cycle/family/arm ids, proposal sha, module sha, ``frozen_config``
projection: trailing-return window, sham shift, staleness mode, S0 cap,
warmup, notional, clocks->pair map, economy order, financing formula,
alpha definition, decision clock) and digests it with the kernel's
canonical JSON: ``sha256(json.dumps(cfg, sort_keys=True,
separators=(',', ':'), ensure_ascii=False).encode('utf-8'))``.
:func:`compute_arm_config_digest` inherits EXACTLY this serialization
(imported read-only from the V3 accounting kernel) and digests whatever
projection the caller passes — proposal_sha, universe, clock, warmup,
features/lags, entry/exit/fills, costs, control spec, falsification rule
— i.e. the digest is over WHAT IS GIVEN; it is the caller's freeze that
determines coverage.  Any change to any field (including nested values
and list order) changes the digest; key insertion order does not.

Append-only publication
-----------------------
:func:`append_row` publishes exactly one canonical JSON line.  It is
append-only in the F-A7T-1 sense: existing bytes are never rewritten.
Implementation: read existing bytes -> append -> re-read and verify the
head bytes are byte-identical and the byte length grew by exactly the
appended line; refuse (raise) otherwise.  It additionally refuses a row
whose ``record_id`` already exists in the file, an existing file whose
last line is not newline-terminated (appending would fuse lines and
modify the meaning of existing bytes), any pre-existing line that cannot
be parsed (a duplicate cannot be proven absent -> fail closed), and — via
the optional ``expected_head_sha256`` pin (the chained head hash returned
by the previous :func:`append_row` call as ``head_sha256_after``) — any
foreign modification of the existing head bytes.  A refused call writes
nothing.

No PnL is computed anywhere in this module; it is schema + publication
machinery only (Phase P rule: no PnL in Phase P).

Run the tests with:
  /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest \
      tests/assets/forex_free_v6/test_p1_kernel.py -q
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from research.assets.forex_free_v3.accounting import (  # READ-ONLY import
    canonical_json_bytes,
    sha256_hex,
)

__all__ = [
    "SCHEMA_TAG",
    "V5_BASELINE_ROW_FIELDS",
    "V6_ADDED_FIELDS",
    "REQUIRED_IDENTITY_FIELDS",
    "LedgerRowError",
    "compute_arm_config_digest",
    "build_scored_ledger_row",
    "append_row",
]

SCHEMA_TAG = "forex_free_v6_scored_ledger_row_v1"

# The exact key set of a published V5 scored ledger row (measured 2026-09-06
# from research/control/forex_free_v5_run/scored_ledger_published.jsonl;
# 3/3 rows uniform).  V6 carries this list as its baseline.
V5_BASELINE_ROW_FIELDS: Tuple[str, ...] = (
    "arm", "base", "base_price_only", "benchmark_treatment",
    "break_even_cost_bps", "cell_id", "cost_tier", "decision_clock",
    "delay_stress", "drop_one_expectancy", "dropout_scenarios", "dry_run",
    "dryrun_gate_scaffold", "family_id", "financing_adjusted_pnl_usd",
    "financing_adjustment_usd", "financing_formula", "fold_positive_share",
    "folds", "folds_declared", "gate_reasons", "gates",
    "gross_price_pnl_usd", "incremental_alpha",
    "incremental_alpha_definition", "mdd_usd", "n_decisions", "n_trades",
    "n_trades_kept", "pair_concentration", "price_only_pnl_usd",
    "proposal_id", "published", "purge_days", "purged_trades", "real_pnl",
    "record_id", "schema", "scored", "stress", "trial_id",
    "usd_drift_diag", "usd_index_pairs", "usd_index_source",
    "weekend_gate_dropped",
)

# What V6 adds on top of the V5 baseline (F-TERM-4 + promoted identity).
V6_ADDED_FIELDS: Tuple[str, ...] = (
    "arm_config_digest", "cycle_id", "code_freeze_sha",
    "data_snapshot_digest",
)

# Identity fields a V6 scored row MUST carry (plan §3 P1: arm_config_digest
# in ledger rows; identity fail-closed).  ``cost_tier`` is numeric
# (frozen kernel tier in {1.0, 1.5, 2.0}); the rest are non-empty strings.
REQUIRED_IDENTITY_FIELDS: Tuple[str, ...] = (
    "cycle_id", "family_id", "arm", "trial_id", "cell_id",
    "code_freeze_sha", "data_snapshot_digest", "cost_tier",
)

_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")


class LedgerRowError(Exception):
    """A V6 ledger-row construction/publication refusal (fail closed).

    ``code`` is a machine-readable rejection reason (mirrors the kernel's
    ``AccountingError`` shape): ARM_CONFIG_DIGEST_REQUIRED,
    ARM_CONFIG_DIGEST_INVALID, IDENTITY_FIELD_MISSING,
    SCHEMA_TAG_MISMATCH, NOT_JSON_SERIALIZABLE, NOT_A_DICT,
    RECORD_ID_REQUIRED, DUPLICATE_RECORD_ID, LAST_LINE_NOT_TERMINATED,
    PREEXISTING_ROW_UNPARSEABLE, PREEXISTING_ROW_MISSING_RECORD_ID,
    HEAD_PIN_MISMATCH, HEAD_BYTES_MODIFIED.
    """

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}: {detail}")
        self.code = code
        self.detail = detail


# -------------------------------------------------------------------------- #
# arm_config_digest (F-TERM-4)                                               #
# -------------------------------------------------------------------------- #
def compute_arm_config_digest(frozen_config: Dict[str, Any]) -> str:
    """Deterministic sha256 over the canonical JSON of a frozen per-arm
    config projection.

    Serialization is the house convention inherited READ-ONLY from the V3
    accounting kernel (``canonical_json_bytes``: sorted keys, no
    whitespace, UTF-8) — the exact bytes a ledger line is written with.
    The digest covers WHAT IS GIVEN: whatever fields the caller's freeze
    carries (proposal_sha, universe, clock, warmup, features/lags,
    entry/exit/fills, costs, control spec, falsification rule, ...).  It
    is the caller's responsibility to freeze a complete projection; this
    function guarantees only determinism and sensitivity:

    * same content, any key insertion order  -> same digest;
    * any value change (nested included)     -> different digest;
    * any list order change                  -> different digest.
    """
    if not isinstance(frozen_config, dict):
        raise LedgerRowError(
            "NOT_A_DICT",
            f"arm config must be a dict, got {type(frozen_config).__name__}")
    try:
        payload = canonical_json_bytes(frozen_config)
    except (TypeError, ValueError) as exc:
        raise LedgerRowError(
            "NOT_JSON_SERIALIZABLE",
            f"arm config cannot be canonicalized: {exc}") from exc
    return sha256_hex(payload)


# -------------------------------------------------------------------------- #
# row construction (fail closed)                                             #
# -------------------------------------------------------------------------- #
def _require_identity(fields: Dict[str, Any], name: str) -> Any:
    if name not in fields:
        raise LedgerRowError(
            "IDENTITY_FIELD_MISSING",
            f"scored ledger row requires identity field {name!r}")
    value = fields[name]
    if value is None:
        raise LedgerRowError(
            "IDENTITY_FIELD_MISSING",
            f"identity field {name!r} is None")
    if isinstance(value, str) and not value.strip():
        raise LedgerRowError(
            "IDENTITY_FIELD_MISSING",
            f"identity field {name!r} is empty")
    return value


def build_scored_ledger_row(**fields: Any) -> Dict[str, Any]:
    """Build one V6 scored-ledger row dict; refuse (raise) unless the row
    carries a well-formed ``arm_config_digest`` and every identity field.

    Required (F-TERM-4): ``arm_config_digest`` -- a 64-char LOWERCASE hex
    string (as produced by :func:`compute_arm_config_digest` /
    ``hashlib.hexdigest()``).  Missing -> ARM_CONFIG_DIGEST_REQUIRED;
    present but malformed (wrong length, uppercase, non-hex, non-str)
    -> ARM_CONFIG_DIGEST_INVALID.

    Required identity: ``cycle_id``, ``family_id``, ``arm``, ``trial_id``,
    ``cell_id``, ``code_freeze_sha``, ``data_snapshot_digest``,
    ``cost_tier`` -- each present and non-empty, else
    IDENTITY_FIELD_MISSING (named in the message).

    ``schema``: stamped to :data:`SCHEMA_TAG`; a caller-supplied foreign
    tag refuses (SCHEMA_TAG_MISMATCH).  All other fields pass through
    (the V5 baseline list :data:`V5_BASELINE_ROW_FIELDS` documents the
    expected row vocabulary).  Values must be JSON-serializable (checked
    at build time, NOT_JSON_SERIALIZABLE).  No PnL is computed here.
    """
    digest = fields.get("arm_config_digest")
    if digest is None:
        raise LedgerRowError(
            "ARM_CONFIG_DIGEST_REQUIRED",
            "F-TERM-4: a V6 scored ledger row mandates arm_config_digest "
            "(sha256 over the arm's frozen config); build it with "
            "compute_arm_config_digest(frozen_config)")
    if not isinstance(digest, str) or not _HEX64_RE.match(digest):
        raise LedgerRowError(
            "ARM_CONFIG_DIGEST_INVALID",
            f"arm_config_digest must be 64-char lowercase hex, got "
            f"{digest!r}")

    for name in REQUIRED_IDENTITY_FIELDS:
        _require_identity(fields, name)

    supplied_schema = fields.get("schema")
    if supplied_schema is not None and supplied_schema != SCHEMA_TAG:
        raise LedgerRowError(
            "SCHEMA_TAG_MISMATCH",
            f"row schema must be {SCHEMA_TAG!r}, got {supplied_schema!r}")

    row = dict(fields)
    row["schema"] = SCHEMA_TAG
    try:
        canonical_json_bytes(row)
    except (TypeError, ValueError) as exc:
        raise LedgerRowError(
            "NOT_JSON_SERIALIZABLE",
            f"row is not JSON-serializable: {exc}") from exc
    return row


# -------------------------------------------------------------------------- #
# append-only publication                                                    #
# -------------------------------------------------------------------------- #
def _read_bytes(path: str) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


def _existing_record_ids(existing: bytes) -> set:
    """Every record_id already in the file; refuses any line that cannot
    be parsed as a JSON object with a record_id (a duplicate cannot be
    proven absent against an unreadable line -> fail closed)."""
    ids = set()
    for lineno, raw in enumerate(existing.split(b"\n"), start=1):
        if not raw.strip():
            continue
        try:
            rec = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise LedgerRowError(
                "PREEXISTING_ROW_UNPARSEABLE",
                f"line {lineno} is not a JSON object ({exc}); refusing to "
                "append onto an unreadable ledger") from exc
        if not isinstance(rec, dict) or not isinstance(
                rec.get("record_id"), str) or not rec["record_id"]:
            raise LedgerRowError(
                "PREEXISTING_ROW_MISSING_RECORD_ID",
                f"line {lineno} carries no record_id; refusing to append "
                "(duplicate check impossible)")
        ids.add(rec["record_id"])
    return ids


def append_row(path: str, row: Dict[str, Any],
               expected_head_sha256: Optional[str] = None) -> Dict[str, Any]:
    """Append EXACTLY ONE canonical JSON line for ``row``; append-only.

    Guarantees (all fail closed; a refused call writes nothing):

    * ``row`` must be a dict with a non-empty string ``record_id``
      (RECORD_ID_REQUIRED) — the duplicate-check key.
    * The line is the kernel-canonical serialization of ``row`` plus one
      trailing ``\\n`` — exactly one JSON line, byte-deterministic.
    * DUPLICATE_RECORD_ID: ``record_id`` already present in the file.
    * LAST_LINE_NOT_TERMINATED: the existing file does not end with a
      newline (appending would fuse into the last existing line and
      modify its bytes' meaning).
    * HEAD_PIN_MISMATCH: ``expected_head_sha256`` (the chained
      ``head_sha256_after`` returned by the previous append_row call) does
      not match the sha256 of the existing bytes — foreign modification
      detected BEFORE any write.
    * HEAD_BYTES_MODIFIED: after writing, the re-read head bytes are no
      longer byte-identical to the pre-write read, or the byte length did
      not grow by exactly the appended line — the append raced a foreign
      writer and is reported as an integrity violation (the on-disk state
      is left untouched as evidence; this module never rewrites history).

    Returns the measured evidence dict: bytes before/after, appended
    bytes, head identity, the appended line's sha256 and the chained
    ``head_sha256_after`` pin for the next append.
    """
    if not isinstance(row, dict):
        raise LedgerRowError(
            "NOT_A_DICT", f"row must be a dict, got {type(row).__name__}")
    record_id = row.get("record_id")
    if not isinstance(record_id, str) or not record_id.strip():
        raise LedgerRowError(
            "RECORD_ID_REQUIRED",
            "row must carry a non-empty string record_id (duplicate-check "
            f"key); got {record_id!r}")
    try:
        line = canonical_json_bytes(row) + b"\n"
    except (TypeError, ValueError) as exc:
        raise LedgerRowError(
            "NOT_JSON_SERIALIZABLE",
            f"row cannot be canonicalized: {exc}") from exc

    path = os.fspath(path)
    parent = os.path.dirname(os.path.abspath(path))
    if parent:
        os.makedirs(parent, exist_ok=True)

    if os.path.exists(path):
        existing = _read_bytes(path)
        if expected_head_sha256 is not None:
            actual_head = sha256_hex(existing)
            if actual_head != expected_head_sha256:
                raise LedgerRowError(
                    "HEAD_PIN_MISMATCH",
                    f"existing head sha256 {actual_head} != pinned "
                    f"{expected_head_sha256}; foreign head bytes detected "
                    "-- refusing to append")
        if existing and not existing.endswith(b"\n"):
            raise LedgerRowError(
                "LAST_LINE_NOT_TERMINATED",
                "existing file does not end with a newline; appending would "
                "modify the meaning of the last existing line")
        if record_id in _existing_record_ids(existing):
            raise LedgerRowError(
                "DUPLICATE_RECORD_ID",
                f"record_id {record_id!r} already exists in {path}; the "
                "ledger is append-only and a record is published once")
    else:
        existing = b""
        if expected_head_sha256 not in (None, sha256_hex(b"")):
            raise LedgerRowError(
                "HEAD_PIN_MISMATCH",
                f"file {path} does not exist but a non-empty head was "
                f"pinned ({expected_head_sha256})")

    bytes_before = len(existing)
    with open(path, "ab") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())

    after = _read_bytes(path)
    head_ok = after[:bytes_before] == existing
    length_ok = len(after) == bytes_before + len(line)
    if not (head_ok and length_ok):
        raise LedgerRowError(
            "HEAD_BYTES_MODIFIED",
            f"post-append verification failed (head_identical={head_ok}, "
            f"length_ok={length_ok}, before={bytes_before}, "
            f"after={len(after)}, expected_after="
            f"{bytes_before + len(line)}); a foreign writer raced the "
            "append -- refusing to certify publication")

    return {
        "path": path,
        "record_id": record_id,
        "bytes_before": bytes_before,
        "bytes_after": len(after),
        "appended_bytes": len(line),
        "head_bytes_identical": True,
        "line_sha256": sha256_hex(line),
        "head_sha256_after": sha256_hex(after),
        "lines_in_file": sum(1 for raw in after.split(b"\n")
                             if raw.strip()),
    }
