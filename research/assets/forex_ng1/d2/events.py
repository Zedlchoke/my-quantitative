"""Announcement census loading, interval-strict-before publication
ordering, and the 16:00-NY decision-grid entry clock for FOREX-NG1 D2.

P-1 evidence law (identical to the D1 proposals):

- exact-time instants (CA true-UTC, NZ Auckland DST-corrected) are
  POINTS;
- DATE_ONLY evidence (GB, AU, US) is a full-day uncertainty interval
  [00:00Z, 23:59:59Z];
- X strictly precedes Y iff X's LATEST possible instant < Y's EARLIEST
  possible instant; anything else is UNPROVABLE ORDER and fails closed.

Entry clock (identical to the D1 proposals):

- A(e) = end of day on ``operative_vintaged_available_from``; the value
  leg's evidenced availability is date-granular, so a 16:00-NY decision
  (20:00/21:00Z) never sees a print whose availability bound is that
  same date: the decision day D(e) is the FIRST common-grid day
  STRICTLY AFTER the operative date (and after any additional
  month-order closure bound for lane A5).
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import date, datetime, timedelta, timezone

CENSUS_SHA256_PIN = ("e8a35d23ce64ce71a8d30792750b877c387de3692"
                     "af1e4d17391ea4cc35b4abe")


class CensusError(Exception):
    """Fail-closed census integrity error."""


def load_census(path: str, verify_sha: bool = True) -> dict:
    """Load the pinned P0 announcement census; verify-on-read sha256."""
    with open(path, "rb") as fh:
        raw = fh.read()
    digest = hashlib.sha256(raw).hexdigest()
    if verify_sha and digest != CENSUS_SHA256_PIN:
        raise CensusError(
            f"census sha256 drift: {digest} != pinned {CENSUS_SHA256_PIN}")
    census = json.loads(raw.decode("utf-8"))
    instants = census.get("instants")
    if not isinstance(instants, list) or not instants:
        raise CensusError("census carries no instants")
    return census


def first_release_events(census: dict) -> list[dict]:
    """Census first releases minus pit_notes rows (fail-closed base
    set; the 16 CA WDS corrections are ordinals 2-4 and drop out via
    is_first_release_of_period)."""
    out = []
    for inst in census["instants"]:
        if not inst.get("is_first_release_of_period"):
            continue
        if inst.get("pit_notes"):
            continue          # fail-closed PIT anomaly policy
        out.append(dict(inst))
    out.sort(key=lambda r: (r["publication_date"], r["economy"]))
    return out


# --------------------------------------------------------------------------- #
# interval ordering (P-1)
# --------------------------------------------------------------------------- #

def interval_bounds(inst: dict) -> tuple[datetime, datetime]:
    """(earliest, latest) possible publication instant of an event."""
    day = date.fromisoformat(inst["publication_date"])
    if inst.get("time_precision") == "CALENDAR_TIME_UTC_EXACT":
        t = datetime.strptime(inst["publication_instant_utc"],
                              "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
        return (t, t)
    lo = datetime(day.year, day.month, day.day, 0, 0, 0, tzinfo=timezone.utc)
    hi = datetime(day.year, day.month, day.day, 23, 59, 59,
                  tzinfo=timezone.utc)
    return (lo, hi)


def strictly_before(x: dict, y: dict) -> bool:
    """P-1 provable strict precedence on uncertainty intervals."""
    bx, by = interval_bounds(x), interval_bounds(y)
    return bx[1] < by[0]


def month_key(inst: dict) -> str:
    """Release-calendar month = calendar month of the evidenced (local)
    publication date."""
    return inst["publication_date"][:7]


# --------------------------------------------------------------------------- #
# order state (lane A5)
# --------------------------------------------------------------------------- #

def order_state(events: list[dict]) -> dict:
    """US-anchored months, unique opening follower, co-earliest sets,
    follower sets.  All claims interval-strict-before; unprovable order
    fails closed (no state)."""
    months: dict[str, dict[str, list[dict]]] = {}
    for e in events:
        months.setdefault(month_key(e), {"US": [], "nonUS": []})
        bucket = "US" if e["economy"] == "US" else "nonUS"
        months[month_key(e)][bucket].append(e)

    anchored: dict[str, dict] = {}
    non_anchored: list[dict] = []
    for m, groups in sorted(months.items()):
        us, nonus = groups["US"], groups["nonUS"]
        if len(us) != 1 or not nonus:
            non_anchored.append({"month": m,
                                 "reason": "no_unique_us_or_no_nonus"})
            continue
        u = us[0]
        if all(strictly_before(u, n) for n in nonus):
            anchored[m] = {"us": u, "nonUS": nonus}
        else:
            non_anchored.append({"month": m, "reason": "us_not_provably_first"})

    unique_of: dict[str, dict] = {}
    no_unique: dict[str, list[dict]] = {}
    co_earliest: dict[str, list[dict]] = {}
    for m, groups in sorted(anchored.items()):
        nonus = groups["nonUS"]
        openers = [n for n in nonus
                   if all(strictly_before(n, o) for o in nonus if o is not n)]
        if len(openers) == 1:
            unique_of[m] = openers[0]
        else:
            # inclusive co-earliest: nothing provably strictly precedes
            # them (the NEIGH-COOPEN construction's event source)
            coe = [n for n in nonus
                   if not any(strictly_before(o, n)
                              for o in nonus if o is not n)]
            no_unique[m] = openers
            co_earliest[m] = coe

    followers: dict[str, list[dict]] = {}
    for m, of in unique_of.items():
        followers[m] = [e for e in anchored[m]["nonUS"] if e is not of]

    return {
        "publication_months": sorted(months),
        "anchored_months": sorted(anchored),
        "anchored": anchored,
        "non_anchored_months": non_anchored,
        "unique_of_months": sorted(unique_of),
        "unique_of": unique_of,
        "no_unique_of_months": sorted(no_unique),
        "co_earliest": co_earliest,
        "followers": followers,
        "counts": {
            "publication_months": len(months),
            "us_anchored_months": len(anchored),
            "non_anchored_months": len(non_anchored),
            "unique_of_months": len(unique_of),
            "unique_of_by_economy": dict(Counter(
                e["economy"] for e in unique_of.values())),
            "no_unique_of_months": len(no_unique),
            "co_earliest_events": sum(len(v) for v in co_earliest.values()),
            "nonus_events_in_anchored_months": sum(
                len(g["nonUS"]) for g in anchored.values()),
        },
    }


# --------------------------------------------------------------------------- #
# the 16:00-NY entry clock on the common grid
# --------------------------------------------------------------------------- #

def first_grid_day_strictly_after(bound_date: date, grid_index: dict,
                                  window_end: date) -> date | None:
    """D(e): the first common-grid day with date > bound_date (a 16:00-NY
    decision can never see a print whose availability bound is the same
    date).  None when the bound falls at/after the window end."""
    probe = bound_date + timedelta(days=1)
    while probe <= window_end:
        if probe in grid_index:
            return probe
        probe += timedelta(days=1)
    return None


def exposure_days(entry: date, hold: int, grid_days: list[date],
                  grid_index: dict) -> list[date]:
    """Exposure cells: entry day and the following hold-1 grid days
    (representation identity: i..i+H-1; the exit fill at i+H is not an
    exposure cell).  Days past the grid end are dropped."""
    i = grid_index[entry]
    return [grid_days[j] for j in range(i, min(i + hold, len(grid_days)))]


def eod_month_bound(inst: dict) -> date:
    """EOD(publication date) bound for month-order closure clocks."""
    return date.fromisoformat(inst["publication_date"])
