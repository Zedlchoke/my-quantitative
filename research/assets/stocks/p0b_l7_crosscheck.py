"""V6-P0b (A3): L7 corporate-action cross-check against SEC issuer facts.

Lesson L7 (binding): corporate-action errors are discovered in the data
phase, never at D2. This module reconciles the authorized price-series
probe against issuer distributions recorded in the pinned inherited SEC
PIT store (sha256 f53eb371...df955, read-only).

Checks implemented
------------------
1. Split continuity (EXACT): for each SEC-evidenced split fact (ratio +
   event window, e.g. TJX 2:1 window 2018-10-22..2018-11-06; CMG 50:1 at
   2024-06-26), the retrieved series must NOT show the raw price impact
   (1/ratio - 1) inside the window if it is split-adjusted. A measured
   raw-like discontinuity is a RED flag either way: it means the series is
   raw (adjustment policy undocumented) or the split is double-counted.

2. Dividend ex-window residuals (TOLERANCE-BASED): for each per-share
   dividend fact (period end, USD/share), the natural ex-date window is
   [period_end - 10, period_end + 70] days. For each window we record the
   minimum daily return and its z-score against the name's full-window
   return distribution. Verdicts:
     - CONSISTENT_WITH_ADJUSTED_SERIES: every window z > -4
     - POSSIBLE_UNADJUSTED_DIVIDEND_DROP: some window z <= -4
   The stated limitation is explicit and frozen: a single series cannot
   separate a small unadjusted dividend drop from market noise at
   single-event granularity; this check can only flag gross violations.
   Definitive dividend-adjustment evidence requires either a
   source-documented adjustment policy or a raw-vs-adjusted pair — both
   are heavy-phase questions.

Fail-closed: a name with no SEC distribution facts records
NO_DISTRIBUTION_FACTS_IN_STORE (NOT_RUN semantics), never a silent pass.
"""

from __future__ import annotations

import math
import statistics
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Dict, List, Optional, Sequence

from research.assets.stocks.p0b_parse import DailyBar, daily_log_returns, split_window_continuity

DIVIDEND_EX_WINDOW_BEFORE_DAYS = 10
DIVIDEND_EX_WINDOW_AFTER_DAYS = 70
DIVIDEND_Z_OUTLIER_THRESHOLD = -4.0


@dataclass(frozen=True)
class SplitFact:
    window_start: date
    window_end: date
    ratio: float
    source_field: str
    fact_available_time: str


@dataclass(frozen=True)
class DividendFact:
    period_end: date
    value_per_share: float
    source_field: str
    fact_available_time: str


def crosscheck_symbol(
    symbol: str,
    bars: Sequence[DailyBar],
    split_facts: Sequence[SplitFact],
    dividend_facts: Sequence[DividendFact],
) -> dict:
    result: dict = {
        "symbol": symbol,
        "n_bars": len(bars),
        "series_first_date": bars[0].date.isoformat() if bars else None,
        "series_last_date": bars[-1].date.isoformat() if bars else None,
        "split_checks": [],
        "dividend_check": None,
    }

    # --- 1. split continuity (exact) ---
    for sf in split_facts:
        check = split_window_continuity(
            bars, sf.window_start, sf.window_end, sf.ratio
        )
        check.update(
            {
                "source_field": sf.source_field,
                "sec_window": [sf.window_start.isoformat(), sf.window_end.isoformat()],
                "sec_ratio": sf.ratio,
                "fact_available_time": sf.fact_available_time,
                "interpretation": (
                    "series behaves SPLIT-ADJUSTED (no raw discontinuity)"
                    if check["verdict"] == "NO_RAW_DISCONTINUITY_ADJUSTED_LIKE"
                    else "series shows a RAW-LIKE discontinuity — adjustment convention undocumented or double-counted"
                    if check["verdict"] == "RAW_LIKE_DISCONTINUITY"
                    else "no series rows inside the SEC window — cannot check"
                ),
            }
        )
        result["split_checks"].append(check)

    # --- 2. dividend ex-window residuals (tolerance-based) ---
    if not dividend_facts:
        result["dividend_check"] = {
            "verdict": "NO_DISTRIBUTION_FACTS_IN_STORE",
            "n_facts": 0,
            "note": "NOT_RUN semantics: nothing to reconcile against",
        }
        return result

    rets = daily_log_returns(bars)
    if len(rets) < 30:
        result["dividend_check"] = {
            "verdict": "INSUFFICIENT_SERIES",
            "n_facts": len(dividend_facts),
        }
        return result
    vals = [r for _, r in rets]
    mu = statistics.fmean(vals)
    sigma = statistics.pstdev(vals)
    if sigma == 0.0:
        result["dividend_check"] = {"verdict": "DEGENERATE_SERIES", "n_facts": len(dividend_facts)}
        return result

    # unique dividend facts by (period_end, value) — the store carries the
    # same fact re-reported by multiple filing vintages; deduplicate for the
    # event study but keep the vintage count as vintage-stability evidence.
    uniq: Dict[tuple, DividendFact] = {}
    vintage_counts: Dict[tuple, int] = {}
    for f in dividend_facts:
        key = (f.period_end, round(f.value_per_share, 6))
        vintage_counts[key] = vintage_counts.get(key, 0) + 1
        uniq.setdefault(key, f)

    events: List[dict] = []
    worst_z = 0.0
    n_in_series = 0
    for key, f in sorted(uniq.items()):
        ws = f.period_end - timedelta(days=DIVIDEND_EX_WINDOW_BEFORE_DAYS)
        we = f.period_end + timedelta(days=DIVIDEND_EX_WINDOW_AFTER_DAYS)
        window = [(d, r) for d, r in rets if ws <= d <= we]
        if not window:
            events.append(
                {
                    "period_end": f.period_end.isoformat(),
                    "value_per_share": f.value_per_share,
                    "in_series": False,
                }
            )
            continue
        n_in_series += 1
        min_day, min_r = min(window, key=lambda dr: dr[1])
        z = (min_r - mu) / sigma
        worst_z = min(worst_z, z)
        events.append(
            {
                "period_end": f.period_end.isoformat(),
                "value_per_share": f.value_per_share,
                "ex_window": [ws.isoformat(), we.isoformat()],
                "min_daily_return": round(min_r, 6),
                "min_return_day": min_day.isoformat(),
                "z_vs_series": round(z, 3),
                "vintage_reports": vintage_counts[key],
                "in_series": True,
            }
        )

    outlier = [e for e in events if e.get("z_vs_series") is not None and e["z_vs_series"] <= DIVIDEND_Z_OUTLIER_THRESHOLD]
    result["dividend_check"] = {
        "n_facts_unique": len(uniq),
        "n_facts_in_series": n_in_series,
        "z_outlier_threshold": DIVIDEND_Z_OUTLIER_THRESHOLD,
        "worst_z": round(worst_z, 3),
        "verdict": (
            "POSSIBLE_UNADJUSTED_DIVIDEND_DROP"
            if outlier
            else "CONSISTENT_WITH_ADJUSTED_SERIES"
        ),
        "limitation": (
            "single-series test: cannot separate small unadjusted dividend drops "
            "from market noise at single-event granularity; definitive dividend "
            "adjustment evidence requires a source-documented policy or a "
            "raw-vs-adjusted pair (heavy-phase scope)"
        ),
        "events": events,
    }
    return result
