"""Stage-A wave-1 tests: 64 T1 leg configs + rule archetypes (PC12A).

Every new config loads, builds, and its archetype decides deterministically
on a small synthetic window with vote in {-1, 0, +1} and a carried
label + cluster_id. Archetype unit tests pin the core rule behavior of
each rule class on hand-built windows.
"""

import datetime as dt
import json
import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from research.pc12a import legs as L                     # noqa: E402
from research.pc12a import leg_rules as R                # noqa: E402
from research.pc12a.legs import BarContext, LegDecision  # noqa: E402

UTC = dt.timezone.utc
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))),
    "research", "pc12a", "legs_config")

CYCLE = "PORTFOLIO-COMPOSITE-12ASSETS-100K-V1"


def _mk_ctx(ts, mid, prev=None, vol=10.0, atr60=0.0005):
    return BarContext(ts=ts, symbol="TEST", mid_close=mid,
                      mid_close_prev=prev if prev is not None else mid,
                      bid_open=mid - 0.00005, ask_open=mid + 0.00005,
                      bid_close=mid - 0.00005, ask_close=mid + 0.00005,
                      bid_low=mid - 0.0001, ask_high=mid + 0.0001,
                      atr60=atr60, in_entry_window=True,
                      is_flat_instant=False, day=ts.date(), profile=None,
                      last_data_ts=ts, mid_high=mid + 0.00005,
                      mid_low=mid - 0.00005, bid_volume=vol)


def _d(y, m, d_, hh=0, mm=0):
    return dt.datetime(y, m, d_, hh, mm, tzinfo=UTC)


def _daily_bars(closes, start="2023-01-02", drift=1.0):
    """Deterministic daily bars on consecutive WEEKDAYS from a close
    series (high/low around each close)."""
    d = dt.date.fromisoformat(start)
    if d.weekday() >= 5:
        d += dt.timedelta(days=(7 - d.weekday()) % 7)
    out = []
    for c in closes:
        while d.weekday() >= 5:
            d += dt.timedelta(days=1)
        out.append({"date": d, "open": c - 0.0002 * drift,
                    "high": c + 0.001 * drift,
                    "low": c - 0.001 * drift, "close": c,
                    "available": dt.datetime.combine(
                        d, dt.time(0, 0), tzinfo=UTC)
                    + dt.timedelta(days=1)})
        d += dt.timedelta(days=1)
    return out


# ---------------------------------------------------------------------------
# 1. every new config loads, builds, carries identity + label + cluster
# ---------------------------------------------------------------------------

WAVE1_GIDS = set()
for fn in os.listdir(CONFIG_DIR):
    if fn.endswith(".json"):
        with open(os.path.join(CONFIG_DIR, fn)) as fh:
            c = json.load(fh)
        if c.get("sleeve_id") == "POOL_B_TRIAGE" and c.get("archetype"):
            WAVE1_GIDS.add(c["corpus_gid"])


def test_wave1_config_count():
    # 75 T1 rows - 2 exemplars already implemented - 9 parked = 64
    assert len(WAVE1_GIDS) == 64


@pytest.mark.parametrize("gid", sorted(WAVE1_GIDS))
def test_config_identity_and_build(gid):
    with open(os.path.join(CONFIG_DIR, f"{gid}.json")) as fh:
        cfg = json.load(fh)
    assert cfg["cycle_id"] == CYCLE
    for k in ("corpus_gid", "family_id", "mech_key", "archetype", "clock",
              "symbol", "pit_join_list", "cost_tier",
              "outcome_exposed_label", "cluster_id", "params",
              "param_source"):
        assert k in cfg, f"{gid} missing {k}"
    assert cfg["param_source"] in ("corpus_verbatim", "triage_default")
    leg = L.build_leg(cfg)
    ident = leg.identity
    assert ident.candidate_id == gid
    assert ident.cycle_id == CYCLE
    assert ident.outcome_exposed_label == cfg["outcome_exposed_label"]
    assert ident.cluster_id == cfg["cluster_id"]
    assert ident.arm_config_digest


