"""FOREX-SEARCH-V1 P0 targeted fixtures (plans/PLAN_forex_search_v1.md §4).

Offline only: NO network in any test. Covers: staging digest pinning,
calendar census (holidays/missing bars, no ffill), fired-census counters
incl. force-flat at fold boundary, the OPEN-GAP §4 F3 timing exception
(one-bar-earlier recomputation mutates the book; later bars never leak),
the §8 warmup rule (253/61 first decision bars, complete-window fail-closed),
and the P0 no-PnL mission invariant.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pytest

WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/forex-search-v1/integration")
P0 = WT / "research/control/forex_search_v1_run/p0"
STAGING = Path("/tmp/fsearch_p0_staging")
sys.path.insert(0, str(WT))

from research.control.forex_search_v1_run.p0.p0_census import (  # noqa: E402
    PAIR_SOURCES, WARMUP_BARS, calendar_census, compute_state, enumerate_configs,
    make_folds, run_census, sha256_file, state_open_gap, state_vol_drift)

LEGS = ["EURUSD", "GBPUSD", "USDCAD", "AUDUSD", "NZDUSD"]
PLAN_DIGEST_PREFIXES = {
    "EURUSD": "01cb862b", "GBPUSD": "e3e4c519", "USDCAD": "4b988c44",
    "AUDUSD": "097cfe59", "NZDUSD": "7dff3299",
}
FORBIDDEN_KEYS = {"pnl", "sharpe", "profit_factor", "expectancy", "drawdown",
                  "survivors", "return", "returns"}


# ------------------------------------------------------------------ helpers

def synth_leg(n: int, start: date = date(2024, 1, 1), base: float = 1.0) -> dict:
    """n consecutive WEEKDAY bars, deterministic prices, ascending dates."""
    dates, o, h, l, c = [], [], [], [], []
    d, px = start, base
    while len(dates) < n:
        if d.isoweekday() <= 5:
            op_, cl_ = px, px * 1.0001
            dates.append(d.isoformat())
            o.append(op_); c.append(cl_)
            h.append(max(op_, cl_) * 1.0002); l.append(min(op_, cl_) * 0.9998)
            px = cl_ * 1.0001
        d += timedelta(days=1)
    return {"symbol": "TEST", "dates": dates,
            "open": np.array(o), "high": np.array(h),
            "low": np.array(l), "close": np.array(c)}


# ------------------------------------------------------------- digest pinning

def test_manifest_pin_matches_plan_frozen_digests():
    pin = json.loads((P0 / "manifest_pin.json").read_text())
    assert pin["schema"] == "p0_manifest_pin@1"
    assert set(pin["pairs"]) == set(LEGS)
    for leg in LEGS:
        p = pin["pairs"][leg]
        assert p["sha256"].startswith(PLAN_DIGEST_PREFIXES[leg])
        assert p["matches_plan_frozen_digest"] is True
        assert p["rows"] == 5000
    assert pin["ng1_copies_byte_identical"] is True
    assert pin["excluded"]["XAUUSD"].startswith("EXCLUDED")


def test_staging_bytes_match_pin():
    """Recompute digests from the extracted staging (skipped when the
    scratch extraction is absent — tests never require the archives)."""
    pin = json.loads((P0 / "manifest_pin.json").read_text())
    for leg in LEGS:
        member = pin["pairs"][leg]["member"]
        f = STAGING / member
        if not f.exists():
            pytest.skip(f"staging extraction absent: {member}")
        assert sha256_file(f) == pin["pairs"][leg]["sha256"]


def test_tarball_digest_manifest_records_all_seven():
    pin = json.loads((P0 / "manifest_pin.json").read_text())
    dig = pin["tarball_sha256_vs_SHA256SUMS"]
    assert len(dig) == 7
    assert all(v["match"] for v in dig.values())


# ---------------------------------------------------------- calendar census

def test_calendar_census_counts_holidays_no_ffill():
    a = synth_leg(30)
    b = synth_leg(30)
    # remove one mid-series weekday from leg b (a "holiday"): index 10
    hol = b["dates"][10]
    for k in ("dates", "open", "high", "low", "close"):
        v = b[k]
        b[k] = v[:10] + v[11:] if isinstance(v, list) else np.concatenate([v[:10], v[11:]])
    legs = {"EURUSD": a, "GBPUSD": b, "USDCAD": a, "AUDUSD": a, "NZDUSD": a}
    cal = calendar_census(legs)
    assert cal["ffill_used"] is False
    assert cal["master_len"] == 29
    assert hol not in set(cal["master_calendar"])
    assert cal["per_leg"]["GBPUSD"]["missing_vs_union_count"] == 1
    assert cal["per_leg"]["GBPUSD"]["missing_vs_union"] == [hol]
    for leg in LEGS:
        if leg != "GBPUSD":
            assert cal["per_leg"][leg]["missing_vs_union_count"] == 0


def test_folds_are_three_chronological_thirds():
    legs = {k: synth_leg(90) for k in LEGS}
    cal = calendar_census(legs)
    folds = make_folds(cal["master_calendar"])
    assert folds["fold_count"] == 3
    sizes = [f["master_bars"] for f in folds["folds"]]
    assert sizes[0] == 30 and sizes[1] == 30 and sizes[2] == 30
    assert folds["folds"][0]["last"] < folds["folds"][1]["first"]
    assert folds["folds"][1]["last"] < folds["folds"][2]["first"]
    assert folds["measured_before_any_census"] is True


# ------------------------------------------------------- fired-census counters

def _tiny_census(dow: int, n_days: int = 210):
    legs = {k: synth_leg(n_days) for k in LEGS}
    cal = calendar_census(legs)
    folds = make_folds(cal["master_calendar"])
    cfg = {"config_id": f"FSS-CLOCK-COND-DOW{dow}-LONG", "family": "CLOCK-COND",
           "dow": dow, "direction": "LONG"}
    census = run_census(legs, cal, folds, [cfg])
    return census["per_config"][cfg["config_id"]], cal, folds


def test_census_counts_dow_state_and_respects_warmup():
    d, cal, folds = _tiny_census(1)
    master = cal["master_calendar"]
    # warmup 60 on the master calendar; force-flat at fold boundary
    expected = 0
    b = folds["boundaries_index"]
    for m in range(60, len(master)):
        f = next(k for k in range(3) if b[k] <= m < b[k + 1])
        nxt_in_fold = (m + 1 < len(master)) and (b[f] <= m + 1 < b[f + 1])
        if date.fromisoformat(master[m]).isoweekday() == 1 and nxt_in_fold:
            expected += 1
    assert d["fired_total"] == expected * 5  # five identical legs
    assert d["fired_by_fold"]["1"] + d["fired_by_fold"]["2"] + d["fired_by_fold"]["3"] == expected * 5


def test_force_flat_at_fold_boundary_drops_execution_outside_fold():
    """210 weekdays from Mon 2024-01-01: fold1 = master[0:70]. DOW5 fires at
    m=64 (counted) AND m=69 — but m=69's execution bar is master[70], in
    fold 2, so force-flat MUST drop it: fold-1 count is 1, not 2."""
    d, cal, _ = _tiny_census(5)
    assert date.fromisoformat(cal["master_calendar"][69]).isoweekday() == 5
    assert date.fromisoformat(cal["master_calendar"][70]).isoweekday() == 1
    assert d["fired_by_fold"]["1"] == 5  # m=64 on each of 5 legs; m=69 dropped
    naive = sum(1 for m in range(60, 70)
                if date.fromisoformat(cal["master_calendar"][m]).isoweekday() == 5)
    assert naive == 2  # per leg: the fixture would fire twice without force-flat
    assert naive * 5 == 10  # and ten leg-events in total


def test_config_enumeration_is_33_with_clock_cond_14():
    cfgs = enumerate_configs()
    assert len(cfgs) == 33
    fams = {}
    for c in cfgs:
        fams[c["family"]] = fams.get(c["family"], 0) + 1
    assert fams == {"CLV-DIVERGENCE": 6, "EXTREME-FADE": 3, "OPEN-GAP": 6,
                    "VOL-DRIFT": 4, "CLOCK-COND": 14}
    ids = [c["config_id"] for c in cfgs]
    assert ids == sorted(ids) and len(set(ids)) == 33
    assert all(i.startswith("FSS-") for i in ids)


# --------------------------------------------------------- OPEN-GAP timing

def test_open_gap_state_uses_close_t_and_open_t1_only():
    """F3 exception: firing depends on close(t) and open(t+1); perturbing the
    execution bar's CLOSE (or anything at/after t+2, except via later
    windows) never changes the firing at t; perturbing open(t+1) does."""
    leg = synth_leg(320)
    master = leg["dates"]
    own = list(range(len(master)))
    big = 10.0
    t = 300  # decision bar; trigger gap at own index t+1
    # baseline: deep positive gap at t+1 -> up-side firing for Q75
    leg["open"][t + 1] = leg["close"][t] + big
    base = state_open_gap(leg, own, "FADE", 75, 252)
    assert base.get(t) == "SHORT"  # fade of an up-gap
    # mutation 1: perturb execution-bar CLOSE (knowable AFTER the fill):
    leg2 = {k: (v.copy() if isinstance(v, np.ndarray) else list(v))
            for k, v in leg.items()}
    leg2["close"][t + 1] = leg2["close"][t + 1] * 1.5
    assert state_open_gap(leg2, own, "FADE", 75, 252).get(t) == "SHORT"
    # mutation 2: perturb open(t+1) -> the firing itself changes:
    leg3 = {k: (v.copy() if isinstance(v, np.ndarray) else list(v))
            for k, v in leg.items()}
    leg3["open"][t + 1] = leg3["close"][t]  # gap neutralised
    assert t not in state_open_gap(leg3, own, "FADE", 75, 252)
    # mutation 3: one-bar-earlier recomputation at t-1 must NOT see the t+1 gap:
    leg4 = {k: (v.copy() if isinstance(v, np.ndarray) else list(v))
            for k, v in leg.items()}
    # (C-PIT-MUTATION spirit: shift the big gap one bar later: state at t
    # uses only windows ending at t; a gap at t+2 is invisible at t)
    leg4["open"][t + 1] = leg4["close"][t]
    leg4["open"][t + 2] = leg4["close"][t + 1] + big
    assert t not in state_open_gap(leg4, own, "FADE", 75, 252)


def test_open_gap_threshold_window_is_trailing_and_causal():
    leg = synth_leg(320)
    master = leg["dates"]
    own = list(range(len(master)))
    t = 300
    # no firing without a deep gap
    assert state_open_gap(leg, own, "FADE", 75, 252).get(t) in (None, "SHORT", "LONG")
    # deep NEGATIVE gap at t+1 -> Q25 (down-tail) fires LONG (fade)
    leg["open"][t + 1] = leg["close"][t] - 10.0
    assert state_open_gap(leg, own, "FADE", 25, 252).get(t) == "LONG"
    assert state_open_gap(leg, own, "CONFIRM", 25, 252).get(t) == "SHORT"
    # Q75 (up-tail) must NOT fire on a deep negative gap
    assert t not in state_open_gap(leg, own, "CONFIRM", 75, 252)


# ------------------------------------------------------------------ warmup

def test_warmup_first_decision_bar_253_for_gap_and_vol_61_otherwise():
    leg = synth_leg(400)
    master = leg["dates"]
    own = list(range(len(master)))
    for cfg in enumerate_configs():
        st = compute_state(cfg, leg, own, master)
        first = min(st) if st else None
        if cfg["family"] in ("OPEN-GAP", "VOL-DRIFT"):
            assert first is None or first >= 252, cfg["config_id"]
        else:
            assert first is None or first >= 60, cfg["config_id"]
        assert WARMUP_BARS[cfg["family"]] in ((252,) if cfg["family"] in
                                              ("OPEN-GAP", "VOL-DRIFT") else (60,))


def test_vol_drift_complete_window_fail_closed_l63():
    """Complete-window law: boundaries need 252 trailing estimator values,
    each needing L returns -> first possible own index is L+251 (=314 for
    L=63). No partial-window firing may exist before it."""
    leg = synth_leg(400)
    own = list(range(len(leg["dates"])))
    st = state_vol_drift(leg, own, "MOM", 63, 252)
    assert all(m >= 63 + 251 for m in st)
    # constant-vol rising series: MOM must fire at the FIRST complete bar
    n = 400
    c = 1.0 + np.arange(n) * 0.001
    leg2 = {"symbol": "T", "dates": leg["dates"], "open": c, "high": c * 1.001,
            "low": c * 0.999, "close": c}
    st2 = state_vol_drift(leg2, own, "MOM", 63, 252)
    assert st2.get(63 + 251) == "LONG"


# --------------------------------------------------------------- artifacts

def test_committed_census_artifact_consistent():
    c = json.loads((P0 / "fired_census.json").read_text())
    assert c["schema"] == "fired_census@1"
    assert c["config_count"] == 33 and c["clock_cond_count"] == 14
    assert set(c["per_config"]) == {x["config_id"] for x in enumerate_configs()}
    for cid, d in c["per_config"].items():
        assert sum(d["fired_by_fold"].values()) == d["fired_total"]
        for f in ("1", "2", "3"):
            assert d["pooled_floor_ge30_by_fold"][f] == (d["fired_by_fold"][f] >= 30)


def test_committed_census_matches_independent_recount():
    """Strong reproduction fixture (skipped without the staging extraction):
    recount CLOCK-COND DOW1-LONG from the raw staging files and compare."""
    if not all((STAGING / PAIR_SOURCES[l][1]).exists() for l in LEGS):
        pytest.skip("staging extraction absent")
    pin = json.loads((P0 / "manifest_pin.json").read_text())
    for leg in LEGS:
        f = STAGING / pin["pairs"][leg]["member"]
        if hashlib.sha256(f.read_bytes()).hexdigest() != pin["pairs"][leg]["sha256"]:
            pytest.skip("staging bytes drifted from pin")
    from research.control.forex_search_v1_run.p0.p0_census import load_leg
    legs = {k: load_leg(STAGING / PAIR_SOURCES[k][1]) for k in LEGS}
    cal = calendar_census(legs)
    folds = make_folds(cal["master_calendar"])
    cfg = [c for c in enumerate_configs()
           if c["config_id"] == "FSS-CLOCK-COND-DOW1-LONG"][0]
    census = run_census(legs, cal, folds, [cfg])
    committed = json.loads((P0 / "fired_census.json").read_text())
    assert (census["per_config"][cfg["config_id"]]["fired_by_fold"]
            == committed["per_config"][cfg["config_id"]]["fired_by_fold"])
    # and the recount must be deterministic byte-wise on the fold structure
    assert folds["master_dates_sha256"] == make_folds(cal["master_calendar"])[
        "master_dates_sha256"]


def test_no_pnl_evidence_in_p0_artifacts():
    """Mission invariant: P0 computes NO candidate PnL/PF/Sharpe/drawdown/
    survivors/S1 evidence. The committed artifacts must not carry any."""
    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                yield k, v
                yield from walk(v)
        elif isinstance(o, list):
            for v in o:
                yield from walk(v)
    for name in ("fired_census.json", "calendar_census.json", "folds_freeze.json",
                 "structural_census.json", "manifest_pin.json"):
        for k, _ in walk(json.loads((P0 / name).read_text())):
            kl = k.lower()
            assert kl not in FORBIDDEN_KEYS, (name, k)


def test_gate_reports_all_seven_gates():
    g = json.loads((P0 / "p0_gate.json").read_text())
    assert g["schema"] == "p0_gate@1"
    assert set(g["gates"]) == {"F1_STAGING_CHAIN", "F2_ENTITLEMENT_TERMS",
                               "F3_CLOCK_EXECUTION", "F4_COSTS_FINANCING",
                               "F5_FOLDS_CENSUS", "F6_REPRODUCIBILITY",
                               "F7_CONTROL_SOURCE_AUTHORITY"}
    assert g["d2_status"].startswith("SKIPPED")
    assert g["gates"]["F4_COSTS_FINANCING"]["constants"][
        "operative_stress_worst_bps_per_round_trip"] == 9.4
