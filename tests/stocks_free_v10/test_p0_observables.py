"""V10-P0 tests: timing/revision observable layer on synthetic fixtures.

All fixtures are SYNTHETIC and hand-computed; no test touches the real
panel, the network, or any credential (CLAUDE.md discipline). The PIT rules
tested here are the frozen definitions in p0_v10_observables.SCHEMA:

  own_norm    prior-only: eff' < eff AND first_avail' <= first_avail_E
  cohort_norm public-only: first_avail' <= first_avail_E
  revision    evidence stamp = last_avail; direction/magnitude from first/last
"""

from __future__ import annotations

import json

import pytest

from research.assets.stocks.p0_v10_observables import (
    MIN_HIST_COHORT,
    REASON_EXCLUDED_NON_NUMERIC,
    REASON_ZERO_BASE,
    REASON_ZERO_SCALE,
    compute_observables,
    scan_groups,
    write_jsonl,
)


def _mk_groups(specs):
    """specs: list of (e, f, eff, avails_and_values) where avails_and_values
    is a list of (avail, value) tuples; returns groups dict + sector map."""
    groups = {}
    sector = {}
    for e, f, eff, avs in specs:
        for av, v in avs:
            key = (e, f, eff)
            g = groups.get(key)
            if g is None:
                groups[key] = [av, v, av, v, 1, av]
            else:
                if av < g[0]:
                    g[0], g[1] = av, v
                if av > g[2]:
                    g[2], g[3] = av, v
                if av not in g[5]:
                    g[4] += 1
                    g[5] += "," + av
        sector[e] = "XLB"
    return groups, sector


def _q(year: int, month: str = "03", day: str = "31") -> str:
    return f"{year:04d}-{month}-{day}"


def _lag_avail(eff: str, lag: int) -> str:
    from datetime import date, timedelta

    return (date.fromisoformat(eff) + timedelta(days=lag)).isoformat()


# --------------------------------------------------------------------------- #
# own norm: prior-only, hand-computed
# --------------------------------------------------------------------------- #

def test_own_norm_prior_only_hand_computed():
    # Filer X, Q1 periods 2010..2015, first-filing lags 30,40,50,60,70 and a
    # very late 2015 filing (lag 200). Own norm at 2015 = median(30..70) = 50,
    # MAD = median(20,10,0,10,20) = 10 -> scale = 14.826 -> z = 150/14.826.
    lags = [30, 40, 50, 60, 70, 200]
    specs = [
        ("CIKX", "us-gaap:Assets", _q(2010 + i), [(_lag_avail(_q(2010 + i), l), 1000.0)])
        for i, l in enumerate(lags)
    ]
    groups, sector = _mk_groups(specs)
    timing, rev, census = compute_observables(groups, sector)
    first = timing[0]
    assert first["eff"] == _q(2010)
    # own norm at the FIRST period: no prior history -> null
    assert first["own_z"] is None
    assert first["own_reason"] == "INSUFFICIENT_HISTORY"
    last = timing[-1]
    assert last["eff"] == _q(2015)
    assert last["own_norm_days"] == pytest.approx(50.0)
    assert last["own_scale_days"] == pytest.approx(1.4826 * 10.0)
    assert last["own_z"] == pytest.approx((200 - 50) / (1.4826 * 10.0), abs=1e-5)
    assert last["own_reason"] is None
    assert last["first_lag_days"] == 200
    assert last["observable_available_at"] == _lag_avail(_q(2015), 200)


def test_own_norm_excludes_not_yet_public_prior_period():
    # Periods 2011..2015 with lags 30,40,50,60 and a not-yet-public 2015
    # period (lag 400) while the current 2016 period files fast (lag 5).
    # The 2015 entry is eff'-prior but first_avail' AFTER the 2016 decision
    # instant -> excluded. Norm at 2016 = median(30,40,50,60) = 45,
    # MAD = median(15,5,5,15) = 10 -> scale 14.826.
    lags = [30, 40, 50, 60, 400]
    years = [2011, 2012, 2013, 2014, 2015]
    specs = [
        ("CIKX", "us-gaap:Assets", _q(y), [(_lag_avail(_q(y), l), 1000.0)])
        for y, l in zip(years, lags)
    ]
    specs.append(
        ("CIKX", "us-gaap:Assets", _q(2016), [(_lag_avail(_q(2016), 5), 1000.0)])
    )
    groups, sector = _mk_groups(specs)
    timing, _rev, _c = compute_observables(groups, sector)
    last = timing[-1]
    assert last["eff"] == _q(2016)
    assert last["own_norm_days"] == pytest.approx(45.0)
    assert last["own_scale_days"] == pytest.approx(1.4826 * 10.0)
    assert last["first_lag_days"] == 5


