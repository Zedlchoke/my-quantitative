#!/usr/bin/env python
"""FOREX-FREE-V4 family1 (FXFV4-A6-P1) tests.

Hand-computed synthetic fixtures ONLY: no real snapshots, no network, no
scored PnL anywhere.  Every expected number is a hand-derived literal or a
closed form pinned against tiny synthetic H1/vintage fixtures.  The frozen
V3 kernel (scored_runner validator, accounting cost/stress kernel) is used
read-only to prove the module plugs into the inherited architecture.
"""
import json
import math
import os
import statistics
import tempfile
from datetime import date, datetime, timedelta, timezone

import pytest

from research.assets.forex_free_v4 import family1 as F
from research.assets.forex_free_v3 import accounting
from research.assets.forex_free_v3 import scored_runner as R
from research.assets.forex_free_v3.macro_reader import PolicyRateReader

UTC = timezone.utc
_NY = F._NY

# b = the fixture's daily bloc step: an alternating +/-1.001/0.999 close
# pattern gives signed log returns of exactly +/-b per trigger pair.
_B = math.log(1.001 / 0.999)
# z of the golden event day: S = -3b against a window of 30*(+b) + 30*(-b):
# mean 0, sample std = b*sqrt(60/59)  ->  z = -3*sqrt(59/60).
_Z_GOLDEN = -3.0 * math.sqrt(59.0 / 60.0)


# ---------------------------------------------------------------- helpers
def _utc(y, mo, d, h, mi=0):
    return datetime(y, mo, d, h, mi, tzinfo=UTC)


def _ny_1600(day: date) -> datetime:
    """The 16:00 America/New_York open instant of `day` as UTC (DST-aware)."""
    return datetime(day.year, day.month, day.day, 16, 0, tzinfo=_NY).astimezone(UTC)


def _weekday_dates(start: date, n: int):
    out, cur = [], start
    while len(out) < n:
        if cur.weekday() < 5:
            out.append(cur)
        cur += timedelta(days=1)
    return out


_DAY_HOURS = {0: range(24), 1: range(24), 2: range(24), 3: range(24),
              4: range(17)}  # Mon-Thu 24 bars, Fri 17 bars (00:00..16:00 NY)


def _pair_bars(days, closes, drop_hours=None):
    """Full synthetic H1 bars for one pair over `days` (Mon-Fri NY-days).

    Every bar of a day carries the day's close as its price (only the
    16:00-NY close feeds the trigger; contiguity needs bar existence).
    `drop_hours`: {day_index: [ny_hour, ...] or "ALL"} bars to DELETE
    (missing-data fixtures)."""
    bars = []
    for k, day in enumerate(days):
        for hour in _DAY_HOURS[day.weekday()]:
            if drop_hours and k in drop_hours:
                marked = drop_hours[k]
                if marked == "ALL" or hour in marked:
                    continue
            c = float(closes[k])
            ts = datetime(day.year, day.month, day.day, hour, 0,
                          tzinfo=_NY).astimezone(UTC)
            bars.append((ts, c, c * 1.0001, c * 0.9999, c))
    bars.sort(key=lambda b: b[0])
    return bars


def _write_windows(tmp, pair, bars):
    tag = pair.replace("/", "")
    rows = [{"datetime": ts.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S"),
             "open": f"{o:.12f}", "high": f"{h:.12f}",
             "low": f"{lo:.12f}", "close": f"{c:.12f}"}
            for ts, o, h, lo, c in bars]
    path = os.path.join(tmp, f"{tag}_1h_2020-01-01_a.json")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"meta": {"symbol": pair, "interval": "1h"},
                   "values": rows, "status": "ok"}, handle)
    return path


def _pattern(base, k, invert=False):
    """Alternating close pattern: +0.1% / -0.1% of base (phase-invertible)."""
    up = (k % 2 == 0)
    if invert:
        up = not up
    return base * (1.001 if up else 0.999)


# Per-pair fixture spec: base price, alternating pattern on/off, USD/CAD-style
# phase inversion, and optional injected event days {k: signed_mult} where the
# pair's SIGNED bloc return is forced to exactly -signed_mult * b.
_DEFAULT_SPEC = {
    "AUD/USD": dict(base=1.00, alt=True),
    "NZD/USD": dict(base=0.65, alt=True),
    "USD/CAD": dict(base=1.26, alt=True, invert=True),
    "USD/JPY": dict(base=145.0, alt=False),
    "USD/CHF": dict(base=0.88, alt=False),
    "EUR/USD": dict(base=1.08, alt=False),
    "GBP/USD": dict(base=1.27, alt=False),
}


def _closes(spec, n, drops=None, drop_hours=None):
    drops = drops or {}
    out = []
    for k in range(n):
        if k in drops:
            prev = out[-1]
            # drops[k] is the SIGNED bloc multiplier: signed = -mult * b, so a
            # sign-(+1) pair closes at prev*exp(-mult*b) and a sign-(-1) pair
            # (USD/CAD, the invert spec) at prev*exp(+mult*b).
            mult = -drops[k] * (-1.0 if spec.get("invert") else 1.0)
            out.append(prev * math.exp(mult * _B))
        else:
            out.append(_pattern(spec["base"], k, spec.get("invert", False))
                       if spec.get("alt") else spec["base"])
    return out


def _build_fixture(tmp, days, spec_overrides=None, drop_hours=None,
                   write_pairs=None):
    """Write the full synthetic snapshot for `days`; returns data_paths plus
    a reader whose constant policy rates give simple hand financing values."""
    drop_hours = drop_hours or {}
    spec = dict(_DEFAULT_SPEC)
    if spec_overrides:
        for p, o in spec_overrides.items():
            cur = dict(spec[p])
            cur.update(o)
            spec[p] = cur
    for pair, pspec in spec.items():
        if write_pairs is not None and pair not in write_pairs:
            continue
        closes = _closes(pspec, len(days), drops=pspec.get("drops"),
                         drop_hours=drop_hours.get(pair))
        bars = _pair_bars(days, closes, drop_hours=drop_hours.get(pair))
        _write_windows(tmp, pair, bars)
    rates = {"US": 1.00, "AU": 2.00, "NZ": 2.00, "CA": 1.50,
             "JP": -0.10, "CH": -0.25, "GB": 0.75, "EMU": -0.50}
    paths = {}
    for area, value in rates.items():
        path = os.path.join(tmp, f"{area}.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump([{"source_id": "BIS_CBPOL", "dataset_id": "WS_CBPOL",
                        "entity_id": area, "field": "policy_rate",
                        "value": value, "unit": "percent_per_annum",
                        "event_time_utc": "2019-01-01T00:00:00Z",
                        "available_time_utc": "2019-01-01T23:59:59Z",
                        "effective_time_utc": "2019-01-01T00:00:00Z",
                        "vintage_time_utc": "2019-01-01T23:59:59Z",
                        "retrieved_time_utc": "2026-09-01T00:00:00Z",
                        "raw_path": "bis/cbol/x.json", "raw_sha256": "a" * 64,
                        "license_id": "bis-terms-public-v1",
                        "entitlement_id": "anonymous-no-key",
                        "normalizer_version": "bis-adapter-1.0.0"}], handle)
        paths[area] = path
    reader = PolicyRateReader.from_data_paths({"macro_vintages": paths})
    data_paths = {"price_h1_dir": str(tmp), "macro_vintages": paths}
    return data_paths, reader


