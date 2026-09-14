"""COMMODITIES-NG1 weekly decision-chain assembly (P0/P1/P2 laws wired).

Builds the per-pair weekly chain the frozen rule consumes:

- CoT facts: committed P0 count fields per report; the release instant
  comes from the COMMITTED generalized rule
  (``feasibility.release_instant_for_report``, imported, never
  re-derived -- the identical rule the D2 chain machinery used):
  Tuesday -> the P0 rule verbatim (``cot_census.release_instant``,
  Friday 15:30 America/New_York of the Tuesday-position week,
  DST-correct); measured holiday-shifted Monday -> the same week
  anchor; anything else refused.  The Tuesday/P0 path passes the
  KERNEL-SIDE PIT gate (``clock.kernel_pit_require_visible``) -- 
  fail-closed;
- release-instant monotonicity is asserted fail-closed (the
  release-sorted prefix is the only legal PIT view, D2 identity);
- decision session: first MEASURED ETP session STRICTLY after the
  release date (``clock.next_session_after``; None when the calendar
  is exhausted -- clock law, never a fabricated session);
- price-side facts: ``cend_close`` = the freshest RAW close whose
  session is strictly before the decision session -- the D1-declared
  stricter V7 close+1 reading (a bar is price-readable only when its
  close instant is STRICTLY BEFORE the decision instant, so the
  decision session's own close is never a fact source);
- counted window: release_date >= WINDOW_START (2018-01-01), the first
  ``WARMUP_WEEKS`` (52) window instants are the warmup carve-out,
  counted rows require a mapped decision session (D2/P2 identity).

This module consumes ALREADY-DIGEST-VERIFIED inputs: on the real
substrate the caller reads CoT archives and ETP CSVs through the P0
plane adapter (``plane_adapter.CommoditiesNG1Plane.consume_records``);
on synthetic fixtures the tests pass hand-built records.  The P2
census identity (``verify_pair_census``) is the fail-closed structural
assertion against the committed per-pair floor evaluation.
"""

from __future__ import annotations

import bisect

from research.assets.commodities_ng1.clock import (
    ClockRefused,
    bar_close_instant_utc,
    bar_readable,
    kernel_pit_require_visible,
    next_session_after,
)
from research.assets.commodities_ng1.feasibility import (
    WARMUP_WEEKS,
    WINDOW_START,
    release_instant_for_report,
)

SCHEMA = "commodities_ng1/runners/chain@1"

REQUIRED_COUNT_FIELDS = (
    "report_date", "open_interest", "noncomm_long", "noncomm_short",
    "noncomm_spreading", "comm_long", "comm_short",
)


class ChainRefused(Exception):
    """Fail-closed chain refusal (malformed report, broken monotonicity,
    non-Tuesday report date, PIT violation, census identity mismatch)."""