def test_own_norm_zero_scale_is_null_not_zero():
    # Identical lags -> MAD 0 -> own_z must be null with ZERO_SCALE, never 0.
    specs = [
        ("CIKX", "us-gaap:Assets", _q(y), [(_lag_avail(_q(y), 40), 1000.0)])
        for y in range(2010, 2017)
    ]
    groups, sector = _mk_groups(specs)
    timing, _rev, _c = compute_observables(groups, sector)
    last = timing[-1]
    assert last["own_norm_days"] == pytest.approx(40.0)
    assert last["own_z"] is None
    assert last["own_reason"] == REASON_ZERO_SCALE


# --------------------------------------------------------------------------- #
# cohort norm: public-only, hand-computed
# --------------------------------------------------------------------------- #

def test_cohort_norm_public_only_boundary():
    # Filer A: 30 Q1 periods alternating lags 29/31 (so MAD != 0), plus one
    # later period filed at lag 30 but ONLY PUBLIC AFTER B's decision
    # instant. Filer B: single 2020 Q1 period at lag 10.
    # Cohort sample at B = the 30 public A entries (median 30, MAD 1) and
    # MUST NOT include the not-yet-public late entry.
    specs = []
    for i in range(30):
        y = 1990 + i
        lag = 29 if i % 2 == 0 else 31
        specs.append(("CIKA", "us-gaap:Assets", _q(y), [(_lag_avail(_q(y), lag), 1000.0)]))
    # late-period entry: same (sector, month) bucket as B, eff 2020-03-31,
    # filed at lag 400 -> first_avail (2021-05-05) is AFTER B's decision
    # instant (2020-04-10) so it MUST be excluded from the cohort sample.
    specs.append(("CIKA", "us-gaap:Assets", _q(2020), [(_lag_avail(_q(2020), 400), 1000.0)]))
    specs.append(("CIKB", "us-gaap:Assets", _q(2020), [(_lag_avail(_q(2020), 10), 1000.0)]))
    groups, sector = _mk_groups(specs)
    timing, _rev, census = compute_observables(groups, sector)
    brow = next(r for r in timing if r["e"] == "CIKB")
    assert brow["cohort_norm_days"] == pytest.approx(30.0)
    assert brow["cohort_scale_days"] == pytest.approx(1.4826, abs=1e-4)
    assert brow["cohort_z"] == pytest.approx((10 - 30) / 1.4826, abs=1e-4)
    assert brow["own_reason"] == "INSUFFICIENT_HISTORY"  # B has no own history
    assert census["timing"]["cohort_z_computable"] >= 1


def test_cohort_norm_min_history_gate():
    # Fewer than MIN_HIST_COHORT public samples -> cohort_z null
    # INSUFFICIENT_HISTORY (fail-closed, never a guessed norm).
    specs = [
        ("CIKA", "us-gaap:Assets", _q(y), [(_lag_avail(_q(y), 30), 1000.0)])
        for y in range(2010, 2010 + MIN_HIST_COHORT - 1)
    ]
    specs.append(("CIKB", "us-gaap:Assets", _q(2050), [(_lag_avail(_q(2050), 10), 1000.0)]))
    groups, sector = _mk_groups(specs)
    timing, _rev, _c = compute_observables(groups, sector)
    brow = next(r for r in timing if r["e"] == "CIKB")
    assert brow["cohort_z"] is None
    assert brow["cohort_reason"] == "INSUFFICIENT_HISTORY"


# --------------------------------------------------------------------------- #
# revision observables
# --------------------------------------------------------------------------- #

