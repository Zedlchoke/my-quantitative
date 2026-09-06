"""A8-I lane tests for A5-V15-F1-ELITE-SIZE-ASYM: the frozen cell runner
kernel -- hand-exact cost-once accounting, force-flat fold boundaries, the
one-event lag, no-lookahead mutations, stress tiers, cash-not-an-instrument
and byte-identical determinism.

Hand world (tests/test_v15_f1_fixtures.py): constant panel, price 100.0,
tick 0.01, fee 5 bps, slippage 2 ticks -> per-unit fill rate
``5e-4 + 2*0.01/100 = 7e-4``; every full transition trades
``Sigma|dw| = 14 * (0.5/7) = 1.0``; the frozen force-flat folds give exactly
6 transitions (entry + flat per fold) => ``cost_total = 6 * 7e-4 = 0.0042``
with price PnL 0 and funding 0, so ``net_return_sum = -0.0042`` exactly.
Stress tiers on the same fills: fee x1.5 -> ``6 * 9.5e-4 = 0.0057``;
+2 ticks -> ``6 * 9e-4 = 0.0054``; +1 day delay -> identical 0.0042 (the
fill prices are day-invariant) with the terminal exit clamped to the last
15m bar close of 2026-08-21.

All data SYNTHETIC; the machine-local staged root is never read; nothing is
scored and no PnL on real data exists anywhere.
"""

from __future__ import annotations

import json

import pytest

from research.v15.families.elite_size_asym.frozen_identity import (
    ANCHOR_ARM,
    CONTROL_ARM,
    NEIGHBOR_ARM,
    UNIVERSE,
)
from research.v15.families.elite_size_asym.runner import (
    fill_cost,
    run_arm,
)

from tests.test_v15_f1_fixtures import (
    BASE_RATE,
    TICK_SIZES,
    constant_root,
    copy_root_with_mutated_metrics,
    day,
    default_sum,
    shift_symbol_metrics_forward,
)

BOME = "BOMEUSDT"  # universe index 7: first middle-tercile name in the hand world
NEAR = "NEARUSDT"  # universe index 13: first short-side name
ONG = "ONGUSDT"  # universe index 14: second short-side name (the mutation survivor)
ZEC = "ZECUSDT"  # universe index 19: last short-side name


def _run(arm, root, **kwargs):
    return run_arm(arm, root, scored=False, tick_sizes=TICK_SIZES, **kwargs)


def _fills_on(run, iso_date):
    return [
        fill
        for fill in run["baseline_run"]["positions"]
        if fill["decision_date"] == iso_date
    ]


# --------------------------------------------------------------------------- #
# Hand-exact end-to-end on the constant panel
# --------------------------------------------------------------------------- #
def test_v15f1_constant_panel_hand_exact_end_to_end(constant_root):
    cell = _run(ANCHOR_ARM, constant_root)
    metrics = cell["baseline_run"]["portfolio_metrics"]
    # cost-only world: price PnL 0, funding 0, net = -cost = -0.0042 (hand)
    assert metrics["price_pnl_sum"] == 0.0
    assert metrics["funding_sum"] == 0.0
    assert metrics["cost_charged_sum"] == pytest.approx(0.0042, abs=1e-12)
    assert metrics["net_return_sum"] == pytest.approx(-0.0042, abs=1e-12)
    assert metrics["net_return_sum"] == pytest.approx(
        -metrics["cost_charged_sum"], abs=1e-12
    )
    # 6 transitions x 14 legs
    assert cell["scored_metrics"]["n_fills"] == 84
    assert metrics["n_days_with_records"] == 363  # 121 + 120 + 122 scored days
    assert metrics["gross_max_observed"] == pytest.approx(1.0, abs=1e-12)
    assert metrics["max_drawdown"] == pytest.approx(0.0042, abs=1e-12)
    assert metrics["position_pf"] == 0.0  # cost-only book: never gains
    assert metrics["expectancy_per_day"] == pytest.approx(
        -0.0042 / 363, abs=1e-15
    )
    # per-fold nets: each fold carries entry + force-flat = 2 x 14 x 7e-4
    assert cell["fold_signs"]["fold_net_sums"] == {
        "F0": pytest.approx(-0.0014, abs=1e-12),
        "F1": pytest.approx(-0.0014, abs=1e-12),
        "F2": pytest.approx(-0.0014, abs=1e-12),
    }
    assert cell["fold_signs"]["fold_positive"] == [False, False, False]
    assert cell["fold_signs"]["fold_day_counts"] == {
        "F0": 121,
        "F1": 120,
        "F2": 122,
    }
    # global defect dates inside the span: anchor windows containing
    # 2025-08-29 (decisions 2025-09-01..05) and 2026-08-12 (2026-08-15..19)
    # refuse for every symbol: 2 * 5 * 20 = 200 refusals
    assert cell["refusal_registry"]["n_refusals"] == 200
    # decisions recorded: 350 ranked days x 14 nonzero target weights
    assert cell["scored_metrics"]["n_decisions"] == 350 * 14


