"""FOREX-NG3 restricted revision-event builder: the first-print stream.

Plan FOREX-NG3 section 3 (census-informed frozen floors) + section 5 P0.
The ng2 P0 census measured first-to-second-vintage revision events per
economy and split out the FIRST-PRINT ("real") sub-stream from history
backfill and bulk re-referencing artifacts.  THIS cycle anchors only on
that first-print stream; this module is the restricted builder the D1/D2
lanes consume.

Inheritance law (plan section 4): the ng2 semantics in
research/assets/forex_ng2/revision_series.py are reused VIA IMPORT and
never edited.  Restricted (first-print) membership, frozen before this
cycle's measurement:

1. the underlying event is an ng2 revision event: per reference month m,
   v1 = first vintage publishing m, v2 = immediately following vintage,
   event iff I_v2(m) != I_v1(m) with full realtime windows on both
   vintages; STRICT vintage monotonicity fail-closed (byte-identical
   duplicate rows deduped first, conflicting same-day rows raise and
   nothing is built);
2. usable: v2 availability day (v2.realtime_start, date-only
   conservative) inside the S0 window 2018-04-04..2025-04-30;
3. FIRST-PRINT restriction (both legs ng2-measured and disclosed):
   a. first_print_in_realtime_era=True -- obs month >= the feed's first
      realtime vintage (history-backfill months whose "first vintage" is
      the archive ingest are NOT genuine first prints); AND
   b. NOT a member of a bulk re-referencing group: >= 10 events sharing
      an identical (v1 day, v2 day, ratio-to-1e-6) signature are ONE
      bulk transition (a re-referencing multiplier applied to whole
      history at a single vintage, e.g. GB 2018: 60/68 events at one
      0.9359% coefficient), not independent first-print revision news.

Anchor universe law (plan section 3, frozen): CA is the ONLY anchor
economy (CA->USDCAD).  GB (8 first-print events; 60/68 usable are one
bulk 2018 re-referencing coefficient), AU (26 usable < 30, the ng2 P0
kill) and NZ (24 first-print events < 30) are EXCLUDED as anchors with
those disclosed reasons; they appear ONLY as non-anchor differential
legs, alongside US (quote leg of every funded pair, measured and
disclosed, never anchored).  Re-including any excluded economy as an
anchor is forbidden in this cycle.

Frozen floors for THIS cycle (design-from-census, set before any new
measurement; no threshold may change after any measurement):

- A4 CA own-economy: >= 30 CA first-print restricted events with full
  availability windows (ng2 measured 72); Q-6 recent >= 15 (the last 24
  calendar months of the S0 window, matched on the RESTRICTED stream's
  v2 availability days);
- A5 differential: >= 12 restricted differential months -- months
  carrying a CA restricted event AND >= 1 other economy restricted event
  (ng2 obs-month join key; ng2's wider all-usable definition measured
  102, this cycle re-measures under the restricted definition and fails
  closed if < 12).

NO PnL, NO outcome, NO scoring anywhere in this module (P0 census law).
"""

from __future__ import annotations

from typing import Iterable, Mapping, Sequence

from research.assets.forex_ng2 import revision_series as ng2

#: Inherited ng2 S0 window (16:00-NY grid coverage; grid 1842 days).
S0_WINDOW = ng2.S0_WINDOW

#: Q-6 recent-window law: last 24 calendar months of the S0 window.
RECENT_WINDOW_MONTHS = ng2.RECENT_WINDOW_MONTHS

#: Plan section 3 frozen floors (BLOCKED_DATA if not evidenced).
CA_FIRST_PRINT_FLOOR = 30      # A4: CA restricted events with full windows
CA_RECENT_FLOOR = 15           # A4: Q-6 recent restricted events
DIFFERENTIAL_FLOOR = 12        # A5: restricted differential months

#: Bulk re-referencing group law (ng2 census disclosure, inherited
#: verbatim): identical (v1 day, v2 day, ratio) across >= 10 months is
#: ONE bulk transition, not independent revision news.
BULK_GROUP_MIN_MONTHS = 10

#: Anchor universe (plan section 3): CA only.
ANCHOR_ECONOMY = "CA"
ANCHOR_PAIR = "USDCAD"

#: Economies excluded as anchor, with the plan's disclosed reasons.
EXCLUDED_AS_ANCHOR = {
    "GB": ("8 first-print events; 60/68 usable events are one bulk 2018 "
           "re-referencing coefficient -- EXCLUDED as anchor, disclosed; "
           "usable only as a non-anchor differential leg"),
    "AU": ("26 usable events < 30 (the ng2 P0 kill) -- EXCLUDED as "
           "anchor, disclosed; usable only as a non-anchor differential "
           "leg"),
    "NZ": ("24 first-print events < 30 -- EXCLUDED as anchor, disclosed; "
           "usable only as a non-anchor differential leg"),
}