GOLDEN_START = date(2024, 1, 1)  # Monday; k=61 -> 2024-03-26 (Tue, EDT)


def _golden(tmp, n_days=69):
    """The golden anchor fixture: alternating +/-b bloc closes; the ONLY
    injected risk-off event is at valid-day index k=61 (S = -3b, the first
    day with an evaluable 60-day window); no other day fires (hand-checked:
    post-event windows hold z in [-0.904, +0.963])."""
    days = _weekday_dates(GOLDEN_START, n_days)
    return _build_fixture(tmp, days,
                          spec_overrides={p: {"drops": {61: 3.0}}
                                          for p in ("AUD/USD", "NZD/USD",
                                                    "USD/CAD")})


def _k_day(k, start=GOLDEN_START):
    return _weekday_dates(start, k + 1)[k]


def _drop_one_spec(tmp, leg):
    """Anchor fixture with one leg excluded, per packet drop_one_design."""
    days = _weekday_dates(GOLDEN_START, 69)
    data_paths, reader = _build_fixture(
        tmp, days, spec_overrides={p: {"drops": {61: 3.0}}
                                   for p in ("AUD/USD", "NZD/USD", "USD/CAD")})
    return F.drop_one_leg_schedule(leg, data_paths, reader), data_paths, reader


# --------------------------------------------------- 1. feature goldens
def test_bloc_signed_returns_sign_convention_golden():
    """Frozen sign convention (+AUD, +NZD, -CAD) as daily log returns,
    hand-computed; mean and median bloc strength."""
    ts = _utc(2024, 3, 25, 20)
    prev = {"AUD/USD": (ts, 1.00, 1.00), "NZD/USD": (ts, 0.65, 0.65),
            "USD/CAD": (ts, 1.26, 1.26)}
    day = {"AUD/USD": (ts, 0.99, 0.99), "NZD/USD": (ts, 0.6435, 0.6435),
           "USD/CAD": (ts, 1.2726, 1.2726)}
    r = F.bloc_signed_returns(day, prev, F.TRIGGER_PAIRS, F.TRIGGER_SIGNS)
    assert r["AUD/USD"] == pytest.approx(math.log(0.99), rel=1e-12)
    assert r["NZD/USD"] == pytest.approx(math.log(0.99), rel=1e-12)
    # the -r(USD/CAD) sign: CAD strength +1% reads NEGATIVE like AUD/NZD down
    assert r["USD/CAD"] == pytest.approx(-math.log(1.01), rel=1e-12)
    s_mean = math.fsum([r[p] for p in F.TRIGGER_PAIRS]) / 3.0
    assert s_mean == pytest.approx(
        (2 * math.log(0.99) - math.log(1.01)) / 3.0, rel=1e-12)
    s_median = statistics.median([r[p] for p in F.TRIGGER_PAIRS])
    assert s_median == pytest.approx(math.log(0.99), rel=1e-12)


def test_z_standardize_golden_window_excludes_decision_day():
    """Hand z golden: window = 30*(+b) + 30*(-b) strictly before the day;
    z = -3*sqrt(59/60) on S = -3b.  Warmup and zero-variance -> None."""
    s = [None] + [(_B if k % 2 == 0 else -_B) for k in range(1, 61)] + [-3.0 * _B]
    z = F.z_standardize(s)
    assert z[60] is None                      # only 59 prior values at k=60
    assert z[61] == pytest.approx(_Z_GOLDEN, rel=1e-12)
    # zero-variance window -> NO_EVAL (never a fabricated z)
    z0 = F.z_standardize([1.0] * 61)
    assert z0[60] is None
    # boundary: z exactly -1.0 FIRES (<= semantics frozen)
    win = [float(v) for v in range(1, 61)]
    sd = statistics.stdev(win)
    z1 = F.z_standardize(win + [math.fsum(win) / 60.0 - sd])
    assert z1[60] == pytest.approx(-1.0, abs=1e-12)
    flags = F.event_flags_from_z(z1)
    assert flags[60] is True


def test_feature_golden_event_basket_and_fills():
    """One hand-computed decision window end-to-end: exactly one event day
    (k=61), the frozen 5-leg basket with frozen sides, next-session entry,
    entry+5-session exit, DST-correct stamps, opens as fill prices."""
    with tempfile.TemporaryDirectory() as tmp:
        data_paths, reader = _golden(tmp)
        out = F.run_arm("anchor", data_paths, reader)
        assert len(out["decisions"]) == 5
        dec_ts = _iso_k(61)
        entry_ts = _iso_k(62)
        exit_ts = _iso_k(67)
        sides = {"AUD/USD": -1, "NZD/USD": -1, "USD/CAD": 1,
                 "USD/JPY": -1, "USD/CHF": -1}
        assert out["meta"]["arm_id"] == "FXFV4-A6-P1-anchor"
        for d in out["decisions"]:
            assert d["decision_ts"] == dec_ts
            assert d["entry_bar_ts"] == entry_ts        # next session
            assert d["exit_bar_ts"] == exit_ts          # entry + 5 NY-days
            assert d["side"] == sides[d["pair"]]
            assert d["notional_usd"] == 10000
            assert d["force_flat"] is False
        by_pair = {d["pair"]: d for d in out["decisions"]}
        # hand trigger values at the event day via the module's own surfaces
        days = _weekday_dates(GOLDEN_START, 69)
        assert dec_ts == _ny_1600(days[61]).isoformat()   # EDT week -> 20:00Z
        assert dec_ts == "2024-03-26T20:00:00+00:00"
        assert entry_ts == _ny_1600(days[62]).isoformat()
        assert exit_ts == _ny_1600(days[67]).isoformat()
        aud = F.valid_daily_bars(F.load_pair_h1_bars("AUD/USD", str(tmp)))
        assert aud[61][2] == pytest.approx(1.001 * math.exp(-3.0 * _B), rel=1e-9)
        assert by_pair["AUD/USD"]["entry_price"] == aud[62][1]
        cad = F.valid_daily_bars(F.load_pair_h1_bars("USD/CAD", str(tmp)))
        assert by_pair["USD/CAD"]["exit_price"] == cad[67][1]
        # financing goldens: 7 held calendar day-starts (03-28..04-03), each
        # at the constant as-of differential; frozen formula
        # sign * notional * sum(d) / 365
        d_aud = (2.00 - 1.00) / 100.0
        assert next(e for e in out["financing_events"]
                    if e["decision_id"] == by_pair["AUD/USD"]["decision_id"]
                    )["financing_adjustment_usd"] == pytest.approx(
            -1.0 * 10000 * 7 * d_aud / 365.0, abs=5e-10)
        d_jpy = (1.00 - (-0.10)) / 100.0
        assert next(e for e in out["financing_events"]
                    if e["decision_id"] == by_pair["USD/JPY"]["decision_id"]
                    )["financing_adjustment_usd"] == pytest.approx(
            -1.0 * 10000 * 7 * d_jpy / 365.0, abs=5e-10)
        assert out["meta"]["schedule"]["total"]["n_event_days"] == 1
        assert out["meta"]["schedule"]["total"]["n_trigger_evaluable_days"] == 8


