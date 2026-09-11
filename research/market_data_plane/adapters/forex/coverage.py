"""Forex adapter coverage diagnostics — expected vs unexplained gaps (A6).

Freeze authority: research/control/market_data_plane_v2_run/architecture_freeze_v2.json
(p3_wave_sha 09a223f6ce166e219beb67b25b8151361979ca21), section
``"adapters" -> "forex"`` (clock): "session/weekend gaps classified EXPECTED,
distinguished from unexplained missing data"; DST-shift artifacts (a local
hour that appears twice / vanishes at a fall-back/spring-forward boundary)
must be CLASSIFIED — never silently accepted and never mistaken for either
plain missing data or a legitimate closure.

Gap classifications (:class:`CoverageReport.gaps`):

* ``EXPECTED_CLOSED_MARKET`` — missing slot inside the frozen weekly closure
  (Fri 21:00Z -> Sun 21:00Z by default; the context session rule decides);
* ``DST_SHIFT_ARTIFACT`` — missing slot correlated (within one interval of
  either fold interpretation) with a quarantined ambiguous/imaginary
  local-time record at a DST boundary.  Classified AND counted against
  completeness: an artifact is provider clock damage, never silently
  accepted, never re-stamped as data;
* ``UNEXPLAINED`` — missing slot inside an open session with no DST
  evidence: genuinely missing data.

Coverage completeness: ``COMPLETE`` only when there are zero UNEXPLAINED and
zero DST_SHIFT_ARTIFACT slots.  Expected closure gaps do not degrade
completeness (they are the calendar, not missing data) but are still counted
and listed.

stdlib + sibling modules only; never mutates its inputs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from market_data_plane import bars as _bars

from .adapter import AdapterResult
from .context import AdapterContext, ForexAdapterError, local_wall_fold_candidates_ns

__all__ = [
    "EXPECTED_CLOSED_MARKET",
    "GAPS_PRESENT",
    "COMPLETE",
    "DST_SHIFT_ARTIFACT",
    "UNEXPLAINED",
    "GAP_CLASSIFICATIONS",
    "GapRecord",
    "CoverageReport",
    "check_coverage",
]

#: Gap classification constants (frozen A6 vocabulary).
EXPECTED_CLOSED_MARKET = "EXPECTED_CLOSED_MARKET"
DST_SHIFT_ARTIFACT = "DST_SHIFT_ARTIFACT"
UNEXPLAINED = "UNEXPLAINED"
GAP_CLASSIFICATIONS: tuple[str, ...] = (
    EXPECTED_CLOSED_MARKET, DST_SHIFT_ARTIFACT, UNEXPLAINED,
)

#: Coverage completeness statuses (bar-stream vocabulary; classified here).
COMPLETE = "COMPLETE"
GAPS_PRESENT = "GAPS_PRESENT"

#: Quarantine reason codes that carry DST-boundary evidence for correlation.
_DST_QUARANTINE_CODES = frozenset({
    "FOREX_AMBIGUOUS_LOCAL_TIME",
    "FOREX_IMAGINARY_LOCAL_TIME",
})


@dataclass(frozen=True)
class GapRecord:
    """One missing expected slot with its classification + evidence."""

    open_time_utc_ns: int
    classification: str
    evidence: str


@dataclass(frozen=True)
class CoverageReport:
    """Asset-calendar coverage census over one normalized forex stream."""

    instrument_ids: tuple[str, ...]
    window_open_time_utc_ns: Optional[int]
    window_close_time_utc_ns: Optional[int]
    expected_slot_count: int
    observed_slot_count: int
    missing_slot_count: int
    expected_closed_market_count: int
    dst_shift_artifact_count: int
    unexplained_count: int
    gaps: tuple[GapRecord, ...]
    coverage_reasons: tuple[str, ...]
    completeness_status: str

    def as_dict(self) -> dict:
        return {
            "instrument_ids": list(self.instrument_ids),
            "window_open_time_utc_ns": self.window_open_time_utc_ns,
            "window_close_time_utc_ns": self.window_close_time_utc_ns,
            "expected_slot_count": self.expected_slot_count,
            "observed_slot_count": self.observed_slot_count,
            "missing_slot_count": self.missing_slot_count,
            "expected_closed_market_count": self.expected_closed_market_count,
            "dst_shift_artifact_count": self.dst_shift_artifact_count,
            "unexplained_count": self.unexplained_count,
            "gaps": [vars(gap) for gap in self.gaps],
            "coverage_reasons": list(self.coverage_reasons),
            "completeness_status": self.completeness_status,
        }


def _dst_candidates_ns(result: AdapterResult, context: AdapterContext) -> list[int]:
    """UTC-ns candidates from quarantined DST-boundary records.

    Both fold interpretations of each rejected ambiguous/imaginary local
    time are candidate instants for the slot it would have covered.  The
    records stay quarantined — correlation classifies the hole, it never
    re-admits the record.
    """
    from .context import load_provider_timezone

    candidates: list[int] = []
    for entry in result.quarantined:
        if entry.get("reason_code") not in _DST_QUARANTINE_CODES:
            continue
        record = entry.get("raw_record")
        if not isinstance(record, dict):
            continue
        ts = record.get("ts")
        if not isinstance(ts, str):
            continue
        tz_name = record.get("tz")
        if tz_name != context.provider_timezone:
            continue  # clock-mismatch records make no DST claim here
        try:
            candidates.extend(
                local_wall_fold_candidates_ns(ts, load_provider_timezone(tz_name)))
        except (ForexAdapterError, ValueError):
            continue
    return candidates


def check_coverage(result: AdapterResult, context: AdapterContext) -> CoverageReport:
    """Classify every missing expected slot of the normalized stream.

    Expected slots run on the ``context.interval_ns`` UTC grid from the first
    bar's open to the last bar's open + interval.  Fail closed on a
    non-:class:`AdapterResult` first argument.
    """
    if not isinstance(result, AdapterResult):
        raise _bars.BarError(
            "MALFORMED_SHAPE",
            f"check_coverage expects an AdapterResult, got {type(result).__name__}")

    instrument_ids = tuple(sorted({bar["instrument_id"] for bar in result.bars}))
    if not result.bars:
        return CoverageReport(
            instrument_ids=instrument_ids,
            window_open_time_utc_ns=None, window_close_time_utc_ns=None,
            expected_slot_count=0, observed_slot_count=0, missing_slot_count=0,
            expected_closed_market_count=0, dst_shift_artifact_count=0,
            unexplained_count=0, gaps=(), coverage_reasons=(),
            completeness_status=COMPLETE)

    interval_ns = context.interval_ns
    window_open = result.bars[0]["open_time_utc_ns"]
    window_close = result.bars[-1]["open_time_utc_ns"] + interval_ns
    observed = {bar["open_time_utc_ns"] for bar in result.bars}
    dst_candidates = _dst_candidates_ns(result, context)

    gaps: list[GapRecord] = []
    counts = {EXPECTED_CLOSED_MARKET: 0, DST_SHIFT_ARTIFACT: 0, UNEXPLAINED: 0}
    for slot in range(window_open, window_close, interval_ns):
        if slot in observed:
            continue
        if context.is_session_closed(slot):
            counts[EXPECTED_CLOSED_MARKET] += 1
            gaps.append(GapRecord(
                open_time_utc_ns=slot, classification=EXPECTED_CLOSED_MARKET,
                evidence="slot opens inside the frozen weekly session closure"))
            continue
        near = [c for c in dst_candidates
                if slot - interval_ns < c < slot + 2 * interval_ns]
        if near:
            counts[DST_SHIFT_ARTIFACT] += 1
            gaps.append(GapRecord(
                open_time_utc_ns=slot, classification=DST_SHIFT_ARTIFACT,
                evidence="missing slot at a DST boundary; correlated with "
                         f"{len(near)} quarantined ambiguous/imaginary local-time "
                         f"record candidate instant(s)"))
            continue
        counts[UNEXPLAINED] += 1
        gaps.append(GapRecord(
            open_time_utc_ns=slot, classification=UNEXPLAINED,
            evidence="missing slot inside an open session; no closure or DST "
                     "evidence explains it"))

    completeness = GAPS_PRESENT if (counts[UNEXPLAINED] or counts[DST_SHIFT_ARTIFACT]) \
        else COMPLETE
    return CoverageReport(
        instrument_ids=instrument_ids,
        window_open_time_utc_ns=window_open,
        window_close_time_utc_ns=window_close,
        expected_slot_count=(window_close - window_open) // interval_ns,
        observed_slot_count=len(result.bars),
        missing_slot_count=len(gaps),
        expected_closed_market_count=counts[EXPECTED_CLOSED_MARKET],
        dst_shift_artifact_count=counts[DST_SHIFT_ARTIFACT],
        unexplained_count=counts[UNEXPLAINED],
        gaps=tuple(gaps),
        coverage_reasons=tuple(
            c for c in GAP_CLASSIFICATIONS if counts[c]),
        completeness_status=completeness,
    )
