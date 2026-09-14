"""VOL-NG1 I-phase per-family decision-rule runners (frozen cells).

Two frozen rule families, implemented EXACTLY as declared in the
binding selection freeze (research/control/vol_ng1_run/s/
selection_freeze.json, sections selected_families +
arm_configuration_plan):

- ``SlopeAccelerationRunner``  (VOLNG1-A4-P2,
  family_form slope_second_difference_regime): frozen latch axis
  latch_m_sessions in {2,3,4} at d_threshold 0.0; the decision state is
  computed from same-session VIX9D/VIX/VIX3M index closes ONLY;
  latch law +1/-1/0 over the trailing m valid second differences, any
  INVALID inside the trailing window -> INVALID (fail-closed, Q-11).
- ``PremiumAsymmetryRunner``   (VOLNG1-A5-P2,
  family_form premium_state_asymmetry_short_vs_mid): frozen
  (asym_threshold, latch_sessions) axis {(0.5,2),(0.75,3),(0.25,1)};
  ASYM = SPREAD_short - SPREAD_mid with
  SPREAD_bucket = expanding-z(VIX close) - expanding-z(realized vol of
  the bucket proxy leg's event-adjusted close, 21 sessions, x
  sqrt(252)); debounce/hysteresis latch on the coded state; INVALID
  passes through untouched (fail-closed, Q-11).

Laws wired through the frozen assets (consumed, never modified):

- LEG CONSUMPTION: every ETP leg series is consumed ONLY through
  ``research.assets.vol_ng1.corp_actions.event_adjusted_closes`` -- the
  mandatory P1 event-adjusted layer (never raw, never
  vendor-adjusted).  ``build_context_from_raw`` refuses uncovered
  mechanical steps (fail-closed) before any runner sees the series.
- DECISION-INSTANT LAW: V7 close+1 (``research.assets.vol_ng1.clocks``):
  a state observed at the close of session t is executable at the NEXT
  grid session; the final grid session is refused as a decision instant;
  never same-bar.
- STATE BUILDERS: the D2 committed builders
  (``research.control.vol_ng1_run.d2.d2_novelty``) are re-used
  UNCHANGED as the anchor parameterization, per the freeze's
  parameter_freeze_rationale; neighbour arms move ONLY the frozen axes
  through the same primitives.
- KERNEL EVENTS: round trips are booked through the P1 dual-book
  accounting kernel ``research.assets.vol_ng1.accounting``
  (tier ladder {1.0,1.5,2.0}, tier 2.0 PRIMARY, cost charged exactly
  once per fill).  The Q-16 roll/decay path component and the expense
  drag are carried as EXPLICIT per-round-trip mechanism lines, never
  folded into the fills (kernel law).

NO scoring, NO outcome numbers on real data: the runners emit decision
series + structural fills + kernel books only.  Scored expectancy/PF
metrics are supplied EXTERNALLY at E under scored authority.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.vol_ng1 import accounting as acc          # noqa: E402
from research.assets.vol_ng1 import clocks as ck               # noqa: E402
from research.assets.vol_ng1 import corp_actions as ca         # noqa: E402
from research.assets.vol_ng1 import feasibility as fb          # noqa: E402
from research.assets.vol_ng1.runners import config as cfg      # noqa: E402
from research.control.vol_ng1_run.d2 import d2_novelty as dn   # noqa: E402

SCHEMA = "vol_ng1_runners/arms@1"


class RunnerError(Exception):
    """Fail-closed runner error: nothing inferred, nothing repaired."""


# --------------------------------------------------------------------------- #
# context assembly (leg consumption ONLY through the event-adjusted layer)
# --------------------------------------------------------------------------- #
def build_context_from_raw(
        grid_index_closes: dict[str, dict[str, float]],
        raw_bars_by_leg: dict[str, list[dict]],
        events_by_leg: dict[str, list[dict]],
        leg_subset: tuple[str, ...]) -> dict:
    """Runner context whose ETP series are built through the ONLY
    lawful layer: ``corp_actions.event_adjusted_closes``.  Fails closed
    on any uncovered mechanical step (the P0 inventory law) -- a caller
    that cannot produce explicit event decisions has no lawful leg
    series here."""
    adj: dict[str, dict[str, float]] = {}
    for leg in leg_subset:
        bars = raw_bars_by_leg.get(leg)
        events = events_by_leg.get(leg)
        if bars is None or events is None:
            raise RunnerError(
                f"leg {leg}: raw bars + explicit event decisions are "
                "required (consumption is ONLY through the "
                "event-adjusted layer)")
        uncovered = ca.scan_uncovered_steps(bars, events)
        if uncovered:
            raise RunnerError(
                f"leg {leg}: uncovered raw steps {uncovered} "
                "(fail-closed)")
        adj[leg] = ca.event_adjusted_closes(bars, events)
    return {
        "index": grid_index_closes,
        "adj": adj,
        "leg_subset": tuple(leg_subset),
        "proxy_leg": fb.PROXY_LEG,
        "proxy_lookback_sessions": fb.PROXY_LOOKBACK_SESSIONS,
        "proxy_annualization": fb.PROXY_ANNUALIZATION,
    }


def grid_of(ctx: dict) -> list[str]:
    """The common decision grid of a context: the strict intersection
    of every consumed series' dates (indices + event-adjusted legs),
    sorted (bar-readable sessions only)."""
    series = list(ctx["index"].values()) + list(ctx["adj"].values())
    if not series:
        raise RunnerError("empty context: no consumed series")
    common = set(series[0])
    for s in series[1:]:
        common &= set(s)
    if not common:
        raise RunnerError("empty common grid across consumed series")
    return sorted(common)


# --------------------------------------------------------------------------- #
# V7 close+1 decision-instant law
# --------------------------------------------------------------------------- #
def decisions_to_executions(
        grid: list[str],
        state_by_date: dict[str, float | None]) -> tuple:
    """V7 close+1: every grid session whose state is computable (not
    INVALID) is a decision at its close, executable at the NEXT grid
    session.  The final grid session is refused as a decision instant
    (no next readable bar; ``clocks.next_session`` raises).  Returns
    rows {decision_session, exec_session, state}; INVALID never becomes
    a decision (Q-11) and is counted separately by the caller."""
    rows = []
    refused_tail = 0
    for d in grid:
        s = state_by_date.get(d)
        if s is None:
            continue                      # INVALID: refused, never coerced
        try:
            nxt = ck.next_session(grid, d)
        except ck.ClockError:
            refused_tail += 1             # final grid session (V7 law)
            continue
        rows.append({"decision_session": d, "exec_session": nxt,
                     "state": float(s)})
    return rows, refused_tail



# --------------------------------------------------------------------------- #
# runners
# --------------------------------------------------------------------------- #
class SlopeAccelerationRunner:
    """VOLNG1-A4-P2 (slope_second_difference_regime), frozen latch axis
    {2,3,4} + latch at d_threshold 0.0.

    State (D2 committed primitives, unchanged):
      S_t = 0.5*(ln(VIX_t/VIX9D_t) + ln(VIX3M_t/VIX_t))
      D_t = S_t - 2 S_(t-1) + S_(t-2)
      state = +1 when the trailing m valid D-values are all > 0
              (accelerating steepening), -1 when all < 0 (accelerating
              flattening), else 0; any INVALID in the trailing window
              -> INVALID (fail-closed).
    Note the frozen functional algebraically reduces to
    0.5*(ln VIX3M_t - ln VIX9D_t): the VIX close cancels.  The runner
    consumes all three granted index closes exactly as declared and
    this identity is disclosed (tested as an invariance, not exploited).
    Placement: equal weight across the frozen SHORT-bucket leg subset,
    signed by the state (action_pole_encoding short_vol_pole +1 /
    long_vol_pole -1).
    """

    family_key = cfg.FAMILY_A4_P2
    family_form = "slope_second_difference_regime"
    decision_axis = "short_vol_pos_long_vol_neg"

    def __init__(self, arm_id: str, arm_config: dict):
        if arm_config.get("family_form") != self.family_form:
            raise RunnerError(
                f"{arm_id}: config family_form "
                f"{arm_config.get('family_form')!r} != {self.family_form!r}")
        self.arm_id = arm_id
        self.latch_m_sessions = int(arm_config["latch_m_sessions"])
        self.d_threshold = float(arm_config["d_threshold"])
        if self.latch_m_sessions not in cfg.A4_LATCH_M_AXIS:
            raise RunnerError(
                f"{arm_id}: latch_m_sessions {self.latch_m_sessions} "
                f"outside the frozen axis {cfg.A4_LATCH_M_AXIS}")
        self.leg_subset = tuple(arm_config["leg_subset"])

    def build_state(self, ctx: dict) -> dict[str, float | None]:
        grid = ctx["grid"]
        s_by_date: dict[str, float | None] = {}
        for d in grid:
            s9 = ctx["index"]["VIX9D"].get(d)
            vx = ctx["index"]["VIX"].get(d)
            v3 = ctx["index"]["VIX3M"].get(d)
            s_by_date[d] = None if None in (s9, vx, v3) else dn.slope_state(
                s9, vx, v3)
        d_by_date = dn.second_difference(s_by_date, grid)
        state = dn.regime_by_run(d_by_date, grid, self.latch_m_sessions,
                                 self.d_threshold)
        return state

    def target_weights(self, state: float) -> dict[str, float]:
        w = float(state) / len(self.leg_subset)
        return {leg: w for leg in self.leg_subset}


class PremiumAsymmetryRunner:
    """VOLNG1-A5-P2 (premium_state_asymmetry_short_vs_mid), frozen
    (asym_threshold, latch_sessions) axis {(0.5,2),(0.75,3),(0.25,1)}.

    State (D2 committed composition, unchanged; the C8 implied-complex
    limitation travels with every artifact of this family):
      rv_bucket  = trailing 21-common-grid-session realized vol of the
                   bucket proxy leg's EVENT-ADJUSTED close x sqrt(252)
                   (short proxy leg VXX, mid reference leg VXZ);
      SPREAD_bkt = expanding-z(VIX close) - expanding-z(rv_bucket)
                   (min history 63, ddof=0);
      ASYM       = SPREAD_short - SPREAD_mid;
      raw state  = short_extreme (+1) when ASYM > thr,
                   mid_extreme (-1) when ASYM < -thr, else aligned (0);
      state      = debounce/hysteresis latch: a change is adopted only
                   after latch_sessions consecutive valid sessions;
                   INVALID passes through untouched (fail-closed, Q-11).
    Placement (bucket_map): +s/n_front on each front-bucket leg,
    -s/n_mid on each mid-bucket leg (front_bucket_pole +1 /
    mid_bucket_pole -1).
    """

    family_key = cfg.FAMILY_A5_P2
    family_form = "premium_state_asymmetry_short_vs_mid"
    decision_axis = "front_bucket_pos_mid_bucket_neg"

    def __init__(self, arm_id: str, arm_config: dict):
        if arm_config.get("family_form") != self.family_form:
            raise RunnerError(
                f"{arm_id}: config family_form "
                f"{arm_config.get('family_form')!r} != {self.family_form!r}")
        self.arm_id = arm_id
        self.asym_threshold = float(arm_config["asym_threshold"])
        self.latch_sessions = int(arm_config["latch_sessions"])
        if (self.asym_threshold, self.latch_sessions) not in \
                set(cfg.A5_ARM_AXES.values()):
            raise RunnerError(
                f"{arm_id}: (asym_threshold, latch_sessions) "
                f"{(self.asym_threshold, self.latch_sessions)} outside "
                f"the frozen axis {sorted(cfg.A5_ARM_AXES.values())}")
        self.leg_subset = tuple(arm_config["leg_subset"])
        self.bucket_map = {
            "front": tuple(arm_config["bucket_map"]["front"]),
            "mid": tuple(arm_config["bucket_map"]["mid"]),
        }
        self.proxy_leg_short = str(arm_config["proxy_leg_short_bucket"])
        self.mid_reference_leg = str(arm_config["mid_reference_leg"])

    def _spread_state(self, ctx: dict, proxy_leg: str) -> dict[str, float | None]:
        """The declared spread functional (identical composition to the
        D2 builder's ``_spread_state``, on this arm's frozen axis)."""
        grid = ctx["grid"]
        z_impl = dn.expanding_z(
            {d: ctx["index"]["VIX"].get(d) for d in grid}, grid,
            int(ctx.get("standardization_min_history",
                        dn.FROZEN_DEFAULTS["standardization_min_history"])))
        rv = dn.realized_vol(ctx["adj"][proxy_leg], grid,
                             ctx["proxy_lookback_sessions"],
                             ctx["proxy_annualization"])
        z_rv = dn.expanding_z(rv, grid,
                              int(ctx.get(
                                  "standardization_min_history",
                                  dn.FROZEN_DEFAULTS[
                                      "standardization_min_history"])))
        spread: dict[str, float | None] = {}
        for d in grid:
            a, b = z_impl.get(d), z_rv.get(d)
            spread[d] = None if (a is None or b is None) else a - b
        return spread

    def build_state(self, ctx: dict) -> dict[str, float | None]:
        grid = ctx["grid"]
        spread_short = self._spread_state(ctx, self.proxy_leg_short)
        spread_mid = self._spread_state(ctx, self.mid_reference_leg)
        asym: dict[str, float | None] = {}
        for d in grid:
            a, b = spread_short.get(d), spread_mid.get(d)
            asym[d] = None if (a is None or b is None) else a - b
        raw = dn.threshold_states(asym, grid, self.asym_threshold,
                                  "short_extreme", "mid_extreme", "aligned")
        codes: dict[str, float | None] = {}
        for d in grid:
            r = raw[d]
            codes[d] = None if r is None else {
                "short_extreme": 1.0, "aligned": 0.0,
                "mid_extreme": -1.0}[r]
        return dn.debounce_latch(codes, grid, self.latch_sessions)

    def target_weights(self, state: float) -> dict[str, float]:
        s = float(state)
        w: dict[str, float] = {}
        for leg in self.bucket_map["front"]:
            w[leg] = s / len(self.bucket_map["front"])
        for leg in self.bucket_map["mid"]:
            w[leg] = -s / len(self.bucket_map["mid"])
        return w


RUNNER_CLASSES = {
    cfg.FAMILY_A4_P2: SlopeAccelerationRunner,
    cfg.FAMILY_A5_P2: PremiumAsymmetryRunner,
}


def runner_for_arm(arm: dict) -> SlopeAccelerationRunner \
        | PremiumAsymmetryRunner:
    """Build the frozen family runner for one assembled arm."""
    klass = RUNNER_CLASSES.get(arm["family_key"])
    if klass is None:
        raise RunnerError(
            f"no runner class for family {arm['family_key']!r}")
    return klass(arm["arm_id"], arm["config"])


# --------------------------------------------------------------------------- #
# cell execution: fills, round trips, kernel events, mechanism lines
# --------------------------------------------------------------------------- #
@dataclass
class CellResult:
    arm_id: str
    family_key: str
    grid: list[str]
    decision_state: dict = field(default_factory=dict)
    decisions: list = field(default_factory=list)
    fills: list = field(default_factory=list)
    round_trips: list = field(default_factory=list)
    kernel_events: list = field(default_factory=list)
    mechanism_lines: list = field(default_factory=list)
    refused_tail_decisions: int = 0
    invalid_instants: int = 0
    meta: dict = field(default_factory=dict)


def run_cell(runner, ctx: dict, cost_source: dict,
             notional_usd_unit: float = cfg.NOTIONAL_USD_UNIT) -> CellResult:
    """Execute one frozen cell on a context: decision series (V7
    close+1 re-clock), structural fills, round trips booked through the
    P1 kernel (cost once per fill, tier ladder, tier 2.0 PRIMARY), and
    explicit Q-16/expense mechanism lines (recorded, never folded into
    the books).  Structural plumbing only -- NO outcome number."""
    grid = ctx["grid"]
    grid_index = {d: i for i, d in enumerate(grid)}
    for leg in runner.leg_subset:
        if leg not in ctx["adj"]:
            raise RunnerError(
                f"leg {leg}: no event-adjusted series in the context "
                "(leg consumption is ONLY through the event-adjusted "
                "layer)")
    state = runner.build_state(ctx)
    invalid_instants = sum(1 for d in grid if state.get(d) is None)
    decisions, refused_tail = decisions_to_executions(grid, state)

    folds = cfg.frozen_folds()
    fills: list[dict] = []
    round_trips: list[dict] = []
    kernel_events: list[dict] = []
    mechanism_lines: list[dict] = []
    open_pos: dict[str, dict] = {}

    def _close(leg: str, exec_session: str, price: float, reason: str) -> None:
        pos = open_pos.pop(leg)
        fills.append({"leg": leg, "session": exec_session,
                      "weight": pos["weight"],
                      "kind": "exit_or_rebalance"})
        rt = {
            "leg": leg,
            "direction": pos["direction"],
            "entry_session": pos["session"],
            "entry_price": pos["price"],
            "exit_session": exec_session,
            "exit_price": price,
            "exit_reason": reason,
            "fold": pos["fold"],
            "held_sessions": grid_index[exec_session]
                             - grid_index[pos["session"]],
            "notional_usd": pos["notional_usd"],
            "bucket": cost_source[leg]["bucket"],
        }
        round_trips.append(rt)
        book = acc.book_round_trip(
            direction=rt["direction"],
            notional_usd=rt["notional_usd"],
            entry_price=rt["entry_price"],
            exit_price=rt["exit_price"],
            stress_spread_frac=cost_source[leg]["stress_spread_frac"])
        kernel_events.append({
            "round_trip_index": len(round_trips) - 1,
            "leg": leg,
            "fold": rt["fold"],
            "book": book,
            "primary_book": acc.PRIMARY_TIER,
            "cost_once_per_fill": True,
        })
        tail = cost_source[leg]["path_adverse_tail_daily_bps"]
        exp = cost_source[leg]["expense_bps_per_day"]
        mechanism_lines.append({
            "round_trip_index": len(round_trips) - 1,
            "leg": leg,
            "bucket": rt["bucket"],
            "path_formula": cost_source[leg]["path_formula"],
            "q16_path_adverse_tail_daily_bps": tail,
            "held_sessions": rt["held_sessions"],
            "q16_path_line_bps": tail * rt["held_sessions"],
            "expense_bps_per_day": exp,
            "expense_line_bps": exp * rt["held_sessions"],
            "recorded_not_booked": True,
        })

    for row in decisions:
        exec_session = row["exec_session"]
        weights = runner.target_weights(row["state"])
        for leg in sorted(set(open_pos) | set(weights)):
            w_new = weights.get(leg, 0.0)
            w_old = open_pos[leg]["weight"] if leg in open_pos else 0.0
            if w_new == w_old:
                continue
            price = ctx["adj"][leg].get(exec_session)
            if price is None or price <= 0:
                raise RunnerError(
                    f"leg {leg}: no positive event-adjusted close at "
                    f"execution session {exec_session} (fail-closed)")
            if leg in open_pos:
                _close(leg, exec_session, price,
                       "rebalance" if w_new != 0.0 else "signal_flat")
            if w_new != 0.0:
                try:
                    fold = cfg.fold_of(exec_session, folds)
                except cfg.ConfigError as exc:
                    raise RunnerError(
                        f"execution session {exec_session} outside the "
                        "frozen fold windows (fail-closed)") from exc
                open_pos[leg] = {
                    "weight": w_new,
                    "direction": 1 if w_new > 0 else -1,
                    "notional_usd": notional_usd_unit * abs(w_new),
                    "session": exec_session,
                    "price": price,
                    "fold": fold,
                }
                fills.append({"leg": leg, "session": exec_session,
                              "weight": w_new, "kind": "entry_or_rebalance"})
    # window tail: still-open positions close at the LAST grid session
    # (disclosed forex-NG1 I precedent convention; no decision inferred)
    last = grid[-1]
    for leg in sorted(open_pos):
        price = ctx["adj"][leg].get(last)
        if price is None or price <= 0:
            raise RunnerError(
                f"leg {leg}: no close at window tail {last} (fail-closed)")
        _close(leg, last, price, "forced_window_end")

    if open_pos:
        raise RunnerError("unclosed positions after window tail")
    ids = [(e["leg"], e["round_trip_index"]) for e in kernel_events]
    if len(set(ids)) != len(ids):
        raise RunnerError("duplicate kernel event identity (fail-closed)")
    result = CellResult(
        arm_id=runner.arm_id,
        family_key=runner.family_key,
        grid=grid,
        decision_state=state,
        decisions=decisions,
        fills=fills,
        round_trips=round_trips,
        kernel_events=kernel_events,
        mechanism_lines=mechanism_lines,
        refused_tail_decisions=refused_tail,
        invalid_instants=invalid_instants,
    )
    result.meta = {
        "grid_sessions": len(grid),
        "decisions": len(decisions),
        "invalid_instants": invalid_instants,
        "refused_tail_decisions": refused_tail,
        "fills": len(fills),
        "round_trips": len(round_trips),
        "kernel_events": len(kernel_events),
        "by_exit_reason": _count(r["exit_reason"] for r in round_trips),
        "by_fold": _count(str(r["fold"]) for r in round_trips),
        "legs": sorted(runner.leg_subset),
        "primary_tier": acc.PRIMARY_TIER,
    }
    return result


def _count(values) -> dict:
    out: dict = {}
    for v in values:
        out[v] = out.get(v, 0) + 1
    return out
