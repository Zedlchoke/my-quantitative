"""CLI for reproducible Binance USD-M universe snapshots."""

from __future__ import annotations

import argparse
from datetime import datetime
from datetime import timezone
from pathlib import Path

from data.universe import UniverseFilters
from data.universe import scan_universe


def _default_output() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return str(Path("research_snapshots") / f"binance_usdm_{stamp}.json")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Snapshot the eligible Binance USD-M universe")
    parser.add_argument("--output", default=None)
    parser.add_argument("--min-onboard-days", type=int, default=365)
    parser.add_argument("--min-quote-volume", type=float, default=50_000_000.0)
    parser.add_argument("--min-trades", type=int, default=10_000)
    parser.add_argument("--tradfi", action="store_true", help="include TradFi perpetual contracts")
    parser.add_argument("--tradfi-only", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    filters = UniverseFilters(
        min_onboard_days=args.min_onboard_days,
        min_quote_volume_24h=args.min_quote_volume,
        min_trades_24h=args.min_trades,
        include_crypto=not args.tradfi_only,
        include_tradfi=args.tradfi or args.tradfi_only,
    )
    output = args.output or _default_output()
    snapshot = scan_universe(filters=filters, output_path=output)
    print(f"Universe snapshot: {output}")
    print(f"Eligible: {snapshot['eligible_count']}/{snapshot['total_contracts']}")
    print(", ".join(snapshot["eligible_symbols"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
