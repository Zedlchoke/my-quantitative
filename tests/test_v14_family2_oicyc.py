"""V14 I-family-2 (A14-V14-A8-OICYC) implementation tests.

Covers, per the V14 Phase-I evidence list (PLAN_crypto_v14.md section 9):

(a) feature golden tests on HAND-COMPUTED synthetic OI panels (slope,
    leave-one-out aggregate, own-share, ranks, books);
(b) THE L-V14-0 COST-SCALING REGRESSION on the family's books: cost is
    strictly linear in the number of fills (2N fills cost exactly 2x N
    fills; a long-hold few-fills book costs the same as a short-hold
    same-fills book; held stamps charge exactly zero), through the frozen
    adapter path (``run_strategy`` + ``rebalance_cost_between``);
(c) AVAILABILITY-LAG MUTATION TESTS for EVERY adopted conditioning field
    (staged OI daily rows; bars used for execution/pricing; funding, which
    is COST ONLY and must never enter any signal): shift availability one
    day later / stamp a row available after a decision and assert the
    pipeline refuses or shifts deterministically -- a decision at T never
    reads data dated after T;
(d) zero-position refusal passthrough (book builder, drop-one, plugin
    chain, publication);
(e) fold force-flat boundary respected (frozen calendar-zone purge pinned;
    no position span straddles a fold boundary through the real runner).

All data SYNTHETIC except the SHA-verified staged-OI authority check;
nothing is scored, no ledger outside ``tmp_path`` is touched, and no
frozen module byte is edited.
"""

from __future__ import annotations

import copy
import dataclasses
import hashlib
import json
import math
from datetime import datetime, timedelta, timezone
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
from research.v11.families.oilever_delev.strategy import (
    BAR_INTERVAL_NS,
    DAY_NS,
    Bar,
    iso_utc,
    parse_iso_utc,
)
from research.v12.accounting import (
    REFUSED_ZERO_POSITIONS,
    ROW_TYPE_CELL_RESULT,
    STAGE_REFUSED,
    publish_v12_cell,
    read_v12_ledger,
)
from research.v14.families.oicyc.frozen_identity import (
    OICYC_ARM_CONFIG_DIGESTS,
    frozen_arm_digest_report,
    frozen_identity,
)
from research.v14.families.oicyc.gate_runner import (
    evaluate_family_gate,
    fold_concentration_check,
    headline_gate,
    incremental_context_gate,
)
from research.v14.families.oicyc.plugin import OicycPlugin
from research.v14.families.oicyc.strategy import (
    ANCHOR_ARM,
    BENCHMARK_SYMBOL,
    CONTROL_ARM,
    FAMILY_ID,
    FIRST_STAMP_ISO,
    NEIGHBOUR_ARM,
    WARMUP_ROWS_FIRST_STAMP,
    EligibilityShortfall,
    LookaheadViolation,
    assert_first_stamp_warmup,
    assert_inputs_available,
    build_hysteresis_book,
    compute_targets_at,
    cycle_slope,
    daily_log_changes,
    drop_one_book,
    effective_schedule,
    fold_assignments,
    frozen_identity as strategy_frozen_identity,
    next_allowed_fill,
    own_share_mean,
    signal_scores_at,
    snap_close_to_boundary,
    stamp_calendar,
)

GOLDEN_DIR = Path(__file__).resolve().parents[1] / "research/v14/families/oicyc/golden"

#: Frozen V10 cost floors (contract_v10; the hand world below uses them).
FEE_BPS = 5.0
TICK = 0.01
PRICE = 100.0
RATE = FEE_BPS * 1e-4 + 1 * TICK / PRICE  # 6e-4 per unit notional


def _load(name: str) -> dict:
    return json.loads((GOLDEN_DIR / name).read_text(encoding="utf-8"))


def _series_from_rows(rows: list[dict], symbol: str) -> list[tuple[int, float]]:
    return [
        (int(row["stamp_ns"]), float(row["levels"][symbol]))
        for row in rows
    ]


def _panel(rows: list[dict], symbols: Sequence[str]) -> dict[str, list[tuple[int, float]]]:
    return {sym: _series_from_rows(rows, sym) for sym in symbols}


# ------------------------------------------------------------------------- #
# (a) feature golden tests -- hand-computed math world (5 symbols)
# ------------------------------------------------------------------------- #
def _math_world() -> tuple[dict[str, list[tuple[int, float]]], list[str], int]:
    fx = _load("cyc_math_fixture.json")
    universe = fx["hand_computed_world"]["universe"]
    return _panel(fx["rows"], universe), universe, int(fx["expected"]["decision_ns"])


def test_golden_math_slope_leave_one_out_and_own_share():
    panel, universe, stamp = _math_world()
    ln2, ln15 = math.log(2.0), math.log(1.5)
    # slopes over the 4-row window (3 paired changes), hand-exact
    expected = {"MA": 4 * ln2 / ln15, "MB": 4 * ln15 / ln2, "MC": 0.0, "MD": 0.0, "ME": 0.0}
    for sym in universe:
        slope = cycle_slope(panel, sym, stamp, universe=universe, window_rows=4)
        assert slope == pytest.approx(expected[sym], abs=1e-12)
    # the leave-one-out aggregate for MA is exactly +/-ln(1.5)/4 (hand)
    changes = daily_log_changes(panel["MA"], stamp)
    fx = _load("cyc_math_fixture.json")
    days = sorted(d for d, v in changes.items() if v is not None)[-3:]
    agg = []
    for d in days:
        others = [daily_log_changes(panel[s], stamp)[d] for s in universe if s != "MA"]
        agg.append(math.fsum(others) / 4.0)
    assert agg == pytest.approx(fx["expected"]["leave_one_out_aggregate_MA_rows_5_6_7"], abs=1e-12)
    # own share of the aggregate over the 4 most recent rows (hand)
    expected_sh = fx["expected"]["own_share_window_rows_4"]
    for sym in universe:
        share = own_share_mean(panel, sym, stamp, universe=universe, window_rows=4)
        assert share == pytest.approx(expected_sh[sym], abs=1e-15)
    # ascending slope ranks / descending own-share presentation (hand)
    scores = {sym: cycle_slope(panel, sym, stamp, universe=universe, window_rows=4) for sym in universe}
    ordered = sorted((scores[s], s) for s in universe)
    ranks = {s: i + 1 for i, (_v, s) in enumerate(ordered)}
    assert ranks == fx["expected"]["ranks_ascending_slope"]
    sh_scores = {sym: own_share_mean(panel, sym, stamp, universe=universe, window_rows=4) for sym in universe}
    desc = {s: i + 1 for i, (_v, s) in enumerate(sorted((-sh_scores[s], s) for s in universe))}
    assert desc == fx["expected"]["ranks_descending_own_share"]


def test_golden_math_window_refusals_fail_closed():
    panel, universe, stamp = _math_world()
    # fewer than 2 paired changes (window_rows < 3) is a construction error
    with pytest.raises(ContractViolation):
        cycle_slope(panel, "MA", stamp, universe=universe, window_rows=2)
    # the frozen 29-row anchor window cannot exist on 7 rows: every symbol
    # is INELIGIBLE and the book layer refuses (flat start, no book)
    scores = signal_scores_at(
        ANCHOR_ARM, oi_by_symbol=panel, stamp_ns=stamp, universe=universe
    )
    assert scores == {}
    with pytest.raises(EligibilityShortfall):
        compute_targets_at(
            ANCHOR_ARM, oi_by_symbol=panel, stamp_ns=stamp, universe=universe
        )
    # warmup guard: the frozen 55-row pool is absent on this world
    with pytest.raises(ContractViolation):
        assert_first_stamp_warmup(panel, universe=universe, first_stamp_ns=stamp)


