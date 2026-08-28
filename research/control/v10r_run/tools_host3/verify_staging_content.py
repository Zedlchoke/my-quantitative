"""Host-3 content verification of the rebuilt staging tree (v2, decoded).

Nautilus parquet columns are raw fixed-precision u64 plus per-file metadata
(``price_precision`` / ``size_precision``); ``ts_event``/``ts_init`` are
nanoseconds. Bytes are therefore NOT comparable across files written with
different instrument precisions — decoded values are. This version decodes
every file with its own metadata and compares:

  1. shape      — unique-bar counts vs D2's recorded numbers;
  2. duplicates — BTCUSDT/ETHUSDT duplicate-row counts vs D2;
  3. coverage   — window-end bar present; zero 15m grid gaps over
                  [2025-07-22, 2026-08-21T00:00Z);
  4. content    — 3 anchor bars per symbol digit-exact vs live fapi klines
                  (open/high/low/close + volume);
  5. overlap    — decoded close+volume digit-exact against the four
                  baseline-authentic files still on this host;
  6. funding    — 20/20 bundles vs D2 n_rows / last settlement (instants).

Anything not executable is reported UNAVAILABLE_FAIL_CLOSED, never PASS.
"""

from __future__ import annotations

import glob
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from urllib.request import urlopen

import pandas as pd
import pyarrow.parquet as pq

