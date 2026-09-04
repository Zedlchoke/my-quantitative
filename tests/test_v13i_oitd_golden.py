"""V13 I lane -- hand-computed feature/target goldens for OITD (evidence a).

Every expected value in this file is derived BY HAND from the synthetic
world in ``tests/v13i_oitd_world.py`` (see its header for the arithmetic):

* signal goldens: world A gives ``D_i = 1 / (1000 + i)`` exactly; world B
  gives group durations D_H = 0.009, D_M = 0.0006, D_L = 0.00012 exactly
  (OI7 = the symbol constant -- 9 daily stamps, latest 7 all equal --
  MK = 10, TO = the group's constant daily turnover);
* target goldens: world B anchor longs = SYM12..17 at +1/12 each, shorts
  = SYM00..05 at -1/12 each, buffer SYM06..11 unheld; with the hand group
  forward returns the anchor weekly book return is EXACTLY +0.03 and the
  56d neighbour's EXACTLY the same (same ranking, wider denominator);
* hysteresis hand-trace at the second weekly stamp: a held long pushed to
  rank 18 FLIPS short; a held long drifting into the buffer KEEPS its
  side; weights re-equalise per side by construction;
* fail-closed goldens: < 7 OI stamps in the trailing 10 days, a 28d
  turnover gap, and a stale (> 24h) mark each make exactly the affected
  symbol ineligible (never guessed, never zeroed by inference);
* breadth: below 12 eligible names raises ``EligibilityShortfall`` on a
  flat start (a stamp without a well-formed book has NO book).

All data synthetic; no real data is read; no scored metric is computed.
"""

from __future__ import annotations

import pytest

from tests.v13i_oitd_world import (
    DAY_NS,
    GROUP_H,
    GROUP_L,
    GROUP_M,
    SYMBOLS,
    T1_DAY,
    T1_NS,
    T2_DAY,
    T2_NS,
    WORLD_B_DURATIONS,
    world_a,
    world_b,
)

from research.v13.families.oitd.book import (
    EligibilityShortfall,
    build_hysteresis_book,
)
from research.v13.families.oitd.strategy import (
    ANCHOR_ARM,
    NEIGHBOUR_ARM,
    compute_targets_at,
    latest_mark,
    mean_daily_turnover,
    oi7_mean,
    signal_scores_at,
)

PER_SIDE_WEIGHT = 1.0 / 12.0  # 0.5 gross per side / 6 members (cap 0.30 slack)


# --------------------------------------------------------------------- #
# Feature goldens (hand-computed signals)
# --------------------------------------------------------------------- #
def test_world_a_duration_scores_are_the_hand_exact_values() -> None:
    world = world_a()
    scores = signal_scores_at(
        ANCHOR_ARM,
        day_turnover_by_symbol=world["day_turnover_by_symbol"],
        stamp_ns=T1_NS,
        universe=world["universe"],
        oi_by_symbol=world["oi_by_symbol"],
        mark_by_symbol=world["mark_by_symbol"],
    )
    assert len(scores) == 18
    for sym, expected in world["expected_scores"].items():
        assert scores[sym] == pytest.approx(expected, rel=1e-15), sym
    # hand spot checks on paper values
    assert scores["SYM00"] == pytest.approx(0.001, rel=1e-15)
    assert scores["SYM17"] == pytest.approx(1.0 / 1017.0, rel=1e-15)


def test_world_b_group_durations_are_hand_exact() -> None:
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    scores = signal_scores_at(
        ANCHOR_ARM,
        day_turnover_by_symbol=world["day_turnover_by_symbol"],
        stamp_ns=T1_NS,
        universe=world["universe"],
        oi_by_symbol=world["oi_by_symbol"],
        mark_by_symbol=world["mark_by_symbol"],
    )
    for sym in GROUP_H:
        assert scores[sym] == pytest.approx(WORLD_B_DURATIONS["H"], rel=1e-15), sym
    for sym in GROUP_M:
        assert scores[sym] == pytest.approx(WORLD_B_DURATIONS["M"], rel=1e-15), sym
    for sym in GROUP_L:
        assert scores[sym] == pytest.approx(WORLD_B_DURATIONS["L"], rel=1e-15), sym