def build_pair_chain(reports: list[dict], session_dates: list,
                     session_closes: dict) -> dict:
    """The full weekly chain (warmup chains included) for ONE pair.

    ``reports``: committed count records (dict rows with
    ``REQUIRED_COUNT_FIELDS``; ``report_date`` a Tuesday ``date``).
    ``session_dates``: the leg's MEASURED ETP session calendar (sorted);
    ``session_closes``: session date -> RAW EOD close (the trading
    surface; RAW primary per the P0 census convention).

    Returns ``{"rows": [...], "counted": [bool]}``; row keys mirror the
    D2 chain identity (``report_date``, ``release_instant``,
    ``release_date``, ``decision_session``, ``g``, ``spec_net``,
    ``open_interest``, ``cend_close``, ``cend_session``).
    """
    for r in reports:
        missing = [k for k in REQUIRED_COUNT_FIELDS if k not in r]
        if missing:
            raise ChainRefused(
                f"report {r.get('report_date')!r} missing fields "
                f"{missing}; fail closed")
        if r["open_interest"] <= 0:
            raise ChainRefused(
                f"report {r['report_date']}: non-positive open interest")
    ordered = sorted(reports, key=lambda r: r["report_date"])
    if len({r["report_date"] for r in ordered}) != len(ordered):
        raise ChainRefused("duplicate report dates; fail closed")

    sessions = sorted(set(session_dates))
    rows: list[dict] = []
    prev_release = None
    for r in ordered:
        report_date = r["report_date"]
        # The COMMITTED generalized release rule (assets feasibility;
        # identical to the D2 chain machinery): Tuesday -> the P0 rule
        # verbatim; measured holiday-shifted Monday -> the same
        # week-anchor rule; anything else refused.  Imported, never
        # re-derived.
        release, rule_source = release_instant_for_report(report_date)
        if prev_release is not None and release < prev_release:
            raise ChainRefused(
                f"release instants not monotone at {report_date.isoformat()}"
                "; PIT prefix law broken")
        prev_release = release
        # Kernel-side PIT gate on this row's own fact read: positions
        # become visible only AT the resolved release instant.  On the
        # Tuesday/P0 path this is the kernel gate verbatim
        # (clock.kernel_pit_require_visible -> P0 pit_guard); on the
        # measured holiday-shift path the row read happens AT the
        # committed week-anchor release instant itself (use == release,
        # the earliest legal instant), and every LATER consumer must
        # gate through the same resolved instants carried on the rows.
        if rule_source == "p0_release_instant":
            kernel_pit_require_visible(report_date, release)
        release_day = release.date()
        try:
            decision_session = next_session_after(release_day, sessions)
        except ClockRefused:
            decision_session = None
        spec_net = r["noncomm_long"] - r["noncomm_short"]
        comm_net = r["comm_long"] - r["comm_short"]
        g = (spec_net - comm_net) / r["open_interest"]
        cend_session = None
        cend_close = None
        if decision_session is not None:
            cut = bisect.bisect_left(sessions, decision_session)
            if cut > 0:
                cand = sessions[cut - 1]
                # D1 stricter close+1 law: the fact bar's close instant
                # must be STRICTLY BEFORE the decision instant; the
                # decision session's own close is never a fact source.
                if bar_readable(cand, bar_close_instant_utc(
                        decision_session)) and cand < decision_session:
                    cend_session = cand
                    cend_close = session_closes[cand]
        rows.append({
            "report_date": report_date,
            "release_instant": release,
            "release_date": release_day,
            "rule_source": rule_source,
            "decision_session": decision_session,
            "g": g,
            "spec_net": spec_net,
            "comm_net": comm_net,
            "open_interest": r["open_interest"],
            "cend_session": cend_session,
            "cend_close": cend_close,
        })

    counted = [False] * len(rows)
    order = 0
    for i, row in enumerate(rows):
        if row["release_date"] >= WINDOW_START:
            if order >= WARMUP_WEEKS and row["decision_session"] is not None:
                counted[i] = True
            order += 1
    return {"rows": rows, "counted": counted}


def counted_rows(chain: dict) -> list[int]:
    """Indices of the counted (grid-eligible) window rows."""
    return [i for i, c in enumerate(chain["counted"]) if c]


def verify_pair_census(pair_id: str, chain: dict, floor_evaluation: dict
                       ) -> bool:
    """Fail-closed identity: the reconstructed grid MUST equal the
    committed P2 per-pair floor evaluation (D2 census identity).

    Checks counted-window release count, grid-eligible (mapped) count,
    first/last counted release, and the unmapped counted releases --
    structural facts only (no PnL, no outcome)."""
    rows = chain["rows"]
    window_rows = [i for i, r in enumerate(rows)
                   if r["release_date"] >= WINDOW_START]
    counted_window = window_rows[WARMUP_WEEKS:]
    mapped = [i for i in counted_window
              if rows[i]["decision_session"] is not None]
    unmapped = [rows[i]["release_date"].isoformat()
                for i in counted_window
                if rows[i]["decision_session"] is None]
    if len(counted_window) != floor_evaluation["counted_expected_releases"]:
        raise ChainRefused(
            f"pair {pair_id}: counted-window releases {len(counted_window)} "
            f"!= committed {floor_evaluation['counted_expected_releases']}")
    if len(mapped) != floor_evaluation["grid_eligible_instants"]:
        raise ChainRefused(
            f"pair {pair_id}: grid-eligible instants {len(mapped)} != "
            f"committed {floor_evaluation['grid_eligible_instants']}")
    if sum(chain["counted"]) != len(mapped):
        raise ChainRefused(
            f"pair {pair_id}: measured mask {sum(chain['counted'])} != "
            f"mapped {len(mapped)}")
    first = rows[mapped[0]]["release_date"].isoformat()
    last = rows[counted_window[-1]]["release_date"].isoformat()
    if first != floor_evaluation["counted_first_release"] \
            or last != floor_evaluation["counted_last_release"]:
        raise ChainRefused(
            f"pair {pair_id}: counted window [{first}..{last}] != "
            f"committed [{floor_evaluation['counted_first_release']}.."
            f"{floor_evaluation['counted_last_release']}]")
    if unmapped != floor_evaluation["unmapped_release_dates_counted"]:
        raise ChainRefused(
            f"pair {pair_id}: unmapped counted releases {unmapped} != "
            f"committed {floor_evaluation['unmapped_release_dates_counted']}")
    return True
