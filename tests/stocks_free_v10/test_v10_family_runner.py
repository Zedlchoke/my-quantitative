"""V10 I-phase tests: hand-computed fixtures for the frozen signal specs and
the two-key scored guard. SYNTHETIC ONLY — no real layer is touched."""

from __future__ import annotations

import pytest

from research.assets.stocks import v10_family_runner as r


# ---------------------------------------------------------------- timing

def test_sig_timing_basic_and_exposure_sign():
    rows = [("2020-01-10", "2019-12-31", 1.5, 0.5, 40)]
    # exposure = -own_z: late filer (own_z>0) -> negative exposure (short)
    assert r.sig_timing(rows, "2020-03-01", "own_z") == pytest.approx(-1.5)
    assert r.sig_timing(rows, "2020-03-01", "first_lag_days") == pytest.approx(-40)


def test_sig_timing_ties_average_and_null_skipped():
    rows = [
        ("2020-01-10", "2019-12-31", 1.5, 0.5, 40),
        ("2020-01-10", "2019-09-30", 0.5, None, 35),
        ("2020-01-09", "2019-08-31", 99.0, 99.0, 999),  # older stamp: ignored
    ]
    # ties on the largest stamp average: (-1.5 + -0.5)/2; null cohort_z in
    # the tied pair makes cohort_z mean over [0.5] only -> -0.5
    assert r.sig_timing(rows, "2020-03-01", "own_z") == pytest.approx(-1.0)
    assert r.sig_timing(rows, "2020-03-01", "cohort_z") == pytest.approx(-0.5)


def test_sig_timing_stale_and_future_and_all_null():
    rows = [
        ("2022-06-01", "2022-03-31", 1.0, 1.0, 10),   # future vs 2021 gate
        ("2017-12-01", "2017-11-30", 2.0, 2.0, 300),  # > 800 days stale
        ("2019-05-01", "2019-03-31", None, None, 50),  # null own/cohort
    ]
    assert r.sig_timing(rows, "2020-03-01", "own_z") is None
    assert r.sig_timing(rows, "2020-03-01", "cohort_z") is None
    assert r.sig_timing(rows, "2020-03-01", "first_lag_days") == pytest.approx(-50)


def test_sig_timing_availability_lag_mutation_boundary():
    # a stamp pushed later must NOT be visible to a gate at or before the
    # stamp and must be visible (age-correct) to a later gate
    rows = [("2020-05-11", "2020-03-31", 1.0, 1.0, 41)]
    assert r.sig_timing(rows, "2020-05-11", "own_z") is None   # same-day gate
    assert r.sig_timing(rows, "2020-05-10", "own_z") is None   # before stamp
    assert r.sig_timing(rows, "2020-05-12", "own_z") == pytest.approx(-1.0)


# -------------------------------------------------------------- revision

def _rev(f, eff, la, amend, inter, d, mag):
    return {"f": f, "eff": eff, "last_avail": la, "amend_count": amend,
            "inter_arrival_days": inter, "rev_dir": d, "rev_mag": mag}


def test_sig_breadth_floor_and_share():
    rows = [
        _rev("us-gaap:A", "2019-12-31", "2020-02-01", 1, 30, -1, 0.1),
        _rev("us-gaap:B", "2019-12-31", "2020-02-05", 1, 40, -1, 0.2),
        _rev("us-gaap:C", "2019-12-31", "2020-03-01", 1, 50, 1, 0.3),
        _rev("us-gaap:D", "2019-12-31", "2020-03-05", 1, 60, 0, None),
    ]
    assert r.sig_breadth(rows, "2020-06-01", -1) == pytest.approx(0.5)
    assert r.sig_breadth(rows, "2020-06-01", 1) == pytest.approx(0.25)
    # below the frozen |Q| >= 4 floor -> unpopulated
    assert r.sig_breadth(rows[:3], "2020-06-01", -1) is None


def test_sig_breadth_per_field_max_eff():
    rows = [
        _rev("us-gaap:A", "2018-12-31", "2019-02-01", 1, 30, -1, 0.1),
        _rev("us-gaap:A", "2019-12-31", "2020-02-01", 1, 30, 1, 0.1),  # newer eff wins
        _rev("us-gaap:B", "2019-12-31", "2020-02-05", 1, 40, 1, 0.2),
        _rev("us-gaap:C", "2019-12-31", "2020-03-01", 1, 50, 1, 0.3),
        _rev("us-gaap:D", "2019-12-31", "2020-03-05", 1, 60, 0, None),
    ]
    # field A keeps only eff 2019-12-31 (dir +1): up share = 3/4
    assert r.sig_breadth(rows, "2020-06-01", 1) == pytest.approx(0.75)


def test_sig_severity_median_and_clean_tie_mass():
    rows = [
        _rev("us-gaap:A", "2019-12-31", "2020-02-01", 1, 30, -1, 0.4),
        _rev("us-gaap:B", "2019-12-31", "2020-02-05", 1, 40, -1, 0.2),
        _rev("us-gaap:C", "2019-12-31", "2020-03-01", 1, 50, -1, None),
        _rev("us-gaap:D", "2019-12-31", "2020-03-05", 1, 60, 0, None),
    ]
    # down-revised non-null mags [0.4, 0.2] -> median 0.3
    assert r.sig_severity(rows, "2020-06-01") == pytest.approx(0.3)
    # no down-revised group at all -> the declared extreme-clean 0.0
    clean = [_rev("us-gaap:D", "2019-12-31", "2020-03-05", 1, 60, 0, None),
             _rev("us-gaap:E", "2019-12-31", "2020-03-06", 1, 60, 0, None),
             _rev("us-gaap:F", "2019-12-31", "2020-03-07", 1, 60, 0, None),
             _rev("us-gaap:G", "2019-12-31", "2020-03-08", 1, 60, 0, None)]
    assert r.sig_severity(clean, "2020-06-01") == 0.0


# ------------------------------------------------------------ guards

def test_scored_run_refused_without_two_keys():
    with pytest.raises(SystemExit):
        r.run_arm("SFV10-A4-H1-ANCHOR", {}, {}, {}, [], dry_run=False,
                  owner_go=None)
