"""Portfolio-level metrics for Sprint V4 cross-sectional experiments (A3).

Pure functions only -- no I/O, no engine imports.  Every estimator is FROZEN
here and declared verbatim in each experiment's launch manifest /
``beta_report.json``:

* ``realized_btc_beta``      OLS slope of portfolio daily returns on BTCUSDT
                             daily returns aligned by UTC date (PLAN section
                             19.3).  Fewer than two overlapping dates or a
                             zero-variance BTC series => ``(None, reason)``
                             (fail-closed; never a silent 0.0 beta).
* ``turnover_from_orders``   sum of |quantity x fill_price| over executed
                             orders (target-weight-delta turnover proxy per
                             PLAN section 19.2).
* ``top_symbol_contribution`` share of POSITIVE-aggregate PnL per symbol
                             (denominator = sum of positive per-symbol
                             aggregates only, PLAN section 23 XG3/XG5).
* ``fold_contribution``      same positive-aggregate convention per fold.
* ``max_drawdown_from_equity`` max peak-to-trough fractional drawdown plus
                             the underwater duration of that episode in days.
* ``expectancy_r_portfolio`` mean of per-leg R multiples.  The shared-capital
                             rank engine has NO stop concept, so A2 legs carry
                             no initial risk: callers must pass
                             ``r_missing_reason="MISSING_R_NORMALIZATION"``
                             and propagate ``expect_R=None`` + reason instead
                             of fabricating an R value (documented limitation).
                             DEPRECATED as a GATE INPUT since V5: portfolio
                             gates use the family-aware block below (daily
                             Sharpe, median fold return, chained MDD,
                             reconciled contributions) -- never a fabricated R.

Sprint V5 family-aware additions (PLAN section 31.4; owner A3):

* ``daily_sharpe``           mean/std of daily net returns (risk-free 0),
                             fail-closed ``(None, reason)`` on degenerate
                             input.  Estimator id frozen:
                             ``DAILY_SHARPE_RF0_V1``.
* ``median_fold_return``     median across fold return series (no fake-R).
* ``per_symbol_contribution``
                             / ``per_fold_contribution``: shares computed ONLY
                             over the canonical population that produced the
                             reported total PnL; ``sum(parts) == total`` is
                             asserted within 1e-9 or
                             :class:`ContributionMismatch` is raised (F01/F02
                             fix: contribution can never silently collapse to
                             0 from a field mismatch).
* ``chained_returns_mdd``    true walk-forward MDD computed on the CHAINED
                             fold-return path -- reset-to-100k equity segments
                             can never pass through this check (F03 fix).

Timestamps may be int nanoseconds (engine convention) or ISO-8601 strings;
both are normalized deterministically.
"""

from __future__ import annotations

import math
import statistics
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping, Sequence

#: Declared frozen estimator identifiers (recorded in manifests/reports).
BETA_ESTIMATOR = "OLS_SLOPE_ALIGNED_DAILY_RETURNS_V1"
TURNOVER_DEFINITION = "SUM_ABS_QTY_TIMES_FILL_PRICE_V1"
CONTRIBUTION_DENOMINATOR = "POSITIVE_AGGREGATE_PNL_ONLY_V1"
MDD_DEFINITION = "MAX_PEAK_TO_TROUGH_FRACTION_EQUITY_CURVE_V1"
DAILY_SHARPE_ESTIMATOR = "DAILY_SHARPE_RF0_V1"
MEDIAN_FOLD_RETURN_ESTIMATOR = "MEDIAN_FOLD_RETURN_V1"
CHAINED_MDD_ESTIMATOR = "CHAINED_FOLD_RETURNS_MDD_V1"

#: Reconciliation tolerance for contribution identities (PLAN 31.2 item 3).
CONTRIBUTION_TOLERANCE = 1e-9

MISSING_R_NORMALIZATION = "MISSING_R_NORMALIZATION"


class ContributionMismatch(ValueError):
    """Per-part PnL does not reconcile to the reported total within 1e-9.

    Raised instead of silently emitting zero/shifted contributions when the
    aggregation population diverges from the PnL population (F01/F02).
    """

_NS_DAY = 86_400_000_000_000


# ----------------------------- timestamp utils ------------------------------ #
def _ts_to_ns(value: Any) -> int:
    """Normalize int-nanoseconds / ISO-8601 timestamps to epoch ns."""
    if isinstance(value, bool):  # pragma: no cover - defensive
        raise TypeError(f"invalid timestamp: {value!r}")
    if isinstance(value, (int, float)):
        return int(value)
    text = str(value).strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    parsed = datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return int(parsed.timestamp() * 1_000_000_000)


