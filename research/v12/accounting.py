"""V12 publication accounting -- zero-position guard + observed-once refusals.

P1 lane A2.  This module is the publication-side accounting helper for the
per-sprint V12 ledger package defined by the FROZEN control artifact
``research/control/v12_run/ledger_package/schema.json`` (read-only for this
lane).  It repairs two documented V11 launch incidents without touching any
historical ledger byte:

* **L-V11-4 (zero-position baseline)** -- launch-1 published a zero-position
  baseline because ``score_valid=true`` over all-zero finite metrics passed
  the pre-score gate.  :func:`validate_position_evidence` refuses any
  computed output with ``n_positions <= 0`` (``REFUSED_ZERO_POSITIONS``) or
  without at least one valid decision/fill record
  (``REFUSED_NO_VALID_DECISION_FILL``).  Missing evidence fails closed --
  absence is never read as zero or as a pass.  The legacy
  :func:`research.adapter_v10.publish.evaluate_pre_score_gate` delegates here
  when its callers opt in (``position_evidence=True``); the V12 entry point
  :func:`publish_v12_cell` always enforces it.
* **L-V11-1 (generic stress superset)** -- the generic 6-cell stress matrix
  is a superset of what frozen family contracts accept.
  :func:`enforce_family_contract_cells` takes the FROZEN per-family cell list
  and refuses any computed cell outside it with
  ``REFUSED_CELL_OUTSIDE_FAMILY_CONTRACT``.  (The cell derivation itself is
  owned by lane A4 in ``research/adapter_v10/stress.py`` -- never edited
  here.)

Row schemas (frozen, from ``schema.json``):

``CELL_RESULT``
    ``row_type, trial_key, arm_id, arm_config_digest, family, cell,
    result_sha256, published_utc, producer_head_sha``
``OBSERVATION``
    ``row_type, trial_key, reason, observed_utc, producer_head_sha, note``

Invariants (enforced on every read AND every append, fail closed):

* append-only JSONL; no row is ever rewritten or deleted;
* ``trial_key`` is unique across ALL rows;
* every computed scored base result appears exactly once -- published as
  ``CELL_RESULT`` or refused as ``OBSERVATION``;
* exact replay of the same trial (same ``trial_key``, which includes the
  ``arm_config_digest``) increments NEITHER counter and adds NO row.

Calling convention for V12 drivers
----------------------------------

1. Freeze the per-family cell list from the family contract (lane A4's
   derivation; probe the frozen folds contract) and pass it as
   ``family_contract_cells`` -- a sequence of :class:`~research.adapter_v10.protocol.StressSpec`
   instances or stress-signature mappings -- to :func:`publish_v12_cell`.
2. Call :func:`publish_v12_cell` exactly once per computed cell with the
   identity fields (``arm_config_digest`` included) and the computed
   ``scored_metrics``.  The function decides the honest outcome:

   * all gates pass            -> one ``CELL_RESULT`` row (published +1);
   * any refusal reason        -> one ``OBSERVATION`` row (observed +1);
   * exact replay (same key)   -> no row, both counters unchanged
     (``stage=IDEMPOTENT_REPLAY``).

3. Read counters only through :func:`v12_denominator_view`; never count raw
   lines.

Fail-closed rules inherited from the factory: no silent defaults, no
fabricated metrics, no rewrite of any existing byte; a corrupt or
schema-violating ledger refuses every further append.
"""

from __future__ import annotations

import hashlib
import json
import math
import subprocess
import threading
from pathlib import Path
from typing import Any, Mapping, Optional, Sequence

from research.adapter_v10.protocol import ContractViolation, StressSpec

# --------------------------------------------------------------------------- #
# Frozen schema tokens (research/control/v12_run/ledger_package/schema.json)
# --------------------------------------------------------------------------- #
LEDGER_PACKAGE_SCHEMA = "v12_ledger_package_v1"
ROW_TYPE_CELL_RESULT = "CELL_RESULT"
ROW_TYPE_OBSERVATION = "OBSERVATION"
V12_ROW_TYPES: tuple[str, ...] = (ROW_TYPE_CELL_RESULT, ROW_TYPE_OBSERVATION)

