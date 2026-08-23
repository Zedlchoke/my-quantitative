"""Canonical metrics extractor (the 0.0-default fix).

``extract_canonical_metrics`` is the ONLY sanctioned way to turn a backtest
result into ``contracts.protocol.CanonicalMetrics``.  Unavailable metrics are
returned as ``MetricValue.missing(<reason>)`` (null + reason code); a silent
``0.0`` default is forbidden.  See ``tests/test_protocol_metrics.py`` for the
regression test against the legacy ``research.optimize._extract_metrics``
behaviour which returned ``max_drawdown=0.0`` when the stats key was absent.

Formulas
--------
Position metrics (prefer funding-adjusted realized PnL series):

    trades            = len(series)
    gross_pnl         = sum(raw engine realized_pnl)           (pre-funding)
    funding_cost      = funding_net cashflow sum (negative = paid)
    net_canonical_pnl = gross_pnl + funding_cashflows
                      = sum(realized_pnl_after_funding)
    expectancy_usdt   = net_canonical_pnl / trades
    position_pf       = sum(wins) / |sum(losses)| on net series
                        (inf when there are no losses; 0.0 only if no wins
                         AND no losses is impossible since trades > 0)
    win_rate          = #wins / trades (descriptive only)

When no funding evidence exists: gross comes from ``result.stats_pnls``
(``PnL (total)`` for ``base_currency``, else the positions report), and
``funding_cost`` / funding-dependent adjustments are
``missing('metric_not_computed')``; then ``net_canonical_pnl == gross_pnl``.

Return-series / equity-timeline metrics:

    equity timeline E_0..E_n = cumulative sum of per-position net PnL ordered
    by close time (anchor 0).  Running peak M_t = max(E_0..E_t).
    relative drawdown_t = (E_t - M_t) / max(M_t, 1.0 USDT)   (<= 0)
    max_drawdown        = min_t drawdown_t                   (negative number)
    underwater interval = consecutive samples with E_t < M_t
    max_dd_duration_bars= longest underwater span in seconds / bar_seconds,
                          where bar_seconds is caller-supplied or inferred as
                          the median delta between consecutive close times.
    exposure_pct        = 100 * union([ts_opened, ts_closed]) /
                          (max(ts_closed) - min(ts_opened))
    sharpe/sortino/turnover are taken from ``stats_returns`` keys matched
    case-insensitively by substring; otherwise missing.

``top_fold_contribution_pct`` is always ``missing('metric_not_computed')``
here — it is computed by the gates layer from fold rows.
"""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Iterable

import pandas as pd

from contracts.protocol import CanonicalMetrics, MetricValue
from reports.funding import FundingAudit, build_funding_audit


def _missing(reason: str = "metric_not_computed") -> MetricValue:
    return MetricValue.missing(reason)


def _parse_money(value: Any) -> float | None:
    """Parse Nautilus money cells like ``'12.34 USDT'`` / Decimal / float."""
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    text = str(value).strip()
    if not text or text.lower() == "nat":
        return None
    token = text.split()[0] if " " in text else text
    token = token.rstrip("%")
    try:
        return float(token)
    except ValueError:
        return None


def _lookup(mapping: dict, *names: str, contains: str | None = None) -> float | None:
    """Return first parseable value for exact names, else substring match.

    Unlike the legacy ``research.optimize._metric_by_name`` this returns None
    instead of 0.0 when nothing matches.
    """
    if not mapping:
        return None
    for name in names:
        if name in mapping and mapping[name] is not None:
            parsed = _parse_money(mapping[name])
            if parsed is not None:
                return parsed
    if contains:
        needle = contains.lower()
        for key, value in mapping.items():
            if needle in str(key).lower() and value is not None:
                parsed = _parse_money(value)
                if parsed is not None:
                    return parsed
    return None


def _series_from_frame(frame: pd.DataFrame, column: str) -> list[float]:
    if frame.empty or column not in frame.columns:
        return []
    values = []
    for raw in frame[column]:
        parsed = _parse_money(raw)
        if parsed is not None:
            values.append(parsed)
    return values


