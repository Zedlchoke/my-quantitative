"""Hand-computed defensive-mapping tests for family_a5.portfolio."""

import pytest

CAP = 0.35
TARGET = 0.10


def test_frozen_mapping_constants(a5):
    assert a5.portfolio.TARGET_VOL_ANNUAL == 0.10
    assert a5.portfolio.PER_ETF_CAP == 0.35


def test_gross_scalar_hand_computed(a5):
    p = a5.portfolio
    # g = min(1, 0.10/sigma): sigma=0.20 -> 0.5; sigma=0.05 -> 2 -> capped at 1.0
    assert p.gross_scalar(0.20) == pytest.approx(0.5)
    assert p.gross_scalar(0.05) == 1.0
    assert p.gross_scalar(0.40) == pytest.approx(0.25)
    # sigma <= 0 -> g = 1.0 (declared deterministic tie-break)
    assert p.gross_scalar(0.0) == 1.0
    assert p.gross_scalar(-0.1) == 1.0


def test_base_equal_weights_cap_binds_only_for_small_sets(a5):
    p = a5.portfolio
    # |E|=1: min(0.35, 1/1) = 0.35 (cap binds)
    assert p.base_equal_weights(["A"]) == {"A": 0.35}
    # |E|=2: min(0.35, 1/2) = 0.35 each (cap binds); sum 0.7, residual is cash
    assert p.base_equal_weights(["A", "B"]) == {"A": 0.35, "B": 0.35}
    # |E|=3: 1/3 < 0.35 -> cap slack, fully invested
    w3 = p.base_equal_weights(["A", "B", "C"])
    assert w3 == {"A": pytest.approx(1 / 3), "B": pytest.approx(1 / 3), "C": pytest.approx(1 / 3)}


def test_weights_hand_computed_n1(a5):
    # |E|=1, arena 0.20: g=0.5, w = 0.5*0.35 = 0.175, cash = 0.825
    w = a5.portfolio.defensive_target_weights(["A"], 0.20)
    assert w == {"A": pytest.approx(0.175), "CASH": pytest.approx(0.825)}


def test_weights_hand_computed_n2_residual_to_cash(a5):
    # |E|=2, arena 0.20: 0.175 each, gross 0.35; the uncapped residual is CASH,
    # never redistributed to other ETFs (spec edge case).
    w = a5.portfolio.defensive_target_weights(["A", "B"], 0.20)
    assert w["A"] == pytest.approx(0.175)
    assert w["B"] == pytest.approx(0.175)
    assert w["CASH"] == pytest.approx(0.65)


def test_weights_hand_computed_n3_half_gross(a5):
    # |E|=3, arena 0.20: g=0.5, w_i = 0.5 * 1/3 = 1/6 = 0.1666666..., cash 0.5
    w = a5.portfolio.defensive_target_weights(["A", "B", "C"], 0.20)
    for s in ("A", "B", "C"):
        assert w[s] == pytest.approx(1.0 / 6.0)
    assert w["CASH"] == pytest.approx(0.5)


def test_weights_full_book_low_vol(a5):
    # |E|=3, arena 0.05: g = min(1, 2) = 1 -> fully invested, cash ~ 0
    w = a5.portfolio.defensive_target_weights(["A", "B", "C"], 0.05)
    for s in ("A", "B", "C"):
        assert w[s] == pytest.approx(1.0 / 3.0)
    assert w["CASH"] == pytest.approx(0.0, abs=1e-12)


def test_weights_empty_eligible_is_all_cash(a5):
    assert a5.portfolio.defensive_target_weights([], 0.20) == {"CASH": 1.0}
    assert a5.portfolio.defensive_target_weights([], 0.0) == {"CASH": 1.0}


def test_structural_invariants_sweep(a5):
    # Long-only, single weight <= 0.35, gross <= 1.0, cash explicit and >= 0,
    # and book sums to exactly 1 — across set sizes and vol regimes.
    p = a5.portfolio
    universe = [f"S{i}" for i in range(15)]
    for n in range(0, 16):
        for arena in (0.0, 0.05, 0.10, 0.20, 0.50, 2.0):
            eligible = universe[:n]
            w = p.defensive_target_weights(eligible, arena)
            assert set(w) == set(eligible) | {"CASH"}
            for s, weight in w.items():
                assert weight >= -1e-12, (n, arena, s)
                if s != "CASH":
                    assert weight <= CAP + 1e-9, (n, arena, s)
            assert w["CASH"] >= -1e-12
            assert sum(w.values()) == pytest.approx(1.0, abs=1e-9)
            assert p.book_gross(w) <= 1.0 + 1e-9


def test_two_way_turnover_hand_computed(a5):
    p = a5.portfolio
    flat = {"A": 0.0, "B": 0.0, "CASH": 1.0}
    book = {"A": 0.30, "B": 0.20, "CASH": 0.50}
    # |0.30| + |0.20| = 0.50 two-way to build the book from flat
    assert p.two_way_turnover(flat, book) == pytest.approx(0.50)
    # 0.35-0.30 = 0.05 and 0.20-0.10 = 0.10 -> 0.15; cash move implied, not counted
    assert p.two_way_turnover(book, {"A": 0.35, "B": 0.10, "CASH": 0.55}) == pytest.approx(0.15)
    # force-flat liquidation of a fully invested 3x(1/3) book measures the gross: 1.0
    full = {"A": 1 / 3, "B": 1 / 3, "C": 1 / 3, "CASH": 0.0}
    assert p.two_way_turnover(full, {"A": 0.0, "B": 0.0, "C": 0.0, "CASH": 1.0}) == pytest.approx(1.0)
    # unchanged book -> zero turnover (sticky-state maintenance events)
    assert p.two_way_turnover(book, book) == 0.0