def test_v15f1_entry_and_forceflat_fill_dates_hand_exact(constant_root):
    run = _run(ANCHOR_ARM, constant_root)["baseline_run"]
    fills_by_date = {}
    for fill in run["positions"]:
        fills_by_date.setdefault(fill["decision_date"], []).append(fill)
    # entry at each fold's first scored day; force-flat at each fold's end
    entry_days = ["2025-08-22", "2025-12-22", "2026-04-22"]
    flat_days = ["2025-12-20", "2026-04-20", "2026-08-21"]
    for day_iso in entry_days + flat_days:
        assert len(fills_by_date[day_iso]) == 14, day_iso
    for day_iso in entry_days:
        for fill in fills_by_date[day_iso]:
            assert fill["force_flat"] is False
            assert abs(fill["delta_w"]) == pytest.approx(0.5 / 7.0, abs=1e-12)
            assert fill["weight_after"] != 0.0
    for day_iso in flat_days:
        for fill in fills_by_date[day_iso]:
            assert fill["force_flat"] is True
            assert abs(fill["delta_w"]) == pytest.approx(0.5 / 7.0, abs=1e-12)
            assert fill["weight_after"] == 0.0
    # the constant book never rebalances: fills happen ONLY on those 6 days
    assert sorted(fills_by_date) == sorted(entry_days + flat_days)
    # no decision day books any weight outside the frozen universe (cash is
    # not an instrument; the untracked remainder simply does not appear)
    for book in run["books"]:
        for symbol, _weight in book["weights"]:
            assert symbol in UNIVERSE


def test_v15f1_costs_charged_exactly_once_and_double_charge_detected(constant_root):
    cell = _run(ANCHOR_ARM, constant_root)
    run = cell["baseline_run"]
    # cost split: fills carry everything; carried boundaries charge exactly 0
    breakout = run["cost_breakout"]
    assert breakout["cost_fills"] == pytest.approx(0.0042, abs=1e-12)
    assert breakout["cost_holding_terms"] == 0.0
    assert breakout["holding_terms_zero_by_construction"] is True
    carried_days = {
        row["decision_date"] for row in run["books"] if row["carried_forward"]
    }
    assert carried_days  # the constant book carries on every ranked day
    for row in run["daily_returns"]:
        if row["instant_iso"][:10] in carried_days:
            assert row["cost_charged_per_unit"] == 0.0
    # per-fill hand check: 0.5/7 notional at rate 7e-4 (fee 5e-4 + 2 ticks)
    entry_fills = _fills_on(cell, "2025-08-22")
    assert len(entry_fills) == 14
    expected_per_fill = (0.5 / 7.0) * BASE_RATE
    for fill in entry_fills:
        assert fill["cost"] == pytest.approx(expected_per_fill, abs=1e-15)
    # the cost primitive is PURE: pricing the same transition twice returns
    # the same charge once -- a double-charge attempt cannot accumulate
    transition_cost = fill_cost(
        delta_w=0.5 / 7.0, fill_price=100.0, tick_size=0.01
    )
    assert transition_cost == fill_cost(
        delta_w=0.5 / 7.0, fill_price=100.0, tick_size=0.01
    )
    assert transition_cost == pytest.approx((0.5 / 7.0) * BASE_RATE, abs=1e-18)
    # an exact replay of the same cell recomputes the identical cost once
    replay = _run(ANCHOR_ARM, constant_root)
    assert replay["baseline_run"]["portfolio_metrics"]["cost_charged_sum"] == (
        cell["baseline_run"]["portfolio_metrics"]["cost_charged_sum"]
    )
    assert (
        replay["hashes"]["result_sha256"] == cell["hashes"]["result_sha256"]
    )