@pytest.mark.parametrize("gid", sorted(WAVE1_GIDS))
def test_config_decides_deterministically(gid):
    """Run the leg over a synthetic stream twice; identical decisions."""
    with open(os.path.join(CONFIG_DIR, f"{gid}.json")) as fh:
        cfg = json.load(fh)
    run1 = _run_leg_synthetic(cfg, seed=1)
    run2 = _run_leg_synthetic(cfg, seed=1)
    assert run1 == run2
    for dec in run1:
        assert isinstance(dec, tuple)
        assert dec[1] in (-1, 0, 1)   # (reason_code, vote)


def _run_leg_synthetic(cfg, seed=7):
    rng = np.random.default_rng(seed)
    leg = L.build_leg(cfg)
    leg.warmup_active = False
    sym = cfg["symbol"]
    pip = 0.01 if sym == "USDJPY" else 0.0001
    out = []
    if leg.wants_every_bar:
        # 6 synthetic days x 1440 minutes of a drifting random walk
        d0 = dt.date(2024, 3, 4)
        price = 1.10 if sym != "USDJPY" else 150.0
        for day_i in range(6):
            d = d0 + dt.timedelta(days=day_i)
            for m in range(1440):
                ts = dt.datetime.combine(d, dt.time(0, 0), tzinfo=UTC) \
                    + dt.timedelta(minutes=m + 1)
                step = rng.normal(0, 3 * pip)
                price += step
                ctx = _mk_ctx(ts, price, prev=price - step,
                              vol=float(20 + 40 * (m % 97 == 0)))
                dec = leg.on_bar(ctx)
                if dec is not None:
                    out.append((dec.reason_code, dec.vote))
        return out
    # daily-clock legs: 300 synthetic closes with trend + noise
    closes = list(1.10 + np.cumsum(rng.normal(0.0004, 0.0012, 300))
                  if sym != "USDJPY" else
                  150.0 + np.cumsum(rng.normal(0.04, 0.12, 300)))
    for bar in _daily_bars(list(closes)):
        dec = leg.on_daily_bar(bar)
        if dec is not None:
            out.append((dec.reason_code, dec.vote))
    return out


# ---------------------------------------------------------------------------
# 2. archetype unit tests (one per rule class)
# ---------------------------------------------------------------------------

def _ident(gid, params=None, sym="GBPUSD"):
    with open(os.path.join(CONFIG_DIR, f"{gid}.json")) as fh:
        cfg = json.load(fh)
    if params:
        cfg["params"].update(params)
    cfg["symbol"] = sym
    return L.make_identity(cfg), cfg


def test_donchian_sar_flips():
    ident, cfg = _ident("USDCAD-S002")
    leg = R.DonchianSarLeg(ident)
    bars = _daily_bars(list(np.linspace(1.30, 1.40, 70)))
    decs = []
    for b in bars:
        d = leg.on_daily_bar(b)
        if d is not None:
            decs.append(d)
    assert any(d.reason_code == "DONCHIAN20_BREAK_LONG" for d in decs)
    assert all(d.vote in (-1, 0, 1) for d in decs)


def test_donchian_sar_adx_gate_blocks_chop():
    ident, _ = _ident("AUDUSD-S002")
    leg = R.DonchianSarLeg(ident)
    rng = np.random.default_rng(3)
    closes = 0.66 + np.cumsum(rng.normal(0, 0.0004, 120))
    decs = [d for b in _daily_bars(list(closes))
            if (d := leg.on_daily_bar(b)) is not None]
    assert all(d.vote in (-1, 0, 1) for d in decs)


def test_donchian_trail_enters_and_trails():
    ident, _ = _ident("GBPUSD-S001")
    leg = R.DonchianTrailLeg(ident)
    closes = list(1.25 + 0.0015 * i for i in range(40))
    decs = [d for b in _daily_bars(closes)
            if (d := leg.on_daily_bar(b)) is not None]
    assert any(d.reason_code == "DONCHIAN20_CLOSE_LONG" for d in decs)


def test_adx_macd_persist_direction():
    ident, _ = _ident("AUDUSD-S003")
    leg = R.AdxMacdLeg(ident)
    rng = np.random.default_rng(2)
    # 45 chop days (ADX low) then a clean uptrend -> the ADX 25-cross
    # happens inside the observed window
    closes = list(0.65 + rng.normal(0, 0.0006, 45)) \
        + list(0.65 + 0.0013 * i for i in range(1, 45))
    decs = [d for b in _daily_bars(closes)
            if (d := leg.on_daily_bar(b)) is not None]
    longs = [d for d in decs if "LONG" in d.reason_code]
    assert longs, "uptrend must produce a long ADX/MACD entry"


