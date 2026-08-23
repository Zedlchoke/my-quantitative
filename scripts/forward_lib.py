"""Testable helpers for the weekly forward-test fetch step (NOTES section 12).

Extracted from the inline heredoc in ``scripts/weekly_forward_test.sh`` so the
W1 tail-overlap guardrails are unit-testable (``tests/test_forward_pipeline.py``):

- Fetch windows must START at last-bar close + :data:`FETCH_BUFFER_MINUTES`.
  Binance keeps adjusting its kline interval ~9 minutes past the bar close;
  requesting an overlapping range makes the download engine silently skip
  those bars (the W1 bug where ETH stalled at 2026-08-21).
- Zero fresh bars while the exchange is more than :data:`STALE_MAX_MINUTES`
  ahead of the catalog must FAIL LOUD, never pass silently.
"""

from __future__ import annotations

import dataclasses
import sys
from typing import Callable

import pandas as pd

from config.settings import ResearchSettings
from config.settings import load_research_config
from data.catalog import Catalog
from data.download import download_historical_data

#: Binance write-intervals extend ~9 min past the last bar close; stay clear.
FETCH_BUFFER_MINUTES = 16
#: A catalog older than this with zero new bars means the market moved on.
STALE_MAX_MINUTES = 60


class StaleForwardDataError(RuntimeError):
    """Raised when 0 new bars were fetched but market data is >1h newer."""


def to_utc(ts) -> pd.Timestamp:
    """Normalize naive/aware timestamps to tz-aware UTC."""
    stamp = pd.Timestamp(ts)
    if stamp.tzinfo is None:
        return stamp.tz_localize("UTC")
    return stamp.tz_convert("UTC")


def compute_fetch_start(
    last_bar_close,
    buffer_minutes: int = FETCH_BUFFER_MINUTES,
) -> pd.Timestamp:
    """Earliest safe request start: last bar close + buffer.

    Anything earlier overlaps Binance's write interval and the overlapping
    range is silently skipped by the download engine (W1 trap).
    """
    return to_utc(last_bar_close) + pd.Timedelta(minutes=buffer_minutes)


def is_safe_fetch_start(
    last_bar_close,
    start,
    buffer_minutes: int = FETCH_BUFFER_MINUTES,
) -> bool:
    """True iff ``start`` clears the write-interval of the last catalog bar."""
    return to_utc(start) >= compute_fetch_start(last_bar_close, buffer_minutes)


def evaluate_staleness(
    symbol: str,
    last_bar_close,
    new_bars: int,
    *,
    now=None,
    max_stale_minutes: int = STALE_MAX_MINUTES,
) -> None:
    """Fail loud when nothing was appended yet the market has newer data."""
    last = to_utc(last_bar_close)
    current = to_utc(now) if now is not None else pd.Timestamp.now("UTC")
    age_min = (current - last) / pd.Timedelta(minutes=1)
    if new_bars <= 0 and age_min > max_stale_minutes:
        raise StaleForwardDataError(
            f"{symbol}: FAIL - 0 new bars fetched but last catalog bar is "
            f"{age_min:.0f}min old (> {max_stale_minutes}min; last bar "
            f"{last:%Y-%m-%d %H:%M} UTC). Market has newer data; refusing to "
            "pass silently. Check network/Binance response before trusting "
            "this forward-test window."
        )


def fetch_disjoint_tail(
    settings: ResearchSettings,
    *,
    downloader: Callable = download_historical_data,
    catalog_factory: Callable[[str], Catalog] = Catalog,
    now: pd.Timestamp | None = None,
    log: Callable[[str], None] = print,
) -> dict[str, dict]:
    """Fetch only the disjoint tail per symbol; return a per-symbol report.

    ``downloader``/``catalog_factory``/``now`` are injectable so tests can
    reproduce the overlap and silent-skip traps without network access.
    """
    current = to_utc(now) if now is not None else pd.Timestamp.now("UTC")
    report: dict[str, dict] = {}
    for symbol in settings.market.symbols:
        catalog = catalog_factory(settings.data.catalog_path)
        bars = catalog.bars(settings.market.bar_type(symbol))
        if not bars:
            log(f"{symbol}: empty catalog, run full download first")
            report[symbol] = {"status": "empty", "new_bars": 0}
            continue

        before = len(bars)
        # ts_event is int nanoseconds (bar close time).
        last = pd.Timestamp(bars[-1].ts_event, unit="ns", tz="UTC")
        start = compute_fetch_start(last)
        if start >= current:
            log(f"{symbol}: catalog already current through {last:%Y-%m-%d %H:%M} UTC")
            report[symbol] = {
                "status": "current",
                "new_bars": 0,
                "last_bar": last.isoformat(),
            }
            continue

        start_str = start.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        market = dataclasses.replace(settings.market, symbols=[symbol])
        data = dataclasses.replace(settings.data, start=start_str, end=None)
        log(f"{symbol}: fetching from {start_str}")

        new_bars = 0
        try:
            summary = downloader(market, data)
            # bars_written counts the whole catalog for this bar type.
            new_bars = max(0, int(summary["per_symbol"][symbol]["bars_written"]) - before)
        except Exception as exc:  # noqa: BLE001
            if "non-disjoint" in str(exc) or "start was > now" in str(exc):
                log(f"{symbol}: already up to date ({exc.__class__.__name__})")
            else:
                raise
        log(f"{symbol}: {new_bars} new bars (catalog {before} -> {before + new_bars})")

        evaluate_staleness(symbol, last, new_bars, now=current)
        report[symbol] = {
            "status": "fetched",
            "new_bars": new_bars,
            "last_bar": last.isoformat(),
            "fetch_start": start_str,
        }
    return report


def main(argv: list[str] | None = None) -> int:
    """CLI entry used by scripts/weekly_forward_test.sh; exit 1 on stale data."""
    import argparse

    parser = argparse.ArgumentParser(description="Fetch disjoint forward-test tail.")
    parser.add_argument("config", help="Path to research YAML config")
    args = parser.parse_args(argv)

    settings = load_research_config(args.config)
    try:
        report = fetch_disjoint_tail(settings)
    except StaleForwardDataError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(f"Fetch summary: {report}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