def test_oi7_is_the_mean_of_the_latest_seven_stamps() -> None:
    # 9 stamps of a hand sequence 1..9 (chronological); OI7 = mean(3..9) = 6
    stamp = T1_NS
    series = tuple(
        (stamp - (10 - d) * DAY_NS, float(d))
        for d in range(1, 10)
    )
    assert oi7_mean(series, stamp) == pytest.approx(6.0)
    # a later-arriving 10th stamp is unreadable (PIT) and changes nothing
    series_with_future = series + ((stamp + DAY_NS, 99.0),)
    assert oi7_mean(series_with_future, stamp) == pytest.approx(6.0)
    # only 6 stamps in the span -> ineligible (fail closed)
    assert oi7_mean(series[:6], stamp) is None


def test_mean_daily_turnover_window_and_gap_fail_closed() -> None:
    # days 1..60 (day index T1_DAY - 60 + d), value = day; 28d mean = ...
    lo = T1_DAY - 60
    days = {lo + d: float(d + 1) for d in range(60)}
    stamp = T1_NS
    # window = the 28 buckets ending at T1_DAY - 1 -> values 33..60, mean 46.5
    assert mean_daily_turnover(days, stamp, window_days=28) == pytest.approx(46.5)
    assert mean_daily_turnover(days, stamp, window_days=56) == pytest.approx(
        (5.0 + 60.0) / 2.0 * 56 / 56
    )  # values 5..60 -> mean 32.5 -- asserted exactly below
    assert mean_daily_turnover(days, stamp, window_days=56) == pytest.approx(32.5)
    # ONE missing day inside the window is a GAP: fail closed (never filled)
    broken = dict(days)
    del broken[T1_DAY - 3]
    assert mean_daily_turnover(broken, stamp, window_days=28) is None
    # a future day can never be read
    future_only = {T1_DAY + 1: 1e9, T1_DAY + 2: 1e9}
    assert mean_daily_turnover(future_only, stamp, window_days=28) is None


def test_latest_mark_staleness_gate() -> None:
    stamp = T1_NS
    fresh = ((stamp - 3_600_000_000_000, 10.0),)
    assert latest_mark(fresh, stamp) == pytest.approx(10.0)
    stale = ((stamp - 25 * 3_600_000_000_000, 10.0),)
    assert latest_mark(stale, stamp) is None
    # a later-arriving snapshot is unreadable (PIT)
    with_future = fresh + ((stamp + 60_000_000_000, 42.0),)
    assert latest_mark(with_future, stamp) == pytest.approx(10.0)
    # non-positive marks fail closed
    assert latest_mark(((stamp - 60, 0.0),), stamp) is None


# --------------------------------------------------------------------- #
# Target goldens (hand-computed books)
# --------------------------------------------------------------------- #
def _anchor_targets(world):
    return compute_targets_at(
        ANCHOR_ARM,
        day_turnover_by_symbol=world["day_turnover_by_symbol"],
        stamp_ns=int(world["stamp_ns"]),
        universe=world["universe"],
        oi_by_symbol=world["oi_by_symbol"],
        mark_by_symbol=world["mark_by_symbol"],
    )


def test_world_b_anchor_book_is_the_hand_computed_book() -> None:
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    book = _anchor_targets(world)
    # hand truth: long the lowest-D tercile (group L), short the highest (H)
    assert [sym for sym, _w in book["longs"]] == list(GROUP_L)
    assert [sym for sym, _w in book["shorts"]] == list(GROUP_H)
    weights = {sym: float(w) for sym, w in book["weights"]}
    assert len(weights) == 12
    for sym in GROUP_L:
        assert weights[sym] == pytest.approx(PER_SIDE_WEIGHT, rel=1e-12), sym
    for sym in GROUP_H:
        assert weights[sym] == pytest.approx(-PER_SIDE_WEIGHT, rel=1e-12), sym
    # the middle tercile is the buffer: never held at entry
    for sym in GROUP_M:
        assert sym not in weights
    # the hand ranks: L best (1..6), M buffer (7..12), H worst (13..18)
    ranks = {sym: int(r) for sym, r in book["diagnostics"]["ranks"]}
    for sym in GROUP_L:
        assert 1 <= ranks[sym] <= 6, sym
    for sym in GROUP_M:
        assert 7 <= ranks[sym] <= 12, sym
    for sym in GROUP_H:
        assert 13 <= ranks[sym] <= 18, sym


def test_world_b_anchor_book_return_is_exactly_plus_three_percent() -> None:
    """The falsifiable direction, on paper: long low-D outperforms high-D."""
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    book = _anchor_targets(world)
    book_return = sum(
        float(w) * world["forward_returns"][str(sym)] for sym, w in book["weights"]
    )
    # long leg 0.5 x (+3%) + short leg 0.5 x (+3%) = +0.03 exactly
    assert book_return == pytest.approx(0.03, abs=1e-12)