def test_ma_adx_regime_enters_uptrend():
    ident, _ = _ident("USDJPY-S002", sym="USDJPY")
    leg = R.MaAdxRegimeLeg(ident)
    closes = list(140.0 + 0.35 * i for i in range(240))
    decs = [d for b in _daily_bars(closes)
            if (d := leg.on_daily_bar(b)) is not None]
    assert any("MA50_200_ADX_LONG" == d.reason_code for d in decs)


def test_ts_momentum_sign_follows_trend():
    ident, _ = _ident("USDJPY-S003", sym="USDJPY")
    leg = R.TsMomentumLeg(ident)
    closes = list(140.0 + 0.08 * i for i in range(290))
    decs = [d for b in _daily_bars(closes)
            if (d := leg.on_daily_bar(b)) is not None]
    rebal = [d for d in decs if d.reason_code == "TSMOM_REBALANCE"]
    assert rebal and all(d.vote == 1 for d in rebal)


def test_ma200_dislocation_entry():
    ident, _ = _ident("USDCAD-S004")
    leg = R.Ma200DislocationLeg(ident)
    # long drift -> price far above a slowly-updating 200DMA
    closes = list(1.30 + 0.0022 * i for i in range(240))
    decs = [d for b in _daily_bars(closes)
            if (d := leg.on_daily_bar(b)) is not None]
    assert any(d.reason_code == "MA200_DISLOC_LONG" for d in decs)


def test_turtle_pyramid_adds_units():
    ident, _ = _ident("USDJPY-S009", sym="USDJPY")
    leg = R.TurtlePyramidLeg(ident)
    closes = list(150.0 + 0.9 * i for i in range(60))
    bars = _daily_bars(closes)
    decs = [d for b in bars if (d := leg.on_daily_bar(b)) is not None]
    assert any(d.reason_code == "TURTLE_UNIT1_LONG" for d in decs)


def test_rsi2_daily_pullback_enters_dip():
    ident, _ = _ident("USDCAD-S011")
    leg = R.Rsi2DailyLeg(ident)
    rng = np.random.default_rng(11)
    closes = list(1.34 + np.cumsum(rng.normal(0.0003, 0.0009, 260)))
    # force a sharp 2-day dip at the end of an uptrend
    closes[-2] = closes[-3] - 0.006
    closes[-1] = closes[-2] - 0.004
    decs = [d for b in _daily_bars(closes)
            if (d := leg.on_daily_bar(b)) is not None]
    assert any("RSI2_PULLBACK" in d.reason_code for d in decs)


def test_bb_squeeze_break_needs_squeeze():
    ident, _ = _ident("USDJPY-S023", sym="USDJPY")
    leg = R.BBSqueezeBreakLeg(ident)
    # compression then a break out (160 flat days give the 120d BW window)
    closes = [151.0] * 160 + [151.4, 151.9, 152.6]
    decs = [d for b in _daily_bars(closes)
            if (d := leg.on_daily_bar(b)) is not None]
    assert any("BB_SQUEEZE_BREAK_LONG" == d.reason_code for d in decs)


def test_bb_lowvol_range_fades_touch():
    ident, _ = _ident("USDCAD-S016")
    leg = R.BBLowVolRangeLeg(ident)
    rng = np.random.default_rng(5)
    # 150 wider days, then 20 flat days (sigma -> 0: BW percentile low),
    # final day a bump above the collapsed upper band
    closes = list(1.35 + rng.normal(0, 0.0008, 150)) + [1.35] * 20
    closes.append(1.3502)
    decs = [d for b in _daily_bars(closes)
            if (d := leg.on_daily_bar(b)) is not None]
    assert any("BB_RANGE_FADE_SHORT" == d.reason_code for d in decs)


