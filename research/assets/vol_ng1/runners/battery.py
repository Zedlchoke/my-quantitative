"""VOL-NG1 I-phase control battery (binding on EVERY runner cell).

Implemented exactly per the binding freeze
(``selection_freeze.i_phase_control_battery``): the mandatory controls
are VETOES, not suggestions; a control that is not runnable makes its
cell NOT_RUN fail-closed (Q-11), never skipped; controls run on the
SAME frozen representation as their arm.

- ``index_only_shadow``  : A4-P2 -- the identical acceleration-regime
  rule driven by the vol index series ALONE (no ETP price anywhere in
  the state), scored as a HYPOTHETICAL INDEX-POINT BOOK on the VIX
  close itself (``index_point_book``): `state` units of the index,
  marked in index points at the V7 re-clock sessions, NO ETP leg and
  NO ETP costs.  The control is "is the ETP decision beating its own
  index re-clock?" (PLAN_vol_ng1.md section 1a) -- a genuinely
  different book from the arm's ETP book for every cell (audit H1
  remediation, pre-scored addendum
  ``selection_freeze_addendum_a7r1.json``; the pre-remediation
  control re-ran the arm's own ETP book, so control == arm and R2's
  control_reproduces veto fired tautologically).  A5-P2 -- the
  identical asymmetry rule with BOTH spread sides proxied from the vol
  INDEX series alone (trailing realized volatility of the VIX close for
  the short side and of a longer-lookback variant of the same index
  series for the mid side, at the committed lookbacks 21 / 90 -- 90 is
  the MID bucket's committed day gap in the frozen cost contract, the
  only committed longer lookback), placement re-clocked onto the ETP
  buckets; no ETP price anywhere in the shadow's state.
- ``cost_path_control``  : the measured execution spreads scaled
  through the committed tier ladder (tier 2.0 at the top), cost once
  per fill, the Q-16 roll/decay path component EXPLICIT at every tier,
  per arm INCLUDING its measured rebalance/fill count (A4-P2) and on
  BOTH buckets (A5-P2: SHORT path formula on the near spread, MID path
  formula on the multi-month spread; a rotation pays both sides).
- ``calendar_clock_shadow`` (k=5): the same rule re-clocked to a fixed
  shift of 5 grid sessions; a placement that survives the re-clock
  unchanged is a calendar artefact and dies (distinctness measured).
- ``placebo`` (seed 20260912): the arm's decision-state series is
  time-shuffled (ORDSHUF-style order shuffle) with matched marginals
  and destroyed temporal ordering; deterministic under the frozen seed.
- ``invalid_null_distinction``: an uncomputable state (warmup, refused
  V7 tail, missing session) is INVALID and refused fail-closed; never
  coerced to flat/aligned and never scored as a decision (Q-11).

NO scoring, NO outcome numbers on real data: every function here emits
structural series/lines/counts only.  USD cost lines and index-point
book lines exist ONLY on synthetic fixtures (unit-tested); scored
verdicts consume externally supplied metrics at E.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

import numpy as np

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.vol_ng1 import accounting as acc             # noqa: E402
from research.assets.vol_ng1.runners import arms as ar            # noqa: E402
from research.assets.vol_ng1.runners import config as cfg         # noqa: E402
from research.control.vol_ng1_run.d2 import d2_novelty as dn      # noqa: E402

SCHEMA = "vol_ng1_runners/battery@1"

#: EXPENSE CONVENTION PIN (audit a7_prelaunch_vol_ng1.json finding M1,
#: committed at 57d5d639; pre-scored addendum
#: ``selection_freeze_addendum_a7r1.json``): ``net_stress_usd_total``
#: INCLUDES the explicit expense line -- net = gross - execution
#: - Q-16 path - expense -- matching the FROZEN P2 round-trip cost
#: ceilings, which include expense in ``round_trip_cost_ceiling_bps``.
#: Both A4-P2 kill routes (R1/R5 ceiling clearance and the R5 stress
#: net) therefore share ONE expense convention; the expense line stays
#: tier-invariant and is never re-scaled.
EXPENSE_IN_NET_STRESS = True


class BatteryError(Exception):
    """Fail-closed battery error."""


# --------------------------------------------------------------------------- #
# index-only shadow
# --------------------------------------------------------------------------- #
def a5_index_only_state(ctx: dict, asym_threshold: float,
                        latch_sessions: int) -> dict[str, float | None]:
    """The A5-P2 index-only shadow state: BOTH spread sides proxied
    from the vol INDEX series alone (no ETP price anywhere):
      rv_short = realized_vol(VIX close, lookback 21)   (committed
                 short/proxy lookback);
      rv_mid   = realized_vol(VIX close, lookback 90)   (the committed
                 MID-bucket day gap: the committed longer-lookback
                 variant of the same index series);
      SPREAD_side = expanding-z(VIX) - expanding-z(rv_side);
      ASYM = SPREAD_short - SPREAD_mid, then the identical
      threshold + debounce-latch law at the arm's frozen axis."""
    grid = ctx["grid"]
    vix = {d: ctx["index"]["VIX"].get(d) for d in grid}
    minh = int(ctx.get("standardization_min_history",
                       dn.FROZEN_DEFAULTS["standardization_min_history"]))
    z_impl = dn.expanding_z(vix, grid, minh)

    def spread(lookback: int) -> dict[str, float | None]:
        rv = dn.realized_vol(vix, grid, lookback,
                             ctx["proxy_annualization"])
        z_rv = dn.expanding_z(rv, grid, minh)
        out: dict[str, float | None] = {}
        for d in grid:
            a, b = z_impl.get(d), z_rv.get(d)
            out[d] = None if (a is None or b is None) else a - b
        return out

    asym_raw: dict[str, float | None] = {}
    s_short = spread(cfg.A5_SHADOW_SHORT_LOOKBACK)
    s_mid = spread(cfg.A5_SHADOW_MID_LOOKBACK)
    for d in grid:
        a, b = s_short.get(d), s_mid.get(d)
        asym_raw[d] = None if (a is None or b is None) else a - b
    raw = dn.threshold_states(asym_raw, grid, asym_threshold,
                              "short_extreme", "mid_extreme", "aligned")
    codes: dict[str, float | None] = {}
    for d in grid:
        r = raw[d]
        codes[d] = None if r is None else {
            "short_extreme": 1.0, "aligned": 0.0, "mid_extreme": -1.0}[r]
    return dn.debounce_latch(codes, grid, latch_sessions)


