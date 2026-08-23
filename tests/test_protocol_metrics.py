"""A3 canonical-metrics tests incl. the legacy max_drawdown=0.0 regression."""

from __future__ import annotations

import json
import math
from pathlib import Path
from tempfile import TemporaryDirectory

import pandas as pd

from contracts.protocol import CanonicalMetrics, MetricValue
from research.optimize import _extract_metrics as legacy_extract_metrics
from research.protocol.metrics import extract_canonical_metrics


class FakeResult:
    """Duck-typed BacktestResult: stats dicts lacking the drawdown key."""

    def __init__(self, pnl_total="-12.5", expectancy="-1.25", returns=None):
        self.stats_pnls = {
            "USDT": {
                "PnL (total)": pnl_total,
                "Expectancy": expectancy,
            }
        }
        self.stats_returns = returns if returns is not None else {"Profit Factor": "0.50"}
        self.total_positions = 2


def _positions(*pnls: str) -> pd.DataFrame:
    base = pd.Timestamp("2026-01-01T00:00:00Z")
    rows = []
    for i, pnl in enumerate(pnls):
        opened = base + pd.Timedelta(minutes=10 * i)
        rows.append(
            {
                "position_id": f"p{i}",
                "instrument_id": "SOLUSDT-PERP.BINANCE",
                "entry": "BUY" if i % 2 == 0 else "SELL",
                "peak_qty": "1",
                "ts_opened": opened.isoformat(),
                "ts_closed": (opened + pd.Timedelta(minutes=5)).isoformat(),
                "realized_pnl": pnl,
            }
        )
    return pd.DataFrame(rows)


def test_legacy_extractor_defaults_drawdown_to_zero_documenting_bug():
    result = FakeResult()
    values = legacy_extract_metrics(result, "USDT")
    pnl, expectancy, profit_factor, win_rate, trades, sharpe, drawdown = values
    assert pnl == -12.5
    # THE BUG: 'Max Drawdown' absent -> silent 0.0 instead of null+reason.
    assert drawdown == 0.0


def test_canonical_extractor_returns_null_with_reason_for_same_input():
    metrics = extract_canonical_metrics(FakeResult(), pd.DataFrame())
    assert isinstance(metrics, CanonicalMetrics)
    assert metrics.max_drawdown.value is None
    assert metrics.max_drawdown.reason == "metric_missing_drawdown"
    assert metrics.max_dd_duration_bars.value is None
    assert metrics.net_canonical_pnl.value == -12.5
    assert metrics.expectancy_usdt.value == -1.25
    assert metrics.trades.value == 2.0
    assert metrics.funding_cost.reason == "metric_not_computed"
    assert metrics.top_fold_contribution_pct.reason == "metric_not_computed"


def test_no_metric_ever_defaults_to_silent_zero_without_reason():
    metrics = extract_canonical_metrics(FakeResult(), pd.DataFrame())
    for name in metrics.__dataclass_fields__:
        metric: MetricValue = getattr(metrics, name)
        if metric.value is None:
            assert metric.reason is not None
        if metric.value == 0.0 and metric.reason is not None:
            raise AssertionError(f"{name}: zero default disguised as missing")


