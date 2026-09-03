"""Dry run + schedule-only feasibility on REAL staged data (S0 only).

Deliverable 4 (real-data half) and the real-calendar feasibility evidence.

Discipline, restated so it cannot be missed:

* the staged snapshot is READ-ONLY and lives outside this worktree; every
  pinned file is sha256-verified before parsing and every read is
  S0-bounded (2018-04-04..2025-07-31).  NO date >= 2025-08-01 (sealed S1)
  is read — enforced by the frozen ``S1Seal``/``S0WindowPolicy`` and
  asserted here;
* schedule-only feasibility runs over the full S0 span: counts and turnover
  only, no prices touched;
* the exact-arm dry run values ONE padded calendar year (Dec 2018 - Dec 2019)
  through the canonical ``factory.value_book`` accounting into a TEMPORARY
  pytest ledger that is deleted after the test; valuation numbers are
  consumed internally by the reconciliation assert and never asserted on,
  returned, printed, or persisted;

NO scored metric was computed or persisted: no PnL / expectancy / PF /
Sharpe / MDD table exists anywhere in this suite, on synthetic or real data.
"""

from __future__ import annotations

import datetime as dt

import pytest

from research.stocks_free_v3.authority import S0_END, S0_START, S1_END, S1_START
from research.stocks_free_v3.family_tom_settle import (
    build_schedule,
    build_schedule_from_windows,
    run_exact_arm_dry_run,
    schedules_equal,
    schedule_feasibility,
    year_turnover,
)
from research.stocks_free_v3.isolation import S1Seal

from tests.stocks_free_v3.family_tom_settle._staging import (
    load_s0_distributions,
    load_s0_raw_closes,
    make_reader,
    pinned_split_factors,
    s0_sessions,
    sessions_between,
    staging_available,
)

ARMS = ("A", "N", "C")

#: exact window-session counts over S0 (88 months: 5 sessions per month for
#: A and C, 3 for N — the anchor and mid-month control windows both span 5).
EXPECTED_WINDOW_SESSIONS_S0 = {"A": 440, "N": 264, "C": 440}

#: exact transition counts over the padded 2019 dry-run coverage
#: (2018-12-03..2019-12-31): 24 in-year transitions plus the boundary fills
#: of the December 2018 window (arm A entry 2018-12-27 + exit 2019-01-04;
#: arm N exit 2018-12-07 (2018-12-05 was the national-mourning closure);
#: arm C entry 2018-12-13 + exit 2018-12-20).
EXPECTED_TRANSITIONS_PADDED_2019 = {"A": 26, "N": 25, "C": 26}

pytestmark = pytest.mark.skipif(
    not staging_available(),
    reason="read-only staged snapshot not present; synthetic coverage remains",
)


@pytest.fixture(scope="module")
def reader():
    return make_reader()


@pytest.fixture(scope="module")
def real_closes(reader):
    return load_s0_raw_closes(reader)


@pytest.fixture(scope="module")
def real_distributions():
    return load_s0_distributions()


# --------------------------------------------------------------------------
# schedule-only feasibility over the full S0 span (no prices touched)
# --------------------------------------------------------------------------
def test_s0_sessions_are_inside_s0_and_never_sealed():
    sessions = s0_sessions()
    assert sessions[0] == S0_START.isoformat()
    assert sessions[-1] <= S0_END.isoformat()
    seal = S1Seal(S1_START, S1_END)
    for s in sessions:
        assert not seal.denies_date(dt.date.fromisoformat(s))


def test_full_s0_schedule_only_feasibility_all_arms():
    sessions = s0_sessions()
    schedules = {}
    for arm in ARMS:
        cfg_arm = _config(arm)
        s1 = build_schedule(cfg_arm, sessions)
        s2 = build_schedule_from_windows(cfg_arm, sessions)
        assert schedules_equal(s1, s2), arm      # double generation on real calendar
        schedules[arm] = s1
    feas = schedule_feasibility(schedules)
    assert feas["all_arms_within_gate"] is True
    assert feas["anchor_control_disjoint"] is True
    for arm in ARMS:
        report = feas["arms"][arm]
        years = report["complete_years"]
        assert [y["year"] for y in years] == [2019, 2020, 2021, 2022, 2023, 2024]
        for year in years:
            assert year["transitions"] == 24, (arm, year["year"])
            assert year["turnover_ok"] is True
            assert year["entries"] == 12 and year["exits"] == 12
            assert year["turnover_two_way_per_year"] == pytest.approx(4.80, abs=1e-9)
        assert report["gross_envelope_ok"] is True
        assert report["gross_max"] <= 0.50 + 1e-9      # inside the 6.0 ceiling
        # exact window-session counts on the real S0 calendar
        assert report["window_sessions"] == EXPECTED_WINDOW_SESSIONS_S0[arm]
    # the risk-matched rule digest is identical across arms (shared frozen rule)
    assert len({report["config_digest"] for report in feas["arms"].values()}) == 3


# --------------------------------------------------------------------------
# exact-arm dry run on real staged data: ONE padded year, temp ledger
# --------------------------------------------------------------------------
@pytest.mark.parametrize("arm", ARMS)
def test_exact_arm_dry_run_real_2019(arm, real_closes, real_distributions, tmp_path):
    cfg = _config(arm)
    sessions = sessions_between("2018-12-01", "2019-12-31")
    assert sessions[0] == "2018-12-03" and sessions[-1] == "2019-12-31"

    ledger_path = tmp_path / f"dryrun_{arm}.json"
    ledger = _ledger(str(ledger_path))
    report = run_exact_arm_dry_run(
        cfg, sessions,
        raw_close=real_closes,
        distributions=real_distributions,
        split_factors=pinned_split_factors(),
        cost_bps=10.0,
        ledger=ledger,
        trial_key=f"DRYRUN::{cfg.arm_id}::REAL_S0_2019::SCHEDULE_VALUATION_ONLY",
    )
    assert report.double_generation_identical is True
    assert report.establishment_fill_session == sessions[0]
    assert report.n_transitions == EXPECTED_TRANSITIONS_PADDED_2019[arm]
    schedule = build_schedule(cfg, sessions)
    stats = year_turnover(schedule, 2019)
    assert stats["transitions"] == 24
    assert stats["one_way_turnover_sum"] == pytest.approx(4.80, abs=1e-9)
    assert report.valuation["attribution_reconciled"] is True
    assert report.valuation["cost_charged_once"] is True
    assert report.valuation["n_fills_costed"] == report.n_fills
    assert report.valuation["n_held_positions"] == 11
    assert report.ledger["published"] is True
    assert report.ledger["replay_zero_delta"] is True

    ledger.save()                     # written ONLY under pytest's tmp_path
    assert ledger_path.exists()
    ledger_path.unlink()
    assert not ledger_path.exists()   # the temporary ledger is deleted after


def test_real_reads_never_touch_s1(real_closes, real_distributions):
    """Every observation the dry run could touch is strictly inside S0."""
    seal = S1Seal(S1_START, S1_END)
    for symbol, series in real_closes.items():
        assert series, symbol
        latest = max(series)
        assert latest <= S0_END.isoformat()
        assert not seal.denies_date(dt.date.fromisoformat(latest))
    for symbol, dists in real_distributions.items():
        if dists:
            assert max(dists) <= S0_END.isoformat(), symbol


def _config(arm):
    from research.stocks_free_v3.family_tom_settle import build_arm_configs
    return build_arm_configs()[arm]


def _ledger(path: str):
    from research.assets.stocks.factory import GatedTrialLedger
    return GatedTrialLedger(path)
