"""Weekly TradFi data-accumulation tracker.

Appends one row per eligible Binance TradFi (stock) perpetual to a CSV history
so we can see when each contract crosses the 365-day research gate.  Snapshots
are point-in-time and keep rejected contracts, matching the crypto workflow in
NOTES section 13.

Run weekly (or via launchd/cron):

    python -m research.tradfi_accumulate
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from data.universe import UniverseFilters, scan_universe

HISTORY_CSV = Path("research_snapshots/tradfi_history.csv")
GATE_DAYS = 365


def cmd_accumulate(args: argparse.Namespace) -> int:
    filters = UniverseFilters(
        min_onboard_days=args.min_onboard_days,
        min_quote_volume_24h=args.min_quote_volume,
        min_trades_24h=args.min_trades,
        include_crypto=False,
        include_tradfi=True,
    )
    stamp = datetime.now(timezone.utc)
    snapshot_path = (
        Path(args.snapshot_dir) / f"binance_tradfi_{stamp:%Y%m%d}.json"
    )
    snapshot = scan_universe(filters=filters, output_path=str(snapshot_path))

    rows = []
    for contract in snapshot["contracts"]:
        if not contract.get("eligible"):
            continue
        onboard = float(contract.get("onboard_days", 0.0))
        rows.append(
            {
                "captured_at": stamp.isoformat(timespec="seconds"),
                "symbol": contract["symbol"],
                "onboard_days": round(onboard, 1),
                "days_to_gate": round(max(0.0, GATE_DAYS - onboard), 0),
                "quote_volume_24h": round(float(contract.get("quote_volume_24h", 0.0)), 0),
                "trade_count_24h": int(contract.get("trade_count_24h", 0)),
                "ready_for_research": onboard >= GATE_DAYS,
            },
        )

    HISTORY_CSV.parent.mkdir(parents=True, exist_ok=True)
    file_exists = HISTORY_CSV.exists()
    with HISTORY_CSV.open("a", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)

    ready = [r for r in rows if r["ready_for_research"]]
    eta = sorted((r for r in rows if not r["ready_for_research"]), key=lambda r: r["days_to_gate"])
    print(f"Snapshot: {snapshot_path}")
    print(f"Eligible TradFi perps: {len(rows)} | appended to {HISTORY_CSV}")
    print(f"Ready for research (>={GATE_DAYS}d): {len(ready)}")
    for r in ready[:10]:
        print(f"  READY {r['symbol']:12s} {r['onboard_days']:.0f}d")
    print("Closest to gate:")
    for r in eta[:10]:
        print(
            f"  {r['symbol']:12s} ~{r['days_to_gate']:.0f}d left "
            f"(vol {r['quote_volume_24h'] / 1e6:.1f}M, trades {r['trade_count_24h'] / 1e3:.0f}k)",
        )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Track TradFi perpetual maturity over time")
    parser.add_argument("--snapshot-dir", default="research_snapshots")
    parser.add_argument("--min-onboard-days", type=int, default=0)
    parser.add_argument("--min-quote-volume", type=float, default=1_000_000.0)
    parser.add_argument("--min-trades", type=int, default=1_000)
    return cmd_accumulate(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