def _iso_k(k, start=GOLDEN_START):
    return _ny_1600(_k_day(k, start)).isoformat()


# ------------------------------------- 2. one-event/one-bar lag (mutation)
def test_no_lookahead_window_and_future_perturbation():
    """No-lookahead mutation pins: (a) the trigger's standardization window
    NEVER includes the decision day (a mutated include-current-day z differs;
    the module matches the hand golden); (b) perturbing every close STRICTLY
    AFTER the event day leaves the schedule byte-identical; (c) every fill is
    strictly after the decision instant and within the 4-day allowance."""
    with tempfile.TemporaryDirectory() as tmp:
        data_paths, reader = _golden(tmp)
        out = F.run_arm("anchor", data_paths, reader)
        assert len(out["decisions"]) == 5
        # (a) window mutation: including S_61 in its own window shifts z far
        # away from the hand golden -> the module used the frozen window.
        s = [None] + [(_B if k % 2 == 0 else -_B) for k in range(1, 61)] \
            + [-3.0 * _B]
        win = [s[i] for i in range(2, 62)]  # MUTATED: includes day 61
        z_mut = (-3.0 * _B - math.fsum(win) / 60.0) / statistics.stdev(win)
        assert z_mut != pytest.approx(_Z_GOLDEN, abs=1e-6)
        # module's own z (hand-check through the public surface)
        trig = F.trigger_day_series(
            {p: F.valid_daily_bars(F.load_pair_h1_bars(p, str(tmp)))
             for p in F.TRIGGER_PAIRS}, F.TRIGGER_PAIRS, F.TRIGGER_SIGNS, "mean")
        z_module = F.z_standardize([d["s"] for d in trig])
        assert z_module[61] == pytest.approx(_Z_GOLDEN, rel=1e-9)
        assert z_module[61] != pytest.approx(z_mut, abs=1e-3)
        # (c) lag discipline on every emitted decision
        for d in out["decisions"]:
            dec = datetime.fromisoformat(d["decision_ts"])
            ent = datetime.fromisoformat(d["entry_bar_ts"])
            ex = datetime.fromisoformat(d["exit_bar_ts"])
            assert ent > dec                      # never same-bar fills
            assert ent - dec <= timedelta(days=4)
            assert ex > ent
        # (b) future perturbation: scale every close strictly AFTER k=61.
        # The SCHEDULE (event day, fill instants, sides, holding) must be
        # identical -- only fill PRICES may move, and only because the
        # entry/exit bars themselves sit in the scaled future (a fill pricing
        # off its own bar's open is the fill convention, not lookahead; the
        # trigger inputs are untouched).
        with tempfile.TemporaryDirectory() as tmp3:
            dp3, reader3 = _golden_scaled_future(tmp3)
            out3 = F.run_arm("anchor", dp3, reader3)
            assert out3["decisions"] != out["decisions"]  # prices did move
            def _sched(decs):
                return [(d["pair"], d["decision_ts"], d["side"],
                         d["entry_bar_ts"], d["exit_bar_ts"], d["force_flat"])
                        for d in decs]
            assert _sched(out3["decisions"]) == _sched(out["decisions"])
            # and the trigger input closes are unchanged
            aud_a = F.valid_daily_bars(F.load_pair_h1_bars("AUD/USD", str(tmp)))
            aud_b = F.valid_daily_bars(
                F.load_pair_h1_bars("AUD/USD", dp3["price_h1_dir"]))
            assert [c[2] for c in aud_a[:62]] == [c[2] for c in aud_b[:62]]


def _golden_scaled_future(tmp):
    """Golden fixture with every close at valid-day index >= 62 scaled 1.3x:
    the decision day's trigger inputs (<= k=61 closes) are untouched."""
    days = _weekday_dates(GOLDEN_START, 69)
    spec = {p: {"drops": {61: 3.0}} for p in ("AUD/USD", "NZD/USD", "USD/CAD")}
    data_paths, reader = _build_fixture(tmp, days, spec_overrides=spec)
    # scale each pair's future bars (k >= 62) in place
    for pair in _DEFAULT_SPEC:
        tag = pair.replace("/", "")
        path = os.path.join(tmp, f"{tag}_1h_2020-01-01_a.json")
        payload = json.load(open(path, encoding="utf-8"))
        for row in payload["values"]:
            ts = datetime.strptime(row["datetime"], "%Y-%m-%d %H:%M:%S") \
                .replace(tzinfo=UTC)
            if ts >= _ny_1600(days[62]):
                for f in ("open", "high", "low", "close"):
                    row[f] = f"{float(row[f]) * 1.3:.12f}"
        json.dump(payload, open(path, "w", encoding="utf-8"))
    return data_paths, reader


