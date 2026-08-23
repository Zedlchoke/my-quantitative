"""Silent-skip-proof incremental bar fetching (owner: A2).

Background (W1 incident): ``scripts/weekly_forward_test.sh`` fetched the disjoint
bar tail and treated *any* failure containing ``non-disjoint`` / ``start was >
now`` as "already up to date". A stale or overlapping request therefore
silently passed and the forward test ran on older data without any error.

This module turns every skip condition into either an explicit
``CATALOG_CURRENT`` result (verified against the expected latest closed bar) or
a raised :class:`IncrementalPipelineError` carrying the contract reason code
``catalog_not_current`` (see ``contracts.protocol.REASON_CODES``).

Timestamp semantics: Binance klines are stored with ``ts_event`` equal to the
bar CLOSE stamp (e.g. ``09:44:59.999000064`` for the 09:30-09:45 bar). The
download/write pipeline lags real time by up to ~9 minutes past a bar close,
so :func:`expected_latest_closed_bar` floors ``now - buffer`` onto the bar grid;
a catalog is only considered current when its newest close stamp reached that
expectation.

Usage::

    from data.incremental import fetch_tail
    result = fetch_tail(catalog, settings.market, settings.data, "SOLUSDT")
    # -> {"status": "CATALOG_CURRENT" | "FETCHED", ...} or raises

The downloader is injected (``download_fn``) so tests can exercise every path
without network access; production defaults to
``data.download.download_historical_data``.
"""

from __future__ import annotations

import dataclasses
from typing import Callable

import pandas as pd

from contracts.protocol import require_reason
from data.download import download_historical_data

#: Write intervals extend ~9 minutes past a bar close before that bar is
#: guaranteed queryable in the catalog (empirical, weekly_forward_test.sh).
DEFAULT_WRITE_BUFFER_MINUTES = 9.0

#: Consecutive 15m close stamps are exactly 900s apart; tolerate adapter padding.
SEAM_TOLERANCE_NS = 2_000_000_000

#: Proven disjoint-tail offset from scripts/weekly_forward_test.sh: requesting
#: strictly after ``last_close + 16m`` never collides with existing catalog data.
TAIL_OFFSET_MINUTES = 16.0


class IncrementalPipelineError(RuntimeError):
    """Raised when an incremental fetch cannot prove catalog freshness."""

    def __init__(self, reason_code: str, message: str) -> None:
        super().__init__(f"[{reason_code}] {message}")
        self.reason_code = require_reason(reason_code)
        self.message = message


def _to_utc(value: pd.Timestamp) -> pd.Timestamp:
    ts = pd.Timestamp(value)
    return ts.tz_localize("UTC") if ts.tzinfo is None else ts.tz_convert("UTC")


def expected_latest_closed_bar(
    interval: str = "15m",
    now: pd.Timestamp | str | None = None,
    write_buffer_minutes: float = DEFAULT_WRITE_BUFFER_MINUTES,
) -> pd.Timestamp:
    """Latest bar-close stamp that must already be written to the catalog.

    Honours the ~9 minute write-interval lag: at wall-clock ``now`` the newest
    fully-written bar closes at ``(now - buffer).floor(interval)``. Bars closing
    later may still be inside their write window.
    """
    moment = _to_utc(pd.Timestamp(now) if now is not None else pd.Timestamp.now("UTC"))
    buffered = moment - pd.Timedelta(minutes=write_buffer_minutes)
    # floor() rejects bare "15m" on newer pandas ('m' became month-end);
    # a fixed Timedelta is an unambiguous grid step.
    return buffered.floor(pd.Timedelta(interval))


def _interval_ns(interval: str) -> int:
    return int(pd.Timedelta(interval).value)


