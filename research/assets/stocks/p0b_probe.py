"""V6-P0b (A3): sample-probe runner — windowed OHLCV evidence + L7 cross-check.

The light phase retrieves SMALL DATE-WINDOWED daily CSV samples, never the
full history: (1) the bulk download is explicitly NOT authorized in this
phase (A1 schedules it as a standalone heavy window); (2) the browser-
equivalent rendering channel (the only channel that passes stooq's
anti-bot gate) is summary-lossy for large documents, so each archived
document must stay small enough to be captured verbatim.

Each probe window is chosen against an SEC-evidenced expectation:

* split windows (TJX 2:1 2018-10; CMG 50:1 2024-06-26) — exact continuity
  checks against the pinned PIT store facts;
* dividend ex-windows (AIG 2022 quarters) — tolerance-based residuals;
* window edges (2025-07 tails; one 1990 depth window) — history-depth and
  served-through-today evidence for the availability table;
* RTX 2020-02..04 — the UTX->RTX identity/ticker-change window.

Fail-loud everywhere: a window that comes back empty, HTML, or challenge
is RECORDED AS A FAILURE in the report — never silently skipped.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Sequence

from research.assets.stocks.calendar import USEquityRegularCalendar
from research.assets.stocks.p0b_l7_crosscheck import (
    DividendFact,
    SplitFact,
    crosscheck_symbol,
)
from research.assets.stocks.p0b_parse import (
    DailyBar,
    StooqParseError,
    daily_log_returns,
    parse_stooq_daily_csv,
)

S0_START = date(2018, 4, 4)
S0_END = date(2025, 7, 24)


def window_stats(
    symbol: str,
    window_id: str,
    d1: date,
    d2: date,
    bars: Sequence[DailyBar],
    calendar: USEquityRegularCalendar,
) -> dict:
    """Coverage metrics for one windowed sample against the shared calendar."""
    actual = {b.date for b in bars}
    expected_sessions: List[date] = []
    day = d1
    while day <= d2:
        if calendar.is_session_day(day):
            expected_sessions.append(day)
        day = date.fromordinal(day.toordinal() + 1)
    missing = [d.isoformat() for d in expected_sessions if d not in actual]
    rets = daily_log_returns(bars)
    return {
        "symbol": symbol,
        "window_id": window_id,
        "requested_window": [d1.isoformat(), d2.isoformat()],
        "rows": len(bars),
        "first_row": bars[0].date.isoformat() if bars else None,
        "last_row": bars[-1].date.isoformat() if bars else None,
        "expected_sessions": len(expected_sessions),
        "missing_session_days": missing,
        "window_returns_computed": len(rets),
        "in_s0_window": (d2 >= S0_START and d1 <= S0_END),
        "date_params_honored": (
            bool(bars)
            and bars[0].date >= d1
            and bars[-1].date <= d2
        ),
    }


def run_probes(
    windows: Sequence[dict],
    raw_dir: Path,
    split_facts: Dict[str, Sequence[SplitFact]],
    dividend_facts: Dict[str, Sequence[DividendFact]],
) -> dict:
    """Parse all staged probe windows and assemble the probe report.

    ``windows`` items: {symbol, window_id, d1, d2, file, retrieval}. Parse
    or coverage failures land in ``failures`` with full detail; nothing is
    silently skipped.
    """
    calendar = USEquityRegularCalendar()
    raw_dir = Path(raw_dir)
    per_symbol_windows: Dict[str, List[dict]] = {}
    failures: List[dict] = []

    for w in windows:
        path = raw_dir / w["file"]
        entry = {
            "symbol": w["symbol"],
            "window_id": w["window_id"],
            "requested_window": [w["d1"].isoformat(), w["d2"].isoformat()],
            "file": w["file"],
        }
        if not path.exists():
            failures.append({**entry, "status": "FAIL", "error": "archived document missing"})
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if not text.strip():
            failures.append({**entry, "status": "FAIL", "error": "archived document empty"})
            continue
        try:
            bars = parse_stooq_daily_csv(text)
        except StooqParseError as exc:
            failures.append({**entry, "status": "FAIL", "error": f"parse error: {exc}"})
            continue
        stats = window_stats(
            w["symbol"], w["window_id"], w["d1"], w["d2"], bars, calendar
        )
        stats["status"] = "OK"
        stats["file"] = w["file"]
        stats["retrieval"] = w.get("retrieval", {})
        per_symbol_windows.setdefault(w["symbol"], []).append(stats)

    l7_results = {}
    for symbol, window_list in sorted(per_symbol_windows.items()):
        merged: List[DailyBar] = []
        for w in window_list:
            path = raw_dir / w["file"]
            try:
                merged.extend(parse_stooq_daily_csv(path.read_text(encoding="utf-8")))
            except StooqParseError:
                continue
        merged.sort(key=lambda b: b.date)
        dedup: Dict[date, DailyBar] = {}
        for b in merged:
            dedup.setdefault(b.date, b)
        series = [dedup[d] for d in sorted(dedup)]
        l7_results[symbol] = crosscheck_symbol(
            symbol,
            series,
            split_facts.get(symbol, []),
            dividend_facts.get(symbol, []),
        )

    return {
        "schema": "stocks_free_v6_run/p0b_sample_probe_report@1",
        "windows": [s for ws in per_symbol_windows.values() for s in ws],
        "failures": failures,
        "l7_crosscheck": l7_results,
        "note": (
            "light-phase evidence: windowed samples only; full-history bulk "
            "download is deferred to the A1-scheduled heavy window and is "
            "NOT executed here"
        ),
    }