# ----------------------------------------------------- 3. DST boundaries
def test_dst_boundary_clock_and_next_session_fills():
    """16:00 America/New_York maps to 21:00Z in EST weeks and 20:00Z in EDT
    weeks (named zone, never fixed offsets); next-session fills across the
    spring-forward and fall-back weekends land on Monday's bar."""
    # zoneinfo goldens around 2025-03-09 (spring forward) and 2025-11-02 (fall back)
    assert _ny_1600(date(2025, 3, 7)) == _utc(2025, 3, 7, 21)   # EST Friday
    assert _ny_1600(date(2025, 3, 10)) == _utc(2025, 3, 10, 20)  # EDT Monday
    assert _ny_1600(date(2025, 10, 31)) == _utc(2025, 10, 31, 20)  # EDT Friday
    assert _ny_1600(date(2025, 11, 3)) == _utc(2025, 11, 3, 21)   # EST Monday
    with tempfile.TemporaryDirectory() as tmp:
        # spring-forward week: Fri 03-07 decision -> Mon 03-10 fill
        days = _weekday_dates(date(2025, 3, 3), 10)
        bars = {leg: F.daily_decision_bars(
            _flat_bars(days, base)) for leg, base in _LEG_BASES.items()}
        sched = F.schedule_legs("arm", [_ny_1600(days[4])], bars)  # Fri
        assert len(sched["decisions"]) == 5
        for d in sched["decisions"]:
            assert d["decision_ts"] == "2025-03-07T21:00:00+00:00"
            assert d["entry_bar_ts"] == "2025-03-10T20:00:00+00:00"
        # fall-back week: Fri 10-31 decision -> Mon 11-03 fill
        days2 = _weekday_dates(date(2025, 10, 27), 10)
        bars2 = {leg: F.daily_decision_bars(
            _flat_bars(days2, base)) for leg, base in _LEG_BASES.items()}
        sched2 = F.schedule_legs("arm", [_ny_1600(days2[4])], bars2)
        for d in sched2["decisions"]:
            assert d["decision_ts"] == "2025-10-31T20:00:00+00:00"
            assert d["entry_bar_ts"] == "2025-11-03T21:00:00+00:00"
        # the module's daily decision bars carry the same DST-aware stamps
        data_paths, reader = _build_fixture(tmp, days)
        daily = F.daily_decision_bars(F.load_pair_h1_bars("EUR/USD", str(tmp)))
        assert daily[4][0] == _utc(2025, 3, 7, 21)
        assert daily[5][0] == _utc(2025, 3, 10, 20)


_LEG_BASES = {"AUD/USD": 1.00, "NZD/USD": 0.65, "USD/CAD": 1.26,
              "USD/JPY": 145.0, "USD/CHF": 0.88}


def _flat_bars(days, base):
    """Constant-price full-day bars (one pair) over `days`."""
    return _pair_bars(days, [base] * len(days))


# --------------------------------------- 4. force-flat at window end
def test_force_flat_at_window_end_no_open_positions():
    """Data ends before the scheduled 5-day exit: every open leg exits at the
    LAST existing bar's open with force_flat=true; no position survives."""
    with tempfile.TemporaryDirectory() as tmp:
        data_paths, reader = _golden(tmp, n_days=64)   # k=0..63
        out = F.run_arm("anchor", data_paths, reader)
        assert len(out["decisions"]) == 5
        last = F.daily_decision_bars(
            F.load_pair_h1_bars("AUD/USD", data_paths["price_h1_dir"]))[-1][0]
        for d in out["decisions"]:
            assert d["force_flat"] is True
            assert d["exit_bar_ts"] == last.isoformat()
            assert d["entry_bar_ts"] == _iso_k(62)
        assert out["meta"]["schedule"]["total"]["n_force_flats"] == 5
        decisions, adjustments, formula = R.validate_decisions(
            out["decisions"], out["financing_events"])
        assert formula == F.FINANCING_FORMULA


# ------------------------------- 5. force-flat at the internal boundary
def test_force_flat_internal_fold_boundary_and_entry_suppression():
    """Fixture spanning the 2022-05-01 boundary: (a) a position whose 5-day
    exit would cross the boundary force-flattens at the last pre-boundary bar
    (2022-04-29, 20:00Z EDT); (b) an entry whose FILL would land on that
    flatten bar is suppressed NO_TRADE (zero-length round trips impossible).
    Weekday map from 2022-01-17: k=70 -> Apr 25, k=73 -> Apr 28,
    k=74 -> Apr 29 (the flatten bar)."""
    start = date(2022, 1, 17)   # Monday
    # (a) event at k=70: entry 04-26, scheduled exit 05-03 crosses -> clamp
    with tempfile.TemporaryDirectory() as tmp:
        days = _weekday_dates(start, 75)
        data_paths, reader = _build_fixture(
            tmp, days, spec_overrides={p: {"drops": {70: 3.0}}
                                       for p in ("AUD/USD", "NZD/USD", "USD/CAD")})
        out = F.run_arm("anchor", data_paths, reader)
        assert len(out["decisions"]) == 5
        for d in out["decisions"]:
            assert d["decision_ts"] == _iso_k(70, start)
            assert d["entry_bar_ts"] == _iso_k(71, start)
            assert d["exit_bar_ts"] == "2022-04-29T20:00:00+00:00"
            assert d["force_flat"] is True
        assert out["meta"]["schedule"]["total"]["n_force_flats"] == 5
        R.validate_decisions(out["decisions"], out["financing_events"])
    # (b) event at k=73 alone: fill would land exactly on the flatten bar
    with tempfile.TemporaryDirectory() as tmp:
        days = _weekday_dates(start, 75)
        data_paths, reader = _build_fixture(
            tmp, days, spec_overrides={p: {"drops": {73: 3.0}}
                                       for p in ("AUD/USD", "NZD/USD", "USD/CAD")})
        out = F.run_arm("anchor", data_paths, reader)
        assert out["decisions"] == []
        skipped = out["meta"]["skipped_entries"]
        assert len(skipped) == 5
        assert {s["reason"] for s in skipped} == {"ENTRY_FILLS_AT_FOLD_FLATTEN_BAR"}
        assert skipped[0]["decision_ts"] == _iso_k(73, start)
        # an empty book is a legitimate outcome for the runner validator
        decisions, adjustments, formula = R.validate_decisions(
            out["decisions"], out["financing_events"])
        assert decisions == [] and formula is None


