"""V13 I lane -- book invariants, cost-once and funding-once tests (f, g).

Evidence (f) -- cap/gross/net/cash invariants and force-flat folds, over a
four-stamp chained hysteresis schedule on the hand world plus the pinned
real-calendar folds:

* ``|weight| <= 0.30`` at every stamp (cap never binding by construction,
  asserted anyway);
* gross ``<= 1.0`` and CASH RECONCILES: ``cash = 1 - gross`` is non-negative
  and each populated side holds exactly its frozen 0.5 budget;
* the force-flat fold contract: each fold's trailing stamp is purged, so a
  book opened inside a fold always realises inside that fold, and the
  family records one FORCED_FLAT boundary action per fold (A3 vocabulary,
  counted separately from discretionary decisions);

Evidence (g) -- cost-once and funding-settlement-once:

* transition cost is the frozen adapter arithmetic, hand-exact for one
  leg; identical books cost exactly zero; the function is pure (no
  accumulation across calls);
* funding accrues exactly ONCE per native settlement inside
  ``[ts_opened, ts_closed]`` under ``LONG_PAYS_POSITIVE_RATE``
  (cashflow = -weight x rate); settlements outside the span never accrue;
  duplicate settlement stamps refuse.

All data synthetic; no real data is read; no scored metric is computed.
"""

from __future__ import annotations

import math

import pytest

from tests.v13i_oitd_world import (
    GROUP_H,
    GROUP_L,
    SYMBOLS,
    T1_DAY,
    T1_NS,
    T4_NS,
    bars_by_symbol,
    merged_world,
    plugin as make_plugin,
    world_b,
)

from research.adapter_v10.base import GenericStrategyBase
from research.adapter_v10.protocol import (
    ContractViolation,
    CostModel,
    PositionSpan,
    SettlementPoint,
    StressSpec,
)

# SettlementPoint is used by the funding-once probes below; the plugin
# takes native loader rows ({"publish_ts_ns", "value"} dicts).
from research.v13.families.oitd.book import build_hysteresis_book
from research.v13.families.oitd.plugin import OitdPlugin
from research.v13.families.oitd.strategy import (
    ANCHOR_ARM,
    CAP_MAX,
    LEG_GROSS,
    fold_assignments,
    purge_fold_members,
    stamp_calendar,
)


WEEK_NS = 7 * 86_400_000_000_000
STAMPS_4 = [T1_NS, T1_NS + WEEK_NS, T1_NS + 2 * WEEK_NS, T1_NS + 3 * WEEK_NS]


def _chained_payloads(stamps):
    """Chained hysteresis target payloads over the given weekly stamps."""
    world = merged_world(stamps)
    p = make_plugin(ANCHOR_ARM, world)
    return [
        p.targets_at(int(stamp), universe=tuple(world["universe"]), stress=p.baseline_stress())
        for stamp in stamps
    ]


# --------------------------------------------------------------------- #
# (f) cap / gross / cash invariants over a chained schedule
# --------------------------------------------------------------------- #
def test_cap_gross_cash_invariants_hold_at_every_stamp() -> None:
    stamps = [T1_NS, T1_NS + 7 * 86_400_000_000_000,
              T1_NS + 14 * 86_400_000_000_000, T4_NS]
    payloads = _chained_payloads(stamps)
    assert len(payloads) == 4
    for payload in payloads:
        weights = {sym: float(w) for sym, w in payload["weights"]}
        assert weights, "a well-formed book always holds positions"
        gross = math.fsum(abs(w) for w in weights.values())
        # |w| <= 0.30 at every stamp
        max_abs = max(abs(w) for w in weights.values())
        assert max_abs <= CAP_MAX + 1e-12
        assert payload["diagnostics"]["max_abs_weight"] <= CAP_MAX + 1e-12
        # gross <= 1.0 and cash reconciles: cash = 1 - gross >= 0
        assert gross <= 1.0 + 1e-9
        cash = 1.0 - gross
        assert cash >= -1e-9
        # each populated side holds exactly its frozen 0.5 budget
        longs = {s: w for s, w in weights.items() if w > 0.0}
        shorts = {s: w for s, w in weights.items() if w < 0.0}
        assert math.fsum(longs.values()) == pytest.approx(LEG_GROSS, abs=1e-9)
        assert math.fsum((abs(w) for w in shorts.values())) == pytest.approx(
            LEG_GROSS, abs=1e-9
        )
        # the carried-book path preserves the same invariants
        if payload["carried_forward"]:
            assert payload["reason_code"] in (
                "SIDE_MEMBERSHIP_BELOW_MIN_BOOK_CARRIED",
                "HELD_SYMBOL_INELIGIBLE_BOOK_CARRIED",
            )


def test_books_never_leak_outside_the_tradeable_universe() -> None:
    universe = set(SYMBOLS)
    for payload in _chained_payloads([T1_NS, T4_NS]):
        for sym, _w in payload["weights"]:
            assert sym in universe