def fetch_tail(
    catalog,
    market_settings,
    data_settings,
    symbol: str,
    *,
    download_fn: Callable[..., dict] | None = None,
    now: pd.Timestamp | str | None = None,
    write_buffer_minutes: float = DEFAULT_WRITE_BUFFER_MINUTES,
    interval: str = "15m",
) -> dict[str, object]:
    """Bring one symbol's catalog up to the latest expected closed bar.

    Returns ``(bars_fetched, bars_written, first_ts, last_ts, status)`` where
    ``status`` is ``CATALOG_CURRENT`` (no fetch needed) or ``FETCHED``.
    ``bars_fetched`` reports what the downloader claims for the symbol;
    ``bars_written`` is the verified catalog growth (authoritative).

    Raises :class:`IncrementalPipelineError` with reason ``catalog_not_current``
    whenever freshness cannot be proven:

    * empty catalog (run the full historical download first);
    * downloader rejected the tail as overlapping/non-disjoint (W1 trap);
    * zero bars written although newer closed bars were expected;
    * seam discontinuity between old and new catalog ranges (a silently
      skipped bar would otherwise become an invisible gap).
    """
    download = download_fn or download_historical_data
    bar_type = market_settings.bar_type(symbol)

    before = catalog.bars(bar_type)
    if not before:
        raise IncrementalPipelineError(
            "catalog_not_current",
            f"{symbol}: empty catalog at {getattr(catalog, 'path', '?')}; "
            "run the full historical download first (incremental needs an anchor)",
        )

    ordered = sorted(int(bar.ts_event) for bar in before)
    first_ns, last_ns = ordered[0], ordered[-1]
    expected_ns = int(
        expected_latest_closed_bar(
            interval,
            now=now,
            write_buffer_minutes=write_buffer_minutes,
        ).value
    )

    def result(
        status: str, fetched: int, written: int, head: int, tail: int
    ) -> dict[str, object]:
        return {
            "symbol": symbol,
            "status": status,
            "bars_fetched": fetched,
            "bars_written": written,
            "first_ts": pd.Timestamp(head, unit="ns", tz="UTC").isoformat(),
            "last_ts": pd.Timestamp(tail, unit="ns", tz="UTC").isoformat(),
        }

    # Close stamps sit up to 100ms before their nominal grid point
    # (exchange closeTime convention); allow that when judging currency.
    if last_ns >= expected_ns - SEAM_TOLERANCE_NS:
        return result("CATALOG_CURRENT", 0, 0, first_ns, last_ns)

    # Catalog behind the expected closed bar -> attempt the disjoint tail.
    tail_start = (
        pd.Timestamp(last_ns, unit="ns", tz="UTC")
        + pd.Timedelta(minutes=TAIL_OFFSET_MINUTES)
    ).strftime("%Y-%m-%dT%H:%M:%S+00:00")

    scoped_market = dataclasses.replace(market_settings, symbols=(symbol,))
    scoped_data = dataclasses.replace(data_settings, start=tail_start, end=None)

    try:
        summary = download(scoped_market, scoped_data)
    except Exception as exc:  # noqa: BLE001
        text = str(exc)
        # W1 regression guard: these used to be swallowed as "already up to
        # date". They mean the catalog state contradicts our expectation.
        if "non-disjoint" in text or "start was > now" in text:
            raise IncrementalPipelineError(
                "catalog_not_current",
                f"{symbol}: tail request from {tail_start} rejected by download "
                f"pipeline ({text}); refusing to silently pass",
            ) from exc
        raise

    after = catalog.bars(bar_type)
    if not after:
        raise IncrementalPipelineError(
            "catalog_not_current",
            f"{symbol}: catalog empty after fetch attempt (downloader reported "
            f"{summary!r})",
        )
    new_ordered = sorted(int(bar.ts_event) for bar in after)
    new_first_ns, new_last_ns = new_ordered[0], new_ordered[-1]
    written = len(new_ordered) - len(ordered)

    per_symbol = {}
    if isinstance(summary, dict):
        per_symbol = summary.get("per_symbol", {}) or {}
    claimed = 0
    if isinstance(per_symbol.get(symbol), dict):
        claimed = int(per_symbol[symbol].get("bars_written", 0))

    if written <= 0:
        raise IncrementalPipelineError(
            "catalog_not_current",
            f"{symbol}: 0 bars written although exchange had newer closed bars "
            f"(catalog end {pd.Timestamp(last_ns, unit='ns', tz='UTC').isoformat()} "
            f"< expected {pd.Timestamp(expected_ns, unit='ns', tz='UTC').isoformat()}; "
            f"downloader claimed {claimed})",
        )

    step_ns = _interval_ns(interval)
    successors = [ts for ts in new_ordered if ts > last_ns]
    if not successors:
        raise IncrementalPipelineError(
            "catalog_not_current",
            f"{symbol}: no bars beyond previous end after fetch "
            f"(downloader claimed {claimed})",
        )
    seam_gap = min(successors) - last_ns
    if abs(seam_gap - step_ns) > SEAM_TOLERANCE_NS:
        raise IncrementalPipelineError(
            "catalog_not_current",
            f"{symbol}: seam discontinuity of {seam_gap / 60e9:.3f} min between "
            f"old end {pd.Timestamp(last_ns, unit='ns', tz='UTC').isoformat()} and "
            f"next bar "
            f"{pd.Timestamp(min(successors), unit='ns', tz='UTC').isoformat()}; "
            "a bar was silently skipped or duplicated",
        )

    return result("FETCHED", claimed, written, new_first_ns, new_last_ns)
