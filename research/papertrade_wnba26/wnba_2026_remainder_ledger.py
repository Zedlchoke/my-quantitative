"""wnba_2026_remainder_ledger — append-only prospective pre-tip WNBA prediction
ledger for the REMAINING 2026 playoff games (schema
``wnba_2026_remainder_ledger@1``).

PROVENANCE (Lane W26 port, cycle WNBA-WINPROB-2026-REMAINDER-V1, 2026-10-07):
ported from the 2027-frozen ``wnba_prospective_ledger@1`` (source law; read-only
source file ``.worktrees/wnba-winprob-prospective-prep-v1/integration/research/
control/WNBA-WINPROB-PROSPECTIVE-PREP-V1/lanes/L_LEDGER/
wnba_prospective_ledger.py``), measured at this port's freeze at PREP tree HEAD
``9ed717c43c2e0724a51095730b28df8c7d5881ae`` (ledger module introduced at
``0d9b3d575106405c5ed5335d02b4c1ec2f132192``). Genesis anchor, sha256 row chain,
canonical JSON, append-only flock+fsync, no-outcome law, hash-chained
postponement/cancellation notices, tamper-evident verify walk, scoring-time
classification are ported verbatim in structure. The frozen B1-WNBA engine
re-hash pins measured at THIS freeze (2026-10-07, byte-identical to the
ERRATUM_R1 pins):

* ``arms.py``    ``82263eab713258b09ef920500a56d1fbf36ef9b9b8ea20965c6b4fd99b04cdd3``
* ``harness.py`` ``b9446f7699ce2e29c8ce66490fc0f9941cc38dda0ed02e8e7fc108e65373485e``

WNBA-2026-REMAINDER adaptations (cycle WNBA-WINPROB-2026-REMAINDER-V1
dispatch, deliverable 1):

* **Window law**: the ledger carries ONLY remaining 2026 playoff games —
  ``season == 2026`` (exact) AND ``game_type == "POST"`` are structurally
  enforced at append, verify and genesis creation. Completed 2026 playoff
  games are HISTORY (stream warm-up material, never scored rows); a real
  ledger file is created ONLY after the owner typed the cycle GO.
* **Batch law (tip-relative day-anchored T0-6h10m)**: rows are appended in
  day-batches per ET calendar day; every row of a batch must satisfy
  ``recorded_at_utc < (min tip_utc of the batch) - 6h10m`` STRICTLY (the batch
  anchor is an exclusive deadline: a row stamped exactly at T0-6h10m is
  refused; the frozen 2027 law was inclusive at exactly 6h — this port
  tightens the boundary per the dispatch dry-run law "append-at-or-after-
  anchor refused") AND the per-row strict law ``recorded_at_utc < tip_utc``
  (strict ``<`` at append AND re-checked at scoring). One batch per ET
  local_date; no re-prediction, no backfill, ever. ``T0`` is the earliest tip
  of the ET game-day from the pinned schedule snapshot when the full day
  slate is batched (day-anchored gate); the tool gates on the min tip of the
  rows actually in the batch (tip-relative), so a partial batch of only
  later-tipped games gates at its own earliest game anchor — disclosed
  behavior: a partial first batch permanently consumes the ET day
  (one-batch-per-day) for games whose own anchor has already passed.
* **Stream state law** (scoring-side; inherited from the frozen B1-WNBA
  engine, not re-implemented here): the rating state used for a batch
  includes only games with ``tip_utc < batch anchor`` AND result present
  (completed only); games sharing an exact tip are predicted from one
  rating snapshot; updates apply only after a day's tips pass.

Stdlib only. SYNTHETIC-tested; contains no real games, no real predictions,
no metrics on outcomes, no real-game probability anywhere.
"""

from __future__ import annotations

import datetime as _dt
import fcntl
import hashlib
import json
import os
import re
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Union
from zoneinfo import ZoneInfo

__all__ = [
    "SCHEMA_VERSION",
    "FIELD_ORDER",
    "OUTCOME_BLOCKLIST",
    "ET_TZ",
    "LedgerError",
    "LedgerValidationError",
    "LedgerIntegrityError",
    "create_ledger",
    "load_genesis",
    "append",
    "append_batch",
    "postpone",
    "cancel",
    "verify_chain",
    "validate_for_scoring",
    "load_rows",
    "compute_row_hash",
    "canonical_json",
    "parse_iso_z",
    "et_local_date",
    "VALID_PROSPECTIVE",
    "INVALID_PROSPECTIVE",
    "NOT_SCORED_CANCELLED",
    "NOT_RUN",
    "NOT_SCORED_NO_ACTUAL_DATA",
]

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "wnba_2026_remainder_ledger@1"
GENESIS_PREFIX = "GENESIS:"
GENESIS_SIDECAR_SCHEMA = "wnba_2026_remainder_ledger_genesis@1"
ET_TZ = ZoneInfo("America/New_York")

#: The only season this cycle's window covers (2026 REMAINDER ONLY).
WINDOW_SEASON = 2026

#: The only game type in the window (remaining playoff games only).
WINDOW_GAME_TYPE = "POST"