def test_golden_book_anchor_chain_flat_start_and_median_exit():
    fx = _load("cyc_book_fixture.json")
    universe = fx["hand_computed_world"]["universe"]
    panel = _panel(fx["rows"], universe)
    t1 = int(fx["hand_computed_world"]["decision_stamps"]["T1"])
    t2 = int(fx["hand_computed_world"]["decision_stamps"]["T2"])
    exp = fx["expected_books"]

    # slopes at T1/T2 match the closed form (11 c / (C - c))
    for stamp, regime in ((t1, "regime_A"), (t2, "regime_B")):
        scores = signal_scores_at(
            ANCHOR_ARM, oi_by_symbol=panel, stamp_ns=stamp, universe=universe
        )
        for sym, want in fx["expected_slopes"][regime].items():
            assert scores[sym] == pytest.approx(want, abs=1e-12)

    # T1 flat-start book (hand): longs = S05..S08, shorts = S01..S04
    book1 = compute_targets_at(
        ANCHOR_ARM, oi_by_symbol=panel, stamp_ns=t1, universe=universe
    )
    want1 = exp["anchor_T1_flat_start"]
    assert dict(book1["longs"]) == want1["longs"]
    assert dict(book1["shorts"]) == want1["shorts"]
    ranks1 = dict(book1["diagnostics"]["ranks"])
    for sym, rank in fx["expected_ranks_ascending"]["T1"].items():
        assert ranks1[sym] == rank
    assert book1["diagnostics"]["median_rank"] == want1["median_rank"]
    assert book1["carried_forward"] is False
    assert book1["confirmatory"]["status"] == "CONFIRMATORY"

    # T2 hysteresis book (hand): the ln2 amplitude moved S01 -> S05, so the
    # held long S05 crosses beyond the median (rank 12 > 6) and FLIPS
    # short; the held short S01 crosses below it (rank 1 < 6) and flips
    # long; buffer never forces an exit.
    prev1 = {sym: float(w) for sym, w in book1["weights"]}
    book2 = compute_targets_at(
        ANCHOR_ARM, oi_by_symbol=panel, stamp_ns=t2, universe=universe, prev_book=prev1
    )
    want2 = exp["anchor_T2_hysteresis"]
    assert dict(book2["longs"]) == want2["longs"]
    assert dict(book2["shorts"]) == want2["shorts"]
    assert book2["diagnostics"]["flips"] == want2["flips"]
    ranks2 = dict(book2["diagnostics"]["ranks"])
    for sym, rank in fx["expected_ranks_ascending"]["T2"].items():
        assert ranks2[sym] == rank
    # gross <= 1.0 and |w| <= 0.30 by construction, at both stamps
    for book in (book1, book2):
        assert book["diagnostics"]["gross_after_weights"] == pytest.approx(1.0, abs=1e-12)
        assert book["diagnostics"]["max_abs_weight"] == pytest.approx(0.125, abs=1e-12)


def test_golden_book_neighbour_same_scores_same_books():
    fx = _load("cyc_book_fixture.json")
    universe = fx["hand_computed_world"]["universe"]
    panel = _panel(fx["rows"], universe)
    t1 = int(fx["hand_computed_world"]["decision_stamps"]["T1"])
    t2 = int(fx["hand_computed_world"]["decision_stamps"]["T2"])
    # identical construction over 14 changes: scores equal the anchor's at
    # both stamps on this world (assert the fixture's expectation)
    for stamp in (t1, t2):
        anchor = signal_scores_at(ANCHOR_ARM, oi_by_symbol=panel, stamp_ns=stamp, universe=universe)
        neighbour = signal_scores_at(NEIGHBOUR_ARM, oi_by_symbol=panel, stamp_ns=stamp, universe=universe)
        assert anchor.keys() == neighbour.keys()
        for sym in anchor:
            assert neighbour[sym] == pytest.approx(anchor[sym], abs=1e-12)
    # chained books coincide
    prev: dict[str, float] = {}
    for stamp in (t1, t2):
        a = compute_targets_at(ANCHOR_ARM, oi_by_symbol=panel, stamp_ns=stamp, universe=universe, prev_book=prev)
        n = compute_targets_at(NEIGHBOUR_ARM, oi_by_symbol=panel, stamp_ns=stamp, universe=universe, prev_book=prev)
        assert a["weights"] == n["weights"]
        prev = {sym: float(w) for sym, w in a["weights"]}


def test_golden_book_control_own_share_descending_book():
    fx = _load("cyc_book_fixture.json")
    universe = fx["hand_computed_world"]["universe"]
    panel = _panel(fx["rows"], universe)
    t1 = int(fx["hand_computed_world"]["decision_stamps"]["T1"])
    t2 = int(fx["hand_computed_world"]["decision_stamps"]["T2"])
    exp = fx["expected_books"]

    # T1: SH values (hand) and the DESCENDING rank presentation (rank 1 =
    # highest share = S12, the constant-1000 dominance name)
    book1 = compute_targets_at(
        CONTROL_ARM, oi_by_symbol=panel, stamp_ns=t1, universe=universe
    )
    want1 = exp["control_T1_flat_start"]
    scores1 = signal_scores_at(CONTROL_ARM, oi_by_symbol=panel, stamp_ns=t1, universe=universe)
    for sym, want in want1["own_share"].items():
        assert scores1[sym] == pytest.approx(want, abs=1e-15)
    ranks_desc = dict(book1["diagnostics"]["ranks_desc"])
    for sym, rank in want1["ranks_desc"].items():
        assert ranks_desc[sym] == rank
    # the BOOK is long lowest-share / short highest-share (hand)
    assert dict(book1["longs"]) == want1["longs"]
    assert dict(book1["shorts"]) == want1["shorts"]
    assert sorted(set(ranks_desc) - set(dict(book1["weights"]))) == sorted(want1["flat"])

    # T2 hysteresis (hand): S05 (long) crosses beyond the median -> flips
    # short; S01 (short) crosses below -> flips long; S12 stays short.
    prev1 = {sym: float(w) for sym, w in book1["weights"]}
    book2 = compute_targets_at(
        CONTROL_ARM, oi_by_symbol=panel, stamp_ns=t2, universe=universe, prev_book=prev1
    )
    want2 = exp["control_T2_hysteresis"]
    scores2 = signal_scores_at(CONTROL_ARM, oi_by_symbol=panel, stamp_ns=t2, universe=universe)
    for sym, want in want2["own_share"].items():
        assert scores2[sym] == pytest.approx(want, abs=1e-15)
    ranks_desc2 = dict(book2["diagnostics"]["ranks_desc"])
    for sym, rank in want2["ranks_desc"].items():
        assert ranks_desc2[sym] == rank
    assert dict(book2["longs"]) == want2["longs"]
    assert dict(book2["shorts"]) == want2["shorts"]
    assert book2["diagnostics"]["flips"] == want2["flips"]


def test_golden_book_incomplete_cross_section_fails_closed():
    fx = _load("cyc_book_fixture.json")
    universe = fx["hand_computed_world"]["universe"]
    panel = _panel(fx["rows"], universe)
    t2 = int(fx["hand_computed_world"]["decision_stamps"]["T2"])
    # A MISSING ROW (deleted) makes that day absent from the symbol's
    # paired presence, so the window shifts back deterministically to the
    # last COMPLETE cross-section row (the D2 panel precedent): the
    # shifted scores equal the scores on the explicitly truncated panel
    # and no partial aggregate is formed.
    broken = {sym: list(rows) for sym, rows in panel.items()}
    broken["S07"] = broken["S07"][:-1]
    truncated = {sym: rows[:-1] for sym, rows in panel.items()}
    got = signal_scores_at(
        ANCHOR_ARM, oi_by_symbol=broken, stamp_ns=t2, universe=universe
    )
    want = signal_scores_at(
        ANCHOR_ARM, oi_by_symbol=truncated, stamp_ns=t2, universe=universe
    )
    assert got.keys() == want.keys()
    for sym in want:
        assert got[sym] == pytest.approx(want[sym], abs=1e-15)
    # A BROKEN VALUE INSIDE the window (non-positive level -> the pair's
    # log change is undefined but the day stays PRESENT) fails the window
    # CLOSED: EVERY symbol turns INELIGIBLE (no back-fill, no partial
    # aggregate) and the book layer refuses.
    gapped = {sym: list(rows) for sym, rows in panel.items()}
    gapped["S07"][39] = (gapped["S07"][39][0], 0.0)  # row 40 level broken
    assert signal_scores_at(
        ANCHOR_ARM, oi_by_symbol=gapped, stamp_ns=t2, universe=universe
    ) == {}
    with pytest.raises(EligibilityShortfall):
        compute_targets_at(
            ANCHOR_ARM, oi_by_symbol=gapped, stamp_ns=t2, universe=universe
        )
    # the same broken value breaks the control's share denominator
    assert signal_scores_at(
        CONTROL_ARM, oi_by_symbol=gapped, stamp_ns=t2, universe=universe
    ) == {}


# ------------------------------------------------------------------------- #
# (b) THE L-V14-0 COST-SCALING REGRESSION on the family's books
# ------------------------------------------------------------------------- #
WEEK_NS = 7 * DAY_NS
T0_NS = int(datetime(2025, 1, 6, tzinfo=timezone.utc).timestamp()) * 1_000_000_000
FAMILY_LEGS = tuple(f"SYM{i:02d}" for i in range(16))


def _family_shape_book(n_legs: int) -> dict[str, float]:
    """The golden anchor book's shape: K/2 longs + K/2 shorts at |w| = 0.125.

    This is exactly the hand-computed anchor book of the 12-name golden
    world (4+4 legs at +/-0.125); 8 and 16 legs keep the per-fill size so
    cost can only scale with the FILL COUNT.
    """
    if n_legs % 2:
        raise ContractViolation("fixture books need an even leg count")
    half = n_legs // 2
    weights = {sym: 0.125 for sym in FAMILY_LEGS[:half]}
    weights.update({sym: -0.125 for sym in FAMILY_LEGS[half : 2 * half]})
    return weights