@dataclass
class ShadowResult:
    control: str
    decision_state: dict = field(default_factory=dict)
    decisions: list = field(default_factory=list)
    refused_tail_decisions: int = 0
    invalid_instants: int = 0
    distinct_from_arm: bool | None = None
    notes: dict = field(default_factory=dict)
    book: dict = field(default_factory=dict)


#: Distinctness law (accurate-disclosure text shared by the notes):
#: book-level distinctness is measured whenever the arm's cell result
#: is supplied; the two books are compared as ordered round-trip
#: identity rows INCLUDING the instrument, so the shadow (index-point
#: instrument) differs from the arm (ETP-leg instrument) for ANY input
#: while either book is non-empty.  Two EMPTY books are unmeasurable
#: (nothing exists to distinguish; disclosed None) and R2 limb (a) is
#: then uncomputable at E: fail-closed NOT_RUN, never an inferred PASS.
_DISTINCT_LAW = (
    "measured at the BOOK level when the arm cell result is supplied: "
    "ordered round-trip identity rows (instrument, entry/exit "
    "sessions, direction, marking prices); the instrument differs for "
    "ANY input (index points vs ETP legs), so a non-empty arm book is "
    "always distinct from its index-only shadow; two empty books are "
    "unmeasurable (None, disclosed)")


def _shadow_book_rows(round_trips: list) -> list:
    return [("index_point_book", rt["mark_series"], rt["entry_session"],
             rt["exit_session"], rt["direction"], rt["entry_close"],
             rt["exit_close"]) for rt in round_trips]