def test_v15f1_stress_tiers_hand_exact(constant_root):
    cell = _run(ANCHOR_ARM, constant_root)
    tiers = cell["stress_tiers"]
    # fee x1.5 (7.5 bps): 6 transitions x 1.0 x (7.5e-4 + 2e-4) = 0.0057
    assert tiers["fee_x1_5"]["cost_total"] == pytest.approx(0.0057, abs=1e-12)
    # +2 ticks (4 total): 6 transitions x 1.0 x (5e-4 + 4e-4) = 0.0054
    assert tiers["plus2ticks"]["cost_total"] == pytest.approx(0.0054, abs=1e-12)
    # +1 day delay: identical fill set and day-invariant prices -> 0.0042,
    # with the terminal exit realized at the last 15m close of 2026-08-21
    assert tiers["delay_plus1d"]["cost_total"] == pytest.approx(0.0042, abs=1e-12)
    assert tiers["delay_plus1d"]["terminal_delay_clamped"] is True
    assert tiers["delay_plus1d"]["n_fills"] == 84
    assert tiers["fee_x1_5"]["terminal_delay_clamped"] is False
    # the three tiers are three DISTINCT cost states on the same bookings
    assert len({tiers[t]["cost_total"] for t in tiers}) == 3
    # all three stress nets are distinct and recorded for the gate set
    nets = {tier: tiers[tier]["net_return_sum"] for tier in tiers}
    assert nets["fee_x1_5"] == pytest.approx(-0.0057, abs=1e-12)
    assert nets["plus2ticks"] == pytest.approx(-0.0054, abs=1e-12)
    assert nets["delay_plus1d"] == pytest.approx(-0.0042, abs=1e-12)


def test_v15f1_fold_force_flat_no_position_straddles_purge(constant_root):
    run = _run(ANCHOR_ARM, constant_root)["baseline_run"]
    purge = {"2025-12-21", "2026-04-21"}
    # no PnL row exists on a purge day (book flat, unscored)
    row_days = {row["instant_iso"][:10] for row in run["daily_returns"]}
    assert not (row_days & purge)
    # every fold-end book is the EMPTY book (force-flat fills at that day's
    # 00:00 open), so no position can straddle into the purge or the next fold
    for book in run["books"]:
        if book["decision_date"] in ("2025-12-20", "2026-04-20", "2026-08-21"):
            assert book["weights"] == []
    # each next fold starts flat and re-enters at its first scored day
    entry_days = {"2025-08-22", "2025-12-22", "2026-04-22"}
    for book in run["books"]:
        if book["decision_date"] in entry_days:
            assert len(book["weights"]) == 14
    # fold indices partition the rows exactly into the frozen folds
    fold_of = {
        "F0": range(121),
        "F1": range(120),
        "F2": range(122),
    }
    counts = {0: 0, 1: 0, 2: 0}
    for row in run["daily_returns"]:
        counts[row["fold_index"]] += 1
    assert counts[0] == len(fold_of["F0"])
    assert counts[1] == len(fold_of["F1"])
    assert counts[2] == len(fold_of["F2"])


# --------------------------------------------------------------------------- #
# Lag / no-lookahead mutations
# --------------------------------------------------------------------------- #
def _mutated_root(source, destination, mutated_days):
    """BOME's sum ratio set to 50.0 (clips to ln 100 at the feature) on the
    given days; everything else stays in the hand world."""

    def mutated_sum(symbol, day_value):
        if symbol == BOME and day_value in set(mutated_days):
            return 50.0
        return default_sum(symbol, day_value)

    return copy_root_with_mutated_metrics(
        source, destination, BOME, sum_fn=mutated_sum
    )


