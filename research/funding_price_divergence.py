"""H-XSECT-FUNDING-PRICE-DIVERGENCE-v1 signal (PLAN section 16.2, frozen V7 contract).

Cross-sectional funding-price divergence: score = percentile_rank(price_return)
- percentile_rank(funding_mean). Funding leg is the TRAILING MEAN of SETTLED
rates (strict PIT: fundingTime <= cutoff, window = funding_lookback_days,
pinned 3). Price leg is the close-to-close return over price_lookback_days
using COMPLETED daily closes <= cutoff only. Long top-2 score / short bottom-2,
weights +-target_gross/4 rescaled so sum(|w|) == target_gross. Any missing
input for ANY symbol skips the whole cross-section (fail-closed).
`reverse` swaps sides end-to-end (sign flip included).
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

DAY_MS = 86_400_000


def _percentile_ranks(values: dict[str, float]) -> dict[str, float]:
    """Percentile rank in [0, 1] with average-rank ties across symbols."""
    ordered = sorted(values, key=lambda s: (round(values[s], 12), s))
    n = len(ordered)
    ranks: dict[str, float] = {}
    i = 0
    while i < n:
        j = i
        while j + 1 < n and round(values[ordered[j + 1]], 12) == round(
            values[ordered[i]], 12
        ):
            j += 1
        avg_rank = ((i + 1) + (j + 1)) / 2.0
        for k in range(i, j + 1):
            ranks[ordered[k]] = avg_rank / n
        i = j + 1
    return ranks


def compute_target_weights_funding_price_divergence(
    *,
    signal_cutoff_ns: int,
    price_lookback_days: int,
    reverse: bool = False,
    funding_bundles_dir: str | Path,
    daily_closes: dict[str, list[tuple[int, float]]],
    traded_symbols: Sequence[str],
    target_gross: float = 0.80,
    funding_lookback_days: int = 3,
) -> dict:
    cutoff_ns = int(signal_cutoff_ns)
    cutoff_ms = cutoff_ns // 1_000_000
    fund_window_start_ms = cutoff_ms - int(funding_lookback_days) * DAY_MS

    from research.funding_pit import load_funding_bundle

    symbols = sorted(dict.fromkeys(str(s) for s in traded_symbols))
    if len(symbols) < 4:
        return {"status": "SKIP_INCOMPLETE",
                "reason_code": "divergence_panel_incomplete"}

    def _incomplete() -> dict:
        return {"status": "SKIP_INCOMPLETE",
                "reason_code": "divergence_panel_incomplete"}

    funding_means: dict[str, float] = {}
    price_returns: dict[str, float] = {}

    for sym in symbols:
        try:
            payload = load_funding_bundle(funding_bundles_dir, sym)
        except Exception:
            return _incomplete()
        settled = [
            float(str(row["fundingRate"]))
            for row in payload.get("rows", [])
            if fund_window_start_ms <= int(row["fundingTime"]) <= cutoff_ms
        ]
        if not settled:
            return _incomplete()
        funding_means[sym] = sum(settled) / len(settled)

        closes = sorted(
            (int(ts), float(px))
            for ts, px in (daily_closes or {}).get(sym, [])
            if int(ts) <= cutoff_ns
        )
        k = int(price_lookback_days)
        if len(closes) < k + 1:
            return _incomplete()
        prev_close = closes[-1 - k][1]
        last_close = closes[-1][1]
        if prev_close <= 0.0:
            return _incomplete()
        price_returns[sym] = last_close / prev_close - 1.0

    price_pct = _percentile_ranks(price_returns)
    funding_pct = _percentile_ranks(funding_means)
    scores = {s: price_pct[s] - funding_pct[s] for s in symbols}

    ranked = sorted(scores, key=lambda s: (round(scores[s], 12), s))
    shorts = ranked[:2]
    longs = ranked[-2:]
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


def build_divergence_traded(
    daily_closes: dict[str, list[tuple[int, float]]],
    benchmark: str = "BTCUSDT",
) -> list[str]:
    """Sorted non-benchmark tradable list (future dispatcher wiring helper)."""
    return sorted(str(s) for s in (daily_closes or {}) if str(s) != str(benchmark))
