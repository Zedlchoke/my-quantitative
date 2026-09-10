#!/usr/bin/env python
"""FOREX-FREE-V3 family2 (FXFV3-A6-P1) tests.  All expected numbers are
hand-computed literals pinned to the frozen proposal
(research/proposals/forex_free_v3/a6_lane/proposal_1.json).  Synthetic
fixtures only -- NO network, NO real scored PnL anywhere; the one real
snapshot test is SCHEDULE-ONLY (counts, no PnL) and skips when the
gitignored snapshot is not staged."""
import hashlib
import json
import math
import os
import tempfile
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from research.assets.forex_free_v3 import family2 as F
from research.assets.forex_free_v3 import scored_runner as R
from research.assets.forex_free_v3 import accounting
from research.assets.forex_free_v3.macro_reader import (
    MacroDataBlocked,
    PolicyRateReader,
    from_data_paths,
)

NY = ZoneInfo("America/New_York")
UTC = timezone.utc
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
DEFAULT_SNAPSHOT = os.path.join(REPO_ROOT, "data_raw", "forex_free_v1")
DEFAULT_MANIFEST = ("/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v2"
                    "/integration/research/control/forex_free_v1_run"
                    "/staged_data_manifest.json")

# Fixture rate levels (percent per annum, the adopted vintage convention).
RATES = {"US": 5.25, "EMU": 4.00, "GB": 5.00, "JP": 0.10, "CH": 5.25,
         "CA": 4.50, "AU": 4.00, "NZ": 5.50}
SCALES = {"EUR/USD": 1.0, "GBP/USD": 1.25, "AUD/USD": 0.65, "NZD/USD": 0.60,
          "USD/JPY": 150.0, "USD/CHF": 0.90, "USD/CAD": 1.35}


# ---------------------------------------------------------------- #
# synthetic fixture builders (continuous 24/7 hourly bars)           #
# ---------------------------------------------------------------- #
def weekday_dates(start: date, end: date) -> list:
    out, d = [], start
    while d <= end:
        if d.weekday() < 5:
            out.append(d)
        d += timedelta(days=1)
    return out


def wd_date(start: date, wd: int) -> date:
    """Calendar date of weekday index ``wd`` (wd counts Mon-Fri only)."""
    d = start
    n = 0
    while True:
        if d.weekday() < 5:
            if n == wd:
                return d
            n += 1
        d += timedelta(days=1)


def bars_continuous(rr_by_day, close_by_day, start: date, end: date, scale=1.0):
    """Continuous hourly bars; per-NY-day true-range width rr/48 so that a
    complete 24-bar NY-day window sums to exactly rr (constant closes =>
    each bar TR = 2x = rr/24, x24 bars = rr)."""
    bars = {}
    t = datetime.combine(start, datetime.min.time(), tzinfo=UTC)
    endt = datetime.combine(end, datetime.min.time(), tzinfo=UTC) + timedelta(hours=23)
    while t <= endt:
        nyd = t.astimezone(NY).date()
        rr = rr_by_day.get(nyd, 0.015)
        c = close_by_day.get(nyd, 1.0) * scale
        x = rr / 48.0
        bars[t] = (c, c + x, c - x, c)
        t += timedelta(hours=1)
    return bars


def write_pair(tmp, pair, bars):
    rows = [{"datetime": s.strftime("%Y-%m-%d %H:%M:%S"),
             "open": repr(o), "high": repr(h), "low": repr(l), "close": repr(c)}
            for s, (o, h, l, c) in sorted(bars.items())]
    path = os.path.join(tmp, pair.replace("/", "") + "_1h_fix_a.json")
    with open(path, "w") as handle:
        json.dump({"meta": {"symbol": pair, "interval": "1h"}, "values": rows}, handle)
    return path


def write_all_pairs(tmp, bars_by_pair):
    for pair, bars in bars_by_pair.items():
        write_pair(tmp, pair, bars)
    return tmp


def vintage(area, value, eff="2024-01-01T00:00:00Z", avail="2024-01-01T20:00:00Z"):
    return {"source_id": "BIS_CBPOL", "dataset_id": "WS_CBPOL", "entity_id": area,
            "field": "policy_rate", "value": value, "unit": "percent_per_annum",
            "event_time_utc": eff, "available_time_utc": avail,
            "effective_time_utc": eff, "vintage_time_utc": avail,
            "retrieved_time_utc": "2026-09-01T00:00:00Z", "raw_path": "bis/x.json",
            "raw_sha256": "a" * 64, "license_id": "bis-terms-public-v1",
            "entitlement_id": "anonymous-no-key", "normalizer_version": "bis-adapter-1.0.0"}


