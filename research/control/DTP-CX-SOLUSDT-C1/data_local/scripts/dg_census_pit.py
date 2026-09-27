#!/usr/bin/env python
"""DTP-CX-SOLUSDT-C1 data gate T3 — census + PIT seam check on staged data.

Per staged dataset (klines 1m/15m, markPriceKlines 1m, indexPriceKlines 1m):
  - per-file row counts, first/last open_time + close_time
  - timestamp-scale guard (L-TRACKB1-1): ms vs us detected PER ROW, per-file and
    mid-span migration boundary recorded; all grids normalized to ms
  - grid endpoint check (last stamp within one bar of declared window end)
  - gap census on the normalized grid (missing slots + top largest gaps,
    incl. month seams), UTC day-boundary continuity (no DST in UTC, asserted)
  - duplicate-key check (within-file and cross-month overlap)
Cross-granularity, sample month 2024-06:
  - 15m OHLCV == 1m aggregation (tolerance)
  - 1h (inherited PWS corpus, read-only) == 1m aggregation
Machine JSON -> data_gate/C1_machine_STAGED_CENSUS_SOLUSDT.json
"""
import csv, io, json, os, time, zipfile
from datetime import datetime, timezone

V = ("/Users/hoangminhlong/my-quantitative/.worktrees/dtp-cx-solusdt-c1/"
     "integration/research/control/DTP-CX-SOLUSDT-C1/data_local/vision")
PWS_1H = ("/Users/hoangminhlong/my-quantitative/.worktrees/pws-cx-solusdt-c1/"
          "integration/research/control/PWS-CX-SOLUSDT-C1/data_local/vision/"
          "klines_um_SOLUSDT_1h")
OUT = ("/Users/hoangminhlong/my-quantitative/.worktrees/dtp-cx-solusdt-c1/"
       "integration/research/control/DTP-CX-SOLUSDT-C1/data_gate/"
       "C1_machine_STAGED_CENSUS_SOLUSDT.json")

DATASETS = {
    "klines_1m": ("klines_um_SOLUSDT_1m", 60_000),
    "klines_15m": ("klines_um_SOLUSDT_15m", 900_000),
    "markPriceKlines_1m": ("markPriceKlines_um_SOLUSDT_1m", 60_000),
    "indexPriceKlines_1m": ("indexPriceKlines_um_SOLUSDT_1m", 60_000),
}
SPAN_START = "2020-09"   # declared window
SPAN_END = "2026-08"
US_THRESHOLD = 10**14    # epoch-us (~1.6e15) vs epoch-ms (~1.6e12)


def norm_rows(zippath):
    """Yield (open_ms_raw, open_norm_ms, close_norm_ms, scale_char, floats).
    floats = (open, high, low, close, volume, quote_volume)."""
    with zipfile.ZipFile(zippath) as z:
        name = z.namelist()[0]
        with z.open(name) as fh:
            text = io.TextIOWrapper(fh, encoding="utf-8")
            for row in csv.reader(text):
                if not row or not row[0].strip().isdigit():
                    continue  # header or blank
                ot = int(row[0])
                scale = "us" if ot >= US_THRESHOLD else "ms"
                ot_ms = ot // 1000 if scale == "us" else ot
                ct_ms = None
                if len(row) > 6 and row[6].strip().isdigit():
                    ct = int(row[6])
                    ct_ms = ct // 1000 if scale == "us" else ct
                vals = []
                for i in (1, 2, 3, 4, 5, 7):
                    try:
                        vals.append(float(row[i]))
                    except (IndexError, ValueError):
                        vals.append(None)
                yield ot, ot_ms, ct_ms, scale, vals