#: Frozen CELL_RESULT field contract (schema.json row_schemas).
CELL_RESULT_REQUIRED_FIELDS: tuple[str, ...] = (
    "row_type",
    "trial_key",
    "arm_id",
    "arm_config_digest",
    "family",
    "cell",
    "result_sha256",
    "published_utc",
    "producer_head_sha",
)
#: Frozen OBSERVATION field contract (schema.json row_schemas; the trailing
#: schema entry is the ``note`` field whose frozen text documents the row).
OBSERVATION_REQUIRED_FIELDS: tuple[str, ...] = (
    "row_type",
    "trial_key",
    "reason",
    "observed_utc",
    "producer_head_sha",
    "note",
)
OBSERVATION_FROZEN_NOTE = "compute-once observation; never publishable"

#: Versioned token inside the trial-key payload so the key definition itself
#: is auditable and can never silently drift.
TRIAL_KEY_SCHEMA = "v12.trial_key.v1"

# --------------------------------------------------------------------------- #
# Refusal reason codes (machine-readable, stable)
# --------------------------------------------------------------------------- #
REFUSED_ZERO_POSITIONS = "REFUSED_ZERO_POSITIONS"
REFUSED_NO_VALID_DECISION_FILL = "REFUSED_NO_VALID_DECISION_FILL"
REFUSED_POSITION_COUNT_ABSENT = "REFUSED_POSITION_COUNT_ABSENT"
REFUSED_POSITION_COUNT_INVALID = "REFUSED_POSITION_COUNT_INVALID"
REFUSED_CELL_OUTSIDE_FAMILY_CONTRACT = "REFUSED_CELL_OUTSIDE_FAMILY_CONTRACT"
REFUSED_PRESCORE_FLAG_FALSE = "REFUSED_PRESCORE_FLAG_FALSE"
REFUSED_PRESCORE_FIELD_ABSENT = "REFUSED_PRESCORE_FIELD_ABSENT"
REFUSED_PRESCORE_FIELD_NON_FINITE = "REFUSED_PRESCORE_FIELD_NON_FINITE"
REFUSED_PRESCORE_FIELD_NOT_NUMERIC = "REFUSED_PRESCORE_FIELD_NOT_NUMERIC"
REFUSED_TRIAL_KEY_ALREADY_PRESENT = "REFUSED_TRIAL_KEY_ALREADY_PRESENT"

#: Honest outcome stages of :func:`publish_v12_cell`.  ``PUBLISHED`` and the
#: replay token reuse the historical factory vocabulary exactly.
STAGE_PUBLISHED = "PUBLISHED"
STAGE_REFUSED = "REFUSED"
STAGE_IDEMPOTENT_REPLAY = "IDEMPOTENT_REPLAY_SKIPPED"

#: Scored metric fields that MUST be present and finite to publish (same
#: vocabulary as the legacy pre-score gate).
REQUIRED_SCORED_FIELDS: tuple[str, ...] = (
    "net_return_sum",
    "expectancy_per_day",
    "max_drawdown",
)

#: Counter fields accepted as decision/fill evidence (publication requires
#: at least ONE of these to be a positive integer).
DECISION_FILL_COUNT_FIELDS: tuple[str, ...] = ("n_decisions", "n_fills")
#: Sequence fields accepted as decision/fill evidence (at least one VALID
#: record required).
DECISION_FILL_RECORD_FIELDS: tuple[str, ...] = ("decisions", "fills")
#: A decision/fill record is VALID iff it is a mapping carrying a non-empty
#: instrument and a non-null timestamp field from this vocabulary.
RECORD_SYMBOL_FIELDS: tuple[str, ...] = ("symbol", "instrument")
RECORD_TIMESTAMP_FIELDS: tuple[str, ...] = (
    "ts",
    "timestamp",
    "ts_ns",
    "decision_ts",
    "filled_at",
)