# ------------------------- 6. costs once per fill; cash never traded
def test_costs_charged_once_per_fill_and_cash_never_traded():
    with tempfile.TemporaryDirectory() as tmp:
        data_paths, reader = _golden(tmp)
        out = F.run_arm("anchor", data_paths, reader)
        specs = [accounting.TradeSpec(
            trade_id=d["decision_id"], pair=d["pair"],
            side="LONG" if d["side"] > 0 else "SHORT",
            notional_usd=float(d["notional_usd"]),
            entry_price=float(d["entry_price"]), exit_price=float(d["exit_price"]),
            entry_ts_utc=d["entry_bar_ts"], exit_ts_utc=d["exit_bar_ts"])
            for d in out["decisions"]]
        booked = accounting.book_round_trips(specs, cost_tier=1.0)
        assert len(booked) == 5
        # exactly one ENTRY + one EXIT fill per trade, each charged once
        for t in booked:
            assert t.entry_cost_usd == pytest.approx(10000 * 1.5 / 10000)
            assert t.exit_cost_usd == pytest.approx(10000 * 1.5 / 10000)
        # the module never trades the cash currency and stays in the universe
        pairs = {d["pair"] for d in out["decisions"]}
        assert pairs == {leg for leg, _ in F.RESPONSE_LEGS}
        assert "USD" not in pairs
        with pytest.raises(accounting.PositionBookError) as err:
            accounting.PositionBook().open_position(
                trade_id="x", pair="USD", side="LONG", notional_usd=10000.0,
                price=1.0, ts_utc="2024-03-27T20:00:00+00:00", cost_tier=1.0)
        assert err.value.code == "BAD_PAIR"


# ------------- 7. stress tiers reach booked PnL; margins scale accordingly
def test_stress_tiers_rebook_at_tiered_costs_and_margins_scale():
    with tempfile.TemporaryDirectory() as tmp:
        data_paths, reader = _golden(tmp)
        out = F.run_arm("anchor", data_paths, reader)
        specs = [accounting.TradeSpec(
            trade_id=d["decision_id"], pair=d["pair"],
            side="LONG" if d["side"] > 0 else "SHORT",
            notional_usd=10000.0, entry_price=float(d["entry_price"]),
            exit_price=float(d["exit_price"]),
            entry_ts_utc=d["entry_bar_ts"], exit_ts_utc=d["exit_bar_ts"])
            for d in out["decisions"]]
        stress = accounting.book_stress(specs)   # kernel certifies distinctness
        gross = math.fsum(t.pnl_usd for t in
                          accounting.book_round_trips(specs, cost_tier=1.0))
        # booked stress PnL == base recomputed AT the tiered per-side cost:
        # round trip = 2 * 1.5 * tier bps = 3.0 / 4.5 / 6.0 USD per trade
        assert stress[1.0].net_pnl_usd == pytest.approx(gross - 5 * 3.0, abs=1e-9)
        assert stress[1.5].net_pnl_usd == pytest.approx(gross - 5 * 4.5, abs=1e-9)
        assert stress[2.0].net_pnl_usd == pytest.approx(gross - 5 * 6.0, abs=1e-9)
        assert stress[1.0].gross_price_pnl_usd == pytest.approx(gross, abs=1e-9)
        assert stress[2.0].gross_price_pnl_usd == pytest.approx(gross, abs=1e-9)
        assert stress[1.0].booked_rows != stress[1.5].booked_rows
        assert stress[1.5].booked_rows != stress[2.0].booked_rows
        # margin fields on a runner-shaped record scale with the tiered book
        rec = {"base": accounting.book_metrics([stress[1.0].net_pnl_usd / 5.0] * 5),
               "base_price_only": accounting.book_metrics([0.0] * 5),
               "folds": [], "mdd_usd": 0.0, "fold_positive_share": 0.0,
               "pair_concentration": {}, "dropout_scenarios": [],
               "usd_drift_diag": {"corr": None, "n_days": 0, "evaluated": False},
               "incremental_alpha": None, "n_decisions": 100,
               "stress": {"tier1.5": dict(stress[1.5].metrics),
                          "tier2.0": dict(stress[2.0].metrics)}}
        margins = F.margin_to_fail(rec)
        assert margins["margin_stress_tier_1_5_pf_vs_1_00"] == \
            pytest.approx(stress[1.5].metrics["pf"] - 1.0, abs=1e-9)
        assert margins["margin_stress_tier_2_0_pf_vs_1_00"] == \
            pytest.approx(stress[2.0].metrics["pf"] - 1.0, abs=1e-9)
        assert margins["margin_stress_tier_2_0_total_sign"] == \
            pytest.approx(stress[2.0].metrics["total_pnl"], abs=1e-9)


# ----------------------------- 8. control arm: sham bloc, differs, completes
def test_control_sham_bloc_fires_differently_and_differs_from_anchor():
    """The sham EUR/GBP trigger fires on DIFFERENT dates than the commodity
    bloc (fails if control == anchor schedule); a commodity-only drop never
    fires the control."""
    with tempfile.TemporaryDirectory() as tmp:
        # commodity bloc drops at k=61; EUR/GBP constant -> control never fires
        data_paths, reader = _golden(tmp)
        anchor = F.run_arm("anchor", data_paths, reader)
        control = F.run_arm("causal_negative_control", data_paths, reader)
        assert control["meta"]["arm_id"] == "FXFV4-A6-P1-ctrl"
        assert control["meta"]["trigger_pairs"] == ["EUR/USD", "GBP/USD"]
        assert len(anchor["decisions"]) == 5
        assert control["decisions"] == []          # sham bloc saw no event
        assert anchor["decisions"] != control["decisions"]
    with tempfile.TemporaryDirectory() as tmp:
        # EUR/GBP drop at k=65 ONLY: control fires at k=65, anchor at k=61.
        # EUR/GBP alternate during warmup so the sham window has variance
        # (a constant bloc is zero-variance -> fail-closed NO_EVAL).
        days = _weekday_dates(GOLDEN_START, 74)
        data_paths, reader = _build_fixture(
            tmp, days,
            spec_overrides={"AUD/USD": {"drops": {61: 3.0}},
                            "NZD/USD": {"drops": {61: 3.0}},
                            "USD/CAD": {"drops": {61: 3.0}},
                            "EUR/USD": {"alt": True, "drops": {65: 3.0}},
                            "GBP/USD": {"alt": True, "drops": {65: 3.0}}})
        anchor = F.run_arm("anchor", data_paths, reader)
        control = F.run_arm("control", data_paths, reader)  # alias accepted
        assert {d["decision_ts"] for d in anchor["decisions"]} == {_iso_k(61)}
        assert {d["decision_ts"] for d in control["decisions"]} == {_iso_k(65)}
        assert anchor["decisions"] != control["decisions"]
        # identical frozen machinery otherwise: legs, sides, holding
        a = sorted((d["pair"], d["side"], d["side"]) for d in anchor["decisions"])
        c = sorted((d["pair"], d["side"], d["side"]) for d in control["decisions"])
        assert a == c
        assert control["meta"]["bloc_estimator"] == "mean"
        R.validate_decisions(control["decisions"], control["financing_events"])


