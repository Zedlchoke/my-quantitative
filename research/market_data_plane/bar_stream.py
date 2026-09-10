"""mdp.market_bar@2 ordered stream: disjointness, order, no-lookahead (A4).

Freeze authority: research/control/market_data_plane_v2_run/architecture_freeze_v2.json
(p3_wave_sha 09a223f6ce166e219beb67b25b8151361979ca21), section
"bar_contract" (field_rules.interval_disjointness) and F4.

Responsibilities (all fail-closed, never quarantine):

* structural validation of every bar via :func:`market_data_plane.bars.validate_bar`;
* interval DISJOINTNESS per identity key
  ``(instrument_id, bar_type, interval_ns, adjustment_mode)``: duplicate or
  non-disjoint intervals raise :class:`BarIntervalError`
  (BAR_INTERVAL_DUPLICATE / BAR_INTERVAL_OVERLAP) — frozen field rule
  "fail closed at build/stream time ... not quarantine";
* stream ORDER per identity key: open_time must strictly increase;
* available-time NO-LOOKAHEAD gate per identity key: availability is
  monotonic non-decreasing in stream order — a later bar that is available
  earlier than an already-delivered bar means the stream carries evidence it
  could not have had at delivery time (IMPOSSIBLE_TIME_ORDER);
* gap accounting: missing bar slots between consecutive intervals are
  counted per key; a stream with missing slots reports
  ``completeness_status="GAPS_PRESENT"`` with sorted unique gap reasons.
  Gap reason code: ``SEQUENCE_GAP`` (reason_codes@1) — bar-interval
  contiguity is the bar-plane analog of @1 sequence contiguity; the frozen
  mdp.bar_reason_codes@2 extension set deliberately has no gap code and is
  not extended here.

Replay entry point ``replay_bars`` reuses the STRUCTURAL-CHECK SPIRIT of
replay.py (``_structural_event_check`` is private to that module and the
lane boundary forbids importing private symbols, so the bar-structural check
is :func:`bars.validate_bar` itself — the full frozen schema — plus the
toggleable named checks below, keeping replay.py's conventions: inputs are
recorded verbatim, nothing is discovered, nothing is deleted, digests are
taken over the exact canonical byte stream).

stdlib + sibling modules only; never mutates its inputs.
"""

from __future__ import annotations

import hashlib

from . import bars as _bars
from . import models as _models

__all__ = [
    "DEFAULT_CHECKS",
    "GAP_REASON_CODE",
    "normalize_bar_stream",
    "replay_bars",
]

#: Named structural checks replay_bars can toggle (order = execution order).
#: ``structural_validation`` (bars.validate_bar over every record) is always
#: enforced — it is the ingestion boundary, mirroring replay.py where the
#: structural event check is likewise non-optional.
DEFAULT_CHECKS: tuple[str, ...] = (
    "structural_validation",
    "ordering",
    "interval_disjointness",
    "availability_no_lookahead",
    "gap_accounting",
)

#: Gap reason code for missing bar slots (reason_codes@1, reused; the frozen
#: bar extension set has no gap code — see module docstring).
GAP_REASON_CODE = "SEQUENCE_GAP"

_TOGGABLE = frozenset(DEFAULT_CHECKS) - {"structural_validation"}


def _identity_key(bar: dict):
    return (bar["instrument_id"], bar["bar_type"], bar["interval_ns"],
            bar["adjustment_mode"])


