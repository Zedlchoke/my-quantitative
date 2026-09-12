"""VOL-NG1 P0 census: fail-closed parsers, frozen floors, P-7 canaries.

Everything here is a MEASUREMENT over pulled bytes; there are no
proposals, no signals, no scoring, and no outcome numbers anywhere
(P0 census law).

Frozen floors (plan section 3, fail-closed -- a shortfall is recorded,
never renegotiated):

- F1: common VIX9D x VIX x VIX3M daily coverage >= 8 years;
- F2: >= 1000 daily term-structure instants post-2015-01-01;
- F3: >= 2 living volatility ETP legs with >= 6 years EOD each;
- F4: >= 1 delisted volatility ETP proven via the EODHD delisted
  channel (XIV.US is empty on the plain eod endpoint -- the delisted
  channel is the only lawful proof route).

P-7 canaries (each must FAIL to look up / refuse):
- a fabricated date (must not be found in any series);
- a never-existed index column name (parser must refuse the file);
- a fabricated ETP ticker (must be refused at the plane and absent
  from the delisted channel together with the other negative controls).
"""

from __future__ import annotations

import csv
import io
from datetime import date, datetime

#: The exact official CBOE daily-history schema (measured 2026-09-12).
CBOE_HEADER = ("DATE", "OPEN", "HIGH", "LOW", "CLOSE")

#: Frozen index-name census (plan section 3).  Anything else is refused.
FROZEN_INDEX_NAMES = ("VIX", "VIX9D", "VIX3M", "VIX6M")

#: The three index legs the frozen floors are computed on.
FLOOR_LEGS = ("VIX9D", "VIX", "VIX3M")

POST_2015 = date(2015, 1, 1)
F1_MIN_YEARS = 8.0
F2_MIN_INSTANTS = 1000
F3_MIN_LEGS = 2
F3_MIN_YEARS = 6.0

#: Corp-actions step detector bounds (measured V8 convention): a raw
#: close ratio at or beyond these magnitudes is a split/reverse-split
#: signature on these ETPs; the adjusted series must be continuous.
STEP_RATIO_GE = 3.0
STEP_RATIO_LE = 1.0 / 3.0
ADJ_CONTINUITY_TOL = 0.10


class CensusError(Exception):
    """Malformed or out-of-census input: fail-closed, nothing inferred."""


# --------------------------------------------------------------------------- #
# CBOE official CSV parser
# --------------------------------------------------------------------------- #

def require_frozen_index_name(index_name: str) -> str:
    if index_name not in FROZEN_INDEX_NAMES:
        raise CensusError(
            f"index name {index_name!r} is outside the frozen census "
            f"{FROZEN_INDEX_NAMES}: refused (P-7)")
    return index_name


def parse_cboe_csv(body: bytes) -> dict:
    """Parse one official CBOE daily-history CSV, fail-closed.

    The header must be EXACTLY ``DATE,OPEN,HIGH,LOW,CLOSE`` -- a
    never-existed index column name fails closed here (P-7).  Dates are
    official M/D/YYYY instants; the result is a sorted ISO-date ->
    CLOSE mapping (close is the daily index fact the floors use).
    """
    text = body.decode("utf-8", "replace")
    reader = csv.reader(io.StringIO(text))
    try:
        header = next(reader)
    except StopIteration as exc:
        raise CensusError("empty CBOE CSV") from exc
    if tuple(h.strip().upper() for h in header) != CBOE_HEADER:
        raise CensusError(
            f"unexpected CBOE header {tuple(header)}: expected "
            f"{CBOE_HEADER} (never-existed column names fail closed)")
    series: dict[str, float] = {}
    for row in reader:
        if not row or all(not c.strip() for c in row):
            continue
        if len(row) != len(CBOE_HEADER):
            raise CensusError(f"malformed CBOE row: {row!r}")
        try:
            d = datetime.strptime(row[0].strip(), "%m/%d/%Y").date()
        except ValueError as exc:
            raise CensusError(
                f"malformed CBOE date {row[0]!r}: {exc}") from exc
        close = float(row[4])
        series[d.isoformat()] = close
    if not series:
        raise CensusError("CBOE CSV parsed to zero rows")
    return series


# --------------------------------------------------------------------------- #
# overlap census (explicit first-common-date)
# --------------------------------------------------------------------------- #