def test_v15f1_lag_boundary_mutation_changes_target_book(constant_root, tmp_path):
    # BOME (index 7, middle) gets ln(50) on 2025-08-15..17 -- all READABLE at
    # the first decision 2025-08-22 (window [2025-08-15 .. 2025-08-19]):
    # median of [ln50, ln50, ln50, ln1.8, ln1.8] = ln(50) -> BOME jumps to
    # the SHORT side top; with 7 names to pick above BOME the displaced
    # short-side member is NEAR (index 13, the weakest short), while ONG
    # (index 14) survives on the mutated side.
    mutated_root = _mutated_root(
        constant_root,
        tmp_path / "mutated_readable",
        [day("2025-08-15"), day("2025-08-16"), day("2025-08-17")],
    )
    base = _run(ANCHOR_ARM, constant_root)
    mutated = _run(ANCHOR_ARM, mutated_root)
    base_entry = _fills_on(base, "2025-08-22")
    mutated_entry = _fills_on(mutated, "2025-08-22")
    assert all(fill["symbol"] != BOME for fill in base_entry)
    assert sorted(f["symbol"] for f in base_entry if f["weight_after"] < 0) == sorted(
        UNIVERSE[13:20]
    )
    bome_fills = [f for f in mutated_entry if f["symbol"] == BOME]
    assert len(bome_fills) == 1
    assert bome_fills[0]["weight_after"] < 0  # enters the SHORT side
    assert bome_fills[0]["delta_w"] == pytest.approx(-0.5 / 7.0, abs=1e-12)
    ong_fills = [f for f in mutated_entry if f["symbol"] == ONG]
    assert len(ong_fills) == 1
    assert ong_fills[0]["weight_after"] < 0  # stays on the mutated short side
    near_fills = [f for f in mutated_entry if f["symbol"] == NEAR]
    assert near_fills == []  # displaced from the short side BEFORE ever holding
    assert mutated["hashes"]["result_sha256"] != base["hashes"]["result_sha256"]


def test_v15f1_no_lookahead_future_mutation_cannot_touch_earlier_decisions(
    constant_root, tmp_path
):
    # The SAME values placed on 2025-08-20..22 are UNREADABLE at the
    # 2025-08-22 decision (they sit after D-3): the book and fills on that
    # day must be byte-identical to the baseline ...
    future_root = _mutated_root(
        constant_root,
        tmp_path / "mutated_future",
        [day("2025-08-20"), day("2025-08-21"), day("2025-08-22")],
    )
    base = _run(ANCHOR_ARM, constant_root)
    future = _run(ANCHOR_ARM, future_root)
    base_entry = sorted(
        (f["symbol"], round(f["delta_w"], 12)) for f in _fills_on(base, "2025-08-22")
    )
    future_entry = sorted(
        (f["symbol"], round(f["delta_w"], 12))
        for f in _fills_on(future, "2025-08-22")
    )
    assert future_entry == base_entry
    base_book = [
        book
        for book in base["baseline_run"]["books"]
        if book["decision_date"] == "2025-08-22"
    ]
    future_book = [
        book
        for book in future["baseline_run"]["books"]
        if book["decision_date"] == "2025-08-22"
    ]
    assert future_book == base_book
    # ... while the SAME future data DOES move LATER decisions (2025-08-25's
    # window [2025-08-18 .. 2025-08-22] reads it): the cell result changes.
    assert future["hashes"]["result_sha256"] != base["hashes"]["result_sha256"]
    future_late = _fills_on(future, "2025-08-25")
    assert [f for f in future_late if f["symbol"] == BOME]
    assert not [f for f in _fills_on(base, "2025-08-25") if f["symbol"] == BOME]


