"""FOREX-NG2 revision-event builder: first-to-second-vintage gap events.

Plan FOREX-NG2 section 4 (the frontier), frozen semantics:

    Revision surprise R(m, v2) = I_v2(m) / I_v1(m) - 1

For EVERY reference month m carried by a vintaged CPI archive:

- v1 = the first vintage that published m (earliest realtime_start with a
  non-missing value);
- v2 = the immediately following vintage of m (next distinct realtime_start);
- a REVISION EVENT exists for m iff I_v2(m) != I_v1(m) AND v2 carries
  available-time evidence (a realtime window [realtime_start,
  realtime_end] on both vintages -- the channel's availability law).

Fail-closed structural law (canary P-7 companion):

- STRICT vintage monotonicity -- consecutive vintages of the same month
  must have strictly increasing realtime_start (a duplicate or backwards
  realtime_start raises VintageMonotonicityError and NOTHING is built).
  The single disclosed relaxation: BYTE-IDENTICAL duplicate rows (same
  obs_date + realtime window + value, an ingest artifact measured 481x
  in the US realtime archive) are removed first by dedupe_exact_rows;
  CONFLICTING same-realtime_start rows (different value/window, a
  genuine same-day correction) still raise -- fail-closed, the month is
  unmeasurable rather than guessed;
- fabricated months must FAIL lookup (found=False, never an inferred
  event).

Usability law (plan section 5 floor basis): an event is USABLE on the
16:00-NY daily grid when its PIT instant -- the v2 availability day
(v2.realtime_start; date-only evidence, conservative same-day end in the
consumers) -- falls inside the S0 window.  Events outside the window are
counted in the all-events column but never toward a floor.

AU/NZ quarterly legs (disclosed lag mapping, inherited ng1 identity
interpretation): reference periods are represented at the quarter FIRST
month (V9 law, quarter_first_month_from_end); vintages arrive
quarterly-ish (measured cadence recorded by the census), so the
first-to-second-vintage gap for AU/NZ is a quarter-over-quarter vintage
gap measured on quarter-first-month keys; monthly legs (GB/CA) key on
calendar months.  Cross-economy differential joins use the month key as
is (a quarterly leg contributes only its quarter-first months).

US leg: fred_cpiaucsl_rt realtime archive.  MEASURED (P0, this cycle):
the archive is NOT a structural zero -- it carries small-magnitude
first-to-second-vintage index-level updates clustered on archive
re-pull days (see the census legs.US block).  US is the quote leg of
every funded pair (no own pair): measured and disclosed, never
floor-anchored.

NO PnL, NO outcome, NO scoring anywhere in this module (P0 census law).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from research.assets.forex_ng1.plane_adapter import FRED_MISSING, VintageRow

#: NG2 S0 window (ng1 measured S0 window, inherited; grid 1842 days).
S0_WINDOW = ("2018-04-04", "2025-04-30")

#: Plan section 5 frozen floors (BLOCKED_DATA if not evidenced).
OWN_ECONOMY_FLOOR = 30
CROSS_ECONOMY_FLOOR = 12

#: Q-6 recent-window law: the last 24 calendar months of the S0 window.
RECENT_WINDOW_MONTHS = 24

#: Monthly MINMEI realtime legs (96-vintage class).
ECONOMIES_MONTHLY = ("GB", "CA")
#: Quarterly vintaged legs (quarter-first-month representation).
ECONOMIES_QUARTERLY = ("AU", "NZ")
#: US realtime leg (quote leg; measured, never floor-anchored).
ECONOMY_US = "US"

#: The four funded pair-anchor economies (own-economy lane A4 anchors:
#: GB->GBPUSD, CA->USDCAD, AU->AUDUSD, NZ->NZDUSD).  US is the quote leg
#: of every funded pair and has no own pair; it is measured and
#: disclosed, never floor-anchored.
PAIR_ANCHOR_ECONOMIES = ("GB", "CA", "AU", "NZ")

#: AU/NZ lag mapping disclosure (ng1 disclosed identity interpretation,
#: inherited): the quarterly reference period is keyed at its FIRST month
#: and the print lags the quarter end by roughly one quarter; the
#: revision event's PIT instant is the v2 realtime_start of the NEXT
#: quarter-ish vintage, not a monthly anniversary.
QUARTERLY_LAG_MAPPING = {
    "AU": ("AUSCPIALLQINMEI quarterly vintaged feed; reference month = "
           "quarter first month (V9 law); vintages arrive ~quarterly "
           "(15th-ish of Feb/May/Aug/Nov + occasional extra pulls); "
           "revision = quarter-over-quarter vintage gap on "
           "quarter-first-month keys"),
    "NZ": ("NZLCPIALLQINMEI quarterly vintaged feed; reference month = "
           "quarter first month (V9 law); vintages arrive ~quarterly; "
           "revision = quarter-over-quarter vintage gap on "
           "quarter-first-month keys"),
}


class RevisionStructureError(Exception):
    """Fail-closed base: nothing is built on a malformed revision shape."""


class VintageMonotonicityError(RevisionStructureError):
    """v2.realtime > v1.realtime STRICT violated for some month."""


@dataclass(frozen=True)
class RevisionEvent:
    """One first-to-second-vintage revision event (descriptive only)."""

    economy: str
    obs_month: str            # "2025-03-01" (quarter-first month for AU/NZ)
    v1_realtime_start: str
    v1_realtime_end: str
    v1_value: str
    v2_realtime_start: str    # the event's PIT availability day
    v2_realtime_end: str
    v2_value: str
    ratio: float              # I_v2 / I_v1 - 1
    first_print_in_realtime_era: bool   # m >= feed's first realtime vintage

    @property
    def month_key(self) -> str:
        return self.obs_month[:7]

    @property
    def event_year(self) -> str:
        return self.v2_realtime_start[:4]


def dedupe_exact_rows(rows: Sequence[VintageRow]) -> tuple[list[VintageRow],
                                                           int]:
    """Remove BYTE-IDENTICAL duplicate vintage rows (an ingest artifact).

    The pinned US realtime archive (fred_cpiaucsl_rt) double-lists its
    final vintage for 106 months / 481 rows: two rows with the SAME
    (obs_date, realtime_start, realtime_end, value).  Identical rows
    carry zero ambiguity -- the vintage is the same -- so removing the
    literal duplicate is a disclosed de-duplication, never a guess.

    This is the ONLY relaxation of the strict law, and it is narrow:
    CONFLICTING rows (same realtime_start, different window or value)
    are NOT touched here and still raise VintageMonotonicityError
    downstream (a same-day correction is genuine ambiguity -> fail
    closed, month unmeasurable).  Returns (deduped_rows, removed_count).
    """
    seen: set[tuple[str, str, str, str]] = set()
    out: list[VintageRow] = []
    removed = 0
    for r in rows:
        key = (r.obs_date, r.realtime_start, r.realtime_end, r.value)
        if key in seen:
            removed += 1
            continue
        seen.add(key)
        out.append(r)
    return out, removed


def _parse_positive(value: str, economy: str, obs_month: str) -> float:
    try:
        x = float(value)
    except ValueError as exc:
        raise RevisionStructureError(
            f"{economy} {obs_month}: unparseable index value {value!r}"
        ) from exc
    if not x > 0.0:
        raise RevisionStructureError(
            f"{economy} {obs_month}: non-positive index value {value!r} "
            "(ratio undefined): fail-closed")
    return x


def vintages_by_month(rows: Sequence[VintageRow]) -> dict[str, list[VintageRow]]:
    """Group non-missing vintages by obs month, STRICT monotonicity-checked.

    Fail-closed: consecutive vintages of the same month must carry
    strictly increasing realtime_start.  A duplicate or unordered
    realtime_start raises VintageMonotonicityError and nothing is
    returned for the caller to mis-measure.
    """
    by_month: dict[str, list[VintageRow]] = {}
    for r in rows:
        if r.value == FRED_MISSING:
            continue
        by_month.setdefault(r.obs_date, []).append(r)
    for month, vintages in by_month.items():
        vintages.sort(key=lambda r: (r.realtime_start, r.realtime_end, r.value))
        for a, b in zip(vintages, vintages[1:]):
            if not b.realtime_start > a.realtime_start:
                raise VintageMonotonicityError(
                    f"month {month}: vintage realtime_start not strictly "
                    f"increasing ({a.realtime_start} -> {b.realtime_start}): "
                    "v2.realtime > v1.realtime STRICT violated; "
                    "fail-closed, no events built")
    return by_month


def realtime_era_start(rows: Sequence[VintageRow]) -> str:
    """Earliest realtime_start in the feed (the archive's own clock zero).

    Months with obs_date < this are BACKFILLED history: their "first
    vintage" is a history ingest, not a genuine first print.  The census
    counts them per the frozen literal definition but flags
    first_print_in_realtime_era=False so downstream lanes see the split.
    """
    return min(r.realtime_start for r in rows)


def build_revision_events(economy: str,
                          rows: Sequence[VintageRow]) -> dict:
    """Build all revision events for one economy (no window filter).

    Returns counts plus the event list; every event carries full
    availability evidence (both realtime windows), the v1->v2 value gap,
    the ratio R = I_v2/I_v1 - 1, and the first-print-era flag.
    """
    by_month = vintages_by_month(rows)   # raises on monotonicity violation
    era_start = realtime_era_start(rows)
    events: list[RevisionEvent] = []
    months_with_v2 = 0
    for month in sorted(by_month):
        vintages = by_month[month]
        if len(vintages) < 2:
            continue
        months_with_v2 += 1
        v1, v2 = vintages[0], vintages[1]
        if v1.value == v2.value:
            continue
        if not (v1.realtime_start and v1.realtime_end
                and v2.realtime_start and v2.realtime_end):
            # available-time evidence missing for one of the vintages:
            # not a usable revision event under the channel law
            continue
        i1 = _parse_positive(v1.value, economy, month)
        i2 = _parse_positive(v2.value, economy, month)
        events.append(RevisionEvent(
            economy=economy,
            obs_month=month,
            v1_realtime_start=v1.realtime_start,
            v1_realtime_end=v1.realtime_end,
            v1_value=v1.value,
            v2_realtime_start=v2.realtime_start,
            v2_realtime_end=v2.realtime_end,
            v2_value=v2.value,
            ratio=i2 / i1 - 1.0,
            first_print_in_realtime_era=month >= era_start,
        ))
    return {
        "economy": economy,
        "months_carried": len(by_month),
        "months_with_second_vintage": months_with_v2,
        "events_all": events,
        "events_all_count": len(events),
    }


def usable_events(events: Iterable[RevisionEvent],
                  window: tuple[str, str] = S0_WINDOW,
                  ) -> list[RevisionEvent]:
    """Events whose v2 availability day falls inside the S0 window.

    These are the events a 16:00-NY grid decision inside the window
    could condition on (PIT at v2.realtime_start; date-only evidence,
    conservative).  Events outside the window are real transitions but
    not usable on this cycle's grid and NEVER count toward a floor.
    """
    lo, hi = window
    return [e for e in events if lo <= e.v2_realtime_start <= hi]


def recent_window_bounds(window: tuple[str, str] = S0_WINDOW,
                         months: int = RECENT_WINDOW_MONTHS,
                         ) -> tuple[str, str]:
    """The last ``months`` calendar months of the window (Q-6 law).

    Window end 2025-04-30 -> recent window 2023-05-01..2025-04-30
    (exactly 24 calendar months), matched against v2 availability days.
    """
    lo, hi = window
    y, m = int(hi[:4]), int(hi[5:7])
    m -= months - 1
    while m <= 0:
        m += 12
        y -= 1
    return (f"{y:04d}-{m:02d}-01", hi)


def cross_economy_differential_months(
        usable_by_economy: Mapping[str, Sequence[RevisionEvent]],
        ) -> dict:
    """Months on which >= 2 economies carry a (usable) revision event.

    Join key: the obs month key (quarterly legs contribute their
    quarter-first months only).  Returns the sorted month list with the
    contributing economies per month and the total (the cross-economy
    differential floor basis).
    """
    months: dict[str, list[str]] = {}
    for economy in sorted(usable_by_economy):
        seen: set[str] = set()
        for e in usable_by_economy[economy]:
            if e.month_key not in seen:
                seen.add(e.month_key)
                months.setdefault(e.month_key, []).append(economy)
    differential = {m: ecos for m, ecos in months.items() if len(ecos) >= 2}
    return {
        "months": differential,
        "sorted_month_keys": sorted(differential),
        "total": len(differential),
        "join_key_law": "obs month key (quarter-first month for AU/NZ); "
                        "event membership keyed by usable-in-window events",
    }


def magnitude_distribution(events: Sequence[RevisionEvent]) -> dict:
    """Descriptive revision-magnitude distribution (percent, no outcome).

    Median / quartiles / extremes of R = I_v2/I_v1 - 1, plus the same
    for |R|.  Descriptive only: nothing here feeds any decision rule.
    """
    if not events:
        return {"n": 0, "note": "no events: distribution undefined"}
    xs = sorted(e.ratio for e in events)

    def _q(sorted_xs: Sequence[float], q: float) -> float:
        # linear interpolation on positions (numpy default), no deps
        pos = q * (len(sorted_xs) - 1)
        lo_i = int(pos)
        hi_i = min(lo_i + 1, len(sorted_xs) - 1)
        frac = pos - lo_i
        return sorted_xs[lo_i] * (1.0 - frac) + sorted_xs[hi_i] * frac

    return {
        "n": len(xs),
        "median_pct": round(100.0 * _q(xs, 0.5), 6),
        "q1_pct": round(100.0 * _q(xs, 0.25), 6),
        "q3_pct": round(100.0 * _q(xs, 0.75), 6),
        "min_pct": round(100.0 * xs[0], 6),
        "max_pct": round(100.0 * xs[-1], 6),
        "abs_median_pct": round(100.0 * _q(sorted(abs(x) for x in xs), 0.5),
                                6),
        "law": "descriptive only (plan section 5 P0 (d)); no outcome, no "
               "threshold, no decision use",
    }


def events_by_year(events: Sequence[RevisionEvent]) -> dict:
    """Distribution of events by PIT availability year (v2 realtime)."""
    out: dict[str, int] = {}
    for e in events:
        out[e.event_year] = out.get(e.event_year, 0) + 1
    return dict(sorted(out.items()))


def lookup_event(events_by_economy: Mapping[str, Sequence[RevisionEvent]],
                 economy: str, obs_month: str) -> dict:
    """Canary-capable exact lookup by (economy, obs month).

    A fabricated month (not carried by the realtime archive) MUST come
    back found=False -- never an inferred or neighboring event.
    """
    hits = [e for e in events_by_economy.get(economy, ())
            if e.obs_month == obs_month]
    return {
        "economy": economy,
        "obs_month": obs_month,
        "found": bool(hits),
        "event_count": len(hits),
    }


def evaluate_floors(usable_counts_by_economy: Mapping[str, int],
                    cross_differential_total: int,
                    own_floor: int = OWN_ECONOMY_FLOOR,
                    cross_floor: int = CROSS_ECONOMY_FLOOR,
                    anchor_economies: Sequence[str] = PAIR_ANCHOR_ECONOMIES,
                    ) -> dict:
    """Compare measured usable counts against the frozen floors.

    The own-economy floor is evaluated for EVERY pair-anchor economy
    (frozen before measurement; a single shortfall is a shortfall -- no
    post-hoc economy exclusion, no floor renegotiation).  Non-anchor
    economies (US: quote leg, structural no-revision archive) are
    recorded but never floor-anchored.
    """
    rows = {}
    for eco in anchor_economies:
        n = usable_counts_by_economy.get(eco, 0)
        rows[eco] = {
            "usable_events": n,
            "floor": own_floor,
            "margin": n - own_floor,
            "verdict": "PASS" if n >= own_floor else "FAIL",
        }
    cross = {
        "differential_months": cross_differential_total,
        "floor": cross_floor,
        "margin": cross_differential_total - cross_floor,
        "verdict": ("PASS" if cross_differential_total >= cross_floor
                    else "FAIL"),
    }
    non_anchor = {
        eco: {"usable_events": usable_counts_by_economy.get(eco, 0),
              "role": "quote leg (no own pair to trade against itself); "
                      "measured and disclosed, not floor-anchored"}
        for eco in usable_counts_by_economy
        if eco not in anchor_economies}
    all_pass = (all(r["verdict"] == "PASS" for r in rows.values())
                and cross["verdict"] == "PASS")
    return {
        "own_economy": rows,
        "own_economy_all_pass": all(r["verdict"] == "PASS"
                                    for r in rows.values()),
        "cross_economy": cross,
        "non_anchor_economies": non_anchor,
        "verdict": "PASS" if all_pass else "FAIL",
        "law": "plan section 5 frozen floors: >=30 usable own-economy "
               "revision events per pair-anchor economy, >=12 "
               "cross-economy differential months; else BLOCKED_DATA",
    }
