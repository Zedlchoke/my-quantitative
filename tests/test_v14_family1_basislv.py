"""V14 I lane (i-family-1) -- A14-V14-A5-BASISLV-PREMFADE frozen machinery.

Evidence pins for the frozen family (PLAN_crypto_v14.md section 9; proposal
``research/proposals/v14/a5/BASISLV-PREMFADE.md``; selection freeze HEAD
``d16341f``):

* (a) HAND-COMPUTED golden feature tests: the committed fixtures
  (``golden/premfade_golden_fixture.json``,
  ``golden/premfade_targets_golden.json``) encode a tiny 13-symbol
  constant-premium synthetic world whose ranks, books, side geometry, tie
  breaks, refusals and the exact sign-inverted control are all derived BY
  HAND and must be reproduced exactly;
* (b) THE L-V14-0 COST-SCALING REGRESSION on this family's book machinery:
  cost strictly linear in the number of FILLS on the family's books across
  full-window runs through the generic adapter kernel -- a constant book
  held across 51 weeks charges only its 4 fill transitions (entry /
  fold-terminal flat / F1 re-entry / final force-flat), rank-flip worlds
  with 2x / 3x the fill count cost EXACTLY 2x / 3x, and not one unit of
  cost accrues at a held stamp;
* (c) AVAILABILITY-LAG MUTATION TESTS for every adopted conditioning
  field -- basis route (signal), execution bars (fills/marks), funding
  (settlements) and the verification-only premium/mark/index kline routes
  -- mutating availability (a row stamped available after the decision /
  the whole series shifted one bucket later / a missing execution bar) and
  asserting the decision pipeline either refuses or shifts
  deterministically: a decision at T never reads data available after T
  (crypto_compat pin style);
* (d) zero-position refusal passthrough (stamp-level
  ``EligibilityShortfall`` and the publication-path
  ``REFUSED_ZERO_POSITIONS``);
* (e) fold force-flat boundaries respected (the F0 fold-terminal flat
  book, the purge-gap carry, no cross-fold holding in a full-window run).

All data SYNTHETIC except the explicitly-skipped real-snapshot evidence
test; nothing is scored; no ledger outside ``tmp_path`` is touched.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

from research.adapter_v10.protocol import (
    ContractViolation,
    PositionSpan,
    StressSpec,
)
from research.adapter_v10.runner import run_strategy
from research.v12.accounting import (
    REFUSED_ZERO_POSITIONS,
    STAGE_REFUSED,
    publish_v12_cell,
)
from research.v14.families.basislv_premfade.frozen_identity import (
    BASISLV_ARM_CONFIG_DIGESTS,
    frozen_arm_digest_report,
    frozen_identity,
)
from research.v14.families.basislv_premfade.gate_runner import (
    CONTROL_NEVER_PROMOTABLE,
    VERDICT_BLOCKED_CLAUSE_INPUTS,
    VERDICT_FALSIFIED_TILT,
    VERDICT_FAMILY_ADVANCES,
    VERDICT_REJECTED_ANCHOR,
    VERDICT_REJECTED_CARRY_HARVEST,
    VERDICT_REJECTED_NEIGHBOUR,
    evaluate_family_gate,
    incremental_gate,
    price_only_clause,
)
from research.v14.families.basislv_premfade.plugin import (
    REASON_FOLD_TERMINAL_FORCE_FLAT,
    BasislvPremfadePlugin,
    family_stress_cell,
    fold_terminal_force_flat_stamps,
)
from research.v14.families.basislv_premfade.strategy import (
    ANCHOR_ARM,
    ARM_IDS,
    BENCHMARK_SYMBOL,
    BUCKET_NS,
    CAP_MAX,
    CONTROL_ARM,
    DAY_NS,
    F0_FOLD_TERMINAL_STAMP_ISO,
    F1_PURGED_STAMP_ISO,
    FAMILY_ID,
    FIRST_STAMP_ISO,
    FORMATION_BUCKETS_ANCHOR,
    FORMATION_BUCKETS_NEIGHBOUR,
    GROSS_TARGET,
    MIN_ELIGIBLE,
    NEIGHBOUR_ARM,
    REASON_MISSING_OR_NON_FINITE_SLOT,
    REASON_UNAVAILABLE_ROW,
    BarSeries,
    BasisRouteSeries,
    build_drop_one_book,
    build_premfade_book,
    compute_targets_at,
    effective_schedule,
    EligibilityShortfall,
    fold_assignments,
    fold_end_ns,
    force_flat_span_end,
    next_allowed_close_fill,
    parse_iso_utc,
    premium_level_at,
    schedule_drop_one,
    select_drop_one_symbol_at,
    side_geometry,
    stamp_calendar,
)

GOLDEN_DIR = Path("research/v14/families/basislv_premfade/golden")


def load_fixture() -> dict:
    with open(GOLDEN_DIR / "premfade_golden_fixture.json", "r", encoding="utf-8") as fh:
        return json.load(fh)


def load_targets_golden() -> dict:
    with open(GOLDEN_DIR / "premfade_targets_golden.json", "r", encoding="utf-8") as fh:
        return json.load(fh)


# ------------------------------------------------------------------------- #
# Synthetic world builders (vectorized; dense 15m grids)
# ------------------------------------------------------------------------- #
def build_premium_world(
    fixture: dict,
    *,
    formation_buckets: int = FORMATION_BUCKETS_NEIGHBOUR,
    drop_buckets: dict[str, set[int]] | None = None,
    late_buckets: dict[str, set[int]] | None = None,
    shift_all_availability: bool = False,
    premium_override: dict[str, dict[int, float]] | None = None,
) -> dict[str, BasisRouteSeries]:
    """Dense constant-premium basis-route world from the fixture constants.

    Slots are indexed by close boundary from ``series_origin_ns`` (slot
    ``formation_buckets`` closes exactly at the decision stamp).  Mutations:
    ``drop_buckets`` marks slots NaN (missing), ``late_buckets`` stamps a
    slot available after the stamp, ``shift_all_availability`` moves every
    slot's availability one bucket past its close.
    """
    stamp = int(fixture["stamp_ns"])
    origin = stamp - formation_buckets * BUCKET_NS
    n = formation_buckets + 1  # closes origin..stamp inclusive
    closes = origin + np.arange(n, dtype=np.int64) * BUCKET_NS
    drops = drop_buckets or {}
    lates = late_buckets or {}
    overrides = premium_override or {}
    world: dict[str, BasisRouteSeries] = {}
    for sym in fixture["symbols"]:
        value = float(fixture["constant_premium_by_symbol"][sym])
        premium = np.full(n, value, dtype=np.float64)
        available = closes.copy()
        for slot in drops.get(sym, set()):
            premium[slot] = np.nan
        for slot in lates.get(sym, set()):
            available[slot] = stamp + BUCKET_NS  # available AFTER the decision
        if shift_all_availability:
            available = available + BUCKET_NS
        for slot, value_override in overrides.get(sym, {}).items():
            premium[slot] = float(value_override)
        world[sym] = BasisRouteSeries(
            origin_ns=int(origin), premium=premium, available_ns=available
        )
    return world


def build_bar_world(
    symbols: Sequence[str],
    *,
    origin_ns: int,
    n_slots: int,
    price: float = 100.0,
    missing_closes: dict[str, set[int]] | None = None,
    late_closes: dict[str, set[int]] | None = None,
) -> dict[str, BarSeries]:
    """Dense constant-price execution bar world (availability = close)."""
    missing = missing_closes or {}
    late = late_closes or {}
    closes = origin_ns + np.arange(n_slots, dtype=np.int64) * BUCKET_NS
    out: dict[str, BarSeries] = {}
    for sym in symbols:
        close = np.full(n_slots, float(price), dtype=np.float64)
        available = closes.copy()
        for slot in missing.get(sym, set()):
            close[slot] = np.nan
        for slot in late.get(sym, set()):
            available[slot] = int(closes[slot]) + BUCKET_NS
        out[sym] = BarSeries(
            origin_ns=int(origin_ns), close=close, available_ns=available
        )
    return out


def build_plugin(
    arm_id: str,
    *,
    world: dict[str, BasisRouteSeries] | None = None,
    symbols: Sequence[str] | None = None,
    fixture: dict | None = None,
    with_benchmark: bool = True,
    tick_size: float = 0.01,
    bars: dict[str, BarSeries] | None = None,
) -> BasislvPremfadePlugin:
    fixture = fixture or load_fixture()
    symbols = list(symbols) if symbols else list(fixture["symbols"])
    if world is None:
        world = build_premium_world(
            fixture, formation_buckets=FORMATION_BUCKETS_ANCHOR
        )
    needed = list(symbols) + ([BENCHMARK_SYMBOL] if with_benchmark else [])
    if bars is None:
        stamp = int(fixture["stamp_ns"])
        bars = build_bar_world(needed, origin_ns=stamp, n_slots=8)
    return BasislvPremfadePlugin(
        arm_id=arm_id,
        basis_by_symbol=world,
        bars_by_symbol=bars,
        tick_sizes={sym: tick_size for sym in needed},
    )


def flip_masks(
    *, origin_ns: int, n_slots: int, segments: list[tuple[int, int]]
) -> np.ndarray:
    """Boolean mask of slots whose close lies inside any ``[a, b)`` segment."""
    closes = origin_ns + np.arange(n_slots, dtype=np.int64) * BUCKET_NS
    mask = np.zeros(n_slots, dtype=bool)
    for a, b in segments:
        mask |= (closes >= a) & (closes < b)
    return mask


# ------------------------------------------------------------------------- #
# (a) Golden feature tests (hand-computed)
# ------------------------------------------------------------------------- #
def test_v14f1_golden_anchor_book_matches_targets_golden():
    fixture = load_fixture()
    golden = load_targets_golden()
    world = build_premium_world(fixture, formation_buckets=FORMATION_BUCKETS_ANCHOR)
    payload = compute_targets_at(
        ANCHOR_ARM,
        basis_by_symbol=world,
        stamp_ns=int(fixture["stamp_ns"]),
        universe=list(fixture["symbols"]),
    )
    for key in (
        "schema",
        "family_id",
        "arm_id",
        "status",
        "carried_forward",
        "decision_ns",
        "weights",
        "longs",
        "shorts",
        "middle",
    ):
        assert payload[key] == golden[key], key
    for key, value in golden["diagnostics"].items():
        assert payload["diagnostics"][key] == value, f"diagnostics.{key}"


def test_v14f1_golden_b_i_equals_constant_premium_hand_exact():
    fixture = load_fixture()
    for formation in (FORMATION_BUCKETS_ANCHOR, FORMATION_BUCKETS_NEIGHBOUR):
        world = build_premium_world(fixture, formation_buckets=formation)
        for sym, c in fixture["constant_premium_by_symbol"].items():
            value, reason = premium_level_at(
                world[sym], int(fixture["stamp_ns"]), formation_buckets=formation
            )
            assert reason is None
            assert value == pytest.approx(float(c), abs=1e-18)


def test_v14f1_golden_neighbour_book_identical_and_control_exact_negation():
    fixture = load_fixture()
    hand = fixture["hand_computed"]
    stamp = int(fixture["stamp_ns"])
    universe = list(fixture["symbols"])
    anchor = compute_targets_at(
        ANCHOR_ARM,
        basis_by_symbol=build_premium_world(
            fixture, formation_buckets=FORMATION_BUCKETS_ANCHOR
        ),
        stamp_ns=stamp,
        universe=universe,
    )
    neighbour = compute_targets_at(
        NEIGHBOUR_ARM,
        basis_by_symbol=build_premium_world(
            fixture, formation_buckets=FORMATION_BUCKETS_NEIGHBOUR
        ),
        stamp_ns=stamp,
        universe=universe,
    )
    control = compute_targets_at(
        CONTROL_ARM,
        basis_by_symbol=build_premium_world(
            fixture, formation_buckets=FORMATION_BUCKETS_ANCHOR
        ),
        stamp_ns=stamp,
        universe=universe,
    )
    # Neighbour: same mechanism/book -- identical weights on this world.
    assert neighbour["weights"] == anchor["weights"]
    assert [s for s, _w in neighbour["longs"]] == hand["neighbour"]["longs"]
    assert [s for s, _w in neighbour["shorts"]] == hand["neighbour"]["shorts"]
    assert neighbour["middle"] == hand["neighbour"]["middle"]
    assert neighbour["diagnostics"]["formation_buckets"] == 5376
    # Control: EXACT sign-inverted anchor book (element-wise negation).
    anchor_w = {sym: w for sym, w in anchor["weights"]}
    control_w = {sym: w for sym, w in control["weights"]}
    assert set(anchor_w) == set(control_w)
    for sym, w in anchor_w.items():
        assert control_w[sym] == pytest.approx(-w, abs=1e-15)
    assert [s for s, _w in control["longs"]] == hand["control_inv"]["longs"]
    assert [s for s, _w in control["shorts"]] == hand["control_inv"]["shorts"]
    assert control["middle"] == hand["control_inv"]["middle"]


def test_v14f1_golden_tie_break_symbol_id_ascending_at_short_boundary():
    fixture = load_fixture()
    tie = fixture["hand_computed"]["tie_scenario"]
    # Hand scores: SYM08 = SYM09 = +2e-4 (an EXACT tie straddling the short
    # boundary); every other symbol at its fixture constant.
    scores = {
        sym: float(fixture["constant_premium_by_symbol"][sym])
        for sym in fixture["symbols"]
    }
    for sym in tie["tie_symbols"]:
        scores[sym] = float(tie["tie_value"])
    book = build_premfade_book(scores)
    assert book["n_eligible"] == tie["n_eligible"]
    assert book["side_size"] == tie["side_size"]
    assert book["longs"] == tie["longs"]
    assert book["shorts"] == tie["shorts"]
    assert book["middle"] == tie["middle"]
    # The tie straddles the short boundary: SYM09 (lexicographically larger)
    # goes short, SYM08 stays middle -- the declared a priori ordering.
    assert tie["tie_symbols"][1] in book["shorts"]
    assert tie["tie_symbols"][0] in book["middle"]


def test_v14f1_golden_missing_slot_refuses_symbol_and_shifts_book_deterministically():
    fixture = load_fixture()
    hand = fixture["hand_computed"]
    refusal = hand["refusal_scenario"]
    formation = FORMATION_BUCKETS_ANCHOR
    # Drop a slot inside the anchor window of the refused symbol.
    drop_slots = {formation - 10}
    world = build_premium_world(
        fixture,
        formation_buckets=formation,
        drop_buckets={refusal["refused_symbol"]: set(drop_slots)},
    )
    value, reason = premium_level_at(
        world[refusal["refused_symbol"]],
        int(fixture["stamp_ns"]),
        formation_buckets=formation,
    )
    assert value is None and reason == refusal["reason_code"]
    payload = compute_targets_at(
        ANCHOR_ARM,
        basis_by_symbol=world,
        stamp_ns=int(fixture["stamp_ns"]),
        universe=list(fixture["symbols"]),
    )
    assert payload["diagnostics"]["n_eligible"] == refusal["n_eligible"]
    assert payload["diagnostics"]["refused"] == {
        refusal["refused_symbol"]: refusal["reason_code"]
    }
    assert payload["longs"] == [[sym, 0.125] for sym in refusal["longs"]]
    assert payload["shorts"] == [[sym, -0.125] for sym in refusal["shorts"]]
    assert payload["middle"] == refusal["middle"]


def test_v14f1_golden_below_floor_stamp_refuses_fail_closed():
    fixture = load_fixture()
    below = fixture["hand_computed"]["below_floor_scenario"]
    formation = FORMATION_BUCKETS_ANCHOR
    drops = {sym: {formation - 10} for sym in below["refused_symbols"]}
    world = build_premium_world(
        fixture, formation_buckets=formation, drop_buckets=drops
    )
    with pytest.raises(EligibilityShortfall):
        compute_targets_at(
            ANCHOR_ARM,
            basis_by_symbol=world,
            stamp_ns=int(fixture["stamp_ns"]),
            universe=list(fixture["symbols"]),
        )


def test_v14f1_golden_side_geometry_hand_table():
    fixture = load_fixture()
    table = fixture["side_geometry_hand_table"]
    assert len(table) == 6
    for n_text, expected in table.items():
        k, per_leg = side_geometry(int(n_text))
        assert k == expected["side_size"], n_text
        assert per_leg == pytest.approx(expected["per_leg_weight"], abs=1e-11)
        assert k * 2 * per_leg == pytest.approx(GROSS_TARGET, abs=1e-12)
        assert per_leg <= CAP_MAX
    with pytest.raises(EligibilityShortfall):
        side_geometry(MIN_ELIGIBLE - 1)


def test_v14f1_golden_world_has_no_scored_metric_available():
    # The golden fixture carries hand-computed BOOK facts only -- no PnL,
    # no return, no expectancy anywhere in the committed fixtures.
    for name in ("premfade_golden_fixture.json", "premfade_targets_golden.json"):
        body = (GOLDEN_DIR / name).read_text(encoding="utf-8").lower()
        for token in ("expectancy", "pnl", "sharpe", "drawdown"):
            assert token not in body, (name, token)


# ------------------------------------------------------------------------- #
# (b) THE L-V14-0 COST-SCALING REGRESSION (family book machinery)
# ------------------------------------------------------------------------- #
FEE_BPS = 5.0
TICK = 0.01
FILL_PRICE = 100.0
BASE_RATE = FEE_BPS * 1e-4 + TICK / FILL_PRICE  # 6e-4 per unit notional
N_SYMBOLS = 13
LEGS = 8  # 13 eligible -> k=4 -> 8 held legs at 0.125
PER_LEG = 0.125
COST_UNITS_PER_TRANSITION = LEGS * PER_LEG  # 1.0 of traded notional


def _cost_world_premiums(
    fixture: dict,
    *,
    flip_segments: list[tuple[int, int]],
) -> dict[str, BasisRouteSeries]:
    """Full-window anchor world: c_i with piecewise -5c_i flip segments.

    A segment of -5c_i flips the cross-sectional ordering for every stamp
    whose 2688-slot anchor window contains more than 2688/6 = 448 segment
    slots (hand: the window mean is coef*c_i with coef = 1 - 6F/2688 < 0);
    every negative coefficient yields the IDENTICAL (reversed) rank order,
    so a 56-day segment produces EXACTLY one entry and one exit churn.
    """
    stamp0 = int(fixture["stamp_ns"])
    formation = FORMATION_BUCKETS_ANCHOR
    origin = stamp0 - formation * BUCKET_NS
    # Cover from origin through the last stamp + 1 day of closes.
    n = formation + (int(stamp_calendar()[-1]) - stamp0) // BUCKET_NS + 96 * 2
    closes = origin + np.arange(n, dtype=np.int64) * BUCKET_NS
    flip = flip_masks(origin_ns=origin, n_slots=n, segments=flip_segments)
    world: dict[str, BasisRouteSeries] = {}
    for sym in fixture["symbols"]:
        c = float(fixture["constant_premium_by_symbol"][sym])
        premium = np.where(flip, -5.0 * c, c)
        world[sym] = BasisRouteSeries(
            origin_ns=int(origin), premium=premium, available_ns=closes
        )
    return world


def _run_full_window(
    fixture: dict,
    *,
    flip_segments: list[tuple[int, int]],
    stress: StressSpec | None = None,
):
    """Full frozen-schedule adapter run of the anchor arm on a cost world."""
    world = _cost_world_premiums(fixture, flip_segments=flip_segments)
    symbols = list(fixture["symbols"])
    needed = symbols + [BENCHMARK_SYMBOL]
    first = int(fixture["stamp_ns"])
    n_slots = (int(stamp_calendar()[-1]) - first) // BUCKET_NS + 96 * 2
    bars = build_bar_world(needed, origin_ns=first, n_slots=n_slots)
    plugin = BasislvPremfadePlugin(
        arm_id=ANCHOR_ARM,
        basis_by_symbol=world,
        bars_by_symbol=bars,
        tick_sizes={sym: TICK for sym in needed},
    )
    return run_strategy(plugin, stress=stress, write_artifact_file=False)


def _segment(stamp0: int, start_days: int, length_days: int) -> tuple[int, int]:
    return (
        stamp0 + start_days * DAY_NS,
        stamp0 + (start_days + length_days) * DAY_NS,
    )


def test_v14f1_l_v14_0_constant_book_costs_fills_not_holding_days():
    """The constant book charges ONLY its 4 fill transitions over 51 weeks.

    Hand: entry at the first stamp + fold-terminal flat at 2025-12-15 + F1
    re-entry at 2025-12-22 + final force-flat = 4 transitions of traded
    notional 8 x 0.125 = 1.0 each at rate 6e-4 => total 4 x 6e-4 = 0.0024,
    INDEPENDENT of the 351 holding days; every one of the 47 held weekly
    boundaries charges EXACTLY zero.
    """
    fixture = load_fixture()
    result = _run_full_window(fixture, flip_segments=[])
    cost = result["portfolio_metrics"]["cost_charged_sum"]
    assert cost == pytest.approx(4 * COST_UNITS_PER_TRANSITION * BASE_RATE, abs=1e-12)
    assert cost == pytest.approx(0.0024, abs=1e-12)
    rows = sorted(result["daily_returns"], key=lambda r: r["decision_ns"])
    charged = [r for r in rows if r["cost_charged_per_unit"] != 0.0]
    assert len(charged) == 4
    fold_terminal = parse_iso_utc(F0_FOLD_TERMINAL_STAMP_ISO)
    first_stamp = parse_iso_utc(FIRST_STAMP_ISO)
    expected_stamps = {
        first_stamp,
        fold_terminal,
        fold_terminal + 7 * DAY_NS,  # F1 re-entry
        int(stamp_calendar()[-1]),  # final force-flat
    }
    assert {int(r["decision_ns"]) for r in charged} == expected_stamps
    for row in charged:
        assert row["cost_charged_per_unit"] == pytest.approx(
            COST_UNITS_PER_TRANSITION * BASE_RATE, abs=1e-12
        )
    # The kernel's price/funding surface is untouched by the cost regime:
    # constant bars and empty settlements => zero price and funding PnL.
    assert result["portfolio_metrics"]["price_pnl_sum"] == pytest.approx(0.0, abs=1e-12)
    assert result["portfolio_metrics"]["funding_sum"] == pytest.approx(0.0, abs=1e-12)
    # net = price + funding - cost exactly (cost charged once per fill).
    assert result["portfolio_metrics"]["net_return_sum"] == pytest.approx(
        -cost, abs=1e-12
    )


def test_v14f1_l_v14_0_double_and_triple_fills_cost_exactly_double_and_triple():
    """Cost is strictly linear in the number of fills on the family's books.

    One 56-day -5c_i flip segment adds EXACTLY two book-wide churn
    transitions (16 fill-units each: 8 legs x |dw| = 0.25); two disjoint
    segments add four.  Hand: W0 = 32 fill-units -> 0.0024; W1 = 64 -> 0.0048
    (= 2x W0); W2 = 96 -> 0.0072 (= 3x W0).  A 2N-fill book costs exactly
    2x the N-fill book, and the extra fills -- not the extra holding days --
    carry every unit of the difference.
    """
    fixture = load_fixture()
    stamp0 = int(fixture["stamp_ns"])
    w0 = _run_full_window(fixture, flip_segments=[])
    w1 = _run_full_window(fixture, flip_segments=[_segment(stamp0, 56, 56)])
    w2 = _run_full_window(
        fixture,
        flip_segments=[_segment(stamp0, 56, 56), _segment(stamp0, 196, 56)],
    )
    cost0 = w0["portfolio_metrics"]["cost_charged_sum"]
    cost1 = w1["portfolio_metrics"]["cost_charged_sum"]
    cost2 = w2["portfolio_metrics"]["cost_charged_sum"]
    assert cost0 == pytest.approx(32 * PER_LEG * BASE_RATE, abs=1e-12)
    assert cost1 == pytest.approx(64 * PER_LEG * BASE_RATE, abs=1e-12)
    assert cost2 == pytest.approx(96 * PER_LEG * BASE_RATE, abs=1e-12)
    assert cost1 == pytest.approx(2 * cost0, rel=1e-12)
    assert cost2 == pytest.approx(3 * cost0, rel=1e-12)
    # Exactly the predicted number of charging boundaries per world.
    for result, n_charged in ((w1, 6), (w2, 8)):
        rows = sorted(result["daily_returns"], key=lambda r: r["decision_ns"])
        assert sum(1 for r in rows if r["cost_charged_per_unit"] != 0.0) == n_charged
    # Linear in fills across the three points (exact hand slope).
    slope1 = (cost1 - cost0) / (32 * PER_LEG)
    slope2 = (cost2 - cost1) / (32 * PER_LEG)
    assert slope1 == pytest.approx(BASE_RATE, rel=1e-12)
    assert slope2 == pytest.approx(BASE_RATE, rel=1e-12)


def test_v14f1_l_v14_0_cost_once_across_replay_and_stress_tiers_on_family_books():
    """Replay charges cost once; the family stress cell moves ONLY cost.

    Hand stress tiers on one entry transition (8 legs x 0.125 notional at
    100.0): baseline (fee x1.0, +1 tick) = 0.0006; fee x1.5 (+1 tick) =
    0.00085; +2 ticks (3 total) = 0.0008 -- the exact 12:17:16 ratio.
    """
    fixture = load_fixture()
    first = _run_full_window(fixture, flip_segments=[])
    replay = _run_full_window(fixture, flip_segments=[])
    assert (
        first["portfolio_metrics"]["cost_charged_sum"]
        == replay["portfolio_metrics"]["cost_charged_sum"]
    )
    assert first["hashes"] == replay["hashes"]

    plugin = build_plugin(ANCHOR_ARM, fixture=fixture)
    baseline = plugin.baseline_stress()
    # The frozen anchor book on the golden world: 4 longs + 4 shorts at 0.125.
    book = {
        "SYM00": PER_LEG,
        "SYM01": PER_LEG,
        "SYM02": PER_LEG,
        "SYM03": PER_LEG,
        "SYM09": -PER_LEG,
        "SYM10": -PER_LEG,
        "SYM11": -PER_LEG,
        "SYM12": -PER_LEG,
    }
    prices = {sym: FILL_PRICE for sym in book}
    entry = ({}, dict(sorted(book.items())))
    base = plugin.rebalance_cost_between(
        *entry, prices=prices, stress=baseline
    )
    fee_up = plugin.rebalance_cost_between(
        *entry,
        prices=prices,
        stress=StressSpec(name="fee_x1_5", fee_multiplier=1.5, tick_slip_ticks=1),
    )
    ticks_up = plugin.rebalance_cost_between(
        *entry,
        prices=prices,
        stress=StressSpec(name="plus2ticks", fee_multiplier=1.0, tick_slip_ticks=3),
    )
    assert base == pytest.approx(0.0006, abs=1e-15)
    assert fee_up == pytest.approx(0.00085, abs=1e-15)
    assert ticks_up == pytest.approx(0.0008, abs=1e-15)
    assert len({base, fee_up, ticks_up}) == 3
    assert fee_up == pytest.approx(base * 17.0 / 12.0, rel=1e-12)
    assert ticks_up == pytest.approx(base * 16.0 / 12.0, rel=1e-12)
    # Purity: pricing the same transition twice returns the same number.
    again = plugin.rebalance_cost_between(*entry, prices=prices, stress=baseline)
    assert again == base
    # The frozen family stress cell is exactly fee x1.5 / +2 ticks / +1 delay.
    cell = family_stress_cell(baseline)
    assert cell.fee_multiplier == 1.5
    assert cell.tick_slip_ticks == baseline.tick_slip_ticks + 2
    assert cell.event_delay_events == baseline.event_delay_events + 1


# ------------------------------------------------------------------------- #
# (c) AVAILABILITY-LAG MUTATION TESTS (every adopted conditioning field)
# ------------------------------------------------------------------------- #
def test_v14f1_mutation_basis_route_row_available_after_decision_refuses():
    """Basis route (the signal): a row available after T is unreadable at T."""
    fixture = load_fixture()
    formation = FORMATION_BUCKETS_ANCHOR
    victim = "SYM02"
    world = build_premium_world(
        fixture,
        formation_buckets=formation,
        late_buckets={victim: {formation - 10}},
    )
    value, reason = premium_level_at(
        world[victim], int(fixture["stamp_ns"]), formation_buckets=formation
    )
    assert value is None and reason == REASON_UNAVAILABLE_ROW
    payload = compute_targets_at(
        ANCHOR_ARM,
        basis_by_symbol=world,
        stamp_ns=int(fixture["stamp_ns"]),
        universe=list(fixture["symbols"]),
    )
    # The stamp shifts DETERMINISTICALLY: the unreadable symbol is excluded,
    # the next-lowest premium name is promoted, everything else unchanged.
    assert payload["diagnostics"]["refused"] == {victim: REASON_UNAVAILABLE_ROW}
    assert payload["longs"] == [[sym, 0.125] for sym in ("SYM00", "SYM01", "SYM03", "SYM04")]


def test_v14f1_mutation_basis_route_series_shifted_one_bucket_refuses_every_symbol():
    """Basis route: shifting ALL availability one bucket later fails closed.

    The last admissible bucket for a Monday 00:00Z stamp is [Sun 23:45,
    Mon 00:00); shifted one bucket its availability becomes T + 15m > T, so
    every symbol refuses and the stamp refuses (no book, no back-fill).
    """
    fixture = load_fixture()
    formation = FORMATION_BUCKETS_ANCHOR
    world = build_premium_world(
        fixture, formation_buckets=formation, shift_all_availability=True
    )
    value, reason = premium_level_at(
        world["SYM00"], int(fixture["stamp_ns"]), formation_buckets=formation
    )
    assert value is None and reason == REASON_UNAVAILABLE_ROW
    with pytest.raises(EligibilityShortfall):
        compute_targets_at(
            ANCHOR_ARM,
            basis_by_symbol=world,
            stamp_ns=int(fixture["stamp_ns"]),
            universe=list(fixture["symbols"]),
        )


def test_v14f1_mutation_execution_bar_available_after_close_refuses_fill():
    """Bars: a fill bar available after its own close can never be transacted.

    The baseline fill REFUSES (a decision cannot transact a row it cannot
    read); under the frozen +1 event-delay stress the fill shifts
    DETERMINISTICALLY to the next completed bar (the 00:30Z close).
    """
    fixture = load_fixture()
    stamp = int(fixture["stamp_ns"])
    bars = build_bar_world(
        ["SYM00"],
        origin_ns=stamp,
        n_slots=8,
        late_closes={"SYM00": {1}},  # the 00:15Z bar, available only at 00:30Z
    )
    event = next_allowed_close_fill(bars["SYM00"], "SYM00", decision_ns=stamp)
    assert event is None  # refused at the baseline lag
    delayed = next_allowed_close_fill(
        bars["SYM00"], "SYM00", decision_ns=stamp, event_delay_events=1
    )
    assert delayed is not None
    assert delayed.fill_ns == stamp + 2 * BUCKET_NS  # the 00:30Z close
    assert delayed.event_offset == 1


def test_v14f1_mutation_execution_missing_bar_shifts_fill_deterministically():
    """Bars: a genuinely missing 00:15Z bar walks the fill to the 00:30Z close."""
    fixture = load_fixture()
    stamp = int(fixture["stamp_ns"])
    bars = build_bar_world(
        ["SYM00"], origin_ns=stamp, n_slots=8, missing_closes={"SYM00": {1}}
    )
    event = next_allowed_close_fill(bars["SYM00"], "SYM00", decision_ns=stamp)
    assert event is not None
    assert event.fill_ns == stamp + 2 * BUCKET_NS  # the 00:30Z close
    assert event.event_offset == 0
    # The frozen +1 event delay walks strictly later completed bars.
    bars_full = build_bar_world(["SYM00"], origin_ns=stamp, n_slots=8)
    delayed = next_allowed_close_fill(
        bars_full["SYM00"], "SYM00", decision_ns=stamp, event_delay_events=1
    )
    assert delayed is not None
    assert delayed.fill_ns == stamp + 2 * BUCKET_NS
    assert delayed.event_offset == 1


def test_v14f1_mutation_marks_never_read_a_bar_available_after_the_instant():
    """Marks: a bar stamped available after the instant is invisible to it."""
    fixture = load_fixture()
    stamp = int(fixture["stamp_ns"])
    bars = build_bar_world(
        ["SYM00", BENCHMARK_SYMBOL],
        origin_ns=stamp,
        n_slots=8,
        late_closes={"SYM00": {0}},
    )
    plugin = BasislvPremfadePlugin(
        arm_id=ANCHOR_ARM,
        basis_by_symbol=build_premium_world(
            fixture, formation_buckets=FORMATION_BUCKETS_ANCHOR
        ),
        bars_by_symbol=bars,
        tick_sizes={"SYM00": TICK, BENCHMARK_SYMBOL: TICK},
    )
    mark = plugin.marks_at(["SYM00"], stamp)
    assert mark["SYM00"] is None  # the only bar is unavailable at the instant
    bars_ok = build_bar_world(["SYM00", BENCHMARK_SYMBOL], origin_ns=stamp, n_slots=8)
    plugin_ok = BasislvPremfadePlugin(
        arm_id=ANCHOR_ARM,
        basis_by_symbol=build_premium_world(
            fixture, formation_buckets=FORMATION_BUCKETS_ANCHOR
        ),
        bars_by_symbol=bars_ok,
        tick_sizes={"SYM00": TICK, BENCHMARK_SYMBOL: TICK},
    )
    assert plugin_ok.marks_at(["SYM00"], stamp)["SYM00"] == pytest.approx(100.0)


def test_v14f1_mutation_funding_settlement_after_span_end_never_accrues():
    """Funding: a settlement accrues on a span iff start < ts <= end (frozen).

    Mutating the settlement stamp one bucket past the span end removes its
    accrual deterministically; a settlement EXACTLY at the span end accrues.
    """
    fixture = load_fixture()
    stamp = int(fixture["stamp_ns"])
    span_end = force_flat_span_end(stamp)  # T + 7d (no fold boundary here)
    plugin = build_plugin(ANCHOR_ARM, fixture=fixture)
    inside = {"publish_ts_ns": stamp + 8 * 3_600_000_000_000, "value": 0.0001}
    at_end = {"publish_ts_ns": span_end, "value": 0.0002}
    after = {"publish_ts_ns": span_end + BUCKET_NS, "value": 0.0004}
    plugin._settlements_raw = {"SYM00": (inside, at_end, after)}
    flows = plugin.funding_cashflows_for_spans(
        [PositionSpan("SYM00", 0.125, stamp, span_end)]
    )
    stamps = sorted(int(f["publish_ts_ns"]) for f in flows)
    assert stamps == [stamp + 8 * 3_600_000_000_000, span_end]
    # LONG_PAYS_POSITIVE_RATE: a long leg PAYS +rate (negative cashflow).
    for flow in flows:
        assert flow["cashflow_per_unit_capital"] == pytest.approx(
            -0.125 * flow["rate"], abs=1e-15
        )


def _write_staged_kline_parquet(
    root: Path, symbol: str, route: str, *, sentinel_rows: int, nonpositive_rows: int
) -> Path:
    """Fabricate a staged-schema kline parquet for the verification loaders."""
    import pandas as pd

    value_col = {
        "premium_klines": "premium_close",
        "mark_klines": "mark_close",
        "index_klines": "index_close",
    }[route]
    n = 16
    opens = 1_724_112_000_000 + np.arange(n, dtype=np.int64) * 900_000
    values = np.full(n, 0.0005 if route == "premium_klines" else 100.0)
    for i in range(sentinel_rows):
        values[i] = 0.0  # the A9-F premium-close sentinel
    for i in range(nonpositive_rows):
        values[n - 1 - i] = -1.0  # a nonpositive price level
    target = root / f"{symbol}_{route}_15m.parquet"
    pd.DataFrame({"open_time_ms": opens, value_col: values}).to_parquet(
        target, index=False
    )
    return target


def test_v14f1_mutation_verification_routes_sentinel_and_sha_fail_closed(tmp_path):
    """Premium/mark/index klines (verification-only): sentinels and SHA drift
    fail closed; the loaders never treat a staged file as readable without
    its manifest SHA (crypto_compat pin style, fail-closed)."""
    from research.v14.families.basislv_premfade import audits as audits_mod

    fixture = load_fixture()
    symbol = fixture["symbols"][0]
    manifest_path = tmp_path / "staged_basis_manifest.json"
    entries: dict[str, dict] = {}
    paths: dict[str, Path] = {}
    for route, sentinels, nonpos in (
        ("premium_klines", 2, 0),
        ("mark_klines", 0, 1),
        ("index_klines", 0, 0),
    ):
        path = _write_staged_kline_parquet(
            tmp_path, symbol, route, sentinel_rows=sentinels, nonpositive_rows=nonpos
        )
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries[f"{route}|{symbol}"] = {
            "file": str(path),
            "sha256": digest,
            "bytes": path.stat().st_size,
            "rows": 16,
            "expected_buckets": 16,
            "missing_buckets": 0,
        }
        paths[route] = path
    manifest_path.write_text(json.dumps({"entries": entries}), encoding="utf-8")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    health = audits_mod.load_verification_route(
        symbol, "premium_klines", manifest=manifest, staged_root=tmp_path,
        verify_sha=False,
    )
    assert health["malformed_or_nonfinite"] == 2  # the 0.0 sentinels
    assert health["zero_grid_gap"] is True
    assert health["signal_use"].startswith("NONE")
    mark_health = audits_mod.load_verification_route(
        symbol, "mark_klines", manifest=manifest, staged_root=tmp_path,
        verify_sha=False,
    )
    assert mark_health["malformed_or_nonfinite"] == 1
    index_health = audits_mod.load_verification_route(
        symbol, "index_klines", manifest=manifest, staged_root=tmp_path,
        verify_sha=False,
    )
    assert index_health["malformed_or_nonfinite"] == 0

    # SHA drift fails closed: flip one byte's digest in the manifest.
    tampered = json.loads(manifest_path.read_text(encoding="utf-8"))
    tampered["entries"][f"premium_klines|{symbol}"]["sha256"] = "0" * 64
    with pytest.raises(ContractViolation):
        audits_mod.verify_staged_file(
            tampered, f"premium_klines|{symbol}", staged_root=tmp_path
        )
    # An honest manifest verifies.
    verified = audits_mod.verify_staged_file(
        manifest, f"premium_klines|{symbol}", staged_root=tmp_path
    )
    assert verified["sha256"] == entries[f"premium_klines|{symbol}"]["sha256"]


# ------------------------------------------------------------------------- #
# (d) Zero-position refusal passthrough
# ------------------------------------------------------------------------- #
def test_v14f1_zero_position_stamp_refusal_propagates_through_plugin():
    """An empty eligible set refuses the stamp; no flat-book passthrough."""
    fixture = load_fixture()
    plugin = build_plugin(ANCHOR_ARM, fixture=fixture, world={})
    with pytest.raises(EligibilityShortfall):
        plugin.targets_at(
            int(fixture["stamp_ns"]),
            universe=list(fixture["symbols"]),
            stress=plugin.baseline_stress(),
        )
    with pytest.raises(EligibilityShortfall):
        compute_targets_at(
            ANCHOR_ARM,
            basis_by_symbol={},
            stamp_ns=int(fixture["stamp_ns"]),
            universe=list(fixture["symbols"]),
        )


def test_v14f1_zero_position_publication_refused(tmp_path):
    """A zero-position scored payload is refused at publication (L-V11-4)."""
    refused = publish_v12_cell(
        strategy_id="hyp_a14_v14_basislv_premfade",
        family=FAMILY_ID,
        arm_id=ANCHOR_ARM,
        arm_config_digest=BASISLV_ARM_CONFIG_DIGESTS[ANCHOR_ARM],
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
        ledger_path=tmp_path / "zero.jsonl",
        producer_head_sha="0" * 40,
    )
    assert refused["published"] is False
    assert refused["stage"] == STAGE_REFUSED
    assert refused["reasons"][0] == REFUSED_ZERO_POSITIONS


# ------------------------------------------------------------------------- #
# (e) Fold force-flat boundaries
# ------------------------------------------------------------------------- #
def test_v14f1_fold_terminal_stamp_is_pinned_and_answered_flat():
    assert fold_terminal_force_flat_stamps() == (
        parse_iso_utc(F0_FOLD_TERMINAL_STAMP_ISO),
    )
    fixture = load_fixture()
    # Bars must cover the fold-terminal stamp's 00:15Z close-fill.
    first = int(fixture["stamp_ns"])
    terminal = parse_iso_utc(F0_FOLD_TERMINAL_STAMP_ISO)
    n_slots = (terminal - first) // BUCKET_NS + 8
    bars = build_bar_world(
        list(fixture["symbols"]) + [BENCHMARK_SYMBOL], origin_ns=first, n_slots=n_slots
    )
    plugin = build_plugin(ANCHOR_ARM, fixture=fixture, bars=bars)
    book = plugin.targets_at(
        terminal,
        universe=list(fixture["symbols"]),
        stress=plugin.baseline_stress(),
    )
    assert book["weights"] == []
    assert book["status"] == "OK"  # a FORCE_FLAT status at an OPEN instant is refused
    assert book["reason_code"] == REASON_FOLD_TERMINAL_FORCE_FLAT
    assert book["diagnostics"]["fold_terminal_force_flat"] is True
    # The flat close-fills execute strictly inside F0 (before 2025-12-21).
    assert (
        book["diagnostics"]["fold_end_ns"] == parse_iso_utc("2025-12-21T00:00:00Z")
    )


def test_v14f1_full_window_run_respects_every_fold_boundary():
    """Full-window run: no cross-fold holding; the purge gap never trades."""
    fixture = load_fixture()
    result = _run_full_window(fixture, flip_segments=[])
    # The runner's own cross-fold invariant passed (run completed); assert
    # it explicitly on the position ledger.
    positions = result["positions"]
    assert positions
    purged = parse_iso_utc(F1_PURGED_STAMP_ISO)
    for position in positions:
        entry_ns = int(position["entry_ns"])
        exit_ns = int(position["exit_ns"])
        if entry_ns == purged:
            continue  # legs carried across the purge gap (frozen semantics)
        assert exit_ns <= fold_end_ns(entry_ns), position
    # The purge gap instant carries positions unchanged (no entry, no cost).
    assert result["purge_gap_instants"] == [purged]
    boundaries = result["books"]
    fold_terminal_book = next(
        b
        for b in boundaries
        if int(b["decision_ns"]) == parse_iso_utc(F0_FOLD_TERMINAL_STAMP_ISO)
    )
    assert fold_terminal_book["weights"] == []
    assert fold_terminal_book["diagnostics"]["fold_terminal_force_flat"] is True
    rows = sorted(result["daily_returns"], key=lambda r: r["decision_ns"])
    gap_row = next(r for r in rows if int(r["decision_ns"]) == purged)
    assert gap_row["cost_charged_per_unit"] == 0.0
    assert gap_row["gross_realised"] == pytest.approx(1.0, abs=1e-9)


def test_v14f1_force_flat_span_never_crosses_fold_end():
    assert force_flat_span_end(parse_iso_utc("2025-12-15T00:00:00Z")) == parse_iso_utc(
        "2025-12-21T00:00:00Z"
    )
    assert force_flat_span_end(parse_iso_utc("2026-04-13T00:00:00Z")) == parse_iso_utc(
        "2026-04-20T00:00:00Z"
    )  # clamped by the F1 end boundary, not T + 7d = 2026-04-20 == boundary
    assert force_flat_span_end(parse_iso_utc("2025-09-01T00:00:00Z")) == parse_iso_utc(
        "2025-09-08T00:00:00Z"
    )


# ------------------------------------------------------------------------- #
# Frozen identity / schedule / plugin interface / gate
# ------------------------------------------------------------------------- #
def test_v14f1_frozen_arm_digests_recompute_match_and_are_pairwise_distinct():
    report = frozen_arm_digest_report()
    assert all(entry["match"] for entry in report.values()), report
    digests = {arm: report[arm]["computed_from_identity"] for arm in ARM_IDS}
    assert len(set(digests.values())) == 3
    for arm in ARM_IDS:
        identity = frozen_identity(arm)
        assert identity.family_id == FAMILY_ID
        assert identity.benchmark_symbols_excluded == (BENCHMARK_SYMBOL,)
        assert identity.matrix_cohort_hint == "v14"
        assert identity.window_start_iso == "2025-08-22T00:00:00Z"
        assert identity.window_end_iso == "2026-08-21T00:00:00Z"


def test_v14f1_frozen_schedule_and_folds_shape():
    calendar = stamp_calendar()
    assert len(calendar) == 52
    assert calendar[0] == parse_iso_utc(FIRST_STAMP_ISO)
    assert calendar[-1] == parse_iso_utc("2026-08-17T00:00:00Z")
    for stamp in calendar:
        moment = datetime.fromtimestamp(stamp / 1e9, tz=timezone.utc)
        assert moment.weekday() == 0 and moment.hour == 0 and moment.minute == 0
    effective, purged = effective_schedule(calendar)
    assert len(effective) == 51
    assert purged == {"F1": [parse_iso_utc(F1_PURGED_STAMP_ISO)]}
    assignments = fold_assignments(calendar)
    assert {label: len(members) for _i, label, members, _p in assignments} == {
        "F0": 17,
        "F1": 17,
        "F2": 17,
    }
    for stamp in calendar:
        assert parse_iso_utc("2025-08-22T00:00:00Z") <= stamp < parse_iso_utc(
            "2026-08-22T00:00:00Z"
        )


def test_v14f1_plugin_driver_surface_answers_on_fixture_world():
    """The V14 driver consumes the plugin mechanically through this surface."""
    fixture = load_fixture()
    plugin = build_plugin(ANCHOR_ARM, fixture=fixture)
    identity = plugin.identity()
    assert identity.arm_id == ANCHOR_ARM
    model = plugin.cost_model()
    assert model.taker_fee_bps == pytest.approx(5.0)
    assert model.adverse_tick_slip_floor == 1
    assert set(model.default_tick_sizes) == set(plugin.benchmark_context_symbols())
    universe = plugin.tradeable_universe()
    assert len(universe) == 13 and BENCHMARK_SYMBOL not in universe
    assert plugin.minimum_tradeable_names() == MIN_ELIGIBLE
    schedule = plugin.schedule()
    assert len(schedule.instants) == 52
    assert len(plugin.effective_instants()) == 51
    folds = plugin.folds(stress=baseline_stress(plugin), instants=list(schedule.instants))
    assert [f.label for f in folds] == ["F0", "F1", "F2"]
    assert [len(f.instants) for f in folds] == [17, 17, 17]
    dropped = plugin.folds(
        stress=StressSpec(name="drop_one_fold", dropped_fold_index=0),
        instants=list(schedule.instants),
    )
    assert dropped[0].dropped is True and not any(f.dropped for f in dropped[1:])
    stamp = int(fixture["stamp_ns"])
    book = plugin.targets_at(
        stamp, universe=universe, stress=baseline_stress(plugin)
    )
    assert book["arm_id"] == ANCHOR_ARM and book["status"] == "OK"
    fills = plugin.fills_at(
        stamp, symbols=["SYM00"], stress=baseline_stress(plugin)
    )
    assert fills[0].applied is True
    assert fills[0].fill_bar_close_ns == stamp + BUCKET_NS  # the 00:15Z close
    assert plugin.declared_execution_lag().startswith("fill at the close")
    assert plugin.marks_at(["SYM00"], stamp)["SYM00"] == pytest.approx(100.0)
    assert plugin.settlements("SYM00") == ()
    spec = plugin.price_only_gate_input_spec()
    assert "price_only_expectancy" in spec and "total_expectancy" in spec


def baseline_stress(plugin: BasislvPremfadePlugin) -> StressSpec:
    return plugin.baseline_stress()


def test_v14f1_gate_runner_preregistered_verdicts():
    passing = [True, True, False]
    failing = [True, False, False]
    # Advance path requires the price-only clause inputs (binding gate input).
    blocked = evaluate_family_gate(
        anchor_fold_positive=passing,
        control_fold_positive=failing,
        neighbour_fold_positive=passing,
    )
    assert blocked["verdict"] == VERDICT_BLOCKED_CLAUSE_INPUTS
    advance = evaluate_family_gate(
        anchor_fold_positive=passing,
        control_fold_positive=failing,
        neighbour_fold_positive=passing,
        price_only_expectancy=0.01,
        total_expectancy=0.02,
    )
    assert advance["verdict"] == VERDICT_FAMILY_ADVANCES
    assert advance["control_never_promotable"] is True
    # Clause fires: carry-harvest rejection even with every gate passing.
    carry = evaluate_family_gate(
        anchor_fold_positive=passing,
        control_fold_positive=failing,
        neighbour_fold_positive=passing,
        price_only_expectancy=-0.01,
        total_expectancy=0.02,
    )
    assert carry["verdict"] == VERDICT_REJECTED_CARRY_HARVEST
    # Control reproduces the anchor: preregistered falsification.
    falsified = evaluate_family_gate(
        anchor_fold_positive=passing,
        control_fold_positive=passing,
        neighbour_fold_positive=passing,
        price_only_expectancy=0.01,
        total_expectancy=0.02,
    )
    assert falsified["verdict"] == VERDICT_FALSIFIED_TILT
    # Anchor fails its own gate.
    anchor_fail = evaluate_family_gate(
        anchor_fold_positive=failing,
        control_fold_positive=passing,
        neighbour_fold_positive=passing,
        price_only_expectancy=0.01,
        total_expectancy=0.02,
    )
    assert anchor_fail["verdict"] == VERDICT_REJECTED_ANCHOR
    # Neighbour flips.
    neighbour_fail = evaluate_family_gate(
        anchor_fold_positive=passing,
        control_fold_positive=failing,
        neighbour_fold_positive=failing,
        price_only_expectancy=0.01,
        total_expectancy=0.02,
    )
    assert neighbour_fail["verdict"] == VERDICT_REJECTED_NEIGHBOUR
    # Clause primitives.
    fired = price_only_clause(price_only_expectancy=0.0, total_expectancy=0.1)
    assert fired["fired"] is True and fired["status"] == "APPLIED"
    not_fired = price_only_clause(price_only_expectancy=0.05, total_expectancy=0.1)
    assert not_fired["fired"] is False
    unevaluated = price_only_clause(price_only_expectancy=None, total_expectancy=0.1)
    assert unevaluated["status"] == "NOT_EVALUATED"
    with pytest.raises(ContractViolation):
        price_only_clause(price_only_expectancy=float("nan"), total_expectancy=0.1)
    with pytest.raises(ContractViolation):
        incremental_gate([True, False])


# ------------------------------------------------------------------------- #
# Drop-one (pinned wording)
# ------------------------------------------------------------------------- #
def test_v14f1_drop_one_selection_and_renormalization_pinned():
    fixture = load_fixture()
    world = build_premium_world(fixture, formation_buckets=FORMATION_BUCKETS_ANCHOR)
    stamp = int(fixture["stamp_ns"])
    universe = list(fixture["symbols"])
    record = compute_targets_at(
        ANCHOR_ARM, basis_by_symbol=world, stamp_ns=stamp, universe=universe
    )
    weights = {sym: w for sym, w in record["weights"]}
    scores = {sym: float(fixture["constant_premium_by_symbol"][sym]) for sym in weights}
    # All legs tie on |weight| = 0.125; the outcome-free tie-break drops the
    # held leg with the LARGEST |b_i|.  On the symmetric fixture world the
    # largest |b_i| = 6e-4 is attained TWICE (SYM00 -6e-4, SYM12 +6e-4), and
    # the pinned exact-tie break is the lexicographically smallest symbol id
    # => SYM00.
    dropped = select_drop_one_symbol_at(weights, scores)
    assert dropped == "SYM00"
    # With a strictly largest |b_i| the rule selects that leg (SYM12).
    scores_strict = dict(scores)
    scores_strict["SYM12"] = 0.0009
    assert select_drop_one_symbol_at(weights, scores_strict) == "SYM12"
    dropped = select_drop_one_symbol_at(weights, scores)
    book = build_drop_one_book(weights, dropped_symbol=dropped)
    assert book["n_surviving_legs"] == 7
    assert book["per_leg_weight"] == pytest.approx(1.0 / 7.0, abs=1e-12)
    assert book["gross"] == pytest.approx(1.0, abs=1e-12)
    assert "SYM00" not in {sym for sym, _w in book["weights"]}
    # An unheld symbol can never be selected; an empty book fails closed.
    with pytest.raises(ContractViolation):
        select_drop_one_symbol_at({"SYM00": 0.0}, scores)
    with pytest.raises(ContractViolation):
        build_drop_one_book(weights, dropped_symbol="SYM04")  # middle: unheld
    selection = schedule_drop_one([record])
    assert selection["proven_held"] is True
    assert selection["stamp_ns"] == stamp


# ------------------------------------------------------------------------- #
# Real A9-F staged snapshot evidence (skipped when the bulk is absent)
# ------------------------------------------------------------------------- #
STAGED_AVAILABLE = True
try:
    from research.v14.families.basislv_premfade import audits as _audits

    _MANIFEST = _audits.load_staged_manifest()
except Exception:  # pragma: no cover - machine-local bulk absent
    STAGED_AVAILABLE = False
    _MANIFEST = None


@pytest.mark.skipif(not STAGED_AVAILABLE, reason="A9-F staged bulk not on this host")
def test_v14f1_real_staged_snapshot_first_stamp_books_and_determinism():
    """SHA-verified staged world: 19/19 eligible at the first stamp, 6v6
    books at 1/12, double generation byte-identical, drop-one non-vacuous.
    Schedule-only -- no PnL."""
    from research.v14.families.basislv_premfade import audits as audits_mod

    world = audits_mod.load_basis_world(manifest=_MANIFEST, verify_sha=True)
    assert sorted(world) == sorted(audits_mod.TRADEABLE_UNIVERSE)
    assert len(world) == 19
    effective, _purged = effective_schedule(stamp_calendar())
    first = int(effective[0])
    for arm_id in (ANCHOR_ARM, NEIGHBOUR_ARM, CONTROL_ARM):
        book = compute_targets_at(
            arm_id,
            basis_by_symbol=world,
            stamp_ns=first,
            universe=audits_mod.TRADEABLE_UNIVERSE,
        )
        assert book["diagnostics"]["n_eligible"] == 19
        assert book["diagnostics"]["side_size"] == 6
        assert book["diagnostics"]["per_leg_weight"] == pytest.approx(1.0 / 12.0)
        assert book["diagnostics"]["gross_after_scale"] == pytest.approx(1.0)
        assert book["diagnostics"]["max_abs_weight"] <= CAP_MAX
        assert len(book["weights"]) == 12
    anchor_a = compute_targets_at(
        ANCHOR_ARM,
        basis_by_symbol=world,
        stamp_ns=first,
        universe=audits_mod.TRADEABLE_UNIVERSE,
    )
    anchor_b = compute_targets_at(
        ANCHOR_ARM,
        basis_by_symbol=world,
        stamp_ns=first,
        universe=audits_mod.TRADEABLE_UNIVERSE,
    )
    assert json.dumps(anchor_a, sort_keys=True) == json.dumps(anchor_b, sort_keys=True)
    # Identity report honest-match on the real lane module.
    assert all(e["match"] for e in frozen_arm_digest_report().values())
