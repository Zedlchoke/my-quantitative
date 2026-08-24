"""Pure point-in-time cross-sectional rank signal (H-XSECT-MOM-v1, owner A4).

No I/O, no randomness, deterministic. The engine (A2) calls
``compute_target_weights`` at each daily signal cutoff and executes the returned
targets at the NEXT 15m event (NEXT_BAR_EVENT_BASELINE).
"""

from __future__ import annotations

import math

DAY_NS = 86_400_000_000_000
BENCHMARK_SYMBOL = "BTCUSDT"


def _last_index_at_or_before(series, cutoff_ns: int):
    """Index of the last point with ts <= cutoff, else None."""
    lo, hi, ans = 0, len(series) - 1, None
    while lo <= hi:
        mid = (lo + hi) // 2
        if series[mid][0] <= cutoff_ns:
            ans = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return ans


def compute_target_weights(
    daily_closes: dict[str, list[tuple[int, float]]],
    signal_cutoff_ns: int,
    lookback_days: int,
    *,
    reverse: bool = False,
    day_ns: int = DAY_NS,
    long_count: int = 2,
    short_count: int = 2,
    weight: float = 0.25,
    min_eligible: int = 7,
) -> dict:
    """Rank symbols on trailing cumulative log return; return equal-weight legs.

    Semantics:
    - Last usable close for a symbol is the latest point with ``ts <= cutoff``.
    - Requires exactly ``lookback_days + 1`` consecutive daily points ending at
      that last usable close (any gap or short history => symbol incomplete =>
      the ENTIRE cross-section is SKIP_INCOMPLETE per pre-registered policy).
    - score = ln(P_last / P_first_of_window); rank DESC (reverse => ASC),
      ties broken by symbol ascending.
    - longs = top ``long_count`` at +weight each; shorts = bottom
      ``short_count`` at −weight each; sum(weights) ≈ 0.
    - BTCUSDT is a benchmark and never traded.
    """
    traded = sorted(s for s in daily_closes if s != BENCHMARK_SYMBOL)
    scores: dict[str, float] = {}
    for sym in traded:
        series = daily_closes.get(sym) or []
        idx = _last_index_at_or_before(series, signal_cutoff_ns)
        if idx is None or idx < lookback_days:
            return _skip(signal_cutoff_ns, lookback_days)
        window = series[idx - lookback_days : idx + 1]
        # consecutive daily points ending at the last usable close
        ts_last = window[-1][0]
        for offset, point in enumerate(reversed(window)):
            expected = ts_last - offset * day_ns
            if int(point[0]) != int(expected):
                return _skip(signal_cutoff_ns, lookback_days)
        first_price = float(window[0][1])
        last_price = float(window[-1][1])
        if first_price <= 0 or last_price <= 0:
            return _skip(signal_cutoff_ns, lookback_days)
        scores[sym] = math.log(last_price / first_price)

    ordered = sorted(scores.items(), key=lambda kv: (-kv[1], kv[0]))
    if reverse:
        ordered = list(reversed(ordered))
    longs = [[sym, weight] for sym, _ in ordered[:long_count]] if long_count else []
    shorts = (
        [[sym, -weight] for sym, _ in ordered[len(ordered) - short_count :]]
        if short_count
        else []
    )
    total = sum(w for _, w in longs) + sum(w for _, w in shorts)
    if abs(total) > 1e-9:
        raise ValueError(f"target weights do not sum to zero: {total}")
    for _, w in longs + shorts:
        if abs(abs(w) - abs(weight)) > 1e-12:
            raise ValueError("weight cap violated")
    return {
        "status": "OK",
        "signal_cutoff_ns": int(signal_cutoff_ns),
        "lookback_days": int(lookback_days),
        "reverse": bool(reverse),
        "scores": scores,
        "longs": longs,
        "shorts": shorts,
    }


def _skip(cutoff_ns: int, lookback_days: int) -> dict:
    return {
        "status": "SKIP_INCOMPLETE",
        "reason_code": "incomplete_cross_section_skip",
        "signal_cutoff_ns": int(cutoff_ns),
        "lookback_days": int(lookback_days),
        "scores": {},
        "longs": [],
        "shorts": [],
    }
