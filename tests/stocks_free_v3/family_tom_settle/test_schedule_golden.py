"""Hand-computed goldens: window sessions and transition fills for arms A/N/C.

Deliverable 3: synthetic month pair with holidays (Jan + Feb 2021, 19 regular
sessions each), every window session and every scheduled fill HAND-COMPUTED
and asserted exactly.  Also pins the frozen books (11 equal legs + explicit
CASH residual) and the A/C window disjointness.
"""

from __future__ import annotations

import math

import pytest

from research.assets.stocks.factory import CASH_SYMBOL
from research.stocks_free_v3.authority import COHORT_SYMBOLS
from research.stocks_free_v3.family_tom_settle import (
    BASE_GROSS,
    BOOK_BASE,
    BOOK_TOM,
    TOM_GROSS,
    anchor_control_disjoint,
    assert_anchor_control_disjoint,
    base_targets,
    build_schedule,
    is_window_session,
    month_ordinals,
    schedules_equal,
    tom_targets,
)
from tests.stocks_free_v3.family_tom_settle.conftest import (
    FEB_2021_SESSIONS,
    HAND_SESSIONS,
    JAN_2021_SESSIONS,
)

TOL = 1e-12


# --------------------------------------------------------------------------
# window membership (hand-computed ordinals)
# --------------------------------------------------------------------------
def test_window_sessions_arm_a_hand_computed(arm_configs, hand_sessions):
    ords = {r.session: r for r in month_ordinals(hand_sessions)}
    rule = arm_configs["A"].window
    # Jan: 19 sessions -> tail = ordinals 17,18,19 = 01-27,01-28,01-29;
    # head = ordinals 1,2 = 01-04,01-05 (the month-start leg of the December
    # 2020 window).  Feb: tail = 02-24,02-25,02-26; head = 02-01,02-02.
    expected = {
        "2021-01-04", "2021-01-05",
        "2021-01-27", "2021-01-28", "2021-01-29",
        "2021-02-01", "2021-02-02",
        "2021-02-24", "2021-02-25", "2021-02-26",
    }
    got = {s for s in hand_sessions if is_window_session(rule, ords[s])}
    assert got == expected


def test_window_sessions_arm_n_hand_computed(arm_configs, hand_sessions):
    ords = {r.session: r for r in month_ordinals(hand_sessions)}
    rule = arm_configs["N"].window
    expected = {
        "2021-01-04", "2021-01-05", "2021-01-06",   # Jan ordinals 1-3
        "2021-02-01", "2021-02-02", "2021-02-03",   # Feb ordinals 1-3
    }
    got = {s for s in hand_sessions if is_window_session(rule, ords[s])}
    assert got == expected


def test_window_sessions_arm_c_hand_computed(arm_configs, hand_sessions):
    ords = {r.session: r for r in month_ordinals(hand_sessions)}
    rule = arm_configs["C"].window
    # Ordinals 8-12, counted on SESSIONS so the holidays (01-18, 02-15) shift
    # the dates: Jan -> 01-13,01-14,01-15,01-19,01-20; Feb -> 02-10,02-11,
    # 02-12,02-16,02-17.
    expected = {
        "2021-01-13", "2021-01-14", "2021-01-15", "2021-01-19", "2021-01-20",
        "2021-02-10", "2021-02-11", "2021-02-12", "2021-02-16", "2021-02-17",
    }
    got = {s for s in hand_sessions if is_window_session(rule, ords[s])}
    assert got == expected


# --------------------------------------------------------------------------
# hand-computed fill schedules (exact structure)
# --------------------------------------------------------------------------
def _fill_rows(schedule):
    return [
        (f.fill_session, f.book, f.establishment, f.decision_session,
         round(f.turnover_one_way, 12))
        for f in schedule.fills
    ]


def test_golden_schedule_arm_a(arm_configs, hand_sessions):
    schedule = build_schedule(arm_configs["A"], hand_sessions)
    assert _fill_rows(schedule) == [
        # establishment at the coverage start: 01-04 is a window session of
        # the December 2020 window (first 2 of January) -> TOM, gross 0.50
        # from the implicit all-CASH book.
        ("2021-01-04", BOOK_TOM, True, None, 0.5),
        # window exit: first non-window session 01-06, decided at 01-05 close.
        ("2021-01-06", BOOK_BASE, False, "2021-01-05", 0.2),
        # January window entry at the first of the last-3 sessions,
        # decided at 01-26 close.
        ("2021-01-27", BOOK_TOM, False, "2021-01-26", 0.2),
        # exit at the first session after the first-2-of-February leg.
        ("2021-02-03", BOOK_BASE, False, "2021-02-02", 0.2),
        # February window entry (coverage ends INSIDE the window: 02-26 is a
        # window session, so the schedule has NO exit fill after 02-24 — the
        # book stays TOM through the last covered session, no compensation
        # trade).
        ("2021-02-24", BOOK_TOM, False, "2021-02-23", 0.2),
    ]
    assert schedule.window_sessions == (
        "2021-01-04", "2021-01-05", "2021-01-27", "2021-01-28", "2021-01-29",
        "2021-02-01", "2021-02-02", "2021-02-24", "2021-02-25", "2021-02-26",
    )
    assert not schedules_equal(schedule, build_schedule(arm_configs["N"], hand_sessions))


