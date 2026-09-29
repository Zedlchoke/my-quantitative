"""Policy skeleton L1-L7 — PC12A implementation lane.

PORTFOLIO_POLICY_ARCHITECTURE.md layer map (skeleton scope for the dry-run
engine; Stage-B freezes the learned parameters):

L1 LEG POOL      the configured legs (identity-frozen)
L2 ELIGIBILITY   E1 floors / E3 staleness / E4 cost-budget -- PRE-TRADE
                 features ONLY (GROUPING_PROPOSAL 3.6 blacklist enforced)
L3 TARGETS       per-leg desired signed units (legs' own frozen rules)
L4 NETTING       per-asset risk-weight voters -> ONE net position
L5 RISK BUDGET   asset/cluster caps (frozen PLACEHOLDER map -- Stage-B
                 re-freezes from TRAIN co-movement)
L6 EXECUTION     next-bar-open fills, cost guard (defer non-urgent when
                 the trailing budget is exhausted; closes always allowed)
L7 STANDING OUT  W1 (no eligible legs -> FLAT) and W4 (unseen structure ->
                 fail-closed FLAT), typed.

GROUPING_PROPOSAL 3.6 (binding on this engine): L2/L3/L5 features are
computed from data <= (fold start - 1-week embargo) only; no future data,
no current-fold realized PnL, no regime-prediction variables, no
unevidenced inputs, no in-fold loss-taxonomy feedback.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 3.6 FORBIDDEN list (explicit, binding)
# ---------------------------------------------------------------------------

FEATURES_BLACKLIST: Tuple[str, ...] = (
    # 1. future data of any kind
    r"^future_data",
    r"_after_decision$",
    r"^bar_open_at_or_after_",
    # 2. current-fold realized PnL of any leg or the portfolio (fold-lock)
    r"_in_fold_pnl$",
    r"^current_fold_.*pnl",
    r"^realized_pnl",
    # 3. regime-prediction variables claiming forward-looking information
    r"^regime_prediction",
    r"^forecast_",
    r"_will_$",
    # 4. anything depending on test-fold outcomes
    r"^test_fold",
    r"_tuned_on_test$",
    # 5. unevidenced inputs (T3 list)
    r"^unevidenced_input",
    r"^consensus_",
    r"^cot_",
    r"^sofr",
    r"^sonia",
    # 6. in-fold loss-taxonomy feedback
    r"^loss_taxonomy_in_fold",
    r"^in_fold_loss_",
)

_BLACKLIST_RES = tuple(re.compile(p) for p in FEATURES_BLACKLIST)


class ForbiddenFeature(RuntimeError):
    """STOP-3-class trip: a forbidden feature tried to enter L2/L3/L5."""


def assert_features_lawful(feature_ids: List[str]) -> None:
    """Enforce GROUPING_PROPOSAL 3.6 at the engine's feature gate."""
    for fid in feature_ids:
        for rx in _BLACKLIST_RES:
            if rx.search(fid):
                raise ForbiddenFeature(
                    f"feature {fid!r} matches forbidden pattern {rx.pattern!r}"
                    f" (GROUPING_PROPOSAL 3.6)")


# ---------------------------------------------------------------------------
# L2 eligibility
# ---------------------------------------------------------------------------


@dataclass
class LegRuntimeStats:
    """Trailing pre-trade statistics (lawful L2 inputs only).

    decision_count_trailing: executed-entry count over the trailing window
    cost_bill_trailing_usd:  the leg's crossing+commission+swap bill
    """

    leg_start_ts: Optional[dt.datetime] = None
    decision_count_trailing: int = 0
    cost_bill_trailing_usd: float = 0.0
    decisions_total: int = 0
    cost_events: List[Tuple[dt.datetime, float]] = field(
        default_factory=list)
    decision_events: List[dt.datetime] = field(default_factory=list)


@dataclass(frozen=True)
class EligibilityVerdict:
    state: str                    # ON | PROBATION | OFF
    rule_id: Optional[str]        # E1/E3/E4/None
    detail: str