def _date_key(value: Any) -> str:
    """UTC calendar-date key ('YYYY-MM-DD') for alignment."""
    ns = _ts_to_ns(value)
    return datetime.fromtimestamp(ns / 1_000_000_000, tz=timezone.utc).strftime("%Y-%m-%d")


# -------------------------------- beta -------------------------------------- #
def realized_btc_beta(
    portfolio_daily_returns: Mapping[Any, float] | Sequence[tuple[Any, float]],
    btc_daily_returns: Mapping[Any, float] | Sequence[tuple[Any, float]],
) -> tuple[float | None, str | None]:
    """OLS slope beta of portfolio on BTC daily returns, aligned by UTC date.

    Returns ``(beta, None)`` or ``(None, reason)`` with reason one of
    ``insufficient_overlap`` (<2 common dates) or ``zero_btc_variance``
    (BTC constant over the overlap).  Fail-closed by construction.
    """
    port = _as_date_map(portfolio_daily_returns)
    btc = _as_date_map(btc_daily_returns)
    common = sorted(set(port) & set(btc))
    if len(common) < 2:
        return None, "insufficient_overlap"
    xs = [btc[d] for d in common]
    ys = [port[d] for d in common]
    mean_x = math.fsum(xs) / len(xs)
    mean_y = math.fsum(ys) / len(ys)
    sxx = math.fsum((x - mean_x) ** 2 for x in xs)
    if sxx <= 0.0:
        return None, "zero_btc_variance"
    sxy = math.fsum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    return sxy / sxx, None


def _as_date_map(source: Mapping[Any, float] | Sequence[tuple[Any, float]]) -> dict[str, float]:
    items: Iterable[tuple[Any, float]]
    if isinstance(source, Mapping):
        items = source.items()
    else:
        items = source  # type: ignore[assignment]
    out: dict[str, float] = {}
    for ts, ret in items:
        out[_date_key(ts)] = float(ret)
    return out


def daily_returns_from_equity_curve(equity_curve: Sequence[tuple[Any, float]]) -> dict[str, float]:
    """Per-UTC-date simple returns from an equity curve (last sample per day).

    Multiple intraday equity samples collapse to the LAST observation of each
    UTC date; dates keep chronological order for deterministic iteration.
    """
    if not equity_curve:
        return {}
    ordered = sorted(equity_curve, key=lambda row: _ts_to_ns(row[0]))
    last_equity: dict[str, float] = {}
    order: list[str] = []
    for ts, equity in ordered:
        key = _date_key(ts)
        if key not in last_equity:
            order.append(key)
        last_equity[key] = float(equity)
    returns: dict[str, float] = {}
    previous_key: str | None = None
    previous_equity = 0.0
    for key in order:
        equity = last_equity[key]
        if previous_key is not None and previous_equity > 0:
            returns[key] = equity / previous_equity - 1.0
        previous_key, previous_equity = key, equity
    return returns


def btc_daily_returns_from_closes(
    daily_closes: Sequence[tuple[int, float]],
) -> dict[str, float]:
    """Simple daily returns keyed by UTC date from [(ts_ns, close)] samples."""
    ordered = sorted(daily_closes, key=lambda row: _ts_to_ns(row[0]))
    closes_by_date: dict[str, float] = {}
    order: list[str] = []
    for ts, close in ordered:
        key = _date_key(ts)
        if key not in closes_by_date:
            order.append(key)
        closes_by_date[key] = float(close)
    returns: dict[str, float] = {}
    previous_close = 0.0
    has_previous = False
    for key in order:
        close = closes_by_date[key]
        if has_previous and previous_close > 0:
            returns[key] = close / previous_close - 1.0
        previous_close, has_previous = close, True
    return returns


# ------------------------------- turnover ----------------------------------- #
def turnover_from_orders(
    orders: Iterable[Mapping[str, Any]],
    *,
    equity: float | None = None,
) -> float:
    """Total traded notional sum(|qty| * fill_price); optional per-equity norm.

    Order rows missing quantity/fill_price are skipped silently ONLY when
    they carry an explicit non-executed marker (``status`` not in
    {None, FILLED, EXECUTED}); otherwise they raise (fail-closed accounting).
    """
    total = 0.0
    for row in orders:
        status = row.get("status")
        if status not in (None, "FILLED", "EXECUTED"):
            continue
        qty = row.get("quantity", row.get("qty"))
        price = row.get("fill_price", row.get("price"))
        if qty is None or price is None:
            raise ValueError(f"executed order missing qty/price: {row!r}")
        total += abs(float(qty)) * abs(float(price))
    if equity is not None and equity > 0:
        return total / float(equity)
    return total