class _FamilyShapeBook(GenericStrategyBase):
    """Synthetic plugin emitting a CONSTANT family-shaped target book.

    The book opens once (entry fills), is HELD unchanged at every
    intermediate weekly stamp (zero weight delta -> zero cost iff and only
    if the kernel charges per fill, never per stamp on open positions),
    and realises once at the trailing force-flat edge (exit fills).
    """

    def __init__(self, *, n_instants: int, n_legs: int) -> None:
        self._instants = tuple(T0_NS + i * WEEK_NS for i in range(n_instants))
        self._weights = _family_shape_book(n_legs)
        self._identity = StrategyIdentity(
            strategy_id="v14i-oicyc-cost-fixture",
            family_id=FAMILY_ID,
            arm_config_id="cost-scaling-fixture",
            direction="long_short",
            window_start_iso="2025-01-01T00:00:00Z",
            window_end_iso="2025-06-01T00:00:00Z",
            config={"rule": "constant_family_shape_book"},
        )

    def identity(self) -> StrategyIdentity:
        return self._identity

    def cost_model(self) -> CostModel:
        return CostModel(
            taker_fee_bps=FEE_BPS,
            adverse_tick_slip_floor=1,
            default_tick_sizes={sym: TICK for sym in FAMILY_LEGS},
        )

    def tradeable_universe(self) -> tuple[str, ...]:
        return tuple(sorted(self._weights))

    def schedule(self) -> ImmutableSchedule:
        return ImmutableSchedule(
            instants=self._instants,
            source="tests.test_v14_family2_oicyc._FamilyShapeBook (weekly)",
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
                price=PRICE,
                fill_open_ns=fill_ns,
                fill_bar_close_ns=fill_ns,
            )
            for sym in sorted(set(symbols))
        )

    def marks_at(
        self, symbols: Sequence[str], instant_ns: int
    ) -> dict[str, Optional[float]]:
        del instant_ns
        return {str(sym): PRICE for sym in sorted(set(symbols))}

    def settlements(self, symbol: str) -> tuple[Any, ...]:
        return ()


def _run_shape(n_instants: int, n_legs: int, stress: StressSpec | None = None):
    return run_strategy(
        _FamilyShapeBook(n_instants=n_instants, n_legs=n_legs),
        stress=stress,
        write_artifact_file=False,
    )


def test_lv14_0_family_book_cost_strictly_linear_in_fills():
    """2N fills cost EXACTLY 2x N fills on the family's book shape.

    Hand world (frozen V10 floors): rate = 5e-4 fee + 1e-4 slip = 6e-4 per
    unit notional; the golden anchor book holds 8 legs at |w| = 0.125, so
    entry + force-flat exit churn 8 * 0.125 = 1.0 of notional ONCE each:
    cost = 1.0 * 6e-4 * 2 = 0.0012.  Doubling the legs at the SAME
    per-fill size doubles the fills (32 vs 16) and the cost exactly.
    """
    eight = _run_shape(n_instants=6, n_legs=8)
    sixteen = _run_shape(n_instants=6, n_legs=16)
    cost8 = eight["portfolio_metrics"]["cost_charged_sum"]
    cost16 = sixteen["portfolio_metrics"]["cost_charged_sum"]
    assert cost8 == pytest.approx(0.0012, abs=1e-15)
    assert cost16 == pytest.approx(0.0024, abs=1e-15)
    assert cost16 == 2 * cost8  # strictly linear in the number of fills


def test_lv14_0_long_hold_book_costs_same_as_short_hold_same_fills():
    """Holding length cannot move cost: identical fills -> identical cost."""
    short_hold = _run_shape(n_instants=6, n_legs=8)    # 16 fills over 5 spans
    long_hold = _run_shape(n_instants=12, n_legs=8)    # SAME 16 fills, 11 spans
    assert (
        long_hold["portfolio_metrics"]["cost_charged_sum"]
        == short_hold["portfolio_metrics"]["cost_charged_sum"]
    )
    assert long_hold["portfolio_metrics"]["cost_charged_sum"] == pytest.approx(
        0.0012, abs=1e-15
    )
    # NOT ONE unit of cost may accrue at a HELD stamp: every boundary
    # between the opening one and the final force-flat exit charges zero.
    for result in (short_hold, long_hold):
        rows = sorted(result["daily_returns"], key=lambda r: r["decision_ns"])
        for row in rows[1:-1]:
            assert row["cost_charged_per_unit"] == 0.0, row
        # entry churn = 8 legs x 0.125 = 1.0 notional -> 1.0 * RATE; the
        # trailing force-flat exit churns the same 1.0 -> 1.0 * RATE.
        assert rows[0]["cost_charged_per_unit"] == pytest.approx(RATE, abs=1e-15)
        assert rows[-1]["cost_charged_per_unit"] == pytest.approx(RATE, abs=1e-15)


def test_lv14_0_stress_tiers_differ_from_base_and_each_other():
    """fee x1.5 / +2 ticks / +1 delay: distinct tiers on the SAME fills.

    Hand: base 0.00060/unit -> 0.0012; fee x1.5 0.00085 -> 0.0017; +2
    ticks (3 total) 0.00080 -> 0.0016 -- the frozen 12:17:16 ratio.
    """
    base = _run_shape(n_instants=6, n_legs=8)
    fee_up = _run_shape(
        n_instants=6, n_legs=8,
        stress=StressSpec(name="fee_x1_5", fee_multiplier=1.5, tick_slip_ticks=1),
    )
    ticks_up = _run_shape(
        n_instants=6, n_legs=8,
        stress=StressSpec(name="plus2ticks", fee_multiplier=1.0, tick_slip_ticks=3),
    )
    c_base = base["portfolio_metrics"]["cost_charged_sum"]
    c_fee = fee_up["portfolio_metrics"]["cost_charged_sum"]
    c_ticks = ticks_up["portfolio_metrics"]["cost_charged_sum"]
    assert c_base == pytest.approx(0.0012, abs=1e-15)
    assert c_fee == pytest.approx(0.0017, abs=1e-15)
    assert c_ticks == pytest.approx(0.0016, abs=1e-15)
    assert len({c_base, c_fee, c_ticks}) == 3
    assert c_fee == pytest.approx(c_base * 17.0 / 12.0, rel=1e-12)
    assert c_ticks == pytest.approx(c_base * 16.0 / 12.0, rel=1e-12)


# ------------------------------------------------------------------------- #
# Synthetic 19-name staged-OI world for the REAL plugin through the runner
# ------------------------------------------------------------------------- #
WORLD_BASE = datetime(2025, 6, 30, tzinfo=timezone.utc)
WORLD_UNIVERSE = tuple(f"SYM{i:02d}" for i in range(1, 20))  # 19 tradeable
WORLD_BENCH = "BTCUSDT"
#: phase-aligned GROWTH FACTORS on the last four names (ascending rank
#: order: the 15 zero-amplitude names rank first by name, then ln1.1..ln2);
#: up rows sit at 100 x factor, down rows at 100.
WORLD_FACT = {"SYM16": 2.0, "SYM17": 1.5, "SYM18": 1.25, "SYM19": 1.1}
WORLD_END = datetime(2026, 8, 21, tzinfo=timezone.utc)


def _world_oi() -> dict[str, list[tuple[int, float]]]:
    """Daily 23:55Z OI rows 2025-06-30..2026-08-21 (>= 55 rows at stamp 1).

    Continuous up/down alternation on the four amplitude names (up on even
    day offsets), constant 100 elsewhere.  Any 28 consecutive paired
    changes are balanced (14/14), so every decision stamp sees the same
    hand-computable slopes: 18 c / (C - c) with C = sum of the dlog
    amplitudes (ln2 + ln1.5 + ln1.25 + ln1.1).
    """
    out: dict[str, list[tuple[int, float]]] = {}
    days = (WORLD_END - WORLD_BASE).days + 1
    for sym in WORLD_UNIVERSE:
        rows: list[tuple[int, float]] = []
        g = WORLD_FACT.get(sym)
        for i in range(days):
            d = WORLD_BASE + timedelta(days=i)
            stamp = int(d.replace(hour=23, minute=55, tzinfo=timezone.utc).timestamp()) * 1_000_000_000
            if g is None:
                level = 100.0
            else:
                level = 100.0 * g if i % 2 == 0 else 100.0
            rows.append((stamp, level))
        out[sym] = rows
    return out