def test_revision_direction_magnitude_and_stamp():
    specs = [
        # depth 2, up-revision of +10% on base 100
        ("CIKX", "us-gaap:Assets", _q(2015),
         [(_q(2015, "05", "10"), 100.0), (_q(2015, "08", "20"), 110.0)]),
        # depth 2, down-revision on negative base -100 -> -110
        ("CIKX", "us-gaap:Liabilities", _q(2015),
         [(_q(2015, "05", "10"), -100.0), (_q(2015, "08", "20"), -110.0)]),
        # flat revision
        ("CIKX", "us-gaap:Cash", _q(2015),
         [(_q(2015, "05", "10"), 50.0), (_q(2015, "08", "20"), 50.0)]),
        # zero base -> magnitude null, direction kept
        ("CIKX", "us-gaap:Equity", _q(2015),
         [(_q(2015, "05", "10"), 0.0), (_q(2015, "08", "20"), 12.0)]),
        # depth 1 -> no revision row at all
        ("CIKX", "us-gaap:Inventory", _q(2015), [(_q(2015, "05", "10"), 7.0)]),
    ]
    groups, sector = _mk_groups(specs)
    timing, rev, census = compute_observables(groups, sector)
    assert len(rev) == 4
    by_f = {r["f"]: r for r in rev}
    a = by_f["us-gaap:Assets"]
    assert a["rev_dir"] == 1
    assert a["rev_mag"] == pytest.approx(0.10)
    assert a["observable_available_at"] == _q(2015, "08", "20")
    l = by_f["us-gaap:Liabilities"]
    assert l["rev_dir"] == -1
    assert l["rev_mag"] == pytest.approx(0.10)
    assert by_f["us-gaap:Cash"]["rev_dir"] == 0
    e = by_f["us-gaap:Equity"]
    assert e["rev_mag"] is None
    assert e["reason"] == REASON_ZERO_BASE
    assert e["rev_dir"] == 1
    assert census["revision"]["groups_depth_ge2"] == 4
    assert "us-gaap:Inventory" not in by_f


def test_revision_non_numeric_excluded_counted():
    specs = [
        ("CIKX", "us-gaap:Custom", _q(2015),
         [(_q(2015, "05", "10"), "n/a"), (_q(2015, "08", "20"), 5.0)]),
    ]
    groups, sector = _mk_groups(specs)
    timing, rev, census = compute_observables(groups, sector)
    assert len(rev) == 1
    assert rev[0]["reason"] == REASON_EXCLUDED_NON_NUMERIC
    assert rev[0]["rev_dir"] is None and rev[0]["rev_mag"] is None
    assert census["revision"]["excluded_non_numeric"] == 1


# --------------------------------------------------------------------------- #
# availability-lag mutation (the I/Q mutation applied at layer level)
# --------------------------------------------------------------------------- #

def test_availability_lag_mutation_shifts_stamp_and_lag_only():
    # Push a filing one day later: first_lag_days and the evidence stamp
    # shift by exactly that day; direction/magnitude must not change.
    specs = [
        ("CIKX", "us-gaap:Assets", _q(2015),
         [(_q(2015, "05", "10"), 100.0), (_q(2015, "08", "20"), 110.0)]),
    ]
    groups, sector = _mk_groups(specs)
    t1, rev1, _c1 = compute_observables(groups, sector)

    specs2 = [
        ("CIKX", "us-gaap:Assets", _q(2015),
         [(_q(2015, "05", "11"), 100.0), (_q(2015, "08", "20"), 110.0)]),
    ]
    groups2, sector2 = _mk_groups(specs2)
    t2, rev2, _c2 = compute_observables(groups2, sector2)

    assert rev2[0]["observable_available_at"] == rev1[0]["observable_available_at"]
    assert rev2[0]["rev_dir"] == rev1[0]["rev_dir"] == 1
    assert rev2[0]["rev_mag"] == rev1[0]["rev_mag"] == pytest.approx(0.10)
    # timing evidence stamp = first_avail: shifted by exactly one day,
    # first_lag_days 40 -> 41, everything else identical
    assert t1[0]["first_lag_days"] == 40
    assert t2[0]["first_lag_days"] == 41
    assert t1[0]["observable_available_at"] == _q(2015, "05", "10")
    assert t2[0]["observable_available_at"] == _q(2015, "05", "11")