def reader_from(tmp, specs):
    """specs: {area: [ (value, eff, avail), ... ]} -> PolicyRateReader."""
    paths = {}
    for area, rows in specs.items():
        p = os.path.join(tmp, f"vint_{area}.json")
        with open(p, "w") as handle:
            json.dump([vintage(area, v, eff, av) for (v, eff, av) in rows], handle)
        paths[area] = p
    return from_data_paths({"macro_vintages": paths})


def family_reader(tmp, rates=RATES, eff="2024-01-01T00:00:00Z",
                  avail="2024-01-01T20:00:00Z"):
    return reader_from(tmp, {a: [(v, eff, avail)] for a, v in rates.items()})


# ---------------------------------------------------------------- #
# shared plans                                                        #
# ---------------------------------------------------------------- #
START = date(2024, 1, 1)       # module churn fixture span
END = date(2025, 12, 31)


def churn_rr_plan():
    """Deterministic churn plan by weekday index (wd 0 = 2024-01-01 Mon):
    baseline 0.03 (wd<199) -> LOW 0.015 (199..258) -> HIGH 0.30 spike block
    (259..278) -> LOW again (279..338) -> HIGH (339..358) -> LOW (359+)."""
    plan = {}
    wd = 0
    d = START
    while d <= END:
        if d.weekday() < 5:
            if wd < 199:
                plan[d] = 0.03
            elif wd < 259:
                plan[d] = 0.015
            elif wd < 279:
                plan[d] = 0.50
            elif wd < 339:
                plan[d] = 0.015
            elif wd < 359:
                plan[d] = 0.30
            else:
                plan[d] = 0.015
            wd += 1
        d += timedelta(days=1)
    return plan


@pytest.fixture(scope="module")
def churn_env():
    """One shared 7-pair synthetic universe + constant macro reader."""
    tmp = tempfile.mkdtemp(prefix="family2_churn_")
    plan = churn_rr_plan()
    bars_by_pair = {p: bars_continuous(plan, {}, START, END, s)
                    for p, s in SCALES.items()}
    write_all_pairs(tmp, bars_by_pair)
    return {"h1_dir": tmp, "reader": family_reader(tmp)}


# ---------------------------------------------------------------- #
# 1. feature goldens: rr + as-of differential directions              #
# ---------------------------------------------------------------- #
def test_rr_and_differential_goldens():
    tmp = tempfile.mkdtemp(prefix="family2_golden_")
    # Jan 2024: Mon 01 .. Thu 04; EST => decision stamps at 21:00Z.
    rr = {date(2024, 1, 1): 0.024, date(2024, 1, 2): 0.024,
          date(2024, 1, 3): 0.048, date(2024, 1, 4): 0.0}
    bars = bars_continuous(rr, {}, date(2024, 1, 1), date(2024, 1, 5))
    write_pair(tmp, "EUR/USD", bars)
    series = F.PairSeries("EUR/USD", F.load_h1_bars(tmp, "EUR/USD"))
    # Valid days: Jan 2..5 (Jan 1 lacks the Dec-31 anchor bar; the fixture
    # extends to Jan 5 for the trailing window).
    valid_days = [series.stamps[i].astimezone(NY).date() for i in series.valid_idx]
    assert valid_days == [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 4),
                          date(2024, 1, 5)]
    # Hand-computed rr goldens.  A 24-bar NY-day window covers 7 bars of the
    # previous NY evening (17:00-24:00 EST: 22Z,23Z + 00-04Z) and 17 bars of
    # the day itself (00:00-16:00 EST: 05-21Z); every bar of NY-day d carries
    # x = rr_d/48 so TR = 2x = rr_d/24 (closes flat at 1.0):
    #   Jan 2: 7 bars @rr .024 + 17 bars @rr .024 = 24*(0.024/24) = 0.024
    #   Jan 3: 7 bars @rr .024 + 17 bars @rr .048 = 0.007 + 0.034 = 0.041
    #   Jan 4: 7 bars @rr .048 + 17 bars @rr .000 = 0.014 + 0 = 0.014
    #   Jan 5: 7 bars @rr .000  + 17 bars @rr .015 = 17*(0.015/24) = 0.010625
    assert series.rr[series.valid_idx[0]] == pytest.approx(0.024, abs=1e-12)
    assert series.rr[series.valid_idx[1]] == pytest.approx(0.041, abs=1e-12)
    assert series.rr[series.valid_idx[2]] == pytest.approx(0.014, abs=1e-12)
    assert series.rr[series.valid_idx[3]] == pytest.approx(0.010625, abs=1e-12)
    # Decision stamps are 16:00 NY in UTC: January => EST => 21:00Z.
    assert _iso(series.stamps[series.valid_idx[0]]) == "2024-01-02T21:00:00+00:00"

    # As-of differential directions on tiny vintages (hand-computed).
    reader = family_reader(tmp)
    t = "2024-01-03T21:00:00+00:00"
    # EUR/USD: (EMU,US) = 4.00 - 5.25 = -1.25 => -1 (short base).
    assert reader.differential("EMU", "US", t) == pytest.approx(-1.25)
    assert F._sign_or_none(reader.differential("EMU", "US", t)) == -1
    # USD/JPY: (US,JP) = 5.25 - 0.10 = +5.15 => +1 (long base).
    assert F._sign_or_none(reader.differential("US", "JP", t)) == 1
    # USD/CHF: exact zero differential => NO_EVAL (never side 0).
    assert reader.differential("US", "CH", t) == 0.0
    assert F._sign_or_none(reader.differential("US", "CH", t)) is None
    # Missing eligible vintage at T => None (fail-closed, never backfilled).
    assert reader.policy_rate("US", "2023-12-30T21:00:00+00:00") is None