def _arm_book_rows(round_trips: list) -> list:
    return [("etp_leg_book", rt["leg"], rt["entry_session"],
             rt["exit_session"], rt["direction"], rt["entry_price"],
             rt["exit_price"]) for rt in round_trips]


def books_distinct(shadow_round_trips: list,
                   arm_round_trips: list) -> bool | None:
    """The H1-remediated distinctness measure: True iff the shadow
    book and the arm book differ as ordered identity-row lists (the
    instrument field makes any non-empty pair differ for ANY input);
    None when BOTH books are empty (unmeasurable: no book exists on
    either side; at E the R2 limb (a) metrics are then missing and
    fail-closed NOT_RUN applies)."""
    if not shadow_round_trips and not arm_round_trips:
        return None
    return _shadow_book_rows(shadow_round_trips) != \
        _arm_book_rows(arm_round_trips)


def index_point_book(grid: list[str], state: dict[str, float | None],
                     index_closes: dict[str, float],
                     mark_series: str = cfg.SHADOW_MARK_SERIES) -> dict:
    """The A4-P2 index-only shadow's HYPOTHETICAL book (audit
    a7_prelaunch_vol_ng1.json finding H1 remediation, pre-scored
    addendum ``selection_freeze_addendum_a7r1.json``): the decision
    state placed as ``state`` units of the marked index series itself
    and marked in INDEX POINTS -- entry/exit at the index closes of the
    V7 close+1 re-clock execution sessions, NO ETP leg anywhere and NO
    ETP costs (an index is not a tradable instrument; the control
    answers PLAN_vol_ng1.md section 1a: is the ETP decision beating its
    own index re-clock?).  Structural plumbing only: no scored metric
    is computed here."""
    grid_index = {d: i for i, d in enumerate(grid)}
    decisions, refused = ar.decisions_to_executions(grid, state)
    round_trips: list[dict] = []
    fills: list[dict] = []
    open_pos: dict | None = None

    def _close(session: str, price: float, reason: str) -> None:
        nonlocal open_pos
        fills.append({"session": session, "units": -open_pos["units"],
                      "kind": "exit_or_rebalance"})
        round_trips.append({
            "instrument": f"{mark_series}_index_close",
            "mark_series": mark_series,
            "units": open_pos["units"],
            "direction": 1 if open_pos["units"] > 0 else -1,
            "entry_session": open_pos["session"],
            "entry_close": open_pos["price"],
            "exit_session": session,
            "exit_close": price,
            "exit_reason": reason,
            "held_sessions": grid_index[session]
                             - grid_index[open_pos["session"]],
            "gross_index_points": open_pos["units"]
                                  * (price - open_pos["price"]),
        })
        open_pos = None

    for row in decisions:
        session = row["exec_session"]
        price = index_closes.get(session)
        if price is None or price <= 0:
            raise BatteryError(
                f"index-only shadow book: no positive {mark_series} "
                f"close at execution session {session} (fail-closed)")
        desired = float(row["state"])
        if open_pos is not None and desired != open_pos["units"]:
            _close(session, price,
                   "rebalance" if desired != 0.0 else "signal_flat")
        if open_pos is None and desired != 0.0:
            open_pos = {"units": desired, "session": session,
                        "price": price}
            fills.append({"session": session, "units": desired,
                          "kind": "entry_or_rebalance"})
    if open_pos is not None:
        last = grid[-1]
        price = index_closes.get(last)
        if price is None or price <= 0:
            raise BatteryError(
                f"index-only shadow book: no {mark_series} close at "
                f"the window tail {last} (fail-closed)")
        _close(last, price, "forced_window_end")
    if len(fills) != 2 * len(round_trips):
        raise BatteryError("index shadow book fills != 2x round trips "
                           "(fail-closed)")
    return {
        "control_book": "index_point_book",
        "mark_series": mark_series,
        "decisions": decisions,
        "refused_tail_decisions": refused,
        "invalid_instants": sum(1 for d in grid if state.get(d) is None),
        "fills": fills,
        "round_trips": round_trips,
        "n_round_trips": len(round_trips),
        "n_fills": len(fills),
        "cost_lines": ("NONE: an index is not a tradable instrument; "
                       "the shadow book carries no ETP leg and no ETP "
                       "costs (declared convention, addendum "
                       "selection_freeze_addendum_a7r1.json)"),
    }


