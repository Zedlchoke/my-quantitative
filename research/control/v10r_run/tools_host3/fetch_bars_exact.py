"""Host-3 bootstrap: byte-exact re-fetch of missing staged bar parts.

Strategy: baseline stage_manifest_R1.csv paths encode the REQUESTED range
(filenames are `start_END.parquet` wall-clock stamps of the original fetch).
Re-issuing the identical request through the repo's own download engine
(data/download.py) over immutable Binance history reproduces the original
content; with the same pinned writer stack (nautilus 1.230.0, pyarrow 25.0.1)
the bytes should match the baseline sha256 too. Instrument-def side effects
are left in throwaway catalogs and never transplanted.

Failure handling: any symbol that cannot be fetched is reported and left
MISSING (fail-closed downstream); no content is invented.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(r"C:\Users\ROYAL\my-quantitative")
BASELINE = REPO / "research/control/v10_discovery_run/stage_manifest_R1.csv"
STAGING = REPO / "research/control/v10r_run/staging/catalog"
BOOT = Path(r"C:\Users\ROYAL\v10r_host3_bootstrap")
NAME_RE = re.compile(
    r"^(\d{4}-\d{2}-\d{2})T(\d{2})-(\d{2})-(\d{2})-(\d{9})Z_"
    r"(\d{4}-\d{2}-\d{2})T(\d{2})-(\d{2})-(\d{2})-(\d{9})Z\.parquet$"
)

sys.path.insert(0, str(REPO))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_name(name: str) -> tuple[str, str] | None:
    m = NAME_RE.match(name)
    if not m:
        return None
    a = f"{m.group(1)}T{m.group(2)}:{m.group(3)}:{m.group(4)}.{m.group(5)}Z"
    b = f"{m.group(6)}T{m.group(7)}:{m.group(8)}:{m.group(9)}.{m.group(10)}Z"
    return a, b


def load_baseline() -> list[dict]:
    rows = []
    with BASELINE.open(newline="") as fh:
        for sha, size, path in csv.reader(fh):
            if not path:
                continue
            rows.append({"sha256": sha, "size": int(size), "path": path})
    return rows


def entry_split(entry: dict) -> tuple[str, str, str]:
    """Return (symbol, filename, subdir) for a manifest bar path."""
    p = Path(entry["path"])
    return p.name, p.parent.name, str(p.parent.parent)


def run_group(symbols: tuple[str, ...], start: str, end: str, tag: str) -> list[Path]:
    """Fetch one (range -> symbols) group into a fresh throwaway catalog."""
    from config.settings import DataDownloadSettings, MarketSettings
    from data.download import download_historical_data

    cat = BOOT / f"throwaway_{tag}"
    if cat.exists():
        shutil.rmtree(cat)
    out = download_historical_data(
        MarketSettings(symbols=symbols, account_type="USDT_FUTURES"),
        DataDownloadSettings(
            catalog_path=str(cat), environment="LIVE", start=start, end=end
        ),
    )
    print(f"[group {tag}] {len(symbols)} symbols {start} -> {end}: {out['per_symbol']}", flush=True)
    return list((cat / "data/binance_bar").glob("*/*.parquet"))


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()
    report: dict = {
        "artifact": "host3_fetch_bars_exact",
        "producer_role": "A1",
        "started_at_utc": now,
        "host": "host3_windows_32gb",
        "reason": "migration bundle absent on host 3; Option A re-fetch via repo engine, "
        "byte-exact request replication from baseline manifest filenames",
        "entries": [],
        "groups": [],
    }
    baseline = [e for e in load_baseline() if "/binance_bar/" in e["path"]]
    funding_entries = [e for e in load_baseline() if "funding" in e["path"]]
    report["baseline_counts"] = {"bars": len(baseline), "funding": len(funding_entries)}

    pending: dict[tuple[str, str], list[dict]] = {}
    for e in baseline:
        tgt = REPO / e["path"]
        if tgt.exists() and sha256(tgt) == e["sha256"] and tgt.stat().st_size == e["size"]:
            report["entries"].append(
                {"path": e["path"], "status": "already_present_hash_match"}
            )
            continue
        name, subdir, _ = entry_split(e)
        rng = parse_name(name)
        if rng is None:
            report["entries"].append(
                {"path": e["path"], "status": "UNPARSEABLE_NAME", "fail_closed": True}
            )
            continue
        sym = subdir.split("-PERP")[0]
        pending.setdefault(rng, []).append({**e, "symbol": sym, "subdir": subdir})

    multi = {k: v for k, v in pending.items() if len(v) > 1}
    single = {k: v for k, v in pending.items() if len(v) == 1}
    report["plan"] = {
        "groups_multi_symbol": len(multi),
        "groups_single_symbol": len(single),
        "to_fetch_entries": sum(len(v) for v in pending.values()),
    }

    ok = bad = 0
    for gi, (rng, entries) in enumerate(sorted(multi.items())):
        syms = tuple(sorted({e["symbol"] for e in entries}))
        files = run_group(syms, rng[0], rng[1], f"multi{gi}")
        by_sym = {f.parent.name.split("-PERP")[0]: f for f in files}
        for e in entries:
            src = by_sym.get(e["symbol"])
            if src is None or src.name != Path(e["path"]).name:
                report["entries"].append(
                    {"path": e["path"], "status": "FETCH_FILE_MISSING", "fail_closed": True}
                )
                bad += 1
                continue
            ok += transplant(e, src, report)

    for gi, (rng, entries) in enumerate(sorted(single.items())):
        e = entries[0]
        files = run_group((e["symbol"],), rng[0], rng[1], f"single{gi}")
        src = next((f for f in files if f.name == Path(e["path"]).name), None)
        if src is None:
            report["entries"].append(
                {"path": e["path"], "status": "FETCH_FILE_MISSING", "fail_closed": True}
            )
            bad += 1
            continue
        ok += transplant(e, src, report)

    report["summary"] = {
        "fetched_hash_match": ok,
        "fetched_hash_mismatch_or_fail": bad,
        "already_present": sum(
            1 for x in report["entries"] if x["status"] == "already_present_hash_match"
        ),
        "all_baseline_bar_entries_resolved": ok + bad + report["summary"]["already_present"]
        if "summary" in report
        else None,
    }
    # recompute cleanly (avoid self-reference above)
    pres = sum(1 for x in report["entries"] if x["status"] == "already_present_hash_match")
    report["summary"] = {
        "fetched_hash_match": ok,
        "fetch_failures": bad,
        "already_present_hash_match": pres,
        "total_baseline_bars": len(baseline),
        "byte_identical_to_baseline": ok + pres == len(baseline),
    }
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    out_path = REPO / "research/control/v10r_run/host3_fetch_bars_report.json"
    out_path.write_text(json.dumps(report, indent=1))
    print("REPORT:", out_path)
    print("SUMMARY:", report["summary"])
    return 0 if bad == 0 else 1


def transplant(entry: dict, src: Path, report: dict) -> int:
    """Copy fetched part into staging and byte-compare with baseline."""
    tgt = REPO / entry["path"]
    tgt.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, tgt)
    got = sha256(tgt)
    match = got == entry["sha256"] and tgt.stat().st_size == entry["size"]
    report["entries"].append(
        {
            "path": entry["path"],
            "status": "fetched_hash_match" if match else "FETCHED_HASH_MISMATCH",
            "sha256_got": got,
            "fail_closed": not match,
        }
    )
    print(
        f"[{'OK' if match else 'MISMATCH'}] {entry['path'].split('/')[-1]} "
        f"({tgt.stat().st_size}B vs baseline {entry['size']}B)",
        flush=True,
    )
    return 1 if match else 0


if __name__ == "__main__":
    raise SystemExit(main())
