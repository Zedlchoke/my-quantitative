"""PSV1 M3 binding ingest verification (scored-run precondition).

Re-downloads EVERY manifest entry from data.binance.vision, re-hashes the
fresh bytes against the manifest digest AND (where a staged file exists)
against the staged bytes. SPY snapshot digest is re-verified separately in
cells.load_spy on every load. ANY drift = fail-closed BLOCKED.
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import urllib.request
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1")
L1_STAGE = WT / "lane-btc-h1/research/control/phase_strategy_v1/lane_btc_h1/data_staging"
L2_STAGE = WT / "lane-btc-h4/research/control/phase_strategy_v1/lane_btc_h4/data_staging"


def _sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def _monthly_url(period: str) -> str:
    return f"https://data.binance.vision/data/futures/um/monthly/klines/BTCUSDT/1h/BTCUSDT-1h-{period}.zip"


def _daily_url(period: str) -> str:
    return f"https://data.binance.vision/data/futures/um/daily/klines/BTCUSDT/1h/BTCUSDT-1h-{period}.zip"


def verify() -> dict:
    results = {"verified": 0, "mismatch": [], "no_staged_file": 0}
    for lane, stage in (("BTC_H1", L1_STAGE), ("BTC_H4", L2_STAGE)):
        man = json.loads((BASE / f"lane_{lane.lower()}" / "data" / "manifest.json").read_text())
        for e in man["files"]:
            url = e.get("url") or (
                _daily_url(e["period"]) if e["kind"] == "daily_zip" else _monthly_url(e["period"]))
            with urllib.request.urlopen(url, timeout=60) as r:  # noqa: S310
                fresh = r.read()
            fresh_sha = _sha(fresh)
            staged_ok = None
            fname = e.get("file") or e.get("staged_file")
            staged = (stage / fname) if fname else None
            if staged is not None and staged.exists():
                staged_ok = _sha(staged.read_bytes()) == e["sha256"]
            elif fname is None:
                results["no_staged_file"] += 1
            if fresh_sha != e["sha256"] or (len(fresh) != e.get("bytes", len(fresh))):
                results["mismatch"].append({"lane": lane, "file": e.get("file", e.get("url")),
                                            "fresh_sha": fresh_sha, "manifest": e["sha256"]})
            elif staged_ok is False:
                results["mismatch"].append({"lane": lane, "file": fname,
                                            "error": "staged bytes differ from manifest"})
            else:
                results["verified"] += 1
    results["verdict"] = "PASS" if not results["mismatch"] else "BLOCKED"
    return results


if __name__ == "__main__":
    rep = verify()
    print(json.dumps(rep, indent=1))
    sys.exit(0 if rep["verdict"] == "PASS" else 2)