def index_only_shadow(runner, ctx: dict,
                      arm_result: "ar.CellResult | None" = None
                      ) -> ShadowResult:
    """The mandatory index-only shadow on the SAME frozen
    representation as the arm (audit H1 remediation, pre-scored
    addendum ``selection_freeze_addendum_a7r1.json``).

    A4-P2: the arm's state source is index-only by the frozen
    state_source_law, so the shadow's DECISION STATE is the identical
    rule on the identical index inputs; the CONTROL is no longer the
    arm's own ETP book re-run (that degenerate control made R2's
    control_reproduces veto tautological -- audit H1 at 57d5d639): the
    control is the HYPOTHETICAL INDEX-POINT BOOK from
    ``index_point_book`` -- ``state`` units of the VIX close, marked in
    index points, V7 re-clock, NO ETP leg, NO ETP costs.  The control
    book is a genuinely different book from the arm's ETP book for
    every cell; ``distinct_from_arm`` is MEASURED at the book level
    whenever the arm's cell result is supplied (``arm_result``), and
    None otherwise (disclosed as not-measured, never assumed).

    A5-P2: UNCHANGED from the freeze's a5_p2_spec -- the shadow
    replaces BOTH realized sides with index-only proxies and its
    decision series is re-clocked onto the ETP buckets; its state MUST
    differ from the arm's (which consumes the event-adjusted ETP
    realized sides) -- distinctness is measured on the state, and the
    books then differ by the same construction."""
    family = runner.family_key
    if family == cfg.FAMILY_A4_P2:
        state = runner.build_state(ctx)
        book = index_point_book(ctx["grid"], state,
                                ctx["index"][cfg.SHADOW_MARK_SERIES])
        if arm_result is None:
            distinct = None    # arm book not supplied: not measured here
        else:
            distinct = books_distinct(book["round_trips"],
                                      arm_result.round_trips)
        decisions = book["decisions"]
        refused = book["refused_tail_decisions"]
        notes = {
            "state_source_law": ("index-only by the arm's own frozen "
                                 "state_source_law; the shadow's "
                                 "decision state equals the arm's state "
                                 "series by that law, but the shadow "
                                 "scores the HYPOTHETICAL index-point "
                                 "book, NOT the arm's ETP book (audit "
                                 "H1 remediation, addendum "
                                 "selection_freeze_addendum_a7r1.json)"),
            "control_book": ("hypothetical index-point book on the "
                             f"{cfg.SHADOW_MARK_SERIES} close (no ETP "
                             "leg, no ETP costs)"),
            "no_etp_price_in_state": True,
            "no_etp_price_in_book": True,
            "distinct_from_arm_law": _DISTINCT_LAW,
            "empty_book_note": ("if the arm book is empty the shadow "
                                "book is empty too (same decision "
                                "series): distinct_from_arm is then "
                                "None (unmeasurable, disclosed) and R2 "
                                "limb (a) is uncomputable at E: "
                                "fail-closed NOT_RUN, never an "
                                "inferred PASS"),
        }
    elif family == cfg.FAMILY_A5_P2:
        state = a5_index_only_state(ctx, runner.asym_threshold,
                                    runner.latch_sessions)
        # structural no-ETP proof: recompute on a permuted-ETP context --
        # the shadow state must be invariant
        ctx2 = dict(ctx)
        ctx2["adj"] = {leg: dict(reversed(sorted(s.items())))
                       for leg, s in ctx["adj"].items()}
        if a5_index_only_state(ctx2, runner.asym_threshold,
                               runner.latch_sessions) != state:
            raise BatteryError(
                "A5 index-only shadow depends on ETP data (fail-closed)")
        arm_state = runner.build_state(ctx)
        distinct = arm_state != state
        book = {}
        decisions, refused = ar.decisions_to_executions(ctx["grid"],
                                                        state)
        notes = {
            "short_side": f"realized_vol(VIX close, "
                          f"{cfg.A5_SHADOW_SHORT_LOOKBACK}) -- committed "
                          "proxy lookback",
            "mid_side": f"realized_vol(VIX close, "
                        f"{cfg.A5_SHADOW_MID_LOOKBACK}) -- the committed "
                        "MID day gap (longer-lookback variant of the "
                        "same index series)",
            "control_book": ("decision series re-clocked onto the ETP "
                             "buckets per the freeze's a5_p2_spec "
                             "(unchanged by the A7-R1 addendum; the "
                             "scored control book is built at E under "
                             "scored authority)"),
            "no_etp_price_in_state": True,
            "distinct_from_arm_law": ("state-level: the shadow state "
                                      "MUST differ from the arm state "
                                      "(which consumes the "
                                      "event-adjusted ETP realized "
                                      "sides); the books then differ by "
                                      "the same construction"),
        }
    else:
        raise BatteryError(f"family {family!r} has no index-only shadow")
    return ShadowResult(
        control="index_only_shadow",
        decision_state=state,
        decisions=decisions,
        refused_tail_decisions=refused,
        invalid_instants=sum(1 for d in ctx["grid"]
                             if state.get(d) is None),
        distinct_from_arm=distinct,
        notes=notes,
        book=book,
    )