def _iso(t):
    return t.strftime("%Y-%m-%dT%H:%M:%S+00:00")


# ---------------------------------------------------------------- #
# 2. PIT / no-lookahead mutation check                                #
# ---------------------------------------------------------------- #
def test_pit_availability_mutation_flips_eligibility():
    tmp = tempfile.mkdtemp(prefix="family2_pit_")
    # A 2024-03 rate change effective Wed 2024-03-20, owner-captured at
    # 21:00Z -- i.e. AFTER that day's 20:00Z (EDT) decision instant but
    # BEFORE the next day's.  EUR/USD direction flips -1 => +1 when eligible.
    old_rows = [(4.00, "2024-01-02T00:00:00Z", "2024-01-02T20:00:00Z"),   # EMU
                (5.25, "2024-01-02T00:00:00Z", "2024-01-02T20:00:00Z")]   # US
    specs = {
        "EMU": old_rows[:1] + [(6.00, "2024-03-20T00:00:00Z", "2024-03-20T21:00:00Z")],
        "US": old_rows[1:] + [(5.50, "2024-03-20T00:00:00Z", "2024-03-20T21:00:00Z")],
    }
    reader = reader_from(tmp, specs)
    t1, t2 = "2024-03-20T20:00:00+00:00", "2024-03-21T20:00:00+00:00"
    # T1 must read the OLD rows (available 21:00Z > T1): diff = 4.00-5.25.
    assert F._sign_or_none(reader.differential("EMU", "US", t1)) == -1
    # T2 reads the NEW rows: diff = 6.00-5.50 = +0.50.
    assert F._sign_or_none(reader.differential("EMU", "US", t2)) == 1
    assert reader.policy_rate("EMU", t1) == 4.00
    assert reader.policy_rate("EMU", t2) == 6.00

    # MUTATION: shift the new vintage's available_time_utc past T2 => T2
    # must flip back to the old rate (eligibility moves with the stamp).
    specs_mut = {
        "EMU": old_rows[:1] + [(6.00, "2024-03-20T00:00:00Z", "2024-03-21T21:00:00Z")],
        "US": old_rows[1:] + [(5.50, "2024-03-20T00:00:00Z", "2024-03-21T21:00:00Z")],
    }
    reader_mut = reader_from(tmp, specs_mut)
    assert F._sign_or_none(reader_mut.differential("EMU", "US", t1)) == -1
    assert F._sign_or_none(reader_mut.differential("EMU", "US", t2)) == -1  # flipped
    assert reader_mut.policy_rate("EMU", t2) == 4.00
    # If the availability lag ever regresses (effective-date-only reads),
    # the base case T1 would read +1 and both asserts above would fail.


# ---------------------------------------------------------------- #
# 3. vol regime boundary                                              #
# ---------------------------------------------------------------- #
def test_median_split_equality_is_high():
    # Anchor estimator (block means): LOW iff S < B STRICTLY.
    assert F.state_is_low([0.04] * 20, [0.05] * 10, estimator="mean") is True
    assert F.state_is_low([0.05] * 20, [0.05] * 10, estimator="mean") is False  # S==B => HIGH
    assert F.state_is_low([0.06] * 20, [0.05] * 10, estimator="mean") is False
    # Neighbour estimator (close-to-close std): 20 identical closes => S=0.
    assert F.state_is_low([0.0] * 19, [0.02] * 10, estimator="std") is True
    assert F.state_is_low([0.0] * 19, [0.0] * 10, estimator="std") is False
    # Median of 10 = mean of the two middle order statistics (hand-pinned).
    assert F._median10([0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10]) \
        == pytest.approx(0.055)