def test_neighbour_56d_book_matches_the_anchor_on_world_b() -> None:
    """Same mechanism, wider denominator: identical legs on the hand world.

    The 56d window equals the 28d window here (constant daily turnover),
    so the neighbour ranks identically -- the neighbour SUPPORTS the
    anchor on this fixture (the instability direction is data-driven and
    remains a Stage-A outcome concern).
    """
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    anchor = _anchor_targets(world)
    neighbour = compute_targets_at(
        NEIGHBOUR_ARM,
        day_turnover_by_symbol=world["day_turnover_by_symbol"],
        stamp_ns=T1_NS,
        universe=world["universe"],
        oi_by_symbol=world["oi_by_symbol"],
        mark_by_symbol=world["mark_by_symbol"],
    )
    assert [s for s, _ in neighbour["longs"]] == [s for s, _ in anchor["longs"]]
    assert [s for s, _ in neighbour["shorts"]] == [s for s, _ in anchor["shorts"]]
    neighbour_return = sum(
        float(w) * world["forward_returns"][str(sym)]
        for sym, w in neighbour["weights"]
    )
    assert neighbour_return == pytest.approx(0.03, abs=1e-12)


# --------------------------------------------------------------------- #
# Hysteresis hand-trace (chained stamps)
# --------------------------------------------------------------------- #
def test_hysteresis_buffer_keeps_side_and_opposite_zone_flips() -> None:
    """Hand trace at the second weekly stamp.

    Enter with the plain world-B book (long L, short H, buffer M).  One
    week later:
    * SYM12 (a held long) gets OI 1200 -> D = 12000/250000 = 0.048, the
      NEW maximum duration -> rank 18 -> SHORT_ENTER zone -> FLIPS short;
    * SYM13 (a held long) gets OI 50 -> D = 500/250000 = 0.002 -> the
      last buffer slot (ordering: SYM14..17, then M, then SYM13, then H,
      then SYM12) -> BUFFER -> KEEPS its long side (exit only beyond the
      buffer into the opposite entry zone).
    Hand book at stamp 2 (7 v 7 after re-equalisation, w = 1/14 each):
    longs = {SYM06, SYM07 (fresh long-zone entrants), SYM13..17 (held)};
    shorts = {SYM00..05 (held), SYM12 (flipped)}.
    """
    from tests.v13i_oitd_world import hysteresis_world, plugin as make_plugin

    world = hysteresis_world({"SYM12": 1200.0, "SYM13": 50.0})
    p = make_plugin(ANCHOR_ARM, world)
    universe = tuple(world["universe"])
    stress = p.baseline_stress()
    first = p.targets_at(T1_NS, universe=universe, stress=stress)
    weights1 = {sym: float(w) for sym, w in first["weights"]}
    assert weights1["SYM12"] > 0 and weights1["SYM13"] > 0  # both held long
    second = p.targets_at(T2_NS, universe=universe, stress=stress)
    weights2 = {sym: float(w) for sym, w in second["weights"]}
    # the flip: SYM12 crossed into the opposite entry zone
    assert weights2["SYM12"] == pytest.approx(-1.0 / 14.0, rel=1e-12)
    # the buffer drift: SYM13 keeps its long side
    assert weights2["SYM13"] == pytest.approx(1.0 / 14.0, rel=1e-12)
    # the rest of the held long tercile stays long
    for sym in ("SYM14", "SYM15", "SYM16", "SYM17"):
        assert weights2[sym] == pytest.approx(1.0 / 14.0, rel=1e-12)
    # fresh long-zone entrants enter long (flat before)
    for sym in ("SYM06", "SYM07"):
        assert weights2[sym] == pytest.approx(1.0 / 14.0, rel=1e-12)
    # the held short tercile stays short and re-equalises over 7 members
    for sym in GROUP_H:
        assert weights2[sym] == pytest.approx(-1.0 / 14.0, rel=1e-12)
    assert len(weights2) == 14
    assert second["carried_forward"] is False


