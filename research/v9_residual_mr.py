"""V9 RESIDUAL-MR signal family: market-neutral residual mean reversion (A3).

Daily residuals against the BTC benchmark are computed PIT-safe from
completed closes STRICTLY BEFORE the Monday ``00:00 UTC`` cutoff:

    r_i,t   = close_i,t / close_i,t-1 - 1          (daily returns)
    beta_i  = OLS slope of r_i on r_btc over the TRAILING 30d window
              ENDING AT THE CUTOFF (aligned by return timestamp);
              fallback ``beta = 1.0`` when fewer than 20 aligned
              observations or zero benchmark variance
    e_i,t   = r_i,t - beta_i * r_btc,t

Residual momentum z-score over the same trailing window:

    z_i = mean(last K = 5 daily residuals)
          / std(all residuals in the 30d window)      (population std)

``std == 0`` (no dispersion) leaves the symbol INELIGIBLE rather than
inventing a score. Selection is SIGN-BASED (this is a fade family):
LONG up to ``2`` eligible symbols ranked by MOST NEGATIVE z (losers fade
up) and SHORT up to ``2`` ranked by MOST POSITIVE z; ties break by
symbol ascending at a 1e-12 rounding tolerance. Each filled position
slot carries a frozen ``+-0.20`` gross so the maximum book is
``4 x 0.20 = 0.80``; fewer eligible symbols scale the total gross DOWN
PROPORTIONALLY via the missing slots (per-slot weight stays ``0.20`` --
no re-concentration).

Negative control (documented id ``XSECT-RESMR-CTRL``): ``reverse=True``
INVERTS the z-sign before ranking, which swaps longs/shorts exactly.

A missing benchmark series fails closed with SKIP_INCOMPLETE.
"""

from __future__ import annotations

import math
from typing import Mapping, Sequence

DAY_NS = 86_400_000_000_000
BETA_WINDOW_DAYS = 30
BETA_MIN_OBS = 20
Z_MOMENTUM_K = 5
SLOT_GROSS = 0.20
TOP_N_PER_SIDE = 2

REASON_MISSING_BENCHMARK = "v9_residual_mr_missing_benchmark"
REASON_EMPTY_UNIVERSE = "v9_residual_mr_empty_universe"


def daily_returns(
    series: Sequence[tuple[int, float]] | None,
    *,
    cutoff_ns: int,
) -> dict[int, float]:
    """Completed-close daily returns keyed by the LATER close timestamp.

    Only closes with ``ts < cutoff_ns`` enter (strictly-before PIT rule);
    each return needs its previous close inside that same visible history.
    """
    cutoff = int(cutoff_ns)
    closes = sorted(
        (int(ts), float(px))
        for ts, px in (series or [])
        if int(ts) < cutoff
    )
    out: dict[int, float] = {}
    for (t0, p0), (t1, p1) in zip(closes, closes[1:]):
        if p0 > 0.0 and p1 > 0.0:
            out[t1] = p1 / p0 - 1.0
    return out


def _ols_slope(xs: Sequence[float], ys: Sequence[float]) -> float:
    n = len(xs)
    mean_x = math.fsum(xs) / n
    mean_y = math.fsum(ys) / n
    cov = math.fsum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var = math.fsum((x - mean_x) ** 2 for x in xs)
    if var <= 0.0:
        return float("nan")
    return cov / var


def estimate_beta(
    sym_returns: Mapping[int, float],
    btc_returns: Mapping[int, float],
    *,
    window_days: int = BETA_WINDOW_DAYS,
    min_obs: int = BETA_MIN_OBS,
) -> tuple[float, int]:
    """PIT OLS beta over the trailing ``window_days`` aligned obs.

    Returns ``(beta, n_obs)``; falls back to ``(1.0, n_obs)`` when fewer
    than ``min_obs`` aligned observations exist or the benchmark variance
    is degenerate (slope undefined).
    """
    common = sorted(set(sym_returns) & set(btc_returns))
    recent = common[-int(window_days):]
    xs = [float(btc_returns[t]) for t in recent]
    ys = [float(sym_returns[t]) for t in recent]
    if len(recent) < int(min_obs):
        return 1.0, len(recent)
    beta = _ols_slope(xs, ys)
    if not math.isfinite(beta):
        return 1.0, len(recent)
    return beta, len(recent)