def test_control_runs_to_completion_fail_closed_missing_bars():
    """Control under evidenced semantics: a leg whose next-session bar is
    missing fails closed NO_TRADE for that leg alone; the other four legs
    complete; a >4-day fill gap fails closed on the frozen allowance."""
    days = _weekday_dates(GOLDEN_START, 74)
    spec = {"EUR/USD": {"alt": True, "drops": {65: 3.0}},
            "GBP/USD": {"alt": True, "drops": {65: 3.0}}}
    with tempfile.TemporaryDirectory() as tmp:
        # USD/JPY data ends at k=65: no next-session bar -> that leg NO_TRADE
        data_paths, reader = _build_fixture(
            tmp, days, spec_overrides=spec, write_pairs=None)
        # rewrite USD/JPY truncated at k=65
        tag = "USD/JPY".replace("/", "")
        path = os.path.join(tmp, f"{tag}_1h_2020-01-01_a.json")
        payload = json.load(open(path, encoding="utf-8"))
        cutoff_str = _ny_1600(days[65]).strftime("%Y-%m-%d %H:%M:%S")
        payload["values"] = [r for r in payload["values"]
                             if r["datetime"] <= cutoff_str]
        json.dump(payload, open(path, "w", encoding="utf-8"))
        out = F.run_arm("control", data_paths, reader)
        pairs = {d["pair"] for d in out["decisions"]}
        assert pairs == {"AUD/USD", "NZD/USD", "USD/CAD", "USD/CHF"}
        assert all(d["decision_ts"] == _iso_k(65) for d in out["decisions"])
        skipped = out["meta"]["skipped_entries"]
        assert [s for s in skipped if s["pair"] == "USD/JPY"] == \
            [{"decision_ts": _iso_k(65), "pair": "USD/JPY",
              "reason": "NO_NEXT_BAR_FOR_ENTRY_FILL"}]
        R.validate_decisions(out["decisions"], out["financing_events"])
    with tempfile.TemporaryDirectory() as tmp:
        # USD/JPY bars missing k=66..70: next bar is k=71 -> gap 6 days > 4
        data_paths, reader = _build_fixture(
            tmp, days, spec_overrides=spec,
            drop_hours={"USD/JPY": {k: "ALL" for k in range(66, 71)}})
        out = F.run_arm("control", data_paths, reader)
        skipped = [s for s in out["meta"]["skipped_entries"]
                   if s["pair"] == "USD/JPY"]
        assert skipped == [{"decision_ts": _iso_k(65), "pair": "USD/JPY",
                            "reason": "ENTRY_FILL_LAG_EXCEEDS_FROZEN_ALLOWANCE"}]
        assert {d["pair"] for d in out["decisions"]} == \
            {"AUD/USD", "NZD/USD", "USD/CAD", "USD/CHF"}


# ------------------------------------------- 9. z-score window warmup
def test_zscore_warmup_no_trigger_before_60_ny_days():
    """No trigger before 60 completed NY-days of history, even on extreme
    early shocks; the first evaluable day is exactly the 62nd valid day."""
    with tempfile.TemporaryDirectory() as tmp:
        days = _weekday_dates(GOLDEN_START, 69)
        data_paths, reader = _build_fixture(
            tmp, days, spec_overrides={p: {"drops": {10: 3.0}}
                                       for p in ("AUD/USD", "NZD/USD", "USD/CAD")})
        out = F.run_arm("anchor", data_paths, reader)
        assert out["decisions"] == []              # early shock inside warmup
        total = out["meta"]["schedule"]["total"]
        assert total["n_trigger_valid_days"] == 69
        assert total["n_trigger_evaluable_days"] == 8   # k=61..68 only
        assert total["n_event_days"] == 0
        assert total["n_no_eval_days"] == 61       # k=0..60


# ------------------------------- 10. malformed / missing data fail closed
def test_malformed_and_missing_data_fail_closed():
    """An interior hole or a quarantined 16:00 bar invalidates the NY-day
    (fail-closed NO_EVAL, never backfilled); malformed rows and missing
    directories raise BLOCKED_DATA.  The fixture uses constant trigger closes
    (zero-variance bloc -> no z anywhere) so the ONLY observable effect is
    the validity machinery itself."""
    flat = {p: {"alt": False, "drops": {61: 3.0}}
            for p in ("AUD/USD", "NZD/USD", "USD/CAD")}
    with tempfile.TemporaryDirectory() as tmp:
        # interior hole on the event day (AUD 15:00 bar missing at k=61):
        # the day is invalid for the trigger -> excluded from the grid
        days = _weekday_dates(GOLDEN_START, 69)
        data_paths, reader = _build_fixture(
            tmp, days, spec_overrides=flat, drop_hours={"AUD/USD": {61: [15]}})
        out = F.run_arm("anchor", data_paths, reader)
        assert out["decisions"] == []   # zero-variance bloc: no z anywhere
        total = out["meta"]["schedule"]["total"]
        assert total["n_trigger_valid_days"] == 68   # k=61 dropped from grid
    with tempfile.TemporaryDirectory() as tmp:
        # same data WITHOUT the hole: the day stays in the grid
        days = _weekday_dates(GOLDEN_START, 69)
        data_paths, reader = _build_fixture(tmp, days, spec_overrides=flat)
        out = F.run_arm("anchor", data_paths, reader)
        assert out["meta"]["schedule"]["total"]["n_trigger_valid_days"] == 69
        assert out["decisions"] == []
    with tempfile.TemporaryDirectory() as tmp:
        # OHLC-inconsistent 16:00 bar at k=61 -> quarantined -> day invalid
        days = _weekday_dates(GOLDEN_START, 69)
        data_paths, reader = _build_fixture(tmp, days, spec_overrides=flat)
        path = os.path.join(tmp, "AUDUSD_1h_2020-01-01_a.json")
        payload = json.load(open(path, encoding="utf-8"))
        bad_ts = _ny_1600(days[61]).strftime("%Y-%m-%d 20:00:00")
        hit = False
        for row in payload["values"]:
            if row["datetime"] == bad_ts:
                row["high"], row["low"] = row["low"], row["high"]  # h < lo
                hit = True
        assert hit
        json.dump(payload, open(path, "w", encoding="utf-8"))
        out = F.run_arm("anchor", data_paths, reader)
        assert out["decisions"] == []   # quarantined close -> NO_EVAL, no fill
        assert out["meta"]["schedule"]["total"]["n_trigger_valid_days"] == 68
    with tempfile.TemporaryDirectory() as tmp:
        # malformed bar row -> BLOCKED_DATA (never fabricated, never skipped)
        days = _weekday_dates(GOLDEN_START, 69)
        data_paths, reader = _build_fixture(tmp, days)
        path = os.path.join(tmp, "AUDUSD_1h_2020-01-01_a.json")
        payload = json.load(open(path, encoding="utf-8"))
        payload["values"][10]["datetime"] = 12345   # non-string stamp
        json.dump(payload, open(path, "w", encoding="utf-8"))
        with pytest.raises(RuntimeError) as err:
            F.load_pair_h1_bars("AUD/USD", str(tmp))
        assert "BLOCKED_DATA" in str(err.value)
    with pytest.raises(RuntimeError) as err:
        F.load_pair_h1_bars("AUD/USD", "/nonexistent/dir/xyz")
    assert "BLOCKED_DATA" in str(err.value)


