#!/usr/bin/env python
"""FOREX-FREE-V3 family1 (FXFV3-A5-P1) tests.

Every expected number is a hand-computed literal pinned against tiny
synthetic H1/vintage fixtures.  NO network, NO real scored PnL anywhere.
Test 9 runs a SCHEDULE-ONLY pass over the real frozen price snapshot
(gitignored copy under data_raw/forex_free_v1) with a DISCLOSED synthetic
macro stub: decision/fill/skip counts only, no PnL, runner-validated.
"""
import json
import os
import tempfile
from datetime import date, datetime, timedelta, timezone

import pytest

from research.assets.forex_free_v3 import family1 as F
from research.assets.forex_free_v3 import scored_runner as R
from research.assets.forex_free_v3 import accounting
from research.assets.forex_free_v3.macro_reader import MacroDataBlocked, PolicyRateReader

UTC = timezone.utc
_NY = F._NY

REAL_MANIFEST = ("/Users/hoangminhlong/my-quantitative/.worktrees/forex-free-v2/"
                 "integration/research/control/forex_free_v1_run/staged_data_manifest.json")
REAL_DATA_DIR = os.path.abspath(os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data_raw"))


# ---------------------------------------------------------------- helpers
def _utc(y, mo, d, h, mi=0):
    return datetime(y, mo, d, h, mi, tzinfo=UTC)


def _ny_1600(day: date) -> datetime:
    """The 16:00 America/New_York open instant of `day` as UTC."""
    return datetime(day.year, day.month, day.day, 16, 0, tzinfo=_NY).astimezone(UTC)


def _weekdays(start: date, end: date):
    out, cur = [], start
    while cur <= end:
        if cur.weekday() < 5:
            out.append(cur)
        cur += timedelta(days=1)
    return out


def _write_windows(tmp, pair, bars):
    """Write canonical TwelveData-style H1 window files (td_loader schema).
    `bars`: iterable of (open_utc, open, high, low, close)."""
    tag = pair.replace("/", "")
    rows = [{"datetime": ts.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S"),
             "open": f"{o:.5f}", "high": f"{h:.5f}",
             "low": f"{lo:.5f}", "close": f"{c:.5f}"}
            for ts, o, h, lo, c in bars]
    path = os.path.join(tmp, f"{tag}_1h_2020-01-01_a.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"meta": {"symbol": pair, "interval": "1h"},
                   "values": rows, "status": "ok"}, handle)
    return path


def _vintage(area, value_pct, effective_day, avail_iso):
    return {"source_id": "BIS_CBPOL", "dataset_id": "WS_CBPOL",
            "entity_id": area, "field": "policy_rate", "value": value_pct,
            "unit": "percent_per_annum",
            "event_time_utc": f"{effective_day}T00:00:00Z",
            "available_time_utc": avail_iso,
            "effective_time_utc": f"{effective_day}T00:00:00Z",
            "vintage_time_utc": avail_iso,
            "retrieved_time_utc": "2026-09-01T00:00:00Z",
            "raw_path": "bis/cbol/x.json", "raw_sha256": "a" * 64,
            "license_id": "bis-terms-public-v1",
            "entitlement_id": "anonymous-no-key",
            "normalizer_version": "bis-adapter-1.0.0"}