# ----------------------------- contributions -------------------------------- #
def _positive_aggregate_shares(aggregates: Mapping[str, float]) -> dict[str, float]:
    denominator = math.fsum(v for v in aggregates.values() if v > 0)
    if denominator <= 0:
        return {}
    return {
        key: value / denominator
        for key, value in sorted(aggregates.items())
        if value > 0
    }


def top_symbol_contribution(closed_legs: Iterable[Mapping[str, Any]]) -> tuple[str | None, float]:
    """(top_symbol, share) of positive-aggregate PnL per symbol.

    Aggregate PnL is summed PER SYMBOL first (a symbol with offsetting legs
    counts once), then shares use the positive-aggregate denominator.  No
    positive PnL anywhere => ``(None, 0.0)``.
    """
    aggregates: dict[str, float] = {}
    for leg in closed_legs:
        symbol = str(leg["symbol"])
        pnl = float(leg.get("canonical_pnl", leg.get("pnl", 0.0)) or 0.0)
        aggregates[symbol] = aggregates.get(symbol, 0.0) + pnl
    shares = _positive_aggregate_shares(aggregates)
    if not shares:
        return None, 0.0
    top_symbol = min(shares, key=lambda k: (-shares[k], k))
    return top_symbol, shares[top_symbol]


def fold_contribution(fold_pnls: Mapping[str, float]) -> tuple[str | None, float]:
    """(top_fold_id, share) using the same positive-aggregate convention."""
    shares = _positive_aggregate_shares({str(k): float(v) for k, v in fold_pnls.items()})
    if not shares:
        return None, 0.0
    top_fold = min(shares, key=lambda k: (-shares[k], k))
    return top_fold, shares[top_fold]


# ------------------------------ drawdown ------------------------------------ #
def max_drawdown_from_equity(
    equity_curve: Sequence[tuple[Any, float]],
) -> tuple[float, float]:
    """(max_drawdown_fraction, underwater_duration_days) from equity curve.

    Duration spans from the running-peak timestamp preceding the worst trough
    until the FIRST timestamp equity recovers that peak, or until the curve
    end when never recovered.  Empty/degenerate curves => (0.0, 0.0).
    """
    if not equity_curve:
        return 0.0, 0.0
    ordered = sorted(equity_curve, key=lambda row: _ts_to_ns(row[0]))
    stamps = [_ts_to_ns(row[0]) for row in ordered]
    values = [float(row[1]) for row in ordered]
    peak_value = -math.inf
    peak_index = 0
    best_mdd = 0.0
    best_duration_days = 0.0
    episode_peak_index: int | None = None
    episode_dd = 0.0

    def _close(recovery_index: int) -> None:
        nonlocal best_mdd, best_duration_days, episode_peak_index, episode_dd
        if episode_peak_index is not None and episode_dd > best_mdd:
            best_mdd = episode_dd
            span_ns = stamps[recovery_index] - stamps[episode_peak_index]
            best_duration_days = max(0.0, span_ns / _NS_DAY)
        episode_peak_index = None
        episode_dd = 0.0

    for index, equity in enumerate(values):
        if equity > peak_value:
            _close(index)
            peak_value = equity
            peak_index = index
            continue
        if peak_value <= 0:
            continue
        if equity < peak_value:
            if episode_peak_index is None:
                episode_peak_index = peak_index
                episode_dd = 0.0
            episode_dd = max(episode_dd, (peak_value - equity) / peak_value)
    _close(len(values) - 1)
    return best_mdd, best_duration_days


# --------------------------- expectancy R ----------------------------------- #
def expectancy_r_portfolio(
    r_multiples: Sequence[float] | None,
    *,
    r_missing_reason: str = MISSING_R_NORMALIZATION,
) -> tuple[float | None, str | None]:
    """Mean per-leg R multiple; ``(None, r_missing_reason)`` when unavailable.

    The V4 shared-capital engine holds no per-leg stop, so legs have no
    initial-risk normalization: callers pass ``None`` and must treat the
    experiment as lacking R evidence (XG3 then reports INCONCLUSIVE for the
    expectancy-R check rather than guessing a proxy).

    DEPRECATED for gate use since Sprint V5 (F07): portfolio gates must use
    :func:`daily_sharpe` / :func:`median_fold_return` instead of any
    expectancy-R proxy.  Kept only for legacy artifact readers.
    """
    if r_multiples is None:
        return None, r_missing_reason
    values = [float(r) for r in r_multiples]
    if not values:
        return None, r_missing_reason
    return math.fsum(values) / len(values), None