#: Process-local single-writer lock around every check-then-append critical
#: section so concurrent writers append serialized rows and exactly-once
#: accounting holds in-process (cross-process writers to ONE ledger file are
#: excluded by factory policy: one writer per worktree ledger).  Reentrant
#: because ``publish_v12_cell`` calls ``append_v12_row`` while holding it.
_V12_LEDGER_LOCK = threading.RLock()


# --------------------------------------------------------------------------- #
# Canonicalisation helpers
# --------------------------------------------------------------------------- #
def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(dict(payload), sort_keys=True, separators=(",", ":"), default=str)


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canonical_cell_signature(stress: Any) -> dict[str, Any]:
    """Canonical stress-signature mapping for one cell.

    Accepts a :class:`StressSpec` (uses its frozen ``signature()`` view) or
    an already-canonical signature mapping.  Anything else is refused.
    """
    if isinstance(stress, StressSpec):
        return dict(stress.signature())
    if isinstance(stress, Mapping):
        return dict(stress)
    raise ContractViolation(
        "cell signature must be a StressSpec or a signature mapping; "
        f"got {type(stress).__name__}"
    )


def canonical_cell_key(stress: Any) -> str:
    """Stable string key of one stress cell (canonical JSON of signature)."""
    return _sha256_text(_canonical_json(canonical_cell_signature(stress)))


def current_producer_head_sha() -> str:
    """``git rev-parse HEAD`` of the producing worktree (best effort).

    Never fabricated: when git is unavailable the honest token
    ``UNAVAILABLE_GIT_HEAD`` is returned so the row schema stays satisfiable
    without inventing a hash.
    """
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        )
        head = out.stdout.strip()
        return head if head else "UNAVAILABLE_GIT_HEAD"
    except Exception:
        return "UNAVAILABLE_GIT_HEAD"


# --------------------------------------------------------------------------- #
# Zero-position / decision-fill evidence gate (L-V11-4)
# --------------------------------------------------------------------------- #
def validate_position_evidence(
    scored_metrics: Optional[Mapping[str, Any]]
) -> tuple[bool, list[str]]:
    """Fail-closed position evidence for publication (repairs L-V11-4).

    Publication requires BOTH:

    1. ``n_positions`` present, integer (bools refused), and ``> 0`` --
       ``n_positions == 0`` yields ``REFUSED_ZERO_POSITIONS``;
    2. at least one valid decision/fill record: a positive-integer
       ``n_decisions``/``n_fills`` counter OR a ``decisions``/``fills``
       sequence containing at least one valid record (mapping with a
       non-empty instrument and a non-null timestamp).

    Missing ``n_positions`` is a refusal (``REFUSED_POSITION_COUNT_ABSENT``),
    never a pass: absence of evidence fails closed exactly like the
    launch-1 incident it repairs.
    """
    if not isinstance(scored_metrics, Mapping):
        return False, [REFUSED_POSITION_COUNT_ABSENT]
    reasons: list[str] = []

    if "n_positions" not in scored_metrics:
        reasons.append(REFUSED_POSITION_COUNT_ABSENT)
    else:
        raw = scored_metrics.get("n_positions")
        if isinstance(raw, bool) or not isinstance(raw, int):
            reasons.append(REFUSED_POSITION_COUNT_INVALID)
        elif int(raw) <= 0:
            reasons.append(REFUSED_ZERO_POSITIONS)

    has_counter_evidence = False
    for field in DECISION_FILL_COUNT_FIELDS:
        value = scored_metrics.get(field)
        if value is None:
            continue
        if isinstance(value, bool) or not isinstance(value, int) or int(value) <= 0:
            reasons.append(f"{REFUSED_NO_VALID_DECISION_FILL}:{field}_not_positive_int")
        else:
            has_counter_evidence = True

    has_record_evidence = False
    for field in DECISION_FILL_RECORD_FIELDS:
        records = scored_metrics.get(field)
        if records is None:
            continue
        if isinstance(records, (str, bytes)) or not isinstance(records, Sequence):
            reasons.append(f"{REFUSED_NO_VALID_DECISION_FILL}:{field}_not_a_sequence")
            continue
        if any(_is_valid_decision_fill_record(rec) for rec in records):
            has_record_evidence = True

    if not (has_counter_evidence or has_record_evidence):
        reasons.append(REFUSED_NO_VALID_DECISION_FILL)

    return (not reasons), reasons