def test_position_metrics_prefer_funding_adjusted_series():
    positions = _positions("10 USDT")
    positions.loc[0, "ts_closed"] = "2026-01-01T09:00:00Z"
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        symbol_dir = root / "SOLUSDT"
        symbol_dir.mkdir()
        payload = {
            "requested_start_ms": int(pd.Timestamp("2026-01-01T00:00:00Z").value // 1e6),
            "requested_end_ms": int(pd.Timestamp("2026-01-01T09:00:00Z").value // 1e6),
            "rows": [
                {
                    "fundingTime": int(pd.Timestamp("2026-01-01T08:00:00Z").timestamp() * 1000),
                    "fundingRate": "0.001",
                    "markPrice": "100",
                }
            ],
        }
        (symbol_dir / "funding.json").write_text(json.dumps(payload))
        metrics = extract_canonical_metrics(
            FakeResult(pnl_total="10", expectancy="10"),
            positions,
            root,
        )
    assert metrics.trades.value == 1.0
    assert metrics.gross_pnl.value == 10.0
    assert metrics.funding_cost.value == -0.1
    assert math.isclose(metrics.net_canonical_pnl.value, 9.9)
    assert math.isclose(metrics.expectancy_usdt.value, 9.9)
    assert metrics.position_pf.value == float("inf")
    assert metrics.win_rate.value == 1.0


def test_summary_dict_only_path_uses_aggregates():
    summary = {
        "trades": 3,
        "pnl_before_funding": 30.0,
        "funding_net": -3.0,
        "pnl_after_funding": 27.0,
        "expectancy_after_funding": 9.0,
        "profit_factor_after_funding": 2.0,
        "win_rate_after_funding": 0.75,
    }
    metrics = extract_canonical_metrics(FakeResult(), pd.DataFrame(), summary)
    assert metrics.gross_pnl.value == 30.0
    assert metrics.funding_cost.value == -3.0
    assert metrics.net_canonical_pnl.value == 27.0
    assert metrics.expectancy_usdt.value == 9.0
    assert metrics.position_pf.value == 2.0
    assert metrics.win_rate.value == 0.75


def test_drawdown_and_duration_computed_from_equity_timeline():
    positions = _positions("10 USDT", "-5 USDT", "-20 USDT")
    positions.loc[1, "ts_closed"] = "2026-01-01T00:11:00Z"
    positions.loc[2, "ts_closed"] = "2026-01-01T00:41:00Z"
    metrics = extract_canonical_metrics(
        FakeResult(), positions, bar_seconds=60
    )
    # equity: 10 -> 5 -> -15 ; peak 10 ; worst (=-15-10)/max(10,1) = -2.5
    assert math.isclose(metrics.max_drawdown.value, -2.5)
    # longest underwater stretch: 00:11 -> 00:41 = 1800s / 60s bars = 30
    assert metrics.max_dd_duration_bars.value == 30.0


def test_exposure_pct_from_merged_position_intervals():
    base = pd.Timestamp("2026-01-01T00:00:00Z")
    positions = pd.DataFrame(
        [
            {
                "position_id": "a",
                "instrument_id": "SOLUSDT-PERP.BINANCE",
                "entry": "BUY",
                "peak_qty": "1",
                "ts_opened": base.isoformat(),
                "ts_closed": (base + pd.Timedelta(minutes=10)).isoformat(),
                "realized_pnl": "1 USDT",
            },
            {
                "position_id": "b",
                "instrument_id": "SOLUSDT-PERP.BINANCE",
                "entry": "SELL",
                "peak_qty": "1",
                "ts_opened": (base + pd.Timedelta(minutes=20)).isoformat(),
                "ts_closed": (base + pd.Timedelta(minutes=50)).isoformat(),
                "realized_pnl": "2 USDT",
            },
        ]
    )
    metrics = extract_canonical_metrics(FakeResult(), positions)
    # in-market 600 + 1800 = 2400 of a 3000s window -> 80%
    assert math.isclose(metrics.exposure_pct.value, 80.0)


def test_return_stats_lookups_and_missing_reasons():
    returns = {
        "Sharpe Ratio (252 days)": 1.5,
        "Sortino Ratio (252 days)": 2.1,
        "Max Drawdown": "-8.5%",
    }
    result = FakeResult(returns=returns)
    metrics = extract_canonical_metrics(result, pd.DataFrame())
    assert metrics.sharpe.value == 1.5
    assert metrics.sortino.value == 2.1
    assert metrics.max_drawdown.value == -8.5
    assert metrics.turnover.value is None
    assert metrics.turnover.reason == "metric_not_computed"
