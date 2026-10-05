"""nfl_ng_ledger — append-only prospective NFL prediction ledger (schema ``nfl_ng_ledger@1``).

Implementation of Lane C's ``LEDGER_SCHEMA.md`` (cycle NFL-WINPROB-NG-PREP-V1,
PREP lane E). Stdlib only. SYNTHETIC-tested; contains no real games, no real
predictions, no metrics on outcomes.

Laws implemented (LEDGER_SCHEMA.md §1–§4, PROTOCOL_NFL_NG.md §4):

* **Append-only JSONL.** The ledger file is only ever opened for reading or for
  end-appends under ``fcntl.flock``; there is no rewrite, edit, or delete API.
* **Genesis anchor.** Line 1 of the ledger carries
  ``prev_row_hash == "GENESIS:" + sha256_hex(freeze_packet_file_bytes)``.
  :func:`create_ledger` binds the file to the freeze GENESIS digest via an
  adjacent self-hashed genesis record (``<ledger>.genesis.json``) that also
  pins the cycle id, optional frozen arm registry (R4) and optional scoring
  freeze timestamp.  (Genesis record = tool mechanism; the schema itself is
  silent on where the genesis digest lives outside line 1 — documented.)
* **Row schema.** Exactly the 17 fields of LEDGER_SCHEMA.md §2, in that exact
  canonical field order; the set is closed under ``nfl_ng_ledger@1``.
  ``row_hash = sha256_hex(canonical_json(row_without_row_hash))`` where the
  canonical form uses the §2 field order, separators ``,``/``:``, no
  whitespace, ``ensure_ascii=false``, UTF-8 (§3).
* **Timestamp law (R2).** ``recorded_at_utc < kickoff_utc`` strictly at append
  time; re-checked at scoring time against the ACTUAL kickoff:
  ``actual > recorded_at_utc`` and ``actual >= freeze timestamp``.
* **No-outcome law (R8).** No key of any row may contain an
  outcome-vocabulary substring (schema list ∪ dispatch list, case-insensitive).
* **Chain (R1) / duplicates (R5) / probability domain (R6) / enums (R7) /
  immutability (R9).** Enforced at append and re-enforced on every read.
* **Scoring-time classification (R10).** :func:`validate_for_scoring` returns
  per-row ``VALID_PROSPECTIVE`` / ``INVALID_PROSPECTIVE`` /
  ``NOT_SCORED_CANCELLED`` / ``NOT_RUN`` (plus ``NOT_SCORED_NO_ACTUAL_DATA``
  for games absent from the actual-kickoff input — documented extension) and a
  game-level ``not_run_games`` list (played games with no rows).  Only
  ``VALID_PROSPECTIVE`` rows are aggregate-eligible; nothing is inferred PASS
  from absence.
* **Postponement / cancellation.** The schema defines the *classification*
  (postponed later stays valid; moved earlier past ``recorded_at_utc`` is
  ``INVALID_PROSPECTIVE``; cancelled is ``NOT_SCORED_CANCELLED``) but is
  silent on a disclosure mechanism.  This tool emits hash-chained notice rows
  (``row_type`` ``POSTPONEMENT_NOTICE`` / ``CANCELLATION_NOTICE``) inside the
  same append-only file so disclosure is tamper-evident.  Documented as a
  schema-silent decision for the successor freeze packet.
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

__all__ = [
    "SCHEMA_VERSION",
    "FIELD_ORDER",
    "OUTCOME_BLOCKLIST",
    "LedgerError",
    "LedgerValidationError",
    "LedgerIntegrityError",
    "create_ledger",
    "load_genesis",
    "append",
    "postpone",
    "cancel",
    "verify_chain",
    "validate_for_scoring",
    "load_rows",
    "compute_row_hash",
    "canonical_json",
    "parse_iso_z",
    "VALID_PROSPECTIVE",
    "INVALID_PROSPECTIVE",
    "NOT_SCORED_CANCELLED",
    "NOT_RUN",
    "NOT_SCORED_NO_ACTUAL_DATA",
]

# ---------------------------------------------------------------------------
# Constants (LEDGER_SCHEMA.md §2, §4-R8)
# ---------------------------------------------------------------------------

SCHEMA_VERSION = "nfl_ng_ledger@1"
GENESIS_PREFIX = "GENESIS:"
GENESIS_SIDECAR_SCHEMA = "nfl_ng_ledger_genesis@1"

#: The 17 binding fields of LEDGER_SCHEMA.md §2, in canonical (§3) order.
FIELD_ORDER: List[str] = [
    "schema_version",
    "cycle_id",
    "game_id",
    "season",
    "game_type",
    "home_team",
    "away_team",
    "kickoff_utc",
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

#: Outcome-vocabulary blocklist (LEDGER_SCHEMA.md §4-R8 ∪ dispatch blocklist).
#: Case-insensitive substring match against every key of every row.
OUTCOME_BLOCKLIST = (
    "score",
    "pts",
    "result",
    "winner",
    "outcome",
    "final",  # dispatch blocklist
    "margin",  # dispatch blocklist
    "total",  # schema R8
    "spread",  # schema R8
)

GAME_TYPES = ("REG", "POST")

# Scoring-time classification labels (LEDGER_SCHEMA.md §4-R10).
VALID_PROSPECTIVE = "VALID_PROSPECTIVE"
INVALID_PROSPECTIVE = "INVALID_PROSPECTIVE"
NOT_SCORED_CANCELLED = "NOT_SCORED_CANCELLED"
NOT_RUN = "NOT_RUN"
#: Documented extension (schema-silent): row whose game has no entry in the
#: actual-kickoff input at scoring time (season incomplete / data not joined).
#: Excluded from aggregates, disclosed — never inferred PASS from absence.
NOT_SCORED_NO_ACTUAL_DATA = "NOT_SCORED_NO_ACTUAL_DATA"

_TS_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")
_HEX64_RE = re.compile(r"^[0-9a-f]{64}$")
_GENESIS_ANCHOR_RE = re.compile(r"^GENESIS:[0-9a-f]{64}$")
_ROW_HASH_RE = re.compile(r"^[0-9a-f]{64}$")
_P_HOME_RE = re.compile(r"^\d\.\d{6}$")

_WEEKDAY_HINT = "ISO-8601 UTC with Z suffix, seconds precision, e.g. 2026-09-10T00:15:00Z"


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------


class LedgerError(Exception):
    """Base class for all ledger failures (fail-closed family)."""


class LedgerValidationError(LedgerError):
    """A row / argument violates the schema; the write or read is refused."""


class LedgerIntegrityError(LedgerError):
    """Existing ledger state is doubtful; the operation is refused."""


# ---------------------------------------------------------------------------
# Canonical serialization, hashing, timestamps (LEDGER_SCHEMA.md §3)
# ---------------------------------------------------------------------------


def canonical_json(obj: Any) -> str:
    """Canonical JSON: ``,``/``:`` separators, no whitespace, non-ASCII kept."""
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":"))


def sha256_hex(text: str) -> str:
    """Lowercase 64-char hex SHA-256 over the UTF-8 bytes of *text*."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def parse_iso_z(value: Any) -> _dt.datetime:
    """Strict ISO-8601 UTC parse (``...Z`` suffix, no naive, no offsets)."""
    if not isinstance(value, str) or not _TS_RE.match(value):
        raise ValueError(f"malformed timestamp {value!r}; required format: {_WEEKDAY_HINT}")
    try:
        parsed = _dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:  # e.g. month 13, day 32
        raise ValueError(f"malformed timestamp {value!r}: {exc}") from exc
    return parsed.replace(tzinfo=_dt.timezone.utc)