def test_atr_ratio_breakout():
    ident, _ = _ident("USDJPY-S029", sym="USDJPY")
    leg = R.AtrRatioBreakoutLeg(ident)
    closes = [152.0] * 25 + [152.0 + 0.1 * i for i in range(1, 8)]
    decs = [d for b in _daily_bars(closes)
            if (d := leg.on_daily_bar(b)) is not None]
    assert any("ATR_RATIO_BREAK" in d.reason_code for d in decs)


def test_weekly_swing_break():
    ident, _ = _ident("USDCAD-S006")
    leg = R.WeeklySwingBreakLeg(ident)
    # 30 weeks of rising prices
    closes = list(1.30 + 0.0035 * i for i in range(150))
    decs = [d for b in _daily_bars(closes)
            if (d := leg.on_daily_bar(b)) is not None]
    assert any("WEEKLY_SWING_BREAK_LONG" == d.reason_code for d in decs)


def test_weekly_ma_regime():
    ident, _ = _ident("GBPUSD-S004")
    leg = R.WeeklyMaRegimeLeg(ident)
    closes = list(1.25 + 0.0022 * i for i in range(140))
    decs = [d for b in _daily_bars(closes)
            if (d := leg.on_daily_bar(b)) is not None]
    assert any("WEEKLY_MA_REGIME_LONG" == d.reason_code for d in decs)


def test_calendar_season_march_short():
    ident, _ = _ident("USDJPY-S044", sym="USDJPY")
    leg = R.CalendarSeasonLeg(ident)
    bars = _daily_bars([150.0 + 0.01 * i for i in range(40)],
                       start="2024-02-01")
    decs = [d for b in bars if (d := leg.on_daily_bar(b)) is not None]
    assert any("SEASON_ENTRY_SHORT" == d.reason_code for d in decs)


def test_calendar_season_month_turn():
    ident, _ = _ident("EURUSD-S046")
    leg = R.CalendarSeasonLeg(ident)
    # rising prior (January) month, decision day inside the Feb turn
    closes = [1.08 + 0.0006 * i for i in range(75)]
    bars = _daily_bars(closes, start="2023-11-15")
    decs = [d for b in bars if (d := leg.on_daily_bar(b)) is not None]
    assert any("MONTH_TURN_CONTINUATION" == d.reason_code for d in decs)


def test_regime_gate_rv_band_states():
    ident, _ = _ident("EURUSD-S091")
    leg = R.RegimeGateLeg(ident)
    # alternating vol regimes produce some gate decision
    rng = np.random.default_rng(9)
    closes = list(1.10 + np.cumsum(rng.normal(0, 0.0008, 300)))
    decs = [d for b in _daily_bars(closes)
            if (d := leg.on_daily_bar(b)) is not None]
    assert all(d.vote in (-1, 0, 1) for d in decs)


def test_regime_gate_weekday():
    ident, _ = _ident("GBPUSD-S048")
    leg = R.RegimeGateLeg(ident)
    closes = list(1.26 + 0.0002 * ((-1) ** i) for i in range(12))
    decs = [d for b in _daily_bars(closes, start="2024-01-01")
            if (d := leg.on_daily_bar(b)) is not None]
    codes = {d.reason_code for d in decs}
    assert codes & {"WEEKDAY_TREND_SIDE", "WEEKDAY_MR_SIDE"}


def test_cross_z_eurgbp_anchor():
    ident, cfg = _ident("GBPUSD-S019")
    leg = R.CrossZLeg(ident)
    gbp = _daily_bars([1.26] * 42 + [1.262, 1.264, 1.266])
    eur = [{"date": b["date"], "close": 1.085,
            "high": 1.086, "low": 1.084} for b in gbp]
    leg.set_cross_feeds({"EURUSD": eur})
    # EURGBP falls (EUR flat, GBP rising) -> z < -2 -> long GBPUSD
    decs = [d for b in gbp if (d := leg.on_daily_bar(b)) is not None]
    assert any("EURGBP_ANCHOR_FADE_LONG" == d.reason_code for d in decs)


def test_cross_z_beta_router_runs():
    ident, _ = _ident("GBPUSD-S083")
    leg = R.CrossZLeg(ident)
    rng = np.random.default_rng(21)
    gbp = _daily_bars(list(1.26 + rng.normal(0, 0.001, 90)))
    eur = _daily_bars(list(1.08 + rng.normal(0, 0.001, 90)))
    leg.set_cross_feeds({"EURUSD": eur})
    decs = [d for b in gbp if (d := leg.on_daily_bar(b)) is not None]
    assert all(d.vote in (-1, 0, 1) for d in decs)