#: The non-anchor legs of the A5 differential (US is the quote leg of
#: every funded pair: measured, never anchored).
NON_ANCHOR_LEGS = ("GB", "AU", "NZ", "US")

RESTRICTED_DEFINITION = (
    "first-print restricted event = ng2 revision event (v1->v2 index gap "
    "with full realtime windows, strict monotonicity fail-closed), "
    "usable in the S0 window, with first_print_in_realtime_era=True AND "
    "not a member of any bulk re-referencing group (>= 10 events sharing "
    "an identical (v1 day, v2 day, ratio-to-1e-6) signature)")

ANCHOR_UNIVERSE_LAW = (
    "anchor universe = {CA} only (CA->USDCAD); GB/AU/NZ excluded as "
    "anchor with disclosed reasons (bulk re-referencing / sub-floor "
    "streams) and appear ONLY as non-anchor differential legs; US is the "
    "quote leg, measured and disclosed, never anchored; re-including any "
    "excluded economy as anchor is forbidden in this cycle (plan "
    "section 3)")


class RestrictedStreamError(Exception):
    """Fail-closed base for malformed restricted-stream requests."""


def bulk_signature(event: ng2.RevisionEvent) -> tuple[str, str, float]:
    """The bulk re-referencing signature (v1 day, v2 day, ratio 1e-6)."""
    return (event.v1_realtime_start, event.v2_realtime_start,
            round(event.ratio, 6))


def bulk_group_signatures(
        events: Sequence[ng2.RevisionEvent],
        min_months: int = BULK_GROUP_MIN_MONTHS,
        ) -> dict[tuple[str, str, float], int]:
    """Signatures carried by >= ``min_months`` events (bulk transitions).

    Law inherited verbatim from the ng2 census bulk disclosure: events
    sharing an identical (v1 day, v2 day, ratio) signature across a bulk
    threshold of months are one structural transition applied to many
    months (a re-referencing multiplier at a single vintage), not
    independent revision news.  Descriptive threshold, frozen at 10.
    """
    counts: dict[tuple[str, str, float], int] = {}
    for e in events:
        sig = bulk_signature(e)
        counts[sig] = counts.get(sig, 0) + 1
    return {sig: n for sig, n in sorted(counts.items()) if n >= min_months}


def restricted_events(
        usable: Sequence[ng2.RevisionEvent],
        min_months: int = BULK_GROUP_MIN_MONTHS,
        ) -> list[ng2.RevisionEvent]:
    """The first-print RESTRICTED sub-stream of the usable events.

    Both legs of the restriction (plan section 3):
    first_print_in_realtime_era AND not in a bulk re-referencing group.
    Backfill history and bulk transitions are excluded from the stream
    D1/D2 consume; they remain visible in restricted_stream_report.
    """
    bulk = bulk_group_signatures(usable, min_months)
    return [e for e in usable
            if e.first_print_in_realtime_era
            and bulk_signature(e) not in bulk]


def restricted_stream_report(
        usable: Sequence[ng2.RevisionEvent],
        min_months: int = BULK_GROUP_MIN_MONTHS,
        ) -> dict:
    """Full provenance split of one economy's usable events.

    Discloses every removal so the restriction is auditable: how many
    usable events were backfill history, how many sat in bulk
    re-referencing groups, and how many first-print-era events were
    removed by the bulk rule on top of the era rule.
    """
    bulk = bulk_group_signatures(usable, min_months)
    first_print = [e for e in usable if e.first_print_in_realtime_era]
    fp_in_bulk = sum(1 for e in first_print
                     if bulk_signature(e) in bulk)
    restricted = [e for e in first_print
                  if bulk_signature(e) not in bulk]
    return {
        "usable_events": len(usable),
        "first_print_era_events": len(first_print),
        "backfill_history_events": len(usable) - len(first_print),
        "first_print_era_in_bulk_groups": fp_in_bulk,
        "bulk_groups_ge_min": {
            f"{v1}->{v2} ratio {r * 100:.4f}%": n
            for (v1, v2, r), n in bulk.items()},
        "bulk_group_events_total": sum(bulk.values()),
        "restricted_events": len(restricted),
        "law": RESTRICTED_DEFINITION,
    }