def test_histories_dedup_multi_field_periods():
    # Timing is a property of the FILING: two fields sharing a filer-period
    # must count ONCE in both own and cohort norms. If fields multiplied,
    # the 2015 own norm would be median(30,30,...,200,200)=125 not 50, and
    # the cohort median below would shift toward the duplicated lag.
    specs = []
    for i, l in enumerate([30, 40, 50, 60, 70, 200]):
        y = 2010 + i
        specs.append(("CIKX", "us-gaap:Assets", _q(y), [(_lag_avail(_q(y), l), 1000.0)]))
        specs.append(("CIKX", "us-gaap:Equity", _q(y), [(_lag_avail(_q(y), l), 500.0)]))
    groups, sector = _mk_groups(specs)
    timing, _rev, _c = compute_observables(groups, sector)
    last = timing[-1]
    assert last["own_norm_days"] == pytest.approx(50.0)
    assert last["own_scale_days"] == pytest.approx(1.4826 * 10.0)


def test_cohort_norm_dedup_across_fields():
    # Filer A: 30 Q1 periods, lags alternating 29/31; a SECOND field repeats
    # only the odd (lag-31) periods. Cohort norm at B must remain the
    # deduplicated median 30 (duplicated fields would pull it to 31).
    specs = []
    for i in range(30):
        y = 1990 + i
        lag = 29 if i % 2 == 0 else 31
        specs.append(("CIKA", "us-gaap:Assets", _q(y), [(_lag_avail(_q(y), lag), 1000.0)]))
        if i % 2 == 1:
            specs.append(("CIKA", "us-gaap:Equity", _q(y), [(_lag_avail(_q(y), lag), 500.0)]))
    specs.append(("CIKB", "us-gaap:Assets", _q(2020), [(_lag_avail(_q(2020), 10), 1000.0)]))
    groups, sector = _mk_groups(specs)
    timing, _rev, _c = compute_observables(groups, sector)
    brow = next(r for r in timing if r["e"] == "CIKB")
    assert brow["cohort_norm_days"] == pytest.approx(30.0)
    assert brow["cohort_scale_days"] == pytest.approx(1.4826, abs=1e-4)


def test_negative_lag_counted_not_asserted():
    # avail before eff is a data-quality fact, never a crash: counted in the
    # census with a negative lag, fail-closed downstream by P2/P3 gates.
    specs = [
        ("CIKX", "us-gaap:Assets", _q(2015), [(_q(2015, "01", "10"), 100.0)]),
    ]
    groups, sector = _mk_groups(specs)
    timing, _rev, census = compute_observables(groups, sector)
    assert timing[0]["first_lag_days"] < 0
    assert census["timing"]["negative_lags"] == 1


# --------------------------------------------------------------------------- #
# scan_groups + write_jsonl determinism
# --------------------------------------------------------------------------- #

def test_scan_groups_roundtrip(tmp_path):
    lines = [
        {"e": "CIKX", "s": "XLB", "f": "us-gaap:Assets", "u": "USD",
         "v": 100.0, "eff": _q(2015), "avail": _q(2015, "05", "10")},
        {"e": "CIKX", "s": "XLB", "f": "us-gaap:Assets", "u": "USD",
         "v": 110.0, "eff": _q(2015), "avail": _q(2015, "08", "20")},
        {"e": "CIKY", "s": "XLV", "f": "us-gaap:Assets", "u": "USD",
         "v": 1.0, "eff": _q(2015), "avail": _q(2015, "06", "01")},
    ]
    p = tmp_path / "panel.jsonl"
    p.write_text("\n".join(json.dumps(x) for x in lines) + "\n")
    groups, sector, rows = scan_groups(str(p))
    assert rows == 3
    g = groups[("CIKX", "us-gaap:Assets", _q(2015))]
    assert g[0] == _q(2015, "05", "10") and g[1] == 100.0
    assert g[2] == _q(2015, "08", "20") and g[3] == 110.0
    assert g[4] == 2
    assert sector == {"CIKX": "XLB", "CIKY": "XLV"}


def test_write_jsonl_deterministic_and_hashed(tmp_path):
    rows = [{"a": 1, "b": "x"}, {"a": 2, "b": None}]
    h1 = write_jsonl(str(tmp_path / "r1.jsonl"), rows)
    h2 = write_jsonl(str(tmp_path / "r2.jsonl"), rows)
    assert h1 == h2
    import hashlib

    assert h1[1] == hashlib.sha256((tmp_path / "r1.jsonl").read_bytes()).hexdigest()
    assert h1[0] == 2
