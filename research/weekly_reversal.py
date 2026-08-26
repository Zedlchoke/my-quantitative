"""V8 weekly reversal signal (PLAN section 5, frozen weekly behavior).

Cross-sectional WEEKLY reversal on daily closes. The signal clock is
Monday ``00:00 UTC``; only COMPLETED closes with ``timestamp <= cutoff``
enter the formation return

    formation = last_close(<= cutoff)
                / close(at or before cutoff - formation_lookback_days) - 1

Default direction is REVERSAL: long the bottom-2 losers, short the top-2
winners. ``control_momentum=True`` flips SELECTION (long top-2 winners /
short bottom-2 losers) -- the WMOM negative control evaluated at the 7D
lookback. The separate ``reverse`` flag swaps the FINAL sides end-to-end
(stress/diag inversion); plain reversal and control+reverse therefore
coincide exactly.

Eligibility is all-six fail-closed (PLAN section 5.1): every declared
traded symbol needs a usable formation return, otherwise the ENTIRE
rebalance is ``SKIP_INCOMPLETE`` with reason ``weekly_panel_incomplete``.
Weights are +-target_gross/4 rescaled so sum(|w|) == target_gross. Ties
break deterministically by symbol ascending at a 1e-12 rounding tolerance.
"""

from __future__ import annotations

import bisect
from datetime import datetime, timedelta, timezone
from typing import Sequence

DAY_MS = 86_400_000
DAY_NS = 86_400_000_000_000
MIN_PANEL_SYMBOLS = 6  # PLAN section 5.1: all-six eligibility
EMBARGO_DAYS = 7  # fold purge/embargo (PLAN section 5.1)

REASON_INCOMPLETE = "weekly_panel_incomplete"


def monday_cutoffs(
    fold_start_dt: datetime, fold_end_dt: datetime
) -> list[datetime]:
    """UTC Mondays 00:00 in the half-open signal window ``[start, end)``.

    Non-UTC inputs are normalized to UTC first. The end edge is EXCLUSIVE
    (mirrors ``portfolio_runner.daily_rebalance_stamps``) so no stamp ever
    lands exactly on a fold boundary where no execution bar would follow.
    """
    start = fold_start_dt.astimezone(timezone.utc)
    end = fold_end_dt.astimezone(timezone.utc)
    cursor = start.replace(hour=0, minute=0, second=0, microsecond=0)
    if cursor < start:
        cursor += timedelta(days=1)
    while cursor.weekday() != 0:  # Monday
        cursor += timedelta(days=1)
    stamps: list[datetime] = []
    while cursor < end:
        stamps.append(cursor)
        cursor += timedelta(days=7)
    return stamps


# Runner-facing alias: portfolio_runner replaces daily_rebalance_stamps
# with this helper for the weekly_reversal family.
monday_weekly_stamps = monday_cutoffs


def weekly_rebalance_stamps(
    fold_start_dt: datetime,
    fold_end_dt: datetime,
    *,
    embargo_days: int = EMBARGO_DAYS,
) -> list[datetime]:
    """Monday stamps with the fold PURGE/EMBARGO filter applied.

    Rebalances falling inside the first ``embargo_days`` days after the
    fold start are excluded, so a fresh fold can never trade on formation
    windows overlapping the boundary (PLAN section 5.1: purge/embargo
    7 days, warmup >= 14 days). Stamps remain sorted and duplicate-free.
    """
    floor = (
        fold_start_dt.astimezone(timezone.utc) + timedelta(days=embargo_days)
    )
    return [
        stamp
        for stamp in monday_weekly_stamps(fold_start_dt, fold_end_dt)
        if stamp >= floor
    ]


def formation_return(
    series: Sequence[tuple[int, float]] | None,
    *,
    cutoff_ns: int,
    lookback_days: int,
) -> float | None:
    """Completed-close formation return at ``cutoff_ns`` (PIT-safe).

    ``last_close`` is the latest close with ``ts <= cutoff``; the reference
    close is the latest close with ``ts <= cutoff - lookback_days``. Both
    legs use COMPLETED bars only -- anything forming after the cutoff or
    strictly inside the formation window's right edge is invisible. Returns
    ``None`` when either leg is missing or non-positive (unusable).
    """
    closes = sorted(
        (int(ts), float(px))
        for ts, px in (series or [])
        if int(ts) <= int(cutoff_ns)
    )
    if not closes:
        return None
    last_px = closes[-1][1]
    ref_edge_ns = int(cutoff_ns) - int(lookback_days) * DAY_NS
    times = [ts for ts, _ in closes]
    index = bisect.bisect_right(times, ref_edge_ns) - 1
    if index < 0:
        return None
    ref_px = closes[index][1]
    if last_px <= 0.0 or ref_px <= 0.0:
        return None
    return last_px / ref_px - 1.0


def _formation_ranks(formation: dict[str, float]) -> dict[str, int]:
    """Deterministic ascending rank (1..n), ties by symbol asc at 1e-12."""
    ranked = sorted(formation, key=lambda s: (round(formation[s], 12), s))
    return {symbol: position + 1 for position, symbol in enumerate(ranked)}


def compute_target_weights_weekly_reversal(
    *,
    signal_cutoff_ns: int,
    formation_lookback_days: int,
    reverse: bool = False,
    daily_closes: dict[str, list[tuple[int, float]]],
    traded_symbols: Sequence[str],
    target_gross: float = 0.80,
    control_momentum: bool = False,
) -> dict:
    """Weekly cross-sectional reversal target book (frozen V8 contract).

    Returns ``{"status": "OK", "longs": [[sym, w], ...],
    "shorts": [[sym, w], ...]}`` mirroring the funding_price_divergence
    shape. Any unusable formation input for ANY declared traded symbol
    fails closed with ``{"status": "SKIP_INCOMPLETE",
    "reason_code": "weekly_panel_incomplete"}``.
    """
    cutoff_ns = int(signal_cutoff_ns)
    symbols = sorted(dict.fromkeys(str(s) for s in traded_symbols))

    def _incomplete() -> dict:
        return {"status": "SKIP_INCOMPLETE", "reason_code": REASON_INCOMPLETE}

    if len(symbols) < MIN_PANEL_SYMBOLS:
        return _incomplete()

    formation: dict[str, float] = {}
    for sym in symbols:
        ret = formation_return(
            (daily_closes or {}).get(sym),
            cutoff_ns=cutoff_ns,
            lookback_days=int(formation_lookback_days),
        )
        if ret is None:
            return _incomplete()
        formation[sym] = ret

    ranked = sorted(symbols, key=lambda s: (round(formation[s], 12), s))
    bottom2, top2 = ranked[:2], ranked[-2:]
    # Reversal default: long bottom-2 losers / short top-2 winners.
    # WMOM control flips selection; the explicit reverse flag then swaps
    # the FINAL sides end-to-end (weights included).
    longs, shorts = (top2, bottom2) if control_momentum else (bottom2, top2)
    if reverse:
        longs, shorts = shorts, longs

    per_leg = target_gross / 4.0
    weights = {s: per_leg for s in longs}
    for s in shorts:
        weights[s] = -per_leg
    gross = sum(abs(w) for w in weights.values())
    scale = (target_gross / gross) if gross > 0 else 0.0

    longs_out = [[s, round(weights[s] * scale, 12)] for s in longs]
    shorts_out = [[s, round(weights[s] * scale, 12)] for s in shorts]
    return {"status": "OK", "longs": longs_out, "shorts": shorts_out}