def test_golden_schedule_arm_n(arm_configs, hand_sessions):
    schedule = build_schedule(arm_configs["N"], hand_sessions)
    assert _fill_rows(schedule) == [
        ("2021-01-04", BOOK_TOM, True, None, 0.5),     # establishment inside Jan window
        ("2021-01-07", BOOK_BASE, False, "2021-01-06", 0.2),  # exit after ordinal 3
        ("2021-02-01", BOOK_TOM, False, "2021-01-29", 0.2),   # February entry
        ("2021-02-04", BOOK_BASE, False, "2021-02-03", 0.2),  # February exit
    ]
    assert schedule.window_sessions == (
        "2021-01-04", "2021-01-05", "2021-01-06",
        "2021-02-01", "2021-02-02", "2021-02-03",
    )


def test_golden_schedule_arm_c(arm_configs, hand_sessions):
    schedule = build_schedule(arm_configs["C"], hand_sessions)
    assert _fill_rows(schedule) == [
        # establishment at BASE: 01-04 is ordinal 1, far from ordinals 8-12
        ("2021-01-04", BOOK_BASE, True, None, 0.3),
        ("2021-01-13", BOOK_TOM, False, "2021-01-12", 0.2),   # Jan ordinal 8
        ("2021-01-21", BOOK_BASE, False, "2021-01-20", 0.2),  # Jan ordinal 13
        ("2021-02-10", BOOK_TOM, False, "2021-02-09", 0.2),   # Feb ordinal 8
        ("2021-02-18", BOOK_BASE, False, "2021-02-17", 0.2),  # Feb ordinal 13
    ]
    assert schedule.window_sessions == (
        "2021-01-13", "2021-01-14", "2021-01-15", "2021-01-19", "2021-01-20",
        "2021-02-10", "2021-02-11", "2021-02-12", "2021-02-16", "2021-02-17",
    )


# --------------------------------------------------------------------------
# frozen books: 11 equal legs + explicit CASH residual, exact values
# --------------------------------------------------------------------------
@pytest.mark.parametrize("arm_key,gross", [("A", TOM_GROSS), ("N", TOM_GROSS), ("C", TOM_GROSS)])
def test_tom_book_legs_and_cash(arm_configs, arm_key, gross):
    targets = tom_targets(arm_configs[arm_key])
    assert list(targets) == list(COHORT_SYMBOLS) + [CASH_SYMBOL]
    for s in COHORT_SYMBOLS:
        assert targets[s] == pytest.approx(gross / 11, abs=TOL)
    assert targets[CASH_SYMBOL] == pytest.approx(1.0 - gross, abs=TOL)
    assert math.fsum(targets.values()) == pytest.approx(1.0, abs=TOL)


def test_base_book_legs_and_cash(arm_configs):
    targets = base_targets(arm_configs["A"])
    for s in COHORT_SYMBOLS:
        assert targets[s] == pytest.approx(BASE_GROSS / 11, abs=TOL)
    assert targets[CASH_SYMBOL] == pytest.approx(1.0 - BASE_GROSS, abs=TOL)
    assert math.fsum(targets.values()) == pytest.approx(1.0, abs=TOL)


def test_every_fill_carries_explicit_cash_residual(arm_configs, hand_sessions):
    for key in ("A", "N", "C"):
        for fill in build_schedule(arm_configs[key], hand_sessions).fills:
            assert CASH_SYMBOL in fill.targets
            expected = 1.0 - (TOM_GROSS if fill.book == BOOK_TOM else BASE_GROSS)
            assert fill.targets[CASH_SYMBOL] == pytest.approx(expected, abs=TOL)


# --------------------------------------------------------------------------
# anchor/control disjointness (family-level frozen property)
# --------------------------------------------------------------------------
def test_anchor_control_disjoint_for_realistic_month_lengths():
    for n in (19, 20, 21, 22, 23):   # the observed real US month lengths
        assert anchor_control_disjoint(n)


def test_anchor_control_disjoint_boundary_lengths():
    assert not anchor_control_disjoint(14)   # 12 is a month-END ordinal here
    assert anchor_control_disjoint(15)       # first length where they cannot touch


def test_anchor_control_disjoint_asserted_on_hand_calendar(arm_configs, hand_sessions):
    # must not raise; A and C share no session on the hand calendar
    assert_anchor_control_disjoint(hand_sessions)
    a = build_schedule(arm_configs["A"], hand_sessions).window_sessions
    c = build_schedule(arm_configs["C"], hand_sessions).window_sessions
    assert not (set(a) & set(c))
