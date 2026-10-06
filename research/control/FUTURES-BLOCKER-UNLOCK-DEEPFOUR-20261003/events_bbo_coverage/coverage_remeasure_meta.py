#!/usr/bin/env python
"""A5-EVENTS-BBO-COVERAGE coverage re-measure (METADATA ONLY).

(a) IBKR raw staleness: max mtime per symbol group vs 2026-10-03.
(b) Vendor parquet coverage windows per symbol via parquet FOOTER metadata only
    (pyarrow ParquetFile.metadata + row-group statistics for ts_event min/max).
No data-column reads. No writes outside this lane directory.

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python coverage_remeasure_meta.py
Output: coverage_remeasure.json (next to this script).
"""
import datetime as dt
import json
import os
import re
import time

VENFOR_ROOT = "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/parquet"
IBKR_RAW = os.path.expanduser("~/.my-quantitative-data/futures-10syms-v1/raw")
IBKR_STAGING = os.path.expanduser(
    "~/.my-quantitative-data/futures-10syms-v1/staging_refetch_20261003"
)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "coverage_remeasure.json")
TODAY_UTC = dt.datetime(2026, 10, 3, tzinfo=dt.timezone.utc)

import pyarrow.parquet as pq  # noqa: E402


def iso(t: float) -> str:
    return dt.datetime.fromtimestamp(t, tz=dt.timezone.utc).isoformat()


# ---------------------------------------------------------------- IBKR raw --
def ibkr_staleness():
    groups = {}
    with os.scandir(IBKR_RAW) as it:
        for e in it:
            if not e.is_file():
                continue
            sym = e.name.split("_", 1)[0]
            st = e.stat()
            g = groups.setdefault(sym, {"n_files": 0, "max_mtime": 0.0, "min_mtime": None})
            g["n_files"] += 1
            g["max_mtime"] = max(g["max_mtime"], st.st_mtime)
            g["min_mtime"] = (
                st.st_mtime if g["min_mtime"] is None else min(g["min_mtime"], st.st_mtime)
            )
    out = {}
    for sym, g in sorted(groups.items()):
        max_dt = dt.datetime.fromtimestamp(g["max_mtime"], tz=dt.timezone.utc)
        out[sym] = {
            "n_files": g["n_files"],
            "min_mtime_utc": iso(g["min_mtime"]),
            "max_mtime_utc": iso(g["max_mtime"]),
            "age_days_vs_20261003": round(
                (TODAY_UTC - max_dt).total_seconds() / 86400.0, 3
            ),
        }
    return out


def staging_state():
    if not os.path.isdir(IBKR_STAGING):
        return {"present": False}
    files = []
    for e in os.scandir(IBKR_STAGING):
        if e.is_file():
            files.append(
                {"name": e.name, "mtime_utc": iso(e.stat().st_mtime), "bytes": e.stat().st_size}
            )
    files.sort(key=lambda x: x["mtime_utc"])
    return {"present": True, "n_files": len(files), "files": files}


# ------------------------------------------------------------- vendor parquet --
FNAME_RE = re.compile(r"__(\d{4}-\d{2}-\d{2})_(\d{4}-\d{2}-\d{2})\.parquet$")


def ns_to_utc(ns: int) -> str:
    return dt.datetime.fromtimestamp(ns / 1e9, tz=dt.timezone.utc).isoformat()