def notice_field_order(row_type: str) -> List[str]:
    """Binding field order for hash-chained notice rows (schema-silent)."""
    order = [
        "schema_version",
        _ROW_TYPE,
        "cycle_id",
        "game_id",
        "season",
        "game_type",
        "home_team",
        "away_team",
        "prior_kickoff_utc",
    ]
    if row_type == POSTPONEMENT_NOTICE:
        order.append("new_kickoff_utc")
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
    """``row_hash`` per §3: SHA-256 over the canonical serialization of the
    row rebuilt in *field_order* with ``row_hash`` removed (``prev_row_hash``
    included).  Independent of the caller's dict key order."""
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
# Genesis record (schema §1 anchor + tool binding; schema-silent mechanism)
# ---------------------------------------------------------------------------


def _sidecar_path(path: Union[str, Path]) -> Path:
    return Path(str(path) + ".genesis.json")


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

    The ledger file itself starts empty; its first prediction row must carry
    ``prev_row_hash == "GENESIS:" + genesis_digest`` (LEDGER_SCHEMA.md §1).
    The binding (plus cycle id, season, optional frozen arm registry for R4
    and optional scoring freeze timestamp) is persisted in an adjacent
    self-hashed genesis record ``<path>.genesis.json`` — the schema is silent
    on a genesis-record mechanism, so this is the tool's documented choice.

    Refuses to overwrite anything (append-only discipline; never recreate).
    """
    path = Path(path)
    sidecar = _sidecar_path(path)
    if path.exists() or sidecar.exists():
        raise LedgerValidationError(
            f"refusing to create {path.name}: ledger or genesis record already exists "
            "(append-only; a ledger is never recreated)"
        )
    if not isinstance(genesis_digest, str) or not _HEX64_RE.match(genesis_digest):
        raise LedgerValidationError("genesis_digest must be lowercase 64-hex sha256 of the freeze packet bytes")
    if not isinstance(cycle_id, str) or not cycle_id:
        raise LedgerValidationError("cycle_id must be a nonempty string")
    if isinstance(season, bool) or not isinstance(season, int) or season < 2026:
        raise LedgerValidationError("season must be an integer >= 2026 for prospective ledgers")
    expected_name = f"predictions_{cycle_id}_{season}.jsonl"
    if path.name != expected_name:
        raise LedgerValidationError(
            f"LEDGER_SCHEMA.md §1 filename law: expected {expected_name!r}, got {path.name!r}"
        )
    registry: Optional[List[str]] = None
    if arm_registry is not None:
        if not isinstance(arm_registry, (list, tuple, set)) or not all(
            isinstance(a, str) and a for a in arm_registry
        ):
            raise LedgerValidationError("arm_registry must be a collection of nonempty strings")
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
        json.dumps(record, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    path.touch()  # empty ledger; line 1 will anchor the chain
    return record


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_iso_z_strict(value: Any, what: str) -> _dt.datetime:
    try:
        return parse_iso_z(value)
    except ValueError as exc:
        raise LedgerValidationError(f"{what}: {exc}") from exc


def load_genesis(path: Union[str, Path]) -> Dict[str, Any]:
    """Load and self-verify the genesis record; fail-closed on tamper/absence."""
    path = Path(path)
    sidecar = _sidecar_path(path)
    if not sidecar.exists():
        raise LedgerIntegrityError(
            f"genesis record missing for {path.name}: ledger is unbound; refusing (fail-closed)"
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


def _validate_prediction_row_fields(row: Dict[str, Any], genesis: Optional[Dict[str, Any]]) -> None:
    """Full append/read validation of one prediction row (R2/R4/R6/R7/R8 +
    structural R3 digest form).  Raises LedgerValidationError."""
    if not isinstance(row, dict):
        raise LedgerValidationError("row must be a JSON object")
    keys = set(row)
    expected = set(FIELD_ORDER)
    # row_hash is computed by this tool; callers may omit it (or must supply
    # the matching value).  Every other field of the closed set is required.
    if keys != expected and keys != (expected - {"row_hash"}):
        missing = sorted(expected - keys)
        extra = sorted(keys - expected)
        raise LedgerValidationError(
            f"field set is not the closed 17-field nfl_ng_ledger@1 set "
            f"(missing={missing}, extra={extra}); additions need a schema-version bump"
        )
    offender = _has_outcome_key(row)
    if offender is not None:
        raise LedgerValidationError(
            f"no-outcome law (R8): key {offender!r} matches the outcome vocabulary"
        )
    if row["schema_version"] != SCHEMA_VERSION:
        raise LedgerValidationError(f"schema_version must be {SCHEMA_VERSION!r}")
    for field in ("cycle_id", "game_id", "home_team", "away_team", "arm_id", "model_version", "recorded_by"):
        _require_nonempty_str(row, field)
    if genesis is not None and row["cycle_id"] != genesis["cycle_id"]:
        raise LedgerValidationError(
            f"cycle_id {row['cycle_id']!r} does not match the genesis-bound cycle "
            f"{genesis['cycle_id']!r}"
        )
    season = row["season"]
    if isinstance(season, bool) or not isinstance(season, int) or season < 2026:
        raise LedgerValidationError("season must be an integer >= 2026 (R7)")
    if row["game_type"] not in GAME_TYPES:
        raise LedgerValidationError(f"game_type must be one of {GAME_TYPES} (R7); PRE is forbidden")
    kickoff = parse_iso_z_strict(row["kickoff_utc"], "kickoff_utc")
    recorded = parse_iso_z_strict(row["recorded_at_utc"], "recorded_at_utc")
    if recorded >= kickoff:
        raise LedgerValidationError(
            "timestamp law (R2): recorded_at_utc must be strictly < kickoff_utc"
        )
    if genesis is not None:
        registry = genesis.get("arm_registry")
        if registry is not None and row["arm_id"] not in registry:
            raise LedgerValidationError(
                f"arm registry law (R4): arm_id {row['arm_id']!r} is not in the frozen registry"
            )
    for digest_field in ("arm_config_digest", "inputs_digest"):
        value = row[digest_field]
        if not isinstance(value, str) or not _HEX64_RE.match(value):
            raise LedgerValidationError(
                f"{digest_field} must be lowercase 64-hex sha256 (structural check; "
                "semantic freeze-registry match is a scoring-time law R3)"
            )
    validate_p_home(row["p_home"])
    prev = row["prev_row_hash"]
    if not isinstance(prev, str) or not (_GENESIS_ANCHOR_RE.match(prev) or _ROW_HASH_RE.match(prev)):
        raise LedgerValidationError(
            "prev_row_hash must be a 64-hex row hash or 'GENESIS:<64-hex>' for line 1"
        )


def validate_p_home(value: Any) -> Decimal:
    """R6: string with exactly 6 fractional digits, strictly inside (0, 1)."""
    if not isinstance(value, str):
        raise LedgerValidationError(
            f"p_home must be a STRING with exactly 6 decimal places (got {type(value).__name__})"
        )
    if not _P_HOME_RE.match(value):
        raise LedgerValidationError(
            f"p_home {value!r} is not a decimal string with exactly 6 fractional digits"
        )
    try:
        number = Decimal(value)
    except Exception as exc:  # pragma: no cover - regex precludes this
        raise LedgerValidationError(f"p_home {value!r} is not a finite decimal") from exc
    if not (Decimal("0") < number < Decimal("1")):
        raise LedgerValidationError(f"p_home {value!r} outside strict open interval (0, 1) (R6)")
    return number


def _validate_notice_row_fields(row: Dict[str, Any]) -> None:
    if row.get(_ROW_TYPE) not in (POSTPONEMENT_NOTICE, CANCELLATION_NOTICE):
        raise LedgerValidationError(f"unknown row_type {row.get(_ROW_TYPE)!r}")
    if row["schema_version"] != SCHEMA_VERSION:
        raise LedgerValidationError("notice schema_version mismatch")
    for field in ("cycle_id", "game_id", "home_team", "away_team", "reason", "recorded_by"):
        _require_nonempty_str(row, field)
    if isinstance(row["season"], bool) or not isinstance(row["season"], int) or row["season"] < 2026:
        raise LedgerValidationError("notice season must be an integer >= 2026")
    if row["game_type"] not in GAME_TYPES:
        raise LedgerValidationError("notice game_type must be REG or POST")
    parse_iso_z_strict(row["prior_kickoff_utc"], "prior_kickoff_utc")
    if row[_ROW_TYPE] == POSTPONEMENT_NOTICE:
        parse_iso_z_strict(row["new_kickoff_utc"], "new_kickoff_utc")
    parse_iso_z_strict(row["noticed_at_utc"], "noticed_at_utc")
    affected = row["affected_row_indices"]
    if not isinstance(affected, list) or not all(
        isinstance(i, int) and not isinstance(i, bool) and i >= 0 for i in affected
    ):
        raise LedgerValidationError("affected_row_indices must be a list of nonnegative ints")
    prev = row["prev_row_hash"]
    if not isinstance(prev, str) or not (_GENESIS_ANCHOR_RE.match(prev) or _ROW_HASH_RE.match(prev)):
        raise LedgerValidationError("notice prev_row_hash malformed")


# ---------------------------------------------------------------------------
# Locked file primitives (append-only by construction)
# ---------------------------------------------------------------------------


class _LockedLedger:
    """Exclusive-flock handle opened read+write; writes only ever go to EOF."""

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
    raw = fh.read()
    return raw.splitlines()


def _parse_existing(fh: Any, genesis: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse every existing line; fail-closed on blank/malformed lines, on any
    stored row_hash that does not recompute, and on any broken linkage
    (never extend a doubtful ledger)."""
    rows: List[Dict[str, Any]] = []
    prev_stored: Optional[str] = None
    for idx, line in enumerate(_read_lines(fh)):
        if not line.strip():
            raise LedgerIntegrityError(f"blank line at ledger index {idx}")
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise LedgerIntegrityError(f"malformed JSON at ledger index {idx}: {exc}") from exc
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
    """Rebuild a row with keys in the binding §2 field order so the written
    line is canonical regardless of the caller's dict insertion order."""
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
# Public API: append
# ---------------------------------------------------------------------------


