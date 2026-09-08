"""Multi-vintage PIT fact semantics for the V6 fundamentals panel (P0a sibling).

STOCKS-FREE-V6 Phase P0a (PLAN_stocks_v6.md section 6 P0a).  The V5 canonical
bridge ``research/assets/stocks/pit_conditioning.py`` stays byte-identical:
its single-vintage aggregation (one effective date per sector per call, only
the filers holding a value at that exact date) is the measured root cause of
the F1 coverage collapse (V5 a9_f feasibility audit).  This sibling module
ADDS the remediated semantics without touching the canonical file:

- a fact observed at decision time ``t`` is the vintage whose availability
  stamp (SEC filed date, end of the filed UTC day) is the latest one strictly
  before the session gate - never the latest vintage in the store;
- an optional filing-age bound (``max_age_days``) drops filers whose newest
  usable vintage is stale, replacing the single-vintage "everyone must share
  one effective date" rule with a per-filer filing-clock rule: off-cycle
  fiscal calendars no longer eject a filer from the aggregate;
- coverage is reported per observation (covered filers / mapped filers) so
  the census can fund or refuse a conditioning clock from measured bytes.

No PnL, no trading logic and no parameter selection live here.  Nothing in
this module authorizes a data source.  Deterministic: same inputs, same
bytes; sorting is total and ``math.fsum`` is used for any aggregation.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from datetime import date, datetime, time, timedelta, timezone
import math
from typing import Iterable, Mapping, Sequence

__all__ = [
    "P0A_SCHEMA_VERSION",
    "EOD_TIME",
    "session_gate_utc",
    "stamp_is_eod_utc",
    "parse_iso_utc",
    "date_to_ord",
    "ord_to_date",
    "VintageStamp",
    "FilerFieldSeries",
    "AsOfObservation",
    "sector_asof_mix",
    "coverage_timeline",
    "LagStats",
    "lag_stats",
    "AGE_GRID_DAYS",
    "COVERAGE_FLOORS",
]

P0A_SCHEMA_VERSION = "stocks_free_v6_run/p0a_multivintage@1"

# SEC filed dates are date-only; the V5 store conservatively stamps
# availability at the end of the filed UTC day.  The panel fails closed if a
# stamp carries any other time-of-day, because date-resolution panels would
# silently shift the gate for such rows.
EOD_TIME = time(23, 59, 59, tzinfo=timezone.utc)

# Ex-ante age bounds evaluated by the census (documented before any run):
# quarterly-to-annual filing cadences plus generous staleness bounds.
AGE_GRID_DAYS: tuple[int | None, ...] = (120, 200, 400, 550, 800, None)

# Ex-ante coverage floors for "first date coverage crosses floor" reporting.
COVERAGE_FLOORS: tuple[float, ...] = (0.4, 0.6, 0.8)

_EPOCH = date(1970, 1, 1)


def session_gate_utc(decision_session: date) -> datetime:
    """Availability gate for a decision taken in ``decision_session``.

    Identical semantics to the canonical bridge: a record is usable iff its
    availability stamp is strictly before 00:00 UTC of the session date.
    """
    return datetime.combine(decision_session, time(0, 0, 0), tzinfo=timezone.utc)


def stamp_is_eod_utc(stamp: datetime) -> bool:
    """True iff the availability stamp is the end-of-day UTC sentinel."""
    return stamp.hour == 23 and stamp.minute == 59 and stamp.second == 59 and stamp.utcoffset() is not None and stamp.utcoffset().total_seconds() == 0


def parse_iso_utc(raw: str) -> datetime:
    value = datetime.fromisoformat(raw)
    if value.tzinfo is None:
        raise ValueError(f"timestamp must be timezone-aware: {raw!r}")
    if value.utcoffset().total_seconds() != 0:
        raise ValueError(f"timestamp must be UTC: {raw!r}")
    return value


def date_to_ord(day: date) -> int:
    return (day - _EPOCH).days


def ord_to_date(ordinal: int) -> date:
    return _EPOCH + timedelta(days=ordinal)


@dataclass(frozen=True, slots=True)
class VintageStamp:
    """One filed vintage of one logical fact (entity, field).

    ``available_ord`` is the day ordinal of the availability stamp (the SEC
    filed date at end of day).  ``effective_date`` is the fact's period end.
    ``value`` may be ``None`` for a non-numeric filed value; such stamps never
    count as coverage.
    """

    available_ord: int
    effective_date: date
    value: float | None


@dataclass(slots=True)
class FilerFieldSeries:
    """All filed vintages of one (entity, field) pair, sorted, append-only.

    The sort key is ``(available_ord, effective_date)`` and is total given the
    upstream sanitizer's duplicate handling; equal-key stamps must carry equal
    values or construction fails closed (mirrors the fusion core's
    AmbiguousVintageError discipline at panel resolution).
    """

    entity_id: str
    stamps: list[VintageStamp] = dc_field(default_factory=list)
    _sorted: bool = False
    rank_conflicts: int = 0

    def add(self, stamp: VintageStamp) -> None:
        self.stamps.append(stamp)
        self._sorted = False

    def finalize(self, *, strict: bool = True) -> "FilerFieldSeries":
        """Sort vintages and police same-rank conflicts.

        ``strict=True`` (value-level/aggregation use) fails closed on two
        distinct values sharing one PIT rank, mirroring the fusion core's
        AmbiguousVintageError discipline.  ``strict=False`` (coverage-census
        use) keeps both stamps, counts the conflict, and leaves the winner
        deterministic (stable sort in store order); coverage itself is
        invariant to which conflicting value wins.  The conflict count is
        surfaced by the caller - never dropped silently.
        """
        self.stamps.sort(key=lambda s: (s.available_ord, s.effective_date))
        conflicts = 0
        for left, right in zip(self.stamps, self.stamps[1:]):
            if (left.available_ord, left.effective_date) == (
                right.available_ord,
                right.effective_date,
            ) and left.value != right.value:
                conflicts += 1
        self.rank_conflicts = conflicts
        if strict and conflicts:
            raise ValueError(
                f"conflicting vintages share PIT rank for {self.entity_id} "
                f"({conflicts} conflict(s))"
            )
        self._sorted = True
        return self

    def observation_at(
        self, decision_session: date, *, max_age_days: int | None = None
    ) -> "AsOfObservation | None":
        """The PIT fact a decision at ``decision_session`` may observe.

        Picks the latest vintage whose availability stamp is strictly before
        the session gate and, when ``max_age_days`` is given, not older than
        the bound (``gate - max_age_days <= stamp < gate``).  Returns ``None``
        when no usable vintage exists - the filer is then explicitly not
        covered, never silently backfilled with a newer or older vintage.
        """
        if not self._sorted:
            self.finalize()
        gate_ord = date_to_ord(decision_session)
        # stamps sorted by available_ord; last one strictly below the gate
        lo, hi = 0, len(self.stamps)
        while lo < hi:
            mid = (lo + hi) // 2
            if self.stamps[mid].available_ord < gate_ord:
                lo = mid + 1
            else:
                hi = mid
        idx = lo - 1
        if idx < 0:
            return None
        stamp = self.stamps[idx]
        if max_age_days is not None and stamp.available_ord < gate_ord - max_age_days:
            return None
        return AsOfObservation(
            entity_id=self.entity_id,
            effective_date=stamp.effective_date,
            available_date=ord_to_date(stamp.available_ord),
            value=stamp.value,
            age_days=gate_ord - stamp.available_ord,
        )


@dataclass(frozen=True, slots=True)
class AsOfObservation:
    """The vintage a decision actually observed for one (entity, field)."""

    entity_id: str
    effective_date: date
    available_date: date
    value: float | None
    age_days: int


def sector_asof_mix(
    series_by_entity: Mapping[str, FilerFieldSeries],
    mapped_filers: Sequence[str],
    decision_session: date,
    *,
    max_age_days: int | None = None,
) -> tuple[int, int, int]:
    """Age-bounded multi-vintage coverage of one field over a filer set.

    Returns ``(filers_included, filers_mapped, numeric_included)`` where a
    filer is included iff it has any usable vintage under the gate and the
    age bound, and counted numeric only if that vintage's value is numeric.
    Unlike the canonical single-vintage aggregate, filers keep their OWN
    newest usable vintage; an off-cycle filer no longer ejects anyone.
    """
    included = 0
    numeric = 0
    for entity in sorted(mapped_filers):
        series = series_by_entity.get(entity)
        if series is None:
            continue
        observation = series.observation_at(decision_session, max_age_days=max_age_days)
        if observation is None:
            continue
        included += 1
        if observation.value is not None:
            numeric += 1
    return included, len(mapped_filers), numeric


def coverage_timeline(
    series_by_entity: Mapping[str, FilerFieldSeries],
    mapped_filers: Sequence[str],
    decision_sessions: Sequence[date],
    *,
    max_age_days: int | None = None,
) -> list[tuple[date, float]]:
    """Coverage fraction at every decision session, in session order."""
    timeline: list[tuple[date, float]] = []
    for session in decision_sessions:
        included, mapped, _ = sector_asof_mix(
            series_by_entity, mapped_filers, session, max_age_days=max_age_days
        )
        fraction = 0.0 if mapped == 0 else included / mapped
        timeline.append((session, fraction))
    return timeline


@dataclass(frozen=True, slots=True)
class LagStats:
    """Availability-lag distribution (available date minus effective date)."""

    n: int
    mean_days: float
    p50_days: int
    p75_days: int
    p90_days: int
    p95_days: int
    p99_days: int
    max_days: int
    min_days: int


def lag_stats(lags_days: Sequence[int]) -> LagStats | None:
    """Percentiles of the availability lag from raw integer day lags."""
    if not lags_days:
        return None
    ordered = sorted(lags_days)
    n = len(ordered)

    def pct(fraction: float) -> int:
        rank = min(n - 1, max(0, int(math.ceil(fraction * n)) - 1))
        return ordered[rank]

    return LagStats(
        n=n,
        mean_days=math.fsum(ordered) / n,
        p50_days=pct(0.50),
        p75_days=pct(0.75),
        p90_days=pct(0.90),
        p95_days=pct(0.95),
        p99_days=pct(0.99),
        max_days=ordered[-1],
        min_days=ordered[0],
    )


def first_cross_date(
    timeline: Sequence[tuple[date, float]], floor: float
) -> date | None:
    """First decision session whose coverage reaches ``floor`` (or None)."""
    for session, fraction in timeline:
        if fraction >= floor:
            return session
    return None