class Eligibility:
    """L2 skeleton: E1 floors, E3 staleness, E4 cost-budget.

    E1 (floors): trailing decision count < 3 over the trailing 26w window
    -> NOT_RUN_THIN FLAT -- ARMED only after the leg has a full 26w of
    history (otherwise a new leg could never accumulate decisions).
    E3 (staleness): any PIT input with max_age_ok False -> OFF
    (fail-closed, never last-known-value).
    E4 (cost budget): the leg's trailing 4w cost bill exceeds its frozen
    share cap -> OFF until the window rolls (monthly reset semantics).

    Features consumed here are ALL pre-trade (counts, cost bills, snapshot
    freshness); PnL never enters (E5 law).
    """

    E1_MIN_DECISIONS_26W = 3
    E1_ARM_WEEKS = 26
    E4_WINDOW_DAYS = 28
    E4_CAP_USD = 2_500.0  # frozen PLACEHOLDER (Stage-B re-freezes from the
    # TRAIN switching-cost ladder; sized so the dry-run smoke is not
    # guard-distorted while the defer path stays unit-tested)

    def evaluate(self, leg_id: str, stats: LegRuntimeStats,
                 pit_snapshot: List[Dict],
                 now: dt.datetime) -> EligibilityVerdict:
        assert_features_lawful([
            f"decision_count_trailing:{leg_id}",
            f"cost_bill_trailing:{leg_id}",
            f"pit_freshness:{leg_id}",
        ])
        for snap in pit_snapshot:
            if not snap.get("max_age_ok", True):
                return EligibilityVerdict(
                    "OFF", "E3",
                    f"E3: PIT input {snap.get('input_id')} stale at "
                    f"{now.isoformat()}")
            # PIT join law (campaign §8.2): an input claiming availability
            # AFTER the decision instant is future data -- fail closed, and
            # an unparseable availability stamp is unverifiable -> E3 too.
            av = snap.get("available_time_utc")
            if isinstance(av, str):
                try:
                    av_ts = dt.datetime.strptime(
                        av, "%Y-%m-%dT%H:%M:%SZ").replace(
                            tzinfo=dt.timezone.utc)
                except ValueError:
                    av_ts = None
                if av_ts is None or av_ts > now:
                    return EligibilityVerdict(
                        "OFF", "E3",
                        f"E3: PIT input {snap.get('input_id')} "
                        f"available_time {av!r} not verifiably <= "
                        f"decision {now.isoformat()} -> fail closed")
        w26 = now - dt.timedelta(weeks=self.E1_ARM_WEEKS)
        if stats.leg_start_ts is not None and stats.leg_start_ts <= w26:
            trailing = sum(1 for t in stats.decision_events
                           if t > w26)
            if trailing < self.E1_MIN_DECISIONS_26W:
                return EligibilityVerdict(
                    "OFF", "E1",
                    f"E1: {trailing} decisions in trailing 26w < "
                    f"{self.E1_MIN_DECISIONS_26W} -> NOT_RUN_THIN FLAT")
        w4 = now - dt.timedelta(days=self.E4_WINDOW_DAYS)
        bill = sum(c for t, c in stats.cost_events if t > w4)
        if bill > self.E4_CAP_USD:
            return EligibilityVerdict(
                "OFF", "E4",
                f"E4: trailing {self.E4_WINDOW_DAYS}d cost bill "
                f"{bill:.2f} > cap {self.E4_CAP_USD:.2f}")
        return EligibilityVerdict("ON", None, "eligible")


# ---------------------------------------------------------------------------
# L4 netting
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class NettingOutcome:
    net_target_units: int
    tie_zero: bool
    contributions: Dict[str, int]     # leg_id -> signed desired units
    offsets: Dict[str, List[str]]


class Netting:
    """Per-asset risk-weight voters -> net target truncated to +/-1 lot.

    A leg may not offset itself; ties (net = 0 with nonzero votes) leave
    the asset FLAT and are journaled NETTED_TO_ZERO (blocked-signal rows).
    """

    LOT_UNITS = 100_000

    def net(self, desires: Dict[str, int]) -> NettingOutcome:
        raw = sum(desires.values())
        if raw > self.LOT_UNITS:
            net = self.LOT_UNITS
        elif raw < -self.LOT_UNITS:
            net = -self.LOT_UNITS
        else:
            net = raw
        nonzero = {k: v for k, v in desires.items() if v != 0}
        tie = net == 0 and bool(nonzero)
        offsets = {}
        for lid in desires:
            offsets[lid] = [o for o, v in desires.items()
                            if o != lid and (v * desires[lid] < 0)]
        return NettingOutcome(net, tie, dict(desires), offsets)


# ---------------------------------------------------------------------------
# L5 risk budget (frozen PLACEHOLDER map -- Stage-B re-freezes)
# ---------------------------------------------------------------------------

FROZEN_CLUSTER_MAP_PLACEHOLDER: Dict[str, int] = {
    # cluster_id -> max |net units| per asset in the cluster (PLACEHOLDER:
    # to be frozen at Stage-B from measured TRAIN co-movement).
    # Verification-lane fix (arm-distinctness battery): keys are the
    # cluster_ids of the 12 FROZEN leg configs (full mech-key spelling,
    # e.g. "volprof_vc1_vaedge"); the earlier short spellings never
    # matched any config, leaving L5 silently inert for the 9 VOLPROF
    # legs (the .get(cid, cap) fallback masked the miss).
    "volprof_vc1_vaedge": 100_000,
    "volprof_vc2_lvnfail": 100_000,
    "volprof_vc3_pocmag": 100_000,
    "trend_daily": 100_000,
    "calendar_weekday": 100_000,
}
PER_ASSET_NET_CAP_UNITS = 100_000