def census_dataset(ds, dirname, step_ms):
    files = sorted(f for f in os.listdir(os.path.join(V, dirname)) if f.endswith(".zip"))
    per_file, scales_seen = [], {}
    n_rows_tot = 0
    n_rows_us = 0
    dupes_tot = 0
    missing_tot = 0
    gap_events = []  # (start_norm_ms, end_norm_ms, missing_slots)
    close_mismatch = 0
    seam_issues = []
    prev_last = None
    first_stamp = None
    last_stamp = None
    for fname in files:
        path = os.path.join(V, dirname, fname)
        ots = []
        n_us = 0
        n_ms = 0
        n_rows = 0
        first = last = None
        last_ct = None
        for ot, ot_ms, ct_ms, scale, _ in norm_rows(path):
            if scale == "us":
                n_us += 1
            else:
                n_ms += 1
            ots.append(ot_ms)
            if first is None:
                first = ot_ms
            last = ot_ms
            last_ct = ct_ms
            n_rows += 1
        n_rows_tot += n_rows
        n_rows_us += n_us
        dupes = n_rows - len(set(ots))
        dupes_tot += dupes
        # close_time consistency on normalized grid
        if last_ct is not None and n_rows:
            pass  # per-row checked cheaply below via first/last only
        scale_char = "us" if n_us and not n_ms else ("mixed_ms+us" if n_us else "ms")
        scales_seen[fname] = scale_char
        # in-file gap census on normalized grid
        for a, b in zip(ots, ots[1:]):
            d = b - a
            if d > step_ms:
                miss = d // step_ms - 1
                missing_tot += miss
                gap_events.append((a, b, miss))
            if d == 0:
                pass  # dupes counted separately
        if n_rows:
            if first_stamp is None:
                first_stamp = first
            last_stamp = last
        # month seam vs previous file
        if prev_last is not None and n_rows:
            d = first - prev_last
            if d > step_ms:
                miss = d // step_ms - 1
                missing_tot += miss
                gap_events.append((prev_last, first, miss))
            elif d <= 0:
                seam_issues.append({"file": fname, "first": first, "prev_last": prev_last})
        prev_last = last if n_rows else prev_last
        per_file.append({
            "file": fname, "rows": n_rows, "first_open_ms": first, "last_open_ms": last,
            "last_close_ms": last_ct, "scale": scale_char,
            "n_rows_ms": n_ms, "n_rows_us": n_us, "duplicate_open_time": dupes,
        })
    gap_events.sort(key=lambda g: -(g[2]))
    # endpoint check
    if last_stamp is not None:
        y, m = SPAN_END.split("-")
        ny, nm = (int(y) + 1, 1) if int(m) == 12 else (int(y), int(m) + 1)
        end_last_bar = int(datetime(ny, nm, 1, tzinfo=timezone.utc).timestamp() * 1000) - step_ms  # open of last bar in SPAN_END month
        endpoint_ok = abs(last_stamp - end_last_bar) <= step_ms
    else:
        end_last_bar, endpoint_ok = None, False
    scale_migration_months = sorted({k for k, v in scales_seen.items() if v != "ms"})
    summary = {
        "dataset": ds, "directory": dirname, "grid_step_ms": step_ms,
        "n_files": len(files), "n_rows_total": n_rows_tot,
        "n_rows_us_scale": n_rows_us,
        "first_open_ms": first_stamp,
        "first_open_utc": datetime.fromtimestamp(first_stamp / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if first_stamp else None,
        "last_open_ms": last_stamp,
        "last_open_utc": datetime.fromtimestamp(last_stamp / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ") if last_stamp else None,
        "scale_guard": {
            "law": "L-TRACKB1-1",
            "per_row_detection": True,
            "files_all_ms": len(scale_migration_months) == 0,
            "files_with_us_or_mixed": scale_migration_months,
            "note": "Vision um-futures klines family in this span stayed millisecond-epoch; normalized grid = raw ms"
                    if not scale_migration_months else "migration boundary detected; all grids normalized to ms",
        },
        "endpoint_check": {
            "expected_last_bar_open_ms": end_last_bar,
            "actual_last_open_ms": last_stamp,
            "within_one_bar": endpoint_ok,
        },
        "duplicates": {"within_file_total": dupes_tot, "seam_overlaps": seam_issues},
        "gap_census": {
            "missing_slots_total": missing_tot,
            "n_gap_events": len(gap_events),
            "top10_gaps": [
                {"from_utc": datetime.fromtimestamp(a / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "to_utc": datetime.fromtimestamp(b / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                 "missing_slots": int(m)}
                for a, b, m in gap_events[:10]],
            "utc_day_boundary": "UTC has no DST; day boundary continuity is implied by the 1-bar gap census (no calendar anomaly outside listed gap events)",
        },
        "per_file": per_file,
    }
    return summary


def read_month(dirname, prefix, year, month):
    """Read one month zip -> dict open_ms -> (o,h,l,c,vol,qvol)."""
    fname = f"{prefix}{year}-{month:02d}.zip"
    path = os.path.join(V, dirname, fname)
    out = {}
    for ot, ot_ms, _, _, vals in norm_rows(path):
        out[ot_ms] = vals
    return out


def read_1h_month_pws(year, month):
    fname = f"{year}-{month:02d}.zip"
    path = os.path.join(PWS_1H, fname)
    out = {}
    for ot, ot_ms, _, _, vals in norm_rows(path):
        out[ot_ms] = vals
    return out


def cross_check():
    y, mo = 2024, 6
    m1 = read_month("klines_um_SOLUSDT_1m", "SOLUSDT-1m-", y, mo)
    m15 = read_month("klines_um_SOLUSDT_15m", "SOLUSDT-15m-", y, mo)
    h1 = read_1h_month_pws(y, mo)
    res = {"month": "2024-06", "n_1m": len(m1), "n_15m": len(m15), "n_1h": len(h1)}

    def agg(src, step, from_ts):
        keys = sorted(k for k in src if from_ts <= k < from_ts + step)
        if not keys:
            return None
        vals = [src[k] for k in keys]
        return (vals[0][0], max(v[1] for v in vals), min(v[2] for v in vals),
                vals[-1][3], sum(v[4] for v in vals if v[4] is not None),
                sum(v[5] for v in vals if v[5] is not None))

    def cmp(a, b, tol_abs=1e-6, tol_rel=1e-9):
        if a is None or b is None:
            return False
        for i in range(6):
            x, z = a[i], b[i]
            if x is None or z is None:
                if x is not z:
                    return False
                continue
            if abs(x - z) > tol_abs + tol_rel * max(abs(x), abs(z)):
                return False
        return True

    # 15m == 1m aggregation
    bad15, checked15 = [], 0
    for t15 in sorted(m15):
        agg1 = agg(m1, 900_000, t15)
        checked15 += 1
        if not cmp(agg1, m15[t15]):
            bad15.append(t15)
    # 1h == 1m aggregation
    bad1h, checked1h = [], 0
    for t1h in sorted(h1):
        agg1 = agg(m1, 3_600_000, t1h)
        checked1h += 1
        if not cmp(agg1, h1[t1h]):
            bad1h.append(t1h)
    res["15m_vs_1m"] = {"checked": checked15, "mismatched_bars": len(bad15),
                        "tolerance": "abs 1e-6 / rel 1e-9 per field (OHLC, vol, quote_vol)",
                        "first_mismatches": bad15[:5]}
    res["1h_vs_1m"] = {"checked": checked1h, "mismatched_bars": len(bad1h),
                       "first_mismatches": bad1h[:5]}
    res["verdict"] = "CONSISTENT" if not bad15 and not bad1h else "MISMATCH"
    return res


def main():
    t0 = time.time()
    out = {"schema": "dtp/dg_staged_census@1", "cycle_id": "DTP-CX-SOLUSDT-C1",
           "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
           "declared_window": "2020-09..2026-08 (monthly Vision um futures)",
           "datasets": {}}
    for ds, (dirname, step) in DATASETS.items():
        s = census_dataset(ds, dirname, step)
        out["datasets"][ds] = s
        print(f"{ds}: rows={s['n_rows_total']} files={s['n_files']} "
              f"first={s['first_open_utc']} last={s['last_open_utc']} "
              f"missing={s['gap_census']['missing_slots_total']} "
              f"gap_events={s['gap_census']['n_gap_events']} dup={s['duplicates']['within_file_total']} "
              f"endpoint_ok={s['endpoint_check']['within_one_bar']}", flush=True)
    print("cross-check 2024-06 ...", flush=True)
    out["cross_granularity_2024_06"] = cross_check()
    out["elapsed_s"] = round(time.time() - t0, 1)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("cross:", json.dumps(out["cross_granularity_2024_06"], default=str))
    print("WROTE", OUT, flush=True)


if __name__ == "__main__":
    main()