def build_restricted_stream(
        economy: str,
        rows: Sequence[ng2.VintageRow],
        window: tuple[str, str] = S0_WINDOW,
        min_months: int = BULK_GROUP_MIN_MONTHS,
        ) -> dict:
    """D1/D2-facing builder: raw vintage rows -> restricted event stream.

    Dedupe (byte-identical ingest artifacts) -> ng2 build_revision_events
    (STRICT monotonicity fail-closed: a violation raises and NOTHING is
    built) -> S0-window usable filter -> first-print restriction.  Every
    restricted event carries full availability evidence (both realtime
    windows), the v1->v2 gap, the ratio R = I_v2/I_v1 - 1 and the
    first-print-era flag.

    ``rows`` is the post-dedupe count (ng2 census comparability);
    ``rows_input`` the raw count; ``distinct_vintages`` distinct
    realtime_start days after dedupe.
    """
    deduped, removed = ng2.dedupe_exact_rows(rows)
    built = ng2.build_revision_events(economy, deduped)   # fail-closed
    usable = ng2.usable_events(built["events_all"], window)
    restricted = restricted_events(usable, min_months)
    return {
        "economy": economy,
        "rows": len(deduped),
        "rows_input": len(rows),
        "exact_duplicate_rows_removed": removed,
        "distinct_vintages": len({r.realtime_start for r in deduped}),
        "months_carried": built["months_carried"],
        "months_with_second_vintage": built["months_with_second_vintage"],
        "events_all_count": built["events_all_count"],
        "events_all": built["events_all"],
        "usable": usable,
        "restricted": restricted,
        "report": restricted_stream_report(usable, min_months),
    }


def restricted_recent_events(
        restricted: Sequence[ng2.RevisionEvent],
        window: tuple[str, str] = S0_WINDOW,
        months: int = RECENT_WINDOW_MONTHS,
        ) -> dict:
    """Q-6 law on the RESTRICTED stream (the A4 recent floor basis).

    Recent window = last ``months`` calendar months of the S0 window,
    matched on v2 availability days (PIT instants).  ng2 inherited
    bounds law; window end 2025-04-30 -> 2023-05-01..2025-04-30.
    """
    lo, hi = ng2.recent_window_bounds(window, months)
    recent = [e for e in restricted if lo <= e.v2_realtime_start <= hi]
    return {
        "window": [lo, hi],
        "count": len(recent),
        "law": (f"Q-6: last {months} calendar months of the S0 window, "
                "matched on the RESTRICTED stream's v2 availability days"),
    }


def restricted_differential_months(
        restricted_by_economy: Mapping[str, Sequence[ng2.RevisionEvent]],
        anchor: str = ANCHOR_ECONOMY,
        ) -> dict:
    """CA-anchored restricted differential months (the A5 floor basis).

    A month counts iff the ANCHOR economy carries a restricted event in
    that obs month AND >= 1 other economy carries a restricted event in
    the same obs month (ng2 join key: obs month key; quarterly legs
    contribute their quarter-first months only).  Months with multi-
    economy overlap but NO anchor event are NOT differential months
    under this cycle's CA-anchored law -- they are counted in the
    disclosure, never toward the floor.
    """
    if anchor not in restricted_by_economy:
        raise RestrictedStreamError(
            f"anchor economy {anchor!r} absent from the restricted "
            "streams: no differential months can be built (fail-closed)")
    anchor_months = {e.month_key
                     for e in restricted_by_economy[anchor]}
    months: dict[str, list[str]] = {}
    other_only: dict[str, list[str]] = {}
    for eco in sorted(restricted_by_economy):
        if eco == anchor:
            continue
        seen: set[str] = set()
        for e in restricted_by_economy[eco]:
            key = e.month_key
            if key in seen:
                continue
            seen.add(key)
            if key in anchor_months:
                months.setdefault(key, [anchor]).append(eco)
            else:
                other_only.setdefault(key, []).append(eco)
    diff = {m: ecos for m, ecos in months.items() if len(ecos) >= 2}
    return {
        "months": diff,
        "sorted_month_keys": sorted(diff),
        "total": len(diff),
        "anchor": anchor,
        "anchor_restricted_months": len(anchor_months),
        "non_anchor_event_months_without_anchor": {
            m: sorted(ecos) for m, ecos in other_only.items()},
        "non_anchor_months_without_anchor_count": len(other_only),
        "join_key_law": ("obs month key (quarter-first month for AU/NZ); "
                         "restricted (first-print) membership; a "
                         "differential month requires the anchor (CA) "
                         "AND >= 1 other economy in the same obs month"),
        "law": ("CA-anchored: months carrying non-anchor restricted "
                "events but NO CA restricted event are disclosed in "
                "non_anchor_event_months_without_anchor and never count "
                "toward the A5 floor"),
    }