def _world_bars() -> dict[str, tuple[Bar, ...]]:
    """Completed 15m bars around every decision stamp and fold end.

    Five slots per instant: the covering slot (open == instant) for marks
    plus four later slots so the pinned next-allowed-fill and the +1-delay
    stress both resolve.  Prices are the constant hand price 100.0.
    """
    instants = sorted(
        set(stamp_calendar())
        | {
            int(parse_iso_utc("2025-12-21T00:00:00Z")),
            int(parse_iso_utc("2026-04-21T00:00:00Z")),
            int(parse_iso_utc("2026-08-21T00:00:00Z")),
        }
    )
    bars: list[Bar] = []
    for instant in instants:
        for k in range(5):
            slot_open = instant + k * BAR_INTERVAL_NS
            bars.append(
                Bar(
                    ts_event_ns=slot_open + BAR_INTERVAL_NS,
                    open=PRICE,
                    high=PRICE,
                    low=PRICE,
                    close=PRICE,
                )
            )
    return {sym: tuple(bars) for sym in set(WORLD_UNIVERSE) | {WORLD_BENCH}}


def _world_plugin(arm_id: str, *, oi: dict | None = None, tick: float = TICK) -> OicycPlugin:
    return OicycPlugin(
        arm_id=arm_id,
        oi_by_symbol=oi if oi is not None else _world_oi(),
        bars_by_symbol=_world_bars(),
        tick_sizes={sym: tick for sym in set(WORLD_UNIVERSE) | {WORLD_BENCH}},
    )


def _world_expected_anchor_book() -> dict[str, float]:
    """The hand world's chained anchor book (constant across all stamps).

    n = 19: n_lo = n_hi = 6, median rank 10, w = min(0.5/6, 0.30) = 1/12.
    Ascending slope ranks: SYM01..SYM15 (zero amplitude) ranks 1..15 by
    name, then SYM19 (16), SYM18 (17), SYM17 (18), SYM16 (19).  Longs =
    ranks 1..6; shorts = ranks 14..19 = {SYM14, SYM15, SYM16..SYM19}.
    """
    w = min(0.5 / 6, 0.30)
    book = {sym: w for sym in WORLD_UNIVERSE[:6]}
    for sym in ("SYM14", "SYM15", "SYM16", "SYM17", "SYM18", "SYM19"):
        book[sym] = -w
    return book


def test_lv14_0_real_plugin_runner_long_hold_cost_once_and_zero_intermediate():
    """The REAL plugin through the frozen runner: cost only on FILLS at the
    six weight transitions; every held stamp charges exactly zero; replay
    is byte-identical.

    Hand: the constant book churns 12 legs x (1/12) = 1.0 of notional per
    side transition.  The frozen fold-terminal force-flat realises each
    fold flat at its last executable slot, so the transition set is exactly
    {entry 08-25, flat 12-15, re-entry 12-22, flat 04-13, re-entry 04-27,
    final force-flat 08-17} = 6 transitions x 1.0 x rate = 6 * RATE
    = 0.0036 -- independent of the 45 held stamps between them.
    """
    plugin = _world_plugin(ANCHOR_ARM)
    result = run_strategy(plugin, stress=None, write_artifact_file=False)
    metrics = result["portfolio_metrics"]
    assert metrics["cost_charged_sum"] == pytest.approx(6.0 * RATE, abs=1e-15)
    # the ledger legs are exactly the 12 hand-book symbols
    expected = _world_expected_anchor_book()
    positions = result["positions"]
    assert {str(p["symbol"]) for p in positions} == set(expected)
    # the runner re-accounts each held leg per boundary: 48 boundaries
    # carry legs (16 per fold; each fold's terminal stamp is flat) x 12
    assert len(positions) == 48 * 12
    assert all(int(p["exit_ns"]) > int(p["entry_ns"]) for p in positions)
    rows = sorted(result["daily_returns"], key=lambda r: r["decision_ns"])
    assert len(rows) == 52
    transition_stamps = {
        parse_iso_utc("2025-08-25T00:00:00Z"),
        parse_iso_utc("2025-12-15T00:00:00Z"),
        parse_iso_utc("2025-12-22T00:00:00Z"),
        parse_iso_utc("2026-04-13T00:00:00Z"),
        parse_iso_utc("2026-04-27T00:00:00Z"),
        parse_iso_utc("2026-08-17T00:00:00Z"),
    }
    for row in rows:
        if int(row["decision_ns"]) in transition_stamps:
            assert row["cost_charged_per_unit"] == pytest.approx(RATE, abs=1e-15), row
        else:
            # NOT ONE unit of cost may accrue at a HELD stamp (L-V14-0)
            assert row["cost_charged_per_unit"] == 0.0, row
    # the opened book IS the hand-computed chained book at every retained
    # non-terminal stamp, and FLAT at the fold-terminal force-flat stamps
    from research.v14.families.oicyc.plugin import (
        REASON_FOLD_TERMINAL_FORCE_FLAT,
        _fold_terminal_stamps,
    )

    terminals = _fold_terminal_stamps()
    assert terminals == {
        parse_iso_utc("2025-12-15T00:00:00Z"),
        parse_iso_utc("2026-04-13T00:00:00Z"),
        parse_iso_utc("2026-08-17T00:00:00Z"),
    }
    universe = plugin.tradeable_universe()
    stress = plugin.baseline_stress()
    purged_stamp = parse_iso_utc("2026-04-20T00:00:00Z")
    for instant in stamp_calendar()[:-1]:
        payload = plugin.targets_at(instant, universe=universe, stress=stress)
        if instant in terminals:
            assert payload["weights"] == []
            assert payload["reason_code"] == REASON_FOLD_TERMINAL_FORCE_FLAT
        elif instant == purged_stamp:
            # the purged gap carries the previous retained book byte-equal
            # (the flat 2026-04-13 fold-terminal force-flat)
            assert payload == plugin.targets_at(
                parse_iso_utc("2026-04-13T00:00:00Z"), universe=universe, stress=stress
            )
        else:
            got = {sym: float(w) for sym, w in payload["weights"]}
            assert got == pytest.approx(expected, abs=1e-12)
    # replay of the SAME book: identical cost, identical hashes (cost once)
    replay = run_strategy(_world_plugin(ANCHOR_ARM), stress=None, write_artifact_file=False)
    assert replay["portfolio_metrics"]["cost_charged_sum"] == metrics["cost_charged_sum"]
    assert replay["hashes"] == result["hashes"]


# ------------------------------------------------------------------------- #
# DELTA1 regression: dropped-fold traversal + intact-schedule byte identity
# ------------------------------------------------------------------------- #
#: Intact-schedule byte digests recorded at the PRE-FIX lane HEAD 0b661a8,
#: BEFORE the delta1 fix re-derived ``plugin._fold_terminal_stamps`` from the
#: full frozen calendar.  First value per arm: SHA-256 over the canonical
#: JSON (sort_keys, compact separators) of every ``targets_at`` payload
#: across the FULL frozen 52-stamp schedule under the baseline stress.
#: Second value per arm: the frozen runner's own full-result hash
#: (``run_strategy(...).hashes["result_sha256"]``).  The fix is an
#: integration-correctness change only: every one of these bytes must stay
#: identical (the acceptance bar), which these assertions pin forever.
DELTA1_INTACT_PAYLOAD_DIGESTS = {
    ANCHOR_ARM: "a1c13b6d3338611dec5ee359380d67899f6d770ab2da254286b78970b334cee1",
    NEIGHBOUR_ARM: "81e764d12bcb561b58aafcad53ec8a9e3dd54f195503f84307b82b8a62f0f232",
    CONTROL_ARM: "46ef410e0800b8d07bad343abab8361ff609b86291bf062ed2448709cf5b8abd",
}
DELTA1_INTACT_RUNNER_RESULT_SHA256 = {
    ANCHOR_ARM: "a39c3d251ba538c6cc4932e2d013e0430293e81f3ff17246a396b01691d9ed35",
    NEIGHBOUR_ARM: "f714081736759437b055c16f0e28f2fded5c916aa38852a9913e58ee86b96f42",
    CONTROL_ARM: "2200b2336425079a38e1a29a31d745ed2a4dd3dca91c801ec1dc32a3ca2c1e1f",
}
#: The NEW dropped-fold traversal product (no pre-fix value exists -- the
#: pre-fix chain REFUSED with "pinned fold F0 received no decision stamps"):
#: the frozen runner's full-result hash on the drop_one_fold cell (F0
#: dropped) for the anchor arm on this world; cost is exactly 4 fill
#: transitions x 1.0 notional x RATE (F1 entry + fold-terminal flat +
#: re-entry, then the runner's final force-flat) = 0.0024.
DELTA1_DROP_F0_RUNNER_RESULT_SHA256 = (
    "78b5c08fa66432bcc5581426a00589f0befdf051146db28f8e60fd96390020c8"
)