# ------------------------------------------------ 11. determinism
def test_deterministic_two_runs_identical_records():
    def _run():
        with tempfile.TemporaryDirectory() as tmp:
            data_paths, reader = _golden(tmp)
            outs = {}
            for arm in ("anchor", "neighbour", "causal_negative_control",
                        "benchmark_treatment"):
                outs[arm] = F.run_arm(arm, data_paths, reader)
            return json.dumps(outs, sort_keys=True)
    assert _run() == _run()


# ------------------------------------- 12. neighbour median-vs-mean wiring
def test_neighbour_median_estimator_diverges_from_anchor_mean():
    """Literal-window divergence: with an extreme +10b outlier in the window
    the MEAN z fires (z=-1.115) while the MEDIAN z does not (z=-0.978); the
    median S composition (median(x,0,0)=0) makes the neighbour never fire
    where the anchor fires."""
    # literal window: 59 * (-b) + one +10b outlier, current day S = -2.4b
    win = [-_B] * 59
    win[30] = 10.0 * _B
    cur = -2.4 * _B
    z_mean = (cur - math.fsum(win) / 60.0) / statistics.stdev(win)
    z_median = (cur - statistics.median(win)) / statistics.stdev(
        [v - statistics.median(win) for v in win])
    assert z_mean <= -1.0 < z_median
    assert F.event_flags_from_z([0.0] * 60 + [z_mean])[60] is True
    assert F.event_flags_from_z([0.0] * 60 + [z_median])[60] is False
    # end-to-end: AUD alternates, NZD/CAD constant -> median(x,0,0) == 0
    # (zero-variance -> NO_EVAL) while the mean sees the alternation
    with tempfile.TemporaryDirectory() as tmp:
        days = _weekday_dates(GOLDEN_START, 69)
        data_paths, reader = _build_fixture(
            tmp, days, spec_overrides={
                "AUD/USD": {"drops": {61: 3.0}},
                "NZD/USD": {"alt": False}, "USD/CAD": {"alt": False}})
        anchor = F.run_arm("anchor", data_paths, reader)
        neigh = F.run_arm("neighbour", data_paths, reader)
        assert neigh["meta"]["arm_id"] == "FXFV4-A6-P1-neigh"
        assert neigh["meta"]["bloc_estimator"] == "median"
        assert len(anchor["decisions"]) == 5
        assert neigh["decisions"] == []
        assert anchor["decisions"] != neigh["decisions"]


# ------------------------------------- 13. benchmark staleness identity
def test_benchmark_stale_trigger_shifts_events_by_ten_ny_days():
    """The benchmark is the anchor law with the trigger read on NY-day t-10:
    its event day set is exactly the anchor's shifted +10 valid days; legs,
    clock, holding and fills identical."""
    with tempfile.TemporaryDirectory() as tmp:
        data_paths, reader = _golden(tmp, n_days=79)
        anchor = F.run_arm("anchor", data_paths, reader)
        bench = F.run_arm("benchmark_treatment", data_paths, reader)
        assert bench["meta"]["arm_id"] == "FXFV4-A6-P1-bench"
        assert bench["meta"]["benchmark_staleness_ny_days"] == 10
        assert {d["decision_ts"] for d in anchor["decisions"]} == {_iso_k(61)}
        assert {d["decision_ts"] for d in bench["decisions"]} == {_iso_k(71)}
        for d in bench["decisions"]:
            assert d["entry_bar_ts"] == _iso_k(72)
            assert d["exit_bar_ts"] == _iso_k(77)
            assert d["force_flat"] is False
        # series-level identity: benchmark flags == anchor flags shifted +10
        trig = F.trigger_day_series(
            {p: F.valid_daily_bars(F.load_pair_h1_bars(p, str(tmp)))
             for p in F.TRIGGER_PAIRS}, F.TRIGGER_PAIRS, F.TRIGGER_SIGNS, "mean")
        z = F.z_standardize([d["s"] for d in trig])
        fresh = F.event_flags_from_z(z)
        stale = F.benchmark_event_flags(z)
        for k in range(len(z)):
            assert stale[k] == (fresh[k - 10] if k >= 10 else False)
        R.validate_decisions(bench["decisions"], bench["financing_events"])


