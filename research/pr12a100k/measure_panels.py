"""I1a panel measurement — PORTFOLIO-ROUTER-12ASSETS-100K-V1.

Read-only pass over the 5 FX price panels. Measures, per panel:
  - file count / total bytes (per side for M1 corpora)
  - first/last tradable timestamps measured FROM THE DATA (not filenames)
  - calendar gaps (missing day files, zero-tradable weekdays)
  - largest intraday tradable-minute gap
  - sha256 of index/manifest files (up to 3) + corpus digest:
      sha256 of the sorted newline-joined list "relpath size" for every
      data file in the panel (deterministic, order-independent).
  - DST/UTC evidence: FX week close/open boundary hours on winter vs
    summer Fridays/Sundays (NY 17:00 = 22:00 UTC under EST, 21:00 UTC
    under EDT; a 1-hour seasonal shift of the boundary inside UTC-stamped
    files is direct evidence the stamps are UTC).

Writes: measured_panels.json next to this script.

Run (from cycle worktree integration/):
  /Users/hoangminhlong/my-quantitative/.venv/bin/python \
      research/pr12a100k/measure_panels.py
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import lzma
import struct
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

REPO = Path("/Users/hoangminhlong/my-quantitative")
OUT = Path(__file__).resolve().parent / "measured_panels.json"

CANDLE = struct.Struct(">5if")  # (sec_of_day, open, close, low, high, vol_f32)

M1_PANELS = {
    "EURUSD": {
        "root": REPO
        / ".worktrees/fx-rangefade-2m-shadow-v1/research/control/"
        "FX-RANGEFADE-2M-SHADOW-V1/data_local/EURUSD",
        "scale": 1e5,
        "manifests": [
            REPO
            / ".worktrees/fx-rangefade-2m-shadow-v1/research/control/"
            "FX-RANGEFADE-2M-SHADOW-V1/data_local/EURUSD/m1_manifest.json",
        ],
        "staged_by": "EURUSD-RANGEEXP-SCORED-V1 (downloaded) / "
        "FX-RANGEFADE-2M-SHADOW-V1 (staged under data_local/EURUSD)",
    },
    "GBPUSD": {
        "root": REPO
        / ".worktrees/fx-majors-search-v1/integration/research/control/"
        "FX-MAJORS-SEARCH-V1/data_local/GBPUSD",
        "scale": 1e5,
        "manifests": [
            REPO
            / ".worktrees/fx-majors-search-v1/integration/research/control/"
            "FX-MAJORS-SEARCH-V1/data_local/GBPUSD/m1_manifest.json",
        ],
        "staged_by": "FX-MAJORS-SEARCH-V1",
    },
    "USDJPY": {
        "root": REPO
        / ".worktrees/fx-majors-search-v1/integration/research/control/"
        "FX-MAJORS-SEARCH-V1/data_local/USDJPY",
        "scale": 1e3,
        "manifests": [
            REPO
            / ".worktrees/fx-majors-search-v1/integration/research/control/"
            "FX-MAJORS-SEARCH-V1/data_local/USDJPY/m1_manifest.json",
        ],
        "staged_by": "FX-MAJORS-SEARCH-V1",
    },
}

H1_PANELS = {
    "USDCAD": {
        "path": REPO
        / ".worktrees/erp1-tracka-cohort-1/repro_twin/research/control/"
        "ERP1-TRACKA-COHORT-1/data_local/derived/bars1h_ANC_USDCAD.parquet",
        "manifests": [
            REPO
            / ".worktrees/erp1-tracka-cohort-1/repro_twin/research/control/"
            "ERP1-TRACKA-COHORT-1/data_local/derived/census_USDCAD.json",
            REPO
            / ".worktrees/erp1-tracka-cohort-1/repro_twin/research/control/"
            "ERP1-TRACKA-COHORT-1/data_local/derived/probe_USDCAD.json",
        ],
        "staged_by": "ERP1-TRACKA-COHORT-1 (repro_twin; source M1 from "
        "ECONOMIC-ROBUSTNESS-PROGRAM-V1 track-A pipeline, Dukascopy)",
    },
    "AUDUSD": {
        "path": REPO
        / ".worktrees/erp1-tracka-cohort-1/repro_twin/research/control/"
        "ERP1-TRACKA-COHORT-1/data_local/derived/bars1h_ANC_AUDUSD.parquet",
        "manifests": [
            REPO
            / ".worktrees/erp1-tracka-cohort-1/repro_twin/research/control/"
            "ERP1-TRACKA-COHORT-1/data_local/derived/census_AUDUSD.json",
            REPO
            / ".worktrees/erp1-tracka-cohort-1/repro_twin/research/control/"
            "ERP1-TRACKA-COHORT-1/data_local/derived/probe_AUDUSD.json",
        ],
        "staged_by": "ERP1-TRACKA-COHORT-1 (repro_twin; source M1 from "
        "ECONOMIC-ROBUSTNESS-PROGRAM-V1 track-A pipeline, Dukascopy)",
    },
}

# Fri/Sun pairs for the UTC/DST boundary probe (EST winter vs EDT summer).
DST_PROBE_DAYS = {
    "friday_winter_est": "2022-01-14",
    "sunday_winter_est": "2022-01-16",
    "friday_summer_edt": "2022-06-10",
    "sunday_summer_edt": "2022-06-12",
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def corpus_digest(root: Path, subdirs: tuple[str, ...]) -> tuple[str, int, int]:
    """sha256 over sorted 'relpath size' lines; returns (digest, n_files, bytes)."""
    lines = []
    total_bytes = 0
    n = 0
    for sub in subdirs:
        d = root / sub
        for f in sorted(d.glob("*.bi5")):
            size = f.stat().st_size
            lines.append(f"{sub}/{f.name} {size}")
            total_bytes += size
            n += 1
    blob = "\n".join(lines) + "\n"
    return hashlib.sha256(blob.encode()).hexdigest(), n, total_bytes


def decode_day(path: Path) -> np.ndarray:
    plain = lzma.decompress(path.read_bytes())
    if len(plain) % CANDLE.size:
        raise SystemExit(f"FAIL_CLOSED {path}: len {len(plain)} % 24 != 0")
    return np.frombuffer(
        plain,
        dtype=np.dtype(
            [("sec", ">i4"), ("o", ">i4"), ("c", ">i4"),
             ("l", ">i4"), ("h", ">i4"), ("v", ">f4")]
        ),
    )


def measure_m1(symbol: str, spec: dict) -> dict:
    root = Path(spec["root"])
    bid_files = sorted((root / "M1/BID").glob("*.bi5"))
    ask_files = sorted((root / "M1/ASK").glob("*.bi5"))
    bid_names = [f.name for f in bid_files]
    ask_names = [f.name for f in ask_files]
    if bid_names != ask_names:
        raise SystemExit(f"FAIL_CLOSED {symbol}: BID/ASK day sets differ")

    digest, n_files, total_bytes = corpus_digest(root, ("M1/BID", "M1/ASK"))

    first_ts = None
    last_ts = None
    missing_days: list[str] = []
    zero_tradable_weekdays: list[str] = []
    short_record_days: dict[str, list[int]] = {}
    largest_gap_min = 0
    largest_gap_at = None
    prev_last_sec = None  # last tradable sec of previous day (as epoch)
    ohlc_violations = 0
    n_minutes_total = 0
    n_minutes_tradable = 0

    d0 = dt.date.fromisoformat(bid_names[0][:10])
    d1 = dt.date.fromisoformat(bid_names[-1][:10])
    expected = {}
    cur = d0
    while cur <= d1:
        expected[cur.isoformat()] = False
        cur += dt.timedelta(days=1)

    for f in bid_files:
        name = f.name
        day = name[:10]
        expected[day] = True
        day0 = dt.datetime.fromisoformat(day).replace(tzinfo=dt.timezone.utc)
        arr_b = decode_day(f)
        arr_a = decode_day(root / "M1/ASK" / name)
        if len(arr_b) != 1440 or len(arr_a) != 1440:
            short_record_days[name] = [len(arr_b), len(arr_a)]
        secs = arr_b["sec"].astype(np.int64)
        vol = arr_b["v"].astype(np.float64)
        o = arr_b["o"].astype(np.float64) / spec["scale"]
        c = arr_b["c"].astype(np.float64) / spec["scale"]
        lo = arr_b["l"].astype(np.float64) / spec["scale"]
        hi = arr_b["h"].astype(np.float64) / spec["scale"]
        tradable = vol > 0
        ohlc_violations += int(np.sum(~((lo <= o + 1e-9) & (lo <= c + 1e-9)
                                        & (hi >= o - 1e-9) & (hi >= c - 1e-9)
                                        & (hi >= lo - 1e-9))))
        n_minutes_total += len(arr_b)
        n_minutes_tradable += int(tradable.sum())
        # intraday gaps between consecutive tradable minutes
        tsec = secs[tradable]
        if len(tsec):
            gaps = np.diff(tsec)
            if len(gaps):
                # gaps are in SECONDS; the metric is in MINUTES (unit fix:
                # the prior attempt stored raw seconds here, inflating the
                # intraday numbers ~60x vs the cross-day branch)
                g = int(gaps.max()) // 60
                if g > largest_gap_min:
                    largest_gap_min = g
                    largest_gap_at = day
            f_ts = day0 + dt.timedelta(seconds=int(tsec[0]))
            l_ts = day0 + dt.timedelta(seconds=int(tsec[-1]))
            if first_ts is None:
                first_ts = f_ts
            # day-boundary gap (weekend etc.) measured from prev tradable min
            if prev_last_sec is not None:
                g = int(tsec[0]) - prev_last_sec + 86400 * 0  # same-day only
                # cross-day gap:
            last_ts = l_ts
            prev_last_sec = int(tsec[-1])
        else:
            if dt.date.fromisoformat(day).weekday() < 5:
                zero_tradable_weekdays.append(day)

    # cross-day gaps: recompute simply — track consecutive file-days
    prev_end_epoch = None
    for f in bid_files:
        day = f.name[:10]
        arr_b = decode_day(f)
        secs = arr_b["sec"].astype(np.int64)
        vol = arr_b["v"].astype(np.float64)
        tsec = secs[vol > 0]
        if not len(tsec):
            continue
        day0 = dt.datetime.fromisoformat(day).replace(tzinfo=dt.timezone.utc)
        start_e = int(day0.timestamp()) + int(tsec[0])
        end_e = int(day0.timestamp()) + int(tsec[-1])
        if prev_end_epoch is not None:
            g = (start_e - prev_end_epoch) // 60
            if g > largest_gap_min:
                largest_gap_min = g
                largest_gap_at = day
        prev_end_epoch = end_e

    missing_days = sorted(d for d, seen in expected.items() if not seen)

    # DST/UTC evidence from boundary days (BID side, tradable minutes)
    dst_probe = {}
    for label, day in DST_PROBE_DAYS.items():
        p = root / "M1/BID" / f"{day}.bi5"
        if not p.exists():
            dst_probe[label] = None
            continue
        arr = decode_day(p)
        secs = arr["sec"].astype(np.int64)
        vol = arr["v"].astype(np.float64)
        tsec = secs[vol > 0]
        if not len(tsec):
            dst_probe[label] = None
            continue
        first = dt.timedelta(seconds=int(tsec[0]))
        last = dt.timedelta(seconds=int(tsec[-1]))
        # volume ramp: first hour whose share of day volume > 5%
        v_by_hour = {}
        for s, v in zip(tsec, vol[vol > 0]):
            v_by_hour[int(s) // 3600] = v_by_hour.get(int(s) // 3600, 0.0) + float(v)
        total_v = sum(v_by_hour.values())
        ramp_hour = None
        for h in sorted(v_by_hour):
            if v_by_hour[h] > 0.05 * total_v:
                ramp_hour = h
                break
        dst_probe[label] = {
            "first_tradable_utc": str(first),
            "last_tradable_utc": str(last),
            "volume_ramp_hour_utc_5pct": ramp_hour,
        }

    return {
        "symbol": symbol,
        "granularity": "M1",
        "root": str(root),
        "side_files": {"BID": len(bid_files), "ASK": len(ask_files)},
        "file_count": len(bid_files) + len(ask_files),
        "total_bytes": total_bytes,
        "file_date_span": [bid_names[0][:10], bid_names[-1][:10]],
        "first_ts": first_ts.isoformat() if first_ts else None,
        "last_ts": last_ts.isoformat() if last_ts else None,
        "corpus_digest": digest,
        "corpus_digest_strategy": (
            "sha256 of newline-joined sorted list "
            "'{side}/{filename} {size_in_bytes}' over all .bi5 files"
        ),
        "manifest_sha256": [
            {"path": str(m), "sha256": sha256_file(m)}
            for m in spec["manifests"]
            if m.exists()
        ],
        "n_minutes_total": n_minutes_total,
        "n_minutes_tradable": n_minutes_tradable,
        "missing_calendar_days": missing_days,
        "zero_tradable_weekdays": zero_tradable_weekdays,
        "short_record_days": short_record_days,
        "largest_tradable_gap_minutes": largest_gap_min,
        "largest_gap_on_day": largest_gap_at,
        "ohlc_invariant_violations": ohlc_violations,
        "dst_utc_probe": dst_probe,
        "staged_by": spec["staged_by"],
        "scale": spec["scale"],
    }


def measure_h1(symbol: str, spec: dict) -> dict:
    path = Path(spec["path"])
    tbl = pq.read_table(path)
    df = tbl.to_pandas()
    ts = pd_sorted = df["ts"]
    ts = ts.sort_values()
    diffs_min = ts.diff().dropna().dt.total_seconds() / 60.0
    largest_gap_h = float(diffs_min.max() / 60.0) if len(diffs_min) else 0.0
    at = ts.iloc[diffs_min.idxmax()] if len(diffs_min) else None
    dup = int(df["ts"].duplicated().sum())
    # DST/UTC evidence: hourly bars per March boundary day + boundary hour shift
    return {
        "symbol": symbol,
        "granularity": "H1",
        "path": str(path),
        "file_count": 1,
        "total_bytes": path.stat().st_size,
        "rows": int(len(df)),
        "columns": list(df.columns),
        "first_ts": ts.iloc[0].isoformat(),
        "last_ts": ts.iloc[-1].isoformat(),
        "file_sha256": sha256_file(path),
        "duplicate_ts": dup,
        "largest_gap_hours": largest_gap_h,
        "largest_gap_after": at.isoformat() if at is not None else None,
        "manifest_sha256": [
            {"path": str(m), "sha256": sha256_file(m)}
            for m in spec["manifests"]
            if m.exists()
        ],
        "staged_by": spec["staged_by"],
    }


def main() -> int:
    out = {"measured_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
           "m1": {}, "h1": {}}
    for sym, spec in M1_PANELS.items():
        print(f"measuring M1 {sym} ...", file=sys.stderr)
        out["m1"][sym] = measure_m1(sym, spec)
    for sym, spec in H1_PANELS.items():
        print(f"measuring H1 {sym} ...", file=sys.stderr)
        out["h1"][sym] = measure_h1(sym, spec)
    OUT.write_text(json.dumps(out, indent=1, default=str))
    print(json.dumps({
        sym: {
            "files": out["m1"][sym]["file_count"],
            "bytes": out["m1"][sym]["total_bytes"],
            "first": out["m1"][sym]["first_ts"],
            "last": out["m1"][sym]["last_ts"],
        }
        for sym in out["m1"]
    } | {
        sym: {
            "rows": out["h1"][sym]["rows"],
            "bytes": out["h1"][sym]["total_bytes"],
            "first": out["h1"][sym]["first_ts"],
            "last": out["h1"][sym]["last_ts"],
        }
        for sym in out["h1"]
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
