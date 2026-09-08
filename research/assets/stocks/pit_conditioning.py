"""PIT conditioning bridge between Data Fusion records and the stocks factory.

STOCKS-FREE-V5 Phase P0 adoption layer (PLAN_stocks_v5.md §6.P0).  The frozen
Data Fusion V1 core (``research/data_fusion`` at MULTISOURCE_DATA_CORE_SHA
c6a0576ef98dd4392e90805c8ba33821da62eabc) normalizes adopted free sources into
``NormalizedRecord`` rows with strict availability semantics.  This module is
the only sanctioned path from those rows to V5 conditioning inputs:

- the conditioning-lag rule (plan §6.P3): a fundamental or macro observation
  influences decisions no earlier than its availability stamp plus one
  session, implemented as ``available_time_utc < 00:00 UTC of the decision
  session`` — an availability stamp landing inside session S (SEC end-of-day
  stamps land at 23:59:59) first becomes usable the following session, and a
  stamp on a non-session day first becomes usable the next session after the
  last session preceding it;
- a decision at T can never read a row whose ``available_time_utc`` is at or
  after the decision gate (regression-pinned in
  ``tests/assets/stocks/test_pit_conditioning_adoption.py``);
- filer-level SEC facts aggregate to the frozen 11-sector ETF cohort level
  deterministically (sorted entity order, ``math.fsum``) and
  survivorship-aware: a filer that stops filing keeps contributing to as-of
  views before its last availability and is absent afterwards because no
  filing exists, never because the panel was silently trimmed — coverage
  counts report exactly who is in.

No PnL, no trading logic and no parameter selection live here; Phase P is
factory-only.  Nothing in this module authorizes a data source: authorization
dispositions are recorded by A3 in the run control directory.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
import math
from typing import Iterable, Mapping, Sequence

from research.data_fusion.models import NormalizedRecord
from research.data_fusion.pit import select_asof

SECTOR_UNIVERSE: tuple[str, ...] = (
    "XLB", "XLC", "XLE", "XLF", "XLI", "XLK", "XLP", "XLRE", "XLU", "XLV", "XLY",
)


def session_gate_utc(decision_session: date) -> datetime:
    """Availability gate for a decision taken in ``decision_session``.

    A record is usable for that session iff ``available_time_utc`` is strictly
    before 00:00 UTC of the session date (conditioning-lag rule: availability
    stamp plus one session).
    """
    return datetime.combine(decision_session, time(0, 0, 0), tzinfo=timezone.utc)


def usable_for_session(record: NormalizedRecord, decision_session: date) -> bool:
    """True iff the record satisfies the conditioning-lag gate for the session."""
    return record.available_time_utc < session_gate_utc(decision_session)


@dataclass(frozen=True, slots=True)
class SectorObservation:
    """One aggregated conditioning input at one decision session."""

    sector: str
    field: str
    effective_date: date
    decision_session: date
    value: float
    filers_included: int
    filers_mapped: int

    @property
    def coverage(self) -> float:
        if self.filers_mapped == 0:
            return 0.0
        return self.filers_included / self.filers_mapped


def _record_effective_date(record: NormalizedRecord) -> date:
    stamp = record.effective_time_utc or record.event_time_utc
    return stamp.date()


def aggregate_sector_asof(
    records: Iterable[NormalizedRecord],
    *,
    filer_sectors: Mapping[str, str],
    decision_session: date,
    field: str,
    max_filing_gap_days: int | None = None,
) -> dict[str, SectorObservation]:
    """Aggregate one filer-level field to every sector at one decision session.

    Deterministic and survivorship-aware:

    - only records already gated by ``usable_for_session`` semantics are
      selected via the fusion core's own ``select_asof`` (latest vintage whose
      availability beats the session gate; re-filed values supersede strictly
      after their own availability, never retroactively);
    - ``max_filing_gap_days`` (required for production conditioning; the
      default pure as-of mode exists only for fixture-level proofs) drops a
      filer whose latest usable filing for this field is older than the gap:
      a filer that stops filing therefore keeps contributing to as-of views
      while its filings stay fresh and drops out afterwards by an explicit,
      PIT-clean filing-clock rule — never by silent panel trimming.  Live
      filers that keep filing stay in.  Coverage reports both counts;
    - filers are visited in sorted ``entity_id`` order and summed with
      ``math.fsum``, so the result does not depend on input order;
    - the aggregate is single-vintage: it uses the latest effective date at
      which at least one participating filer has a gated record, and includes
      exactly the filers holding a selected value at that effective date;
    - ``None``-valued selections are skipped and counted as not included.
    """
    gate = session_gate_utc(decision_session)
    by_filer: dict[str, dict[date, list[NormalizedRecord]]] = {}
    for record in records:
        if record.field != field:
            continue
        effective = _record_effective_date(record)
        by_filer.setdefault(record.entity_id, {}).setdefault(effective, []).append(record)

    freshness_cutoff: datetime | None = None
    if max_filing_gap_days is not None:
        freshness_cutoff = gate - timedelta(days=max_filing_gap_days)

    observations: dict[str, SectorObservation] = {}
    for sector in SECTOR_UNIVERSE:
        sector_filers = sorted(
            entity for entity, tag in filer_sectors.items() if tag == sector
        )
        if not sector_filers:
            continue
        participating: list[str] = []
        for entity in sector_filers:
            filer_records = [r for rows in by_filer.get(entity, {}).values() for r in rows]
            usable = [r for r in filer_records if r.available_time_utc < gate]
            if not usable:
                continue
            if freshness_cutoff is not None:
                latest_available = max(r.available_time_utc for r in usable)
                if latest_available < freshness_cutoff:
                    continue
            participating.append(entity)
        # one effective date per sector per call: the latest effective date at
        # which at least one participating filer has a gated record
        effective_dates = sorted(
            {
                effective
                for entity in participating
                for effective in by_filer.get(entity, ())
            },
            reverse=True,
        )
        for effective in effective_dates:
            included: list[float] = []
            for entity in participating:
                selected = select_asof(
                    by_filer.get(entity, {}).get(effective, ()),
                    gate,
                )
                if selected is not None and selected.value is not None:
                    if isinstance(selected.value, (int, float)) and not isinstance(
                        selected.value, bool
                    ):
                        included.append(float(selected.value))
            if included:
                observations[sector] = SectorObservation(
                    sector=sector,
                    field=field,
                    effective_date=effective,
                    decision_session=decision_session,
                    value=math.fsum(included) / len(included),
                    filers_included=len(included),
                    filers_mapped=len(sector_filers),
                )
                break
    return observations


def conditioning_panel(
    records: Iterable[NormalizedRecord],
    *,
    filer_sectors: Mapping[str, str],
    sessions: Sequence[date],
    field: str,
    max_filing_gap_days: int | None = None,
) -> dict[date, dict[str, SectorObservation]]:
    """Build the PIT conditioning panel for every session in ``sessions``.

    The panel is the sequence of per-session sector aggregates; sessions must
    be the frozen SPY session calendar slice authorized by A3.  A decision at
    session S only ever sees rows gated by ``session_gate_utc(S)`` — the
    regression test pins this by mutation: any row with a later availability
    stamp must be invisible.
    """
    materialized = tuple(records)
    panel: dict[date, dict[str, SectorObservation]] = {}
    for session in sessions:
        panel[session] = aggregate_sector_asof(
            materialized,
            filer_sectors=filer_sectors,
            decision_session=session,
            field=field,
            max_filing_gap_days=max_filing_gap_days,
        )
    return panel