def overlap_census(series_by_name: dict[str, dict[str, float]]) -> dict:
    """Common-date census over the FLOOR_LEGS (VIX9D x VIX x VIX3M).

    The intersection is computed from the actual date sets; the
    first-common-date is recorded explicitly.  A missing floor leg is
    fail-closed (the census refuses to compute a partial floor).
    """
    for leg in FLOOR_LEGS:
        if leg not in series_by_name:
            raise CensusError(
                f"floor leg {leg!r} absent: term-structure floors refuse "
                "to compute on a partial census")
    common = set(series_by_name[FLOOR_LEGS[0]])
    for leg in FLOOR_LEGS[1:]:
        common &= set(series_by_name[leg])
    if not common:
        raise CensusError("empty common-date intersection")
    dates = sorted(common)
    first = date.fromisoformat(dates[0])
    last = date.fromisoformat(dates[-1])
    span_years = (last - first).days / 365.25
    post_2015 = [d for d in dates if date.fromisoformat(d) >= POST_2015]
    return {
        "legs": list(FLOOR_LEGS),
        "per_leg_first_date": {
            leg: min(series_by_name[leg]) for leg in FLOOR_LEGS},
        "per_leg_last_date": {
            leg: max(series_by_name[leg]) for leg in FLOOR_LEGS},
        "per_leg_rows": {
            leg: len(series_by_name[leg]) for leg in FLOOR_LEGS},
        "first_common_date": dates[0],
        "last_common_date": dates[-1],
        "common_days": len(dates),
        "span_years": round(span_years, 4),
        "instants_post_2015": len(post_2015),
    }


# --------------------------------------------------------------------------- #
# ETP leg coverage (RAW bars primary)
# --------------------------------------------------------------------------- #

def etp_leg_coverage(bars: list[dict]) -> dict:
    """Years of RAW EOD coverage for one living leg (V8 convention: the
    RAW series is primary).  Bars are the served EODHD JSON objects."""
    dates = sorted(b["date"] for b in bars if isinstance(b, dict) and b.get("date"))
    if not dates:
        raise CensusError("ETP leg has zero dated bars")
    first = date.fromisoformat(dates[0])
    last = date.fromisoformat(dates[-1])
    return {
        "first_bar": dates[0],
        "last_bar": dates[-1],
        "bars": len(dates),
        "years_eod": round((last - first).days / 365.25, 4),
    }


def detect_corp_action_steps(bars: list[dict]) -> dict:
    """Measured corp-actions inventory (V8 convention, RAW primary).

    Every raw-close step at split magnitude is inventoried with what
    the adjusted series does at the same instant:

    - ``ADJUSTED_CONTINUOUS``: adjusted ratio within +-10% of 1.0 (the
      vendor's adjusted series compensates the step);
    - ``ADJUSTED_TRACKS_RAW``: adjusted ratio within +-10% of the raw
      ratio (the step is present in BOTH series -- e.g. a genuine
      price collapse, or an uncompensated reorg step);
    - ``RESIDUAL``: neither -- recorded with the implied split factor
      ``raw_ratio / adjusted_ratio`` (measured; e.g. an exact 4.0 or
      5.0 with a larger-than-tolerance same-day market move).

    This is a MEASURED INVENTORY, not a pass/fail gate: the RAW series
    is primary (V8 convention) and this inventory is the mandatory
    event-handling input for any later consumption lane.  No vendor
    statement is assumed anywhere -- the steps are discovered in the
    served bytes themselves."""
    clean = sorted(
        (b for b in bars
         if isinstance(b, dict) and b.get("date")
         and isinstance(b.get("close"), (int, float))
         and isinstance(b.get("adjusted_close"), (int, float))),
        key=lambda b: b["date"])
    steps = []
    for prev, cur in zip(clean, clean[1:]):
        if prev["close"] <= 0 or prev["adjusted_close"] <= 0:
            continue
        raw_ratio = cur["close"] / prev["close"]
        if raw_ratio >= STEP_RATIO_GE or raw_ratio <= STEP_RATIO_LE:
            adj_ratio = cur["adjusted_close"] / prev["adjusted_close"]
            adjusted_continuous = (1.0 - ADJ_CONTINUITY_TOL
                                   <= adj_ratio <= 1.0 + ADJ_CONTINUITY_TOL)
            adjusted_tracks_raw = (
                abs(adj_ratio - raw_ratio) / abs(raw_ratio)
                <= ADJ_CONTINUITY_TOL)
            klass = ("ADJUSTED_CONTINUOUS" if adjusted_continuous
                     else "ADJUSTED_TRACKS_RAW" if adjusted_tracks_raw
                     else "RESIDUAL")
            steps.append({
                "date": cur["date"],
                "raw_ratio": round(raw_ratio, 6),
                "adjusted_ratio": round(adj_ratio, 6),
                "implied_factor": round(raw_ratio / adj_ratio, 6),
                "classification": klass,
            })
    by_class: dict[str, int] = {}
    for s in steps:
        by_class[s["classification"]] = by_class.get(
            s["classification"], 0) + 1
    return {
        "step_events": steps,
        "class_counts": by_class,
        "raw_primary_note": "RAW series primary (V8 convention); every "
                            "inventoried step requires explicit event "
                            "handling in any later consumption lane",
    }