def _delta1_targets_digest(
    plugin: OicycPlugin, *, universe, stress
) -> str:
    """SHA-256 over the canonical JSON of every full-schedule payload."""
    digest = hashlib.sha256()
    for instant in stamp_calendar():
        payload = plugin.targets_at(instant, universe=universe, stress=stress)
        digest.update(
            json.dumps(
                payload, sort_keys=True, separators=(",", ":"), allow_nan=False
            ).encode("utf-8")
        )
    return digest.hexdigest()


def test_delta1_dropped_fold_traverses_and_intact_books_byte_identical():
    """Driver-discovered V14 integration defect, discharged (DELTA1).

    Pre-fix, the plugin's chained book derived the fold-terminal stamps
    from the RETAINED (stress-filtered) decision stamps:
    ``_fold_terminal_stamps(retained)`` called ``fold_assignments``, which
    refuses when a fold has no retained members -- so the frozen generic
    runner (which queries ``targets_at`` at every open instant, including a
    dropped fold's stamps) crashed on ANY drop_one_fold traversal.  The fix
    (OITD/LIQEPIS V13 + basislv V14 precedent): fold terminals are derived
    from the FULL frozen calendar -- a calendar property -- and the
    retention/drop is applied as a filter.

    This regression pins BOTH sides:
      1. the drop_one_fold cell (and each single-fold drop at plugin level)
         now TRAVERSES end-to-end through the frozen runner; and
      2. the intact (non-dropped) schedule books are BYTE-IDENTICAL to the
         pre-fix recorded digests above -- no frozen identity constant,
         window, book rule, cost, clock or threshold moved.
    """
    from research.v14.families.oicyc.plugin import (
        REASON_CARRIED_FLAT_START,
        REASON_FOLD_TERMINAL_FORCE_FLAT,
        _fold_terminal_stamps,
    )

    # terminals are a FULL-CALENDAR property: identical under any stress
    expected_terminals = {
        parse_iso_utc("2025-12-15T00:00:00Z"),
        parse_iso_utc("2026-04-13T00:00:00Z"),
        parse_iso_utc("2026-08-17T00:00:00Z"),
    }
    assert _fold_terminal_stamps() == expected_terminals

    # fold ownership of every schedule stamp on the frozen calendar
    fold_of: dict[int, int] = {}
    for index, _label, members, _purged in fold_assignments(list(stamp_calendar())):
        for stamp in members:
            fold_of[int(stamp)] = index

    for arm_id in (ANCHOR_ARM, NEIGHBOUR_ARM, CONTROL_ARM):
        plugin = _world_plugin(arm_id)
        universe = plugin.tradeable_universe()
        baseline = plugin.baseline_stress()

        # -- (2) intact-schedule byte identity against the PRE-FIX digests
        assert (
            _delta1_targets_digest(plugin, universe=universe, stress=baseline)
            == DELTA1_INTACT_PAYLOAD_DIGESTS[arm_id]
        )
        intact = run_strategy(
            _world_plugin(arm_id), stress=None, write_artifact_file=False
        )
        assert (
            intact["hashes"]["result_sha256"]
            == DELTA1_INTACT_RUNNER_RESULT_SHA256[arm_id]
        )

        # -- (1) every single-fold drop traverses the FULL frozen schedule
        for dropped_index in (0, 1, 2):
            spec = dataclasses.replace(
                baseline, name="drop_one_fold", dropped_fold_index=dropped_index
            )
            drop_universe = plugin.universe(spec)
            retained = set(plugin.decision_instants(stress=spec))
            for instant in stamp_calendar()[:-1]:
                payload = plugin.targets_at(
                    instant, universe=drop_universe, stress=spec
                )
                assert payload["confirmatory"]["status"] == "CONFIRMATORY"
                if int(instant) in retained:
                    # a RETAINED fold-terminal force-flats; every other
                    # retained stamp is the discretionary chained book
                    if int(instant) in expected_terminals:
                        assert (
                            payload["reason_code"]
                            == REASON_FOLD_TERMINAL_FORCE_FLAT
                        )
                        assert payload["weights"] == []
                else:
                    # a NON-decision instant (the dropped fold's stamps and
                    # the purge gap) CARRIES: byte-equal to the last prior
                    # retained decision, or the explicit flat start
                    prior_stamps = [s for s in retained if s < int(instant)]
                    if prior_stamps:
                        assert payload == plugin.targets_at(
                            max(prior_stamps), universe=drop_universe, stress=spec
                        )
                    else:
                        assert payload["reason_code"] == REASON_CARRIED_FLAT_START
            # structural: the DROPPED fold's own terminal is not a retained
            # decision stamp -- it never force-flats, the chain carries
            # through it (the loop above pins that carry byte-equal)
            dropped_terminal = [
                s for s in expected_terminals if fold_of[int(s)] == dropped_index
            ]
            assert len(dropped_terminal) == 1
            assert int(dropped_terminal[0]) not in retained

        # F0 dropped with no prior retained decision: the dropped stamps
        # carry the FLAT START (explicit reason code)
        spec0 = dataclasses.replace(
            baseline, name="drop_one_fold", dropped_fold_index=0
        )
        first = plugin.targets_at(
            parse_iso_utc("2025-08-25T00:00:00Z"),
            universe=plugin.universe(spec0),
            stress=spec0,
        )
        assert first["reason_code"] == REASON_CARRIED_FLAT_START
        assert first["weights"] == [] and first["carried_forward"] is True

    # -- (1) the frozen drop_one_fold CELL through the frozen runner,
    #         end-to-end: completes with the pinned new-behavior bytes
    anchor_plugin = _world_plugin(ANCHOR_ARM)
    spec0 = dataclasses.replace(
        anchor_plugin.baseline_stress(), name="drop_one_fold", dropped_fold_index=0
    )
    dropped = run_strategy(
        _world_plugin(ANCHOR_ARM), stress=spec0, write_artifact_file=False
    )
    assert dropped["hashes"]["result_sha256"] == DELTA1_DROP_F0_RUNNER_RESULT_SHA256
    assert dropped["portfolio_metrics"]["cost_charged_sum"] == pytest.approx(
        4.0 * RATE, abs=1e-15
    )


def test_plugin_chain_deterministic_across_arms_and_call_order():
    """One book per arm: the chained books are call-order independent and
    identical across plugin instances built from the same injected data."""
    for arm_id in (ANCHOR_ARM, NEIGHBOUR_ARM, CONTROL_ARM):
        a = _world_plugin(arm_id)
        b = _world_plugin(arm_id)
        universe = a.tradeable_universe()
        stress = a.baseline_stress()
        stamps = stamp_calendar()
        forward = [a.targets_at(s, universe=universe, stress=stress) for s in stamps]
        backward = [b.targets_at(s, universe=universe, stress=stress) for s in reversed(stamps)]
        backward = backward[::-1]
        assert forward == backward
        # every retained stamp carries the CONFIRMATORY metadata block
        for payload in forward:
            assert payload["confirmatory"]["status"] == "CONFIRMATORY"


# ------------------------------------------------------------------------- #
# (c) AVAILABILITY-LAG MUTATION TESTS (every adopted conditioning field)
# ------------------------------------------------------------------------- #
def test_mutation_oi_row_stamped_after_decision_is_invisible():
    """A decision at T never reads data dated after T: injecting a wild OI
    row stamped AFTER the decision changes NO payload byte."""
    fx = _load("cyc_book_fixture.json")
    universe = fx["hand_computed_world"]["universe"]
    panel = _panel(fx["rows"], universe)
    t2 = int(fx["hand_computed_world"]["decision_stamps"]["T2"])
    baseline = compute_targets_at(
        ANCHOR_ARM, oi_by_symbol=panel, stamp_ns=t2, universe=universe
    )
    baseline_control = compute_targets_at(
        CONTROL_ARM, oi_by_symbol=panel, stamp_ns=t2, universe=universe
    )
    # append a wild future row (stamped after the decision) to EVERY symbol
    poisoned = {
        sym: rows + [(rows[-1][0] + DAY_NS, 1e18 if i == 0 else 1.0)]
        for i, (sym, rows) in enumerate(panel.items())
    }
    assert compute_targets_at(
        ANCHOR_ARM, oi_by_symbol=poisoned, stamp_ns=t2, universe=universe
    ) == baseline
    assert compute_targets_at(
        CONTROL_ARM, oi_by_symbol=poisoned, stamp_ns=t2, universe=universe
    ) == baseline_control