def vendor_meta():
    files = []
    for dirpath, _dirnames, filenames in os.walk(VENFOR_ROOT):
        for fn in sorted(filenames):
            if fn.endswith(".parquet"):
                files.append(os.path.join(dirpath, fn))
    per_file = []
    for path in sorted(files):
        rel = os.path.relpath(path, VENFOR_ROOT)
        group = rel.split(os.sep)[0]
        m = FNAME_RE.search(fn := os.path.basename(path))
        fname_from, fname_to = (m.group(1), m.group(2)) if m else (None, None)
        pf = pq.ParquetFile(path)  # footer read only
        md = pf.metadata
        cols = [md.schema.column(i).name for i in range(md.num_columns)]
        rec = {
            "group": group,
            "file": rel,
            "bytes": os.path.getsize(path),
            "fname_window": [fname_from, fname_to],
            "num_rows": md.num_rows,
            "num_row_groups": md.num_row_groups,
            "columns": cols,
        }
        # ts_event min/max from row-group statistics ONLY (no data decode)
        if "ts_event" in cols:
            idx = cols.index("ts_event")
            lo, hi = None, None
            for rg in range(md.num_row_groups):
                st = md.row_group(rg).column(idx).statistics
                if st is None or not st.has_min_max:
                    continue
                lo = st.min if lo is None or st.min < lo else lo
                hi = st.max if hi is None or st.max > hi else hi
            if lo is not None:
                rec["ts_event_min_utc"] = ns_to_utc(int(lo))
                rec["ts_event_max_utc"] = ns_to_utc(int(hi))
            else:
                rec["ts_event_min_utc"] = None
                rec["ts_event_stats_note"] = "row-group stats absent for ts_event"
        per_file.append(rec)
    return per_file


def summarize(per_file):
    """Aggregate O1M price coverage per symbol from group names + ts_event."""
    sym_re = re.compile(r"O1M-(ES|NQ|6E|6B|6J|6A|CL|NG|GC|SI)")
    summary = {}
    for r in per_file:
        m = sym_re.search(r["group"])
        if not m:
            continue
        sym = m.group(1)
        s = summary.setdefault(
            sym,
            {
                "o1m_files": 0,
                "o1m_rows": 0,
                "ts_event_min_utc": None,
                "ts_event_max_utc": None,
                "groups": [],
            },
        )
        s["o1m_files"] += 1
        s["o1m_rows"] += r["num_rows"]
        s["groups"].append(r["group"])
        if r.get("ts_event_min_utc"):
            if s["ts_event_min_utc"] is None or r["ts_event_min_utc"] < s["ts_event_min_utc"]:
                s["ts_event_min_utc"] = r["ts_event_min_utc"]
        if r.get("ts_event_max_utc"):
            if s["ts_event_max_utc"] is None or r["ts_event_max_utc"] > s["ts_event_max_utc"]:
                s["ts_event_max_utc"] = r["ts_event_max_utc"]
    for sym in ("ES", "NQ", "6E", "6B", "6J", "6A", "CL", "NG", "GC", "SI"):
        if sym not in summary:
            summary[sym] = {
                "o1m_files": 0,
                "o1m_rows": 0,
                "ts_event_min_utc": None,
                "ts_event_max_utc": None,
                "groups": [],
                "note": "NO ohlcv-1m files on disk (definition/statistics ALL10 only)",
            }
    # definition / statistics windows (ALL10)
    for kind in ("definition", "statistics"):
        rows = [r for r in per_file if r["group"] == f"AV1T-{kind}-ALL10"]
        if rows:
            lo = min(r["ts_event_min_utc"] for r in rows if r.get("ts_event_min_utc"))
            hi = max(r["ts_event_max_utc"] for r in rows if r.get("ts_event_max_utc"))
            summary[f"_ALL10_{kind}"] = {
                "files": len(rows),
                "rows": sum(r["num_rows"] for r in rows),
                "ts_event_min_utc": lo,
                "ts_event_max_utc": hi,
            }
    return summary


def main():
    t0 = time.time()
    out = {
        "schema": "a5_coverage_remeasure_v1",
        "generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "method": "OBSERVED — os.stat mtimes; parquet FOOTER metadata + row-group statistics only (no data scans)",
        "today_reference_utc": TODAY_UTC.isoformat(),
        "vendor_root": VENFOR_ROOT,
        "ibkr_raw_root": IBKR_RAW,
        "ibkr_raw_staleness": ibkr_staleness(),
        "ibkr_staging_refetch_20261003": staging_state(),
        "vendor_parquet_files": vendor_meta(),
    }
    out["vendor_o1m_summary"] = summarize(out["vendor_parquet_files"])
    out["runtime_seconds"] = round(time.time() - t0, 2)
    with open(OUT, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: out[k] for k in ("ibkr_raw_staleness", "vendor_o1m_summary", "runtime_seconds")}, indent=1))


if __name__ == "__main__":
    main()