# --------------------------------------------------------------------------- #
# Sprint V5 family-aware metrics (PLAN section 31.4; owner A3).  No fake R.
# --------------------------------------------------------------------------- #
def daily_sharpe(
    source: Sequence[tuple[Any, float]] | Mapping[Any, float] | Sequence[float],
    *,
    rf: float = 0.0,
) -> tuple[float | None, str | None]:
    """Annualization-free Sharpe of daily net returns (risk-free ``rf``).

    Accepts either an equity curve (``[(ts, equity), ...]`` -- converted via
    :func:`daily_returns_from_equity_curve`) or daily returns directly (a
    mapping keyed by date/timestamp, or a plain sequence ordered by day).
    Returns ``(sharpe, None)`` or ``(None, reason)``:

    * ``insufficient_observations``  fewer than 2 return samples;
    * ``zero_variance``              sample stdev of excess returns is 0.

    Estimator id: :data:`DAILY_SHARPE_RF0_V1` (mean / sample-stdev of
    ``r_t - rf``, ddof=1; NOT annualized -- callers must never rescale to an
    annual figure without recording the factor).
    """
    returns: list[float]
    if isinstance(source, Mapping):
        date_map = _as_date_map(source)
        returns = [date_map[k] for k in sorted(date_map)]
    elif source and isinstance(source[0], (tuple, list)):
        # Equity-curve shaped: [(timestamp, equity), ...]
        curve_returns = daily_returns_from_equity_curve(source)  # type: ignore[arg-type]
        returns = [curve_returns[k] for k in sorted(curve_returns)]
    else:
        returns = [float(v) for v in source]  # type: ignore[union-attr,arg-type]
    excess = [float(v) - float(rf) for v in returns]
    if len(excess) < 2:
        return None, "insufficient_observations"
    mean = math.fsum(excess) / len(excess)
    stdev = statistics.stdev(excess)
    if stdev <= 0.0:
        return None, "zero_variance"
    return mean / stdev, None


def median_fold_return(fold_returns: Sequence[float | None]) -> float | None:
    """Median across per-fold returns; ``None`` when nothing is measurable.

    ``None`` entries are treated as missing measurements and dropped; an
    empty (or all-missing) input yields ``None`` so gates report
    ``metric_missing`` fail-closed instead of a fabricated median.
    Estimator id: :data:`MEDIAN_FOLD_RETURN_ESTIMATOR`.
    """
    values = [float(v) for v in (fold_returns or []) if v is not None]
    if not values:
        return None
    return statistics.median(values)


def _canonical_pnl_of(leg: Mapping[str, Any]) -> float:
    """Strictly read the CANONICAL PnL field; no silent realized_pnl fallback."""
    if "canonical_pnl" not in leg:
        raise ContributionMismatch(
            f"leg missing canonical_pnl field (got keys {sorted(leg)}); "
            "refusing silent realized_pnl fallback (F01)"
        )
    value = leg["canonical_pnl"]
    if value is None:
        raise ContributionMismatch("leg canonical_pnl is null")
    return float(value)


def _reconcile_parts(
    parts: Mapping[str, float],
    total_pnl: float,
    population_note: str,
) -> None:
    scale = max(1.0, abs(float(total_pnl)))
    drift = abs(math.fsum(parts.values()) - float(total_pnl))
    if drift > CONTRIBUTION_TOLERANCE * scale:
        raise ContributionMismatch(
            f"{population_note}: sum(parts)={math.fsum(parts.values())!r} != "
            f"total_pnl={total_pnl!r} (drift {drift!r} > "
            f"{CONTRIBUTION_TOLERANCE} * scale)"
        )


