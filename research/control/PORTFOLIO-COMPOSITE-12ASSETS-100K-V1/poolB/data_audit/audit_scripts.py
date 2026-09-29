#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Lane D (data/PIT/cost audit) — PORTFOLIO-COMPOSITE-12ASSETS-100K-V1, pool B.

Physical audit of the three M1 FX panels that would back the volume-profile /
tick-volume strategy class: EURUSD (fx-rangefade-2m-shadow-v1 worktree),
GBPUSD + USDJPY (fx-majors-search-v1 worktree). Dukascopy .bi5 daily M1
candle files, BID + ASK sides.

Stages (deterministic, no network, READ-ONLY on the panels; writes only to
this lane's output dir):
  1. inventory     — file counts, date span, missing weekday/weekend files,
                     non-conforming names, 0-byte files.
  2. hashpass      — sha256 + size of EVERY .bi5 (-> panel_hashes_<PAIR>.jsonl),
                     lzma-decode EVERY file (decodability, record counts),
                     minute-level tradable census + per-minute spread matrices.
  3. format_verify — empirical record-format verification on the structured
                     sample (candidate structs, field order, price-scale
                     divisor, volume encoding, timestamp units, continuity).
  4. sample_stats  — structured ~68-day sample: price bands, OHLC invariants,
                     volume distribution / session profile / BID-ASK agreement,
                     weekend carry-forward behaviour, Sunday reopen.
  5. spread_check  — 20-weekday x 4-timepoint spread spot-check; C1 re-measure
                     (all Fridays 2021-01-08..2026-06-26, [20:00,20:01) bar);
                     C2 roll-window and C3 Sunday-reopen corroboration.
  6. provenance    — cross-check vs pr12a100k data_manifest_fx.json (counts,
                     bytes, corpus digests) and the staged m1_manifest.json
                     per-file hashes (all 4184 files per pair).

Outputs written by this script:
  <out>/panel_hashes_<PAIR>.jsonl   (3 files, per-file path/bytes/sha256)
  <out>/audit_summary.json          (machine-readable, everything below)
The MD report and the handoff JSON are authored by the lane from these outputs.

Run:  .venv/bin/python audit_scripts.py
"""

import hashlib
import json
import lzma
import re
import sys
import time
from datetime import date, timedelta
from pathlib import Path

import numpy as np

ROOT = Path("/Users/hoangminhlong/my-quantitative")
OUT = ROOT / "research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/poolB/data_audit"

PANELS = {
    "EURUSD": ROOT / ".worktrees/fx-rangefade-2m-shadow-v1/research/control/FX-RANGEFADE-2M-SHADOW-V1/data_local/EURUSD/M1",
    "GBPUSD": ROOT / ".worktrees/fx-majors-search-v1/integration/research/control/FX-MAJORS-SEARCH-V1/data_local/GBPUSD/M1",
    "USDJPY": ROOT / ".worktrees/fx-majors-search-v1/integration/research/control/FX-MAJORS-SEARCH-V1/data_local/USDJPY/M1",
}
SCALE = {"EURUSD": 1e5, "GBPUSD": 1e5, "USDJPY": 1e3}   # raw uint -> price divisor (to be DERIVED, then confirmed)
PIP = {"EURUSD": 1e-4, "GBPUSD": 1e-4, "USDJPY": 1e-2}  # 1 pip in price units
# generous absolute plausibility bands (task bands are narrower; these only
# serve to discriminate the order of magnitude of the scale divisor)
BAND = {"EURUSD": (0.85, 1.35), "GBPUSD": (0.95, 1.50), "USDJPY": (90.0, 170.0)}

PRIOR_MANIFEST = ROOT / ".worktrees/portfolio-router-12assets-100k-v1/integration/research/pr12a100k/data_manifest_fx.json"
COST_TABLE_PATH = ROOT / "research/control/SLEEVE-FX5-100K-V1/pitcost/COST_AUTHORITY_TABLE.md"

NAME_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})\.bi5$")
MINUTES_PER_DAY = 1440
REC_BYTES = 24

# ---------------------------------------------------------------- samples --
SPAN_START = date(2021, 1, 1)
SPAN_END = date(2026, 9, 23)

# grid every 47 days (47 mod 7 = 5 -> cycles through all weekday phases;
# a 50-day grid from a Friday would sample ONLY Fridays)
GRID = [SPAN_START + timedelta(days=47 * k) for k in range(45)]

# Sunday-reopen days (first trading day of a week)
TRICKY_SUNDAYS = [date(2021, 1, 3), date(2022, 1, 2), date(2024, 1, 7), date(2025, 6, 15)]
# Christmas / New-Year week days (half-days and full closures)
TRICKY_HOLIDAY = [
    date(2021, 12, 24), date(2021, 12, 27), date(2021, 12, 31),
    date(2022, 12, 23), date(2022, 12, 26), date(2022, 12, 27), date(2022, 12, 30),
    date(2023, 1, 2), date(2024, 12, 25), date(2024, 12, 31), date(2025, 1, 1),
]
# roll-window Wednesdays (incl. first-of-month triple-swap 2023-03-01)
TRICKY_ROLLWED = [date(2023, 3, 1), date(2023, 6, 14), date(2024, 6, 12), date(2025, 6, 11), date(2026, 1, 7)]
# macro anchor days (approximate known extremes, from lane knowledge; used
# ONLY as order-of-magnitude scale anchors, not exact assertions)
TRICKY_ANCHOR = [date(2022, 9, 26), date(2022, 9, 28), date(2024, 7, 3)]

DECODE_SAMPLE = sorted(set(GRID) | set(TRICKY_SUNDAYS) | set(TRICKY_HOLIDAY)
                       | set(TRICKY_ROLLWED) | set(TRICKY_ANCHOR))

# 20 evenly-spaced weekdays for the spread spot-check
ALL_WEEKDAYS = [d for d in (SPAN_START + timedelta(days=i)
                            for i in range((SPAN_END - SPAN_START).days + 1))
                if d.weekday() < 5]
_idx = sorted({round(k * (len(ALL_WEEKDAYS) - 1) / 19) for k in range(20)})
SPREAD_SAMPLE = [ALL_WEEKDAYS[i] for i in _idx]

# C1 window from COST_AUTHORITY_TABLE (Friday-20:00 fill spread, n=286)
C1_START, C1_END = date(2021, 1, 8), date(2026, 6, 26)
FRIDAYS_C1 = [d for d in (C1_START + timedelta(days=i)
                          for i in range((C1_END - C1_START).days + 1))
              if d.weekday() == 4]

SPOT_MINUTES = {"02:00": 120, "12:00": 720, "20:00": 1200, "21:30": 1290}
ROLL_WINDOW_MINUTES = list(range(1260, 1320))  # bars opening 21:00..21:59 close in (21:00,22:00]

COST_TABLE_C1 = {"EURUSD": (0.3, 0.5), "GBPUSD": (0.8, 1.3), "USDJPY": (0.5, 0.9)}
COST_TABLE_C2_MONTTHU = {"EURUSD": (0.6, 2.7), "GBPUSD": (1.4, 5.8), "USDJPY": (1.0, 4.9)}
COST_TABLE_C2_FRI = {"EURUSD": (0.5, 1.1), "GBPUSD": (1.2, 2.3), "USDJPY": (0.8, 1.8)}
COST_TABLE_C3 = {"EURUSD": (5.9, 9.0), "GBPUSD": (13.4, 23.8), "USDJPY": (11.0, 22.0)}


def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def daterange(a, b):
    d = a
    while d <= b:
        yield d
        d += timedelta(days=1)


def pcts(a, qs=(10, 50, 90, 99)):
    if len(a) == 0:
        return {f"p{q}": None for q in qs}
    return {f"p{q}": round(float(np.percentile(a, q)), 4) for q in qs}


def iso(d):
    return d.isoformat()


# ------------------------------------------------------------ decode core --
DTYPE_REC = np.dtype([("t", ">u4"), ("o", ">u4"), ("c", ">u4"),
                      ("l", ">u4"), ("h", ">u4"), ("v", ">f4")])


def decode_bi5(path):
    """Return (raw_bytes, decompressed_bytes, structured_array_or_None, err)."""
    raw = path.read_bytes()
    try:
        dec = lzma.decompress(raw, format=lzma.FORMAT_AUTO)
    except Exception as e:  # noqa: BLE001 - record any decode failure
        return raw, None, None, f"{type(e).__name__}: {e}"
    if len(dec) % REC_BYTES != 0:
        return raw, dec, None, f"len%24={len(dec) % 24}"
    if len(dec) == 0:
        return raw, dec, None, "empty payload"
    arr = np.frombuffer(dec, dtype=DTYPE_REC)
    return raw, dec, arr, None


# ------------------------------------------------------- stage 1+2: pass ---
def audit_pair(pair):
    """Inventory + hash + decode pass over one pair. Returns state dict."""
    m1dir = PANELS[pair]
    t0 = time.time()
    side_files, side_badnames = {}, {}
    for side in ("BID", "ASK"):
        d = m1dir / side
        files, bad = {}, []
        for p in sorted(d.iterdir()):
            if not p.is_file():
                continue
            m = NAME_RE.match(p.name)
            if not m:
                bad.append(p.name)
                continue
            files[m.group(1)] = p
        side_files[side], side_badnames[side] = files, bad

    dates = sorted(set(side_files["BID"]) | set(side_files["ASK"]))
    date_key = [date.fromisoformat(s) for s in dates]
    row_of = {s: i for i, s in enumerate(dates)}
    n = len(dates)

    trad = {s: np.zeros((n, MINUTES_PER_DAY), dtype=bool) for s in ("BID", "ASK")}
    spread_open = np.zeros((n, MINUTES_PER_DAY), dtype=np.int32)   # raw points
    spread_close = np.zeros((n, MINUTES_PER_DAY), dtype=np.int32)  # raw points
    per_file = {s: {} for s in ("BID", "ASK")}
    anomalies = []

    for i, ds in enumerate(dates):
        arrs = {}
        for side in ("BID", "ASK"):
            p = side_files[side].get(ds)
            if p is None:
                per_file[side][ds] = {"missing_side_file": True}
                anomalies.append(f"{side} {ds}: file missing")
                continue
            raw, dec, arr, err = decode_bi5(p)
            rec = {"path": str(p), "bytes": len(raw),
                   "sha256": hashlib.sha256(raw).hexdigest(),
                   "zero_byte": len(raw) == 0}
            if err is not None:
                rec["decode_error"] = err
                per_file[side][ds] = rec
                if not rec["zero_byte"]:
                    anomalies.append(f"{side} {ds}: {err}")
                continue
            nrec = len(dec) // REC_BYTES
            rec["nrec"] = nrec
            if nrec != MINUTES_PER_DAY:
                anomalies.append(f"{side} {ds}: nrec={nrec} (expected 1440)")
            per_file[side][ds] = rec
            m = np.frombuffer(dec, dtype=">u4").reshape(nrec, 6)
            tv = m[:, 5] != 0  # nonzero float32 bits <=> volume != 0 (non-negative)
            trad[side][i, :nrec] = tv
            arrs[side] = m
        if "BID" in arrs and "ASK" in arrs:
            mb, ma = arrs["BID"], arrs["ASK"]
            if mb.shape[0] == MINUTES_PER_DAY and ma.shape[0] == MINUTES_PER_DAY:
                spread_open[i] = ma[:, 1].astype(np.int32) - mb[:, 1].astype(np.int32)
                spread_close[i] = ma[:, 2].astype(np.int32) - mb[:, 2].astype(np.int32)

    # ---- inventory numbers
    span_days = (date_key[-1] - date_key[0]).days + 1
    cal = list(daterange(date_key[0], date_key[-1]))
    present = set(dates)
    missing_weekday = [iso(d) for d in cal if d.weekday() < 5 and iso(d) not in present]
    missing_weekend = [iso(d) for d in cal if d.weekday() >= 5 and iso(d) not in present]

    side_stats = {}
    for side in ("BID", "ASK"):
        pf = per_file[side]
        nfiles = sum(1 for k, v in pf.items() if "sha256" in v)
        total_bytes = sum(v.get("bytes", 0) for v in pf.values())
        zero_byte = [k for k, v in pf.items() if v.get("zero_byte")]
        undecodable = [k for k, v in pf.items() if "decode_error" in v]
        nrec_hist = {}
        for v in pf.values():
            if "nrec" in v:
                nrec_hist[str(v["nrec"])] = nrec_hist.get(str(v["nrec"]), 0) + 1
        lines = [f"{k}|{v['bytes']}|{v['sha256']}" for k, v in sorted(pf.items()) if "sha256" in v]
        agg = hashlib.sha256("\n".join(sorted(lines)).encode()).hexdigest()
        # prior manifest's corpus-digest method: sha256 over newline-joined
        # sorted "filename,size" lines (both trailing-newline variants tried)
        clines = sorted(f"{k}.bi5,{v['bytes']}" for k, v in pf.items() if "sha256" in v)
        cd1 = hashlib.sha256("\n".join(clines).encode()).hexdigest()
        cd2 = hashlib.sha256(("\n".join(clines) + "\n").encode()).hexdigest()
        side_stats[side] = {
            "files": nfiles,
            "total_bytes": total_bytes,
            "zero_byte_files": zero_byte,
            "undecodable_files": undecodable,
            "nrec_histogram": nrec_hist,
            "aggregate_digest_sha256": agg,
            "aggregate_digest_method": "sha256 of '\\n'.join(sorted 'YYYY-MM-DD|bytes|sha256' lines)",
            "corpus_digest_prior_method_no_trailing_nl": cd1,
            "corpus_digest_prior_method_trailing_nl": cd2,
            "min_date": dates[0] if dates else None,
            "max_date": dates[-1] if dates else None,
        }

    # ---- census
    def census(side):
        t = trad[side]
        flat = t.reshape(-1)
        nz = np.nonzero(flat)[0]
        first_flat = int(nz[0]) if len(nz) else None
        last_flat = int(nz[-1]) if len(nz) else None

        def flat_to_ts(idx):
            return (date_key[idx // MINUTES_PER_DAY],
                    idx % MINUTES_PER_DAY)

        x = flat.astype(np.int8)
        dd = np.diff(np.concatenate(([0], x, [0])))
        starts = np.where(dd == 1)[0]
        ends = np.where(dd == -1)[0]
        if len(starts):
            runs = ends - starts
            k = int(runs.argmax())
            run_len, run_start = int(runs[k]), int(starts[k])
            rd, rm = flat_to_ts(run_start)
            run_info = {"minutes": run_len, "start_date": iso(rd),
                        "start_minute_utc": rm,
                        "start_time_utc": f"{rm // 60:02d}:{rm % 60:02d}"}
        else:
            run_info = None
        day_trad = t.sum(axis=1)
        zero_days = [iso(date_key[i]) for i in range(n) if day_trad[i] == 0]
        zero_weekday = [d for d in zero_days
                        if date.fromisoformat(d).weekday() < 5]
        zero_weekend = [d for d in zero_days
                        if date.fromisoformat(d).weekday() >= 5]
        first_ts = None
        if first_flat is not None:
            fd, fm = flat_to_ts(first_flat)
            first_ts = f"{iso(fd)}T{fm // 60:02d}:{fm % 60:02d}:00Z"
        last_ts = None
        if last_flat is not None:
            ld, lm = flat_to_ts(last_flat)
            last_ts = f"{iso(ld)}T{lm // 60:02d}:{lm % 60:02d}:00Z"
        return {
            "tradable_minutes": int(day_trad.sum()),
            "first_tradable_ts": first_ts,
            "last_tradable_ts": last_ts,
            "largest_tradable_run": run_info,
            "zero_tradable_weekdays": zero_weekday,
            "zero_tradable_weekend_days_count": len(zero_weekend),
            "zero_tradable_days_total": len(zero_days),
        }

    neg_open_all = int((spread_open < 0).sum())
    neg_close_all = int((spread_close < 0).sum())
    max_open_pts = int(spread_open.max())

    state = {
        "path": str(m1dir),
        "dates": dates, "date_key": date_key, "row_of": row_of,
        "per_file": per_file, "trad": trad,
        "spread_open": spread_open, "spread_close": spread_close,
        "anomalies": anomalies,
        "side_stats": side_stats,
        "census": {"BID": census("BID"), "ASK": census("ASK")},
        "inventory": {
            "span_calendar_days": span_days,
            "files_per_side": {s: side_stats[s]["files"] for s in ("BID", "ASK")},
            "missing_weekday_files": missing_weekday,
            "missing_weekend_files": missing_weekend,
            "non_conforming_names": {s: side_badnames[s] for s in ("BID", "ASK")},
            "side_date_sets_identical": set(side_files["BID"]) == set(side_files["ASK"]),
        },
        "spread_matrix": {
            "negative_spread_open_minutes_all": neg_open_all,
            "negative_spread_close_minutes_all": neg_close_all,
            "max_spread_open_points": max_open_pts,
        },
    }
    pair_lines = []
    for side in ("BID", "ASK"):
        for k, v in sorted(per_file[side].items()):
            if "sha256" in v:
                pair_lines.append(f"{side}:{k}|{v['bytes']}|{v['sha256']}")
    state["pair_aggregate_digest"] = hashlib.sha256(
        "\n".join(sorted(pair_lines)).encode()).hexdigest()
    log(f"  {pair}: pass done in {time.time() - t0:.1f}s "
        f"({n} dates, anomalies={len(anomalies)})")
    return state


def write_hash_jsonl(pair, state):
    out = OUT / f"panel_hashes_{pair}.jsonl"
    with out.open("w") as f:
        for side in ("BID", "ASK"):
            for k in sorted(state["per_file"][side]):
                v = state["per_file"][side][k]
                if "sha256" not in v:
                    continue
                f.write(json.dumps({
                    "pair": pair, "side": side, "file": f"{k}.bi5",
                    "path": v["path"], "bytes": v["bytes"],
                    "sha256": v["sha256"]}) + "\n")
    return out


# --------------------------------------------- stage 3+4: sample analytics --
def sample_analytics(pair, state):
    """Decode the structured sample; format verification + volume statistics."""
    sc, pip = SCALE[pair], PIP[pair]
    res = {"sample_size": len(DECODE_SAMPLE),
           "sample_dates": [iso(d) for d in DECODE_SAMPLE]}
    # weekday composition of sample
    comp = {}
    for d in DECODE_SAMPLE:
        comp[d.strftime("%a")] = comp.get(d.strftime("%a"), 0) + 1
    res["sample_weekday_composition"] = comp

    sides = {}
    day_flags = []  # (weekday_bool) per successfully decoded BID file, aligned with BID vols
    for side in ("BID", "ASK"):
        vols, opens, recs_all, files_used = [], [], 0, 0
        vol_frac_per_day = {}
        for ds in DECODE_SAMPLE:
            p = PANELS[pair] / side / f"{iso(ds)}.bi5"
            if not p.exists():
                continue
            raw, dec, arr, err = decode_bi5(p)
            if arr is None:
                res.setdefault("sample_decode_errors", []).append(f"{side} {ds}: {err}")
                continue
            files_used += 1
            recs_all += len(arr)
            v = arr["v"].astype(np.float64)
            vols.append(v)
            opens.append(arr["o"].astype(np.int64))
            if side == "BID":
                day_flags.append(ds.weekday() < 5)
            tv = v > 0
            vol_frac_per_day[iso(ds)] = {
                "weekday": ds.weekday() < 5,
                "n_minutes": len(v),
                "n_vol_gt0": int(tv.sum()),
                "price_min_scaled": float(arr["o"][tv].min() / sc) if tv.any() else None,
                "price_max_scaled": float(arr["o"][tv].max() / sc) if tv.any() else None,
            }
        vol = np.concatenate(vols)
        op = np.concatenate(opens)
        sides[side] = {"vol": vol, "open": op, "files_used": files_used,
                       "recs": recs_all, "per_day": vol_frac_per_day}

    # ---------- format verification (BID side primarily) ----------
    b = sides["BID"]
    vol = b["vol"]
    fmt = {}
    # field0 / timestamp units, record length on one busy file
    pbusy = PANELS[pair] / "BID" / "2023-06-14.bi5"
    raw, dec, arr, err = decode_bi5(pbusy)
    if arr is not None:
        t = arr["t"].astype(np.int64)
        diffs = np.unique(np.diff(t))
        fmt["busy_file"] = {
            "file": "2023-06-14.bi5", "side": "BID",
            "uncompressed_bytes": len(dec), "records": len(arr),
            "bytes_per_record": len(dec) / len(arr),
            "t_min": int(t.min()), "t_max": int(t.max()),
            "t_unique_diffs": [int(x) for x in diffs],
            "timestamp_units_verdict": "seconds-from-00:00-UTC" if int(t.max()) <= 90000 else "NOT_SECONDS",
        }
        tv = arr["v"] > 0
        # field-order hypotheses on positions f1..f4 after the timestamp
        f1, f2, f3, f4 = (arr[x].astype(np.int64) for x in "oclh")
        # H_A Dukascopy order (t,o,c,l,h): f3<=min(f1,f2), f4>=max(f1,f2), f3<=f4
        vA = int(((f3 > np.minimum(f1, f2)) | (f4 < np.maximum(f1, f2)) | (f3 > f4))[tv].sum())
        # H_B OHLC order (t,o,h,l,c): f2>=max(f1,f4), f3<=min(f1,f4)
        vB = int(((f2 < np.maximum(f1, f4)) | (f3 > np.minimum(f1, f4)))[tv].sum())
        # H_C (t,o,c,h,l): f3>=max(f1,f2), f4<=min(f1,f2)
        vC = int(((f3 < np.maximum(f1, f2)) | (f4 > np.minimum(f1, f2)))[tv].sum())
        ntv = int(tv.sum())
        fmt["busy_file"]["ohlc_invariant_violations_tradable"] = {
            "H_A_dukascopy_t_o_c_l_h": vA,
            "H_B_ohlc_t_o_h_l_c": vB,
            "H_C_t_o_c_h_l": vC,
            "n_tradable_records": ntv,
        }
        # continuity close_k -> open_{k+1} under both close candidates
        both = tv[:-1] & tv[1:]
        gapA = np.abs(f1[1:][both] - f2[:-1][both])   # close = pos2 (Dukascopy)
        gapB = np.abs(f1[1:][both] - f4[:-1][both])   # close = pos4 (OHLC candidate)
        fmt["busy_file"]["next_open_vs_prev_close_abs"] = {
            "close_is_pos2_p50_pips": round(float(np.percentile(gapA, 50) / (sc * pip)), 4),
            "close_is_pos2_p90_pips": round(float(np.percentile(gapA, 90) / (sc * pip)), 4),
            "close_is_pos4_p50_pips": round(float(np.percentile(gapB, 50) / (sc * pip)), 4),
            "close_is_pos4_p90_pips": round(float(np.percentile(gapB, 90) / (sc * pip)), 4),
            "n": int(both.sum()),
        }

    # holiday carry file (2021-01-01, expected flat/zero-volume)
    pflat = PANELS[pair] / "BID" / "2021-01-01.bi5"
    raw, dec, arr, err = decode_bi5(pflat)
    if arr is not None:
        flat_price = arr["o"][0]
        fmt["carry_file"] = {
            "file": "2021-01-01.bi5", "records": len(arr),
            "all_ohlc_equal": bool(np.all(arr["o"] == arr["c"])
                                   and np.all(arr["l"] == arr["o"])
                                   and np.all(arr["h"] == arr["o"])),
            "all_vol_zero": bool(np.all(arr["v"] == 0)),
            "flat_price_scaled": float(flat_price / sc),
        }

    # price scale divisor derivation on the whole sample (BID tradable opens)
    tv_all = vol > 0
    tv_open = b["open"][tv_all]
    scale_report = {}
    for div in (1e3, 1e4, 1e5, 1e6):
        prices = tv_open / div
        lo, hi = BAND[pair]
        scale_report[f"divisor_{div:.0e}"] = {
            "in_band_fraction": round(float(((prices >= lo) & (prices <= hi)).mean()), 6),
            "observed_min": round(float(prices.min()), 5),
            "observed_max": round(float(prices.max()), 5),
        }
    fmt["price_scale_divisor_derivation"] = scale_report
    fmt["derived_divisor"] = sc if scale_report[f"divisor_{sc:.0e}"]["in_band_fraction"] == 1.0 else None
    fmt["pip_definition"] = pip
    fmt["pips_per_raw_point"] = 1.0 / (sc * pip)  # = 0.1 for all 3 pairs

    # volume encoding tests (BID, whole sample)
    vpos = vol[vol > 0]
    fmt["volume_encoding"] = {
        "n_minutes_total": int(len(vol)),
        "n_vol_gt0": int(tv_all.sum()),
        "integer_fraction_of_positive_volumes": round(float((vpos == np.round(vpos)).mean()), 8)
        if len(vpos) else None,
        "min_positive_volume": float(vpos.min()) if len(vpos) else None,
        "max_volume": float(vol.max()),
        "negative_volume_count": int((vol < 0).sum()),
        "as_uint32_interpretation_max_raw": None,  # filled below
    }
    pbusy2 = PANELS[pair] / "BID" / "2023-06-14.bi5"
    raw2, dec2, arr2, _ = decode_bi5(pbusy2)
    if arr2 is not None:
        m = np.frombuffer(dec2, dtype=">u4").reshape(-1, 6)
        vb = m[:, 5]
        nzv = vb[vb != 0]
        fmt["volume_encoding"]["as_uint32_interpretation_max_raw"] = int(vb.max())
        fmt["volume_encoding"]["nonzero_vol_field_raw_uint_min"] = int(nzv.min()) if len(nzv) else None
        fmt["volume_encoding"]["nonzero_vol_field_raw_uint_max"] = int(nzv.max()) if len(nzv) else None
        fmt["volume_encoding"]["float32_bits_diagnostic"] = (
            "nonzero raw uint32 values are ~1.0e9 magnitude (float32 bit patterns of small counts), "
            "NOT small integers -> volume field is float32-encoded, not a raw uint count"
            if len(nzv) and nzv.min() > 10_000_000 else "INCONCLUSIVE")

    # OHLC invariants over the whole sample (BID, tradable)
    viol_total, recs_total = 0, 0
    for ds in DECODE_SAMPLE:
        p = PANELS[pair] / "BID" / f"{iso(ds)}.bi5"
        if not p.exists():
            continue
        _, _, arr, err = decode_bi5(p)
        if arr is None:
            continue
        tv = arr["v"] > 0
        o, c, l, h = (arr[x].astype(np.int64) for x in "oclh")
        viol_total += int(((l > np.minimum(o, c)) | (h < np.maximum(o, c)) | (l > h))[tv].sum())
        recs_total += int(tv.sum())
    fmt["ohlc_h1_violations_sample_tradable"] = {
        "violations": viol_total, "tradable_records": recs_total}

    res["format"] = fmt

    # ---------- volume statistics (task c) ----------
    volb, vola = sides["BID"]["vol"], sides["ASK"]["vol"]
    wd_mask = np.concatenate([np.full(MINUTES_PER_DAY, f, dtype=bool) for f in day_flags])
    assert len(wd_mask) == len(volb), "mask/volume misalignment"
    vstats = {
        "sample_files_per_side": sides["BID"]["files_used"],
        "fraction_minutes_vol_gt0_all": round(float((volb > 0).mean()), 6),
        "fraction_minutes_vol_gt0_weekdays": round(float((volb[wd_mask] > 0).mean()), 6),
        "fraction_minutes_vol_gt0_weekend": round(float((volb[~wd_mask] > 0).mean()), 6),
        "distribution_all_minutes": pcts(volb),
        "distribution_positive_minutes": pcts(volb[volb > 0]),
        "max": float(volb.max()),
    }
    # granularity + side ratio (volume-semantics characterisation)
    vpos = volb[volb > 0]
    if len(vpos):
        vstats["fraction_positive_values_multiple_of_0_01"] = round(
            float((np.abs(vpos / 0.01 - np.round(vpos / 0.01)) < 1e-3).mean()), 6)
    vstats["total_volume_ratio_ask_bid"] = round(float(vola.sum() / volb.sum()), 4)
    # hour-of-day profile (weekday, vol>0)
    hour_idx = np.concatenate([np.arange(MINUTES_PER_DAY) // 60 for _ in day_flags])
    sel = wd_mask & (volb > 0)
    hour_mean = {}
    for hh in range(24):
        hh_mask = sel & (hour_idx == hh)
        hour_mean[f"{hh:02d}"] = round(float(volb[hh_mask].mean()), 3) if hh_mask.any() else None
    vstats["weekday_mean_volume_by_utc_hour"] = hour_mean
    core = sel & np.isin(hour_idx, [12, 13, 14, 15, 16])
    lull = sel & np.isin(hour_idx, [22, 23, 0, 1, 2, 3, 4, 5])
    vstats["london_ny_core_12_16_mean"] = round(float(volb[core].mean()), 3) if core.any() else None
    vstats["asia_lull_22_06_mean"] = round(float(volb[lull].mean()), 3) if lull.any() else None
    vstats["core_vs_lull_ratio"] = (round(vstats["london_ny_core_12_16_mean"] / vstats["asia_lull_22_06_mean"], 3)
                                    if vstats["asia_lull_22_06_mean"] else None)
    # volume vs activity: correlation with per-minute H-L range (pips)
    rngs, volsel, volsa = [], [], []
    for ds in DECODE_SAMPLE:
        if ds.weekday() >= 5:
            continue
        pb = PANELS[pair] / "BID" / f"{iso(ds)}.bi5"
        pa = PANELS[pair] / "ASK" / f"{iso(ds)}.bi5"
        if not pb.exists() or not pa.exists():
            continue
        _, _, ab, e1 = decode_bi5(pb)
        _, _, aa, e2 = decode_bi5(pa)
        if ab is None or aa is None:
            continue
        tv = ab["v"] > 0
        rng = (ab["h"].astype(np.float64) - ab["l"].astype(np.float64)) / (sc * pip)
        rngs.append(rng[tv])
        volsel.append(ab["v"].astype(np.float64)[tv])
        volsa.append(aa["v"].astype(np.float64)[tv])
    if volsel:
        rv = np.concatenate(volsel)
        rr = np.concatenate(rngs)
        ra = np.concatenate(volsa)
        vstats["pearson_corr_volume_vs_hl_range_pips"] = round(float(np.corrcoef(rv, rr)[0, 1]), 4)
        vstats["pearson_corr_bidvol_vs_askvol"] = round(float(np.corrcoef(rv, ra)[0, 1]), 4)
        vstats["mean_abs_pct_diff_bid_vs_ask_volume"] = round(
            float(np.mean(np.abs(rv - ra) / np.maximum(rv, 1))), 4)

    # weekend carry-forward check (Saturdays in sample)
    carry = []
    for ds in DECODE_SAMPLE:
        if ds.weekday() != 5:
            continue
        pb = PANELS[pair] / "BID" / f"{iso(ds)}.bi5"
        if not pb.exists():
            continue
        _, _, ab, _ = decode_bi5(pb)
        if ab is None:
            continue
        carry.append({
            "date": iso(ds),
            "distinct_open_prices": int(len(np.unique(ab["o"]))),
            "minutes_vol_gt0": int((ab["v"] > 0).sum()),
            "flat_price_scaled": float(ab["o"][0] / sc),
        })
    res["weekend_carry_saturdays"] = carry

    res["volume"] = vstats

    # Sunday reopen (task: tricky Sunday days)
    reopen = []
    for ds in TRICKY_SUNDAYS:
        i = state["row_of"].get(iso(ds))
        if i is None:
            continue
        tv = state["trad"]["BID"][i]
        nz = np.nonzero(tv)[0]
        if len(nz) == 0:
            reopen.append({"date": iso(ds), "no_tradable_minutes": True})
            continue
        fm = int(nz[0])
        sp = int(state["spread_open"][i, fm]) / (sc * pip)
        reopen.append({"date": iso(ds), "first_tradable_minute_utc": f"{fm // 60:02d}:{fm % 60:02d}",
                       "first_bar_spread_open_pips": round(sp, 2),
                       "tradable_minutes_that_sunday": int(tv.sum())})
    res["sunday_reopen_sample"] = reopen
    return res


# -------------------------------------------------- stage 5: spread checks --
def spread_checks(pair, state):
    sc, pip = SCALE[pair], PIP[pair]
    ppp = 1.0 / (sc * pip)  # raw points -> pips
    row_of = state["row_of"]

    def bar_spread(ds, minute, field="open"):
        i = row_of.get(iso(ds))
        if i is None:
            return None, None
        m = state["spread_open" if field == "open" else "spread_close"]
        tradable = state["trad"]["BID"][i, minute] and state["trad"]["ASK"][i, minute]
        return int(m[i, minute]) * ppp, bool(tradable)

    out = {}

    # (i) 20-weekday spot check at 4 time points
    spot = {}
    for label, minute in SPOT_MINUTES.items():
        vals_all, vals_trad = [], []
        for ds in SPREAD_SAMPLE:
            v, trad = bar_spread(ds, minute)
            if v is None:
                continue
            vals_all.append(v)
            if trad:
                vals_trad.append(v)
        spot[label] = {
            "n_days": len(vals_all), "n_tradable": len(vals_trad),
            "p50_pips_tradable": round(float(np.percentile(vals_trad, 50)), 2) if vals_trad else None,
            "p90_pips_tradable": round(float(np.percentile(vals_trad, 90)), 2) if vals_trad else None,
            "p50_pips_all": round(float(np.percentile(vals_all, 50)), 2) if vals_all else None,
            "p90_pips_all": round(float(np.percentile(vals_all, 90)), 2) if vals_all else None,
        }
    out["spot_check_20_weekdays"] = {"sample_dates": [iso(d) for d in SPREAD_SAMPLE],
                                     "by_time_utc": spot}

    # (ii) C1 re-measure: all Fridays 2021-01-08..2026-06-26, [20:00,20:01) bar
    vals, n_missing = [], 0
    for ds in FRIDAYS_C1:
        v, trad = bar_spread(ds, 1200)
        if v is None:
            n_missing += 1
            continue
        if trad:
            vals.append(v)
    out["c1_friday_2000_remeasure"] = {
        "window": "2021-01-08..2026-06-26", "n_fridays": len(FRIDAYS_C1),
        "n_missing_bar": n_missing, "n_tradable": len(vals),
        "p50_pips": round(float(np.percentile(vals, 50)), 3) if vals else None,
        "p90_pips": round(float(np.percentile(vals, 90)), 3) if vals else None,
        "cost_table_p50_p90": list(COST_TABLE_C1[pair]),
    }

    # (iii) C2 corroboration: roll window, per-minute CLOSE spread,
    #       minutes closing in (21:00,22:00]
    def roll_stats(days, label):
        vals = []
        for ds in days:
            i = row_of.get(iso(ds))
            if i is None:
                continue
            for minute in ROLL_WINDOW_MINUTES:
                if state["trad"]["BID"][i, minute] and state["trad"]["ASK"][i, minute]:
                    vals.append(int(state["spread_close"][i, minute]) * ppp)
        return {
            "label": label, "n_days": len(days), "n_obs": len(vals),
            "p50_pips": round(float(np.percentile(vals, 50)), 2) if vals else None,
            "p90_pips": round(float(np.percentile(vals, 90)), 2) if vals else None,
        }
    mt = [d for d in SPREAD_SAMPLE if d.weekday() < 4]
    fr = [d for d in SPREAD_SAMPLE if d.weekday() == 4]
    out["c2_roll_window_corroboration"] = {
        "mon_thu_sample": roll_stats(mt, "Mon-Thu, 20-weekday sample subset"),
        "friday_sample": roll_stats(fr, "Friday, 20-weekday sample subset"),
        "wednesday_tricky_days": roll_stats(TRICKY_ROLLWED, "5 roll-window Wednesdays"),
        "cost_table_mon_thu_p50_p90": list(COST_TABLE_C2_MONTTHU[pair]),
        "cost_table_fri_p50_p90": list(COST_TABLE_C2_FRI[pair]),
    }

    # (iii-b) C2 FULL-WINDOW re-measure over the cost-table sleeve window
    #         (minutes closing in (21:00,22:00], per-minute close spread),
    #         both with and without the tradability filter, to reconcile
    #         against the table cell (method sensitivity check).
    def roll_full(days):
        vals_trad, vals_all, n_days = [], [], 0
        trad_min_count = 0
        for ds in days:
            i = row_of.get(iso(ds))
            if i is None:
                continue
            n_days += 1
            sc = state["spread_close"][i, 1260:1320]
            tmask = state["trad"]["BID"][i, 1260:1320] & state["trad"]["ASK"][i, 1260:1320]
            trad_min_count += int(tmask.sum())
            vals_trad.extend((sc[tmask] * ppp).tolist())
            vals_all.extend((sc * ppp).tolist())
        res = {"n_days": n_days, "tradable_minutes_in_window": trad_min_count}
        for lbl, vv in (("tradable_only", vals_trad), ("all_minutes_incl_stale", vals_all)):
            res[lbl] = {"n_obs": len(vv),
                        "p50_pips": round(float(np.percentile(vv, 50)), 3) if vv else None,
                        "p90_pips": round(float(np.percentile(vv, 90)), 3) if vv else None}
        return res

    sleeve_montthu = [d for d in daterange(C1_START, C1_END) if d.weekday() < 4]
    sleeve_fri = FRIDAYS_C1
    out["c2_roll_window_full_sleeve_window"] = {
        "window": "2021-01-08..2026-06-26",
        "mon_thu": roll_full(sleeve_montthu),
        "friday": roll_full(sleeve_fri),
        "cost_table_mon_thu_p50_p90": list(COST_TABLE_C2_MONTTHU[pair]),
        "cost_table_fri_p50_p90": list(COST_TABLE_C2_FRI[pair]),
    }

    # (iii-c) C2 WINDOW-VARIANT evidence: the prior table's Mon-Thu cell does
    #         not reproduce on the declared (21:00,22:00] window; test the
    #         neighbouring 22:00-23:00 UTC hour to localise the discrepancy.
    def roll_window_slice(days, lo, hi):
        vals = []
        for ds in days:
            i = row_of.get(iso(ds))
            if i is None:
                continue
            sc = state["spread_close"][i, lo:hi]
            tmask = state["trad"]["BID"][i, lo:hi] & state["trad"]["ASK"][i, lo:hi]
            vals.extend((sc[tmask] * ppp).tolist())
        return {"n_obs": len(vals),
                "p50_pips": round(float(np.percentile(vals, 50)), 2) if vals else None,
                "p90_pips": round(float(np.percentile(vals, 90)), 2) if vals else None}

    out["c2_window_variants"] = {
        "window": "2021-01-08..2026-06-26, tradable minutes only, per-minute close spread",
        "mon_thu_2100_2200_utc": roll_window_slice(sleeve_montthu, 1260, 1320),
        "mon_thu_2200_2300_utc": roll_window_slice(sleeve_montthu, 1320, 1380),
        "friday_2100_2200_utc": roll_window_slice(sleeve_fri, 1260, 1320),
        "friday_2200_2300_utc": roll_window_slice(sleeve_fri, 1320, 1380),
        "cost_table_mon_thu_p50_p90": list(COST_TABLE_C2_MONTTHU[pair]),
        "cost_table_fri_p50_p90": list(COST_TABLE_C2_FRI[pair]),
        "interpretation": ("table Friday cell reproduces EXACTLY on 21:00-22:00 UTC; "
                           "table Mon-Thu cell is consistent with the 22:00-23:00 UTC "
                           "hour instead of its declared (21:00,22:00] window"),
    }

    # (vi) BID vs ASK tradable-mask identity (spread validity precondition)
    both = state["trad"]["BID"] & state["trad"]["ASK"]
    xor = state["trad"]["BID"] ^ state["trad"]["ASK"]
    out["bid_ask_tradable_masks"] = {
        "bid_tradable": int(state["trad"]["BID"].sum()),
        "ask_tradable": int(state["trad"]["ASK"].sum()),
        "both_tradable": int(both.sum()),
        "symmetric_difference": int(xor.sum()),
    }

    # (iv) C3 corroboration: Sunday reopen spread at first tradable bar
    # (already collected per-sample in sample_analytics; recompute here from matrices)
    rr = []
    for ds in TRICKY_SUNDAYS:
        i = row_of.get(iso(ds))
        if i is None:
            continue
        nz = np.nonzero(state["trad"]["BID"][i])[0]
        if len(nz) == 0:
            continue
        fm = int(nz[0])
        rr.append(int(state["spread_open"][i, fm]) * ppp)
    out["c3_sunday_reopen_corroboration"] = {
        "n_sundays": len(rr), "values_pips": [round(x, 2) for x in rr],
        "median_pips": round(float(np.median(rr)), 2) if rr else None,
        "cost_table_p50_p90": list(COST_TABLE_C3[pair]),
        "note": "small-n corroboration only (4 sample Sundays); table cell used n=283/284",
    }

    # (v) negative spreads inside the spot sample (sanity)
    neg = 0
    for ds in SPREAD_SAMPLE:
        i = row_of.get(iso(ds))
        if i is None:
            continue
        neg += int((state["spread_open"][i] < 0).sum())
    out["negative_spread_open_minutes_in_20day_sample"] = neg
    return out


# --------------------------------------------------- stage 6: provenance ----
def provenance_checks(pairs_state):
    out = {"prior_manifest_path": str(PRIOR_MANIFEST),
           "prior_manifest_found": PRIOR_MANIFEST.exists(),
           "note": ("data_manifest_fx.json was NOT found under the fx-rangefade or "
                    "fx-majors control dirs (searched); the only copy is in the "
                    "portfolio-router-12assets-100k-v1 worktree (prior cycle I1a lane)")}
    if not PRIOR_MANIFEST.exists():
        return out
    pm = json.loads(PRIOR_MANIFEST.read_text())
    out["prior_manifest_schema"] = pm.get("schema")
    out["prior_manifest_measured_at"] = pm.get("measured_at")

    def norm_ts(x):
        return x.replace("+00:00", "Z") if isinstance(x, str) else x

    cmp = {}
    for pair, state in pairs_state.items():
        pmm = pm["panels"].get(pair, {})
        pair_dir = PANELS[pair].parent  # .../data_local/<PAIR>
        row = {"side_files_agree": {}, "total_bytes_agree": {},
               "corpus_digest_agree": {}, "coverage_agree": None}
        for side in ("BID", "ASK"):
            mine = state["side_stats"][side]
            theirs = pmm.get("side_files", {}).get(side)
            row["side_files_agree"][side] = (theirs == mine["files"])
            tbytes = pmm.get("total_bytes_by_side", {}).get(side)
            row["total_bytes_agree"][side] = (tbytes == mine["total_bytes"])
            td = pmm.get("corpus_digest", {}).get(side)
            row["corpus_digest_agree"][side] = {
                "no_trailing_nl": td == mine["corpus_digest_prior_method_no_trailing_nl"],
                "trailing_nl": td == mine["corpus_digest_prior_method_trailing_nl"],
            }
        # tradable minutes (prior manifest reports one number; compare BID)
        row["tradable_minutes_bid_agree"] = (
            pmm.get("gaps", {}).get("tradable_minutes") == state["census"]["BID"]["tradable_minutes"])
        row["zero_tradable_weekdays_agree_bid"] = (
            pmm.get("gaps", {}).get("zero_tradable_weekdays") == state["census"]["BID"]["zero_tradable_weekdays"])
        row["prior_file_name_range"] = pmm.get("file_name_range")
        row["prior_first_ts"] = pmm.get("first_ts_measured")
        row["prior_last_ts"] = pmm.get("last_ts_measured")
        row["my_first_ts_bid"] = state["census"]["BID"]["first_tradable_ts"]
        row["my_last_ts_bid"] = state["census"]["BID"]["last_tradable_ts"]
        row["first_ts_agree"] = (norm_ts(pmm.get("first_ts_measured"))
                                 == state["census"]["BID"]["first_tradable_ts"])
        row["last_ts_agree"] = (norm_ts(pmm.get("last_ts_measured"))
                                == state["census"]["BID"]["last_tradable_ts"])
        # largest tradable run (prior value, for divergence reporting)
        row["prior_largest_tradable_run"] = pmm.get("gaps", {}).get("largest_tradable_minute_run")
        row["prior_largest_run_on"] = pmm.get("gaps", {}).get("largest_tradable_minute_run_on")
        row["my_largest_tradable_run_bid"] = state["census"]["BID"]["largest_tradable_run"]
        row["largest_run_agree"] = (
            pmm.get("gaps", {}).get("largest_tradable_minute_run")
            == state["census"]["BID"]["largest_tradable_run"]["minutes"])

        # staged per-file manifest m1_manifest.json (fxm.m1_manifest@1)
        m1m_path = pair_dir / "m1_manifest.json"
        m1m_found = m1m_path.exists()
        row["m1_manifest_path"] = str(m1m_path)
        row["m1_manifest_found"] = m1m_found
        if m1m_found:
            m1m = json.loads(m1m_path.read_text())
            files = m1m.get("files", {})
            match_hash, match_bytes, mismatch, missing_in_manifest = 0, 0, [], []
            for side in ("BID", "ASK"):
                for ds, v in state["per_file"][side].items():
                    if "sha256" not in v:
                        continue
                    key = f"M1/{side}/{ds}.bi5"
                    if key not in files:
                        missing_in_manifest.append(key)
                        continue
                    if files[key]["sha256"] == v["sha256"]:
                        match_hash += 1
                    else:
                        mismatch.append(key)
                    if files[key]["bytes"] == v["bytes"]:
                        match_bytes += 1
                    else:
                        mismatch.append(key + " (bytes)")
            row["m1_manifest_files"] = len(files)
            row["m1_per_file_sha256_matches"] = match_hash
            row["m1_per_file_mismatches"] = mismatch[:10]
            row["m1_per_file_mismatch_count"] = len(mismatch)
            row["m1_missing_in_manifest_count"] = len(missing_in_manifest)
            row["m1_manifest_sha256"] = hashlib.sha256(m1m_path.read_bytes()).hexdigest()
        cmp[pair] = row
    out["per_pair"] = cmp

    # index manifest hashes listed by prior manifest
    idx = {}
    for pair, state in pairs_state.items():
        pmm = pm["panels"].get(pair, {})
        pair_dir = PANELS[pair].parent
        for rel, claimed in pmm.get("index_manifests_sha256", {}).items():
            candidates = [pair_dir / rel, pair_dir / Path(rel).name,
                          pair_dir / "derived" / Path(rel).name]
            f = next((c for c in candidates if c.exists()), None)
            if f is not None:
                actual = hashlib.sha256(f.read_bytes()).hexdigest()
                idx[f"{pair}:{rel}"] = {"found": True, "path": str(f),
                                        "agree": actual == claimed,
                                        "actual": actual, "claimed": claimed}
            else:
                idx[f"{pair}:{rel}"] = {"found": False,
                                        "paths_tried": [str(c) for c in candidates]}
    out["index_manifest_hashes"] = idx
    return out


# ------------------------------------------------------------------- main --
def main():
    t0 = time.time()
    log(f"PC12A Lane D data audit — sample={len(DECODE_SAMPLE)} days, "
        f"spread sample={len(SPREAD_SAMPLE)} weekdays, C1 Fridays={len(FRIDAYS_C1)}")
    summary = {
        "schema": "pc12a_poolB_data_audit@1",
        "generated": date.today().isoformat(),
        "script": "audit_scripts.py",
        "python": sys.version.split()[0],
        "panels": {}, "format_and_volume": {}, "spread": {}, "provenance": {},
        "digests": {},
    }

    states = {}
    for pair in PANELS:
        log(f"=== {pair}: inventory + hash + decode pass ===")
        states[pair] = audit_pair(pair)
        write_hash_jsonl(pair, states[pair])

    # overall digest across all 6 sides
    all_lines = []
    for pair, state in states.items():
        for side in ("BID", "ASK"):
            for k, v in sorted(state["per_file"][side].items()):
                if "sha256" in v:
                    all_lines.append(f"{pair}:{side}:{k}|{v['bytes']}|{v['sha256']}")
    summary["digests"] = {
        "method": "sha256 of '\\n'.join(sorted '<PAIR>:<SIDE>:<date>|<bytes>|<sha256>' lines)",
        "per_pair_aggregate": {p: states[p]["pair_aggregate_digest"] for p in states},
        "per_side_aggregate": {p: {s: states[p]["side_stats"][s]["aggregate_digest_sha256"]
                                   for s in ("BID", "ASK")} for p in states},
        "overall_aggregate": hashlib.sha256("\n".join(sorted(all_lines)).encode()).hexdigest(),
        "total_files_hashed": len(all_lines),
        "total_bytes_hashed": sum(v["bytes"] for s in states.values()
                                  for side in s["per_file"].values() for v in side.values()
                                  if "bytes" in v),
    }

    for pair, state in states.items():
        log(f"=== {pair}: sample analytics (format + volume) ===")
        summary["panels"][pair] = {
            "path": state["path"],
            "inventory": state["inventory"],
            "sides": {s: {k: state["side_stats"][s][k] for k in
                          ("files", "total_bytes", "zero_byte_files", "undecodable_files",
                           "nrec_histogram", "min_date", "max_date")} for s in ("BID", "ASK")},
            "census": state["census"],
            "spread_matrix": state["spread_matrix"],
            "anomalies": state["anomalies"][:20],
            "anomaly_count": len(state["anomalies"]),
        }
        summary["format_and_volume"][pair] = sample_analytics(pair, state)
        log(f"=== {pair}: spread checks ===")
        summary["spread"][pair] = spread_checks(pair, state)

    log("=== provenance cross-check ===")
    summary["provenance"] = provenance_checks(states)

    # strip non-serializable numpy state before writing
    with (OUT / "audit_summary.json").open("w") as f:
        json.dump(summary, f, indent=1, default=str)

    # console digest of headline numbers
    log("---- HEADLINES ----")
    for pair in PANELS:
        inv = summary["panels"][pair]["inventory"]
        cen = summary["panels"][pair]["census"]["BID"]
        vol = summary["format_and_volume"][pair]["volume"]
        c1 = summary["spread"][pair]["c1_friday_2000_remeasure"]
        print(f"\n{pair}: files/side={inv['files_per_side']} span={inv['span_calendar_days']}d "
              f"missingWD={len(inv['missing_weekday_files'])} missingWE={len(inv['missing_weekend_files'])} "
              f"anomalies={summary['panels'][pair]['anomaly_count']}")
        print(f"  census BID: tradable={cen['tradable_minutes']} first={cen['first_tradable_ts']} "
              f"last={cen['last_tradable_ts']} zeroWD={cen['zero_tradable_weekdays']}")
        print(f"  vol: frac>0 all={vol['fraction_minutes_vol_gt0_all']} wd={vol['fraction_minutes_vol_gt0_weekdays']} "
              f"pos-dist={vol['distribution_positive_minutes']} core/lull={vol['core_vs_lull_ratio']} "
              f"integ={summary['format_and_volume'][pair]['format']['volume_encoding']['integer_fraction_of_positive_volumes']}")
        print(f"  C1 Fri20:00 p50/p90={c1['p50_pips']}/{c1['p90_pips']} n={c1['n_tradable']}/{c1['n_fridays']} "
              f"table={c1['cost_table_p50_p90']}")
        print(f"  spot20d: " + "; ".join(
            f"{k}={v['p50_pips_tradable']}/{v['p90_pips_tradable']}(n={v['n_tradable']})"
            for k, v in summary["spread"][pair]["spot_check_20_weekdays"]["by_time_utc"].items()))
    log(f"TOTAL elapsed {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