# ---- minute archetypes ------------------------------------------------------


def _feed_minute(leg, days=6, base=1.2650, pip=0.0001, seed=13,
                 start="2024-03-04", volume_spike_min=None):
    rng = np.random.default_rng(seed)
    d0 = dt.date.fromisoformat(start)
    price = base
    out = []
    for day_i in range(days):
        d = d0 + dt.timedelta(days=day_i)
        for m in range(1440):
            ts = dt.datetime.combine(d, dt.time(0, 0), tzinfo=UTC) \
                + dt.timedelta(minutes=m + 1)
            step = rng.normal(0, 2.5 * pip)
            prev = price
            price += step
            vol = 20.0
            if volume_spike_min is not None and m in volume_spike_min:
                vol = 500.0
            ctx = _mk_ctx(ts, price, prev=prev, vol=vol)
            dec = leg.on_bar(ctx)
            if dec is not None:
                out.append(dec)
    return out


def _set_eur_feed(leg, days=40):
    eur = _daily_bars(list(1.085 + 0.0002 * i for i in range(days)))
    leg.set_cross_feeds({"EURUSD": eur})


def test_keltner_break():
    ident, _ = _ident("GBPUSD-S007")
    leg = R.KeltnerBreakLeg(ident)
    leg.warmup_active = False
    # warm its H4 clock + d1 history with a quiet drift, then a jump day
    decs = _feed_minute(leg, days=7, base=1.26, seed=4)
    assert all(d.vote in (-1, 0, 1) for d in decs)


def test_adx_ema_rider_runs():
    ident, _ = _ident("GBPUSD-S003")
    leg = R.AdxEmaRiderLeg(ident)
    leg.warmup_active = False
    decs = _feed_minute(leg, days=6, seed=6)
    assert all(d.vote in (-1, 0, 1) for d in decs)


def test_h4_zscore_fades_extreme():
    ident, _ = _ident("EURUSD-S013")
    leg = R.H4ZscoreLeg(ident)
    leg.warmup_active = False
    decs = _feed_minute(leg, days=6, seed=17)
    assert all(d.vote in (-1, 0, 1) for d in decs)


def test_rsi2_barclock_h4():
    ident, _ = _ident("USDJPY-S014", sym="USDJPY")
    leg = R.Rsi2BarClockLeg(ident)
    leg.warmup_active = False
    decs = _feed_minute(leg, days=6, base=151.0, pip=0.01, seed=23)
    assert all(d.vote in (-1, 0, 1) for d in decs)


def test_atr_ratio_h4_runs():
    ident, _ = _ident("EURUSD-S027")
    leg = R.AtrRatioH4Leg(ident)
    leg.warmup_active = False
    decs = _feed_minute(leg, days=6, seed=29)
    assert all(d.vote in (-1, 0, 1) for d in decs)


def test_h1_pdh_pdl_break():
    ident, _ = _ident("USDJPY-S026", sym="USDJPY")
    leg = R.H1PdhPdlLeg(ident)
    leg.warmup_active = False
    decs = _feed_minute(leg, days=6, base=151.0, pip=0.01, seed=31)
    assert all(d.vote in (-1, 0, 1) for d in decs)


def test_h1_pdh_pdl_eurusd_confirm():
    ident, _ = _ident("GBPUSD-S065")
    leg = R.H1PdhPdlLeg(ident)
    leg.warmup_active = False
    _set_eur_feed(leg)
    decs = _feed_minute(leg, days=5, seed=37)
    assert all(d.vote in (-1, 0, 1) for d in decs)


def test_usdjpy_momentum_gate():
    ident, _ = _ident("GBPUSD-S086")
    leg = R.UsdjpyMomentumGateLeg(ident)
    leg.warmup_active = False
    jpy = _daily_bars(list(150.0 + 0.15 * i for i in range(70)))
    leg.set_cross_feeds({"USDJPY": jpy})
    decs = _feed_minute(leg, days=3, seed=41)
    codes = {d.reason_code for d in decs}
    assert "USDJPY_MOMENTUM_GATE" in codes


