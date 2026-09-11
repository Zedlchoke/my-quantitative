"""FOREX-NG1 I-phase runner tests (task forex-ng1-i-runners).

Every fixture is SMALL, SYNTHETIC and HAND-COMPUTED under /tmp or in
memory: no pinned series is consumed, no scored mode is enabled, no real
PnL is computed anywhere in this file (accounting outcomes are refused
and the refusal itself is the tested behavior).

Coverage (dispatch contract):

1. one-event lag correctness (PIT entry clock; as-of vintage reads);
2. cost charged exactly ONCE per fill (2 fills per round trip);
3. fold force-flat at the frozen fold boundaries;
4. DST-correct 16:00-NY decision instants;
5. seeded placebo determinism (frozen RNG);
6. control arm distinct from the anchor (different book);
7. the dry-run leak scanner detects a planted leak field;
8. R1-R6 evaluator: one pass + one fail case per rule.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, timedelta

import pytest

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.forex_ng1.d2 import events as E           # noqa: E402
from research.assets.forex_ng1.d2.series import VintagedSeries # noqa: E402
from research.assets.forex_ng1.spot_series import (            # noqa: E402
    ny_decision_instant_utc,
)
from research.assets.forex_ng1.run import accounting as K      # noqa: E402
from research.assets.forex_ng1.run import arms as A            # noqa: E402
from research.assets.forex_ng1.run import config as C          # noqa: E402
from research.assets.forex_ng1.run import evaluator as R       # noqa: E402
from research.assets.forex_ng1.run import scanner as S         # noqa: E402
from research.assets.forex_ng1.run.data import RunEnv          # noqa: E402
from research.assets.forex_ng1.run.dgs10 import Dgs10LevelSeries

# --------------------------------------------------------------------------- #
# hand-computed fixture: 15 weekday spot bars (2021-06-14..2021-07-02),
# one US-anchored month, CA opening follower; CA/US/GB vintaged legs
# --------------------------------------------------------------------------- #

GRID_DAYS = [date(2021, 6, d) for d in (14, 15, 16, 17, 18, 21, 22, 23,
                                        24, 25, 28, 29, 30)] + \
            [date(2021, 7, 1), date(2021, 7, 2)]
GRID_INDEX = {d: i for i, d in enumerate(GRID_DAYS)}


def _ev(economy, ref, pub, operative, value, exact_utc=None):
    rec = {
        "economy": economy,
        "reference_period": ref,
        "publication_date": pub,
        "time_precision": ("CALENDAR_TIME_UTC_EXACT" if exact_utc
                           else "DATE_ONLY_CONSERVATIVE_END_OF_DAY"),
        "publication_instant_utc": exact_utc or f"{pub}T23:59:59Z",
        "operative_vintaged_available_from": operative,
        "vintaged_first_value": value,
        "is_first_release_of_period": True,
    }
    return rec


def fixture_events():
    """US-anchored month 2021-06; CA is the provably-unique opening
    follower (CA exact 06-16 12:30Z strictly precedes GB 06-23)."""
    return [
        _ev("US", "2021-05", "2021-06-10", "2021-06-10", 270.0),
        _ev("CA", "2021-05", "2021-06-16", "2021-06-23", 100.2,
            exact_utc="2021-06-16T12:30:00Z"),
        _ev("GB", "2021-05", "2021-06-23", "2021-07-10", 120.0),
    ]


def _row(obs, rs, re, value):
    return {"obs": f"{obs}-01", "rs": date.fromisoformat(rs),
            "re": date.fromisoformat(re), "value": value}


def ca_series():
    """Monthly CA leg, hand-computed s1 at entry 2021-06-24:
    I(2021-04)=100, I(2020-05) revised to 110 on 2021-06-23 (visible at
    the 06-24 decision, NOT at the 06-16 publication), I(2020-04)=100,
    I_print=100.2 -> I_hat = 100*110/100 = 110 ->
    s1 = 100*(100.2/110 - 1) = -8.909090... pp (below -0.10 -> fires)."""
    rows = [
        _row("2021-04", "2000-01-01", "2099-12-31", 100.0),
        _row("2020-05", "2000-01-01", "2021-06-22", 100.0),
        _row("2020-05", "2021-06-23", "2099-12-31", 110.0),
        _row("2020-04", "2000-01-01", "2099-12-31", 100.0),
        _row("2021-05", "2021-06-23", "2099-12-31", 100.2),
    ]
    return VintagedSeries(series_id="CANCPIALLMINMEI", rows=rows)


def us_series():
    """US leg: I(2021-04)=I(2020-05)=I(2020-04)=100, print=100.3 ->
    pi_bar=0, I_hat=100, s2=+0.3pp (>= +0.15 -> fires long USD)."""
    rows = [
        _row("2021-04", "2000-01-01", "2099-12-31", 100.0),
        _row("2020-05", "2000-01-01", "2099-12-31", 100.0),
        _row("2020-04", "2000-01-01", "2099-12-31", 100.0),
        _row("2021-05", "2021-06-11", "2099-12-31", 100.3),
    ]
    return VintagedSeries(series_id="CPIAUCSL", rows=rows)


def gb_series():
    rows = [_row("2021-04", "2000-01-01", "2099-12-31", 100.0),
            _row("2020-05", "2000-01-01", "2099-12-31", 100.0),
            _row("2020-04", "2000-01-01", "2099-12-31", 100.0),
            _row("2021-05", "2021-07-10", "2099-12-31", 100.1)]
    return VintagedSeries(series_id="GBRCPIALLMINMEI", rows=rows)


def fixture_env():
    events = fixture_events()
    return RunEnv(
        census={}, events=events, order_state=E.order_state(events),
        grid=list(GRID_DAYS), grid_index=dict(GRID_INDEX),
        series_by_eco={"CA": ca_series(), "US": us_series(),
                       "GB": gb_series()},
        dgs10_rows=[], spot_sha256={}, provenance={})


# --------------------------------------------------------------------------- #
# 1. one-event lag correctness
# --------------------------------------------------------------------------- #

def test_a5_one_event_lag_entry_and_asof_read():
    env = fixture_env()
    book = A.build_a5p1_anchor(env)
    # order state: one US-anchored month, CA unique opener (hand-computed)
    assert env.order_state["counts"]["us_anchored_months"] == 1
    assert env.order_state["counts"]["unique_of_months"] == 1
    recs = book["decisions"]
    assert len(recs) == 1
    r = recs[0]
    # CA operative 2021-06-23 + US pub 2021-06-10 -> bound 06-23; the
    # FIRST grid day strictly after is 06-24 (a same-day 16:00-NY
    # decision can never see an EOD availability bound of that day).
    assert r["entry_grid_day"] == "2021-06-24"
    assert r["event"]["economy"] == "CA"
    # s1 read AS-OF entry: the 06-23 revision (110) is in force ->
    # s1 = -8.9090909...pp -> ssign -1 -> CA funded SHORT -> USDCAD +1
    assert r["direction"] == +1
    assert r["pair"] == "USDCAD"
    # H=5 grid days: idx(06-24)=8 -> exit idx 13 = 2021-07-01
    assert r["exit_grid_day"] == "2021-07-01"
    assert r["exit_reason"] == "horizon"
    assert r["fold"] == 2
    assert "s1(-8.909091pp)" in r["signal_source"]


def test_a5_same_day_decision_never_sees_print():
    # 16:00-NY on 2021-06-23 (EDT) = 20:00Z < 23:59:59Z EOD bound
    assert ny_decision_instant_utc(date(2021, 6, 23)).strftime(
        "%Y-%m-%dT%H:%M:%SZ") == "2021-06-23T20:00:00Z"
    assert E.first_grid_day_strictly_after(
        date(2021, 6, 23), GRID_INDEX, date(2021, 7, 2)) == date(2021, 6, 24)


def test_a4_us_event_fires_four_pair_decisions():
    env = fixture_env()
    book = A.build_a4p2_anchor(env)
    us_recs = [r for r in book["decisions"]
               if r["event"]["economy"] == "US"]
    # US print: operative 06-10 -> entry = first grid day after = 06-14
    # s2 = +0.3pp -> long USD in all four pairs:
    # GBPUSD/AUDUSD/NZDUSD short (-1), USDCAD long (+1)
    assert {r["entry_grid_day"] for r in us_recs} == {"2021-06-14"}
    signs = {r["pair"]: r["direction"] for r in us_recs}
    assert signs == {"GBPUSD": -1, "USDCAD": 1,
                     "AUDUSD": -1, "NZDUSD": -1}
    # exit: idx(06-14)=0 -> idx 5 = 2021-06-21
    assert {r["exit_grid_day"] for r in us_recs} == {"2021-06-21"}


def test_neigh_smooth2_two_window_prior():
    vs = VintagedSeries(series_id="T", rows=[
        _row("2021-04", "2000-01-01", "2099-12-31", 100.0),
        _row("2021-03", "2000-01-01", "2099-12-31", 100.0),
        _row("2020-05", "2000-01-01", "2099-12-31", 100.0),
        _row("2020-04", "2000-01-01", "2099-12-31", 100.0),
        _row("2020-03", "2000-01-01", "2099-12-31", 100.0),
        _row("2020-02", "2000-01-01", "2099-12-31", 100.0),
    ])
    # pi1 = 100/100-1 = 0; pi2 = 100/100-1 = 0 -> pi_bar2 = 0,
    # I_hat = 100 -> s2' = 100*(100.15/100 - 1) = +0.15 (>= thr)
    s, detail = A.s2_smooth2(vs, "2021-05", 100.15,
                             date(2021, 6, 24))
    assert s == pytest.approx(0.15)
    assert detail["pi_bar2"] == pytest.approx(0.0)


# --------------------------------------------------------------------------- #
# 2. cost charged exactly ONCE per fill
# --------------------------------------------------------------------------- #

def test_cost_once_per_fill():
    # per-fill cost = notional x 1.5bps x tier; NOTIONAL 10000:
    # tier 1.0 -> 1.50, 1.5 -> 2.25, 2.0 -> 3.00 USD per fill
    costs = K.round_trip_costs(10000.0)
    assert costs["1.0"]["fills"] == 2
    assert costs["2.0"]["cost_per_fill_usd"] == pytest.approx(3.00)
    assert costs["1.5"]["cost_per_fill_usd"] == pytest.approx(2.25)
    assert costs["1.0"]["cost_per_fill_usd"] == pytest.approx(1.50)
    # exactly two charges per round trip (once per fill, never re-scaled)
    assert costs["2.0"]["cost_round_trip_usd"] == pytest.approx(6.00)
    assert costs["2.0"]["cost_round_trip_usd"] == pytest.approx(
        2 * costs["2.0"]["cost_per_fill_usd"])
    # frozen PnL identity on a hand-computed synthetic fill (no real
    # data; scored aggregation stays refused below)
    assert K.price_pnl_usd(+1, 10000.0, 1.00, 1.01) == pytest.approx(100.0)
    assert K.price_pnl_usd(-1, 10000.0, 1.00, 1.01) == pytest.approx(-100.0)
    # net at tier 2.0 for that synthetic fill: 100 - 2x3.00 = 94.00
    assert 100.0 - costs["2.0"]["cost_round_trip_usd"] == pytest.approx(94.0)


def test_outcome_computation_refused_in_this_lane():
    with pytest.raises(K.AccountingRefused):
        K.compute_outcomes([], {}, scored=False)
    with pytest.raises(K.AccountingRefused):
        # scored=True alone is NOT sufficient: the spot channel is not
        # AUTHORIZED (and this lane never passes scored=True anyway)
        K.compute_outcomes([], {}, scored=True, spot_authority=None)


def test_tier_outside_ladder_refused():
    with pytest.raises(K.AccountingRefused):
        K.bps_cost(10000.0, 2.5)


# --------------------------------------------------------------------------- #
# 3. fold force-flat
# --------------------------------------------------------------------------- #

def _grid_2020():
    days, d = [], date(2020, 6, 22)
    while d <= date(2020, 7, 10):
        if d.weekday() < 5:
            days.append(d)
        d += timedelta(days=1)
    return days


def test_fold_force_flat_at_boundary():
    grid = _grid_2020()
    gi = {d: i for i, d in enumerate(grid)}
    # entry Mon 2020-06-29 is in fold 1 (ends Tue 06-30): H=5 would be
    # 07-06 (fold 2) -> force-flat exit at the fold-1 last grid day
    exit_day, reason, fold = A.exit_plan(date(2020, 6, 29), grid, gi)
    assert (exit_day, reason, fold) == (date(2020, 6, 30),
                                        "fold_force_flat", 1)
    # entry Wed 2020-06-24: H=5 -> 07-01 in fold 2 -> forced at 06-30
    exit_day, reason, fold = A.exit_plan(date(2020, 6, 24), grid, gi)
    assert (exit_day, reason, fold) == (date(2020, 6, 30),
                                        "fold_force_flat", 1)
    # entry Wed 2020-07-01 (fold 2): horizon 07-08, well inside fold 2
    exit_day, reason, fold = A.exit_plan(date(2020, 7, 1), grid, gi)
    assert (exit_day, reason, fold) == (date(2020, 7, 8), "horizon", 2)


def test_fold_of_day_boundaries():
    assert C.fold_of_day(date(2020, 6, 30)) == 1
    assert C.fold_of_day(date(2020, 7, 1)) == 2
    assert C.fold_of_day(date(2022, 10, 31)) == 2
    assert C.fold_of_day(date(2022, 11, 1)) == 3
    with pytest.raises(ValueError):
        C.fold_of_day(date(2026, 1, 1))


# --------------------------------------------------------------------------- #
# 4. DST-correct 16:00-NY decision instants
# --------------------------------------------------------------------------- #

def test_dst_1600ny_instants():
    def iso(d):
        return ny_decision_instant_utc(d).strftime("%Y-%m-%dT%H:%M:%SZ")
    # EDT (UTC-4): 16:00 NY = 20:00Z
    assert iso(date(2021, 6, 24)) == "2021-06-24T20:00:00Z"
    assert iso(date(2021, 3, 10)) == "2021-03-10T21:00:00Z"  # EST eve of DST
    # 2021 DST starts Sun 03-14, ends Sun 11-07
    assert iso(date(2021, 3, 12)) == "2021-03-12T21:00:00Z"  # EST
    assert iso(date(2021, 3, 15)) == "2021-03-15T20:00:00Z"  # EDT
    assert iso(date(2021, 11, 5)) == "2021-11-05T20:00:00Z"  # EDT
    assert iso(date(2021, 11, 8)) == "2021-11-08T21:00:00Z"  # EST
    # across the fall-back weekend the grid instant jumps +1h
    assert (ny_decision_instant_utc(date(2021, 11, 8))
            - ny_decision_instant_utc(date(2021, 11, 5))
            ).total_seconds() == 3 * 86400 + 3600


# --------------------------------------------------------------------------- #
# 5. seeded placebo determinism
# --------------------------------------------------------------------------- #

def _ordshuf_env():
    """Anchored month with a 4-event pool of threshold-passers (GB/CA/
    NZ/AU distinct publication days) + a small anchor book."""
    events = [
        _ev("US", "2021-05", "2021-06-10", "2021-06-10", 270.0),
        _ev("CA", "2021-05", "2021-06-16", "2021-06-23", 100.2,
            exact_utc="2021-06-16T12:30:00Z"),
        _ev("GB", "2021-05", "2021-06-23", "2021-06-23", 100.5),
        _ev("NZ", "2021-05", "2021-06-24", "2021-06-24", 100.5),
        _ev("AU", "2021-05", "2021-06-25", "2021-06-25", 100.5),
    ]
    lags = ("2021-04", "2020-05", "2020-04")
    series = {}
    for eco in ("US", "CA"):
        rows = [_row(m, "2000-01-01", "2099-12-31", 100.0) for m in lags]
        series[eco] = VintagedSeries(series_id=eco, rows=rows)
    for eco in ("GB", "NZ", "AU"):
        rows = [_row(m, "2000-01-01", "2099-12-31", 100.0) for m in lags]
        rows.append(_row("2021-05", "2000-01-01", "2099-12-31", 100.5))
        series[eco] = VintagedSeries(series_id=eco, rows=rows)
    return RunEnv(census={}, events=events,
                  order_state=E.order_state(events),
                  grid=list(GRID_DAYS), grid_index=dict(GRID_INDEX),
                  series_by_eco=series, dgs10_rows=[], spot_sha256={},
                  provenance={})


def test_placebo_seed_determinism():
    env = _ordshuf_env()
    anchor = A.build_a5p1_anchor(env)
    b1 = A.build_a5p1_ordshuf(env, anchor, seed=C.PLACEBO_RNG_SEED)
    b2 = A.build_a5p1_ordshuf(env, anchor, seed=C.PLACEBO_RNG_SEED)
    # frozen seed -> byte-identical selection and records
    assert b1["meta"]["drawn_event_keys"] == b2["meta"]["drawn_event_keys"]
    assert b1["decisions"] == b2["decisions"]
    # a different seed changes the draw on this fixture
    b3 = A.build_a5p1_ordshuf(env, anchor, seed=7)
    assert b3["meta"]["drawn_event_keys"] != b1["meta"]["drawn_event_keys"]
    # marginal fired-count preserved: n* == anchor fired count
    assert b1["meta"]["n_star"] == anchor["meta"]["decisions_fired"]
    assert b1["meta"]["decisions_fired"] == b1["meta"]["n_star"]


# --------------------------------------------------------------------------- #
# 6. control arm distinct from the anchor
# --------------------------------------------------------------------------- #

def _fixture_dgs10():
    """Extended weekday grid (>=252 days ending 2021-07-02); levels 2.0
    everywhere except the entry day 06-24 revised to 1.0 -> below the
    trailing median -> state +1."""
    days, d = [], date(2021, 7, 2)
    while len(days) < 260:
        if d.weekday() < 5:
            days.append(d)
        d -= timedelta(days=1)
    days.reverse()
    rows = [{"obs": "2021-06-23", "rs": date(2019, 1, 1),
             "re": date(2099, 12, 31), "value": 2.0},
            {"obs": "2021-06-24", "rs": date(2021, 6, 24),
             "re": date(2099, 12, 31), "value": 1.0}]
    return Dgs10LevelSeries(rows, days)


def test_control_arm_distinct_from_anchor():
    env = fixture_env()
    anchor = A.build_a5p1_anchor(env)
    ctl = A.build_dgs10_control("FXNG1-A5-P1-CTL-DGS10LEVEL", env,
                                anchor, _fixture_dgs10())
    a = anchor["decisions"][0]
    c = ctl["decisions"][0]
    # identical clock/pair/horizon, DIFFERENT direction (anchor +1 from
    # s1<0; control +1 funded sign from below-median DGS10 -> USDCAD -1)
    assert c["entry_grid_day"] == a["entry_grid_day"]
    assert c["exit_grid_day"] == a["exit_grid_day"]
    assert c["pair"] == a["pair"]
    assert c["direction"] != a["direction"]
    # and the books' digests differ (different representation identity)
    da = C.arm_config_digest("FXNG1-A5-P1-ANCHOR")
    dc = C.arm_config_digest("FXNG1-A5-P1-CTL-DGS10LEVEL")
    assert da != dc


def test_budget_digests_pairwise_distinct_and_deterministic():
    d1 = C.budget_arm_digests()
    d2 = C.budget_arm_digests()
    assert d1 == d2
    assert len(set(d1.values())) == 6
    assert set(d1) == {arm for _, arm in C.BUDGET_ARMS}


# --------------------------------------------------------------------------- #
# 7. leak scanner (negative control included)
# --------------------------------------------------------------------------- #

def test_scanner_detects_planted_leak():
    planted = {
        "schema": "x@1",
        "meta": {"decisions_fired": 3},
        "decisions": [
            {"decision_id": "A|CA|2021-06-16|USDCAD",
             "entry_grid_day": "2021-06-24",
             "nested": {"deep": [{"pnl_usd": 12.34}]}}
        ],
    }
    found = S.scan_document(planted)
    assert len(found) == 1
    assert found[0]["path"] == ("$.decisions[0].nested.deep[0].pnl_usd")
    assert found[0]["key"] == "pnl_usd"


def test_scanner_variants_and_clean():
    # other forbidden spellings at any depth
    for key in ("PF", "profit-factor", "expectancy_net", "breakeven_bps",
                "stress_pnl"):
        assert len(S.scan_document({"a": [{"b": {key: 1.0}}]})) == 1, key
    # null outcome fields are verified-absent, not leaks
    assert S.scan_document({"pnl": None}) == []
    # a canonical dry decision record is clean
    env = fixture_env()
    rec = A.build_a5p1_anchor(env)["decisions"][0]
    assert S.scan_document(rec) == []


def test_scanner_on_file(tmp_path):
    p = tmp_path / "planted.json"
    p.write_text(json.dumps({"ok": 1, "sub": {"expectancy": 0.5}}))
    found = S.scan_json_file(str(p))
    assert len(found) == 1 and found[0]["key"] == "expectancy"
    clean = tmp_path / "clean.json"
    clean.write_text(json.dumps({"decisions": [
        {"decision_id": "x", "direction": 1}]}))
    assert S.scan_json_file(str(clean)) == []


# --------------------------------------------------------------------------- #
# 8. R1-R6 evaluator: one pass + one fail case per rule
# --------------------------------------------------------------------------- #

def _base_metrics():
    return {
        "expectancy_net_tier2": 5.0,
        "anchor_expectancy_net_tier2": 5.0,
        "control_expectancy_net_tier2": 1.0,      # 1.0 < 0.5*5.0
        "fold_expectancies_net_tier2": {"1": 3.0, "2": 2.0, "3": 0.5},
        "profit_factor_net_tier2": 1.25,
        "stress_tier2_expectancy_net": 4.0,
        "drop_one_fold_positive": {"1": True, "2": True, "3": True},
        "max_single_event_gross_share": 0.30,
    }


def test_r1_expectancy():
    assert R.evaluate_r1(_base_metrics()) == "PASS"
    m = _base_metrics() | {"expectancy_net_tier2": -0.01}
    assert R.evaluate_r1(m) == "FAIL"
    assert R.evaluate_r1({}) == "NOT_RUN"


def test_r2_control_kill():
    assert R.evaluate_r2(_base_metrics()) == "PASS"
    # control reproduces: 3.0 >= 0.5 * 5.0 (same-sign positive)
    m = _base_metrics() | {"control_expectancy_net_tier2": 3.0}
    assert R.evaluate_r2(m) == "FAIL"
    # the A5 additional V7-recap kill (R2') fires independently
    m = _base_metrics() | {"v7recap_expectancy_net_tier2": 5.0}
    assert R.evaluate_r2(m) == "FAIL"
    assert R.evaluate_r2({}) == "NOT_RUN"


def test_r3_folds():
    assert R.evaluate_r3(_base_metrics()) == "PASS"
    m = _base_metrics() | {"fold_expectancies_net_tier2":
                           {"1": 3.0, "2": -1.0, "3": -0.5}}
    assert R.evaluate_r3(m) == "FAIL"
    assert R.evaluate_r3({}) == "NOT_RUN"


def test_r4_pf_with_margin():
    r = R.evaluate_r4(_base_metrics())
    assert r["verdict"] == "PASS" and r["margin_to_bar"] == 0.15
    r = R.evaluate_r4(_base_metrics() | {"profit_factor_net_tier2": 1.05})
    assert r["verdict"] == "FAIL" and r["margin_to_bar"] == -0.05
    assert R.evaluate_r4({})["verdict"] == "NOT_RUN"


def test_r5_stress():
    assert R.evaluate_r5(_base_metrics()) == "PASS"
    m = _base_metrics() | {"stress_tier2_expectancy_net": -1.0}
    assert R.evaluate_r5(m) == "FAIL"
    assert R.evaluate_r5({}) == "NOT_RUN"


def test_r6_non_concentration():
    assert R.evaluate_r6(_base_metrics()) == "PASS"
    m = _base_metrics() | {"max_single_event_gross_share": 0.60}
    assert R.evaluate_r6(m) == "FAIL"
    m = _base_metrics() | {"drop_one_fold_positive":
                           {"1": True, "2": True, "3": False}}
    assert R.evaluate_r6(m) == "FAIL"
    assert R.evaluate_r6({}) == "NOT_RUN"


def test_stage_a_verdicts():
    ok = R.evaluate_stage_a(_base_metrics())
    assert ok["verdict"] == "PROVISIONAL_STAGE_A_SURVIVOR"
    missing = R.evaluate_stage_a({})
    assert missing["verdict"] == "NOT_RUN"
    dead = R.evaluate_stage_a(
        _base_metrics() | {"expectancy_net_tier2": -1.0})
    assert dead["verdict"] == "STAGE_A_DEAD"


# --------------------------------------------------------------------------- #
# dry-record schema: no outcome fields, IDs distinct (belt + braces)
# --------------------------------------------------------------------------- #

def test_dry_records_carry_no_outcome_fields():
    env = fixture_env()
    for arm in ("FXNG1-A5-P1-ANCHOR", "FXNG1-A4-P2-ANCHOR"):
        book = A.build_arm(arm, env)
        assert book["decisions"]
        assert S.scan_document(book) == []
    env2 = fixture_env()
    ids = [r["decision_id"]
           for arm in ("FXNG1-A5-P1-ANCHOR", "FXNG1-A4-P2-ANCHOR")
           for r in A.build_arm(arm, env2)["decisions"]]
    assert len(set(ids)) == len(ids)