# --------------------------------------------------------------------------- #
# calendar-clock shadow (k=5 grid sessions)
# --------------------------------------------------------------------------- #
def calendar_clock_shadow(runner, ctx: dict,
                          k: int = cfg.CALENDAR_SHIFT_K_SESSIONS) -> ShadowResult:
    """The same rule re-clocked to a fixed shift of k=5 grid sessions:
    the placement induced by state'[t] := state[t-k] (INVALID before the
    first shifted session).  A placement that survives the re-clock
    unchanged is a calendar artefact and dies (freeze spec):
    distinctness is measured on the COMMON VALID decision span (the
    decision sessions where BOTH the arm and the shifted series have
    decisions; the shift's k-session warm-up INVALID prefix is
    structural, not evidence of distinctness).  Identical placement on
    that span -> not distinct (calendar artefact)."""
    grid = ctx["grid"]
    state = runner.build_state(ctx)
    shifted: dict[str, float | None] = {}
    for i, d in enumerate(grid):
        shifted[d] = state.get(grid[i - k]) if i >= k else None
    decisions, refused = ar.decisions_to_executions(grid, shifted)
    arm_decisions, _ = ar.decisions_to_executions(grid, state)
    arm_by_d = {r["decision_session"]: r["state"] for r in arm_decisions}
    shadow_by_d = {r["decision_session"]: r["state"] for r in decisions}
    common = sorted(set(arm_by_d) & set(shadow_by_d))
    if not common:
        distinct = None          # unmeasurable on an empty overlap
    else:
        distinct = any(arm_by_d[d] != shadow_by_d[d] for d in common)
    return ShadowResult(
        control="calendar_clock_shadow",
        decision_state=shifted,
        decisions=decisions,
        refused_tail_decisions=refused,
        invalid_instants=sum(1 for d in grid if shifted.get(d) is None),
        distinct_from_arm=distinct,
        notes={"calendar_shift_k_sessions": k,
               "common_valid_decision_sessions": len(common),
               "distinctness_law": "measured on the common valid decision "
                                   "span; identical placement there is a "
                                   "calendar artefact (freeze spec)"},
    )