def append(path: Union[str, Path], row: Dict[str, Any]) -> Dict[str, Any]:
    """Validate and append one prediction row; returns the row as written.

    The tool computes ``row_hash``; if the caller supplies one it must already
    match (fail-closed).  Refuses: non-closed field sets, outcome-vocabulary
    keys (R8), ``recorded_at_utc >= kickoff_utc`` (R2), malformed timestamps,
    out-of-registry arms when a registry is bound (R4), duplicate
    ``(game_id, arm_id)`` (R5), duplicate ``row_hash``, wrong chain parent
    (R1), ``p_home`` not a 6-dp string inside (0,1) (R6), bad enums (R7).
    """
    path = Path(path)
    genesis = load_genesis(path)  # fail-closed if unbound/tampered
    candidate = dict(row)
    provided_hash = candidate.get("row_hash")
    _validate_prediction_row_fields(candidate, genesis)
    with _LockedLedger(path) as fh:
        existing = _parse_existing(fh, genesis)
        if candidate["prev_row_hash"] != _required_parent(existing, genesis):
            expected = _required_parent(existing, genesis)
            raise LedgerValidationError(
                f"wrong chain parent (R1): prev_row_hash must be {expected[:20]}…, "
                f"got {str(candidate['prev_row_hash'])[:20]}…"
            )
        pairs = {
            (r["game_id"], r["arm_id"])
            for r in existing
            if _ROW_TYPE not in r
        }
        if (candidate["game_id"], candidate["arm_id"]) in pairs:
            raise LedgerValidationError(
                f"duplicate (game_id, arm_id) (R5): ({candidate['game_id']!r}, {candidate['arm_id']!r})"
            )
        seen_hashes = {r["row_hash"] for r in existing}
        computed = compute_row_hash(candidate, FIELD_ORDER)
        if provided_hash is not None and provided_hash != computed:
            raise LedgerValidationError(
                "supplied row_hash does not match the canonical recomputation"
            )
        if computed in seen_hashes:
            raise LedgerValidationError("duplicate row_hash: an identical row already exists")
        candidate["row_hash"] = computed
        _write_row(fh, candidate, FIELD_ORDER)
    return candidate