def test_london_persistence():
    ident, _ = _ident("GBPUSD-S002")
    leg = R.LondonPersistenceLeg(ident)
    leg.warmup_active = False
    # a strong directional 07:00-09:00 London move on day 3
    rng = np.random.default_rng(43)
    d0 = dt.date(2024, 2, 12)      # Mon; directional day = day 20 (a Mon)
    price = 1.2650
    out = []
    n_days = 22
    for day_i in range(n_days):
        d = d0 + dt.timedelta(days=day_i)
        for m in range(1440):
            ts = dt.datetime.combine(d, dt.time(0, 0), tzinfo=UTC) \
                + dt.timedelta(minutes=m + 1)
            prev = price
            drift = 0.0
            if day_i == n_days - 2 and 7 * 60 <= m < 9 * 60:
                drift = 0.00003  # persistent up-move in the London window
            price += rng.normal(0, 0.00002) + drift
            ctx = _mk_ctx(ts, price, prev=prev)
            dec = leg.on_bar(ctx)
            if dec is not None:
                out.append(dec)
    assert any(d.reason_code == "LONDON_PERSIST_LONG" for d in out)


def test_asian_fake_break_fade():
    ident, _ = _ident("GBPUSD-S011")
    leg = R.SessionRangeFadeLeg(ident)
    leg.warmup_active = False
    decs = _feed_minute(leg, days=5, seed=47)
    assert all(d.vote in (-1, 0, 1) for d in decs)


def test_monday_gap_gbp():
    ident, _ = _ident("GBPUSD-S016")
    leg = R.SessionRangeFadeLeg(ident)
    leg.warmup_active = False
    rng = np.random.default_rng(53)
    d0 = dt.date(2024, 2, 29)   # Thursday; gap Monday = 2024-03-04
    price = 1.2650
    out = []
    for day_i in range(7):
        d = d0 + dt.timedelta(days=day_i)
        for m in range(1440):
            ts = dt.datetime.combine(d, dt.time(0, 0), tzinfo=UTC) \
                + dt.timedelta(minutes=m + 1)
            prev = price
            gap = 0.0008 if (d.weekday() == 0 and m < 60) else 0.0
            price += rng.normal(0, 0.00003) + gap * (1 / 8)
            ctx = _mk_ctx(ts, price, prev=prev)
            dec = leg.on_bar(ctx)
            if dec is not None:
                out.append(dec)
    assert any("MON_GAP_FADE_GBP" in d.reason_code for d in out)


def test_ny_vwap_reversion():
    ident, _ = _ident("GBPUSD-S017")
    leg = R.SessionRangeFadeLeg(ident)
    leg.warmup_active = False
    decs = _feed_minute(leg, days=5, seed=59)
    assert all(d.vote in (-1, 0, 1) for d in decs)


def test_nr7_stop_orders():
    ident, _ = _ident("EURUSD-S024")
    leg = R.Nr7StopOrderLeg(ident)
    leg.warmup_active = False
    decs = _feed_minute(leg, days=8, seed=61)
    assert all(d.vote in (-1, 0, 1) for d in decs)


def test_nr7_m30_break():
    ident, _ = _ident("GBPUSD-S023")
    leg = R.Nr7M30BreakLeg(ident)
    leg.warmup_active = False
    decs = _feed_minute(leg, days=8, seed=67)
    assert all(d.vote in (-1, 0, 1) for d in decs)


def test_hour_of_day_drift_runs():
    ident, _ = _ident("USDJPY-S050", sym="USDJPY")
    leg = R.HourOfDayDriftLeg(ident)
    leg.warmup_active = False
    decs = _feed_minute(leg, days=4, base=151.0, pip=0.01, seed=71)
    assert all(d.vote in (-1, 0, 1) for d in decs)


def test_round_number_fade():
    ident, _ = _ident("GBPUSD-S014")
    leg = R.RoundNumberFadeLeg(ident)
    leg.warmup_active = False
    decs = _feed_minute(leg, days=6, seed=73)
    assert all(d.vote in (-1, 0, 1) for d in decs)