# --------------------------------------------------------------------------- #
# placebo (ORDSHUF-style order shuffle, frozen seed 20260912)
# --------------------------------------------------------------------------- #
def placebo(runner, ctx: dict,
            seed: int = cfg.PLACEBO_SEED) -> ShadowResult:
    """The arm's decision-state series time-shuffled with matched
    marginals and destroyed temporal ordering (ORDSHUF-style order
    shuffle), seeded ``numpy.random.default_rng(seed)`` frozen in the
    freeze (seed law per the FOREX-NG1 precedent).  A permutation
    preserves the value multiset EXACTLY (marginals matched, INVALID
    positions included) and destroys the temporal order."""
    grid = ctx["grid"]
    state = runner.build_state(ctx)
    series = [state.get(d) for d in grid]
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(series))
    shuffled_list = [series[int(i)] for i in perm]
    shuffled = {d: shuffled_list[i] for i, d in enumerate(grid)}
    # matched marginals: the sorted multiset must be identical
    def key(v):
        return "INVALID" if v is None else repr(float(v))
    if sorted(map(key, series)) != sorted(map(key, shuffled_list)):
        raise BatteryError("placebo marginals drifted (fail-closed)")
    decisions, refused = ar.decisions_to_executions(grid, shuffled)
    arm_rows = [(r["decision_session"], r["state"])
                for r in ar.decisions_to_executions(grid, state)[0]]
    shadow_rows = [(r["decision_session"], r["state"]) for r in decisions]
    distinct = (shadow_rows != arm_rows)
    return ShadowResult(
        control="placebo",
        decision_state=shuffled,
        decisions=decisions,
        refused_tail_decisions=refused,
        invalid_instants=sum(1 for d in grid if shuffled.get(d) is None),
        distinct_from_arm=distinct,
        notes={"placebo_seed": seed, "rng_kind": cfg.PLACEBO_RNG_KIND,
               "shuffle": "one default_rng permutation of the arm's "
                          "decision-state series over the grid "
                          "(marginals matched, temporal ordering "
                          "destroyed by construction)",
               "law": "a significant differential placement under the "
                      "placebo kills the arm (evaluated at E, scored)"},
    )


# --------------------------------------------------------------------------- #
# invalid-null distinction audit
# --------------------------------------------------------------------------- #
def invalid_null_audit(result: ar.CellResult) -> dict:
    """Q-11 audit on a cell result: an uncomputable state is INVALID,
    refused fail-closed, never coerced to flat/aligned and never scored
    as a decision.  Structural proofs: (a) no decision row's
    decision_session carries an INVALID state; (b) INVALID count equals
    the state series' None count; (c) no fill outside decision exec
    sessions (the window-tail closes are the disclosed exception and
    are counted)."""
    bad = [r for r in result.decisions
           if result.decision_state.get(r["decision_session"]) is None]
    state_invalid = sum(1 for v in result.decision_state.values()
                        if v is None)
    exec_sessions = {r["exec_session"] for r in result.decisions}
    tail_fills = [f for f in result.fills
                  if f["session"] not in exec_sessions]
    ok = (not bad
          and state_invalid == result.invalid_instants
          and all(f["kind"] == "exit_or_rebalance" for f in tail_fills))
    return {
        "control": "invalid_null_distinction",
        "verdict": "PASS" if ok else "FAIL",
        "invalid_instants": state_invalid,
        "decisions_from_invalid": len(bad),
        "window_tail_closes": len(tail_fills),
        "law": "uncomputable = INVALID, refused fail-closed, never "
               "coerced to NULL/flat/aligned, never scored (Q-11)",
    }