# ------------------------------ 14. margin-to-fail record fields
def test_margin_to_fail_fields_hand_computed():
    folds = [
        {"fold": 0, "trades": 30, "expectancy": 2.0, "pf": 1.5,
         "gross_positive": 90.0, "populated": True},
        {"fold": 1, "trades": 30, "expectancy": -1.0, "pf": 0.7,
         "gross_positive": 10.0, "populated": True},
        {"fold": 2, "trades": 30, "expectancy": 0.5, "pf": 1.1,
         "gross_positive": 40.0, "populated": True},
    ]
    rec = {
        "base": {"trades": 10, "total_pnl": 12.0, "expectancy": 1.2, "pf": 1.32,
                 "gross_positive": 20.0},
        "base_price_only": {"trades": 10, "total_pnl": 8.0, "expectancy": 0.8,
                            "pf": 1.25, "gross_positive": 15.0},
        "folds": folds, "mdd_usd": 800.0, "fold_positive_share": 0.6,
        "pair_concentration": {"AUD/USD": 0.45, "USD/JPY": 0.55},
        "dropout_scenarios": [{"scenario": f"s{i}", "expectancy": 0.1,
                               "survived": True} for i in range(7)]
        + [{"scenario": "s7", "expectancy": -0.1, "survived": False}],
        "usd_drift_diag": {"corr": -0.2, "n_days": 90, "evaluated": True},
        "incremental_alpha": 0.35, "n_decisions": 100,
        "stress": {"tier1.5": {"pf": 1.05, "total_pnl": 2.0},
                   "tier2.0": {"pf": 0.95, "total_pnl": -1.0}},
    }
    m = F.margin_to_fail(rec)
    # the eight directive margins
    assert m["margin_expectancy_vs_0"] == pytest.approx(1.2)
    assert m["margin_pf_vs_1_10"] == pytest.approx(0.22)
    assert m["margin_fold_positive_share_vs_50pct"] == pytest.approx(-0.1)
    assert m["margin_mdd_vs_ceiling_usd"] == pytest.approx(1700.0)
    assert m["margin_usd_drift_vs_0_30"] == pytest.approx(0.1)
    assert m["margin_concentration_vs_40pct"] == pytest.approx(-0.15)
    assert m["margin_dropout_vs_6_of_8"] == 1
    assert m["margin_incremental_alpha_vs_0"] == pytest.approx(0.35)
    # remaining frozen Stage-A gates
    assert m["margin_price_only_sign"] == pytest.approx(0.8)
    assert m["margin_decision_floor_vs_40"] == 60
    assert m["margin_populated_folds_positive_vs_2"] == 0
    assert m["margin_fold_pf_vs_0_80"] == pytest.approx(-0.1)
    assert m["margin_stress_tier_1_5_pf_vs_1_00"] == pytest.approx(0.05)
    assert m["margin_stress_tier_2_0_pf_vs_1_00"] == pytest.approx(-0.05)
    assert m["margin_stress_tier_2_0_total_sign"] == pytest.approx(-1.0)
    # not-evaluable -> None (never fabricated)
    rec2 = dict(rec)
    rec2["incremental_alpha"] = None
    rec2["usd_drift_diag"] = {"corr": None, "n_days": 0, "evaluated": False}
    rec2["pair_concentration"] = {}
    rec2["stress"] = {}
    m2 = F.margin_to_fail(rec2)
    assert m2["margin_incremental_alpha_vs_0"] is None
    assert m2["margin_usd_drift_vs_0_30"] is None
    assert m2["margin_concentration_vs_40pct"] is None
    assert m2["margin_stress_tier_2_0_pf_vs_1_00"] is None
    # at-threshold semantics: pf == 1.10 -> margin 0.0 (passing side of >=)
    rec3 = {"base": {"expectancy": 0.0, "pf": 1.10},
            "folds": [], "mdd_usd": 0.0, "pair_concentration": {},
            "dropout_scenarios": [], "incremental_alpha": None,
            "n_decisions": 0}
    m3 = F.margin_to_fail(rec3)
    assert m3["margin_pf_vs_1_10"] == 0.0
    assert m3["margin_expectancy_vs_0"] == 0.0


# ------------------------- 15. drop-one leg-drop non-vacuity (packet test)
def test_drop_one_leg_schedules_are_non_vacuous():
    """Each of the 5 leg-drop scenarios' schedules differs from the full
    anchor book (asserted at implementation per the packet)."""
    with tempfile.TemporaryDirectory() as tmp:
        data_paths, reader = _golden(tmp)
        full = F.run_arm("anchor", data_paths, reader)["decisions"]
        assert full
        for leg in F.RESPONSE_LEGS_LEGSET:
            with tempfile.TemporaryDirectory() as tmp2:
                dropped, _, _ = _drop_one_spec_in(tmp2, leg)
                assert dropped["decisions"] != full
                assert all(d["pair"] != leg for d in dropped["decisions"])
        with pytest.raises(ValueError):
            F.drop_one_leg_schedule("EUR/USD", data_paths, reader)


def _drop_one_spec_in(tmp, leg):
    days = _weekday_dates(GOLDEN_START, 69)
    data_paths, reader = _build_fixture(
        tmp, days, spec_overrides={p: {"drops": {61: 3.0}}
                                   for p in ("AUD/USD", "NZD/USD", "USD/CAD")})
    return F.drop_one_leg_schedule(leg, data_paths, reader), data_paths, reader


# ------------------------- 16. runner contract / registration discovery
def test_runner_contract_validator_and_registration():
    with tempfile.TemporaryDirectory() as tmp:
        data_paths, reader = _golden(tmp)
        for arm in ("anchor", "neighbour", "control", "benchmark_treatment"):
            out = F.run_arm(arm, data_paths, reader)
            assert set(out) == {"decisions", "financing_events", "meta"}
            meta = out["meta"]
            assert meta["decision_clock"] == "daily"
            assert meta["proposal_id"] == "FXFV4-A6-P1"
            assert meta["alpha_definition"] == \
                "per_trade_expectancy_difference_v1"
            decisions, adjustments, formula = R.validate_decisions(
                out["decisions"], out["financing_events"])
            # an empty book takes the validator's early return (formula None)
            if out["decisions"]:
                assert formula == F.FINANCING_FORMULA
            else:
                assert formula is None and not adjustments
            assert set(adjustments) == {d["decision_id"] for d in decisions}
            assert len({d["decision_id"] for d in decisions}) == len(decisions)
            # freeze_token accepted and ignored
            out2 = F.run_arm(arm, data_paths, reader, freeze_token="TOK")
            assert out2 == out
        # discovery mirrors the V3 exec_driver pattern exactly
        R.register_family("family1", F)
        try:
            assert R.FAMILIES["family1"].run_arm is F.run_arm
        finally:
            R.FAMILIES.pop("family1", None)
        with pytest.raises(ValueError):
            F.run_arm("unknown_arm", data_paths, reader)


# ------------------------------- 17. NY-day validity machinery (unit)
def test_ny_day_validity_gap_free_and_16bar():
    days = _weekday_dates(date(2024, 1, 1), 3)
    bars = _pair_bars(days, [1.0, 1.0, 1.0])
    valid = F.ny_day_valid_map(bars)
    assert all(valid[d] for d in days)
    # interior hole (drop 15:00 of day 1) invalidates that NY-day only
    bars_hole = _pair_bars(days, [1.0, 1.0, 1.0], drop_hours={1: [15]})
    valid_hole = F.ny_day_valid_map(bars_hole)
    assert valid_hole[days[0]] is True
    assert valid_hole[days[1]] is False
    assert valid_hole[days[2]] is True
    # missing 16:00 bar -> invalid even when gap-free
    bars_close = _pair_bars(days, [1.0, 1.0, 1.0], drop_hours={1: [16]})
    assert F.ny_day_valid_map(bars_close)[days[1]] is False
    # valid_daily_bars exposes only valid days' 16:00 closes
    daily = F.valid_daily_bars(bars_hole)
    assert [b[0] for b in daily] == [_ny_1600(days[0]), _ny_1600(days[2])]