def test_v15f1_shifting_data_forward_changes_results(constant_root, tmp_path):
    # readable-window mutation at 2025-08-16..18 (BOME's sum -> 50); then
    # shift BOME's whole panel +1 day (the earliest day falls off; nothing
    # is synthesized).  Both runs read a 3-of-5 majority of ln(50) at the
    # first decisions, so the short-side entry is identical; the slide
    # surfaces at the EXIT: the unshifted median reverts to ln(1.8) at the
    # 2025-08-24 decision (window [2025-08-17 .. 2025-08-21] holds only 2
    # mutated cells) -> BOME exits the short side on 2025-08-24, while the
    # shifted panel still holds 3 mutated cells in that window and exits on
    # 2025-08-25 instead.  The shifted data also ends one day earlier
    # (2025-08-22), so BOME's later windows go over the >10% hole bound and
    # its decisions refuse -- visible in the registry, never synthesized.
    readable_root = _mutated_root(
        constant_root,
        tmp_path / "mutated_slide",
        [day("2025-08-16"), day("2025-08-17"), day("2025-08-18")],
    )
    shifted_root = shift_symbol_metrics_forward(
        readable_root, tmp_path / "shifted", BOME, shift_days=1
    )
    unshifted = _run(ANCHOR_ARM, readable_root)
    shifted = _run(ANCHOR_ARM, shifted_root)
    assert (
        shifted["hashes"]["result_sha256"]
        != unshifted["hashes"]["result_sha256"]
    )
    # identical short-side entry at the first decision (2025-08-22)
    unshifted_entry = sorted(
        (f["symbol"], round(f["delta_w"], 12))
        for f in _fills_on(unshifted, "2025-08-22")
    )
    shifted_entry = sorted(
        (f["symbol"], round(f["delta_w"], 12))
        for f in _fills_on(shifted, "2025-08-22")
    )
    assert unshifted_entry == shifted_entry
    assert any(f["symbol"] == BOME for f in _fills_on(unshifted, "2025-08-22"))
    # the exit slides 2025-08-24 (unshifted) -> 2025-08-25 (shifted)
    unshifted_exit = [
        f for f in _fills_on(unshifted, "2025-08-24") if f["symbol"] == BOME
    ]
    assert len(unshifted_exit) == 1
    assert unshifted_exit[0]["weight_after"] == 0.0
    assert not [
        f for f in _fills_on(shifted, "2025-08-24") if f["symbol"] == BOME
    ]
    shifted_exit = [
        f for f in _fills_on(shifted, "2025-08-25") if f["symbol"] == BOME
    ]
    assert len(shifted_exit) == 1
    assert shifted_exit[0]["weight_after"] == 0.0
    # the shift perturbs RANKS, not coverage: BOME's refusals stay exactly
    # the 10 global-defect-window days in both runs
    unshifted_bome = unshifted["refusal_registry"]["by_symbol"].get(BOME, 0)
    shifted_bome = shifted["refusal_registry"]["by_symbol"].get(BOME, 0)
    assert unshifted_bome == shifted_bome == 10


# --------------------------------------------------------------------------- #
# Neighbour / control cells on the same kernel
# --------------------------------------------------------------------------- #
def test_v15f1_neighbor_cell_hand_exact_and_tolerates_one_in_ten(constant_root):
    cell = _run(NEIGHBOR_ARM, constant_root)
    metrics = cell["baseline_run"]["portfolio_metrics"]
    # 10 legs x 0.10 = 1.0 gross per transition: the SAME hand total
    assert metrics["cost_charged_sum"] == pytest.approx(0.0042, abs=1e-12)
    assert cell["scored_metrics"]["n_fills"] == 6 * 10
    entry = _fills_on(cell, "2025-08-22")
    assert len(entry) == 10
    assert all(abs(f["delta_w"]) - 0.10 < 1e-12 for f in entry)
    # the 10-day window tolerates exactly-one missing cell (1/10 = 10% is
    # NOT > 10%): the two in-span global defect dates refuse NOTHING
    assert cell["refusal_registry"]["n_refusals"] == 0


def test_v15f1_control_cell_runs_identical_kernel_on_level_feature(constant_root):
    anchor = _run(ANCHOR_ARM, constant_root)
    control = _run(CONTROL_ARM, constant_root)
    # structural distinctness: identical cost state (same machinery, same
    # fold force-flats) but a DIFFERENT book membership (level ties break by
    # symbol id ascending: long = universe[0:7] -- the same side here, so
    # the digests agree only if the machinery does; the arm identity pins
    # the distinction)
    assert control["baseline_run"]["portfolio_metrics"][
        "cost_charged_sum"
    ] == pytest.approx(0.0042, abs=1e-12)
    assert control["refusal_registry"]["n_refusals"] == 200
    assert control["arm_id"] == CONTROL_ARM
    assert anchor["hashes"]["result_sha256"] != control["hashes"]["result_sha256"]
    assert control["role"] == "causal_negative_control"
    # the control's sort key is the headcount LEVEL alone: on this panel
    # every level is ln(1.0) = 0 -> the tie-break book longs universe[0:7]
    entry = _fills_on(control, "2025-08-22")
    assert sorted(f["symbol"] for f in entry if f["delta_w"] > 0) == sorted(
        UNIVERSE[0:7]
    )


