"""V12P A4 -- pre-score target-book validator and schedule-only diagnostics.

Hard scope boundary (PLAN_crypto.md section 7, A4): this module computes NO
PnL, no returns and no scored metric of any kind.  Every output is a count,
a duration, an absolute-weight extremum or a verdict flag.

The validator runs BEFORE any scoring: given a schedule of decision stamps
and their target books, it validates EVERY stamp against the frozen adapter
contract (``DEFAULT_WEIGHT_CAP_MAX = 0.30``, never loosened here) and fails
closed with per-stamp reason codes.  Its only product is a feasibility
verdict payload -- never a capital path.

Cap semantics mirror :func:`research.adapter_v10.converters.normalise_target_book`
exactly (the frozen pre-score authority):

* a book breaches the cap iff ``abs(w) > cap_max + WEIGHT_TOL``;
* weights with ``|w| <= WEIGHT_TOL`` are flushed to ``0.0`` (not held);
* duplicate symbols and non-finite weights are refused.

Fail-closed rule: an empty stamp schedule can never produce a PASS; a stamp
with any failing check forces the schedule verdict to FAIL.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Optional, Sequence

from research.adapter_v10.protocol import (
    DEFAULT_WEIGHT_CAP_MAX,
    WEIGHT_TOL,
)

SCHEMA_VERSION = "v12.feasibility.a4.v1"
PRODUCER_ROLE = "A4"

DAY_NS = 86_400_000_000_000

#: Verdict vocabulary (cost_feasibility-compatible tokens).
VERDICT_PASS = "PASS"
VERDICT_FAIL = "FAIL"
VERDICT_UNAVAILABLE = "UNAVAILABLE_FAIL_CLOSED"

#: Per-stamp reason codes (fail-closed; ``REASON_OK`` is the only non-failure).
REASON_OK = "OK"
REASON_WEIGHT_NOT_FINITE = "WEIGHT_NOT_FINITE"
REASON_WEIGHT_ABOVE_CAP = "WEIGHT_ABS_ABOVE_FROZEN_CAP"
REASON_EMPTY_BOOK = "EMPTY_BOOK_CONTRACT_REQUIRES_NON_EMPTY"
REASON_DUPLICATE_SYMBOL = "DUPLICATE_SYMBOL"
REASON_BAD_SHAPE = "BAD_BOOK_SHAPE"
REASON_LEG_COUNT_MISMATCH = "LEG_COUNT_MISMATCH"

_HELD_TOL = WEIGHT_TOL


# --------------------------------------------------------------------------- #
# Book parsing (mirror of the adapter normalisation, as checks not raises)
# --------------------------------------------------------------------------- #
def _weights_mapping(body: Any) -> tuple[Optional[dict[str, float]], Optional[str]]:
    """``[[sym, w], ...]`` / ``{sym: w}`` -> mapping; refused shapes -> None."""
    if isinstance(body, Mapping):
        out: dict[str, float] = {}
        for sym, weight in body.items():
            key = str(sym)
            if key in out:
                return None, f"{REASON_DUPLICATE_SYMBOL}:{key}"
            try:
                out[key] = float(weight)
            except (TypeError, ValueError):
                return None, f"{REASON_BAD_SHAPE}:{key}"
        return out, None
    if isinstance(body, Sequence) and not isinstance(body, (str, bytes)):
        out = {}
        for entry in body:
            try:
                sym, weight = str(entry[0]), float(entry[1])
            except (TypeError, ValueError, IndexError):
                return None, REASON_BAD_SHAPE
            if sym in out:
                return None, f"{REASON_DUPLICATE_SYMBOL}:{sym}"
            out[sym] = weight
        return out, None
    return None, REASON_BAD_SHAPE


def _book_weights(record: Any) -> tuple[Optional[dict[str, float]], Optional[str]]:
    """Accept a repo-wide book payload (``weights`` body) or a bare mapping."""
    if isinstance(record, Mapping) and "weights" in record:
        return _weights_mapping(record["weights"])
    if isinstance(record, Mapping):
        bare = {key: value for key, value in record.items() if key not in ("status", "decision_ns")}
        if not bare:
            return {}, None
        return _weights_mapping(bare)
    return _weights_mapping(record)


# --------------------------------------------------------------------------- #
# Per-stamp validation
# --------------------------------------------------------------------------- #
def validate_target_book(
    record: Any,
    *,
    decision_ns: Optional[int] = None,
    cap_max: float = DEFAULT_WEIGHT_CAP_MAX,
    require_non_empty: bool = True,
    legs_per_side: Optional[int] = None,
) -> dict[str, Any]:
    """Validate ONE target book against the frozen adapter cap contract.

    Fail-closed per-stamp checks, in order: shape, duplicates, finiteness,
    cap, emptiness (when the contract requires a non-empty book) and -- when
    ``legs_per_side`` is declared -- the exact number of held names per side
    (the OILEV-V2 four-plus-four identity).  Returns a JSON-safe check
    payload; it NEVER contains a return, a cost or a PnL.
    """
    cap = float(cap_max)
    if cap <= 0.0:
        raise ValueError("cap_max must be positive")
    weights, error = _book_weights(record)
    reasons: list[str] = []
    if error is not None:
        reasons.append(error)
        weights = None

    max_abs = 0.0
    n_longs = n_shorts = 0
    if weights is not None:
        for sym, weight in weights.items():
            if not math.isfinite(weight):
                reasons.append(f"{REASON_WEIGHT_NOT_FINITE}:{sym}")
        if not reasons:
            held = {sym: w for sym, w in weights.items() if abs(w) > _HELD_TOL}
            for sym, weight in weights.items():
                if abs(weight) > cap + WEIGHT_TOL:
                    reasons.append(f"{REASON_WEIGHT_ABOVE_CAP}:{sym}")
            max_abs = max((abs(w) for w in held.values()), default=0.0)
            n_longs = sum(1 for w in held.values() if w > 0.0)
            n_shorts = sum(1 for w in held.values() if w < 0.0)
            if require_non_empty and not held:
                reasons.append(REASON_EMPTY_BOOK)
            if legs_per_side is not None and not reasons:
                if n_longs != int(legs_per_side) or n_shorts != int(legs_per_side):
                    reasons.append(f"{REASON_LEG_COUNT_MISMATCH}:{n_longs}L/{n_shorts}S")
    status = REASON_OK if (weights is not None and not reasons) else VERDICT_FAIL
    return {
        "decision_ns": None if decision_ns is None else int(decision_ns),
        "status": status,
        "reason_codes": reasons if reasons else [REASON_OK],
        "n_weights": 0 if weights is None else len(weights),
        "n_longs": n_longs,
        "n_shorts": n_shorts,
        "max_abs_weight": round(max_abs, 12),
        "cap_max": cap,
    }


# --------------------------------------------------------------------------- #
# Whole-schedule verdict
# --------------------------------------------------------------------------- #
def validate_stamp_schedule(
    records: Sequence[Any],
    *,
    cap_max: float = DEFAULT_WEIGHT_CAP_MAX,
    require_non_empty: bool = True,
    legs_per_side: Optional[int] = None,
) -> dict[str, Any]:
    """Validate EVERY stamp of a decision schedule; produce the verdict artifact.

    Fail-closed: zero stamps yields ``UNAVAILABLE_FAIL_CLOSED`` (an empty
    schedule can never infer a PASS); any failing stamp forces ``FAIL`` and
    the failing stamps are listed with their reason codes.  Counts only --
    no returns/PnL is ever computed or exposed.
    """
    per_stamp: list[dict[str, Any]] = []
    for index, record in enumerate(records):
        decision_ns = None
        if isinstance(record, Mapping):
            raw = record.get("decision_ns", record.get("stamp_ns"))
            if isinstance(raw, (int, float)) and math.isfinite(float(raw)):
                decision_ns = int(raw)
        per_stamp.append(
            validate_target_book(
                record,
                decision_ns=decision_ns,
                cap_max=cap_max,
                require_non_empty=require_non_empty,
                legs_per_side=legs_per_side,
            )
        )
    if not per_stamp:
        return {
            "schema": SCHEMA_VERSION,
            "producer_role": PRODUCER_ROLE,
            "verdict": VERDICT_UNAVAILABLE,
            "reason_code": "NO_STAMPS_PROVIDED",
            "n_stamps": 0,
            "n_pass": 0,
            "n_fail": 0,
            "failing_stamps": [],
        }
    failures = [
        {"index": index, **stamp}
        for index, stamp in enumerate(per_stamp)
        if stamp["status"] != REASON_OK
    ]
    verdict = VERDICT_PASS if not failures else VERDICT_FAIL
    return {
        "schema": SCHEMA_VERSION,
        "producer_role": PRODUCER_ROLE,
        "verdict": verdict,
        "cap_max": float(cap_max),
        "n_stamps": len(per_stamp),
        "n_pass": len(per_stamp) - len(failures),
        "n_fail": len(failures),
        "failing_stamps": failures,
        "per_stamp": per_stamp,
    }


# --------------------------------------------------------------------------- #
# Schedule-only diagnostics (counts / durations / turnover -- never PnL)
# --------------------------------------------------------------------------- #
def _stamp_weights(record: Any) -> dict[str, float]:
    weights, _error = _book_weights(record)
    return dict(weights or {})


def one_way_turnover(previous: Mapping[str, float], new: Mapping[str, float]) -> float:
    """Sum of absolute target deltas over the symbol union (one-way turnover)."""
    union = set(previous) | set(new)
    return math.fsum(abs(float(new.get(sym, 0.0)) - float(previous.get(sym, 0.0))) for sym in union)


def schedule_diagnostics(
    records: Sequence[Any],
    *,
    funding_events_by_symbol: Optional[Mapping[str, Sequence[int]]] = None,
) -> dict[str, Any]:
    """Schedule-only diagnostics for one book schedule: decision count,
    one-way turnover from target deltas, holding durations from target-book
    occupancy, and funding-event counts while held.

    No cost threshold is evaluated and no PnL/return is computed.  Funding
    events need the per-symbol settlement timestamps; without a local funding
    series the metric is ``UNAVAILABLE`` (fail-closed, never inferred) and the
    diagnostics verdict degrades to ``UNAVAILABLE_FAIL_CLOSED`` while the
    stamp feasibility verdict stays a separate, independent artifact.
    """
    if not records:
        return {
            "schema": SCHEMA_VERSION + ".diagnostics",
            "verdict": VERDICT_UNAVAILABLE,
            "reason_code": "NO_STAMPS_PROVIDED",
            "decision_count": 0,
        }
    stamp_weights = [_stamp_weights(record) for record in records]

    def _record_ns(record: Any, index: int) -> Optional[int]:
        if isinstance(record, Mapping):
            raw = record.get("decision_ns", record.get("stamp_ns"))
            if isinstance(raw, (int, float)) and not isinstance(raw, bool) and math.isfinite(float(raw)):
                return int(raw)
        return None

    decisions: list[Optional[int]] = [_record_ns(record, index) for index, record in enumerate(records)]
    have_ns = all(value is not None for value in decisions)

    turnover_total = 0.0
    per_step: list[float] = []
    for prev, new in zip(stamp_weights, stamp_weights[1:]):
        step = one_way_turnover(prev, new)
        per_step.append(round(step, 12))
        turnover_total += step

    durations_days: list[float] = []
    held_spans: list[dict[str, Any]] = []
    symbols = sorted({sym for weights in stamp_weights for sym in weights})
    for sym in symbols:
        run_start: Optional[int] = None
        for index, weights in enumerate(stamp_weights):
            held = abs(weights.get(sym, 0.0)) > _HELD_TOL
            if held and run_start is None:
                run_start = index
            if (not held or index == len(stamp_weights) - 1) and run_start is not None:
                run_end = index if held else index - 1
                if run_end > run_start and have_ns:
                    span_days = (
                        int(decisions[run_end]) - int(decisions[run_start])
                    ) / DAY_NS
                    durations_days.append(span_days)
                    held_spans.append(
                        {
                            "symbol": sym,
                            "start_index": run_start,
                            "end_index": run_end,
                            "duration_days": round(span_days, 12),
                        }
                    )
                run_start = None

    durations_days.sort()
    mid = len(durations_days) // 2
    median_days = (
        durations_days[mid]
        if len(durations_days) % 2
        else 0.5 * (durations_days[mid - 1] + durations_days[mid])
    ) if durations_days else None

    if funding_events_by_symbol is None:
        funding_block: dict[str, Any] = {
            "status": "UNAVAILABLE",
            "reason_code": "NO_LOCAL_FUNDING_SERIES",
            "events_while_held_total": None,
        }
        diagnostics_verdict = VERDICT_UNAVAILABLE
    elif not have_ns:
        funding_block = {
            "status": "UNAVAILABLE",
            "reason_code": "NO_DECISION_NS_IN_RECORDS",
            "events_while_held_total": None,
        }
        diagnostics_verdict = VERDICT_UNAVAILABLE
    else:
        events_total = 0
        for span in held_spans:
            window = funding_events_by_symbol.get(span["symbol"], ())
            events_total += sum(
                1
                for ts in window
                if int(decisions[span["start_index"]]) < int(ts) <= int(decisions[span["end_index"]])
            )
        funding_block = {
            "status": "OK",
            "reason_code": None,
            "events_while_held_total": int(events_total),
        }
        diagnostics_verdict = VERDICT_PASS

    if not have_ns:
        holdings_block: dict[str, Any] = {
            "status": "UNAVAILABLE",
            "reason_code": "NO_DECISION_NS_IN_RECORDS",
            "n_spans": 0,
            "median_holding_days": None,
            "min_holding_days": None,
            "max_holding_days": None,
            "spans": [],
        }
        diagnostics_verdict = VERDICT_UNAVAILABLE
    else:
        holdings_block = {
            "status": "OK",
            "reason_code": None,
            "n_spans": len(held_spans),
            "median_holding_days": None if median_days is None else round(median_days, 12),
            "min_holding_days": None if not durations_days else round(durations_days[0], 12),
            "max_holding_days": None if not durations_days else round(durations_days[-1], 12),
            "spans": held_spans,
        }

    gross_by_stamp = [round(math.fsum(abs(w) for w in weights.values()), 12) for weights in stamp_weights]
    return {
        "schema": SCHEMA_VERSION + ".diagnostics",
        "verdict": diagnostics_verdict,
        "decision_count": len(records),
        "one_way_turnover": {
            "total": round(turnover_total, 12),
            "per_step": per_step,
            "definition": "sum of |delta target weight| across consecutive decision stamps",
        },
        "holdings": holdings_block,
        "funding_events_while_held": funding_block,
        "gross_by_stamp": gross_by_stamp,
        "note": "schedule-only diagnostics; no cost threshold, no PnL, no returns",
    }
