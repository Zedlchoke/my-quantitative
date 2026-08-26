"""V9 TS-TREND signal family: pure per-symbol time-series trend (A3).

At each Monday ``00:00 UTC`` cutoff stamp every traded symbol is scored by
its trailing return over ``L = 14`` days computed from DAILY CLOSES
STRICTLY BEFORE the cutoff (a close stamped exactly at the cutoff instant
is invisible -- the strict ``<`` filter makes no-lookahead structural,
not merely filtered):

    trailing = last_close(ts < cutoff)
               / close(at or before cutoff - L days) - 1

Direction rule with the frozen dead zone ``0.0``:

    trailing > +dead_zone  => LONG
    trailing < -dead_zone  => SHORT
    otherwise              => FLAT

Portfolio split: equal weight across ACTIVE SIDES to
``target_gross = 0.80``. Both sides active => each side carries
``0.40`` gross split equally over its members (2+2 symbols =>
``+-0.20`` per slot). A single active side receives the FULL ``0.80``
split equally over its members. No active symbol => a flat OK book.

Symbols without a usable trailing return (insufficient history, missing
series, non-positive prices) are INACTIVE for the stamp -- unlike the
weekly all-six eligibility this family degrades gracefully to fewer
active names; an EMPTY traded universe fails closed with SKIP_INCOMPLETE.
Weights round to 12 decimals and ties never arise (per-symbol scores).

Negative control (documented id ``XSECT-TSTREND-CTRL``): ``reverse=True``
INVERTS the trend sign end-to-end -- long the trend losers / short the
trend winners -- swapping both sides including weights.
"""

from __future__ import annotations

import bisect
from typing import Mapping, Sequence

DAY_NS = 86_400_000_000_000
LOOKBACK_DAYS = 14  # frozen primary candidate (V9 plan)
DEAD_ZONE = 0.0
TARGET_GROSS = 0.80

REASON_EMPTY_UNIVERSE = "v9_ts_trend_empty_universe"


def trailing_return(
    series: Sequence[tuple[int, float]] | None,
    *,
    cutoff_ns: int,
    lookback_days: int = LOOKBACK_DAYS,
) -> float | None:
    """Trailing ``lookback_days`` return from closes STRICTLY before cutoff.

    The last leg uses the latest close with ``ts < cutoff``; the reference
    leg uses the latest close with ``ts <= cutoff - lookback_days``. Both
    legs are completed bars only. Returns ``None`` when either leg is
    missing or non-positive (unusable history).
    """
    cutoff = int(cutoff_ns)
    closes = sorted(
        (int(ts), float(px))
        for ts, px in (series or [])
        if int(ts) < cutoff
    )
    if not closes:
        return None
    last_px = closes[-1][1]
    ref_edge_ns = cutoff - int(lookback_days) * DAY_NS
    times = [ts for ts, _ in closes]
    index = bisect.bisect_right(times, ref_edge_ns) - 1
    if index < 0:
        return None
    ref_px = closes[index][1]
    if last_px <= 0.0 or ref_px <= 0.0:
        return None
    return last_px / ref_px - 1.0


def trend_scores(
    *,
    daily_closes: Mapping[str, list[tuple[int, float]]],
    signal_cutoff_ns: int,
    traded_symbols: Sequence[str],
    lookback_days: int = LOOKBACK_DAYS,
) -> dict[str, float | None]:
    """Per-symbol trailing returns at the cutoff (``None`` = unusable)."""
    cutoff_ns = int(signal_cutoff_ns)
    symbols = sorted(dict.fromkeys(str(s) for s in traded_symbols))
    return {
        sym: trailing_return(
            (daily_closes or {}).get(sym),
            cutoff_ns=cutoff_ns,
            lookback_days=int(lookback_days),
        )
        for sym in symbols
    }


def compute_targets(
    *,
    daily_closes: Mapping[str, list[tuple[int, float]]],
    signal_cutoff_ns: int,
    traded_symbols: Sequence[str],
    lookback_days: int = LOOKBACK_DAYS,
    dead_zone: float = DEAD_ZONE,
    target_gross: float = TARGET_GROSS,
    reverse: bool = False,
) -> dict:
    """TS-TREND target book: {"status", "longs", "shorts"} (V9 contract).

    Longs/shorts are ``[[symbol, weight], ...]`` mirroring the
    weekly_reversal shape. Equal weight within an active side; side gross
    splits ``target_gross`` evenly across active sides. Unusable symbols
    stay inactive; an empty universe fails closed.
    """
    symbols = sorted(dict.fromkeys(str(s) for s in traded_symbols))
    if not symbols:
        return {"status": "SKIP_INCOMPLETE",
                "reason_code": REASON_EMPTY_UNIVERSE}

    scores = trend_scores(
        daily_closes=daily_closes,
        signal_cutoff_ns=int(signal_cutoff_ns),
        traded_symbols=symbols,
        lookback_days=int(lookback_days),
    )
    dz = float(dead_zone)
    longs = sorted(s for s, v in scores.items() if v is not None and v > dz)
    shorts = sorted(s for s, v in scores.items()
                    if v is not None and v < -dz)
    if reverse:
        longs, shorts = shorts, longs

    n_sides = (1 if longs else 0) + (1 if shorts else 0)
    per_side = float(target_gross) / n_sides if n_sides else 0.0
    longs_out = [[s, round(per_side / len(longs), 12)] for s in longs]
    shorts_out = [[s, round(-per_side / len(shorts), 12)] for s in shorts]
    return {"status": "OK", "longs": longs_out, "shorts": shorts_out}