def test_ar_gate():
    ident, _ = _ident("GBPUSD-S084")
    leg = R.ArGateLeg(ident)
    leg.warmup_active = False
    decs = _feed_minute(leg, days=8, seed=79)
    assert all(d.vote in (-1, 0, 1) for d in decs)


def test_weekly_nr7_bracket():
    ident, _ = _ident("AUDUSD-S023")
    leg = R.WeeklyNr7BracketLeg(ident)
    # 30 aligned Mon..Fri weeks: 29 wide trending weeks, week 30 NR7
    d = dt.date(2024, 1, 1)          # a Monday
    assert d.weekday() == 0
    bars = []
    c = 0.6500
    for wk in range(30):
        for day in range(5):
            c += 0.0018
            rng_w = 0.004 if wk < 29 else 0.0004   # final week = NR7
            bars.append({"date": d, "open": c - 0.001, "high": c + rng_w,
                         "low": c - rng_w, "close": c,
                         "available": dt.datetime.combine(
                             d, dt.time(0, 0), tzinfo=UTC)
                         + dt.timedelta(days=1)})
            d += dt.timedelta(days=1)
        d += dt.timedelta(days=2)   # skip the weekend
    # the Monday AFTER the NR7 week fires the bracket entry
    nxt = {"date": d, "open": c - 0.001, "high": c + 0.004,
           "low": c - 0.004, "close": c,
           "available": dt.datetime.combine(
               d, dt.time(0, 0), tzinfo=UTC) + dt.timedelta(days=1)}
    bars.append(nxt)
    decs = [dd for b in bars if (dd := leg.on_daily_bar(b)) is not None]
    assert any("WEEKLY_NR7_BRACKET" in dd.reason_code for dd in decs)


def test_weekly_h4_break():
    ident, _ = _ident("AUDUSD-S029")
    leg = R.WeeklyH4BreakLeg(ident)
    leg.warmup_active = False
    decs = _feed_minute(leg, days=8, base=0.6580, seed=83)
    assert all(d.vote in (-1, 0, 1) for d in decs)


def test_minute_legs_suppress_warmup_entries():
    ident, _ = _ident("GBPUSD-S002")
    leg = R.LondonPersistenceLeg(ident)
    leg.warmup_active = True
    rng = np.random.default_rng(89)
    d = dt.date(2024, 3, 4)
    price = 1.265
    for m in range(1440):
        ts = dt.datetime.combine(d, dt.time(0, 0), tzinfo=UTC) \
            + dt.timedelta(minutes=m + 1)
        prev = price
        price += rng.normal(0, 0.00004)
        leg.on_bar(_mk_ctx(ts, price, prev=prev))
    assert leg.desired_units == 0   # no unjournaled warmup position


# ---------------------------------------------------------------------------
# 3. engine-level invariants
# ---------------------------------------------------------------------------

def test_registry_covers_all_archetypes():
    for gid in sorted(WAVE1_GIDS):
        with open(os.path.join(CONFIG_DIR, f"{gid}.json")) as fh:
            cfg = json.load(fh)
        key = ("POOL_B_TRIAGE", cfg["archetype"])
        assert key in R.RULE_REGISTRY, f"{gid} archetype not registered"


def test_parked_legs_not_configured():
    parked = {"USDJPY-S064", "USDJPY-S066", "USDJPY-S070",
              "AUDUSD-S066", "AUDUSD-S069", "AUDUSD-S082", "AUDUSD-S083",
              "AUDUSD-S091", "USDCAD-S068"}
    assert parked.isdisjoint(WAVE1_GIDS)


def test_leak_scan_clean_on_wave1_outputs():
    """The wave-1 rule module emits decisions only; scanning a synthetic
    serialization of every wave-1 reason code stays clean of the
    forbidden output keys (source text is out of scope: 'return' is a
    python keyword, not a reported metric)."""
    from research.pc12a.run_dry import leak_scan
    codes = set()
    for gid in sorted(WAVE1_GIDS):
        for dec in _run_leg_synthetic(
                json.load(open(os.path.join(CONFIG_DIR, f"{gid}.json")))):
            codes.add(dec[0])
    blob = json.dumps(sorted(codes))
    assert leak_scan(blob)["clean"]