def test_full_leg_flip_rebalances_and_reequalises() -> None:
    """All six held longs pushed past the buffer -> the whole leg flips.

    One week after the plain world-B book, every L name's duration jumps
    to 0.048 (OI 1200 x MK 10 / 250_000): all six cross into the short
    entry zone and flip, the held H shorts stay short (buffer), and the
    fresh long-zone entrants (group M) enter long.  Hand book at stamp 2:
    longs = M (6 x 1/12), shorts = H + flipped L (12 x -1/24).
    """
    from tests.v13i_oitd_world import (
        GROUP_L,
        GROUP_M,
        hysteresis_world,
        plugin as make_plugin,
    )

    world = hysteresis_world({sym: 1200.0 for sym in GROUP_L})
    p = make_plugin(ANCHOR_ARM, world)
    universe = tuple(world["universe"])
    stress = p.baseline_stress()
    first = p.targets_at(T1_NS, universe=universe, stress=stress)
    weights1 = {sym: float(w) for sym, w in first["weights"]}
    assert all(weights1[sym] > 0 for sym in GROUP_L)  # L held long at stamp 1
    second = p.targets_at(T2_NS, universe=universe, stress=stress)
    assert second["carried_forward"] is False
    weights2 = {sym: float(w) for sym, w in second["weights"]}
    # the flipped leg
    for sym in GROUP_L:
        assert weights2[sym] == pytest.approx(-1.0 / 24.0, rel=1e-12), sym
    # the buffer-held shorts
    for sym in world["universe"]:
        if sym in {"SYM00", "SYM01", "SYM02", "SYM03", "SYM04", "SYM05"}:
            assert weights2[sym] == pytest.approx(-1.0 / 24.0, rel=1e-12), sym
    # the fresh long-zone entrants
    assert sorted(sym for sym, w in weights2.items() if w > 0) == list(GROUP_M)
    for sym in GROUP_M:
        assert weights2[sym] == pytest.approx(1.0 / 12.0, rel=1e-12), sym
    # invariants survive the re-equalisation
    import math

    gross = math.fsum(abs(w) for w in weights2.values())
    assert gross == pytest.approx(1.0, abs=1e-9)


def test_held_symbol_losing_eligibility_carries_the_book() -> None:
    """A held symbol whose score disappears must not be zeroed by inference.

    SYM17's turnover map loses one day inside the window -> its D is
    uncomputable at stamp 2 -> the WHOLE stamp's rebalance is skipped and
    the previous book is carried (fail-closed).
    """
    from tests.v13i_oitd_world import merged_world, plugin as make_plugin

    world = merged_world(
        [T1_NS, T2_NS],
        drop_turnover_days_for={"SYM17": [T2_DAY - 3]},
    )
    p = make_plugin(ANCHOR_ARM, world)
    universe = tuple(world["universe"])
    stress = p.baseline_stress()
    first = p.targets_at(T1_NS, universe=universe, stress=stress)
    weights1 = {sym: float(w) for sym, w in first["weights"]}
    assert weights1["SYM17"] > 0
    second = p.targets_at(T2_NS, universe=universe, stress=stress)
    assert second["carried_forward"] is True
    assert second["reason_code"] == "HELD_SYMBOL_INELIGIBLE_BOOK_CARRIED"
    assert {sym: float(w) for sym, w in second["weights"]} == weights1


def test_flat_start_has_no_hysteresis_memory() -> None:
    """A FLAT start re-derives zones from scratch: long side = group M.

    Contrast with the chained trace above: pushing every L name to huge
    duration on a FLAT start simply re-ranks -- the long zone is the
    entry zone (group M), never a thin side; the thin-side guard exists
    for the CHAINED book (see the carry test above).
    """
    from tests.v13i_oitd_world import plugin as make_plugin

    w = world_b(
        day_index=T1_DAY,
        stamp_ns=T1_NS,
        oi_overrides={sym: 1200.0 for sym in GROUP_L},
    )
    p = make_plugin(ANCHOR_ARM, w)
    book = p.targets_at(T1_NS, universe=tuple(w["universe"]), stress=p.baseline_stress())
    assert book["carried_forward"] is False
    assert [sym for sym, _w in book["longs"]] == list(GROUP_M)
    assert [sym for sym, _w in book["shorts"]] == list(GROUP_L)
    for _sym, w in book["weights"]:
        assert abs(float(w)) == pytest.approx(PER_SIDE_WEIGHT, rel=1e-12)


def test_below_twelve_eligible_names_fails_closed_on_a_flat_start() -> None:
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    short_universe = list(SYMBOLS[:11])
    with pytest.raises(EligibilityShortfall):
        compute_targets_at(
            ANCHOR_ARM,
            day_turnover_by_symbol=world["day_turnover_by_symbol"],
            stamp_ns=T1_NS,
            universe=short_universe,
            oi_by_symbol=world["oi_by_symbol"],
            mark_by_symbol=world["mark_by_symbol"],
        )