def test_mutation_oi_boundary_stamp_is_readable_next_ns_is_not():
    """A staged OI row stamped EXACTLY T is readable (<= T); the same row
    stamped T + 1ns is NOT, and the window shifts deterministically."""
    panel, universe, stamp = _math_world()
    ln2, ln15 = math.log(2.0), math.log(1.5)
    readable = cycle_slope(panel, "MA", stamp, universe=universe, window_rows=4)
    assert readable == pytest.approx(4 * ln2 / ln15, abs=1e-12)
    # shift EVERY symbol's last row stamp one nanosecond past the decision
    # (the cross-section stays complete): the window now ends at row 6 --
    # a deterministic shift, never a guess -- and the slope equals the
    # value recomputed on the explicitly truncated panel.
    shifted = {
        sym: [(rows[-1][0] + 1, rows[-1][1])] + rows[:-1] if rows else rows
        for sym, rows in ((s, sorted(rows)) for s, rows in panel.items())
    }
    shifted = {s: sorted(rows) for s, rows in shifted.items()}
    got = cycle_slope(shifted, "MA", stamp, universe=universe, window_rows=4)
    truncated = {sym: rows[:-1] for sym, rows in panel.items()}
    want = cycle_slope(truncated, "MA", stamp, universe=universe, window_rows=4)
    assert got == pytest.approx(want, abs=1e-15)
    # observability of the deterministic shift on this periodic world: the
    # readable row count at T drops 7 -> 6 and the CONSUMED change-days
    # move back one row exactly (the slope VALUE is phase-invariant on
    # this world; the window identity is not).
    from research.v14.families.oicyc.strategy import warmup_rows_at

    assert warmup_rows_at(panel["MA"], stamp) == 7
    assert warmup_rows_at(shifted["MA"], stamp) == 6
    days_readable = sorted(daily_log_changes(panel["MA"], stamp))
    days_shifted = sorted(daily_log_changes(shifted["MA"], stamp))
    assert days_shifted == days_readable[:-1]
    assert days_shifted != days_readable


def test_mutation_oi_all_rows_shifted_one_day_later_shifts_deterministically():
    """Shifting the staged-OI availability one day later moves each row's
    readability horizon exactly one day: at the SAME decision stamp the
    pipeline provably computes on the deterministically older window (the
    consumed row-stamps move back by one), and a shift that starves the
    frozen warmup/window floors refuses outright."""
    fx = _load("cyc_book_fixture.json")
    universe = fx["hand_computed_world"]["universe"]
    panel = _panel(fx["rows"], universe)
    t2 = int(fx["hand_computed_world"]["decision_stamps"]["T2"])
    shifted = {
        sym: [(t + DAY_NS, v) for t, v in rows]  # every row available 1 day later
        for sym, rows in panel.items()
    }
    # reference: the explicitly truncated panel (row 59 unreadable at T2)
    truncated = {sym: rows[:-1] for sym, rows in panel.items()}
    reference = compute_targets_at(
        ANCHOR_ARM, oi_by_symbol=truncated, stamp_ns=t2, universe=universe
    )
    got = compute_targets_at(
        ANCHOR_ARM, oi_by_symbol=shifted, stamp_ns=t2, universe=universe
    )
    assert got == reference  # deterministic shift, byte-equal
    # the consumed window genuinely moved: the readable row count at T2
    # drops 59 -> 58 and the newest consumed change-stamp moves back a day
    from research.v14.families.oicyc.strategy import warmup_rows_at

    assert warmup_rows_at(panel["S01"], t2) == 59
    assert warmup_rows_at(shifted["S01"], t2) == 58
    # the newest consumed ROW moved back one: the shifted world's newest
    # readable row is the (shifted) row 58, whose stamp lands exactly on
    # row 59's ORIGINAL stamp -- one row of availability lost, provably
    # the same values consumed (got == reference byte-equality above)
    # pushing availability 60 days later starves the frozen 29-row anchor
    # window at T2: every symbol turns INELIGIBLE and the book layer
    # refuses (a data insufficiency is a refusal, never an inference).
    pushed = {sym: [(t + 60 * DAY_NS, v) for t, v in rows] for sym, rows in panel.items()}
    assert signal_scores_at(
        ANCHOR_ARM, oi_by_symbol=pushed, stamp_ns=t2, universe=universe
    ) == {}
    with pytest.raises(EligibilityShortfall):
        compute_targets_at(
            ANCHOR_ARM, oi_by_symbol=pushed, stamp_ns=t2, universe=universe
        )
    with pytest.raises(ContractViolation):
        assert_first_stamp_warmup(pushed, universe=universe, first_stamp_ns=t2)


def test_mutation_oi_lookahead_gate_raises_fail_closed():
    """The availability gate refuses any consumed input stamped after its
    readable horizon (the p_freeze PIT authority), at decision AND fill
    horizons."""
    with pytest.raises(LookaheadViolation):
        assert_inputs_available(
            [parse_iso_utc("2026-01-05T00:00:00Z")],
            as_of_ns=parse_iso_utc("2026-01-04T00:00:00Z"),
            context="mutation",
        )
    # boundary: a record stamped exactly AT the horizon IS readable
    t = parse_iso_utc("2026-01-04T00:00:00Z")
    assert_inputs_available([t], as_of_ns=t, context="mutation_boundary")
    # a fill at slot-open F must refuse a decision payload dated after F
    decision = parse_iso_utc("2026-01-05T00:00:00Z")
    fill_open = decision + 15 * 60 * 1_000_000_000
    with pytest.raises(LookaheadViolation):
        assert_inputs_available(
            [fill_open + 1], as_of_ns=fill_open, context="next_allowed_fill"
        )


def test_mutation_bars_missing_slot_and_event_delay_shift_deterministically():
    """Bars (execution/pricing field): the fill lands at the first
    slot-open >= release; a missing slot shifts to the NEXT existing slot
    (never backwards, never fabricated); no bar at/after release -> NO
    fill (refusal)."""
    monday = parse_iso_utc("2026-01-05T00:00:00Z")
    release = monday + BAR_INTERVAL_NS

    def bar(slot_open: int, price: float) -> Bar:
        return Bar(
            ts_event_ns=slot_open + BAR_INTERVAL_NS,
            open=price, high=price, low=price, close=price,
        )

    # normal: fills at the 00:15Z slot-open at that bar's OPEN price
    bars = [bar(monday, 100.0), bar(release, 101.0), bar(release + BAR_INTERVAL_NS, 102.0)]
    fill = next_allowed_fill(bars, "SYM01", decision_ns=monday)
    assert fill.fill_open_ns == release
    assert fill.price == 101.0
    assert fill.event_offset == 0
    # stress +1 event delay: the NEXT slot's open, deterministically
    delayed = next_allowed_fill(bars, "SYM01", decision_ns=monday, event_delay_events=1)
    assert delayed.fill_open_ns == release + BAR_INTERVAL_NS
    assert delayed.price == 102.0
    # missing slot: the 00:15Z bar is absent -> the 00:30Z slot is the
    # first allowed slot-open (deterministic shift, never a substitute)
    gapped = [bar(monday, 100.0), bar(release + BAR_INTERVAL_NS, 102.0)]
    gapped_fill = next_allowed_fill(gapped, "SYM01", decision_ns=monday)
    assert gapped_fill.fill_open_ns == release + BAR_INTERVAL_NS
    assert gapped_fill.event_offset == 0
    # no completed bar at/after release -> NO event (refusal, fail-closed)
    assert next_allowed_fill([bar(monday, 100.0)], "SYM01", decision_ns=monday) is None
    # a non-midnight decision stamp is out of contract outright
    with pytest.raises(ContractViolation):
        next_allowed_fill(bars, "SYM01", decision_ns=monday + 1)
    # duplicate slots refuse (one completed bar per slot)
    with pytest.raises(ContractViolation):
        next_allowed_fill([bar(release, 101.0), bar(release, 101.0)], "SYM01", decision_ns=monday)
    # a bar stamped just before the boundary snaps forward to its slot
    assert snap_close_to_boundary(release - 64) == release


def test_mutation_bar_close_not_readable_by_the_fill():
    """The fill's readability horizon is its slot-open instant: the chosen
    bar's CLOSE stamp (slot-open + 15m) is strictly later and is never a
    readable input at the fill."""
    monday = parse_iso_utc("2026-01-05T00:00:00Z")
    release = monday + BAR_INTERVAL_NS
    bar = Bar(
        ts_event_ns=release + BAR_INTERVAL_NS,
        open=101.0, high=101.0, low=101.0, close=101.0,
    )
    fill = next_allowed_fill([bar], "SYM01", decision_ns=monday)
    assert fill.fill_open_ns == release
    with pytest.raises(LookaheadViolation):
        assert_inputs_available(
            [int(bar.ts_event_ns)], as_of_ns=int(fill.fill_open_ns),
            context="next_allowed_fill.bar_close",
        )


