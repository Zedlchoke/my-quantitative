#!/usr/bin/env python
"""Adapter smoke test on the REAL raw snapshot (descriptive only).

Loads every raw file through the futbt adapter and reports parse coverage
and descriptive pathology fractions per symbol. NO PnL, no signals, no
strategy — this only proves the adapter matches the actual IBKR JSON
schema of ~/.my-quantitative-data/futures-10syms-v1/raw/ (read-only).

Run (offline, fast, no lock needed):
  /Users/hoangminhlong/my-quantitative/.venv/bin/python \\
      scripts/smoke_adapter_real.py \\
      --raw ~/.my-quantitative-data/futures-10syms-v1/raw \\
      --out ../analysis/engine_adapter_smoke.json
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from collections import defaultdict
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(CODE_DIR))

from futbt.rawdata import (RawFileName, RawFileError,  # noqa: E402
                           contracts_by_symbol, load_contract_directory)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    raw_dir = Path(args.raw).expanduser()
    files = sorted(raw_dir.glob("*.json"))
    parsed = 0
    failed: list[str] = []
    kinds: dict[str, int] = defaultdict(int)
    for p in files:
        try:
            name = RawFileName.parse(p.name)
            kinds[f"{name.what}/{name.bar_size}"
                  + ("/front" if name.is_front_marker else "")] += 1
            parsed += 1
        except RawFileError:
            failed.append(p.name)

    contracts = load_contract_directory(raw_dir)
    by = contracts_by_symbol(contracts)

    per_symbol: dict[str, dict] = {}
    for sym, cds in sorted(by.items()):
        daily_bars = close_only = neg = 0
        bidask_pairs = 0
        for cd in cds:
            daily_bars += len(cd.daily_trades)
            close_only += sum(1 for b in cd.daily_trades if b.is_close_only)
            neg += sum(1 for b in cd.daily_trades if b.c < 0)
            bidask_pairs += len(cd.daily_bidask_map())
        per_symbol[sym] = {
            "n_contracts": len(cds),
            "front": cds[0].identity.local_symbol if cds else None,
            "back": cds[-1].identity.local_symbol if cds else None,
            "daily_trade_bars": daily_bars,
            "close_only_fraction": round(close_only / daily_bars, 4)
            if daily_bars else None,
            "negative_close_bars": neg,
            "daily_bidask_overlap_days": bidask_pairs,
            "tz": cds[0].daily_trades and None,
        }

    doc = {
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(
            timespec="seconds"),
        "classification": "DESCRIPTIVE ONLY — adapter schema smoke on the "
                          "read-only raw snapshot; no PnL, no signals, no "
                          "selection (PREP lane rules)",
        "raw_dir": str(raw_dir),
        "files_total": len(files),
        "filenames_parsed_ok": parsed,
        "filenames_failed": failed,
        "file_kinds": dict(sorted(kinds.items())),
        "contracts_grouped": len(contracts),
        "per_symbol": per_symbol,
        "evidence_tag": "OBSERVED",
        "script": "research/control/FUTURES-BEHAVIOR-10SYMS-PREP-20261002/"
                  "code/scripts/smoke_adapter_real.py",
        "window": f"raw snapshot fetched 2026-10-02 "
                  f"({len(files)} files)",
    }
    out = Path(args.out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(doc, indent=1, sort_keys=True))
    print(json.dumps(doc, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