# --------------------------------------------------------------------------- #
# frozen floors
# --------------------------------------------------------------------------- #

def floors(overlap: dict, living_legs: dict[str, dict],
           delisted: dict) -> dict:
    """Evaluate the four frozen floors; every verdict is measured."""
    f1_ok = overlap["span_years"] >= F1_MIN_YEARS
    f2_ok = overlap["instants_post_2015"] >= F2_MIN_INSTANTS
    qualifying = {t: m for t, m in living_legs.items()
                  if m["years_eod"] >= F3_MIN_YEARS}
    f3_ok = len(qualifying) >= F3_MIN_LEGS
    dead_proven = [c for c, present in delisted.get("dead_present", {}).items()
                   if present]
    controls_clean = all(delisted.get("controls_absent", {}).values()) \
        if delisted.get("controls_absent") else False
    f4_ok = bool(dead_proven) and controls_clean and bool(delisted.get("served"))
    return {
        "F1_common_term_structure_coverage_years": {
            "floor": F1_MIN_YEARS,
            "measured": overlap["span_years"],
            "first_common_date": overlap["first_common_date"],
            "last_common_date": overlap["last_common_date"],
            "verdict": "PASS" if f1_ok else "FAIL",
        },
        "F2_term_structure_instants_post_2015": {
            "floor": F2_MIN_INSTANTS,
            "measured": overlap["instants_post_2015"],
            "verdict": "PASS" if f2_ok else "FAIL",
        },
        "F3_living_etp_legs_with_6y_eod": {
            "floor_legs": F3_MIN_LEGS,
            "floor_years": F3_MIN_YEARS,
            "measured_legs": {t: m["years_eod"] for t, m in
                              living_legs.items()},
            "qualifying_legs": sorted(qualifying),
            "verdict": "PASS" if f3_ok else "FAIL",
        },
        "F4_delisted_vol_etp_proven": {
            "required": ">=1 dead vol ETP present on the US delisted "
                        "channel with clean never-existed controls",
            "dead_present": dead_proven,
            "controls_absent": delisted.get("controls_absent", {}),
            "delisted_channel_served": bool(delisted.get("served")),
            "verdict": "PASS" if f4_ok else "FAIL",
        },
    }


# --------------------------------------------------------------------------- #
# P-7 canaries
# --------------------------------------------------------------------------- #

def canaries(series_by_name: dict[str, dict[str, float]],
             delisted: dict) -> list[dict]:
    """Each canary must FAIL to find/refuse -- recorded per P-7."""
    rows = []

    # 1. fabricated date: must not be present in any floor leg or the
    #    common intersection (2026-09-12 is a Saturday; 2099-01-01 is
    #    beyond any data; use both).
    common: set[str] | None = None
    for leg in FLOOR_LEGS:
        leg_dates = set(series_by_name[leg])
        common = leg_dates if common is None else (common & leg_dates)
    for fake in ("2026-09-12", "2099-01-01"):
        in_intersection = fake in (common or set())
        in_any = any(fake in s for s in series_by_name.values())
        found = in_intersection or in_any
        rows.append({
            "canary": "fabricated_date",
            "probe": fake,
            "found": found,
            "verdict": "PASS" if not found else "FAIL",
        })

    # 2. never-existed index column: the parser must refuse a file
    #    carrying a fabricated column name, and the name census must
    #    refuse a fabricated index.
    fake_header = b"DATE,VIX2M,CLOSE\n01/02/2020,20.0,20.0\n"
    refused = False
    try:
        parse_cboe_csv(fake_header)
    except CensusError:
        refused = True
    name_refused = False
    try:
        require_frozen_index_name("VIX2M")
    except CensusError:
        name_refused = True
    ok = refused and name_refused
    rows.append({
        "canary": "never_existed_index_column",
        "probe": "VIX2M",
        "parser_refused_header": refused,
        "name_census_refused": name_refused,
        "verdict": "PASS" if ok else "FAIL",
    })

    # 3. fabricated ETP ticker: must be absent from the delisted
    #    channel alongside the other negative controls (the plane-level
    #    refusal is asserted separately by the tests).
    absent = {c: not delisted.get("dead_present", {}).get(c, False)
              for c in ("ZZZVIX", "QVIXX")}
    rows.append({
        "canary": "fabricated_etp_ticker",
        "probe": sorted(absent),
        "absent_everywhere": all(absent.values()),
        "verdict": "PASS" if all(absent.values()) else "FAIL",
    })
    return rows