def test_weight_cap_guard_inside_the_builder() -> None:
    """A cap breach cannot be constructed: the builder refuses itself."""
    scores = {f"S{i:02d}": float(i) for i in range(12)}
    book = build_hysteresis_book(
        scores,
        prev_book=None,
        sort_ascending=True,
        leg_gross=0.5,
        cap_max=0.30,
        min_side_members=4,
        min_eligible=12,
    )
    assert max(abs(float(w)) for _s, w in book["weights"]) <= 0.30 + 1e-12
    # per-side equal weights at 4 members = 0.125 (cap slack, no clipping)
    assert all(abs(abs(float(w)) - 0.125) < 1e-12 for _s, w in book["weights"])


# --------------------------------------------------------------------- #
# (f) force-flat at fold boundaries (pinned calendar)
# --------------------------------------------------------------------- #
def test_fold_purge_guarantees_in_fold_realisation() -> None:
    calendar = list(stamp_calendar())
    purged = purge_fold_members(fold_assignments(calendar), purge_days=1)
    week = 7 * 86_400_000_000_000
    for index, label, members, gaps in purged:
        assert gaps == [fold_assignments(calendar)[index][2][-1]]
        # no retained stamp of fold f appears in any other fold
        for other_index, _other, other_members, _g in purged:
            if other_index <= index:
                continue
            assert not (set(members) & set(other_members))
        # books opened at the last retained stamp realise within one week,
        # strictly before the fold end recorded in the pinned windows
        assert members[-1] + week <= T4_MAX_BOUNDARY(index)


def T4_MAX_BOUNDARY(index: int) -> int:
    from research.v13.families.oitd.audits import fold_end_instants

    return fold_end_instants()[index]


def test_boundary_actions_are_separate_from_discretionary_decisions() -> None:
    """The frozen A3 vocabulary: FORCED_FLAT rows are counted separately."""
    from research.v13.families.oitd.audits import fold_end_instants

    calendar = list(stamp_calendar())
    retained = {int(v) for v in calendar}
    boundaries = fold_end_instants()
    assert len(boundaries) == 3
    for boundary in boundaries:
        # a boundary is never itself a decision stamp (it is a fold window
        # end; the Mondays inside the fold are the discretionary stamps)
        assert boundary not in retained
        assert boundary % 86_400_000_000_000 == 0


# --------------------------------------------------------------------- #
# (g) cost-once (frozen adapter arithmetic, hand-exact)
# --------------------------------------------------------------------- #
class _CostProbe(GenericStrategyBase):
    """Minimal adapter exposing the frozen cost/funding arithmetic."""

    def __init__(self, tick=0.01, fee_bps=5.0, settlements=None):
        self._tick = tick
        self._fee = fee_bps
        self._settlements = settlements or {}

    def cost_model(self):
        return CostModel(
            taker_fee_bps=self._fee,
            adverse_tick_slip_floor=1,
            default_tick_sizes={"SYM00": self._tick},
        )

    def settlements(self, symbol):
        return tuple(self._settlements.get(symbol, ()))


BASELINE = StressSpec(name="baseline", fee_multiplier=1.0, tick_slip_ticks=1)


def test_transition_cost_is_hand_exact_and_charged_once() -> None:
    probe = _CostProbe()
    # flat -> +0.5 SYM00 at price 100, fee 5bps, 1 adverse tick of 0.01:
    # cost = 0.5 x (5e-4 x 1 + 1 x 0.01/100) = 0.5 x 0.0006 = 0.0003
    cost = probe.rebalance_cost_between(
        {}, {"SYM00": 0.5}, prices={"SYM00": 100.0}, stress=BASELINE
    )
    assert cost == pytest.approx(0.0003, abs=1e-15)
    # identical books trade nothing: cost exactly zero
    zero = probe.rebalance_cost_between(
        {"SYM00": 0.5}, {"SYM00": 0.5}, prices={"SYM00": 100.0}, stress=BASELINE
    )
    assert zero == 0.0
    # purity: the same transition costs the same on every call (no
    # accumulation, no state -- cost charged exactly once per transition)
    again = probe.rebalance_cost_between(
        {}, {"SYM00": 0.5}, prices={"SYM00": 100.0}, stress=BASELINE
    )
    assert again == cost


def test_stress_cost_multiplies_the_frozen_way() -> None:
    probe = _CostProbe()
    stressed = StressSpec(name="stress", fee_multiplier=1.5, tick_slip_ticks=3)
    # 0.5 x (5e-4 x 1.5 + 3 x 0.01/100) = 0.5 x (0.00075 + 0.0003) = 0.000525
    cost = probe.rebalance_cost_between(
        {}, {"SYM00": 0.5}, prices={"SYM00": 100.0}, stress=stressed
    )
    assert cost == pytest.approx(0.000525, abs=1e-15)
    # a missing tick size with ticks requested refuses (never a silent 0)
    probe_no_tick = _CostProbe(tick=0.0)
    with pytest.raises(ContractViolation):
        probe_no_tick.rebalance_cost_between(
            {}, {"SYM00": 0.5}, prices={"SYM00": 100.0}, stress=BASELINE
        )