def _timestamps(frame: pd.DataFrame, column: str) -> list[pd.Timestamp]:
    if frame.empty or column not in frame.columns:
        return []
    stamps: list[pd.Timestamp] = []
    for raw in frame[column]:
        try:
            ts = pd.Timestamp(raw)
        except (TypeError, ValueError):
            continue
        if pd.isna(ts):
            continue
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        stamps.append(ts)
    return sorted(stamps)


def _aligned_timeline(
    frame: pd.DataFrame,
    pnl_column: str,
) -> tuple[list[float], list[pd.Timestamp]]:
    """Return (pnls, close_times) sorted by close time so rows stay paired."""
    if frame.empty or pnl_column not in frame.columns or "ts_closed" not in frame.columns:
        return [], []
    rows: list[tuple[pd.Timestamp, float]] = []
    for _, row in frame.iterrows():
        pnl = _parse_money(row.get(pnl_column))
        try:
            ts = pd.Timestamp(row["ts_closed"])
        except (TypeError, ValueError):
            continue
        if pnl is None or pd.isna(ts):
            continue
        if ts.tzinfo is None:
            ts = ts.tz_localize("UTC")
        rows.append((ts, pnl))
    rows.sort(key=lambda item: item[0])
    return [pnl for _, pnl in rows], [ts for ts, _ in rows]