def test_mutation_funding_never_enters_any_signal_and_accrues_once():
    """Funding is COST ONLY: wild settlement values change NO target-book
    byte on any arm; accrual happens exactly ONCE per settlement inside a
    held span (never per holding-day) and never outside it."""
    oi = _world_oi()
    settlements = {
        sym: (
            {"publish_ts_ns": int(parse_iso_utc("2025-09-01T08:00:00Z")), "value": 0.0001},
            {"publish_ts_ns": int(parse_iso_utc("2025-09-01T16:00:00Z")), "value": 9.99},
            {"publish_ts_ns": int(parse_iso_utc("2025-09-02T08:00:00Z")), "value": -0.5},
        )
        for sym in WORLD_UNIVERSE
    }
    plain = _world_plugin(ANCHOR_ARM)
    funded = OicycPlugin(
        arm_id=ANCHOR_ARM,
        oi_by_symbol=oi,
        bars_by_symbol=_world_bars(),
        settlements_by_symbol=settlements,
        tick_sizes={sym: TICK for sym in set(WORLD_UNIVERSE) | {WORLD_BENCH}},
    )
    universe = plain.tradeable_universe()
    stress = plain.baseline_stress()
    for stamp in stamp_calendar()[:6]:
        assert (
            plain.targets_at(stamp, universe=universe, stress=stress)
            == funded.targets_at(stamp, universe=universe, stress=stress)
        )
    # accrual: exactly once per settlement inside [ts_opened, ts_closed]
    span = type(
        "Span", (), {
            "symbol": "SYM01",
            "signed_weight": 0.5,
            "start_ns": int(parse_iso_utc("2025-09-01T00:00:00Z")),
            "end_ns": int(parse_iso_utc("2025-09-02T00:00:00Z")),
        },
    )()
    flows = funded.funding_cashflows_for_spans([span])
    assert [f["publish_ts_ns"] for f in flows] == [
        int(parse_iso_utc("2025-09-01T08:00:00Z")),
        int(parse_iso_utc("2025-09-01T16:00:00Z")),
    ]  # the 09-02 settlement lies OUTSIDE the span (start < ts <= end)
    assert flows[0]["cashflow_per_unit_capital"] == pytest.approx(-0.5 * 0.0001, abs=1e-18)
    assert flows[1]["cashflow_per_unit_capital"] == pytest.approx(-0.5 * 9.99, abs=1e-12)


# ------------------------------------------------------------------------- #
# (d) zero-position refusal passthrough
# ------------------------------------------------------------------------- #
def test_zero_position_book_refused_at_builder_and_drop_one():
    # a cross-section below the structural tercile floor has NO book
    with pytest.raises(EligibilityShortfall):
        build_hysteresis_book({"A": 1.0, "B": 2.0})
    # an empty book after construction refuses
    with pytest.raises(EligibilityShortfall):
        build_hysteresis_book({"A": float("nan"), "B": float("inf")})
    # drop-one on a zero-position book refuses (never scored as a baseline)
    with pytest.raises(EligibilityShortfall):
        drop_one_book({})
    # a well-formed book drops its held max-|weight| symbol with the
    # remaining weights UNCHANGED (no renormalisation)
    book = {"A": 0.125, "B": 0.125, "C": -0.125, "D": -0.30}
    dropped = drop_one_book(book)
    assert dropped["dropped_symbol"] == "D"
    assert dropped["weights"] == [["A", 0.125], ["B", 0.125], ["C", -0.125]]


def test_zero_position_refusal_passthrough_publication(tmp_path):
    """An arm that would publish zero positions is REFUSED at publication,
    never scored as a zero baseline (L-V11-4 passthrough, family-keyed)."""
    refused = publish_v12_cell(
        strategy_id="hyp_a14_v14_a8_oicyc",
        family=FAMILY_ID,
        arm_id=ANCHOR_ARM,
        arm_config_digest="0" * 64,
        stress_signature=StressSpec(name="baseline"),
        window_start_iso="2025-08-22T00:00:00Z",
        window_end_iso="2026-08-21T00:00:00Z",
        scored_metrics={
            "score_valid": True,
            "net_return_sum": 0.0,
            "expectancy_per_day": 0.0,
            "max_drawdown": 0.0,
            "n_positions": 0,
            "n_decisions": 0,
            "n_fills": 0,
        },
        result_sha256="a" * 64,
        ledger_path=tmp_path / "oicyc_zero.jsonl",
        producer_head_sha="0" * 40,
    )
    assert refused["published"] is False
    assert refused["stage"] == STAGE_REFUSED
    assert refused["reasons"][0] == REFUSED_ZERO_POSITIONS
    assert refused["published_delta"] == 0 and refused["observed_delta"] == 1
    state = read_v12_ledger(tmp_path / "oicyc_zero.jsonl")
    assert state["count"] == 1
    assert state["rows"][0]["row_type"] != ROW_TYPE_CELL_RESULT


def test_zero_position_refusal_through_plugin_chain_broken_cross_section():
    """A broken cross-section at a RETAINED stamp raises through the
    plugin chain (no zero book is silently produced)."""
    fx = _load("cyc_book_fixture.json")
    universe = fx["hand_computed_world"]["universe"]
    panel = _panel(fx["rows"], universe)
    t1 = int(fx["hand_computed_world"]["decision_stamps"]["T1"])
    # a BROKEN level inside the first Monday's 28-change window poisons the
    # leave-one-out aggregate for the whole cross-section at that stamp
    broken = {sym: list(rows) for sym, rows in panel.items()}
    broken["S07"][29] = (broken["S07"][29][0], 0.0)  # row 30 level = 0.0
    fixture_bars = {
        sym: (
            Bar(
                ts_event_ns=t1 + BAR_INTERVAL_NS,
                open=PRICE, high=PRICE, low=PRICE, close=PRICE,
            ),
        )
        for sym in universe
    }
    fixture_bars[BENCHMARK_SYMBOL] = fixture_bars[universe[0]]
    plugin = OicycPlugin(
        arm_id=ANCHOR_ARM,
        oi_by_symbol=broken,
        bars_by_symbol=fixture_bars,
        tick_sizes={sym: TICK for sym in universe},
        assert_warmup=False,
    )
    # at the FIRST retained Monday the whole cross-section is INELIGIBLE:
    # the book layer refuses through the plugin chain (no zero-position
    # book is ever produced -- L-V11-4 passthrough)
    with pytest.raises(EligibilityShortfall):
        plugin.targets_at(
            stamp_calendar()[0], universe=sorted(universe), stress=plugin.baseline_stress()
        )


# ------------------------------------------------------------------------- #
# (e) fold force-flat boundary respected
# ------------------------------------------------------------------------- #
def test_fold_calendar_and_one_day_zone_purge_pinned():
    """The pinned F0/F1/F2 calendar with the frozen 1-day calendar-zone
    purge: 52 scheduled Mondays, 51 effective at 17/17/17; exactly the
    2026-04-20 stamp sits inside F1's purge zone (the measured V13/V14
    convention; A9F counts 17/17/17 for this family)."""
    stamps = stamp_calendar()
    assert len(stamps) == 52
    assert stamps[0] == parse_iso_utc(FIRST_STAMP_ISO)
    assert stamps[-1] == parse_iso_utc("2026-08-17T00:00:00Z")
    assignments = fold_assignments(list(stamps))
    effective, purged = effective_schedule(stamps)
    # fold_assignments returns the EFFECTIVE (zone-purged) members
    assert [len(m) for _i, _l, m, _p in assignments] == [17, 17, 17]
    assert len(effective) == 51
    assert purged == {"F1": [parse_iso_utc("2026-04-20T00:00:00Z")]}
    # the fold windows themselves are the pinned calendar, byte-for-byte
    from research.v14.families.oicyc.strategy import FOLD_WINDOWS

    assert FOLD_WINDOWS == (
        ("F0", "2025-08-22", "2025-12-21"),
        ("F1", "2025-12-22", "2026-04-21"),
        ("F2", "2026-04-22", "2026-08-21"),
    )