REPO = Path(r"C:\Users\ROYAL\my-quantitative")
STAGING = REPO / "research/control/v10r_run/staging"
D2 = json.loads((REPO / "research/control/v10r_run/d2_stage_report.json").read_text())
WINDOW_END = pd.Timestamp("2026-08-21T00:00:00Z")
WARMUP_START = pd.Timestamp("2025-07-22T00:00:00Z")
ANCHOR_OPENS = [  # bar OPEN times, ms epoch
    pd.Timestamp("2026-08-20T23:45:00Z"),
    pd.Timestamp("2026-08-20T00:00:00Z"),
    pd.Timestamp("2025-08-20T00:00:00Z"),
]
FUNDING_FLOOR_MS = int(pd.Timestamp("2026-08-20T16:00:00Z").value // 10**6)
LIVE = "https://fapi.binance.com/fapi/v1/klines"
BAR_MS = 900_000


def _raw_ints(series: pd.Series) -> pd.Series:
    """Nautilus stores prices/volumes as 8-byte little-endian binaries."""
    def one(v):
        return int.from_bytes(v, "little") if isinstance(v, (bytes, bytearray)) else int(v)
    return series.map(one)


def read_decoded(path: str) -> pd.DataFrame:
    """Decode one nautilus bar part: ts -> ms epoch, prices/volume -> float."""
    pf = pq.ParquetFile(path)
    md = pf.metadata.metadata or {}
    pp = int(md.get(b"price_precision", b"0"))
    sp = int(md.get(b"size_precision", b"0"))
    df = pf.read(columns=["ts_event", "open", "high", "low", "close", "volume"]).to_pandas()
    out = pd.DataFrame(
        {
            "open_ms": (df["ts_event"].astype("uint64") // 10**6) - (BAR_MS - 1),
            "open": _raw_ints(df["open"]) / (10.0**pp),
            "high": _raw_ints(df["high"]) / (10.0**pp),
            "low": _raw_ints(df["low"]) / (10.0**pp),
            "close": _raw_ints(df["close"]) / (10.0**pp),
            "volume": _raw_ints(df["volume"]) / (10.0**sp),
        }
    )
    out["price_precision"] = pp
    out["size_precision"] = sp
    return out


def live_kline(symbol: str, open_ms: int) -> list | None:
    url = (
        f"{LIVE}?symbol={symbol}&interval=15m&startTime={open_ms}"
        f"&endTime={open_ms + BAR_MS - 1}&limit=1"
    )
    with urlopen(url, timeout=20) as r:
        data = json.loads(r.read())
    return data[0] if data else None


def bar_matches(live_kl: list, row: dict) -> bool:
    for want, got in (
        (live_kl[1], row["open"]),
        (live_kl[2], row["high"]),
        (live_kl[3], row["low"]),
        (live_kl[4], row["close"]),
    ):
        if Decimal(str(want)) != Decimal(repr(got)):
            return False
    return Decimal(str(live_kl[5])) == Decimal(repr(row["volume"]))


def main() -> int:
    report: dict = {
        "artifact": "host3_verify_staging_content",
        "version": 2,
        "producer_role": "A1",
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "per_symbol": {},
        "failures": [],
    }
    anchor_ms = [int(t.value // 10**6) for t in ANCHOR_OPENS]
    for sym, exp in sorted(D2["bars"]["per_symbol"].items()):
        rec: dict = {"symbol": sym}
        parts = sorted(glob.glob(str(STAGING / f"catalog/data/binance_bar/{sym}-PERP*/*.parquet")))
        rec["n_parts"] = len(parts)
        rec["expected_n_parts"] = exp["n_parts"]
        if not parts:
            rec["verdict"] = "UNAVAILABLE_FAIL_CLOSED"
            report["failures"].append(f"{sym}: no staged parts")
            report["per_symbol"][sym] = rec
            continue
        frames = [read_decoded(p) for p in parts]
        df = pd.concat(frames, ignore_index=True)
        rec["n_rows_raw"] = int(len(df))
        rec["n_unique"] = int(df["open_ms"].nunique())
        rec["expected_n_unique"] = exp["n_unique_bars"]
        rec["duplicates"] = rec["n_rows_raw"] - rec["n_unique"]
        rec["expected_duplicates"] = exp["n_duplicate_rows"]
        end_bar_open = int(pd.Timestamp("2026-08-20T23:45:00Z").value // 10**6)
        rec["window_end_bar_present"] = bool((df["open_ms"] == end_bar_open).any())
        grid = pd.date_range(WARMUP_START, WINDOW_END, freq="15min", inclusive="left").asi8 // 10**6
        have = set(int(v) for v in df["open_ms"])
        rec["grid_gaps_warmup_to_end"] = int(sum(1 for g in grid if g not in have))
        rec["last_bar_close_utc"] = pd.Timestamp(
            int(df["open_ms"].max()) + BAR_MS - 1, unit="ms"
        ).isoformat()

        anchor_hits = 0
        for open_ms in anchor_ms:
            sel = df[df["open_ms"] == open_ms]
            kl = live_kline(sym, open_ms)
            if kl is None or sel.empty:
                continue
            anchor_hits += 1 if bar_matches(kl, sel.iloc[-1].to_dict()) else 0
        rec["anchors_digit_exact"] = f"{anchor_hits}/{len(anchor_ms)}"

        checks_ok = (
            rec["window_end_bar_present"]
            and rec["grid_gaps_warmup_to_end"] == 0
            and rec["n_unique"] == exp["n_unique_bars"]
            and anchor_hits == len(anchor_ms)
        )
        rec["verdict"] = "PASS" if checks_ok else "FAIL"
        if not checks_ok:
            report["failures"].append(f"{sym}: {rec}")
        report["per_symbol"][sym] = rec
        print(f"[{rec['verdict']}] {sym}: uniq={rec['n_unique']} dups={rec['duplicates']} "
              f"gaps={rec['grid_gaps_warmup_to_end']} anchors={rec['anchors_digit_exact']} "
              f"last={rec['last_bar_close_utc'][:19]}", flush=True)

    overlap = {"method": "decoded close+volume equality on open_ms intersection", "pairs": []}
    for old_path in sorted(glob.glob(str(REPO / "catalog/data/binance_bar/*/*.parquet"))):
        sym_dir = Path(old_path).parent.name.split("-PERP")[0]
        old_name = Path(old_path).name
        new_paths = sorted(glob.glob(str(STAGING / f"catalog/data/binance_bar/{sym_dir}-PERP*/*.parquet")))
        old_t = read_decoded(old_path).drop_duplicates("open_ms")
        for np_ in new_paths:
            if Path(np_).name == old_name:
                continue
            new_t = read_decoded(np_)
            merged = old_t.merge(new_t, on="open_ms", suffixes=("_o", "_n"))
            if merged.empty:
                continue
            close_mism = int((merged["close_o"] != merged["close_n"]).sum())
            vol_mism = int((merged["volume_o"] != merged["volume_n"]).sum())
            overlap["pairs"].append({
                "symbol": sym_dir, "old": old_name, "new": Path(np_).name,
                "overlap_rows": int(len(merged)),
                "close_mismatches": close_mism, "volume_mismatches": vol_mism,
                "digit_exact": close_mism == 0 and vol_mism == 0,
            })
            print(f"[overlap] {sym_dir} {Path(np_).name[:20]} rows={len(merged)} "
                  f"close_mism={close_mism} vol_mism={vol_mism}", flush=True)

    fund: dict = {}
    ok_f = 0
    for sym, exp in sorted(D2["funding"]["per_symbol"].items()):
        f = STAGING / f"funding_data/scan_2026/{sym}/funding.json"
        if not f.exists():
            fund[sym] = "UNAVAILABLE_FAIL_CLOSED"
            report["failures"].append(f"funding {sym}: missing")
            continue
        rows = json.loads(f.read_text())["rows"]
        last_ms = max(r["fundingTime"] for r in rows)
        exp_last = int(pd.Timestamp(exp["last_settlement_utc"]).value // 10**6)
        matches = len(rows) == exp["n_rows"] and abs(last_ms - exp_last) <= 15_000
        floor_ok = last_ms >= FUNDING_FLOOR_MS
        fund[sym] = {
            "n_rows": len(rows), "expected_n_rows": exp["n_rows"],
            "matches_d2": matches, "satisfies_window_funding_floor": floor_ok,
        }
        ok_f += 1 if matches and floor_ok else 0
        if not (matches and floor_ok):
            report["failures"].append(f"funding {sym}: {fund[sym]}")
    report["funding"] = fund

    overlap_mism = sum(
        p["close_mismatches"] + p["volume_mismatches"] for p in overlap["pairs"]
    )
    if overlap_mism:
        report["failures"].append(f"overlap: {overlap_mism} decoded value mismatches")
    bars_ok = sum(1 for v in report["per_symbol"].values() if v["verdict"] == "PASS")
    report["overlap_equivalence"] = overlap
    report["summary"] = {
        "bars_pass": bars_ok,
        "bars_total": len(report["per_symbol"]),
        "funding_matched": ok_f,
        "funding_total": len(fund),
        "overlap_pairs": len(overlap["pairs"]),
        "overlap_rows": sum(p["overlap_rows"] for p in overlap["pairs"]),
        "overlap_mismatches": overlap_mism,
        "n_failures": len(report["failures"]),
        "all_pass": bars_ok == len(report["per_symbol"])
        and ok_f == len(fund) and not report["failures"],
    }
    report["finished_at_utc"] = datetime.now(timezone.utc).isoformat()
    (REPO / "research/control/v10r_run/host3_verify_staging_report.json").write_text(
        json.dumps(report, indent=1, default=str)
    )
    print("SUMMARY:", json.dumps(report["summary"]))
    return 0 if report["summary"]["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