# --------------------------------------------------------------------------- #
# Accounting identity / determinism / driver shape
# --------------------------------------------------------------------------- #
def test_v15f1_cash_not_an_instrument_and_identity_holds(constant_root):
    cell = _run(ANCHOR_ARM, constant_root)
    run = cell["baseline_run"]
    metrics = run["portfolio_metrics"]
    # no instrument outside the frozen universe can ever appear (cash is
    # not an instrument: untracked budget simply does not appear)
    for book in run["books"]:
        for symbol, _weight in book["weights"]:
            assert symbol in UNIVERSE
    # exact accounting identity: net = price + funding - cost
    assert metrics["net_return_sum"] == pytest.approx(
        metrics["price_pnl_sum"] + metrics["funding_sum"] - metrics[
            "cost_charged_sum"
        ],
        abs=1e-12,
    )
    # fully-refused days (2025-09-01..05, 2026-08-15..19) never trade: their
    # book rows are carried_forward with UNCHANGED weights and zero cost
    refused_days = {
        "2025-09-01",
        "2025-09-02",
        "2025-09-03",
        "2025-09-04",
        "2025-09-05",
        "2026-08-15",
        "2026-08-16",
        "2026-08-17",
        "2026-08-18",
        "2026-08-19",
    }
    books_by_date = {b["decision_date"]: b for b in run["books"]}
    carried = {
        row["decision_date"]
        for row in run["books"]
        if row["carried_forward"]
    }
    assert refused_days <= carried
    weights_on_refused = books_by_date["2025-09-01"]["weights"]
    weights_before = books_by_date["2025-08-29"]["weights"]
    assert weights_on_refused == weights_before
    for row in run["daily_returns"]:
        if row["instant_iso"][:10] in refused_days:
            assert row["cost_charged_per_unit"] == 0.0


def test_v15f1_deterministic_double_generation_byte_identical(constant_root):
    first = _run(ANCHOR_ARM, constant_root)
    second = _run(ANCHOR_ARM, constant_root)
    assert json.dumps(first, sort_keys=True, separators=(",", ":"), default=str) == (
        json.dumps(second, sort_keys=True, separators=(",", ":"), default=str)
    )
    # ... and the neighbour cell differs from the anchor cell (distinct arm)
    neighbor = _run(NEIGHBOR_ARM, constant_root)
    assert neighbor["hashes"]["result_sha256"] != first["hashes"][
        "result_sha256"
    ]


def test_v15f1_cell_result_matches_v14_driver_contract_shape(constant_root):
    cell = _run(ANCHOR_ARM, constant_root, )
    # the keys the V14 scored-driver contract consumes (run_v14_cell.py)
    assert cell["family_id"] == "A5-V15-F1-ELITE-SIZE-ASYM"
    assert cell["arm_id"] == ANCHOR_ARM
    assert cell["scored"] is False  # no scored flag is ever set by this lane
    assert cell["universe"] == list(UNIVERSE)
    scored = cell["scored_metrics"]
    for key in (
        "score_valid",
        "net_return_sum",
        "expectancy_per_day",
        "max_drawdown",
        "position_pf",
        "n_positions",
        "n_decisions",
        "n_fills",
        "decisions",
        "fills",
        "cost_fills",
        "cost_holding_terms",
        "cost_total",
        "funding_sum",
        "price_pnl_sum",
        "remediated_kernel",
    ):
        assert key in scored, key
    assert scored["remediated_kernel"] is True
    run = cell["baseline_run"]
    for key in (
        "daily_returns",
        "books",
        "positions",
        "decisions",
        "fills",
        "portfolio_metrics",
        "cost_breakout",
        "hashes",
    ):
        assert key in run, key
    row = run["daily_returns"][0]
    for key in (
        "decision_ns",
        "fold_index",
        "net_return_per_unit",
        "cost_charged_per_unit",
    ):
        assert key in row, key
    assert "result_sha256" in cell["hashes"]
    # spec pins ride with the cell (proposal + selection + p3 + amendment)
    assert cell["spec_pins"]["proposal_P1"] == (
        "6d2bc25fc3d3e5ebd96ca60c8e428efed9823b94589073f41ddcbdf47392cb16"
    )
    # refusal registry digest is carried for the cell evidence
    assert len(cell["refusal_registry"]["digest"]) == 64
    # per-symbol PnL shares: a cost-only book has no positive pool
    assert cell["per_symbol_pnl"]["positive_shares"] == {}
    assert cell["per_symbol_pnl"]["largest_positive_share"] == 0.0
    totals = cell["per_symbol_pnl"]["totals"]
    assert sorted(totals) == sorted(UNIVERSE)
    held = sorted(s for s in UNIVERSE if abs(totals[s]) > 0.0)
    assert len(held) == 14
    assert all(totals[s] == pytest.approx(-6 * (0.5 / 7.0) * BASE_RATE, abs=1e-12) for s in held)
    assert all(totals[s] == 0.0 for s in UNIVERSE if s not in held)
