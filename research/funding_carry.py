"""H-XSECT-FUNDING-CARRY-v1 signal (PLAN section 8, frozen contract).

Cross-sectional funding carry: rank TRAILING MEAN of SETTLED funding rates
(strict PIT: settlement_ms <= signal cutoff), long bottom-2 / short top-2,
weights rescaled so sum(|w|) == target_gross. Missing data skips the whole
cross-section (fail-closed). `reverse` swaps sides end-to-end.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

DAY_MS = 86_400_000


def compute_target_weights_funding_carry(
    *,
    signal_cutoff_ns: int,
    lookback_days: int,
    reverse: bool = False,
    funding_bundles_dir: str | Path,
    traded_symbols: Sequence[str],
    target_gross: float = 0.80,
) -> dict:
    cutoff_ms = int(signal_cutoff_ns) // 1_000_000
    window_start_ms = cutoff_ms - int(lookback_days) * DAY_MS

    from research.funding_pit import load_funding_bundle

    means: dict[str, float] = {}
    for sym in sorted(traded_symbols):
        try:
            payload = load_funding_bundle(funding_bundles_dir, sym)
        except Exception:
            return {"status": "SKIP_INCOMPLETE",
                    "reason_code": "funding_panel_incomplete"}
        settled = [
            float(str(row["fundingRate"]))
            for row in payload.get("rows", [])
            if window_start_ms <= int(row["fundingTime"]) <= cutoff_ms
        ]
        if not settled:
            return {"status": "SKIP_INCOMPLETE",
                    "reason_code": "funding_panel_incomplete"}
        means[sym] = sum(settled) / len(settled)

    ordered = sorted(means, key=lambda s: (round(means[s], 12), s))
    if len(ordered) < 4:
        return {"status": "SKIP_INCOMPLETE",
                "reason_code": "funding_panel_incomplete"}
    longs = ordered[:2]
    shorts = ordered[-2:]
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