def test_gate_flips_exactly_at_pinned_dates(churn_env):
    series = F.PairSeries("EUR/USD", F.load_h1_bars(churn_env["h1_dir"], "EUR/USD"))
    vi = series.valid_idx
    # Warmup: 219 valid days => NO_EVAL; day 220 (wd index 220) => first eval.
    assert series.vol_state(vi[218], "mean") is None
    d219 = _iso(series.stamps[vi[219]])
    assert d219 == "2024-11-04T21:00:00+00:00"      # 220th valid NY-day
    assert series.vol_state(vi[219], "mean") is True   # S=0.015 < B~0.03 => LOW
    # LOW region ends at wd 258; the first 0.30-spike day is wd 259.
    d258 = wd_date(START, 258)
    d259 = wd_date(START, 259)
    i258 = series.stamps.index(F.ny_decision_stamp(d258))
    i259 = series.stamps.index(F.ny_decision_stamp(d259))
    assert series.valid[i258] and series.valid[i259]
    assert series.vol_state(i258, "mean") is True      # still LOW
    assert series.vol_state(i259, "mean") is False     # flips HIGH exactly here
    # (19*0.015 + 0.30)/20 = 0.02925 > baseline-dominated median; prior day
    # S = 0.015 < median.  The gate flipped on exactly the pinned date.


# ---------------------------------------------------------------- #
# 4. next-session fill + DST across the 2025 transitions              #
# ---------------------------------------------------------------- #
def test_dst_decision_stamps_and_next_session_fill(churn_env):
    series = F.PairSeries("EUR/USD", F.load_h1_bars(churn_env["h1_dir"], "EUR/USD"))
    # Spring forward 2025-03-09: Fri 03-07 (EST) 21:00Z -> Mon 03-10 (EDT) 20:00Z.
    fri = F.ny_decision_stamp(date(2025, 3, 7))
    mon = F.ny_decision_stamp(date(2025, 3, 10))
    assert _iso(fri) == "2025-03-07T21:00:00+00:00"
    assert _iso(mon) == "2025-03-10T20:00:00+00:00"
    assert series.next_bar_index(series.stamps.index(fri)) == series.stamps.index(mon)
    # Fall back 2025-11-02: Fri 10-31 (EDT) 20:00Z -> Mon 11-03 (EST) 21:00Z.
    fri2 = F.ny_decision_stamp(date(2025, 10, 31))
    mon2 = F.ny_decision_stamp(date(2025, 11, 3))
    assert _iso(fri2) == "2025-10-31T20:00:00+00:00"
    assert _iso(mon2) == "2025-11-03T21:00:00+00:00"
    assert series.next_bar_index(series.stamps.index(fri2)) == series.stamps.index(mon2)


def test_e2e_fills_are_next_existing_bar_with_weekend_lag(churn_env):
    out = F.run_arm("anchor", {"h1_dir": churn_env["h1_dir"]}, churn_env["reader"])
    decisions = out["decisions"]
    assert decisions, "churn fixture must trade"
    series = F.PairSeries("EUR/USD", F.load_h1_bars(churn_env["h1_dir"], "EUR/USD"))
    stamp_index = {s: i for i, s in enumerate(series.stamps)}
    weekend_lags = 0
    for dec in decisions:
        di = stamp_index[datetime.fromisoformat(dec["decision_ts"])]
        nb = series.next_bar_index(di)
        assert nb is not None
        assert dec["entry_bar_ts"] == _iso(series.stamps[nb])   # one-event lag
        assert datetime.fromisoformat(dec["entry_bar_ts"]) > \
            datetime.fromisoformat(dec["decision_ts"])
        lag = (datetime.fromisoformat(dec["entry_bar_ts"])
               - datetime.fromisoformat(dec["decision_ts"])).days
        assert 1 <= lag <= 4
        weekend_lags += 1 if lag == 3 else 0
    assert weekend_lags >= 1   # Friday decision filling Monday exists