def per_symbol_contribution(
    closed_legs: Iterable[Mapping[str, Any]],
    *,
    total_pnl: float,
    population: Sequence[str] | None = None,
) -> dict[str, float]:
    """Per-symbol shares of positive-aggregate PnL over the canonical population.

    ``population`` is the explicit canonical symbol list whose legs produced
    ``total_pnl``.  When omitted it defaults to exactly the symbols present
    in ``closed_legs`` (the only defensible implicit choice).  Legs outside
    the declared population raise :class:`ContributionMismatch`, as does
    ``sum(per-symbol aggregates)`` diverging from ``total_pnl`` beyond 1e-9
    scaled -- contributions can therefore never silently collapse to 0 the
    way the V4 artifacts did (F02).
    """
    aggregates: dict[str, float] = {}
    allowed = {str(s) for s in population} if population is not None else None
    for leg in closed_legs:
        symbol = str(leg["symbol"])
        if allowed is not None and symbol not in allowed:
            raise ContributionMismatch(
                f"symbol {symbol!r} outside declared canonical population"
            )
        aggregates[symbol] = aggregates.get(symbol, 0.0) + _canonical_pnl_of(leg)
    if population is not None:
        for symbol in allowed or set():
            aggregates.setdefault(symbol, 0.0)
    if not aggregates:
        return {}
    _reconcile_parts(aggregates, total_pnl, "per_symbol_contribution")
    shares = _positive_aggregate_shares(aggregates)
    return shares


def per_fold_contribution(
    fold_pnls: Mapping[str, float],
    *,
    total_pnl: float,
    population: Sequence[str] | None = None,
) -> dict[str, float]:
    """Per-fold shares over the canonical fold population (same identity check).

    ``population`` restricts/declares the exact fold ids that produced
    ``total_pnl``; folds outside it (or a parts/total drift beyond 1e-9
    scaled) raise :class:`ContributionMismatch`.
    """
    allowed = {str(f) for f in population} if population is not None else None
    aggregates: dict[str, float] = {}
    for fold_id, pnl in fold_pnls.items():
        key = str(fold_id)
        if allowed is not None and key not in allowed:
            raise ContributionMismatch(
                f"fold {key!r} outside declared canonical population"
            )
        if pnl is None:
            raise ContributionMismatch(f"fold {key!r} pnl is null")
        aggregates[key] = aggregates.get(key, 0.0) + float(pnl)
    if population is not None:
        for key in allowed or set():
            aggregates.setdefault(key, 0.0)
    if not aggregates:
        return {}
    _reconcile_parts(aggregates, total_pnl, "per_fold_contribution")
    return _positive_aggregate_shares(aggregates)


def chain_fold_segments(
    fold_segments: Sequence[Sequence[tuple[Any, float]]],
) -> list[tuple[int, float]]:
    """Chain reset-capital fold equity segments into ONE continuous curve.

    Segment k+1 is rescaled by ``(previous_chain_end / segment_start)``, i.e.
    capital compounds across folds exactly as continuous-capital walk-forward
    requires (PLAN 31.2 item 5); raw 100k-reset curves are never concatenated.
    Timestamps are re-based to sequential integer indices to keep the output
    order deterministic regardless of each fold's internal clock.
    """
    chained: list[tuple[int, float]] = []
    carry: float | None = None
    for segment in fold_segments:
        if not segment:
            continue
        ordered = sorted(segment, key=lambda row: _ts_to_ns(row[0]))
        start_equity = float(ordered[0][1])
        if start_equity <= 0:
            raise ValueError("fold segment starts at non-positive equity")
        factor = 1.0 if carry is None else carry / start_equity
        for ts, equity in ordered:
            value = float(equity) * factor
            chained.append((len(chained), value))
        carry = chained[-1][1]
    return chained


def chained_returns_mdd(
    fold_start_equities: Sequence[float],
    fold_return_series: Sequence[Sequence[float]],
) -> float:
    """TRUE walk-forward max drawdown from chained fold return series.

    Compounds every fold's return sequence onto one continuous equity path
    starting at ``fold_start_equities[0]``; fold boundaries do NOT reset the
    path (recorded reset baselines are ignored on purpose -- that is the
    defect this estimator exists to catch, F03/V5-C07/C08).  Equal-length
    validation is strict; empty input yields 0.0.

    Estimator id: :data:`CHAINED_MDD_ESTIMATOR`.
    """
    if len(fold_start_equities) != len(fold_return_series):
        raise ValueError(
            "fold_start_equities and fold_return_series length mismatch"
        )
    series_list = [list(map(float, s)) for s in fold_return_series]
    if not series_list:
        return 0.0
    equity = float(fold_start_equities[0])
    if equity <= 0:
        raise ValueError("initial walk-forward equity must be positive")
    peak = equity
    mdd = 0.0
    for series in series_list:
        for ret in series:
            if ret <= -1.0:
                return 1.0  # total wipe-out of the chained account
            equity *= 1.0 + ret
            if equity > peak:
                peak = equity
            elif peak > 0:
                mdd = max(mdd, (peak - equity) / peak)
    return mdd