def evaluate_floors(ca_restricted_total: int,
                    ca_restricted_recent: int,
                    differential_months: int,
                    own_floor: int = CA_FIRST_PRINT_FLOOR,
                    recent_floor: int = CA_RECENT_FLOOR,
                    diff_floor: int = DIFFERENTIAL_FLOOR,
                    ) -> dict:
    """Compare the restricted measurements against the frozen floors.

    Only the CA anchor is floor-anchored (plan section 3: the anchor
    universe is CA only; GB/AU/NZ are excluded as anchor with disclosed
    reasons and are never floor rows -- re-including them is forbidden).
    """
    a4_total = {
        "measured": ca_restricted_total,
        "floor": own_floor,
        "margin": ca_restricted_total - own_floor,
        "verdict": "PASS" if ca_restricted_total >= own_floor else "FAIL",
    }
    a4_recent = {
        "measured": ca_restricted_recent,
        "floor": recent_floor,
        "margin": ca_restricted_recent - recent_floor,
        "verdict": ("PASS" if ca_restricted_recent >= recent_floor
                    else "FAIL"),
    }
    a5 = {
        "measured": differential_months,
        "floor": diff_floor,
        "margin": differential_months - diff_floor,
        "verdict": ("PASS" if differential_months >= diff_floor
                    else "FAIL"),
    }
    all_pass = all(row["verdict"] == "PASS"
                   for row in (a4_total, a4_recent, a5))
    return {
        "a4_ca_own_economy": a4_total,
        "a4_ca_recent_q6": a4_recent,
        "a5_restricted_differential": a5,
        "verdict": "PASS" if all_pass else "FAIL",
        "law": ("plan section 3 frozen floors: >= 30 CA first-print "
                "restricted events with full availability windows; Q-6 "
                "recent >= 15; >= 12 restricted differential months "
                "(CA AND >= 1 other economy); anchor universe CA only; "
                "else BLOCKED_DATA"),
    }


def verify_anchor_universe(
        restricted_by_economy: Mapping[str, Sequence[ng2.RevisionEvent]],
        floors: Mapping[str, Mapping],
        ) -> dict:
    """Prove GB/AU/NZ are NOT anchors (only non-anchor differential legs).

    Checks, fail-closed:
    - the floors structure carries anchor rows ONLY for CA (no GB/AU/NZ
      own-economy floor row can exist by construction -- asserted, never
      assumed);
    - every measured economy other than CA is recorded as a non-anchor
      leg with its disclosed exclusion reason (or the US quote-leg
      reason);
    - the anchor is exactly the frozen ANCHOR_ECONOMY.
    """
    problems: list[str] = []
    anchor_rows = {k for k in floors if k.startswith("a4_")}
    non_anchor = {}
    for eco in sorted(restricted_by_economy):
        if eco == ANCHOR_ECONOMY:
            continue
        if eco in EXCLUDED_AS_ANCHOR:
            role = ("non-anchor differential leg (excluded as anchor: "
                    + EXCLUDED_AS_ANCHOR[eco])
        elif eco == "US":
            role = ("quote leg of every funded pair; measured and "
                    "disclosed, never anchored")
        else:
            problems.append(
                f"economy {eco!r} is neither the anchor, an excluded-as-"
                "anchor leg nor the US quote leg: unknown role")
            role = "UNKNOWN"
        non_anchor[eco] = {
            "restricted_events": len(restricted_by_economy[eco]),
            "role": role,
        }
    for bad in ("GB", "AU", "NZ"):
        for key, row in floors.items():
            if bad in str(key):
                problems.append(f"excluded economy {bad!r} leaked into "
                                f"floor row {key!r}")
    if not anchor_rows:
        problems.append("no a4 anchor rows found in the floors structure")
    verdict = "PASS" if not problems else "FAIL"
    return {
        "anchor": ANCHOR_ECONOMY,
        "anchor_pair": ANCHOR_PAIR,
        "anchor_law": ANCHOR_UNIVERSE_LAW,
        "excluded_as_anchor": EXCLUDED_AS_ANCHOR,
        "non_anchor_legs": non_anchor,
        "problems": problems,
        "verdict": verdict,
    }


def lookup_restricted(
        restricted_by_economy: Mapping[str,
                                       Sequence[ng2.RevisionEvent]],
        economy: str, obs_month: str) -> dict:
    """Canary-capable exact lookup on the RESTRICTED streams.

    A fabricated month MUST come back found=False; a known backfill or
    bulk month (a real usable event excluded by the restriction) MUST
    ALSO come back found=False on the restricted stream -- the
    restriction canary (proves the restriction bites, never a no-op).
    """
    hits = [e for e in restricted_by_economy.get(economy, ())
            if e.obs_month == obs_month]
    return {
        "economy": economy,
        "obs_month": obs_month,
        "found": bool(hits),
        "event_count": len(hits),
    }