# ---------------------------------------------------------------- #
# 5. derangement causal control                                       #
# ---------------------------------------------------------------- #
def test_derangement_frozen_mapping_identity_free_and_deterministic():
    assert F.SHAM_LEGS == {
        "EUR/USD": ("AU", "US"), "GBP/USD": ("NZ", "US"), "AUD/USD": ("US", "JP"),
        "NZD/USD": ("US", "CH"), "USD/JPY": ("US", "CA"), "USD/CHF": ("EMU", "US"),
        "USD/CAD": ("GB", "US")}
    for pair in F.PAIR_ORDER:   # identity-free: no pair drives itself
        assert F.SHAM_LEGS[pair] != F.PAIR_AREAS[pair]
        assert F.derangement_sham_legs(pair) == F.SHAM_LEGS[pair]  # deterministic


def test_control_directions_differ_from_anchor_on_fixture(churn_env):
    out_a = F.run_arm("anchor", {"h1_dir": churn_env["h1_dir"]}, churn_env["reader"])
    out_c = F.run_arm("causal_negative_control", {"h1_dir": churn_env["h1_dir"]},
                      churn_env["reader"])
    assert accounting.canonical_json_bytes(out_c) == \
        accounting.canonical_json_bytes(F.run_arm("control", {"h1_dir": churn_env["h1_dir"]},
                                                  churn_env["reader"]))
    sides_a = {(d["pair"], d["decision_ts"]): d["side"] for d in out_a["decisions"]}
    sides_c = {(d["pair"], d["decision_ts"]): d["side"] for d in out_c["decisions"]}
    shared = set(sides_a) & set(sides_c)
    assert shared, "both arms trade the same vol calendar"
    differing = {k for k in shared if sides_a[k] != sides_c[k]}
    assert differing, "sham pairing must flip at least one direction"
    # GBP/USD: own (GB,US) = -0.25 => -1; sham (NZ,US) = +0.25 => +1.
    assert any(k[0] == "GBP/USD" and sides_a[k] == -1 and sides_c[k] == 1
               for k in differing)
    # USD/CHF own differential is exactly zero => anchor never trades it;
    # the control's sham leg (EMU,US) does.
    assert not any(p == "USD/CHF" for p, _ in sides_a)
    assert any(p == "USD/CHF" for p, _ in sides_c)