# --------------------------------------------------------------------------- #
# cost-path control (the measured path-cost ladder)
# --------------------------------------------------------------------------- #
def cost_path_control(result: ar.CellResult, cost_source: dict,
                      tiers: tuple = cfg.COST_TIER_LADDER) -> dict:
    """The mandatory cost-path control: the arm's OWN round trips
    (its measured rebalance count included) re-booked through the FULL
    measured path-cost ladder: execution spreads scaled through the
    committed tier ladder (tier 2.0 at the top), cost once per fill,
    plus the Q-16 roll/decay path component EXPLICIT at every tier
    (adverse tail x held sessions per leg; A5 rotations pay BOTH
    bucket formulas because every leg carries its own bucket line).
    Path/expense are MECHANISM lines: tier-invariant, never re-scaled.

    EXPENSE CONVENTION (audit M1 pin, EXPENSE_IN_NET_STRESS):
    ``net_stress_usd_total`` = gross - execution - Q-16 path - EXPENSE,
    matching the frozen P2 round-trip cost ceilings which INCLUDE the
    expense drag -- the two A4-P2 kill routes share ONE convention.

    Emits structural lines + per-tier totals on the SUPPLIED books
    (synthetic fixtures in I; real scored books only at E under
    authority)."""
    if tiers != cfg.COST_TIER_LADDER:
        raise BatteryError(
            f"tier ladder {tiers} != the committed ladder "
            f"{cfg.COST_TIER_LADDER}")
    legs = sorted({rt["leg"] for rt in result.round_trips})
    unknown = [l for l in legs if l not in cost_source]
    if unknown:
        raise BatteryError(f"cost source missing legs {unknown}")
    per_trip = []
    for i, rt in enumerate(result.round_trips):
        src = cost_source[rt["leg"]]
        exec_cost = {
            str(t): 2.0 * rt["notional_usd"]
            * (src["stress_spread_frac"] / 2.0) * t
            for t in tiers
        }
        once = acc.per_fill_cost_usd(rt["notional_usd"],
                                     src["stress_spread_frac"],
                                     cfg.PRIMARY_TIER)
        if abs(exec_cost[str(cfg.PRIMARY_TIER)] - 2.0 * once) > 1e-9:
            raise BatteryError(
                "execution cost not charged exactly once per fill "
                "(fail-closed)")
        path_line_usd = (rt["notional_usd"] / 1e4
                         * src["path_adverse_tail_daily_bps"]
                         * rt["held_sessions"])
        expense_line_usd = (rt["notional_usd"] / 1e4
                            * src["expense_bps_per_day"]
                            * rt["held_sessions"])
        per_trip.append({
            "round_trip_index": i,
            "leg": rt["leg"],
            "bucket": src["bucket"],
            "path_formula": src["path_formula"],
            "held_sessions": rt["held_sessions"],
            "execution_cost_usd_by_tier": exec_cost,
            "q16_path_line_usd_explicit": path_line_usd,
            "expense_line_usd_explicit": expense_line_usd,
        })
    totals = {}
    for t in tiers:
        exec_total = sum(p["execution_cost_usd_by_tier"][str(t)]
                         for p in per_trip)
        path_total = sum(p["q16_path_line_usd_explicit"] for p in per_trip)
        expense_total = sum(p["expense_line_usd_explicit"]
                            for p in per_trip)
        gross_total = sum(
            result.kernel_events[p["round_trip_index"]]["book"][
                "gross_pnl_usd"] for p in per_trip)
        totals[str(t)] = {
            "execution_cost_usd_total": exec_total,
            "q16_path_line_usd_total_explicit": path_total,
            "expense_line_usd_total_explicit": expense_total,
            # M1 convention pin: the expense drag IS included, matching
            # the frozen P2 round-trip cost ceilings (EXPENSE_IN_NET_STRESS).
            "net_stress_usd_total": gross_total - exec_total - path_total
            - expense_total,
            "primary": t == cfg.PRIMARY_TIER,
        }
    buckets = sorted({p["bucket"] for p in per_trip})
    return {
        "control": "cost_path_control",
        "n_round_trips": len(per_trip),
        "n_fills": 2 * len(per_trip),
        "rebalance_closes": sum(
            1 for rt in result.round_trips
            if rt["exit_reason"] == "rebalance"),
        "buckets_present": buckets,
        "both_bucket_paths_paid": (
            "SHORT" in buckets and "MID" in buckets),
        "per_round_trip": per_trip,
        "totals_by_tier": totals,
        "tier_ladder": list(tiers),
        "primary_tier": cfg.PRIMARY_TIER,
        "expense_in_net_stress": EXPENSE_IN_NET_STRESS,
        "q16_law": "path component explicit at every tier; tier ladder "
                   "scales execution frictions only (frozen contract); "
                   "net stress includes the explicit expense line, "
                   "matching the frozen P2 cost ceilings (audit M1 "
                   "convention pin, addendum "
                   "selection_freeze_addendum_a7r1.json)",
    }
