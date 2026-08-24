"""Hand-fixture tests for the pure XSECT-MOM rank signal (owner A4)."""

from __future__ import annotations

import math

from research.xsect_rank import compute_target_weights

DAY = 86_400_000_000_000
T0 = 1_755_000_000_000_000_000  # arbitrary anchor


def _panel(prices_by_day: dict[str, list[float]], days: int, start=T0):
    return {
        sym: [(start + i * DAY, p) for i, p in enumerate(prices)]
        for sym, prices in prices_by_day.items()
    }


def test_basic_ranking_long_top_short_bottom():
    # 4-day window (lookback 3): momentum order BTCX > ETH > ... by return
    panel = _panel(
        {
            "ETHUSDT": [100, 101, 102, 103],
            "SOLUSDT": [100, 103, 106, 109],   # strongest
            "BNBUSDT": [100, 100, 100, 100],   # flat
            "XRPUSDT": [100, 99, 98, 97],      # weakest
            "DOGEUSDT": [100, 100.5, 101, 101.5],
            "LINKUSDT": [100, 99.5, 100.5, 100],
            "ADAUSDT": [100, 102, 101, 104],
        },
        days=4,
    )
    cutoff = T0 + 3 * DAY
    res = compute_target_weights(panel, cutoff, lookback_days=3)
    assert res["status"] == "OK"
    assert [s for s, _ in res["longs"]] == ["SOLUSDT", "ADAUSDT"]
    # XRP lowest; BNB and LINK tie at exactly 0 -> symbol_ascending puts
    # LINK after BNB, so LINK joins XRP in the bottom leg.
    assert [s for s, _ in res["shorts"]] == ["LINKUSDT", "XRPUSDT"]
    total = sum(w for _, w in res["longs"] + res["shorts"])
    assert abs(total) < 1e-9


def test_tie_break_symbol_ascending():
    panel = _panel(
        {
            "ZZUSDT": [100, 110, 120],
            "AAUSDT": [100, 110, 120],  # identical scores
            "MMUSDT": [100, 105, 110],
            "BBUSDT": [100, 95, 90],
            "CCUSDT": [100, 96, 92],
            "DDUSDT": [100, 100, 100],
            "EEUSDT": [100, 101, 102],
        },
        days=3,
    )
    res = compute_target_weights(panel, T0 + 2 * DAY, lookback_days=2)
    long_syms = [s for s, _ in res["longs"]]
    short_syms = [s for s, _ in res["shorts"]]
    assert long_syms == ["AAUSDT", "ZZUSDT"]       # tie -> ascending
    assert short_syms == ["CCUSDT", "BBUSDT"]


def test_reverse_control_flips_signs():
    panel = _panel(
        {
            "ETHUSDT": [100, 110, 120],
            "SOLUSDT": [100, 105, 108],
            "BNBUSDT": [100, 100, 100],
            "XRPUSDT": [100, 90, 80],
            "DOGEUSDT": [100, 95, 92],
            "LINKUSDT": [100, 102, 101],
            "ADAUSDT": [100, 98, 96],
        },
        days=3,
    )
    fwd = compute_target_weights(panel, T0 + 2 * DAY, lookback_days=2)
    rev = compute_target_weights(panel, T0 + 2 * DAY, lookback_days=2, reverse=True)
    # Equal weights within legs => only membership matters.
    assert sorted(s for s, _ in fwd["longs"]) == sorted(s for s, _ in rev["shorts"])
    assert sorted(s for s, _ in fwd["shorts"]) == sorted(s for s, _ in rev["longs"])
    assert all(w < 0 for _, w in rev["shorts"])


def test_cutoff_boundary_includes_exact_and_excludes_after():
    closes = [(T0 + i * DAY, 100 + i) for i in range(5)]
    panel = {"ETHUSDT": closes}
    # cutoff exactly at day-3 close: usable points are days 0..3
    res = compute_target_weights(
        {**panel}, T0 + 3 * DAY, lookback_days=3, min_eligible=1,
        long_count=1, short_count=0, weight=1.0,
    )
    assert res["status"] == "OK"
    score = math.log(103 / 100)
    assert abs(res["scores"]["ETHUSDT"] - score) < 1e-12
    # a bar AFTER cutoff must not be visible: shift last point later only
    panel2 = {"ETHUSDT": closes[:-1] + [(T0 + 4 * DAY + 3600_000_000_000, 200)]}
    res2 = compute_target_weights(
        panel2, T0 + 3 * DAY, lookback_days=3, min_eligible=1,
        long_count=1, short_count=0, weight=1.0,
    )
    assert res2["status"] == "OK"
    assert abs(res2["scores"]["ETHUSDT"] - score) < 1e-12


def test_missing_symbol_skips_entire_cross_section():
    full = {
        f"S{i}USDT": [(T0 + j * DAY, 100 + j + i) for j in range(4)]
        for i in range(7)
    }
    ok = compute_target_weights(full, T0 + 3 * DAY, lookback_days=3)
    assert ok["status"] == "OK"
    broken = dict(full)
    broken["S6USDT"] = full["S6USDT"][:-1]  # one symbol short history
    skip = compute_target_weights(broken, T0 + 3 * DAY, lookback_days=3)
    assert skip["status"] == "SKIP_INCOMPLETE"
    assert skip["reason_code"] == "incomplete_cross_section_skip"


def test_gap_in_daily_series_skips():
    closes = [(T0 + j * DAY, 100 + j) for j in range(4)]
    closes[2] = (T0 + 2 * DAY + 3600_000_000_000, 102)  # non-daily gap
    panel = {"AUSDT": closes, **{
        f"S{i}USDT": [(T0 + j * DAY, 100 + j + i) for j in range(4)] for i in range(6)
    }}
    res = compute_target_weights(panel, T0 + 3 * DAY, lookback_days=3)
    assert res["status"] == "SKIP_INCOMPLETE"


def test_benchmark_btc_never_traded():
    panel = {
        "BTCUSDT": [(T0 + j * DAY, 50000 + 5000 * j) for j in range(4)],
        **{f"S{i}USDT": [(T0 + j * DAY, 100 + j + i) for j in range(4)] for i in range(7)},
    }
    res = compute_target_weights(panel, T0 + 3 * DAY, lookback_days=3)
    traded = [s for s, _ in res["longs"] + res["shorts"]]
    assert "BTCUSDT" not in traded


def test_determinism():
    panel = _panel(
        {f"S{i}USDT": [100 + j * (i + 1) for j in range(8)] for i in range(7)},
        days=8,
    )
    a = compute_target_weights(panel, T0 + 7 * DAY, lookback_days=5)
    b = compute_target_weights(panel, T0 + 7 * DAY, lookback_days=5)
    assert a == b