#: The 18 binding fields of the WNBA adaptation, in canonical order.
FIELD_ORDER: List[str] = [
    "schema_version",
    "cycle_id",
    "game_id",
    "season",
    "game_type",
    "home_team",
    "away_team",
    "tip_utc",
    "local_date",
    "recorded_at_utc",
    "arm_id",
    "arm_config_digest",
    "model_version",
    "inputs_digest",
    "p_home",
    "recorded_by",
    "prev_row_hash",
    "row_hash",
]

_ROW_TYPE = "row_type"
POSTPONEMENT_NOTICE = "POSTPONEMENT_NOTICE"
CANCELLATION_NOTICE = "CANCELLATION_NOTICE"

OUTCOME_BLOCKLIST = (
    "score",
    "pts",
    "result",
    "winner",
    "outcome",
    "final",
    "margin",
    "total",
    "spread",
)

GAME_TYPES = ("REG", "POST")

VALID_PROSPECTIVE = "VALID_PROSPECTIVE"
INVALID_PROSPECTIVE = "INVALID_PROSPECTIVE"
NOT_SCORED_CANCELLED = "NOT_SCORED_CANCELLED"
NOT_RUN = "NOT_RUN"
NOT_SCORED_NO_ACTUAL_DATA = "NOT_SCORED_NO_ACTUAL_DATA"

#: Batch law (2026-REMAINDER adaptation): every row of a day-batch is recorded
#: STRICTLY earlier than this long before the batch's earliest tip. The batch
#: anchor ``T0 - BATCH_LEAD`` is an EXCLUSIVE deadline (a row stamped exactly
#: at the anchor is refused). 6h10m = 370 minutes per the dispatch law.
BATCH_LEAD_MINUTES = 6 * 60 + 10

_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_GENESIS_ANCHOR_RE = re.compile(r"^GENESIS:[0-9a-f]{64}$")
_ROW_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_P_HOME_RE = re.compile(r"^\d\.\d{6}$")

_HINT = "ISO-8601 UTC with Z suffix, seconds precision, e.g. 2026-10-07T23:30:00Z"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class LedgerError(Exception):
    """Base class for all ledger failures (fail-closed family)."""


class LedgerValidationError(LedgerError):
    """A row / batch / argument violates the schema; the write is refused."""


class LedgerIntegrityError(LedgerError):
    """Existing ledger state is doubtful; the operation is refused."""


# ---------------------------------------------------------------------------
# Canonical serialization, hashing, timestamps
# ---------------------------------------------------------------------------


def canonical_json(obj: Any) -> str:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_iso_z(value: Any) -> _dt.datetime:
    """Strict ISO-8601 UTC parse (``...Z`` suffix, no naive, no offsets)."""
    if not isinstance(value, str) or not _TS_RE.match(value):
        raise ValueError(f"malformed timestamp {value!r}; required format: {_HINT}")
    try:
        parsed = _dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise ValueError(f"malformed timestamp {value!r}: {exc}") from exc
    return parsed.replace(tzinfo=_dt.timezone.utc)


def et_local_date(tip_utc: _dt.datetime) -> _dt.date:
    """SPEC §3 day-key law: local_date := tip_utc in America/New_York."""
    return tip_utc.astimezone(ET_TZ).date()


def notice_field_order(row_type: str) -> List[str]:
    order = [
        "schema_version",
        _ROW_TYPE,
        "cycle_id",
        "game_id",
        "season",
        "game_type",
        "home_team",
        "away_team",
        "prior_tip_utc",
    ]
    if row_type == POSTPONEMENT_NOTICE:
        order.append("new_tip_utc")
    order += [
        "reason",
        "noticed_at_utc",
        "affected_row_indices",
        "recorded_by",
        "prev_row_hash",
        "row_hash",
    ]
    return order


def _field_order_for(row: Dict[str, Any]) -> List[str]:
    if _ROW_TYPE in row:
        return notice_field_order(row[_ROW_TYPE])
    return FIELD_ORDER


def compute_row_hash(row: Dict[str, Any], field_order: List[str]) -> str:
    content = {field: row[field] for field in field_order if field != "row_hash"}
    return sha256_hex(canonical_json(content))


def _has_outcome_key(row: Dict[str, Any]) -> Optional[str]:
    for key in row:
        lowered = key.lower()
        for token in OUTCOME_BLOCKLIST:
            if token in lowered:
                return key
    return None


# ---------------------------------------------------------------------------
# Genesis record
# ---------------------------------------------------------------------------


def _sidecar_path(path: Union[str, Path]) -> Path:
    return Path(str(path) + ".genesis.json")


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso_z_strict(value: Any, what: str) -> _dt.datetime:
    try:
        return parse_iso_z(value)
    except ValueError as exc:
        raise LedgerValidationError(f"{what}: {exc}") from exc


