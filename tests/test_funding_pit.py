"""Tests for the point-in-time funding helper (owner: A2, consumer: A4)."""

from __future__ import annotations

import json

import pandas as pd
import pytest

from research.funding_pit import MIN_PUBLISHED_SETTLEMENTS, FundingPIT

DAY_MS = 86_400_000
EIGHT_H_MS = 8 * 3_600_000


def _anchor_ms() -> int:
    return int(pd.Timestamp("2026-06-01T00:00:00Z").value // 1e6)


def _write_bundle(tmp_path, symbol, rates, step_ms=EIGHT_H_MS):
    anchor = _anchor_ms()
    rows = [
        {"fundingTime": anchor + i * step_ms, "fundingRate": str(rate)}
        for i, rate in enumerate(rates)
    ]
    d = tmp_path / symbol
    d.mkdir(parents=True)
    (d / "funding.json").write_text(json.dumps({
        "requested_start_ms": anchor,
        "requested_end_ms": anchor + 730 * DAY_MS,
        "rows": rows,
    }))
    return tmp_path


# Hand-checked rate ladder: 5,1,4,2,3,1,5,2,4,1,3,2 (x1e-4)
RATES = [5e-4, 1e-4, 4e-4, 2e-4, 3e-4, 1e-4, 5e-4, 2e-4, 4e-4, 1e-4, 3e-4, 2e-4]


def test_rate_asof_between_settlements_returns_older_rate_no_lookahead(tmp_path):
    _write_bundle(tmp_path, "AAAUSDT", RATES)
    pit = FundingPIT("AAAUSDT", tmp_path)
    assert pit.n_settlements == len(RATES)

    anchor = _anchor_ms()
    # ts strictly between settlement #0 (t+0) and #1 (t+8h): must see the OLDER one.
    settlement, reason = pit.rate_asof(anchor + 4 * 3_600_000)
    assert reason is None
    assert settlement.rate == pytest.approx(5e-4)
    assert settlement.funding_time_utc == pd.Timestamp(anchor, unit="ms", tz="UTC").isoformat()

    # Exactly at a settlement stamp: that settlement is visible.
    settlement, reason = pit.rate_asof(anchor + 3 * EIGHT_H_MS)
    assert reason is None and settlement.rate == pytest.approx(2e-4)

    # One millisecond before a stamp: previous settlement.
    settlement, reason = pit.rate_asof(anchor + 3 * EIGHT_H_MS - 1)
    assert reason is None and settlement.rate == pytest.approx(4e-4)


def test_rate_asof_never_forward_fills_beyond_published(tmp_path):
    _write_bundle(tmp_path, "BBBUSDT", RATES)
    pit = FundingPIT("BBBUSDT", tmp_path)
    last_ms = _anchor_ms() + (len(RATES) - 1) * EIGHT_H_MS
    settlement, reason = pit.rate_asof(last_ms + 30 * DAY_MS)
    assert reason is None
    assert settlement.rate == pytest.approx(RATES[-1])


def test_percentile_math_hand_checked_full_window(tmp_path):
    _write_bundle(tmp_path, "CCCUSDT", RATES)
    pit = FundingPIT("CCCUSDT", tmp_path)
    # Query at settlement #11 (rate 2e-4) with a 30-day window: all 12 rates
    # are in the trailing window; values <= 2e-4 among
    # [5,1,4,2,3,1,5,2,4,1,3,2]e-4 -> six values (the three 1s + three 2s).
    ts_ms = _anchor_ms() + 11 * EIGHT_H_MS
    pct, reason = pit.percentile_asof(ts_ms, window_days=30)
    assert reason is None
    assert pct == pytest.approx(6 / 12)

    # Short window covering only the trailing three settlements [1,3,2]e-4:
    # last=2e-4, count(<=2e-4)=2 -> 2/3.
    pct_short, _ = pit.percentile_asof(ts_ms, window_days=1)
    assert pct_short == pytest.approx(2 / 3)


def test_percentile_bounds_and_min_rank(tmp_path):
    # Query at settlement #5 (rate 1e-4): only six settlements are published
    # by then and all fall inside the 30-day trailing window
    # [5,1,4,2,3,1]e-4 -> two values <= 1e-4 -> 2/6.
    _write_bundle(tmp_path, "DDDUSDT", RATES)
    pit = FundingPIT("DDDUSDT", tmp_path)
    ts_ms = _anchor_ms() + 5 * EIGHT_H_MS
    pct_min, reason = pit.percentile_asof(ts_ms, window_days=30)
    assert reason is None
    assert pct_min == pytest.approx(2 / 6)

    # Ascending ladder: last-asof rate is always the running maximum -> 1.0.
    _write_bundle(tmp_path, "EEEUSDT", sorted(RATES))
    pit_asc = FundingPIT("EEEUSDT", tmp_path)
    pct_max, _ = pit_asc.percentile_asof(_anchor_ms() + 11 * EIGHT_H_MS, window_days=30)
    assert pct_max == 1.0


def test_insufficient_history_fail_closed(tmp_path):
    short_rates = RATES[: MIN_PUBLISHED_SETTLEMENTS - 1]  # 9 < N=10
    _write_bundle(tmp_path, "EEEUSDT", short_rates)
    pit = FundingPIT("EEEUSDT", tmp_path)
    late_ts = _anchor_ms() + 100 * EIGHT_H_MS
    value, reason = pit.rate_asof(late_ts)
    assert value is None and reason == "insufficient_history"
    value, reason = pit.percentile_asof(late_ts, window_days=30)
    assert value is None and reason == "insufficient_history"


def test_empty_bundle_and_pre_history_fail_closed(tmp_path):
    _write_bundle(tmp_path, "FFFUSDT", [])
    pit = FundingPIT("FFFUSDT", tmp_path)
    value, reason = pit.rate_asof(_anchor_ms() + DAY_MS)
    assert value is None and reason == "empty_bundle"

    _write_bundle(tmp_path, "GGGUSDT", RATES)
    pit_g = FundingPIT("GGGUSDT", tmp_path)
    before_first = _anchor_ms() - DAY_MS
    value, reason = pit_g.rate_asof(before_first)
    assert value is None and reason == "no_settlement_asof"
    value, reason = pit_g.percentile_asof(before_first, window_days=30)
    assert value is None and reason == "no_settlement_asof"


def test_missing_bundle_raises_at_construction(tmp_path):
    with pytest.raises(ValueError, match="Missing funding bundle"):
        FundingPIT("NOPEUSDT", tmp_path)


def test_invalid_window_days_rejected(tmp_path):
    _write_bundle(tmp_path, "HHHUSDT", RATES)
    pit = FundingPIT("HHHUSDT", tmp_path)
    with pytest.raises(ValueError):
        pit.percentile_asof(_anchor_ms(), window_days=0)