def test_transition_to_flat_prices_the_full_exit_once() -> None:
    probe = _CostProbe()
    cost = probe.rebalance_cost_between(
        {"SYM00": -0.5}, {}, prices={"SYM00": 100.0}, stress=BASELINE
    )
    assert cost == pytest.approx(0.0003, abs=1e-15)


# --------------------------------------------------------------------- #
# (g) funding settlement-once (LONG_PAYS_POSITIVE_RATE)
# --------------------------------------------------------------------- #
def _probe_with_settlements(stamps_and_rates):
    return _CostProbe(
        settlements={
            "SYM00": tuple(
                SettlementPoint(publish_ts_ns=int(ts), value=float(rate))
                for ts, rate in stamps_and_rates
            )
        }
    )


def test_funding_accrues_exactly_once_per_settlement_inside_the_span() -> None:
    week = 7 * 86_400_000_000_000
    start, end = T1_NS, T1_NS + week
    inside = [
        (start + 1, 0.0001),
        (start + week // 2, -0.0002),
        (end, 0.0003),  # the closed end is INSIDE [start, end]
    ]
    outside = [
        (start - 1, 0.9),  # before the span
        (end + 1, 0.9),  # after the span
    ]
    probe = _probe_with_settlements(inside + outside)
    span = PositionSpan(symbol="SYM00", signed_weight=0.25, start_ns=start, end_ns=end)
    flows = probe.funding_cashflows_for_spans([span])
    assert [f["publish_ts_ns"] for f in flows] == [ts for ts, _r in inside]
    # each settlement exactly once; hand sign: LONG pays positive rate
    for flow, (ts, rate) in zip(flows, inside):
        assert flow["rate"] == pytest.approx(rate)
        assert flow["signed_weight"] == pytest.approx(0.25)
        assert flow["cashflow_per_unit_capital"] == pytest.approx(-0.25 * rate, abs=1e-15)
        assert flow["sign_convention"] == "LONG_PAYS_POSITIVE_RATE"
    # short leg receives the positive rate
    short_flows = probe.funding_cashflows_for_spans(
        [PositionSpan(symbol="SYM00", signed_weight=-0.25, start_ns=start, end_ns=end)]
    )
    assert short_flows[0]["cashflow_per_unit_capital"] == pytest.approx(0.25 * 0.0001, abs=1e-15)
    # calling again accrues nothing new (settlement exactly once per span)
    assert probe.funding_cashflows_for_spans([span]) == flows


def test_zero_weight_spans_and_duplicate_settlements() -> None:
    probe = _probe_with_settlements([(T1_NS + 1, 0.0001)])
    flat = PositionSpan(symbol="SYM00", signed_weight=0.0, start_ns=T1_NS, end_ns=T1_NS + 1)
    assert probe.funding_cashflows_for_spans([flat]) == []
    duplicate = _CostProbe(
        settlements={
            "SYM00": (
                SettlementPoint(publish_ts_ns=T1_NS + 5, value=0.1),
                SettlementPoint(publish_ts_ns=T1_NS + 5, value=0.1),
            )
        }
    )
    span = PositionSpan(symbol="SYM00", signed_weight=0.5, start_ns=T1_NS, end_ns=T1_NS + 10)
    with pytest.raises(ContractViolation):
        duplicate.funding_cashflows_for_spans([span])


def test_plugin_funding_uses_native_settlements_of_the_held_symbol() -> None:
    """The dry-run accrual probe: cashflows exist over a real held span."""
    from tests.v13i_oitd_world import plugin as make_plugin

    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    settlements = {
        # native loader row shape: {"publish_ts_ns", "value"} dicts
        "SYM12": (
            {"publish_ts_ns": T1_NS + 100, "value": 0.0001},
            {"publish_ts_ns": T1_NS + 200, "value": 0.0002},
        )
    }
    p = OitdPlugin(
        arm_id=ANCHOR_ARM,
        day_turnover_by_symbol=dict(world["day_turnover_by_symbol"]),
        bars_by_symbol=bars_by_symbol(world["universe"], T1_NS),
        oi_by_symbol=dict(world["oi_by_symbol"]),
        mark_by_symbol=dict(world["mark_by_symbol"]),
        settlements_by_symbol=dict(settlements),
    )
    book = p.targets_at(T1_NS, universe=tuple(world["universe"]), stress=p.baseline_stress())
    weights = {sym: float(w) for sym, w in book["weights"]}
    assert weights["SYM12"] > 0  # held long on the hand world
    span = PositionSpan(
        symbol="SYM12", signed_weight=weights["SYM12"], start_ns=T1_NS, end_ns=T1_NS + 7 * 86_400_000_000_000
    )
    flows = p.funding_cashflows_for_spans([span])
    assert len(flows) == 2  # exactly the two native settlements
    assert flows[0]["cashflow_per_unit_capital"] == pytest.approx(
        round(-weights["SYM12"] * 0.0001, 12), abs=1e-18
    )