def _write_vintages(tmp, areas_rows):
    paths = {}
    for area, rows in areas_rows.items():
        path = os.path.join(tmp, f"{area}.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump([_vintage(area, v, eff, av) for v, eff, av in rows], handle)
        paths[area] = path
    return PolicyRateReader.from_data_paths({"macro_vintages": paths})


def _daily_closes(start_value, step, n):
    """Deterministic ascending closes; returns (open, close) float pairs
    via the SAME string rounding the window writer uses."""
    closes = [float(f"{start_value + step * i:.5f}") for i in range(n)]
    opens = [float(f"{c - 0.0002:.5f}") for c in closes]
    return opens, closes


def _h1_bars_from_daily(days, opens, closes, decoys=()):
    """One H1 bar per daily decision bar (the 16:00-NY open) plus decoy
    bars at explicitly given UTC instants."""
    out = []
    for day, o, c in zip(days, opens, closes):
        ts = _ny_1600(day)
        hi = max(o, c) + 0.0001
        lo = min(o, c) - 0.0001
        out.append((ts, o, hi, lo, c))
    for ts, px in decoys:
        out.append((ts, px, px + 0.0001, px - 0.0001, px))
    out.sort(key=lambda b: b[0])
    return out


# Aux areas/pairs: constant policy differentials (g == 0 forever) so the
# goldens stay pinned to the EUR/USD and USD/JPY episodes only, while run_arm
# still sees the full frozen 7-pair universe and all 8 rate areas (fail-closed).
_AUX_AREA_VALUES = {"GB": 0.75, "CH": -0.75, "CA": 1.00, "AU": 0.85, "NZ": 1.20,
                    "JP": -0.10}
_AUX_PAIR_STARTS = {"GBP/USD": 1.35, "USD/CHF": 0.91, "USD/CAD": 1.26,
                    "AUD/USD": 0.65, "NZD/USD": 0.60, "USD/JPY": 145.0}


def _write_aux(tmp, step, n_days, first_day, pairs=None):
    """Aux pairs share the same daily grid; their closes are CONSTANT so
    m == 0 exactly (anchor/neighbour flat) regardless of their differential."""
    days = _weekdays(first_day, first_day + timedelta(days=int(n_days * 1.6)))
    days = days[:n_days]
    for pair, start in _AUX_PAIR_STARTS.items():
        if pairs is not None and pair not in pairs:
            continue
        o, c = _daily_closes(start, 0.0, len(days))
        _write_windows(tmp, pair, _h1_bars_from_daily(days, o, c))


def _aux_vintage_rows():
    rows = {}
    for area, value in _AUX_AREA_VALUES.items():
        rows[area] = [(value, "2019-06-01", "2019-06-01T23:59:59Z")]
    return rows


# ------------------------------------------------------- fixture A (goldens)
def _fixture_a(tmp, us_step2_avail="2020-06-01T23:59:59Z"):
    """Weekday 16:00-NY bars 2020-01-30..2020-12-31 for EUR/USD and USD/JPY.
    US policy steps 0.25% -> 1.25% (effective 2020-06-01, availability stamped
    end-of-UTC-day); EMU constant -0.50%; JP constant -0.10%; aux areas const."""
    days = _weekdays(date(2020, 1, 30), date(2020, 12, 31))
    n = len(days)
    eu_o, eu_c = _daily_closes(1.20, 0.001, n)          # ascending -> m > 0
    jp_o, jp_c = _daily_closes(145.0, 0.05, n)          # ascending -> m > 0
    decoys = [(_utc(2020, 6, 1, 19), 1.11), (_utc(2020, 6, 2, 21), 1.12)]
    _write_windows(tmp, "EUR/USD", _h1_bars_from_daily(days, eu_o, eu_c, decoys))
    _write_windows(tmp, "USD/JPY", _h1_bars_from_daily(days, jp_o, jp_c))
    _write_aux(tmp, 0.001, n, days[0],
               pairs={p for p in _AUX_PAIR_STARTS if p != "USD/JPY"})
    reader = _write_vintages(tmp, {
        "US": [(0.25, "2020-01-01", "2020-01-01T23:59:59Z"),
               (1.25, "2020-06-01", us_step2_avail)],
        "EMU": [(-0.50, "2020-01-01", "2020-01-01T23:59:59Z")],
        **_aux_vintage_rows(),
    })
    data_paths = {"price_h1_dir": str(tmp),
                  "macro_vintages": {a: os.path.join(tmp, f"{a}.json")
                                     for a in ("US", "EMU", "JP", *_AUX_AREA_VALUES)}}
    return data_paths, reader


# ------------------------------------------------------- fixture B (fills)
def _fixture_b(tmp, truncate_at=None):
    """EUR/USD focus, weekday 16:00-NY bars 2021-03-01..2021-12-31 (full
    universe present with constant aux differentials).  US steps 0.25% ->
    1.25% effective 2021-06-16, availability stamped 2021-06-16T23:59:59Z, so
    the FIRST decision reading the new rate is Friday 2021-06-18 (P): the
    g = d(t) - d(t-63) sign window opens there and the g == 0 exit lands 63
    bars later, again a Friday, filling Monday."""
    days = _weekdays(date(2021, 3, 1), date(2021, 12, 31))
    if truncate_at is not None:
        days = [d for d in days if d <= truncate_at]
    n = len(days)
    eu_o, eu_c = _daily_closes(1.18, 0.0005, n)
    _write_windows(tmp, "EUR/USD", _h1_bars_from_daily(days, eu_o, eu_c))
    _write_aux(tmp, 0.0005, n, days[0])
    reader = _write_vintages(tmp, {
        "US": [(0.25, "2021-01-01", "2021-01-01T23:59:59Z"),
               (1.25, "2021-06-17", "2021-06-17T23:59:59Z")],
        "EMU": [(-0.50, "2021-01-01", "2021-01-01T23:59:59Z")],
        **_aux_vintage_rows(),
    })
    data_paths = {"price_h1_dir": str(tmp),
                  "macro_vintages": {a: os.path.join(tmp, f"{a}.json")
                                     for a in ("US", "EMU", *_AUX_AREA_VALUES)}}
    return data_paths, reader, days


# ---------------------------------------------------- 1. feature goldens
def test_feature_goldens_differential_drift_and_momentum():
    with tempfile.TemporaryDirectory() as tmp:
        data_paths, reader = _fixture_a(tmp)
        eu_days = _weekdays(date(2020, 1, 30), date(2020, 12, 31))
        daily = F.daily_decision_bars(F.load_pair_h1_bars("EUR/USD", str(tmp)))
        assert len(daily) == len(eu_days)
        # DST: 2020-01-30 is EST -> 21:00Z; from 2020-03-09 (EDT) -> 20:00Z
        assert daily[0][0] == _utc(2020, 1, 30, 21)
        assert daily[63][0] == _utc(2020, 4, 28, 20)     # warmup end bar
        states = F.pair_state_series("EUR/USD", daily, reader, "anchor")
        # bar 20: momentum cannot exist (i < 21) -> void, fail-closed
        assert states[20]["m"] is None and states[20]["state"] is None
        # bar 62: m exists but the 63d drift cannot -> void
        assert states[62]["m"] is not None and states[62]["g"] is None
        assert states[62]["state"] is None
        # bar 63 = 2020-04-29: first evaluable bar; g = d(t) - d(t-63) = 0 exactly
        assert states[63]["ts"] == _utc(2020, 4, 28, 20)
        m63 = (1.20 + 0.001 * 63) / (1.20 + 0.001 * 42) - 1.0      # 0.021/1.242
        assert states[63]["m"] == pytest.approx(m63, rel=1e-9)
        assert states[63]["d"] == pytest.approx(-0.0075, abs=1e-12)
        assert states[63]["g"] == 0.0
        assert states[63]["gate"] == "flat" and states[63]["state"] == 0
        # availability lag: the 2020-06-01 20:00Z decision (bar 87) still reads
        # the OLD US rate (availability stamp 2020-06-01T23:59:59Z > 20:00Z)
        assert states[87]["ts"] == _utc(2020, 6, 1, 20)
        assert states[87]["d"] == pytest.approx(-0.0075, abs=1e-12)
        # bar 88 = 2020-06-02: first decision strictly after the stamp day.
        # hand-computed: d = -0.50% - 1.25% = -1.75% = -0.0175;
        # g = -0.0175 - (-0.0075) = -0.01; m = 0.021/1.267 > 0 -> DISAGREE
        assert states[88]["ts"] == _utc(2020, 6, 2, 20)
        assert states[88]["d"] == pytest.approx(-0.0175, abs=1e-12)
        assert states[88]["g"] == pytest.approx(-0.01, abs=1e-12)
        m88 = (1.20 + 0.001 * 88) / (1.20 + 0.001 * 67) - 1.0      # 0.021/1.267
        assert states[88]["m"] == pytest.approx(m88, rel=1e-9)
        assert states[88]["gate"] == "flat" and states[88]["state"] == 0
        # USD/JPY same bar: d = 1.25% - (-0.10%) = 1.35% = 0.0135;
        # g = 0.0135 - 0.0035 = +0.01; m > 0 -> AGREE -> long gate
        jp_daily = F.daily_decision_bars(F.load_pair_h1_bars("USD/JPY", str(tmp)))
        jp_states = F.pair_state_series("USD/JPY", jp_daily, reader, "anchor")
        assert jp_states[88]["d"] == pytest.approx(0.0135, abs=1e-12)
        assert jp_states[88]["g"] == pytest.approx(0.01, abs=1e-12)
        assert jp_states[88]["gate"] == "long" and jp_states[88]["state"] == 1
        # 63 bars later (2020-08-28) both reads see the same rows -> g == 0 exact
        assert states[151]["ts"] == _utc(2020, 8, 28, 20)
        assert states[151]["g"] == 0.0 and states[151]["gate"] == "flat"
        # the anchor book: exactly ONE round trip (the USD/JPY agreement episode)
        out = F.run_arm("anchor", data_paths, reader)
        assert len(out["decisions"]) == 1
        dec = out["decisions"][0]
        assert dec["pair"] == "USD/JPY" and dec["side"] == 1
        assert dec["decision_ts"] == "2020-06-02T20:00:00+00:00"
        assert dec["entry_bar_ts"] == "2020-06-03T20:00:00+00:00"
        assert dec["exit_bar_ts"] == "2020-08-31T20:00:00+00:00"  # Mon after Fri 08-28
        assert dec["force_flat"] is False
        # entry fill = OPEN of the next existing daily bar (bar 89); exit fill
        # = OPEN of bar 152; same string rounding as the window writer
        jp_o, jp_c = _daily_closes(145.0, 0.05, len(eu_days))
        assert dec["entry_price"] == jp_o[89]
        assert dec["exit_price"] == jp_o[152]
        # financing: held calendar days 2020-06-04..2020-08-31 = 89 day-starts,
        # each reading d = +0.0135: 10000 * 89 * 0.0135 / 365 = 32.9178082192
        ev = out["financing_events"][0]
        assert ev["decision_id"] == dec["decision_id"]
        assert ev["formula"] == "V3_FROZEN_POLICY_RATE_CARRY"
        assert ev["financing_adjustment_usd"] == pytest.approx(32.9178082192, abs=5e-10)
        assert out["meta"]["decision_clock"] == "daily"
        assert out["meta"]["schedule"]["total"]["n_force_flats"] == 0


# ------------------------- 2. PIT / no-lookahead mutation (regression pin)
def test_pit_mutation_moves_gate_to_not_eligible():
    with tempfile.TemporaryDirectory() as tmp:
        data_paths, reader = _fixture_a(tmp)
        base = F.run_arm("anchor", data_paths, reader)
        assert len(base["decisions"]) == 1                 # the golden book
        # MUTATE: push the second US vintage's availability past 2020-06-02
        mutated_dir = os.path.join(tmp, "mutated")
        os.makedirs(mutated_dir)
        data_paths2, reader2 = _fixture_a(mutated_dir, us_step2_avail="2020-07-01T23:59:59Z")
        daily = F.daily_decision_bars(F.load_pair_h1_bars("EUR/USD", data_paths2["price_h1_dir"]))
        states = F.pair_state_series("EUR/USD", daily, reader2, "anchor")
        # the 2020-06-02 decision now CANNOT see the new vintage: d stays the
        # old value and g collapses to exactly 0 -> gate NOT eligible
        assert states[88]["d"] == pytest.approx(-0.0075, abs=1e-12)
        assert states[88]["g"] == 0.0
        assert states[88]["gate"] == "flat" and states[88]["state"] == 0
        jp_daily = F.daily_decision_bars(F.load_pair_h1_bars("USD/JPY", data_paths2["price_h1_dir"]))
        jp_states = F.pair_state_series("USD/JPY", jp_daily, reader2, "anchor")
        assert jp_states[88]["g"] == 0.0 and jp_states[88]["gate"] == "flat"
        out2 = F.run_arm("anchor", data_paths2, reader2)
        # the agreement episode moved with the lag: the 2020-06-02 decision is
        # voided and the JPY entry now happens only after the pushed stamp
        assert [d["decision_ts"] for d in out2["decisions"] if d["pair"] == "USD/JPY"] \
            == ["2020-07-02T20:00:00+00:00"]
        assert out2["decisions"] != base["decisions"]      # the lag is observable


# ----------------------------------- 3. next-session fill / missing next bar
def test_next_session_fill_and_missing_next_bar_skip():
    with tempfile.TemporaryDirectory() as tmp:
        data_paths, reader, days = _fixture_b(tmp)
        out = F.run_arm("causal_negative_control", data_paths, reader)
        decs = [d for d in out["decisions"] if d["pair"] == "EUR/USD"]
        # every pair shares the moving US leg, so all seven trade this window
        assert len(out["decisions"]) == 7
        # first evaluable g != 0 bar is Friday 2021-06-18 (first bar reading the
        # 06-16 vintage); the SHORT entry fills at the NEXT existing bar.
        assert len(decs) == 1
        dec = decs[0]
        assert dec["side"] == -1
        assert dec["decision_ts"] == "2021-06-18T20:00:00+00:00"
        assert dec["entry_bar_ts"] == "2021-06-21T20:00:00+00:00"   # Monday
        assert datetime.fromisoformat(dec["decision_ts"]).weekday() == 4
        assert datetime.fromisoformat(dec["entry_bar_ts"]).weekday() == 0
        # g returns to exactly 0 when d(t-63) first reads the new vintage:
        # the 63rd weekday after the 2021-06-18 decision is 2021-09-15 (Wed);
        # the exit fills at the NEXT existing bar, 2021-09-16 (Thu).
        assert dec["exit_bar_ts"] == "2021-09-16T20:00:00+00:00"
        assert datetime.fromisoformat(dec["exit_bar_ts"]).weekday() == 3
        runner_validate(out)
        # truncated variant: the go decision IS the last bar -> no next bar
        # exists -> skipped_decision, no round trip, fail-closed (no fill-forward)
        with tempfile.TemporaryDirectory() as tmp2:
            data_paths2, reader2, _ = _fixture_b(tmp2, truncate_at=date(2021, 6, 18))
            out2 = F.run_arm("causal_negative_control", data_paths2, reader2)
            assert out2["decisions"] == []
            skips = out2["meta"]["skipped_decisions"]
            assert len(skips) == 7                     # one per pair, all voided
            eur_skips = [s for s in skips if s["pair"] == "EUR/USD"]
            assert eur_skips[0]["decision_ts"] == "2021-06-18T20:00:00+00:00"
            assert eur_skips[0]["reason"] == "NO_NEXT_BAR_FOR_ENTRY_FILL"
            assert out2["meta"]["schedule"]["total"]["n_skipped_entry_fills"] == 7


def runner_validate(out):
    decisions, adjustments, formula = R.validate_decisions(
        out["decisions"], out["financing_events"])
    if not decisions:
        assert out["financing_events"] == []
        return decisions
    assert formula == "V3_FROZEN_POLICY_RATE_CARRY"
    assert set(adjustments) == {d["decision_id"] for d in decisions}
    return decisions


# --------------------------------------------------- 4. DST decision stamps
def test_dst_decision_stamps_2025_transitions():
    with tempfile.TemporaryDirectory() as tmp:
        days = (_weekdays(date(2025, 2, 17), date(2025, 3, 21))
                + _weekdays(date(2025, 10, 20), date(2025, 11, 14)))
        o, c = _daily_closes(1.08, 0.0003, len(days))
        decoys = [(_utc(2025, 3, 5, 20), 1.09),    # 15:00 NY EST  -> NOT a decision bar
                  (_utc(2025, 3, 12, 21), 1.10),   # 17:00 NY EDT -> NOT a decision bar
                  (_utc(2025, 11, 5, 20), 1.11)]   # 15:00 NY EST -> NOT a decision bar
        _write_windows(tmp, "EUR/USD", _h1_bars_from_daily(days, o, c, decoys))
        daily = F.daily_decision_bars(F.load_pair_h1_bars("EUR/USD", str(tmp)))
        stamps = {ts.astimezone(UTC).isoformat() for ts, _o, _c in daily}
        # US spring-forward 2025-03-09: EST weeks stamp 21:00Z, EDT weeks 20:00Z
        assert "2025-03-07T21:00:00+00:00" in stamps   # Fri before transition
        assert "2025-03-10T20:00:00+00:00" in stamps   # Mon after transition
        # US fall-back 2025-11-02: EDT 20:00Z before, EST 21:00Z after
        assert "2025-10-31T20:00:00+00:00" in stamps
        assert "2025-11-03T21:00:00+00:00" in stamps
        # the decoy instants never become decision bars; only 20:00Z/21:00Z do
        for decoy in ("2025-03-05T20:00:00+00:00", "2025-03-12T21:00:00+00:00",
                      "2025-11-05T20:00:00+00:00"):
            assert decoy not in stamps
        assert {s[11:13] for s in stamps} <= {"20", "21"}
        assert len(stamps) == len(days)


# --------------------------------------- 5. control cannot equal the anchor
def test_control_cannot_equal_anchor():
    with tempfile.TemporaryDirectory() as tmp:
        data_paths, reader = _fixture_a(tmp)
        anchor = F.run_arm("anchor", data_paths, reader)
        control = F.run_arm("causal_negative_control", data_paths, reader)
        # preregistered difference is observable: the control drops the m leg,
        # so it trades EVERY pair whose differential drifts (all share the US
        # leg), including the EUR/USD window the anchor must skip (m > 0 there)
        assert anchor["decisions"] != control["decisions"]
        assert {d["pair"] for d in anchor["decisions"]} == {"USD/JPY"}
        assert "EUR/USD" in {d["pair"] for d in control["decisions"]}
        assert {d["pair"] for d in control["decisions"]} == set(F.PAIRS)
        assert control["decisions"][0]["side"] == -1          # EUR/USD short
        runner_validate(control)
        neighbour = F.run_arm("neighbour", data_paths, reader)
        # neighbour needs 252 eligible daily reads -> void until bar 251; on
        # this fixture the trailing median has converged to the current level
        # by then, so the level gap is identically 0 -> flat (never trades).
        # Its schedule is nonetheless evaluated and distinct from the anchor's.
        assert neighbour["meta"]["arm_id"] == "FXFV3-A5-P1-neigh"
        assert neighbour["decisions"] != anchor["decisions"]
        daily_eu = F.daily_decision_bars(F.load_pair_h1_bars("EUR/USD", str(tmp)))
        nb_states = F.pair_state_series("EUR/USD", daily_eu, reader, "neighbour")
        assert len(daily_eu) < 252                        # 252 reads never available
        assert nb_states[-1]["state"] is None             # void to the last bar
        assert neighbour["meta"]["schedule"]["total"]["n_void_bars"] > 0
        with pytest.raises(ValueError):
            F.run_arm("bogus_arm", data_paths, reader)


# ------------------------------------------ 6. force-flat at a fold boundary
def test_force_flat_at_fold_boundary():
    with tempfile.TemporaryDirectory() as tmp:
        # grid spanning the 2022-05-01 internal boundary; US steps 2022-02-01
        # so the control's g = -0.01 window is open across the boundary
        days = _weekdays(date(2021, 12, 1), date(2022, 5, 10))
        n = len(days)
        o, c = _daily_closes(1.10, 0.0004, n)
        _write_windows(tmp, "EUR/USD", _h1_bars_from_daily(days, o, c))
        _write_aux(tmp, 0.0004, n, days[0])
        reader = _write_vintages(tmp, {
            "US": [(0.25, "2021-06-01", "2021-06-01T23:59:59Z"),
                   (1.25, "2022-02-01", "2022-02-01T23:59:59Z")],
            "EMU": [(-0.50, "2021-06-01", "2021-06-01T23:59:59Z")],
            **_aux_vintage_rows(),
        })
        data_paths = {"price_h1_dir": str(tmp),
                      "macro_vintages": {a: os.path.join(tmp, f"{a}.json")
                                         for a in ("US", "EMU", *_AUX_AREA_VALUES)}}
        out = F.run_arm("causal_negative_control", data_paths, reader)
        flats = [d for d in out["decisions"] if d["force_flat"]]
        # every pair holds a control position into the boundary: all 7 are
        # force-flattened; pin the EUR/USD one
        assert len(flats) == 7
        dec = [d for d in flats if d["pair"] == "EUR/USD"][0]
        # the last existing 16:00-NY bar before 2022-05-01T00:00Z is
        # Friday 2022-04-29 (EDT): the position closes AT that bar's open
        assert dec["exit_bar_ts"] == "2022-04-29T20:00:00+00:00"
        assert dec["force_flat"] is True
        assert datetime.fromisoformat(dec["exit_bar_ts"]) < datetime.fromisoformat(
            R.INTERNAL_BOUNDARIES[1])
        # entry is the first evaluable g != 0 bar: the US window opens
        # 2022-02-02, evaluation is possible only after 63 warmup bars,
        # i.e. from 2022-02-28 (the first evaluable bar already sees g = -0.01)
        assert dec["decision_ts"] == "2022-02-28T21:00:00+00:00"
        assert dec["entry_bar_ts"] == "2022-03-01T21:00:00+00:00"
        # no trade spans the boundary; the runner's fold validator agrees
        runner_validate(out)
        for d in out["decisions"]:
            b = datetime.fromisoformat(R.INTERNAL_BOUNDARIES[1])
            assert not (datetime.fromisoformat(d["entry_bar_ts"]) < b
                        <= datetime.fromisoformat(d["exit_bar_ts"]))
        assert out["meta"]["schedule"]["total"]["n_force_flats"] == 7
        # entry suppression at the flatten bar and the bar before it
        assert out["meta"]["schedule"]["total"]["n_entries_suppressed_by_boundary"] >= 1


# ------------------- 7. frozen financing formula + dual-book kernel booking
def test_financing_frozen_formula_three_day_hold_and_dual_book():
    with tempfile.TemporaryDirectory() as tmp:
        data_paths, reader, _days = _fixture_b(tmp)
        # hand-computed 3-calendar-day hold, LONG base, d = -0.0075 constant:
        # entry 2021-06-07T20:00Z, exit 2021-06-10T20:00Z accrues day-starts
        # 06-08, 06-09, 06-10 -> 10000 * (-0.0225) / 365 = -0.6164383562
        decision = {"side": 1, "notional_usd": 10000,
                    "entry_bar_ts": "2021-06-07T20:00:00+00:00",
                    "exit_bar_ts": "2021-06-10T20:00:00+00:00"}
        adjustment = F.financing_adjustment_usd("EUR/USD", decision, reader)
        assert adjustment == pytest.approx(-0.6164383562, abs=5e-10)
        # mirrored short book flips the sign, nothing else
        short_decision = dict(decision, side=-1)
        assert F.financing_adjustment_usd("EUR/USD", short_decision, reader) \
            == pytest.approx(0.6164383562, abs=5e-10)
        # weekend calendar days accrue (Fri->Mon hold = 3 day-starts)
        weekend = dict(decision, entry_bar_ts="2021-06-11T20:00:00+00:00",
                       exit_bar_ts="2021-06-14T20:00:00+00:00")
        assert F.financing_adjustment_usd("EUR/USD", weekend, reader) \
            == pytest.approx(-0.6164383562, abs=5e-10)
        # dual book through the V3 P1 kernel: price-only vs financing-adjusted
        # differ by EXACTLY the carried term
        specs = [accounting.TradeSpec(
            trade_id="t1", pair="EUR/USD", side="LONG", notional_usd=10000.0,
            entry_price=1.2100, exit_price=1.2150,
            entry_ts_utc=decision["entry_bar_ts"],
            exit_ts_utc=decision["exit_bar_ts"])]
        dual = accounting.book_dual(specs, financing_adjustment_usd={"t1": adjustment})
        assert dual[0].financing_adjusted_pnl_usd - dual[0].price_only_pnl_usd \
            == pytest.approx(adjustment, abs=1e-9)
        # and the emitted schedule carries the same formula per event
        b2 = os.path.join(tmp, "schedule_fixture")
        os.makedirs(b2)
        data_paths, reader_b, _days_b = _fixture_b(b2)
        out = F.run_arm("causal_negative_control", data_paths, reader_b)
        assert {ev["formula"] for ev in out["financing_events"]} \
            == {"V3_FROZEN_POLICY_RATE_CARRY"}
        assert len(out["financing_events"]) == len(out["decisions"])


# --------------------------------------------- 8. deterministic double generation
def test_run_arm_deterministic_double_generation():
    with tempfile.TemporaryDirectory() as tmp:
        data_paths, reader = _fixture_a(tmp)
        for arm in ("anchor", "neighbour", "causal_negative_control"):
            first = F.run_arm(arm, data_paths, reader)
            second = F.run_arm(arm, data_paths, reader)
            assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)
            # decision ids are unique and the stream passes the runner contract
            runner_validate(first)


