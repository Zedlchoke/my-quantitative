"""Download funding/OI/mark-price research bundles for selected symbols."""

from __future__ import annotations

import argparse
from datetime import datetime
from datetime import timedelta
from datetime import timezone

from data.derivatives import fetch_funding_history
from data.derivatives import fetch_mark_price_klines
from data.derivatives import fetch_open_interest_history
from data.derivatives import write_derivatives_bundle


def _to_ms(value: datetime) -> int:
    return int(value.timestamp() * 1000)


def main() -> int:
    parser = argparse.ArgumentParser(description="Download Binance derivatives overlays")
    parser.add_argument("symbols", nargs="+")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--output-dir", default="derivatives_data")
    args = parser.parse_args()

    end = datetime.now(timezone.utc)
    start = end - timedelta(days=args.days)
    for symbol in args.symbols:
        symbol = symbol.upper()
        funding = fetch_funding_history(symbol, start_ms=_to_ms(start), end_ms=_to_ms(end))
        oi = fetch_open_interest_history(symbol, start_ms=_to_ms(start), end_ms=_to_ms(end))
        mark = fetch_mark_price_klines(symbol, start_ms=_to_ms(start), end_ms=_to_ms(end))
        path = write_derivatives_bundle(
            args.output_dir,
            symbol,
            funding=funding,
            open_interest=oi,
            mark_price_klines=mark,
        )
        print(f"{symbol}: funding={len(funding)} oi={len(oi)} mark={len(mark)} -> {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