class ClusterCaps:
    """L5 skeleton: per-asset one-way net cap + cluster map lookup."""

    def clamp(self, net_units: int,
              cluster_ids: List[str]) -> Tuple[int, Optional[str]]:
        cap = PER_ASSET_NET_CAP_UNITS
        for cid in cluster_ids:
            cap = min(cap, FROZEN_CLUSTER_MAP_PLACEHOLDER.get(cid, cap))
        if abs(net_units) > cap:
            reason = f"L5: cluster/asset cap {cap} units"
            return (cap if net_units > 0 else -cap), reason
        return net_units, None


# ---------------------------------------------------------------------------
# L6 execution: cost guard
# ---------------------------------------------------------------------------


@dataclass
class CostGuardState:
    window_days: int = 28
    cap_usd: float = 2_500.0  # frozen PLACEHOLDER (Stage-B: TRAIN ladder)
    spend: List[Tuple[dt.datetime, float]] = field(default_factory=list)


@dataclass(frozen=True)
class GuardVerdict:
    allow: bool
    trailing_spend_usd: float
    in_window_items: List[Tuple[dt.datetime, float]]
    urgency: str
    reason: str


class CostGuard:
    """Defer NON-URGENT size changes when the trailing state-change cost
    budget is exhausted; risk-REDUCING closes are always allowed (R1)."""

    def __init__(self, state: CostGuardState):
        self.state = state

    def evaluate(self, now: dt.datetime, current_units: int,
                 target_units: int, est_total_usd: float) -> GuardVerdict:
        wstart = now - dt.timedelta(days=self.state.window_days)
        # PIT law (campaign §8.1, verification-lane fix): only spends with
        # timestamp <= the decision instant may enter the trailing sum.
        # The guard is shared across symbol engines that run sequentially,
        # so the spend list can already contain FUTURE-dated entries when
        # an earlier instant of another symbol is evaluated; summing them
        # leaked post-decision spends into a past decision.
        in_win = [(t, c) for t, c in self.state.spend
                  if wstart < t <= now]
        trailing = sum(c for _, c in in_win)
        risk_reducing = abs(target_units) < abs(current_units) or (
            current_units * target_units < 0 and abs(target_units)
            <= abs(current_units))
        urgent = "RISK_REDUCING_CLOSE" if risk_reducing else \
            "NON_URGENT_INCREASE"
        if trailing >= self.state.cap_usd and not risk_reducing:
            return GuardVerdict(False, trailing, in_win, urgent,
                                f"L6 cost guard: trailing "
                                f"{self.state.window_days}d spend "
                                f"{trailing:.4f} >= cap "
                                f"{self.state.cap_usd:.2f}")
        return GuardVerdict(True, trailing, in_win, urgent,
                            f"guard open (trailing {trailing:.4f})")

    def record_spend(self, ts: dt.datetime, usd: float) -> None:
        self.state.spend.append((ts, usd))


# ---------------------------------------------------------------------------
# L7 standing out (typed)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class StandingOutEvent:
    code: str      # W1_NO_ELIGIBLE_LEGS | W4_UNSEEN_STRUCTURE
    detail: str


def w1_check(eligible_leg_ids: List[str]) -> Optional[StandingOutEvent]:
    """W1: no eligible legs -> portfolio FLAT (typed event)."""
    if not eligible_leg_ids:
        return StandingOutEvent(
            "W1_NO_ELIGIBLE_LEGS",
            "all legs OFF/PROBATION-exhausted -> portfolio FLAT")
    return None


def w4_check(ctx_values: Dict[str, float]) -> Optional[StandingOutEvent]:
    """W4: any input outside its frozen domain -> fail-closed FLAT."""
    for k, v in ctx_values.items():
        dom = KNOWN_INPUT_DOMAINS.get(k)
        if dom is None:
            return StandingOutEvent(
                "W4_UNSEEN_STRUCTURE",
                f"input {k!r} outside frozen domain -> asset FLAT")
        lo, hi = dom
        if not (lo <= v <= hi):
            return StandingOutEvent(
                "W4_UNSEEN_STRUCTURE",
                f"input {k!r} value {v} outside frozen domain "
                f"[{lo}, {hi}] -> asset FLAT")
    return None


KNOWN_INPUT_DOMAINS: Dict[str, tuple] = {
    # frozen at registration from the Lane D audit (panels 2021-01-01..
    # 2026-09-23; sane price bands per pair)
    "EURUSD_mid_range": (0.85, 1.35),
    "GBPUSD_mid_range": (0.95, 1.60),
    "USDJPY_mid_range": (95.0, 200.0),
    "spread_pips_max": (0.0, 60.0),
}