def create_ledger(
    path: Union[str, Path],
    genesis_digest: str,
    cycle_id: str,
    season: int,
    arm_registry: Optional[List[str]] = None,
    freeze_utc: Optional[str] = None,
    created_at_utc: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a NEW empty ledger bound to the freeze GENESIS digest.

    Refuses to overwrite anything. Filename law:
    ``predictions_<cycle_id>_2026.jsonl`` with season == 2026
    (2026-REMAINDER window only). Creating the REAL ledger happens ONLY after
    the owner typed the cycle GO; sandbox ledgers must use a sandbox cycle id.
    """
    path = Path(path)
    sidecar = _sidecar_path(path)
    if path.exists() or sidecar.exists():
        raise LedgerValidationError(
            f"refusing to create {path.name}: ledger or genesis record already exists "
            "(append-only; a ledger is never recreated)"
        )
    if not isinstance(genesis_digest, str) or not _HEX64_RE.match(genesis_digest):
        raise LedgerValidationError(
            "genesis_digest must be lowercase 64-hex sha256 of the freeze packet bytes")
    if not isinstance(cycle_id, str) or not cycle_id:
        raise LedgerValidationError("cycle_id must be a nonempty string")
    if isinstance(season, bool) or not isinstance(season, int) or season != WINDOW_SEASON:
        raise LedgerValidationError(
            "season must be exactly %d (2026-REMAINDER ONLY: wnba_2026_remainder_"
            "ledger@1 carries no other season)" % WINDOW_SEASON)
    expected_name = f"predictions_{cycle_id}_{WINDOW_SEASON}.jsonl"
    if path.name != expected_name:
        raise LedgerValidationError(
            f"filename law: expected {expected_name!r}, got {path.name!r}"
        )
    registry: Optional[List[str]] = None
    if arm_registry is not None:
        if not isinstance(arm_registry, (list, tuple, set)) or not all(
            isinstance(a, str) and a for a in arm_registry
        ):
            raise LedgerValidationError(
                "arm_registry must be a collection of nonempty strings")
        registry = sorted(set(arm_registry))
    if freeze_utc is not None:
        parse_iso_z_strict(freeze_utc, "freeze_utc")

    record: Dict[str, Any] = {
        "schema": GENESIS_SIDECAR_SCHEMA,
        "ledger_file": path.name,
        "cycle_id": cycle_id,
        "season": season,
        "genesis_digest": genesis_digest,
        "arm_registry": registry,
        "freeze_utc": freeze_utc,
        "created_at_utc": created_at_utc if created_at_utc is not None else _now_iso(),
    }
    record["self_hash"] = sha256_hex(canonical_json(record))
    sidecar.write_text(
        json.dumps(record, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    path.touch()
    return record


def load_genesis(path: Union[str, Path]) -> Dict[str, Any]:
    path = Path(path)
    sidecar = _sidecar_path(path)
    if not sidecar.exists():
        raise LedgerIntegrityError(
            f"genesis record missing for {path.name}: ledger is unbound; refusing "
            "(fail-closed)"
        )
    try:
        record = json.loads(sidecar.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise LedgerIntegrityError(f"genesis record unreadable: {exc}") from exc
    if not isinstance(record, dict) or record.get("schema") != GENESIS_SIDECAR_SCHEMA:
        raise LedgerIntegrityError("genesis record has wrong schema marker")
    stored = record.get("self_hash")
    if not isinstance(stored, str) or not _HEX64_RE.match(stored):
        raise LedgerIntegrityError("genesis record self_hash missing/malformed")
    content = {k: v for k, v in record.items() if k != "self_hash"}
    if sha256_hex(canonical_json(content)) != stored:
        raise LedgerIntegrityError("genesis record self_hash mismatch (tampered)")
    if record.get("ledger_file") != path.name:
        raise LedgerIntegrityError("genesis record names a different ledger file")
    return record


# ---------------------------------------------------------------------------
# Row validation
# ---------------------------------------------------------------------------


def _require_nonempty_str(row: Dict[str, Any], field: str) -> None:
    value = row[field]
    if not isinstance(value, str) or not value:
        raise LedgerValidationError(f"field {field!r} must be a nonempty string")


def _validate_window_law(row: Dict[str, Any]) -> None:
    """2026-REMAINDER window law: season == 2026 AND game_type == POST."""
    season = row["season"]
    if isinstance(season, bool) or not isinstance(season, int) or season != WINDOW_SEASON:
        raise LedgerValidationError(
            "window law: season must be exactly %d (2026-REMAINDER only); got %r"
            % (WINDOW_SEASON, season))
    if row["game_type"] != WINDOW_GAME_TYPE:
        raise LedgerValidationError(
            "window law: game_type must be %r (remaining 2026 playoff games only); "
            "got %r" % (WINDOW_GAME_TYPE, row["game_type"]))


def _validate_prediction_row_fields(
    row: Dict[str, Any], genesis: Optional[Dict[str, Any]]
) -> None:
    """Full append/read validation of one prediction row (schema, no-outcome,
    window law, timestamp strict-<, local-date law, p_home domain, enums,
    digests)."""
    if not isinstance(row, dict):
        raise LedgerValidationError("row must be a JSON object")
    keys = set(row)
    expected = set(FIELD_ORDER)
    if keys != expected and keys != (expected - {"row_hash"}):
        missing = sorted(expected - keys)
        extra = sorted(keys - expected)
        raise LedgerValidationError(
            f"field set is not the closed 18-field wnba_2026_remainder_ledger@1 set "
            f"(missing={missing}, extra={extra}); additions need a schema-version bump"
        )
    offender = _has_outcome_key(row)
    if offender is not None:
        raise LedgerValidationError(
            f"no-outcome law: key {offender!r} matches the outcome vocabulary"
        )
    if row["schema_version"] != SCHEMA_VERSION:
        raise LedgerValidationError(f"schema_version must be {SCHEMA_VERSION!r}")
    for field in ("cycle_id", "game_id", "home_team", "away_team", "arm_id",
                  "model_version", "recorded_by"):
        _require_nonempty_str(row, field)
    if genesis is not None and row["cycle_id"] != genesis["cycle_id"]:
        raise LedgerValidationError(
            f"cycle_id {row['cycle_id']!r} does not match the genesis-bound cycle "
            f"{genesis['cycle_id']!r}"
        )
    if row["game_type"] not in GAME_TYPES:
        raise LedgerValidationError(f"game_type must be one of {GAME_TYPES}")
    _validate_window_law(row)
    tip = parse_iso_z_strict(row["tip_utc"], "tip_utc")
    recorded = parse_iso_z_strict(row["recorded_at_utc"], "recorded_at_utc")
    if recorded >= tip:
        raise LedgerValidationError(
            "timestamp law: recorded_at_utc must be STRICTLY < tip_utc"
        )
    if not isinstance(row["local_date"], str) or not _DATE_RE.match(row["local_date"]):
        raise LedgerValidationError(
            f"local_date {row.get('local_date')!r} must be a YYYY-MM-DD string")
    want_local = et_local_date(tip)
    if row["local_date"] != want_local.isoformat():
        raise LedgerValidationError(
            f"local_date law: tip_utc {row['tip_utc']} is ET {want_local.isoformat()}, "
            f"row claims {row['local_date']}"
        )
    if genesis is not None:
        registry = genesis.get("arm_registry")
        if registry is not None and row["arm_id"] not in registry:
            raise LedgerValidationError(
                f"arm registry law: arm_id {row['arm_id']!r} is not in the frozen "
                "registry"
            )
    for digest_field in ("arm_config_digest", "inputs_digest"):
        value = row[digest_field]
        if not isinstance(value, str) or not _HEX64_RE.match(value):
            raise LedgerValidationError(
                f"{digest_field} must be lowercase 64-hex sha256 (structural check; "
                "semantic freeze-registry match is a scoring-time law)"
            )
    validate_p_home(row["p_home"])
    prev = row["prev_row_hash"]
    if not isinstance(prev, str) or not (
        _GENESIS_ANCHOR_RE.match(prev) or _ROW_HASH_RE.match(prev)
    ):
        raise LedgerValidationError(
            "prev_row_hash must be a 64-hex row hash or 'GENESIS:<64-hex>' for line 1"
        )


def validate_p_home(value: Any) -> Decimal:
    """p_home law: string with exactly 6 fractional digits, strictly inside (0, 1)."""
    if not isinstance(value, str):
        raise LedgerValidationError(
            f"p_home must be a STRING with exactly 6 decimal places "
            f"(got {type(value).__name__})"
        )
    if not _P_HOME_RE.match(value):
        raise LedgerValidationError(
            f"p_home {value!r} is not a decimal string with exactly 6 fractional digits"
        )
    try:
        number = Decimal(value)
    except Exception as exc:  # pragma: no cover
        raise LedgerValidationError(f"p_home {value!r} is not a finite decimal") from exc
    if not (Decimal("0") < number < Decimal("1")):
        raise LedgerValidationError(
            f"p_home {value!r} outside strict open interval (0, 1)")
    return number


def _validate_notice_row_fields(row: Dict[str, Any]) -> None:
    if row.get(_ROW_TYPE) not in (POSTPONEMENT_NOTICE, CANCELLATION_NOTICE):
        raise LedgerValidationError(f"unknown row_type {row.get(_ROW_TYPE)!r}")
    if row["schema_version"] != SCHEMA_VERSION:
        raise LedgerValidationError("notice schema_version mismatch")
    for field in ("cycle_id", "game_id", "home_team", "away_team", "reason",
                  "recorded_by"):
        _require_nonempty_str(row, field)
    if (isinstance(row["season"], bool) or not isinstance(row["season"], int)
            or row["season"] != WINDOW_SEASON):
        raise LedgerValidationError(
            "notice season must be exactly %d (2026-REMAINDER only)" % WINDOW_SEASON)
    if row["game_type"] != WINDOW_GAME_TYPE:
        raise LedgerValidationError(
            "notice game_type must be %r (window law)" % WINDOW_GAME_TYPE)
    parse_iso_z_strict(row["prior_tip_utc"], "prior_tip_utc")
    if row[_ROW_TYPE] == POSTPONEMENT_NOTICE:
        parse_iso_z_strict(row["new_tip_utc"], "new_tip_utc")
    parse_iso_z_strict(row["noticed_at_utc"], "noticed_at_utc")
    affected = row["affected_row_indices"]
    if not isinstance(affected, list) or not all(
        isinstance(i, int) and not isinstance(i, bool) and i >= 0 for i in affected
    ):
        raise LedgerValidationError(
            "affected_row_indices must be a list of nonnegative ints")
    prev = row["prev_row_hash"]
    if not isinstance(prev, str) or not (
        _GENESIS_ANCHOR_RE.match(prev) or _ROW_HASH_RE.match(prev)
    ):
        raise LedgerValidationError("notice prev_row_hash malformed")


# ---------------------------------------------------------------------------
# Locked file primitives (append-only by construction)
# ---------------------------------------------------------------------------


class _LockedLedger:
    def __init__(self, path: Path) -> None:
        self._path = path
        self._fh: Optional[Any] = None

    def __enter__(self) -> Any:
        if not self._path.exists():
            raise LedgerIntegrityError(
                f"ledger file {self._path.name} missing while its genesis record exists"
            )
        self._fh = open(self._path, "r+", encoding="utf-8")
        fcntl.flock(self._fh.fileno(), fcntl.LOCK_EX)
        return self._fh

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        assert self._fh is not None
        try:
            fcntl.flock(self._fh.fileno(), fcntl.LOCK_UN)
        finally:
            self._fh.close()
            self._fh = None


def _read_lines(fh: Any) -> List[str]:
    fh.seek(0)
    return fh.read().splitlines()


def _parse_existing(fh: Any, genesis: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    prev_stored: Optional[str] = None
    for idx, line in enumerate(_read_lines(fh)):
        if not line.strip():
            raise LedgerIntegrityError(f"blank line at ledger index {idx}")
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LedgerIntegrityError(
                f"malformed JSON at ledger index {idx}: {exc}") from exc
        if not isinstance(row, dict):
            raise LedgerIntegrityError(f"non-object JSON at ledger index {idx}")
        field_order = _field_order_for(row)
        if set(row) != set(field_order):
            raise LedgerIntegrityError(f"unexpected field set at ledger index {idx}")
        if compute_row_hash(row, field_order) != row.get("row_hash"):
            raise LedgerIntegrityError(
                f"stored row_hash does not recompute at ledger index {idx}; "
                "integrity doubt — refusing to extend the ledger"
            )
        expected_prev = (
            GENESIS_PREFIX + genesis["genesis_digest"] if idx == 0 else prev_stored
        )
        if row.get("prev_row_hash") != expected_prev:
            raise LedgerIntegrityError(
                f"broken chain linkage at ledger index {idx}; "
                "integrity doubt — refusing to extend the ledger"
            )
        prev_stored = row.get("row_hash")
        rows.append(row)
    return rows


def _canonical_row(row: Dict[str, Any], field_order: List[str]) -> Dict[str, Any]:
    return {field: row[field] for field in field_order}


def _write_row(fh: Any, row: Dict[str, Any], field_order: List[str]) -> None:
    fh.seek(0, os.SEEK_END)
    fh.write(canonical_json(_canonical_row(row, field_order)) + "\n")
    fh.flush()
    os.fsync(fh.fileno())


def _required_parent(existing: List[Dict[str, Any]], genesis: Dict[str, Any]) -> str:
    if existing:
        return existing[-1]["row_hash"]
    return GENESIS_PREFIX + genesis["genesis_digest"]


# ---------------------------------------------------------------------------
# Public API: append (single row)
# ---------------------------------------------------------------------------


def append(path: Union[str, Path], row: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and append ONE prediction row (single-row emergency path).

    Prefer :func:`append_batch` (the day-batch law is the operative cadence).
    Same laws; batch-level anchor laws apply only to :func:`append_batch`.
    """
    return append_batch(path, [row])[0]


def append_batch(path: Union[str, Path], rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Validate and append ONE DAY-BATCH of prediction rows; returns rows as written.

    Batch law (2026-REMAINDER adaptation: tip-relative day-anchored T0-6h10m):
      * non-empty batch;
      * every row passes the full single-row validation (strict
        ``recorded_at_utc < tip_utc`` and the 2026-POST window law included);
      * all rows share ONE Eastern local_date (the ET day key);
      * ``max(recorded_at_utc) < min(tip_utc) - 6h10m`` STRICTLY — the batch
        anchor (T0 - 6h10m, T0 = the batch's earliest tip, i.e. the ET
        game-day's earliest tip when the full day slate is batched) is an
        EXCLUSIVE deadline: a row stamped exactly at the anchor is refused;
      * no earlier batch (or row) already covers that local_date — one batch
        per ET day, no re-prediction, no backfill.
    The batch is atomic: validation happens for ALL rows before ANY write; a
    refusal writes nothing. Tool-level auto-chain: a row with
    ``prev_row_hash: null`` is chained from the current tail at write time
    (documented convenience; an explicitly supplied prev hash must still match,
    and a supplied row_hash cannot be combined with a null prev hash).
    """
    path = Path(path)
    if not rows:
        raise LedgerValidationError("day-batch law: a batch must be non-empty")
    genesis = load_genesis(path)
    candidates = []
    for i, raw in enumerate(rows):
        candidate = dict(raw)
        provided_hash = candidate.get("row_hash")
        auto_prev = candidate.get("prev_row_hash") is None
        if auto_prev:
            if provided_hash is not None:
                raise LedgerValidationError(
                    "row_hash cannot be pre-supplied with a null prev_row_hash "
                    "(the chain parent is assigned at write time)")
            candidate["prev_row_hash"] = "0" * 64  # format placeholder for
            # validation only; the true parent is injected at write time and the
            # row_hash recomputed over it — the placeholder never reaches disk.
        _validate_prediction_row_fields(candidate, genesis)
        candidates.append((candidate, provided_hash, auto_prev))
    days = {c["local_date"] for c, _, _ in candidates}
    if len(days) != 1:
        raise LedgerValidationError(
            f"day-batch law: one batch covers exactly one ET local_date "
            f"(got {sorted(days)})")
    day = days.pop()
    min_tip = min(parse_iso_z_strict(c["tip_utc"], "tip_utc") for c, _, _ in candidates)
    max_rec = max(parse_iso_z_strict(c["recorded_at_utc"], "recorded_at_utc")
                  for c, _, _ in candidates)
    anchor = min_tip - _dt.timedelta(minutes=BATCH_LEAD_MINUTES)
    if max_rec >= anchor:
        raise LedgerValidationError(
            "day-batch law: every row must be recorded STRICTLY before the batch "
            "anchor T0-%dh%02dm (max_recorded %s vs anchor %s; T0 = earliest tip %s)"
            % (BATCH_LEAD_MINUTES // 60, BATCH_LEAD_MINUTES % 60,
               max_rec.strftime("%Y-%m-%dT%H:%M:%SZ"),
               anchor.strftime("%Y-%m-%dT%H:%M:%SZ"),
               min_tip.strftime("%Y-%m-%dT%H:%M:%SZ")))
    with _LockedLedger(path) as fh:
        existing = _parse_existing(fh, genesis)
        # one batch per ET day: any existing prediction row on the same local_date
        # refuses the batch (no re-prediction / backfill of a day)
        prior_day_rows = [r for r in existing
                          if _ROW_TYPE not in r and r.get("local_date") == day]
        if prior_day_rows:
            raise LedgerValidationError(
                "day-batch law violated: ET day %s already has %d recorded row(s); "
                "one batch per day, no re-prediction" % (day, len(prior_day_rows)))
        written = []
        for candidate, provided_hash, auto_prev in candidates:
            if auto_prev:
                candidate["prev_row_hash"] = _required_parent(existing, genesis)
            if candidate["prev_row_hash"] != _required_parent(existing, genesis):
                raise LedgerValidationError(
                    "wrong chain parent: prev_row_hash must be %s…, got %s…"
                    % (_required_parent(existing, genesis)[:20],
                       str(candidate["prev_row_hash"])[:20])
                )
            pairs = {(r["game_id"], r["arm_id"]) for r in existing
                     if _ROW_TYPE not in r}
            if (candidate["game_id"], candidate["arm_id"]) in pairs:
                raise LedgerValidationError(
                    "duplicate (game_id, arm_id): (%r, %r)"
                    % (candidate["game_id"], candidate["arm_id"])
                )
            seen_hashes = {r["row_hash"] for r in existing}
            computed = compute_row_hash(candidate, FIELD_ORDER)
            if provided_hash is not None and provided_hash != computed:
                raise LedgerValidationError(
                    "supplied row_hash does not match the canonical recomputation")
            if computed in seen_hashes:
                raise LedgerValidationError(
                    "duplicate row_hash: an identical row already exists")
            candidate["row_hash"] = computed
            _write_row(fh, candidate, FIELD_ORDER)
            existing.append(candidate)
            written.append(candidate)
    return written


def load_rows(path: Union[str, Path]) -> List[Dict[str, Any]]:
    path = Path(path)
    if not path.exists():
        raise LedgerIntegrityError(f"ledger file {path.name} does not exist")
    rows: List[Dict[str, Any]] = []
    for idx, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
        if not line.strip():
            raise LedgerIntegrityError(f"blank line at ledger index {idx}")
        rows.append(json.loads(line))
    return rows


# ---------------------------------------------------------------------------
# Public API: postponement / cancellation notices
# ---------------------------------------------------------------------------


def _game_rows(existing: List[Dict[str, Any]], game_id: str) -> List[tuple]:
    return [
        (i, r)
        for i, r in enumerate(existing)
        if isinstance(r, dict) and _ROW_TYPE not in r and r.get("game_id") == game_id
    ]


def _emit_notice(
    path: Path,
    row_type: str,
    game_id: str,
    reason: str,
    noticed_at_utc: Optional[str],
    recorded_by: Optional[str],
    prior_tip_utc: Optional[str],
    game_meta: Optional[Dict[str, Any]],
    new_tip_utc: Optional[str] = None,
) -> Dict[str, Any]:
    if not isinstance(recorded_by, str) or not recorded_by:
        raise LedgerValidationError(
            "recorded_by (recorder session id) is required for notices")
    if not isinstance(reason, str) or not reason.strip():
        raise LedgerValidationError("reason must be a nonempty string")
    noticed = noticed_at_utc if noticed_at_utc is not None else _now_iso()
    genesis = load_genesis(path)
    new_tip_dt = (parse_iso_z_strict(new_tip_utc, "new_tip_utc")
                  if new_tip_utc else None)
    with _LockedLedger(path) as fh:
        existing = _parse_existing(fh, genesis)
        rows_for_game = _game_rows(existing, game_id)
        if rows_for_game:
            scheduled = {r["tip_utc"] for _, r in rows_for_game}
            if len(scheduled) > 1:
                raise LedgerIntegrityError(
                    f"inconsistent scheduled tips recorded for game {game_id!r}"
                )
            prior_tip = scheduled.pop()
            meta = rows_for_game[0][1]
            if new_tip_dt is not None:
                affected = [
                    i
                    for i, r in rows_for_game
                    if parse_iso_z(r["recorded_at_utc"]) >= new_tip_dt
                ]
            else:
                affected = [i for i, _ in rows_for_game]
        else:
            if prior_tip_utc is None or game_meta is None:
                raise LedgerValidationError(
                    f"game {game_id!r} has no rows; supply prior_tip_utc and "
                    "game_meta(season, game_type, home_team, away_team)"
                )
            prior_tip = prior_tip_utc
            meta = game_meta
            affected = []
        notice: Dict[str, Any] = {
            "schema_version": SCHEMA_VERSION,
            _ROW_TYPE: row_type,
            "cycle_id": genesis["cycle_id"],
            "game_id": game_id,
            "season": meta["season"],
            "game_type": meta["game_type"],
            "home_team": meta["home_team"],
            "away_team": meta["away_team"],
            "prior_tip_utc": prior_tip,
        }
        if row_type == POSTPONEMENT_NOTICE:
            notice["new_tip_utc"] = new_tip_utc
        notice.update(
            {
                "reason": reason,
                "noticed_at_utc": noticed,
                "affected_row_indices": affected,
                "recorded_by": recorded_by,
                "prev_row_hash": _required_parent(existing, genesis),
            }
        )
        field_order = notice_field_order(row_type)
        _validate_notice_row_fields(notice)
        notice["row_hash"] = compute_row_hash(notice, field_order)
        _write_row(fh, notice, field_order)
    return notice


def postpone(
    path: Union[str, Path],
    game_id: str,
    new_tip_utc: str,
    reason: str,
    *,
    prior_tip_utc: Optional[str] = None,
    game_meta: Optional[Dict[str, Any]] = None,
    noticed_at_utc: Optional[str] = None,
    recorded_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Record a postponement as a hash-chained POSTPONEMENT_NOTICE (classification
    happens at scoring time against the actual tip; nothing is marked in place)."""
    return _emit_notice(
        Path(path), POSTPONEMENT_NOTICE, game_id, reason, noticed_at_utc,
        recorded_by, prior_tip_utc, game_meta, new_tip_utc=new_tip_utc,
    )


def cancel(
    path: Union[str, Path],
    game_id: str,
    reason: str,
    *,
    prior_tip_utc: Optional[str] = None,
    game_meta: Optional[Dict[str, Any]] = None,
    noticed_at_utc: Optional[str] = None,
    recorded_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Record a cancellation as a hash-chained CANCELLATION_NOTICE."""
    return _emit_notice(
        Path(path), CANCELLATION_NOTICE, game_id, reason, noticed_at_utc,
        recorded_by, prior_tip_utc, game_meta,
    )


# ---------------------------------------------------------------------------
# Public API: verification (full re-hash walk + read-side laws)
# ---------------------------------------------------------------------------


def verify_chain(
    path: Union[str, Path],
    expected_genesis_digest: Optional[str] = None,
) -> List[int]:
    """Full re-hash walk; returns 0-based indices of broken rows (empty = intact)."""
    path = Path(path)
    genesis = load_genesis(path)
    if (expected_genesis_digest is not None
            and expected_genesis_digest != genesis["genesis_digest"]):
        raise LedgerIntegrityError(
            "expected_genesis_digest does not match the ledger's genesis record "
            "(line 1 must anchor to the freeze packet GENESIS digest)"
        )
    genesis_anchor = GENESIS_PREFIX + genesis["genesis_digest"]
    broken: List[int] = []
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise LedgerIntegrityError(f"ledger unreadable: {exc}") from exc
    if raw == "":
        return []
    lines = raw.splitlines()
    prev_stored_hash: Optional[str] = None
    seen_pairs: Set[tuple] = set()
    seen_hashes: Set[str] = set()
    for idx, line in enumerate(lines):
        row_hash_here: Optional[str] = None
        if not line.strip():
            broken.append(idx)
        else:
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                broken.append(idx)
                row = None
            if isinstance(row, dict):
                known_type = _ROW_TYPE not in row or row.get(_ROW_TYPE) in (
                    POSTPONEMENT_NOTICE,
                    CANCELLATION_NOTICE,
                )
                field_order = _field_order_for(row) if known_type else None
                if not known_type or set(row) != set(field_order):
                    broken.append(idx)
                elif _has_outcome_key(row) is not None:
                    broken.append(idx)
                elif not isinstance(row.get("row_hash"), str) or not _ROW_HASH_RE.match(
                    row["row_hash"]
                ):
                    broken.append(idx)
                elif compute_row_hash(row, field_order) != row["row_hash"]:
                    broken.append(idx)
                elif idx == 0 and row["prev_row_hash"] != genesis_anchor:
                    broken.append(idx)
                elif idx > 0 and row["prev_row_hash"] != prev_stored_hash:
                    broken.append(idx)
                else:
                    try:
                        if _ROW_TYPE in row:
                            _validate_notice_row_fields(row)
                        else:
                            _validate_prediction_row_fields(row, genesis)
                            pair = (row["game_id"], row["arm_id"])
                            if pair in seen_pairs:
                                raise LedgerValidationError(
                                    "duplicate (game_id, arm_id)")
                            seen_pairs.add(pair)
                    except LedgerValidationError:
                        broken.append(idx)
                    else:
                        if row["row_hash"] in seen_hashes:
                            broken.append(idx)
                        else:
                            seen_hashes.add(row["row_hash"])
                row_hash_here = (row.get("row_hash")
                                 if isinstance(row.get("row_hash"), str) else None)
            else:
                row_hash_here = None
        prev_stored_hash = row_hash_here
    return sorted(set(broken))


# ---------------------------------------------------------------------------
# Public API: scoring-time validation
# ---------------------------------------------------------------------------


def validate_for_scoring(
    path: Union[str, Path],
    actual_tips: Dict[str, str],
    cancelled_games: Optional[Set[str]] = None,
    freeze_utc: Optional[str] = None,
) -> Dict[str, Any]:
    """The real anti-retrospective gate. Fails closed on any chain break.

    *actual_tips*: ``{game_id: actual tip ISO-Z}`` from the audited final data.
    Per-row verdicts: cancelled -> NOT_SCORED_CANCELLED; game absent from
    *actual_tips* -> NOT_SCORED_NO_ACTUAL_DATA; ``actual <= recorded_at_utc`` ->
    INVALID_PROSPECTIVE (strict ``<`` re-checked at scoring); ``actual <
    freeze_utc`` -> NOT_RUN (played-before-record write-off); else
    VALID_PROSPECTIVE. Also reports game-level ``not_run_games``.
    """
    path = Path(path)
    genesis = load_genesis(path)
    if freeze_utc is None:
        freeze_utc = genesis.get("freeze_utc")
    freeze_dt = parse_iso_z_strict(freeze_utc, "freeze_utc") if freeze_utc else None
    broken = verify_chain(path)
    if broken:
        raise LedgerIntegrityError(
            f"ledger integrity failure: chain broken at row indices {broken}; "
            "scoring refused (fail-closed)"
        )
    actual: Dict[str, _dt.datetime] = {}
    for game_id, tip in actual_tips.items():
        actual[game_id] = parse_iso_z_strict(tip, f"actual_tips[{game_id!r}]")
    cancelled = set(cancelled_games or ())
    rows = load_rows(path)
    for row in rows:
        if isinstance(row, dict) and row.get(_ROW_TYPE) == CANCELLATION_NOTICE:
            cancelled.add(row["game_id"])
    games_with_rows = {
        r["game_id"] for r in rows if isinstance(r, dict) and _ROW_TYPE not in r
    }
    verdicts: List[Dict[str, Any]] = []
    counts: Dict[str, int] = {}
    for idx, row in enumerate(rows):
        if _ROW_TYPE in row:
            continue
        game_id = row["game_id"]
        if game_id in cancelled:
            verdict = NOT_SCORED_CANCELLED
            why = "game cancelled; no result exists; excluded, no outcome join"
        elif game_id not in actual:
            verdict = NOT_SCORED_NO_ACTUAL_DATA
            why = "no actual tip in scoring input; unresolved, excluded"
        else:
            actual_dt = actual[game_id]
            recorded_dt = parse_iso_z(row["recorded_at_utc"])
            if actual_dt <= recorded_dt:
                verdict = INVALID_PROSPECTIVE
                why = ("actual tip is not strictly after recorded_at_utc "
                       "(retro-injection or tip moved earlier past the record); "
                       "permanent — never repairable retroactively")
            elif freeze_dt is not None and actual_dt < freeze_dt:
                verdict = NOT_RUN
                why = "actual tip precedes the freeze timestamp (played-before-record)"
            else:
                verdict = VALID_PROSPECTIVE
                why = "recorded strictly before the actual tip, inside the window"
        counts[verdict] = counts.get(verdict, 0) + 1
        verdicts.append(
            {
                "index": idx,
                "game_id": game_id,
                "arm_id": row["arm_id"],
                "verdict": verdict,
                "reason": why,
            }
        )
    not_run_games = sorted(
        g for g in actual if g not in cancelled and g not in games_with_rows
    )
    return {
        "schema_version": SCHEMA_VERSION,
        "freeze_utc": freeze_utc,
        "freeze_check": "APPLIED" if freeze_dt is not None else "SKIPPED",
        "rows": verdicts,
        "counts": counts,
        "aggregate_eligible_rows": counts.get(VALID_PROSPECTIVE, 0),
        "not_run_games": not_run_games,
        "cancelled_games": sorted(cancelled),
        "note": (
            "Only VALID_PROSPECTIVE rows are aggregate-eligible; "
            "NOT_RUN means missing evidence, never inferred PASS."
        ),
    }