def _drawdown_from_timeline(
    pnls: list[float],
    close_times: list[pd.Timestamp],
    bar_seconds: float | None,
) -> tuple[float | None, int | None]:
    """Compute (max_drawdown, max_dd_duration_bars) from closed-position PnL.

    Drawdown is relative to the running peak of the zero-anchored cumulative
    PnL curve (denominator floored at 1.0 to stay defined before any profit);
    it is reported as a negative number, consistent with nautilus output.
    Duration converts the longest underwater span to bars using ``bar_seconds``
    or the median inter-close interval.
    """
    if not pnls:
        return None, None
    equity = 0.0
    peak = 0.0
    worst = 0.0
    underwater_start: pd.Timestamp | None = None
    worst_span_seconds: float = 0.0
    previous_time: pd.Timestamp | None = None
    deltas: list[float] = []

    for pnl, ts in zip(pnls, close_times, strict=False):
        equity += pnl
        peak = max(peak, equity)
        drawdown = (equity - peak) / max(peak, 1.0)
        worst = min(worst, drawdown)
        if previous_time is not None:
            deltas.append((ts - previous_time).total_seconds())
        previous_time = ts
        if equity < peak:
            if underwater_start is None:
                underwater_start = ts
            span = (ts - underwater_start).total_seconds()
            worst_span_seconds = max(worst_span_seconds, span)
        else:
            underwater_start = None

    seconds = bar_seconds
    if seconds is None and deltas:
        positive = sorted(d for d in deltas if d > 0)
        if positive:
            seconds = positive[len(positive) // 2]
    duration_bars = (
        int(round(worst_span_seconds / seconds)) if seconds and worst_span_seconds > 0 else None
    )
    worst_value = worst if worst < 0 else None
    return worst_value, duration_bars


def _exposure_pct(positions: pd.DataFrame) -> float | None:
    opened = _timestamps(positions, "ts_opened")
    closed = _timestamps(positions, "ts_closed")
    if not opened or len(opened) != len(closed):
        return None
    intervals = sorted(zip(opened, closed, strict=True))
    merged: list[tuple[pd.Timestamp, pd.Timestamp]] = []
    for start, end in intervals:
        if end <= start:
            continue
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    if not merged:
        return None
    span = (merged[-1][1] - merged[0][0]).total_seconds()
    if span <= 0:
        return None
    in_market = sum((end - start).total_seconds() for start, end in merged)
    return 100.0 * in_market / span


def _resolve_funding_inputs(
    funding_audit_summary_or_none: dict | FundingAudit | str | Path | None,
    positions_report_df: pd.DataFrame,
) -> tuple[dict | None, pd.DataFrame]:
    """Normalise the third argument into (summary, adjusted_or_raw_frame)."""
    arg = funding_audit_summary_or_none
    if arg is None:
        return None, positions_report_df
    if isinstance(arg, FundingAudit):
        return dict(arg.summary), arg.adjusted_positions
    if isinstance(arg, (str, Path)):
        audit = build_funding_audit(positions_report_df, Path(arg))
        return dict(audit.summary), audit.adjusted_positions
    if isinstance(arg, dict):
        return arg, positions_report_df
    raise TypeError(f"unsupported funding argument type: {type(arg)!r}")


def _pnl_stats_from_series(series: list[float]) -> tuple[float, float, float]:
    total = math.fsum(series)
    wins = [v for v in series if v > 0]
    losses = [v for v in series if v <= 0]
    gross_win = math.fsum(wins)
    gross_loss = abs(math.fsum(losses))
    pf = (gross_win / gross_loss) if gross_loss else math.inf
    win_rate = (len(wins) / len(series)) if series else 0.0
    return total, pf, win_rate


def extract_canonical_metrics(
    result: Any,
    positions_report_df: pd.DataFrame,
    funding_audit_summary_or_none: dict | FundingAudit | str | Path | None = None,
    *,
    base_currency: str = "USDT",
    bar_seconds: float | None = None,
) -> CanonicalMetrics:
    """Build :class:`CanonicalMetrics` without ever defaulting to 0.0.

    ``result`` is duck-typed (needs ``stats_pnls``, ``stats_returns``,
    ``total_positions``).  ``positions_report_df`` is the trader positions
    report (may be empty).  The third argument may be a precomputed funding
    audit summary dict, a full :class:`FundingAudit`, a funding bundle root
    path (an audit is built via ``reports.funding.build_funding_audit``), or
    None when no funding evidence exists.
    """
    stats_pnls: dict = getattr(result, "stats_pnls", None) or {}
    stats_returns: dict = getattr(result, "stats_returns", None) or {}
    summary, pnl_frame = _resolve_funding_inputs(
        funding_audit_summary_or_none, positions_report_df
    )

    raw_series = _series_from_frame(positions_report_df, "realized_pnl")

    commission_known = _lookup(stats_pnls, contains="commission")
    slippage_known = _lookup(stats_pnls, "Slippage", contains="slippage")

    if summary is not None:
        trades_val = summary.get("trades")
        trades = MetricValue.known(float(trades_val)) if trades_val is not None else _missing()
        gross_val = summary.get("pnl_before_funding")
        if gross_val is None:
            gross_val = math.fsum(raw_series) if raw_series else None
        gross = MetricValue.known(float(gross_val)) if gross_val is not None else _missing()
        funding_val = summary.get("funding_net")
        funding = (
            MetricValue.known(float(funding_val))
            if funding_val is not None
            else _missing("metric_not_computed")
        )
        net_val = summary.get("pnl_after_funding")
        if net_val is None:
            net_val = (
                (gross.value + (funding.value or 0.0))
                if gross.value is not None and funding.value is not None
                else None
            )
        net = MetricValue.known(float(net_val)) if net_val is not None else _missing()
        exp_val = summary.get("expectancy_after_funding")
        if exp_val is None and net.value is not None and trades.value:
            exp_val = net.value / trades.value
        expectancy = MetricValue.known(float(exp_val)) if exp_val is not None else _missing()
        pf_val = summary.get("profit_factor_after_funding")
        wr_val = summary.get("win_rate_after_funding")
        series = _series_from_frame(pnl_frame, "realized_pnl_after_funding") or raw_series
        if series and (pf_val is None or wr_val is None):
            _series_total, series_pf, series_wr = _pnl_stats_from_series(series)
            pf_val = pf_val if pf_val is not None else series_pf
            wr_val = wr_val if wr_val is not None else series_wr
        position_pf = MetricValue.known(float(pf_val)) if pf_val is not None else _missing()
        win_rate = MetricValue.known(float(wr_val)) if wr_val is not None else _missing()
    elif raw_series:
        total, pf, wr = _pnl_stats_from_series(raw_series)
        pnl_group = stats_pnls.get(base_currency, {})
        stats_total = _lookup(pnl_group, "PnL (total)", contains="pnl")
        gross = MetricValue.known(stats_total if stats_total is not None else total)
        trades = MetricValue.known(
            float(getattr(result, "total_positions", None) or len(raw_series))
        )
        expectancy = MetricValue.known(total / len(raw_series))
        position_pf = MetricValue.known(pf)
        win_rate = MetricValue.known(wr)
        funding = _missing("metric_not_computed")
        net = MetricValue.known(total)
    else:
        pnl_group = stats_pnls.get(base_currency, {})
        stats_total = _lookup(pnl_group, "PnL (total)", contains="pnl")
        stats_expectancy = _lookup(pnl_group, "Expectancy", contains="expectancy")
        total_positions = getattr(result, "total_positions", None)
        gross = MetricValue.known(stats_total) if stats_total is not None else _missing()
        trades = (
            MetricValue.known(float(total_positions))
            if total_positions
            else _missing("metric_not_computed")
        )
        expectancy = (
            MetricValue.known(stats_expectancy)
            if stats_expectancy is not None
            else _missing("metric_not_computed")
        )
        position_pf = _missing("metric_not_computed")
        win_rate = _missing("metric_not_computed")
        funding = _missing("metric_not_computed")
        net = gross

    commission = (
        MetricValue.known(commission_known) if commission_known is not None else _missing()
    )
    slippage = MetricValue.known(slippage_known) if slippage_known is not None else _missing()

    sharpe_val = _lookup(stats_returns, contains="sharpe")
    sortino_val = _lookup(stats_returns, contains="sortino")
    turnover_val = _lookup(stats_returns, contains="turnover")

    dd_val = _lookup(stats_returns, "Max Drawdown", "Max (Drawdown)", contains="drawdown")
    timeline_series, close_times = _aligned_timeline(pnl_frame, "realized_pnl_after_funding")
    if not timeline_series:
        timeline_series, close_times = _aligned_timeline(positions_report_df, "realized_pnl")
    computed_dd: float | None = None
    computed_duration: int | None = None
    if timeline_series:
        computed_dd, computed_duration = _drawdown_from_timeline(
            timeline_series, close_times, bar_seconds
        )

    max_drawdown = (
        MetricValue.known(dd_val)
        if dd_val is not None
        else (
            MetricValue.known(computed_dd)
            if computed_dd is not None
            else _missing("metric_missing_drawdown")
        )
    )
    duration = (
        MetricValue.known(float(computed_duration))
        if computed_duration is not None
        else _missing("metric_not_computed")
    )
    exposure_val = _exposure_pct(positions_report_df)
    exposure = MetricValue.known(exposure_val) if exposure_val is not None else _missing()

    def _ratio(value: float | None) -> MetricValue:
        return MetricValue.known(value) if value is not None else _missing()

    return CanonicalMetrics(
        trades=trades,
        net_canonical_pnl=net,
        expectancy_usdt=expectancy,
        position_pf=position_pf,
        win_rate=win_rate,
        gross_pnl=gross,
        commission_cost=commission,
        slippage_cost=slippage,
        funding_cost=funding,
        max_drawdown=max_drawdown,
        max_dd_duration_bars=duration,
        sharpe=_ratio(sharpe_val),
        sortino=_ratio(sortino_val),
        exposure_pct=exposure,
        turnover=_ratio(turnover_val),
        top_fold_contribution_pct=_missing("metric_not_computed"),
    )


def fold_contribution_pct(fold_rows: Iterable[dict]) -> float | None:
    """Share of total PnL contributed by the largest fold (fraction 0..1+).

    Computed here for the gates/scorecard callers; the canonical metrics
    record leaves ``top_fold_contribution_pct`` missing on purpose.
    """
    rows = [row for row in fold_rows]
    pnls = [float(row.get("pnl_after_cost", 0.0) or 0.0) for row in rows]
    total = math.fsum(pnls)
    if total <= 0 or not pnls:
        return None
    return max(abs(pnl) for pnl in pnls) / total