# ---------------------------------------------------------------- #
# 6. force-flat at the 2024-07-01 fold boundary                       #
# ---------------------------------------------------------------- #
def test_force_flat_at_2024_07_01_boundary():
    tmp = tempfile.mkdtemp(prefix="family2_fflat_")
    start, end = date(2023, 1, 2), date(2024, 9, 30)
    # Baseline: alternating 20-day blocks of 0.06 / 0.02 (block median 0.04)
    # through wd 299, so every baseline-day state is comfortably HIGH or the
    # churn exits; the LOW region (rr = 0.01, S drops below B=0.04 after the
    # pre-300 tail drains from the 20-day window: first LOW day wd 309 =
    # 2024-01-26) persists past 2024-06-28 because the rolling 220-day
    # window keeps >= 4 baseline blocks (median >= 0.02 > S = 0.01) through
    # the boundary.  An open position is therefore force-flattened at the
    # boundary's last decision bar.
    plan = {}
    wd = 0
    d = start
    while d <= end:
        if d.weekday() < 5:
            if wd < 300:
                plan[d] = 0.06 if (wd // 20) % 2 == 0 else 0.02
            else:
                plan[d] = 0.01
            wd += 1
        d += timedelta(days=1)
    write_all_pairs(tmp, {p: bars_continuous(plan, {}, start, end, s)
                          for p, s in SCALES.items()})
    reader = family_reader(tmp)
    out = F.run_arm("anchor", {"h1_dir": tmp}, reader)
    decisions, events = out["decisions"], out["financing_events"]
    # The boundary force-flat: an open position exits at the open of the
    # last decision day's bar before 2024-07-01 (Fri 2024-06-28, EDT).
    ff = [d for d in decisions if d["force_flat"]]
    assert ff, "an open position must be force-flattened at the boundary"
    for dec in ff:
        assert dec["exit_bar_ts"] == "2024-06-28T20:00:00+00:00"  # Fri, EDT
        assert dec["decision_ts"] < "2024-07-01T00:00:00+00:00"
    # No trade crosses the boundary; the re-entry from the 06-28 decision
    # fills on 07-01 (after the boundary, a new fold) and exits later.
    trades, _adj, _f = R.validate_decisions(decisions, events)   # must NOT raise
    assert not any(d["entry_bar_ts"] == "2024-06-28T20:00:00+00:00" for d in decisions)
    assert all(datetime.fromisoformat(d["exit_bar_ts"]) < datetime(2024, 7, 1, tzinfo=UTC)
               or datetime.fromisoformat(d["entry_bar_ts"]) >= datetime(2024, 7, 1, tzinfo=UTC)
               for d in decisions)


# ---------------------------------------------------------------- #
# 7. dual-book separation with a hand-computed 3-day-hold term        #
# ---------------------------------------------------------------- #
def test_dual_book_three_day_hold_financing_hand_computed():
    tmp = tempfile.mkdtemp(prefix="family2_dual_")
    start = date(2023, 1, 2)
    plan = {}
    wd = 0
    d = start
    while d <= date(2024, 3, 31):
        if d.weekday() < 5:
            if wd < 199:
                plan[d] = 0.03            # baseline region
            elif wd in (253, 274):
                plan[d] = 0.50            # spikes: HIGH while inside S-window
            else:
                plan[d] = 0.015           # LOW elsewhere
            wd += 1
        d += timedelta(days=1)
    # wd 253 spike rolls out of the 20-day window at wd 273 (Thursday):
    # S(273)=0.015 < B => LOW => entry decision, fill Friday wd 274.
    # The spike AT wd 274 (Friday) makes S(274)=0.039 > B => HIGH => exit
    # fill Monday wd 275.  Exactly a 3-calendar-day (Fri->Mon) hold.
    assert wd_date(start, 273).weekday() == 3    # Thursday
    assert wd_date(start, 274).weekday() == 4    # Friday (entry fill day)
    assert wd_date(start, 275).weekday() == 0    # Monday (exit fill day)
    write_all_pairs(tmp, {p: bars_continuous(plan, {}, start, date(2024, 3, 31), s)
                          for p, s in SCALES.items()})
    reader = family_reader(tmp)
    out = F.run_arm("anchor", {"h1_dir": tmp}, reader)
    trips = [d for d in out["decisions"]
             if (datetime.fromisoformat(d["exit_bar_ts"])
                 - datetime.fromisoformat(d["entry_bar_ts"])).days == 3]
    assert trips, "the aligned spike fixture must produce a 3-day hold"
    fin_by_id = {e["decision_id"]: e["financing_adjustment_usd"]
                 for e in out["financing_events"]}
    dec = trips[0]
    hold_days = 3
    base, quote = F.PAIR_AREAS[dec["pair"]]
    diff_decimal = (RATES[base] - RATES[quote]) / 100.0     # hand-computed
    expected = dec["side"] * 10000 * diff_decimal * hold_days / 365.0
    got = fin_by_id[dec["decision_id"]]
    assert got == pytest.approx(expected, abs=1e-12)
    # Weekend accrual days carry Friday's decision-instant differential (all
    # three accrual days equal here), so the frozen formula is exact.
    booked, _specs, dual = R.book_trades([dec], {dec["decision_id"]: got})
    # The runner rounds both columns to 10 decimals; the separation equals
    # the carried adjustment to that precision (kernel identity is exact
    # before rounding).
    assert booked[0]["_pnl"] - booked[0]["_price_only"] == pytest.approx(got, abs=1e-9)
    assert dual[0].financing_adjusted_pnl_usd - dual[0].price_only_pnl_usd \
        == pytest.approx(got, abs=1e-9)
    assert {e["formula"] for e in out["financing_events"]} == {F.FINANCING_FORMULA_ID}


# ---------------------------------------------------------------- #
# 8. deterministic double generation                                  #
# ---------------------------------------------------------------- #
def test_run_arm_byte_identical_double_generation(churn_env):
    for arm in ("anchor", "neighbour", "causal_negative_control"):
        b1 = accounting.canonical_json_bytes(
            F.run_arm(arm, {"h1_dir": churn_env["h1_dir"]}, churn_env["reader"]))
        b2 = accounting.canonical_json_bytes(
            F.run_arm(arm, {"h1_dir": churn_env["h1_dir"]}, churn_env["reader"]))
        assert b1 == b2, f"{arm} must generate byte-identical output"


def test_neighbour_arm_is_same_law_different_estimator(churn_env):
    out_a = F.run_arm("anchor", {"h1_dir": churn_env["h1_dir"]}, churn_env["reader"])
    out_n = F.run_arm("neighbour", {"h1_dir": churn_env["h1_dir"]}, churn_env["reader"])
    assert out_a["decisions"] != out_n["decisions"]   # distinct frozen spec
    assert out_n["meta"]["vol_regime_window"]["neighbour_measure"]
    assert out_n["meta"]["decision_clock"] == "daily"


# ---------------------------------------------------------------- #
# fail-closed behavior                                                #
# ---------------------------------------------------------------- #
def test_fail_closed_on_missing_inputs(churn_env):
    reader = churn_env["reader"]
    with pytest.raises(F.DataBlocked, match="BLOCKED_DATA"):
        F.run_arm("anchor", {}, reader)                    # no h1_dir
    with pytest.raises(F.DataBlocked, match="BLOCKED_DATA"):
        F.run_arm("anchor", {"h1_dir": "/nonexistent-dir-xyz"}, reader)
    with pytest.raises(F.DataBlocked, match="BLOCKED_DATA"):
        F.run_arm("anchor", {"h1_dir": churn_env["h1_dir"]}, None)  # no reader
    empty = tempfile.mkdtemp(prefix="family2_empty_")
    with pytest.raises(F.DataBlocked, match="BLOCKED_DATA"):
        F.run_arm("anchor", {"h1_dir": empty}, reader)     # no pair files
    with pytest.raises(ValueError, match="arm must be one of"):
        F.run_arm("sideways", {"h1_dir": churn_env["h1_dir"]}, reader)
    # A missing macro AREA fails closed through the reader path.
    with pytest.raises(MacroDataBlocked, match="BLOCKED_DATA"):
        PolicyRateReader({}).policy_rate("US", "2024-01-03T21:00:00Z")


def test_meta_contract_and_decision_payload_shape(churn_env):
    out = F.run_arm("anchor", {"h1_dir": churn_env["h1_dir"]}, churn_env["reader"])
    meta = out["meta"]
    assert meta["decision_clock"] == "daily"             # runner-required
    assert meta["proposal_id"] == F.PROPOSAL_ID == "FXFV3-A6-P1"
    assert meta["pair_universe"] == list(F.PAIR_UNIVERSE)
    window = meta["vol_regime_window"]
    assert window["state_block_ny_days"] == 20 and window["baseline_blocks"] == 10
    assert window["warmup_completed_valid_ny_days"] == 220
    assert "LOW iff S_T < B_T" in window["anchor_measure"]
    assert meta["financing"]["disclosed_approximation"].startswith("policy rates")
    for dec in out["decisions"]:
        assert set(dec) == {"decision_id", "pair", "side", "decision_ts",
                            "notional_usd", "entry_bar_ts", "entry_price",
                            "exit_bar_ts", "exit_price", "force_flat"}
        assert dec["notional_usd"] == 10000 and dec["side"] in (1, -1)
        assert dec["decision_ts"].endswith("+00:00")
        ny = datetime.fromisoformat(dec["decision_ts"]).astimezone(NY)
        assert ny.hour == 16 and ny.minute == 0 and ny.weekday() < 5
    assert all(e["formula"] == F.FINANCING_FORMULA_ID for e in out["financing_events"])
    assert {e["decision_id"] for e in out["financing_events"]} == \
        {d["decision_id"] for d in out["decisions"]}


# ---------------------------------------------------------------- #
# 9. schedule-only replay on the REAL snapshot (counts, no PnL)       #
# ---------------------------------------------------------------- #
def test_real_snapshot_schedule_only_replay():
    snapshot = os.environ.get("FXFV3_SNAPSHOT_DIR", DEFAULT_SNAPSHOT)
    manifest_path = os.environ.get("FXFV3_DATA_MANIFEST", DEFAULT_MANIFEST)
    if not (os.path.isdir(snapshot) and os.path.exists(manifest_path)):
        pytest.skip("real snapshot / manifest not staged in this worktree")
    # Digest verification FIRST: 156/156 against the frozen V1 manifest.
    with open(manifest_path, "r", encoding="utf-8") as handle:
        digests = json.load(handle)["digests_exec2"]
    matched = mismatched = missing = 0
    for rel, expected in sorted(digests.items()):
        path = os.path.join(REPO_ROOT, rel)
        if not os.path.exists(path):
            missing += 1
            continue
        with open(path, "rb") as handle:
            observed = hashlib.sha256(handle.read()).hexdigest()
        if observed == expected:
            matched += 1
        else:
            mismatched += 1
    assert (matched, mismatched, missing) == (156, 0, 0)

    counts = F.schedule_counts({"h1_dir": snapshot})
    assert counts["no_pnl"] is True and counts["no_macro_read"] is True
    # A9-F measured weekday decision-bar enumeration, per pair (exact).
    a9f_bars = {"EUR/USD": 1652, "GBP/USD": 1657, "AUD/USD": 1656,
                "NZD/USD": 1656, "USD/JPY": 1653, "USD/CHF": 1655,
                "USD/CAD": 1654}
    for pair, n in a9f_bars.items():
        assert counts["pairs"][pair]["decision_bars_present"] == n, pair
    # Per-arm schedule decision counts clear the frozen floor of 40.
    per_arm = counts["per_arm_decision_counts"]
    assert all(v >= 40 for v in per_arm.values()), per_arm
    # ~220-NY-day activation.  Bar-counting basis (the (n+1)-th weekday
    # decision bar) reproduces the A9-F measured window 2020-12-02..04.
    for pair, info in counts["pairs"].items():
        act = info["bar_counting_activation_221st_bar"][:10]
        assert act in ("2020-12-02", "2020-12-03", "2020-12-04"), (pair, act)
        # Strict valid-day basis (fail-closed on early missing decision
        # bars): disclosed offset of a few NY-days, still December 2020.
        first = info["first_schedule_decision"][:10]
        assert "2020-12-02" <= first <= "2020-12-20", (pair, first)
        assert info["schedule_decision_days"] >= 1000


# ---------------------------------------------- benchmark treatment (V3-I H1)
def test_benchmark_treatment_270d_lag_removes_fresh_information(churn_env):
    # constant vintages: the lag is invisible -> the benchmark IS the anchor
    # law (identical schedule and sides); only ids, arm_id and the lag meta
    # distinguish it
    out_a = F.run_arm("anchor", {"h1_dir": churn_env["h1_dir"]}, churn_env["reader"])
    out_b = F.run_arm("benchmark_treatment", {"h1_dir": churn_env["h1_dir"]},
                      churn_env["reader"])
    assert F.BENCHMARK_ARM == "benchmark_treatment" and F.BENCHMARK_LAG_DAYS == 270
    assert out_b["meta"]["arm_id"] == "FXFV3-A6-P1-bench"
    assert out_b["meta"]["benchmark_treatment"]["lag_days"] == 270
    assert all("-BN-" in d["decision_id"] for d in out_b["decisions"])
    sides_a = {(d["pair"], d["decision_ts"]): d["side"] for d in out_a["decisions"]}
    sides_b = {(d["pair"], d["decision_ts"]): d["side"] for d in out_b["decisions"]}
    assert sides_a and sides_a == sides_b
    _trades, _adj, formula = R.validate_decisions(out_b["decisions"],
                                                  out_b["financing_events"])
    assert formula == F.FINANCING_FORMULA_ID

    # fresh-information removal: the US rate drops 5.25 -> 1.00 effective
    # 2025-06-02 (owner-captured 20:00Z that day).  The anchor's 2025-06-13
    # decisions read the NEW rate; the benchmark reads T-270d (2024-09-16),
    # i.e. the OLD one, so the (X,US)-driven sides flip while the vol gate
    # (price history only) keeps the schedule shape identical.
    tmp2 = tempfile.mkdtemp(prefix="family2_bench_")
    specs = {a: [(v, "2024-01-01T00:00:00Z", "2024-01-01T20:00:00Z")]
             for a, v in RATES.items()}
    specs["US"].append((1.00, "2025-06-02T00:00:00Z", "2025-06-02T20:00:00Z"))
    reader2 = reader_from(tmp2, specs)
    out_a2 = F.run_arm("anchor", {"h1_dir": churn_env["h1_dir"]}, reader2)
    out_b2 = F.run_arm("benchmark_treatment", {"h1_dir": churn_env["h1_dir"]},
                       reader2)
    sa = {(d["pair"], d["decision_ts"]): d["side"] for d in out_a2["decisions"]}
    sb = {(d["pair"], d["decision_ts"]): d["side"] for d in out_b2["decisions"]}
    # USD/CHF's own differential is exactly zero under the OLD read (5.25-5.25):
    # the anchor trades it post-change; the benchmark (NO_EVAL at T-270d,
    # never a side-0 decision) cannot
    assert ("USD/CHF", "2025-06-13T20:00:00+00:00") in sa
    assert ("USD/CHF", "2025-06-13T20:00:00+00:00") not in sb
    # GBP/USD flips: anchor reads 5.00-1.00 = +4.00 -> +1; benchmark reads
    # the lagged vintage 5.00-5.25 = -0.25 -> -1
    key = ("GBP/USD", "2025-06-13T20:00:00+00:00")
    assert sa[key] == 1 and sb[key] == -1
    # EUR/USD and AUD/USD flip the same way; USD/CAD flips sign the other
    # direction; USD/JPY and NZD/USD keep their sign (differential stays
    # positive under both reads) -> exactly 4 shared-key side flips
    differing = {k for k in sa if k in sb and sa[k] != sb[k]}
    assert {k[0] for k in differing} == {"EUR/USD", "GBP/USD", "AUD/USD",
                                         "USD/CAD"}
    assert all(k[1] == "2025-06-13T20:00:00+00:00" for k in differing)