def _normalize(bars, *, availability_rule, ordering: bool,
               disjointness: bool, availability_gate: bool,
               gap_accounting: bool) -> dict:
    canonical: list[dict] = []
    last: dict = {}
    gaps: list[dict] = []

    for raw in bars:
        bar = _bars.validate_bar(raw, availability_rule=availability_rule)
        key = _identity_key(bar)
        open_ns = bar["open_time_utc_ns"]
        available_ns = bar["available_time_utc_ns"]
        interval_ns = bar["interval_ns"]
        previous = last.get(key)
        if previous is not None:
            if disjointness and open_ns == previous["open"]:
                raise _bars.BarIntervalError(
                    "BAR_INTERVAL_DUPLICATE",
                    f"interval duplicate for identity {key}: open_time_utc_ns "
                    f"{open_ns} repeats the previous bar's interval start")
            if ordering and open_ns < previous["open"]:
                raise _bars.BarIntervalError(
                    "BAR_INTERVAL_OVERLAP",
                    f"stream order violation for identity {key}: open_time_utc_ns "
                    f"{open_ns} precedes the previous bar's interval start "
                    f"{previous['open']} (backwards delivery)")
            if disjointness and open_ns < previous["open"] + interval_ns:
                raise _bars.BarIntervalError(
                    "BAR_INTERVAL_OVERLAP",
                    f"non-disjoint intervals for identity {key}: open_time_utc_ns "
                    f"{open_ns} falls inside the previous interval "
                    f"[{previous['open']}, {previous['open'] + interval_ns})")
            if availability_gate and available_ns < previous["available"]:
                raise _bars.BarError(
                    "IMPOSSIBLE_TIME_ORDER",
                    f"no-lookahead violation for identity {key}: available_time_utc_ns "
                    f"{available_ns} precedes the previous bar's availability "
                    f"{previous['available']}; a delivered stream cannot carry "
                    f"earlier-availability evidence after a later one")
            if gap_accounting:
                missing = (open_ns - previous["open"]) // interval_ns - 1
                if missing > 0:
                    gaps.append({
                        "instrument_id": key[0],
                        "bar_type": key[1],
                        "interval_ns": key[2],
                        "adjustment_mode": key[3],
                        "missing_open_time_utc_ns": previous["open"] + interval_ns,
                        "missing_interval_count": missing,
                    })
        last[key] = {"open": open_ns, "available": available_ns}
        canonical.append(bar)

    gap_reasons = sorted({GAP_REASON_CODE}) if gaps else []
    stream_bytes = _models.stream_bytes(canonical)
    return {
        "bars": canonical,
        "bar_count": len(canonical),
        "completeness_status": ("GAPS_PRESENT" if gaps else "COMPLETE")
        if gap_accounting else None,
        "gap_reasons": gap_reasons if gap_accounting else [],
        "gaps": sorted(gaps, key=lambda g: (
            g["instrument_id"], g["bar_type"], g["interval_ns"],
            g["adjustment_mode"], g["missing_open_time_utc_ns"]),
        ) if gap_accounting else None,
        "stream_digest": hashlib.sha256(stream_bytes).hexdigest(),
        "stream_byte_length": len(stream_bytes),
    }


def normalize_bar_stream(bars, *, availability_rule=_bars.STRICT) -> dict:
    """Validate + order-check a bar stream; enforce interval disjointness.

    Returns a result dict: canonical ``bars`` (validated, input order
    preserved — the stream normalizer never reorders), ``bar_count``,
    ``completeness_status`` (COMPLETE / GAPS_PRESENT), sorted-unique
    ``gap_reasons``, per-key ``gaps`` records, and the canonical
    ``stream_digest``/``stream_byte_length``.  Any structural, ordering,
    disjointness or no-lookahead violation raises (fail closed) — nothing is
    quarantined, nothing is dropped.
    """
    return _normalize(
        bars, availability_rule=availability_rule, ordering=True,
        disjointness=True, availability_gate=True, gap_accounting=True)


def replay_bars(bars, checks=None, *, availability_rule=_bars.STRICT) -> dict:
    """Structural bar replay in the SPIRIT of replay.py (lane A4).

    ``checks`` is an optional mapping of check name (DEFAULT_CHECKS) to bool;
    unknown names raise, ``structural_validation=False`` raises (the
    structural check is the ingestion boundary and is always enforced).
    Disabled checks are skipped and recorded in ``checks_run`` /
    ``checks_disabled``; skipping ``gap_accounting`` leaves
    ``completeness_status`` as None (never a silent COMPLETE).

    Returns the normalize result plus verbatim ``checks`` recording — inputs
    are recorded, nothing is discovered, nothing is deleted, and the digest
    covers the exact canonical byte stream.
    """
    if checks is None:
        enabled = dict.fromkeys(DEFAULT_CHECKS, True)
    else:
        if not isinstance(checks, dict):
            raise ValueError("checks must be None or a dict of check name -> bool")
        unknown = sorted(set(checks) - set(DEFAULT_CHECKS))
        if unknown:
            raise ValueError(f"unknown check name(s): {unknown}")
        enabled = dict.fromkeys(DEFAULT_CHECKS, True)
        for name, value in checks.items():
            if not isinstance(value, bool):
                raise ValueError(f"check {name!r} must be a bool")
            enabled[name] = value
    if not enabled["structural_validation"]:
        raise ValueError("structural_validation cannot be disabled: "
                         "bars.validate_bar is the ingestion boundary")

    result = _normalize(
        bars,
        availability_rule=availability_rule,
        ordering=enabled["ordering"],
        disjointness=enabled["interval_disjointness"],
        availability_gate=enabled["availability_no_lookahead"],
        gap_accounting=enabled["gap_accounting"],
    )
    result["checks"] = dict(checks) if isinstance(checks, dict) else None
    result["checks_run"] = tuple(name for name in DEFAULT_CHECKS if enabled[name])
    result["checks_disabled"] = tuple(
        name for name in DEFAULT_CHECKS if not enabled[name])
    result["input_complete"] = True
    return result
