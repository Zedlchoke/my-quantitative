"""Schedule-only feasibility on synthetic calendars: 24/yr, 4.80, envelope.

Deliverable 1d: transitions per year, one-way turnover sum per complete
calendar year, and the gross envelope — reported WITHOUT computing any PnL.
The real-calendar counterpart runs in ``test_dry_run_real.py``.
"""

from __future__ import annotations

import pytest

from research.assets.stocks.factory import CASH_SYMBOL
from research.stocks_free_v3.family_tom_settle import (
    BASE_GROSS,
    TOM_GROSS,
    TURNOVER_CEILING_TWO_WAY_PER_YEAR,
    build_schedule,
    complete_calendar_years,
    schedule_feasibility,
    year_turnover,
)
from tests.stocks_free_v3.family_tom_settle.conftest import (
    PADDED_YEAR_2021,
    weekday_sessions,
)

ARMS = ("A", "N", "C")


def test_padded_year_2021_is_complete():
    assert complete_calendar_years(PADDED_YEAR_2021) == (2021,)


def test_incomplete_years_are_not_claimed():
    calendar = weekday_sessions("2021-01-01", "2022-06-30")
    # starts exactly at 2021-01-01 (no padding before) -> 2021 is NOT complete;
    # 2022 is truncated -> not complete either
    assert complete_calendar_years(calendar) == ()


@pytest.mark.parametrize("arm", ARMS)
def test_exact_24_transitions_and_4_80_on_complete_synthetic_year(arm_configs, arm):
    schedule = build_schedule(arm_configs[arm], PADDED_YEAR_2021)
    stats = year_turnover(schedule, 2021)
    assert stats["transitions"] == 24
    assert stats["entries"] == 12 and stats["exits"] == 12
    assert abs(stats["one_way_turnover_sum"] - 4.80) < 1e-9
    # every transition moves exactly |delta gross| = 0.20 between the two books
    for fill in schedule.transitions:
        assert fill.turnover_one_way == pytest.approx(0.20, abs=1e-12)


@pytest.mark.parametrize("arm", ARMS)
def test_three_complete_synthetic_years(arm_configs, arm):
    calendar = weekday_sessions("2019-10-01", "2023-01-31")
    assert complete_calendar_years(calendar) == (2020, 2021, 2022)
    schedule = build_schedule(arm_configs[arm], calendar)
    for year in (2020, 2021, 2022):
        stats = year_turnover(schedule, year)
        assert stats["transitions"] == 24
        assert abs(stats["one_way_turnover_sum"] - 4.80) < 1e-9


def test_family_feasibility_report_synthetic(arm_configs):
    schedules = {arm: build_schedule(arm_configs[arm], PADDED_YEAR_2021) for arm in ARMS}
    feas = schedule_feasibility(schedules)
    assert feas["feasibility"] == "SCHEDULE_ONLY_NO_PNL"
    assert feas["anchor_control_disjoint"] is True
    assert feas["all_arms_within_gate"] is True
    assert feas["turnover_ceiling_two_way_per_year"] == TURNOVER_CEILING_TWO_WAY_PER_YEAR == 6.0
    for arm in ARMS:
        report = feas["arms"][arm]
        assert len(report["complete_years"]) == 1
        year = report["complete_years"][0]
        assert year["year"] == 2021
        assert year["transitions"] == 24 and year["transitions_ok"] is True
        assert year["turnover_ok"] is True
        assert year["turnover_two_way_per_year"] == pytest.approx(4.80, abs=1e-9)
        assert report["gross_envelope_ok"] is True
        assert report["gross_min"] == pytest.approx(BASE_GROSS, abs=1e-9)
        assert report["gross_max"] == pytest.approx(TOM_GROSS, abs=1e-9)
        # 2021 has 12 windows: 12 entries + 12 exits + establishment = 25 fills
        assert report["n_fills"] == report["n_transitions"] + 1
        # total windows over the whole padded coverage (includes the partial
        # Nov-2020 and Jan-2022 boundary windows)
        assert report["windows"] == report["n_transitions"] // 2


def test_gross_envelope_contains_only_the_two_frozen_books(arm_configs):
    for arm in ARMS:
        schedule = build_schedule(arm_configs[arm], PADDED_YEAR_2021)
        grosses = {
            round(sum(w for s, w in f.targets.items() if s != CASH_SYMBOL), 12)
            for f in schedule.fills
        }
        assert grosses == {round(BASE_GROSS, 12), round(TOM_GROSS, 12)}


def test_feasibility_computes_no_pnl(arm_configs):
    """The feasibility payload must carry only counts and schedule facts."""
    schedules = {arm: build_schedule(arm_configs[arm], PADDED_YEAR_2021) for arm in ARMS}
    payload = schedule_feasibility(schedules)

    forbidden = (
        "pnl", "equity", "expectancy", "profit_factor", "pf", "sharpe",
        "drawdown", "mdd", "return", "returns", "alpha",
    )

    def _walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                assert not any(tok in str(key).lower() for tok in forbidden), key
                _walk(value)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(payload)