def residual_z_scores(
    *,
    daily_closes: Mapping[str, list[tuple[int, float]]],
    benchmark_closes: Mapping[str, list[tuple[int, float]]]
    | Sequence[tuple[int, float]],
    signal_cutoff_ns: int,
    traded_symbols: Sequence[str],
    beta_window_days: int = BETA_WINDOW_DAYS,
    min_beta_obs: int = BETA_MIN_OBS,
    z_momentum_k: int = Z_MOMENTUM_K,
) -> dict[str, dict]:
    """Per-symbol ``{"beta", "z", "n_obs"}`` diagnostics at the cutoff.

    ``z`` is ``None`` for symbols with unusable history (< 2 usable closes)
    or zero residual dispersion; such symbols are never selectable.
    """
    cutoff_ns = int(signal_cutoff_ns)
    btc_raw = (
        benchmark_closes.get("BTCUSDT")
        if isinstance(benchmark_closes, Mapping) else benchmark_closes
    )
    btc_returns = daily_returns(btc_raw, cutoff_ns=cutoff_ns)
    out: dict[str, dict] = {}
    for sym in sorted(dict.fromkeys(str(s) for s in traded_symbols)):
        sym_returns = daily_returns(
            (daily_closes or {}).get(sym), cutoff_ns=cutoff_ns)
        common = sorted(set(sym_returns) & set(btc_returns))
        if len(common) < 2:
            out[sym] = {"beta": None, "z": None, "n_obs": len(common)}
            continue
        recent = common[-int(beta_window_days):]
        beta, n_obs = estimate_beta(
            sym_returns, btc_returns,
            window_days=int(beta_window_days),
            min_obs=int(min_beta_obs),
        )
        residuals = [
            sym_returns[t] - beta * btc_returns[t] for t in recent
        ]
        mean_res = math.fsum(residuals) / len(residuals)
        std_res = math.sqrt(
            math.fsum((r - mean_res) ** 2 for r in residuals)
            / len(residuals)
        )
        tail = residuals[-int(z_momentum_k):]
        z = None if std_res <= 0.0 else (
            math.fsum(tail) / len(tail) / std_res
        )
        out[sym] = {
            "beta": round(float(beta), 12),
            "z": None if z is None else round(float(z), 12),
            "n_obs": int(n_obs),
        }
    return out


def compute_targets(
    *,
    daily_closes: Mapping[str, list[tuple[int, float]]],
    benchmark_closes: Mapping[str, list[tuple[int, float]]]
    | Sequence[tuple[int, float]],
    signal_cutoff_ns: int,
    traded_symbols: Sequence[str],
    beta_window_days: int = BETA_WINDOW_DAYS,
    min_beta_obs: int = BETA_MIN_OBS,
    z_momentum_k: int = Z_MOMENTUM_K,
    slot_gross: float = SLOT_GROSS,
    top_n_per_side: int = TOP_N_PER_SIDE,
    reverse: bool = False,
) -> dict:
    """RESIDUAL-MR target book: {"status", "longs", "shorts"} (V9 contract).

    Long the up-to-``top_n_per_side`` most-NEGATIVE-z eligible symbols,
    short the same count of most-POSITIVE-z, ``+-slot_gross`` per slot;
    sign-based sides can never overlap and empty signs leave that side
    unfilled (proportional gross scale-down).
    """
    symbols = sorted(dict.fromkeys(str(s) for s in traded_symbols))
    if not symbols:
        return {"status": "SKIP_INCOMPLETE",
                "reason_code": REASON_EMPTY_UNIVERSE}
    btc_raw = (
        benchmark_closes.get("BTCUSDT")
        if isinstance(benchmark_closes, Mapping) else benchmark_closes
    )
    if not list(btc_raw or []):
        return {"status": "SKIP_INCOMPLETE",
                "reason_code": REASON_MISSING_BENCHMARK}

    scores = residual_z_scores(
        daily_closes=daily_closes,
        benchmark_closes=benchmark_closes,
        signal_cutoff_ns=int(signal_cutoff_ns),
        traded_symbols=symbols,
        beta_window_days=int(beta_window_days),
        min_beta_obs=int(min_beta_obs),
        z_momentum_k=int(z_momentum_k),
    )
    ranked = sorted(
        (sym for sym, row in scores.items() if row["z"] is not None),
        key=lambda s: (round(float(scores[s]["z"]), 12), s),
    )
    top_n = max(0, int(top_n_per_side))
    # Sign-based fade selection: longs come off the negative-z end,
    # shorts off the positive-z end -- a mean-reversion family never
    # longs positive residual momentum (or vice versa under reverse).
    neg_asc = [s for s in ranked if float(scores[s]["z"]) < 0.0]
    pos_desc = list(reversed(
        [s for s in ranked if float(scores[s]["z"]) > 0.0]))
    if reverse:
        longs, shorts = pos_desc[:top_n], neg_asc[:top_n]
    else:
        longs, shorts = neg_asc[:top_n], pos_desc[:top_n]

    slot = float(slot_gross)
    longs_out = [[s, round(slot, 12)] for s in sorted(longs)]
    shorts_out = [[s, round(-slot, 12)] for s in sorted(shorts)]
    return {"status": "OK", "longs": longs_out, "shorts": shorts_out}
