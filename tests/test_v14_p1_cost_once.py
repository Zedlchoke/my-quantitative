"""V14 Phase P1 A2 -- cost-once-per-fill kernel fixtures (L-V14-0).

Hand-computed fixtures pinning the binding remediation of PLAN_crypto_v14.md
section 6 (P1): execution cost is charged EXACTLY ONCE PER FILL -- never per
holding-day, never per stamp on open positions -- on the frozen generic
adapter path (``research.adapter_v10.runner.run_strategy`` +
``GenericStrategyBase.rebalance_cost_between``) and through the frozen V12
publication accounting (``research.v12.accounting``).  Every expected value
below is computed BY HAND in this docstring and asserted exactly.

All data SYNTHETIC; no real data file is read, nothing is scored, no ledger
outside ``tmp_path`` is touched, and no frozen V11/V12/V13 module byte is
edited.  This module PINS the kernel semantics; the V13 driver defect
(uniform ``tick_size 0.01`` stub) itself is remediated in
``research/control/v13_run/tools/run_v13_cell.py::build_liqepis``.

Frozen cost schedule used by every fixture (V10 floors, byte-identical):

    rate_per_unit_notional = taker_fee_bps * 1e-4 * fee_multiplier
                           + tick_slip_ticks * tick_size / fill_price

Hand world: fee 5.0 bps -> 5e-4; tick_size 0.01; fill price 100.0;
baseline slip floor 1 tick -> slip 1e-4.  Baseline rate = 6e-4 per unit
notional.  A book of K legs at |w| = 0.125 trades Sigma|dw| = K * 0.125 of
notional once on entry and once on the final force-flat exit:

    cost_total(K legs, any holding length) = K * 0.125 * 6e-4 * 2

    8 legs  -> 1.0 * 6e-4 * 2 = 0.0012   (any number of held stamps)
    16 legs -> 2.0 * 6e-4 * 2 = 0.0024   (exactly 2x the 8-leg book)

Stress tiers on the 8-leg book (identical fill set):
    baseline  (fee x1.0, +1 tick):  rate 0.00050 + 0.00010 = 0.00060 -> 0.0012
    fee x1.5  (fee x1.5, +1 tick):  rate 0.00075 + 0.00010 = 0.00085 -> 0.0017
    +2 ticks  (fee x1.0, +3 ticks): rate 0.00050 + 0.00030 = 0.00080 -> 0.0016
Three DISTINCT totals on the same fills, in the exact hand ratio 12:17:16.

Fixture map (mission items a-f):

* (a) test_v14p1_many_small_positions_cost_scales_with_fills_not_holding_days
* (b) test_v14p1_stress_tiers_differ_from_base_and_each_other_in_expected_ratio
* (c) test_v14p1_cost_once_across_replay_of_the_same_book
* (d) test_v14p1_scored_row_observed_once_and_replay_never_moves_counters
* (e) test_v14p1_zero_fill_book_charges_zero_cost_and_publication_refused
* (f) test_v14p1_append_serialization_duplicate_row_cannot_double_count
plus the L-V14-0 defect-arithmetic pin
(test_v14p1_uniform_tick_stub_inflates_per_fill_slip_hand_exact).
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

import pytest

from research.adapter_v10.base import GenericStrategyBase
from research.adapter_v10.protocol import (
    ContractViolation,
    CostModel,
    FillRecord,
    FillStatusVocabulary,
    ImmutableSchedule,
    StressSpec,
    StrategyIdentity,
)
from research.adapter_v10.runner import run_strategy
from research.v12.accounting import (
    REFUSED_TRIAL_KEY_ALREADY_PRESENT,
    REFUSED_ZERO_POSITIONS,
    ROW_TYPE_CELL_RESULT,
    STAGE_IDEMPOTENT_REPLAY,
    STAGE_PUBLISHED,
    STAGE_REFUSED,
    append_v12_row,
    publish_v12_cell,
    read_v12_ledger,
    v12_denominator_view,
)

# ------------------------------------------------------------------------- #
# Hand world constants (every expected value derives from these)
# ------------------------------------------------------------------------- #
FEE_BPS = 5.0
FEE_RATE = 5.0e-4
TICK_SIZE = 0.01
FILL_PRICE = 100.0
SLIP_FLOOR_TICKS = 1
SLIP_RATE = SLIP_FLOOR_TICKS * TICK_SIZE / FILL_PRICE  # 1e-4
BASE_RATE = FEE_RATE + SLIP_RATE                       # 6e-4

WEEK_NS = 7 * 86_400_000_000_000
T0_NS = int(datetime(2025, 1, 6, tzinfo=timezone.utc).timestamp()) * 1_000_000_000

ALL_SYMBOLS = tuple(f"SYM{i:02d}" for i in range(16))


def _book(n_legs: int) -> dict[str, float]:
    """A constant dollar-neutral book: n_legs/2 longs + n_legs/2 shorts.

    Every leg holds |w| = 0.125 (below the 0.30 cap), so entry + exit churn
    exactly Sigma|dw| = n_legs * 0.125 regardless of the holding length.
    """
    if n_legs % 2:
        raise ContractViolation("fixture books need an even leg count")
    half = n_legs // 2
    weights = {sym: 0.125 for sym in ALL_SYMBOLS[:half]}
    weights.update({sym: -0.125 for sym in ALL_SYMBOLS[half : 2 * half]})
    return weights


def _prices() -> dict[str, float]:
    return {sym: FILL_PRICE for sym in ALL_SYMBOLS}


class _LongHoldBook(GenericStrategyBase):
    """Synthetic plugin whose target book NEVER changes across its schedule.

    The book opens once (entry fills at stamp 0), is HELD unchanged at every
    intermediate weekly stamp (zero weight delta -> zero cost if and only if
    the kernel charges per fill, never per stamp on open positions), and
    realises once at the trailing force-flat edge (exit fills).
    """

    def __init__(self, *, n_instants: int, n_legs: int) -> None:
        if n_instants < 3:
            raise ContractViolation("fixture schedule needs >= 3 instants")
        self._instants = tuple(T0_NS + i * WEEK_NS for i in range(n_instants))
        self._weights = _book(n_legs)
        self._identity = StrategyIdentity(
            strategy_id="v14p1-longhold-fixture",
            family_id="V14P1_COST_ONCE_FIXTURE",
            arm_config_id="longhold-baseline",
            direction="BOTH_WITH_SIGN_SEMANTICS",
            window_start_iso="2025-01-01T00:00:00Z",
            window_end_iso="2025-06-01T00:00:00Z",
            config={"rule": "constant_book_no_randomness"},
        )

    def identity(self) -> StrategyIdentity:
        return self._identity

    def cost_model(self) -> CostModel:
        return CostModel(
            taker_fee_bps=FEE_BPS,
            adverse_tick_slip_floor=SLIP_FLOOR_TICKS,
            default_tick_sizes={sym: TICK_SIZE for sym in ALL_SYMBOLS},
        )

    def tradeable_universe(self) -> tuple[str, ...]:
        return tuple(sorted(self._weights))

    def schedule(self) -> ImmutableSchedule:
        return ImmutableSchedule(
            instants=self._instants,
            source="tests.test_v14_p1_cost_once._LongHoldBook (weekly)",
            clock="15M",
        )

    def fold_count(self) -> int:
        return 1

    def purge_days(self) -> int:
        return 1

    def targets_at(
        self, instant_ns: int, *, universe: Sequence[str], stress: StressSpec
    ) -> dict[str, Any]:
        del instant_ns, universe, stress
        return {
            "status": "OK",
            "weights": dict(sorted(self._weights.items())),
            "carried_forward": False,
        }

    def fills_at(
        self, instant_ns: int, *, symbols: Sequence[str], stress: StressSpec
    ) -> tuple[FillRecord, ...]:
        del stress
        fill_ns = int(instant_ns) + 15 * 60 * 1_000_000_000
        return tuple(
            FillRecord(
                symbol=str(sym),
                decision_ns=int(instant_ns),
                status=FillStatusVocabulary.APPLIED,
                applied=True,
                price=FILL_PRICE,
                fill_open_ns=fill_ns,
                fill_bar_close_ns=fill_ns,
            )
            for sym in sorted(set(symbols))
        )

    def marks_at(
        self, symbols: Sequence[str], instant_ns: int
    ) -> dict[str, Optional[float]]:
        del instant_ns
        return {str(sym): FILL_PRICE for sym in sorted(set(symbols))}

    def settlements(self, symbol: str) -> tuple[Any, ...]:
        return ()


def _run(n_instants: int, n_legs: int, stress: StressSpec | None = None):
    return run_strategy(
        _LongHoldBook(n_instants=n_instants, n_legs=n_legs),
        stress=stress,
        write_artifact_file=False,
    )


# ------------------------------------------------------------------------- #
# (a) cost scales with FILLS, not holding days
# ------------------------------------------------------------------------- #
def test_v14p1_many_small_positions_cost_scales_with_fills_not_holding_days():
    # 8 small legs (16 fills: 8 entries + 8 exits) held over 5 weekly spans:
    # cost = 8 * 0.125 * (5e-4 + 1e-4) * 2 = 0.0012 (hand).
    short_hold = _run(n_instants=6, n_legs=8)
    # The SAME book held over 11 weekly spans (2.2x the holding period,
    # identical 16 fills) must charge the IDENTICAL total.
    long_hold = _run(n_instants=12, n_legs=8)
    assert short_hold["portfolio_metrics"]["cost_charged_sum"] == pytest.approx(
        0.0012, abs=1e-15
    )
    assert long_hold["portfolio_metrics"]["cost_charged_sum"] == pytest.approx(
        0.0012, abs=1e-15
    )
    assert (
        long_hold["portfolio_metrics"]["cost_charged_sum"]
        == short_hold["portfolio_metrics"]["cost_charged_sum"]
    )

    # NOT ONE unit of cost may accrue at a held stamp: every boundary between
    # the opening one and the final force-flat exit charges exactly zero.
    for result in (short_hold, long_hold):
        rows = sorted(result["daily_returns"], key=lambda r: r["decision_ns"])
        for row in rows[1:-1]:
            assert row["cost_charged_per_unit"] == 0.0, row
        assert rows[0]["cost_charged_per_unit"] == pytest.approx(0.0006, abs=1e-15)
        assert rows[-1]["cost_charged_per_unit"] == pytest.approx(0.0006, abs=1e-15)

    # Doubling the FILL COUNT at the same per-fill size doubles the cost:
    # 16 legs -> 32 fills -> 16 * 0.125 * 6e-4 * 2 = 0.0024 (hand).
    double_fills = _run(n_instants=6, n_legs=16)
    assert double_fills["portfolio_metrics"]["cost_charged_sum"] == pytest.approx(
        0.0024, abs=1e-15
    )
    assert (
        double_fills["portfolio_metrics"]["cost_charged_sum"]
        == 2 * short_hold["portfolio_metrics"]["cost_charged_sum"]
    )


# ------------------------------------------------------------------------- #
# (b) stress tiers: distinct from base AND from each other, exact ratio
# ------------------------------------------------------------------------- #
def test_v14p1_stress_tiers_differ_from_base_and_each_other_in_expected_ratio():
    # Identical fill set (8-leg book, 6 instants) under three stress tiers.
    base = _run(n_instants=6, n_legs=8)  # rate 0.00060 -> 0.0012
    fee_up = _run(
        n_instants=6,
        n_legs=8,
        stress=StressSpec(name="fee_x1_5", fee_multiplier=1.5, tick_slip_ticks=1),
    )  # rate 0.00085 -> 0.0017
    ticks_up = _run(
        n_instants=6,
        n_legs=8,
        stress=StressSpec(name="plus2ticks", fee_multiplier=1.0, tick_slip_ticks=3),
    )  # rate 0.00080 -> 0.0016

    cost_base = base["portfolio_metrics"]["cost_charged_sum"]
    cost_fee = fee_up["portfolio_metrics"]["cost_charged_sum"]
    cost_ticks = ticks_up["portfolio_metrics"]["cost_charged_sum"]

    assert cost_base == pytest.approx(0.0012, abs=1e-15)
    assert cost_fee == pytest.approx(0.0017, abs=1e-15)
    assert cost_ticks == pytest.approx(0.0016, abs=1e-15)

    # All three tiers differ from the base AND from each other, in the exact
    # hand ratio 12 : 17 : 16.
    assert len({cost_base, cost_fee, cost_ticks}) == 3
    assert cost_fee == pytest.approx(cost_base * 17.0 / 12.0, rel=1e-12)
    assert cost_ticks == pytest.approx(cost_base * 16.0 / 12.0, rel=1e-12)
    assert cost_fee != pytest.approx(cost_ticks, rel=1e-12)

    # The stress multipliers changed NOTHING but cost: the price/funding
    # position surface is identical across tiers (positions themselves carry
    # cost_allocated_per_unit, so their hash legitimately differs).
    for key in ("price_pnl_sum", "funding_sum", "n_positions"):
        assert base["portfolio_metrics"][key] == fee_up["portfolio_metrics"][key]
        assert base["portfolio_metrics"][key] == ticks_up["portfolio_metrics"][key]
    # net_return_sum moves by EXACTLY the cost difference, nothing else.
    assert (
        base["portfolio_metrics"]["net_return_sum"]
        - fee_up["portfolio_metrics"]["net_return_sum"]
    ) == pytest.approx(cost_fee - cost_base, abs=1e-15)
    assert (
        base["portfolio_metrics"]["net_return_sum"]
        - ticks_up["portfolio_metrics"]["net_return_sum"]
    ) == pytest.approx(cost_ticks - cost_base, abs=1e-15)


# ------------------------------------------------------------------------- #
# (c) cost-once across replay
# ------------------------------------------------------------------------- #
def test_v14p1_cost_once_across_replay_of_the_same_book():
    first = _run(n_instants=6, n_legs=8)
    # Replaying the SAME book (fresh strategy instance, identical inputs)
    # recomputes the same cost exactly once -- never an incremental charge.
    replay = _run(n_instants=6, n_legs=8)
    assert (
        replay["portfolio_metrics"]["cost_charged_sum"]
        == first["portfolio_metrics"]["cost_charged_sum"]
    )
    assert replay["hashes"] == first["hashes"]
    assert replay["portfolio_metrics"] == first["portfolio_metrics"]

    # Purity at the cost primitive itself: the same transition priced twice
    # returns the same number (no accumulation across calls).
    plugin = _LongHoldBook(n_instants=6, n_legs=8)
    entry_transition = (
        {},
        dict(sorted(_book(8).items())),
    )
    once = plugin.rebalance_cost_between(
        *entry_transition, prices=_prices(), stress=plugin.baseline_stress()
    )
    twice = plugin.rebalance_cost_between(
        *entry_transition, prices=_prices(), stress=plugin.baseline_stress()
    )
    assert once == twice == pytest.approx(0.0006, abs=1e-15)


# ------------------------------------------------------------------------- #
# (d) observed-once / replay-never counters (scored rows carrying cost)
# ------------------------------------------------------------------------- #
SCORED_METRICS = {
    # cost-bearing scored row: net is price PnL minus the charged cost
    "score_valid": True,
    "net_return_sum": 0.0031 - 0.0012,
    "expectancy_per_day": 0.0003,
    "max_drawdown": 0.0009,
    "n_positions": 8,
    "n_decisions": 6,
    "n_fills": 16,
}

ZERO_METRICS = {
    "score_valid": True,
    "net_return_sum": 0.0,
    "expectancy_per_day": 0.0,
    "max_drawdown": 0.0,
    "n_positions": 0,
    "n_decisions": 0,
    "n_fills": 0,
}


def _publish_kwargs(tmp_path: Path, arm_id: str, ledger_name: str, scored=None) -> dict:
    return dict(
        strategy_id="v14p1-cost-once-fixture",
        family="V14P1_COST_ONCE_FIXTURE",
        arm_id=arm_id,
        arm_config_digest="d" * 64,
        stress_signature=StressSpec(name="baseline"),
        window_start_iso="2025-01-01T00:00:00Z",
        window_end_iso="2025-06-01T00:00:00Z",
        scored_metrics=dict(SCORED_METRICS if scored is None else scored),
        result_sha256="a" * 64,
        ledger_path=tmp_path / ledger_name,
        producer_head_sha="0" * 40,
    )


def test_v14p1_scored_row_observed_once_and_replay_never_moves_counters(tmp_path):
    ledger = tmp_path / "observed_once.jsonl"

    # First computation of the scored row: published, counted exactly once.
    first = publish_v12_cell(**_publish_kwargs(tmp_path, "anchor", "observed_once.jsonl"))
    assert first["stage"] == STAGE_PUBLISHED
    assert first["published_delta"] == 1 and first["observed_delta"] == 0
    assert v12_denominator_view(ledger) == {
        "published": 1,
        "observed": 0,
        "observed_total": 1,
        "rows": 1,
    }
    rows = [
        json.loads(line)
        for line in ledger.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(rows) == 1 and rows[0]["row_type"] == ROW_TYPE_CELL_RESULT

    # Exact replay of the same scored row: zero incremental charge, zero
    # counter movement, zero new rows.
    replay = publish_v12_cell(**_publish_kwargs(tmp_path, "anchor", "observed_once.jsonl"))
    assert replay["stage"] == STAGE_IDEMPOTENT_REPLAY
    assert replay["published_delta"] == 0 and replay["observed_delta"] == 0
    assert v12_denominator_view(ledger)["rows"] == 1

    # A DIFFERENT trial that refuses (zero positions) is observed exactly
    # once; its replay observes nothing incremental.
    zero = publish_v12_cell(
        **_publish_kwargs(tmp_path, "zero-arm", "observed_once.jsonl", ZERO_METRICS)
    )
    assert zero["stage"] == STAGE_REFUSED
    assert zero["reasons"][0] == REFUSED_ZERO_POSITIONS
    assert zero["observed_delta"] == 1
    zero_replay = publish_v12_cell(
        **_publish_kwargs(tmp_path, "zero-arm", "observed_once.jsonl", ZERO_METRICS)
    )
    assert zero_replay["stage"] == STAGE_IDEMPOTENT_REPLAY
    assert zero_replay["observed_delta"] == 0

    assert v12_denominator_view(ledger) == {
        "published": 1,
        "observed": 1,
        "observed_total": 2,
        "rows": 2,
    }


# ------------------------------------------------------------------------- #
# (e) zero-fill book: zero cost + zero-position publication refusal
# ------------------------------------------------------------------------- #
class _NeverFillsBook(_LongHoldBook):
    """Same surface, but the target book is ALWAYS FLAT: zero fills ever."""

    def __init__(self, *, n_instants: int) -> None:
        super().__init__(n_instants=n_instants, n_legs=8)
        self._weights = {}
        self._identity = StrategyIdentity(
            strategy_id="v14p1-zerofill-fixture",
            family_id="V14P1_COST_ONCE_FIXTURE",
            arm_config_id="zerofill-baseline",
            direction="BOTH_WITH_SIGN_SEMANTICS",
            window_start_iso="2025-01-01T00:00:00Z",
            window_end_iso="2025-06-01T00:00:00Z",
            config={"rule": "always_flat"},
        )

    def tradeable_universe(self) -> tuple[str, ...]:
        return ALL_SYMBOLS[:2]


def _never_fills_metrics() -> dict[str, Any]:
    result = run_strategy(
        _NeverFillsBook(n_instants=6), stress=None, write_artifact_file=False
    )
    metrics = result["portfolio_metrics"]
    # Zero fills -> zero cost at EVERY boundary and in total (exactly 0.0).
    assert metrics["cost_charged_sum"] == 0.0
    assert metrics["n_positions"] == 0
    for row in result["daily_returns"]:
        assert row["cost_charged_per_unit"] == 0.0
    return metrics


def test_v14p1_zero_fill_book_charges_zero_cost_and_publication_refused(tmp_path):
    metrics = _never_fills_metrics()
    refused = publish_v12_cell(
        strategy_id="v14p1-cost-once-fixture",
        family="V14P1_COST_ONCE_FIXTURE",
        arm_id="never-fills",
        arm_config_digest="e" * 64,
        stress_signature=StressSpec(name="baseline"),
        window_start_iso="2025-01-01T00:00:00Z",
        window_end_iso="2025-06-01T00:00:00Z",
        scored_metrics={
            "score_valid": True,
            "net_return_sum": metrics["net_return_sum"],
            "expectancy_per_day": metrics["expectancy_per_day"],
            "max_drawdown": metrics["max_drawdown"],
            "n_positions": metrics["n_positions"],
            "n_decisions": 0,
            "n_fills": 0,
        },
        result_sha256="b" * 64,
        ledger_path=tmp_path / "zero.jsonl",
        producer_head_sha="0" * 40,
    )
    assert refused["published"] is False
    assert refused["stage"] == STAGE_REFUSED
    assert refused["reasons"][0] == REFUSED_ZERO_POSITIONS
    assert refused["published_delta"] == 0 and refused["observed_delta"] == 1
    # ...and the refused compute can never appear as a published row.
    state = read_v12_ledger(tmp_path / "zero.jsonl")
    assert state["count"] == 1
    assert state["rows"][0]["row_type"] != ROW_TYPE_CELL_RESULT


# ------------------------------------------------------------------------- #
# (f) A1 append serialization: a duplicate row cannot double-count
# ------------------------------------------------------------------------- #
def _cell_row(key: str) -> dict:
    return {
        "row_type": ROW_TYPE_CELL_RESULT,
        "trial_key": key,
        "arm_id": "serial-arm",
        "arm_config_digest": "f" * 64,
        "family": "V14P1_COST_ONCE_FIXTURE",
        "cell": {"name": "baseline"},
        "result_sha256": "c" * 64,
        "published_utc": "2026-09-05T00:00:00Z",
        "producer_head_sha": "0" * 40,
    }


def test_v14p1_append_serialization_duplicate_row_cannot_double_count(tmp_path):
    ledger = tmp_path / "serial.jsonl"
    key = "9" * 64

    first = append_v12_row(_cell_row(key), ledger)
    assert first["appended"] is True
    serialized_bytes = ledger.read_bytes()

    # Appending the SAME scored row twice is refused: no second row, the
    # duplicate cannot double-count, and the ledger bytes never rewrite.
    duplicate = append_v12_row(_cell_row(key), ledger)
    assert duplicate["attempted"] is True
    assert duplicate["appended"] is False
    assert duplicate["reasons"] == [REFUSED_TRIAL_KEY_ALREADY_PRESENT]
    assert ledger.read_bytes() == serialized_bytes
    assert read_v12_ledger(ledger)["count"] == 1
    assert v12_denominator_view(ledger)["published"] == 1

    # The publication entry point serializes the same way under its lock:
    # a second publish of the same trial is an idempotent replay.
    record = publish_v12_cell(**_publish_kwargs(tmp_path, "serial", "serial2.jsonl"))
    assert record["stage"] == STAGE_PUBLISHED
    replay = publish_v12_cell(**_publish_kwargs(tmp_path, "serial", "serial2.jsonl"))
    assert replay["stage"] == STAGE_IDEMPOTENT_REPLAY
    assert v12_denominator_view(tmp_path / "serial2.jsonl")["published"] == 1

    # Concurrent same-key appends land EXACTLY once (serialized, not lost).
    race_ledger = tmp_path / "race.jsonl"
    results: list = [None] * 8
    start = threading.Barrier(len(results))

    def attempt(index: int) -> None:
        start.wait(timeout=30)
        results[index] = append_v12_row(_cell_row(key), race_ledger)

    threads = [
        threading.Thread(target=attempt, args=(i,), daemon=True) for i in range(8)
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)
    assert sum(1 for r in results if r["appended"]) == 1
    assert read_v12_ledger(race_ledger)["count"] == 1


# ------------------------------------------------------------------------- #
# L-V14-0 defect arithmetic pin (the V13 driver stub, hand-exact)
# ------------------------------------------------------------------------- #
class _RealTickProbe(_LongHoldBook):
    """The same fixture plugin carrying a REAL sub-cent tick (1e-07)."""

    def cost_model(self) -> CostModel:
        return CostModel(
            taker_fee_bps=FEE_BPS,
            adverse_tick_slip_floor=SLIP_FLOOR_TICKS,
            default_tick_sizes={sym: 1e-07 for sym in ALL_SYMBOLS},
        )


def test_v14p1_uniform_tick_stub_inflates_per_fill_slip_hand_exact():
    """The V13 defect at the rate level on a sub-cent symbol (hand-exact).

    BOME-like price 0.0025 with the V13 uniform stub tick 0.01: one adverse
    tick of slip costs 0.01 / 0.0025 = 4.0 per unit notional, so a delta of
    1.0 costs 5e-4 * 1.0 + 4.0 = 4.0005.  With the REAL tick (1e-07) the
    same fill costs 5e-4 + 1e-7 / 0.0025 = 0.00054.  The slip TERM alone is
    inflated exactly 100000x here; across the V13 book average it surfaced
    as the ~3-4 orders cost anomaly (L-V14-0: cost_charged_sum 25.03 vs
    price-only PnL -0.31, corrected ~900-1700x lower).
    """
    sub_cent = 0.0025
    stub = _LongHoldBook(n_instants=6, n_legs=8).rebalance_cost_between(
        {"SYM00": 0.0},
        {"SYM00": 1.0},
        prices={"SYM00": sub_cent},
        stress=StressSpec(name="baseline", fee_multiplier=1.0, tick_slip_ticks=1),
    )
    real = _RealTickProbe(n_instants=6, n_legs=8).rebalance_cost_between(
        {"SYM00": 0.0},
        {"SYM00": 1.0},
        prices={"SYM00": sub_cent},
        stress=StressSpec(name="baseline", fee_multiplier=1.0, tick_slip_ticks=1),
    )
    assert stub == pytest.approx(4.0005, abs=1e-15)      # 5e-4 + 0.01/0.0025
    assert real == pytest.approx(0.00054, abs=1e-15)     # 5e-4 + 1e-7/0.0025
    assert stub > 1000 * real  # the per-fill charge is ~7.4e3x inflated here
    slip_stub = 0.01 / sub_cent
    slip_real = 1e-07 / sub_cent
    assert slip_stub == pytest.approx(4.0, abs=1e-15)
    assert slip_stub / slip_real == pytest.approx(100_000)