def test_fold_force_flat_no_position_span_crosses_a_fold_boundary():
    """Through the REAL frozen runner: every position span lies inside the
    fold that owns it and the final boundary is the force-flat edge."""
    plugin = _world_plugin(ANCHOR_ARM)
    result = run_strategy(plugin, stress=None, write_artifact_file=False)
    bounds = [
        (parse_iso_utc("2025-08-22T00:00:00Z"), parse_iso_utc("2025-12-21T00:00:00Z")),
        (parse_iso_utc("2025-12-22T00:00:00Z"), parse_iso_utc("2026-04-21T00:00:00Z")),
        (parse_iso_utc("2026-04-22T00:00:00Z"), parse_iso_utc("2026-08-21T00:00:00Z")),
    ]
    positions = result["positions"]
    assert positions, "the synthetic world must open positions"
    for position in positions:
        start, end = int(position["entry_ns"]), int(position["exit_ns"])
        assert any(lo <= start and end <= hi for lo, hi in bounds), (
            f"span [{iso_utc(start)}, {iso_utc(end)}] straddles a fold boundary"
        )
    # the purged stamp carries (no book opened there): the plugin answers
    # it with the previous retained book byte-equal -- the 2026-04-13
    # fold-terminal force-flat FLAT book
    purged = parse_iso_utc("2026-04-20T00:00:00Z")
    universe = plugin.tradeable_universe()
    stress = plugin.baseline_stress()
    retained = [s for s in stamp_calendar() if s < purged][-1]
    assert retained == parse_iso_utc("2026-04-13T00:00:00Z")
    carried = plugin.targets_at(purged, universe=universe, stress=stress)
    terminal_payload = plugin.targets_at(retained, universe=universe, stress=stress)
    assert carried == terminal_payload  # byte-equal carry (V13 OITD precedent)
    assert carried["weights"] == []
    assert carried["reason_code"] == "FOLD_TERMINAL_FORCE_FLAT"
    # off-schedule instants still refuse fail-closed
    with pytest.raises(ContractViolation):
        plugin.targets_at(
            parse_iso_utc("2026-04-21T12:00:00Z"), universe=universe, stress=stress
        )


def test_folds_accept_dropped_fold_l_v11_1():
    """The family's folds contract ACCEPTS a dropped fold (L-V11-1)."""
    plugin = _world_plugin(ANCHOR_ARM)
    stress = StressSpec(name="drop_one_fold", dropped_fold_index=1)
    folds = plugin.folds(stress=stress, instants=list(stamp_calendar()))
    assert [f.dropped for f in folds] == [False, True, False]
    decision = plugin.decision_instants(stress=stress)
    f1 = [f for f in folds if f.index == 1][0]
    for stamp in f1.instants:
        assert stamp not in decision


# ------------------------------------------------------------------------- #
# Plugin interface + identity + confirmatory carry-through + gate runner
# ------------------------------------------------------------------------- #
def test_frozen_identity_digests_match_and_arms_are_distinct():
    report = frozen_arm_digest_report()
    assert all(entry["match"] for entry in report.values()), report
    digests = {arm: entry["computed_from_identity"] for arm, entry in report.items()}
    assert digests == dict(OICYC_ARM_CONFIG_DIGESTS)
    assert len(set(digests.values())) == 3  # distinct trial keys per arm
    # strategy-level accessor returns the same identity objects
    for arm in (ANCHOR_ARM, NEIGHBOUR_ARM, CONTROL_ARM):
        assert strategy_frozen_identity(arm) == frozen_identity(arm)
    with pytest.raises(ContractViolation):
        frozen_identity("NOT-AN-ARM")


def test_plugin_interface_statement_for_the_driver():
    """The mechanical driver surface: identity, cost model, universe,
    schedule, folds, one book per arm, preflight digests, status."""
    plugin = _world_plugin(ANCHOR_ARM)
    report = plugin.plugin_interface_report()
    assert report["family_id"] == FAMILY_ID == "A14-V14-A8-OICYC"
    assert report["arm_id"] == ANCHOR_ARM == "CYC-28D"
    assert report["arm_role"] == "anchor"
    assert report["tradeable_universe"] == list(WORLD_UNIVERSE)
    assert report["minimum_tradeable_names"] == 12
    assert report["benchmark_context_symbols"] == sorted(set(WORLD_UNIVERSE) | {WORLD_BENCH})
    assert report["schedule_instants"] == 52
    assert report["fold_count"] == 3 and report["purge_days"] == 1
    assert report["weight_cap_abs"] == 0.30 and report["gross_cap"] == 1.0
    assert report["cost_model"]["taker_fee_bps"] == 5.0
    assert report["cost_model"]["adverse_tick_slip_floor"] == 1
    assert report["status_metadata"]["scored_status"] == "CONFIRMATORY"
    assert report["warmup_rows_at_first_stamp"] and set(
        report["warmup_rows_at_first_stamp"].values()
    ) == {56}
    model = plugin.cost_model()
    assert model.taker_fee_bps == 5.0 and model.adverse_tick_slip_floor == 1
    # the control arm carries its own preflight statement
    control = _world_plugin(CONTROL_ARM)
    creport = control.plugin_interface_report()
    assert creport["arm_role"] == "causal_negative_control"
    assert creport["status_metadata"]["scored_status"] == "CONFIRMATORY"
    # unknown arms refuse
    with pytest.raises(ContractViolation):
        _world_plugin("OICYC-404")
    # the benchmark leg can never be a tradeable candidate
    with pytest.raises(ContractViolation):
        OicycPlugin(
            arm_id=ANCHOR_ARM,
            oi_by_symbol={**_world_oi(), WORLD_BENCH: [(0, 1.0)]},
            bars_by_symbol=_world_bars(),
            tick_sizes={},
            assert_warmup=False,
        )


def test_gate_runner_preregistered_rules_and_confirmatory_carry():
    """The Stage-A rule table (no PnL computed here): control firing
    falsifies; the incremental context is decisive; the verdict carries
    the CONFIRMATORY status for the driver's verdict + denominator."""
    good = headline_gate(expectancy=0.01, position_pf=1.2, fold_positive=[True, True, False])
    bad = headline_gate(expectancy=-0.01, position_pf=0.9, fold_positive=[True, False, False])
    inc = incremental_context_gate(
        excess_bh_fold_positive=[True, True, False],
        excess_beta_fold_positive=[True, False, True],
    )
    inc_fail = incremental_context_gate(
        excess_bh_fold_positive=[True, True, False],
        excess_beta_fold_positive=[True, False, False],
    )
    conc = fold_concentration_check(largest_fold_positive_share=0.4)
    conc_bad = fold_concentration_check(largest_fold_positive_share=0.6)

    # 1. anchor fails -> REJECTED_ANCHOR_FAIL
    v1 = evaluate_family_gate(
        anchor_headline=bad, control_headline=good, neighbour_headline=good,
        anchor_incremental=inc, anchor_fold_concentration=conc,
    )
    assert v1["verdict"] == "REJECTED_ANCHOR_FAIL"
    # 2. anchor passes, incremental context fails -> REJECTED (beta
    #    repackaging; raw PnL never overrides a failed context)
    v2 = evaluate_family_gate(
        anchor_headline=good, control_headline=bad, neighbour_headline=good,
        anchor_incremental=inc_fail, anchor_fold_concentration=conc,
    )
    assert v2["verdict"] == "REJECTED_ANCHOR_FAIL"
    # 3. anchor + control both pass -> FALSIFIED (OI-dominance artifact)
    v3 = evaluate_family_gate(
        anchor_headline=good, control_headline=good, neighbour_headline=good,
        anchor_incremental=inc, anchor_fold_concentration=conc,
    )
    assert v3["verdict"] == "FALSIFIED_CONTROL_REPRODUCES_OI_DOMINANCE"
    assert v3["control_never_promotable"] is True
    # 4. neighbour fails -> REJECTED_NEIGHBOUR_SIGN_FLIP
    v4 = evaluate_family_gate(
        anchor_headline=good, control_headline=bad, neighbour_headline=bad,
        anchor_incremental=inc, anchor_fold_concentration=conc,
    )
    assert v4["verdict"] == "REJECTED_NEIGHBOUR_SIGN_FLIP"
    # 5. fold-positive concentration > 50% -> falsified
    v5 = evaluate_family_gate(
        anchor_headline=good, control_headline=bad, neighbour_headline=good,
        anchor_incremental=inc, anchor_fold_concentration=conc_bad,
    )
    assert v5["verdict"] == "FALSIFIED_SINGLE_REGIME_ARTIFACT"
    # 6. everything clean -> FAMILY_ADVANCES_TO_STAGE_A
    v6 = evaluate_family_gate(
        anchor_headline=good, control_headline=bad, neighbour_headline=good,
        anchor_incremental=inc, anchor_fold_concentration=conc,
    )
    assert v6["verdict"] == "FAMILY_ADVANCES_TO_STAGE_A"
    # EVERY verdict carries the confirmatory status + denominator note
    for verdict in (v1, v2, v3, v4, v5, v6):
        assert verdict["confirmatory_status"] == "CONFIRMATORY"
        assert "denominator" in verdict["denominator_note"]
        assert verdict["section_1_1_disclosure"]
    # malformed gate payloads refuse
    with pytest.raises(ContractViolation):
        headline_gate(expectancy=0.1, position_pf=1.2, fold_positive=[True, True])
    with pytest.raises(ContractViolation):
        fold_concentration_check(largest_fold_positive_share=1.5)