def load_rows(path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Parse the full ledger (no validation — callers must verify_chain first)."""
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
# Public API: postponement / cancellation notices (schema-silent mechanism)
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
    prior_kickoff_utc: Optional[str],
    game_meta: Optional[Dict[str, Any]],
    new_kickoff_utc: Optional[str] = None,
) -> Dict[str, Any]:
    if not isinstance(recorded_by, str) or not recorded_by:
        raise LedgerValidationError("recorded_by (recorder session id) is required for notices")
    if not isinstance(reason, str) or not reason.strip():
        raise LedgerValidationError("reason must be a nonempty string")
    noticed = noticed_at_utc if noticed_at_utc is not None else _now_iso()
    genesis = load_genesis(path)
    new_kick_dt = parse_iso_z_strict(new_kickoff_utc, "new_kickoff_utc") if new_kickoff_utc else None
    with _LockedLedger(path) as fh:
        existing = _parse_existing(fh, genesis)
        rows_for_game = _game_rows(existing, game_id)
        if rows_for_game:
            scheduled = {r["kickoff_utc"] for _, r in rows_for_game}
            if len(scheduled) > 1:
                raise LedgerIntegrityError(
                    f"inconsistent scheduled kickoffs recorded for game {game_id!r}"
                )
            prior_kickoff = scheduled.pop()
            meta = rows_for_game[0][1]
            if new_kick_dt is not None:
                affected = [
                    i
                    for i, r in rows_for_game
                    if parse_iso_z(r["recorded_at_utc"]) >= new_kick_dt
                ]
            else:  # cancellation: every row of the game is excluded at scoring
                affected = [i for i, _ in rows_for_game]
        else:
            if prior_kickoff_utc is None or game_meta is None:
                raise LedgerValidationError(
                    f"game {game_id!r} has no rows; supply prior_kickoff_utc and "
                    "game_meta(season, game_type, home_team, away_team)"
                )
            prior_kickoff = prior_kickoff_utc
            missing = {"season", "game_type", "home_team", "away_team"} - set(game_meta or {})
            if missing:
                raise LedgerValidationError(f"game_meta missing fields: {sorted(missing)}")
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
            "prior_kickoff_utc": prior_kickoff,
        }
        if row_type == POSTPONEMENT_NOTICE:
            notice["new_kickoff_utc"] = new_kickoff_utc
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
    new_kickoff_utc: str,
    reason: str,
    *,
    prior_kickoff_utc: Optional[str] = None,
    game_meta: Optional[Dict[str, Any]] = None,
    noticed_at_utc: Optional[str] = None,
    recorded_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Record a postponement/flex as a hash-chained ``POSTPONEMENT_NOTICE``.

    Classification is NOT changed here (append-only — nothing is ever marked
    in place): a move LATER keeps existing rows valid (re-confirmed at scoring
    against the actual kickoff); a move EARLIER past a row's
    ``recorded_at_utc`` makes those rows ``INVALID_PROSPECTIVE`` at scoring
    time.  ``affected_row_indices`` in the notice discloses which existing
    line indices the move invalidates (0 if the move is later than every
    recorded_at).  If the game has no rows yet, supply ``prior_kickoff_utc``
    and ``game_meta``.
    """
    return _emit_notice(
        Path(path),
        POSTPONEMENT_NOTICE,
        game_id,
        reason,
        noticed_at_utc,
        recorded_by,
        prior_kickoff_utc,
        game_meta,
        new_kickoff_utc=new_kickoff_utc,
    )


def cancel(
    path: Union[str, Path],
    game_id: str,
    reason: str,
    *,
    prior_kickoff_utc: Optional[str] = None,
    game_meta: Optional[Dict[str, Any]] = None,
    noticed_at_utc: Optional[str] = None,
    recorded_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Record a cancellation as a hash-chained ``CANCELLATION_NOTICE``; the
    game's rows classify ``NOT_SCORED_CANCELLED`` at scoring (excluded, no
    outcome join) whether the status comes from this notice or from the
    scoring-time ``cancelled_games`` input."""
    return _emit_notice(
        Path(path),
        CANCELLATION_NOTICE,
        game_id,
        reason,
        noticed_at_utc,
        recorded_by,
        prior_kickoff_utc,
        game_meta,
    )


# ---------------------------------------------------------------------------
# Public API: verification (R1 full re-hash walk + read-side laws)
# ---------------------------------------------------------------------------


def verify_chain(
    path: Union[str, Path],
    expected_genesis_digest: Optional[str] = None,
) -> List[int]:
    """Full re-hash walk of the ledger; returns the 0-based indices of broken
    rows (empty list = intact).

    Re-validates on read: chain linkage (R1) against the genesis binding,
    hash recomputation (§3), closed field sets, the no-outcome law (R8), the
    timestamp law (R2), p_home domain (R6), enums (R7), duplicate
    ``(game_id, arm_id)`` (R5, later index broken) and duplicate row_hash.
    Raises ``LedgerIntegrityError`` (fail-closed) when the ledger or its
    genesis binding itself is unreadable/tampered, or when
    *expected_genesis_digest* contradicts the bound genesis digest.
    """
    path = Path(path)
    genesis = load_genesis(path)
    if expected_genesis_digest is not None and expected_genesis_digest != genesis["genesis_digest"]:
        raise LedgerIntegrityError(
            "expected_genesis_digest does not match the ledger's genesis record "
            "(R1: line 1 must anchor to the freeze packet GENESIS digest)"
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
                row_type = row.get(_ROW_TYPE)
                known_type = _ROW_TYPE not in row or row_type in (
                    POSTPONEMENT_NOTICE,
                    CANCELLATION_NOTICE,
                )
                field_order = _field_order_for(row) if known_type else None
                if not known_type or set(row) != set(field_order):
                    broken.append(idx)
                elif _has_outcome_key(row) is not None:  # R8 read-side guard
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
                                raise LedgerValidationError("duplicate (game_id, arm_id) (R5)")
                            seen_pairs.add(pair)
                    except LedgerValidationError:
                        broken.append(idx)
                    else:
                        if row["row_hash"] in seen_hashes:
                            broken.append(idx)
                        else:
                            seen_hashes.add(row["row_hash"])
                row_hash_here = row.get("row_hash") if isinstance(row.get("row_hash"), str) else None
            else:
                row_hash_here = None
        # Chain linkage is defined over STORED hash values: a tampered row
        # breaks at its own index; its stored hash remains the parent for the
        # next link so one tamper does not cascade.
        prev_stored_hash = row_hash_here
    return sorted(set(broken))


# ---------------------------------------------------------------------------
# Public API: scoring-time validation (R2 actual-kickoff gate, R10 classes)
# ---------------------------------------------------------------------------


def validate_for_scoring(
    path: Union[str, Path],
    actual_kickoffs: Dict[str, str],
    cancelled_games: Optional[Set[str]] = None,
    freeze_utc: Optional[str] = None,
) -> Dict[str, Any]:
    """The real anti-retrospective gate.  Fails closed on any chain break.

    *actual_kickoffs*: ``{game_id: actual kickoff ISO-Z}`` from the audited
    final data.  *cancelled_games*: game ids with no result.  *freeze_utc*:
    the successor cycle's freeze timestamp (defaults to the genesis-bound
    value when present).

    Per-row verdicts (R10): cancelled → ``NOT_SCORED_CANCELLED``; game absent
    from *actual_kickoffs* → ``NOT_SCORED_NO_ACTUAL_DATA`` (documented
    extension); ``actual <= recorded_at_utc`` → ``INVALID_PROSPECTIVE``
    (retro-injection / kickoff moved earlier past the record);
    ``actual < freeze_utc`` → ``NOT_RUN`` (played-before-freeze write-off —
    can never be repaired retroactively); else ``VALID_PROSPECTIVE``.
    Additionally reports game-level ``not_run_games`` (played games with no
    rows — missing evidence, never inferred PASS).
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
    for game_id, kick in actual_kickoffs.items():
        actual[game_id] = parse_iso_z_strict(kick, f"actual_kickoffs[{game_id!r}]")
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
            why = "no actual kickoff in scoring input; unresolved, excluded"
        else:
            actual_dt = actual[game_id]
            recorded_dt = parse_iso_z(row["recorded_at_utc"])
            if actual_dt <= recorded_dt:
                verdict = INVALID_PROSPECTIVE
                why = (
                    "actual kickoff is not strictly after recorded_at_utc "
                    "(retro-injection or kickoff moved earlier past the record); "
                    "permanent — never repairable retroactively"
                )
            elif freeze_dt is not None and actual_dt < freeze_dt:
                verdict = NOT_RUN
                why = "actual kickoff precedes the cycle freeze timestamp (played-before-record write-off)"
            else:
                verdict = VALID_PROSPECTIVE
                why = "recorded strictly before the actual kickoff and inside the prospective window"
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
            "Only VALID_PROSPECTIVE rows are aggregate-eligible (R10); "
            "NOT_RUN means missing evidence, never inferred PASS."
        ),
    }
