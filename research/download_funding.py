"""Download reproducible Binance funding bundles for backtest accounting."""

from __future__ import annotations

import argparse
from datetime import datetime
from datetime import timedelta
from datetime import timezone

import pandas as pd

from data.derivatives import fetch_funding_history
from data.derivatives import write_funding_history


def _utc(value: str) -> datetime:
    parsed = pd.Timestamp(value)
    if parsed.tzinfo is None:
        parsed = parsed.tz_localize("UTC")
    return parsed.tz_convert("UTC").to_pydatetime()


def _to_ms(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def main() -> int:
    parser = argparse.ArgumentParser(description="Download Binance funding accounting data")
    parser.add_argument("symbols", nargs="+")
    parser.add_argument("--days", type=int, default=730)
    parser.add_argument("--start")
    parser.add_argument("--end")
    parser.add_argument("--output-dir", default="funding_data")
    args = parser.parse_args()

    end = _utc(args.end) if args.end else datetime.now(timezone.utc)
    start = _utc(args.start) if args.start else end - timedelta(days=args.days)
    if start >= end:
        raise ValueError("Funding start must be earlier than end")
    start_ms = _to_ms(start)
    end_ms = _to_ms(end)

    for raw_symbol in args.symbols:
        symbol = raw_symbol.upper()
        rows = fetch_funding_history(symbol, start_ms=start_ms, end_ms=end_ms)
        path = write_funding_history(
            args.output_dir,
            symbol,
            requested_start_ms=start_ms,
            requested_end_ms=end_ms,
            rows=rows,
        )
        first = rows[0]["fundingTime"] if rows else None
        last = rows[-1]["fundingTime"] if rows else None
        print(f"{symbol}: rows={len(rows)} first={first} last={last} -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