def _is_valid_decision_fill_record(record: Any) -> bool:
    """One decision/fill record is valid iff instrumented and time-stamped."""
    if not isinstance(record, Mapping):
        return False
    has_symbol = any(
        str(record.get(field, "") or "").strip() for field in RECORD_SYMBOL_FIELDS
    )
    has_timestamp = any(record.get(field) is not None for field in RECORD_TIMESTAMP_FIELDS)
    return has_symbol and has_timestamp


def validate_pre_score_metrics(
    scored_metrics: Optional[Mapping[str, Any]],
    *,
    required_fields: Sequence[str] = REQUIRED_SCORED_FIELDS,
) -> tuple[bool, list[str]]:
    """V12 pre-score gate: score flag + finite required metrics.

    Same semantics as the legacy gate, but emits the stable V12 reason codes
    so refused computes carry one uniform refusal vocabulary.
    """
    if not isinstance(scored_metrics, Mapping):
        return False, [REFUSED_PRESCORE_FLAG_FALSE, REFUSED_PRESCORE_FIELD_ABSENT]
    reasons: list[str] = []
    if not bool(scored_metrics.get("score_valid", False)):
        reasons.append(REFUSED_PRESCORE_FLAG_FALSE)
    for field in required_fields:
        value = scored_metrics.get(field)
        if value is None:
            reasons.append(f"{REFUSED_PRESCORE_FIELD_ABSENT}:{field}")
        elif isinstance(value, float) and not math.isfinite(value):
            reasons.append(f"{REFUSED_PRESCORE_FIELD_NON_FINITE}:{field}")
        elif not isinstance(value, (int, float)) or isinstance(value, bool):
            reasons.append(f"{REFUSED_PRESCORE_FIELD_NOT_NUMERIC}:{field}")
    return (not reasons), reasons


# --------------------------------------------------------------------------- #
# Trial identity -- same key whether the trial publishes or is refused
# --------------------------------------------------------------------------- #
def v12_trial_key(
    *,
    strategy_id: str,
    family: str,
    arm_id: str,
    arm_config_digest: str,
    stress_signature: Any,
    window_start_iso: str,
    window_end_iso: str,
) -> str:
    """Deterministic sha256 trial key (identity ONLY -- never the outcome).

    ``arm_config_digest`` is part of the key material (deliverable 3), so an
    exact replay of the same trial reproduces the same key and every
    score-affecting arm change produces a different one.  The outcome
    (result digest, refusal reason) is deliberately EXCLUDED so a refused
    compute and its would-be publication share exactly one key -- the
    ledger can then carry the trial exactly once either way.
    """
    payload = {
        "schema": TRIAL_KEY_SCHEMA,
        "strategy_id": str(strategy_id),
        "family": str(family),
        "arm_id": str(arm_id),
        "arm_config_digest": str(arm_config_digest),
        "cell": canonical_cell_signature(stress_signature),
        "window_start_iso": str(window_start_iso),
        "window_end_iso": str(window_end_iso),
    }
    return _sha256_text(_canonical_json(payload))


# --------------------------------------------------------------------------- #
# Family-contract cell guard (L-V11-1)
# --------------------------------------------------------------------------- #
def freeze_family_cell_contract(
    family: str, cells: Sequence[Any]
) -> dict[str, dict[str, Any]]:
    """Freeze the per-family cell list into ``{cell_key: signature}``.

    ``cells`` comes from the FROZEN family contract (lane A4's per-family
    derivation over the frozen folds contract) -- never from the generic
    stress matrix.  Deterministic; duplicate keys are refused.
    """
    if not str(family).strip():
        raise ContractViolation("family_contract.family must be non-empty")
    frozen: dict[str, dict[str, Any]] = {}
    for cell in cells:
        signature = canonical_cell_signature(cell)
        key = _sha256_text(_canonical_json(signature))
        if key in frozen:
            raise ContractViolation(
                f"family_contract duplicate cell key for family {family!r}"
            )
        frozen[key] = signature
    return frozen