# ------------------------------------------ macro fail-closed (BLOCKED_DATA)
def test_missing_vintage_area_fails_closed():
    with tempfile.TemporaryDirectory() as tmp:
        data_paths, _reader = _fixture_a(tmp)
        broken = dict(data_paths)
        broken["macro_vintages"] = {k: v for k, v in data_paths["macro_vintages"].items()
                                    if k != "JP"}
        with pytest.raises(MacroDataBlocked, match="BLOCKED_DATA"):
            F.run_arm("anchor", broken, None)
        with pytest.raises(RuntimeError, match="BLOCKED_DATA"):
            F.run_arm("anchor", {"macro_vintages": data_paths["macro_vintages"]}, None)


# ------------------------- 9. schedule-only pass over the REAL price snapshot
def test_real_snapshot_schedule_only():
    price_dir = os.path.join(REAL_DATA_DIR, "forex_free_v1")
    if not os.path.isdir(price_dir):
        pytest.skip("real snapshot not copied into this worktree (gitignored)")
    manifest = None
    if os.path.exists(REAL_MANIFEST):
        with open(REAL_MANIFEST, "r", encoding="utf-8") as handle:
            manifest = json.load(handle)
        import hashlib
        bad = missing = 0
        for rel, expected in manifest["digests_exec2"].items():
            path = os.path.join(os.path.dirname(REAL_DATA_DIR), rel)
            if not os.path.exists(path):
                missing += 1
            elif hashlib.sha256(open(path, "rb").read()).hexdigest() != expected:
                bad += 1
        assert (bad, missing) == (0, 0), "staged snapshot digests must match 156/156"

    with tempfile.TemporaryDirectory() as tmp:
        # DISCLOSED synthetic schedule stub: real BIS vintages are
        # NOT_PROVEN_ON_LIVE_FETCH (blocked at the Q data-hash gate), so the
        # macro gate runs on a deterministic oscillating stub (steps every
        # 9 calendar days through a 4-phase cycle per area; cadence chosen
        # only to exercise go/no-go churn, never scored).  This measures the
        # real daily 16:00-NY schedule (decision/fill/skip mechanics) only.
        areas = {"US": 1.50, "EMU": -0.40, "GB": 0.75, "JP": -0.10,
                 "CH": -0.75, "CA": 1.00, "AU": 0.85, "NZ": 1.20}
        paths = {}
        for area, base in areas.items():
            rows = []
            day = date(2019, 1, 7)
            k = 0
            while day <= date(2026, 8, 31):
                value = round(base + 0.25 * ((k % 4) - 1.5), 4)
                rows.append((value, day.isoformat(), f"{day.isoformat()}T23:59:59Z"))
                day += timedelta(days=9)
                k += 1
            path = os.path.join(tmp, f"{area}.json")
            with open(path, "w", encoding="utf-8") as handle:
                json.dump([_vintage(area, v, eff, av) for v, eff, av in rows], handle)
            paths[area] = path
        reader = PolicyRateReader.from_data_paths({"macro_vintages": paths})
        data_paths = {"price_h1_dir": price_dir,
                      "macro_vintages": paths}

        counts = {}
        for arm in ("anchor", "neighbour", "causal_negative_control"):
            out = F.run_arm(arm, data_paths, reader)
            runner_validate(out)                       # frozen fail-closed rules
            total = out["meta"]["schedule"]["total"]
            # schedule-only: no PnL fields may exist anywhere on a decision
            for dec in out["decisions"]:
                assert not any("pnl" in key.lower() for key in dec)
                assert dec["notional_usd"] == 10000
            # frozen sample floor (baseline_invariants v3_sample_floors)
            assert len(out["decisions"]) >= 40, (arm, total)
            assert total["n_evaluated_bars"] >= 40 * 7
            assert total["n_round_trips"] == len(out["decisions"])
            # DST: every decision/fill stamp is a 20:00Z or 21:00Z 16:00-NY bar
            for dec in out["decisions"]:
                for key in ("decision_ts", "entry_bar_ts", "exit_bar_ts"):
                    t = datetime.fromisoformat(dec[key])
                    assert t.hour in (20, 21) and t.minute == 0
                    assert R._is_ny_1600(t)
            # weekday coverage Mon..Fri (spec direction/weekday checks)
            seen_weekdays = {datetime.fromisoformat(d["decision_ts"]).weekday()
                             for d in out["decisions"]}
            assert seen_weekdays == {0, 1, 2, 3, 4}
            counts[arm] = {"decisions": len(out["decisions"]),
                           "evaluated_bars": total["n_evaluated_bars"],
                           "void_bars": total["n_void_bars"],
                           "skipped_entry_fills": total["n_skipped_entry_fills"],
                           "skipped_exit_fills": total["n_skipped_exit_fills"],
                           "force_flats": total["n_force_flats"]}

        # warmup feasibility: exactly the first 63 daily bars are void, the
        # first evaluable bar falls in the ~2020-05-01 activation window
        daily = F.daily_decision_bars(F.load_pair_h1_bars("EUR/USD", price_dir))
        states = F.pair_state_series("EUR/USD", daily, reader, "anchor")
        assert states[62]["state"] is None and states[63]["state"] is not None
        first_evaluable = states[63]["ts"].date()
        assert date(2020, 4, 15) <= first_evaluable <= date(2020, 5, 15)
        counts["first_evaluable_bar_utc"] = first_evaluable.isoformat()
        counts["eurusd_daily_bars"] = len(daily)