# --------------------------------------------------------------------- #
# Data-driven ineligibility (fail-closed goldens)
# --------------------------------------------------------------------- #
def test_insufficient_oi_history_makes_the_symbol_ineligible() -> None:
    world = world_b(day_index=T1_DAY, stamp_ns=T1_NS)
    broken_oi = {sym: series for sym, series in world["oi_by_symbol"].items()}
    broken_oi["SYM07"] = broken_oi["SYM07"][:6]  # 6 stamps < the frozen 7
    scores = signal_scores_at(
        ANCHOR_ARM,
        day_turnover_by_symbol=world["day_turnover_by_symbol"],
        stamp_ns=T1_NS,
        universe=world["universe"],
        oi_by_symbol=broken_oi,
        mark_by_symbol=world["mark_by_symbol"],
    )
    assert "SYM07" not in scores
    assert set(scores) == set(world["universe"]) - {"SYM07"}


def test_turnover_gap_and_stale_mark_ineligibility_flow_into_the_book() -> None:
    """Hand book after two eligible-name losses (both from the long group).

    SYM16 loses a 28d turnover day (gap -> fail closed) and SYM15's mark
    goes stale (> 24h -> fail closed): 16 eligible names remain, terciles
    of 5.  Hand result: long zone ranks 1..5 = {SYM12,13,14,17} + SYM06
    at w = 0.1; short zone ranks 12..16 = SYM01..05 at w = -0.1.
    """
    world = dict(world_b(day_index=T1_DAY, stamp_ns=T1_NS))
    to = {sym: dict(days) for sym, days in world["day_turnover_by_symbol"].items()}
    del to["SYM16"][T1_DAY - 5]  # a gap inside the 28d window
    world["day_turnover_by_symbol"] = to
    world["mark_by_symbol"] = {
        **world["mark_by_symbol"],
        "SYM15": ((T1_NS - 25 * 3_600_000_000_000, 10.0),),  # stale > 24h
    }
    book = _anchor_targets(world)
    assert book["diagnostics"]["n_eligible"] == 16
    # hand legs (book lists render alphabetically sorted)
    assert [sym for sym, _w in book["longs"]] == sorted(
        ["SYM12", "SYM13", "SYM14", "SYM17", "SYM06"]
    )
    assert [sym for sym, _w in book["shorts"]] == sorted(
        ["SYM01", "SYM02", "SYM03", "SYM04", "SYM05"]
    )
    # hand ranks: the four surviving L names hold ranks 1..4
    ranks = {sym: int(r) for sym, r in book["diagnostics"]["ranks"]}
    assert sorted((ranks[s], s) for s in ("SYM12", "SYM13", "SYM14", "SYM17")) == [
        (1, "SYM12"),
        (2, "SYM13"),
        (3, "SYM14"),
        (4, "SYM17"),
    ]
    for sym, w in book["weights"]:
        assert abs(float(w)) == pytest.approx(0.1, rel=1e-12), sym


def test_book_builder_rank_semantics_are_direction_explicit() -> None:
    """Ascending sort longs the best ranks; descending longs the worst."""
    scores = {"A": 1.0, "B": 2.0, "C": 3.0, "D": 4.0, "E": 5.0, "F": 6.0,
              "G": 7.0, "H": 8.0, "I": 9.0, "J": 10.0, "K": 11.0, "L": 12.0}
    up = build_hysteresis_book(
        scores, prev_book=None, sort_ascending=True,
        leg_gross=0.5, cap_max=0.30, min_side_members=4, min_eligible=12,
    )
    up_ranks = {sym: int(r) for sym, r in up["ranks"]}
    assert up_ranks["A"] == 1 and up_ranks["L"] == 12
    assert sorted(s for s, _ in up["longs"]) == ["A", "B", "C", "D"]
    assert sorted(s for s, _ in up["shorts"]) == ["I", "J", "K", "L"]
    down = build_hysteresis_book(
        scores, prev_book=None, sort_ascending=False,
        leg_gross=0.5, cap_max=0.30, min_side_members=4, min_eligible=12,
    )
    down_ranks = {sym: int(r) for sym, r in down["ranks"]}
    assert down_ranks["L"] == 1 and down_ranks["A"] == 12  # direction flipped
    assert sorted(s for s, _ in down["longs"]) == ["I", "J", "K", "L"]
    assert sorted(s for s, _ in down["shorts"]) == ["A", "B", "C", "D"]