def validate_family_contract_cells(
    contract_cells: Mapping[str, Mapping[str, Any]],
    computed_cells: Sequence[Any],
) -> list[str]:
    """Offending cell keys (subset superset check).  Empty list == OK."""
    offenders: list[str] = []
    for cell in computed_cells:
        key = _sha256_text(_canonical_json(canonical_cell_signature(cell)))
        if key not in contract_cells:
            offenders.append(key)
    return offenders


def enforce_family_contract_cells(
    contract_cells: Mapping[str, Mapping[str, Any]],
    computed_cells: Sequence[Any],
    *,
    family: str = "",
) -> None:
    """Raise :class:`ContractViolation` on ANY cell outside the frozen
    per-family contract (generic superset -- L-V11-1), with the stable
    reason code ``REFUSED_CELL_OUTSIDE_FAMILY_CONTRACT``."""
    offenders = validate_family_contract_cells(contract_cells, computed_cells)
    if offenders:
        raise ContractViolation(
            f"{REFUSED_CELL_OUTSIDE_FAMILY_CONTRACT}:"
            f"family={family or 'unspecified'};"
            f"cell_keys={','.join(sorted(offenders))}"
        )


# --------------------------------------------------------------------------- #
# Ledger IO -- read, verify, append (single-writer serialized)
# --------------------------------------------------------------------------- #
def read_v12_ledger(path: str | Path) -> dict[str, Any]:
    """Read-only snapshot of the V12 ledger, verifying the frozen invariants.

    Returns ``{"path", "rows", "count", "sha256", "existed"}``.  A missing
    file is an honest empty snapshot; a corrupt line, an unknown
    ``row_type``, a missing/blank required field or a DUPLICATE
    ``trial_key`` raises :class:`ContractViolation` (fail closed -- a
    violating ledger refuses every further append).
    """
    target = Path(path)
    if not target.exists():
        return {
            "path": str(target),
            "rows": [],
            "count": 0,
            "sha256": None,
            "existed": False,
        }
    rows: list[dict[str, Any]] = []
    seen_keys: set[str] = set()
    with open(target, "r", encoding="utf-8") as handle:
        for lineno, raw in enumerate(handle, start=1):
            line = raw.strip()
            if not line:
                continue
            try:
                doc = json.loads(line)
            except ValueError as exc:
                raise ContractViolation(
                    f"v12_ledger_corrupt_line:{lineno}:{exc}"
                ) from exc
            if not isinstance(doc, Mapping):
                raise ContractViolation(f"v12_ledger_line_not_object:{lineno}")
            row = dict(doc)
            reasons = validate_v12_row(row)
            if reasons:
                raise ContractViolation(
                    f"v12_ledger_schema_violation:line={lineno};" + ";".join(reasons)
                )
            key = str(row["trial_key"])
            if key in seen_keys:
                raise ContractViolation(
                    f"v12_ledger_duplicate_trial_key:line={lineno}:{key}"
                )
            seen_keys.add(key)
            rows.append(row)
    digest = hashlib.sha256()
    with open(target, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return {
        "path": str(target),
        "rows": rows,
        "count": len(rows),
        "sha256": digest.hexdigest(),
        "existed": True,
    }


def validate_v12_row(row: Mapping[str, Any]) -> list[str]:
    """Reason strings for any violated frozen row schema (empty list == OK)."""
    reasons: list[str] = []
    row_type = row.get("row_type")
    if row_type not in V12_ROW_TYPES:
        return [f"unknown_v12_row_type:{row_type!r}"]
    required = (
        CELL_RESULT_REQUIRED_FIELDS
        if row_type == ROW_TYPE_CELL_RESULT
        else OBSERVATION_REQUIRED_FIELDS
    )
    for field in required:
        value = row.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            reasons.append(f"v12_row_missing_field:{field}")
    key = row.get("trial_key")
    if isinstance(key, str) and (len(key) != 64 or any(c not in "0123456789abcdef" for c in key)):
        reasons.append("v12_row_trial_key_not_sha256_hex")
    if row_type == ROW_TYPE_OBSERVATION:
        note = row.get("note")
        if note is not None and str(note) != OBSERVATION_FROZEN_NOTE:
            reasons.append("v12_row_observation_note_drift")
        reason = str(row.get("reason", ""))
        if reason and not _is_documented_refusal_reason(reason):
            reasons.append(f"v12_row_undocumented_refusal_reason:{reason}")
    return reasons


def _is_documented_refusal_reason(reason: str) -> bool:
    base = reason.split(":", 1)[0]
    documented = {
        REFUSED_ZERO_POSITIONS,
        REFUSED_NO_VALID_DECISION_FILL,
        REFUSED_POSITION_COUNT_ABSENT,
        REFUSED_POSITION_COUNT_INVALID,
        REFUSED_CELL_OUTSIDE_FAMILY_CONTRACT,
        REFUSED_PRESCORE_FLAG_FALSE,
        REFUSED_TRIAL_KEY_ALREADY_PRESENT,
        "REFUSED_PRESCORE_FIELD_ABSENT",
        "REFUSED_PRESCORE_FIELD_NON_FINITE",
        "REFUSED_PRESCORE_FIELD_NOT_NUMERIC",
        "LEDGER_APPEND_REFUSED",
    }
    return base in documented


def append_v12_row(
    entry: Mapping[str, Any], path: str | Path
) -> dict[str, Any]:
    """Serialized verify-then-append of ONE row (the only writer).

    Under one process-local lock the ledger is re-read and its invariants
    verified; a duplicate ``trial_key`` adds NO row (idempotent replay) and
    any schema violation writes NOTHING.  Returns an honest record
    ``{"attempted", "appended", "reasons", "trial_key"}``.
    """
    row = dict(entry)
    schema_reasons = validate_v12_row(row)
    if schema_reasons:
        raise ContractViolation(
            "v12_row_refused_by_schema:" + ";".join(schema_reasons)
        )
    key = str(row["trial_key"])
    target = Path(path)
    with _V12_LEDGER_LOCK:
        state = read_v12_ledger(target)
        existing_keys = {str(r["trial_key"]) for r in state["rows"]}
        if key in existing_keys:
            return {
                "attempted": True,
                "appended": False,
                "reasons": [REFUSED_TRIAL_KEY_ALREADY_PRESENT],
                "trial_key": key,
            }
        line = json.dumps(row, sort_keys=True, separators=(",", ":"), default=str)
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(line + "\n")
            handle.flush()
            import os

            os.fsync(handle.fileno())
        # Post-write re-verify: the file must still satisfy every invariant.
        after = read_v12_ledger(target)
        if after["count"] != state["count"] + 1:
            raise ContractViolation(
                "v12_ledger_append_changed_row_count_unexpectedly:"
                f"{state['count']}->{after['count']}"
            )
        return {
            "attempted": True,
            "appended": True,
            "reasons": [],
            "trial_key": key,
            "count_after": after["count"],
            "sha256_after": after["sha256"],
        }


# --------------------------------------------------------------------------- #
# Publication entry point for V12 drivers
# --------------------------------------------------------------------------- #
def publish_v12_cell(
    *,
    strategy_id: str,
    family: str,
    arm_id: str,
    arm_config_digest: str,
    stress_signature: Any,
    window_start_iso: str,
    window_end_iso: str,
    scored_metrics: Optional[Mapping[str, Any]],
    result_sha256: str = "",
    ledger_path: str | Path,
    family_contract_cells: Optional[Mapping[str, Mapping[str, Any]]] = None,
    producer_head_sha: str = "",
    required_fields: Sequence[str] = REQUIRED_SCORED_FIELDS,
) -> dict[str, Any]:
    """Exactly-once V12 publication of ONE computed cell.

    Gate order (first hit wins; every refusal appends ONE ``OBSERVATION``
    row -- observed +1, never publishable -- and an exact replay of the same
    ``trial_key`` adds no row and moves no counter):

    1. replay check (same trial already has a row of either type);
    2. family-contract cell guard (``REFUSED_CELL_OUTSIDE_FAMILY_CONTRACT``);
    3. pre-score metrics gate (flag + finite required fields);
    4. position evidence gate (``REFUSED_ZERO_POSITIONS`` /
       ``REFUSED_NO_VALID_DECISION_FILL`` -- L-V11-4).

    Returns an honest decision record with ``stage``, ``published``,
    ``reasons``, ``trial_key`` and the ``observation`` append outcome.
    """
    head = str(producer_head_sha or "").strip() or current_producer_head_sha()
    for name, value in (
        ("strategy_id", strategy_id),
        ("family", family),
        ("arm_id", arm_id),
        ("arm_config_digest", arm_config_digest),
        ("window_start_iso", window_start_iso),
        ("window_end_iso", window_end_iso),
    ):
        if not str(value or "").strip():
            raise ContractViolation(f"publish_v12_cell.{name} must be non-empty")

    key = v12_trial_key(
        strategy_id=strategy_id,
        family=family,
        arm_id=arm_id,
        arm_config_digest=arm_config_digest,
        stress_signature=stress_signature,
        window_start_iso=window_start_iso,
        window_end_iso=window_end_iso,
    )
    cell = canonical_cell_signature(stress_signature)
    cell_key = _sha256_text(_canonical_json(cell))

    record: dict[str, Any] = {
        "trial_key": key,
        "family": str(family),
        "arm_id": str(arm_id),
        "cell_key": cell_key,
        "published": False,
        "stage": "",
        "reasons": [],
        "observed_delta": 0,
        "published_delta": 0,
    }

    with _V12_LEDGER_LOCK:
        state = read_v12_ledger(ledger_path)
        record["ledger_count_before"] = state["count"]
        record["ledger_sha256_before"] = state["sha256"]
        existing_keys = {str(r["trial_key"]) for r in state["rows"]}
        if key in existing_keys:
            record.update(
                stage=STAGE_IDEMPOTENT_REPLAY,
                reasons=[REFUSED_TRIAL_KEY_ALREADY_PRESENT],
            )
            return record

        # -- family-contract cell guard (L-V11-1) --------------------------
        if family_contract_cells is not None:
            offenders = validate_family_contract_cells(
                family_contract_cells, [stress_signature]
            )
            if offenders:
                return _record_refusal(
                    record,
                    ledger_path=ledger_path,
                    reason=f"{REFUSED_CELL_OUTSIDE_FAMILY_CONTRACT}:{offenders[0]}",
                    head=head,
                )

        # -- pre-score metrics gate ----------------------------------------
        prescore_ok, prescore_reasons = validate_pre_score_metrics(
            scored_metrics, required_fields=required_fields
        )
        if not prescore_ok:
            return _record_refusal(
                record,
                ledger_path=ledger_path,
                reason=prescore_reasons[0],
                head=head,
                extra_reasons=prescore_reasons[1:],
            )

        # -- position evidence gate (L-V11-4) -------------------------------
        evidence_ok, evidence_reasons = validate_position_evidence(scored_metrics)
        if not evidence_ok:
            return _record_refusal(
                record,
                ledger_path=ledger_path,
                reason=evidence_reasons[0],
                head=head,
                extra_reasons=evidence_reasons[1:],
            )

        if not str(result_sha256 or "").strip():
            raise ContractViolation(
                "publish_v12_cell.result_sha256 must be non-empty for a "
                "publishable cell (no fabricated results)"
            )

        row = {
            "row_type": ROW_TYPE_CELL_RESULT,
            "trial_key": key,
            "arm_id": str(arm_id),
            "arm_config_digest": str(arm_config_digest),
            "family": str(family),
            "cell": cell,
            "result_sha256": str(result_sha256),
            "published_utc": _utc_now(),
            "producer_head_sha": head,
        }
        appended = append_v12_row(row, ledger_path)
        if not appended["appended"]:
            # Lost a serialization race: the trial already has a row, so the
            # honest outcome is an idempotent replay -- never a second row.
            record.update(
                stage=STAGE_IDEMPOTENT_REPLAY,
                reasons=list(appended["reasons"]),
            )
            return record
        record.update(
            stage=STAGE_PUBLISHED,
            published=True,
            published_delta=1,
            observed_delta=0,
            reasons=[],
        )
        return record


def _record_refusal(
    record: dict[str, Any],
    *,
    ledger_path: str | Path,
    reason: str,
    head: str,
    extra_reasons: Optional[Sequence[str]] = None,
) -> dict[str, Any]:
    """Record ONE computed-but-refused output as an OBSERVATION row.

    The refusal increments the OBSERVED denominator exactly once (a unique
    ``trial_key`` OBSERVATION row per the frozen schema) and can never
    publish: the row carries no publication fields at all.
    """
    reasons = [reason, *list(extra_reasons or [])]
    row = {
        "row_type": ROW_TYPE_OBSERVATION,
        "trial_key": record["trial_key"],
        "reason": reason,
        "observed_utc": _utc_now(),
        "producer_head_sha": head,
        "note": OBSERVATION_FROZEN_NOTE,
    }
    appended = append_v12_row(row, ledger_path)
    record.update(
        stage=STAGE_REFUSED,
        reasons=reasons,
        observed_delta=1 if appended["appended"] else 0,
        observation=appended,
    )
    return record


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# --------------------------------------------------------------------------- #
# Honest denominator view
# --------------------------------------------------------------------------- #
def v12_denominator_view(path: str | Path) -> dict[str, int]:
    """Honest V12 counter split over the ledger.

    ``published`` counts ``CELL_RESULT`` rows; ``observed`` counts
    ``OBSERVATION`` rows (distinct ``trial_key`` -- the ledger read refuses
    duplicates, so this equals the row count); ``observed_total`` is the
    scientific denominator every statistical consumer must use.
    """
    state = read_v12_ledger(path)
    published = sum(
        1 for r in state["rows"] if r.get("row_type") == ROW_TYPE_CELL_RESULT
    )
    observed = sum(
        1 for r in state["rows"] if r.get("row_type") == ROW_TYPE_OBSERVATION
    )
    return {
        "published": published,
        "observed": observed,
        "observed_total": published + observed,
        "rows": state["count"],
    }


__all__ = [
    "CELL_RESULT_REQUIRED_FIELDS",
    "DECISION_FILL_COUNT_FIELDS",
    "DECISION_FILL_RECORD_FIELDS",
    "LEDGER_PACKAGE_SCHEMA",
    "OBSERVATION_FROZEN_NOTE",
    "OBSERVATION_REQUIRED_FIELDS",
    "REFUSED_CELL_OUTSIDE_FAMILY_CONTRACT",
    "REFUSED_NO_VALID_DECISION_FILL",
    "REFUSED_POSITION_COUNT_ABSENT",
    "REFUSED_POSITION_COUNT_INVALID",
    "REFUSED_PRESCORE_FIELD_ABSENT",
    "REFUSED_PRESCORE_FIELD_NON_FINITE",
    "REFUSED_PRESCORE_FIELD_NOT_NUMERIC",
    "REFUSED_PRESCORE_FLAG_FALSE",
    "REFUSED_TRIAL_KEY_ALREADY_PRESENT",
    "REFUSED_ZERO_POSITIONS",
    "REQUIRED_SCORED_FIELDS",
    "ROW_TYPE_CELL_RESULT",
    "STAGE_IDEMPOTENT_REPLAY",
    "STAGE_PUBLISHED",
    "STAGE_REFUSED",
    "ROW_TYPE_OBSERVATION",
    "TRIAL_KEY_SCHEMA",
    "V12_ROW_TYPES",
    "append_v12_row",
    "canonical_cell_key",
    "canonical_cell_signature",
    "current_producer_head_sha",
    "enforce_family_contract_cells",
    "freeze_family_cell_contract",
    "publish_v12_cell",
    "read_v12_ledger",
    "validate_family_contract_cells",
    "validate_position_evidence",
    "validate_pre_score_metrics",
    "validate_v12_row",
    "v12_denominator_view",
    "v12_trial_key",
]
