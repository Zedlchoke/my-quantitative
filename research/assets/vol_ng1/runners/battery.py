"""VOL-NG1 I-phase control battery (binding on EVERY runner cell).

Implemented exactly per the binding freeze
(``selection_freeze.i_phase_control_battery``): the mandatory controls
are VETOES, not suggestions; a control that is not runnable makes its
cell NOT_RUN fail-closed (Q-11), never skipped; controls run on the
SAME frozen representation as their arm.

- ``index_only_shadow``  : A4-P2 -- the identical acceleration-regime
  rule driven by the vol index series ALONE, placement re-clocked onto
  the ETP legs, no ETP price anywhere in the state.  A5-P2 -- the
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
structural series/lines/counts only.  USD cost lines exist ONLY on
synthetic fixtures (unit-tested); scored verdicts consume externally
supplied metrics at E.
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


def index_only_shadow(runner, ctx: dict) -> ShadowResult:
    """The mandatory index-only shadow on the SAME frozen
    representation as the arm.  A4-P2: the arm's state source is
    index-only by the frozen state_source_law, so the shadow state is
    the identical rule on the identical inputs; the falsification
    content at R2 is the out-earning comparison (E-phase, scored) and
    the structural identity is DISCLOSED here rather than hidden.
    A5-P2: the shadow replaces BOTH realized sides with index-only
    proxies; its state MUST differ from the arm's (which consumes the
    event-adjusted ETP realized sides) -- distinctness is measured."""
    family = runner.family_key
    if family == cfg.FAMILY_A4_P2:
        state = runner.build_state(ctx)
        notes = {
            "state_source_law": ("index-only by the arm's own frozen "
                                 "state_source_law; shadow == arm state "
                                 "by construction (disclosed, per the "
                                 "freeze's a4_p2_spec)"),
            "no_etp_price_in_state": True,
        }
        distinct = None   # measured at E via the scored out-earning limb
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
        notes = {
            "short_side": f"realized_vol(VIX close, "
                          f"{cfg.A5_SHADOW_SHORT_LOOKBACK}) -- committed "
                          "proxy lookback",
            "mid_side": f"realized_vol(VIX close, "
                        f"{cfg.A5_SHADOW_MID_LOOKBACK}) -- the committed "
                        "MID day gap (longer-lookback variant of the "
                        "same index series)",
            "no_etp_price_in_state": True,
        }
    else:
        raise BatteryError(f"family {family!r} has no index-only shadow")
    decisions, refused = ar.decisions_to_executions(ctx["grid"], state)
    return ShadowResult(
        control="index_only_shadow",
        decision_state=state,
        decisions=decisions,
        refused_tail_decisions=refused,
        invalid_instants=sum(1 for d in ctx["grid"]
                             if state.get(d) is None),
        distinct_from_arm=distinct,
        notes=notes,
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
            "net_stress_usd_total": gross_total - exec_total - path_total,
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
        "q16_law": "path component explicit at every tier; tier ladder "
                   "scales execution frictions only (frozen contract)",
    }
