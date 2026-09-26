"""15m/H1 bar build + hardened cost-authority census — ERP1-TRACKA-COHORT-1.

PORT LINEAGE: ported from EURUSD-RANGEEXP-SCORED-V1/scripts/build_bars.py
(fx-rangefade-2m-shadow-v1 worktree) and PARAMETRIZED per pair — the
ancestor's PIP=1e-4, PRICE_SCALE=1e5 (`o / 1e5`) and the EURUSD band
0.80<bid<1.35 are gone; pip/scale/band come from the probe-proven
PairConfig (plan §5.2 BLOCKING PORT DEFECT fix). Schema hardened per
plan §6 (datacost critic requirements, binding):

  - per-session buckets with per-bucket COUNTS persisted; a low-sample
    bucket becomes explicit null quantiles + LOW_SAMPLE_BUCKET flag —
    never silently dropped;
  - CLOSE-spread quantiles persisted alongside OPEN-spread, both in PIPS;
  - census-vs-executor reconcile: per-bar spread medians re-derived from
    the PERSISTED bars15 parquet, bucketed per session, must equal the
    census p50 within rounding (gate);
  - H1 bars: s_open = a_o - b_o, s_close = a_c - b_c (v2_lib semantics);
  - gap census: missing 15m slots enumerated (micro-gaps), day gaps,
    Friday->Sunday boundaries measured, DST-shift Sunday-open hours
    visible in a table;
  - every gate reported with margin-to-fail; duplicates = 0 fail-closed.

Conventions (ancestor, probe-proven): minute ts = day 00:00 UTC + sec;
minute TRADABLE iff vol>0 AND band_lo<bid.open<band_hi AND ask>=bid;
15m bar VALID iff all 15 minutes tradable (no interpolation anywhere);
H1 bar VALID iff exactly its four 15m bars are VALID and consecutive.

LINEAGE-NOTE-1 (deviation, documented): the ancestor built 15m
high/low from the CLOSE column (bb[:,2].max()/bb[:,3].min() under its
decode order open,close,low,high) — this port uses the true high/low
columns, which the layout fix makes available honestly.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

LANE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(LANE / "scripts"))
sys.path.insert(0, "/Users/hoangminhlong/my-quantitative/research")

from pair_config import load_pair_config  # noqa: E402

RAW = LANE / "data_local" / "duka" / "M1"
DERIVED = LANE / "data_local" / "derived"
CANDLE_DTYPE = np.dtype([("sec", ">i4"), ("o", ">i4"), ("c", ">i4"),
                         ("l", ">i4"), ("h", ">i4"), ("v", ">f4")])
assert CANDLE_DTYPE.itemsize == 24

SESSION_BUCKETS = (
    "asia_00_07", "london_07_12", "ny_overlap_12_16", "ny_late_16_21",
    "rollover_21_22", "late_22_24", "friday_20_23_open", "sunday_open_21_22",
)
MIN_BUCKET_N = 100
QUANTILE_POINTS = (50, 75, 90, 95, 99)


def session_bucket(hour: np.ndarray, dow: np.ndarray):
    """Fixed-UTC bucket per 15m bar-open; special Friday/Sunday cells are
    standalone (they overlap the regular buckets BY DESIGN and are
    reported separately). Returns dict bucket -> bool mask. Pure function
    so synthetic-DST fixture tests can drive it."""
    m = {}
    m["asia_00_07"] = (hour >= 0) & (hour < 7)
    m["london_07_12"] = (hour >= 7) & (hour < 12)
    m["ny_overlap_12_16"] = (hour >= 12) & (hour < 16)
    m["ny_late_16_21"] = (hour >= 16) & (hour < 21)
    m["rollover_21_22"] = hour == 21
    m["late_22_24"] = hour >= 22
    m["friday_20_23_open"] = (dow == 4) & (hour >= 20) & (hour < 23)
    m["sunday_open_21_22"] = (dow == 6) & (hour == 21)
    return m


def q3(a) -> dict:
    a = np.asarray(a, dtype=float)
    return {str(p): round(float(np.quantile(a, p / 100)), 3) for p in QUANTILE_POINTS}


def bucket_entry(vals_open_pips, vals_close_pips):
    n = int(len(vals_open_pips))
    if n < MIN_BUCKET_N:
        return {"n": n, "open": None, "close": None, "flag": "LOW_SAMPLE_BUCKET"}
    return {"n": n, "open": q3(vals_open_pips), "close": q3(vals_close_pips)}


def dst_transition_sundays(year: int):
    """EU + US DST transition Sundays for a year (fixed rules)."""
    def sundays(y, month):
        d = dt.date(y, month, 1)
        out = []
        while d.month == month:
            if d.weekday() == 6:
                out.append(d)
            d += dt.timedelta(days=1)
        return out
    mar, oct_, nov = sundays(year, 3), sundays(year, 10), sundays(year, 11)
    return [
        (mar[-1], "EU_spring"), (oct_[-1], "EU_fall"),
        (mar[1], "US_spring"), (nov[0], "US_fall"),
    ]


def load_day(side: str, name: str, cfg, man):
    """Verify sha from manifest, decode 24B records -> structured array.

    The 24-byte layout invariant is asserted on the DECOMPRESSED length
    (the 20B tick / 24B candle container trap: see duka_lib docstring).
    """
    import lzma

    path = RAW / side / cfg.symbol / name
    raw = path.read_bytes()
    entry = man["files"].get(f"{cfg.symbol}/{side}/{name}")
    if entry is None or entry.get("sha256") != hashlib.sha256(raw).hexdigest():
        raise SystemExit(f"FAIL_CLOSED manifest mismatch: {cfg.symbol}/{side}/{name}")
    plain = lzma.decompress(raw)
    if len(plain) % CANDLE_DTYPE.itemsize:
        raise SystemExit(
            f"FAIL_CLOSED {cfg.symbol}/{side}/{name}: decompressed len "
            f"{len(plain)} not multiple of {CANDLE_DTYPE.itemsize}"
        )
    return np.frombuffer(plain, dtype=CANDLE_DTYPE)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    args = ap.parse_args()

    # Machine-wide heavy lock: the census scans every downloaded byte and
    # writes the derived planes — a bounded heavy job like the download.
    from governance import heavy_lock

    man_path0 = LANE / "data_local" / "duka" / f"m1_manifest_{args.symbol}.json"
    lock = None
    status, note = "FAILED", ""
    try:
        try:
            lock = heavy_lock.acquire(
                cycle_id="ERP1-TRACKA-COHORT-1",
                role="datagate-census",
                worktree=str(LANE),
                command=[sys.executable, str(Path(__file__).resolve()), args.symbol],
                expected_artifacts=[str(DERIVED / f"census_{args.symbol}.json")],
            )
        except heavy_lock.LockBusyError as e:
            print(json.dumps({"verdict": "NOT_RUN_RESOURCE_CONFLICT", "reason": str(e)}))
            return 4
        rc = _census(args.symbol, man_path0, lock)
        status = "FINISHED" if rc == 0 else "FAILED"
        note = "" if rc == 0 else f"census exit {rc} (see census_{args.symbol}.json)"
        return rc
    except Exception as e:  # noqa: BLE001
        status, note = "FAILED", f"{type(e).__name__}: {e}"[:400]
        raise
    finally:
        if lock is not None:
            lock.release(status=status, note=note)


def _census(symbol: str, man_path: Path, lock) -> int:
    cfg = load_pair_config(symbol)

    man = json.loads(man_path.read_text())

    bid_files = sorted(f.name for f in (RAW / "BID" / cfg.symbol).glob("*.bi5"))
    ask_files = sorted(f.name for f in (RAW / "ASK" / cfg.symbol).glob("*.bi5"))
    if bid_files != ask_files:
        raise SystemExit("FAIL_CLOSED BID/ASK day file sets differ")

    pip = cfg.pip
    rows = []
    census = {
        "schema": "tracka_census@2",
        "symbol": cfg.symbol,
        "pair_config": {
            "pip": pip, "price_scale": cfg.price_scale,
            "band_lo": cfg.band_lo, "band_hi": cfg.band_hi,
            "provenance": cfg.derivation,
        },
        "days": 0,
        "days_missing_both": sorted(
            d for d in man.get("days_missing", [])
        ),
        "days_short_records": {},
        "days_zero_tradable": {"count": 0, "weekend": 0, "weekday": 0,
                               "weekday_dates": []},
        "min_tradable_by_dow": [0] * 7,
        "min_total_by_dow": [0] * 7,
        "nonpos_spread_minutes": 0,
        "price_range_violations": 0,
        "first_ts": None, "last_ts": None,
    }

    for name in bid_files:
        y, m, d = map(int, name[:-4].split("-"))
        day0 = dt.datetime(y, m, d, tzinfo=dt.timezone.utc)
        b = load_day("BID", name, cfg, man)
        a = load_day("ASK", name, cfg, man)
        census["days"] += 1
        if len(b) != 1440 or len(a) != 1440:
            census["days_short_records"][name] = [len(b), len(a)]
        n = min(len(b), len(a))
        # structured dtype: convert fields individually (no whole-record cast)
        bb, aa = b[:n], a[:n]
        sc = cfg.price_scale
        secs = bb["sec"]
        bo = bb["o"].astype(np.float64) / sc
        ao = aa["o"].astype(np.float64) / sc
        tradable = (
            (bb["v"].astype(np.float64) > 0)
            & (bo > cfg.band_lo) & (bo < cfg.band_hi) & (ao >= bo)
        )
        census["nonpos_spread_minutes"] += int(np.sum(ao < bo))
        census["price_range_violations"] += int(
            np.sum(~((bo > cfg.band_lo) & (bo < cfg.band_hi)))
        )
        dow = day0.weekday()
        census["min_tradable_by_dow"][dow] += int(tradable.sum())
        census["min_total_by_dow"][dow] += n
        if tradable.any():
            ts_first = day0 + dt.timedelta(seconds=int(secs[int(np.argmax(tradable))]))
            census["first_ts"] = census["first_ts"] or ts_first.isoformat()
            census["last_ts"] = (
                day0 + dt.timedelta(seconds=int(secs[n - 1]))
            ).isoformat()
        elif dow >= 5:
            census["days_zero_tradable"]["weekend"] += 1
        else:
            census["days_zero_tradable"]["weekday"] += 1
            census["days_zero_tradable"]["weekday_dates"].append(name[:-4])
        bc, ac = bb["c"].astype(np.float64) / sc, aa["c"].astype(np.float64) / sc
        bl, al = bb["l"].astype(np.float64) / sc, aa["l"].astype(np.float64) / sc
        bh, ah = bb["h"].astype(np.float64) / sc, aa["h"].astype(np.float64) / sc
        for k in range(0, n - 14, 15):  # 15m buckets aligned :00 :15 :30 :45
            sl = slice(k, k + 15)
            if not tradable[sl].all() or not np.all(np.diff(secs[sl]) == 60):
                continue
            rows.append(
                (
                    int(day0.timestamp()) + int(secs[k]),
                    bo[k], bh[sl].max(), bl[sl].min(), bc[sl][-1],
                    ao[k], ah[sl].max(), al[sl].min(), ac[sl][-1],
                    ao[k] - bo[k], ac[sl][-1] - bc[sl][-1],
                )
            )
        if census["days"] % 200 == 0:
            print(f"... {cfg.symbol} {census['days']} days", file=sys.stderr)
            lock.heartbeat(extra={"symbol": cfg.symbol, "days": census["days"]})

    cols = ["ts", "b_o", "b_h", "b_l", "b_c", "a_o", "a_h", "a_l", "a_c",
            "s_open", "s_close"]
    df = pd.DataFrame(rows, columns=cols).sort_values("ts").reset_index(drop=True)
    dup = int(df["ts"].duplicated().sum())
    if dup:
        census["gates"] = {"duplicate_15m_ts_eq_0": False}
        census["gate_margins"] = {"duplicate_15m_ts_eq_0": -dup}
        census["verdict"] = "BUILD_FAIL"
        (DERIVED / f"census_{cfg.symbol}.json").write_text(
            json.dumps(census, indent=1, default=str))
        print(f"FAIL_CLOSED duplicate 15m timestamps: {dup}")
        return 2
    df["ts"] = pd.to_datetime(df["ts"], unit="s", utc=True)

    DERIVED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(DERIVED / f"bars15_{cfg.symbol}.parquet", index=False)

    # ---- H1 plane: valid iff exactly its four 15m bars, consecutive ----
    h1_rows = []
    ts_s = (
        df["ts"].dt.tz_convert("UTC").dt.tz_localize(None)
        .to_numpy().astype("datetime64[s]").astype("int64")
    )
    in_hour = ts_s // 3600
    start = 0
    for i in range(1, len(df) + 1):
        if i == len(df) or in_hour[i] != in_hour[start]:
            grp = slice(start, i)
            if i - start == 4 and all(np.diff(ts_s[grp]) == 900):
                f, l = grp.start, grp.stop - 1
                h1_rows.append((
                    int(in_hour[start] * 3600),
                    df["b_o"].iloc[f], df["b_h"].iloc[grp].max(),
                    df["b_l"].iloc[grp].min(), df["b_c"].iloc[l],
                    df["a_o"].iloc[f], df["a_c"].iloc[l],
                    df["a_o"].iloc[f] - df["b_o"].iloc[f],
                    df["a_c"].iloc[l] - df["b_c"].iloc[l],
                ))
            start = i
    h1 = pd.DataFrame(h1_rows, columns=[
        "ts", "b_o", "b_h", "b_l", "b_c", "a_o", "a_c", "s_open", "s_close",
    ])
    h1["ts"] = pd.to_datetime(h1["ts"], unit="s", utc=True)
    h1.to_parquet(DERIVED / f"bars1h_{cfg.symbol}.parquet", index=False)

    # ---- hardened spread census (pips) ----
    s_open = df["s_open"].to_numpy() / pip
    s_close = df["s_close"].to_numpy() / pip
    hour = df["ts"].dt.hour.to_numpy()
    dow = df["ts"].dt.dayofweek.to_numpy()
    masks = session_bucket(hour, dow)

    by_session = {k: bucket_entry(s_open[mk], s_close[mk]) for k, mk in masks.items()}
    low_sample = sorted(k for k, v in by_session.items() if v.get("flag"))
    census["spread_pips"] = {
        "overall_open": q3(s_open),
        "overall_close": q3(s_close),
        "by_session": by_session,
        # ancestor-compatible convenience views (quantiles only, n>=MIN_BUCKET_N)
        "by_session_open": {
            k: v["open"] for k, v in by_session.items() if v["open"] is not None
        },
        "friday_20_23_open": by_session["friday_20_23_open"]["open"],
        "sunday_open_21_22": by_session["sunday_open_21_22"]["open"],
    }
    census["low_sample_buckets"] = low_sample

    # ---- gap census ----
    gaps = gap_census(df, ts_s, hour)
    census["gap_census"] = gaps

    # ---- share gates ----
    expected_midweek = census["min_tradable_by_dow"][0] + census["min_tradable_by_dow"][2]
    total_midweek = census["min_total_by_dow"][0] + census["min_total_by_dow"][2]
    share = expected_midweek / max(total_midweek, 1)
    census["midweek_tradable_share"] = round(share, 5)
    census["days_short_records_n"] = len(census["days_short_records"])
    census["bars15_valid"] = int(len(df))
    census["bars1h_valid"] = int(len(h1))

    nonpos_share = census["nonpos_spread_minutes"] / max(len(df) * 15, 1)

    # ---- census-vs-executor reconcile from the PERSISTED parquet ----
    rb = pd.read_parquet(DERIVED / f"bars15_{cfg.symbol}.parquet")
    r_open = (rb["s_open"].to_numpy() / pip)
    r_hour = pd.to_datetime(rb["ts"], utc=True).dt.hour.to_numpy()
    r_dow = pd.to_datetime(rb["ts"], utc=True).dt.dayofweek.to_numpy()
    r_masks = session_bucket(r_hour, r_dow)
    max_diff, per_bucket = 0.0, {}
    for k in SESSION_BUCKETS:
        mk = r_masks[k]
        if mk.sum() < MIN_BUCKET_N:
            per_bucket[k] = None
            continue
        med = round(float(np.median(r_open[mk])), 3)
        per_bucket[k] = med
        census_med = by_session[k]["open"][ "50"]
        max_diff = max(max_diff, abs(med - census_med))
    tol = 5e-4  # census p50s rounded to 3 decimals
    reconcile_pass = max_diff <= tol
    census["reconcile"] = {
        "method": ("per-bar s_open/pip medians recomputed from persisted "
                   "bars15 parquet, bucketed per session, vs census p50"),
        "max_abs_diff_pips": round(max_diff, 6),
        "tolerance": tol,
        "pass": reconcile_pass,
        "per_bucket_median_open_p50": per_bucket,
    }

    # ---- gates with margins ----
    gates = {
        "midweek_tradable_share_gt_0.90": share > 0.90,
        "nonpos_spread_share_lt_1pct": nonpos_share < 0.01,
        "bars15_gt_100k": len(df) > 100_000,
        "duplicate_15m_ts_eq_0": dup == 0,
        "reconcile_p50_within_rounding": reconcile_pass,
    }
    census["gates"] = gates
    census["gate_margins"] = {
        "midweek_tradable_share_gt_0.90": round(share - 0.90, 6),
        "nonpos_spread_share_lt_1pct": round(0.01 - nonpos_share, 6),
        "bars15_gt_100k": int(len(df) - 100_000),
        "duplicate_15m_ts_eq_0": int(-dup),
        "reconcile_p50_within_rounding": round(tol - max_diff, 6),
    }
    census["nonpos_spread_share"] = round(nonpos_share, 8)

    # DST/rollover fixture assertions (build-failing, plan §6)
    assert by_session["rollover_21_22"]["n"] > 0, \
        "FAIL_CLOSED rollover bucket empty"
    assert by_session["sunday_open_21_22"]["n"] > 0, \
        "FAIL_CLOSED Sunday-open cell absent"
    census["fixture_asserts"] = {
        "rollover_bucket_count_gt_0": True,
        "sunday_open_cell_present": True,
        "synthetic_dst_calendar_tests": "tests/test_engine.py::test_*",
    }

    census["data_manifest"] = {
        "bars15_rows": int(len(df)),
        "bars1h_rows": int(len(h1)),
        "m1_manifest_sha256": hashlib.sha256(man_path.read_bytes()).hexdigest(),
        "m1_manifest_path": str(man_path.relative_to(LANE)),
        "day_files": len(bid_files),
    }
    census["verdict"] = "BUILD_PASS" if all(gates.values()) else "BUILD_FAIL"

    out = DERIVED / f"census_{cfg.symbol}.json"
    out.write_text(json.dumps(census, indent=1, default=str))
    print(json.dumps({
        "symbol": cfg.symbol,
        "verdict": census["verdict"],
        "gates": gates,
        "gate_margins": census["gate_margins"],
        "bars15_valid": census["bars15_valid"],
        "bars1h_valid": census["bars1h_valid"],
        "midweek_tradable_share": census["midweek_tradable_share"],
        "nonpos_spread_minutes": census["nonpos_spread_minutes"],
        "price_range_violations": census["price_range_violations"],
        "overall_open_p50_pips": census["spread_pips"]["overall_open"]["50"],
        "rollover_n": by_session["rollover_21_22"]["n"],
        "sunday_open_n": by_session["sunday_open_21_22"]["n"],
    }, indent=1))
    return 0 if census["verdict"] == "BUILD_PASS" else 2


def gap_census(df, ts_s, hour) -> dict:
    """Micro-gaps (missing 15m slots inside a day), day gaps, weekend
    boundaries, DST-shift visibility."""
    out = {"micro_gaps": {}, "day_boundaries": {}, "weekend_boundaries": {},
           "dst_shift_table": []}

    # missing expected slots INSIDE each day's traded span (interior
    # micro-gaps). Slots outside the day's first..last bar are market
    # closure, not gaps — closure shape is exposed via span statistics.
    day_of = ts_s // 86400
    uniq_days, first_idx = np.unique(day_of, return_index=True)
    miss_entries, miss_by_hour = [], {h: 0 for h in range(24)}
    span_by_dow = []  # (dow, first_slot, last_slot)
    for d, fi in zip(uniq_days, first_idx):
        li = fi
        while li + 1 < len(day_of) and day_of[li + 1] == d:
            li += 1
        day_ts = ts_s[fi:li + 1]
        slots = ((day_ts - d * 86400) // 900)
        have = set(slots.tolist())
        dow_d = dt.datetime.fromtimestamp(
            int(d) * 86400, tz=dt.timezone.utc).weekday()
        span_by_dow.append((dow_d, int(slots[0]), int(slots[-1])))
        for slot in range(int(slots[0]) + 1, int(slots[-1])):
            if slot not in have:
                miss_by_hour[slot // 4] += 1
                if len(miss_entries) < 500:
                    t = dt.datetime.fromtimestamp(
                        d * 86400 + slot * 900, tz=dt.timezone.utc)
                    miss_entries.append({"ts": t.isoformat(), "hour": slot // 4})
    wd = [s for s in span_by_dow if s[0] < 5]
    out["micro_gaps"] = {
        "definition": "expected 15m slot absent between a day's first and "
                      "last valid bar (interior hole; >=1 non-tradable "
                      "minute inside the slot). Market-closed slots outside "
                      "a day's span are reported by span stats, not as gaps",
        "count": sum(miss_by_hour.values()),
        "by_hour_of_day": miss_by_hour,
        "entries_capped_500": miss_entries,
        "day_span_slots": {
            "first_slot_p50_weekday": float(np.median([s[1] for s in wd])) if wd else None,
            "last_slot_p50_weekday": float(np.median([s[2] for s in wd])) if wd else None,
            "note": "slot = minute-of-day // 15 over the 96-slot UTC grid",
        },
    }

    # day-to-day boundaries (within contiguous valid days)
    b_entries = []
    for i in range(1, len(ts_s)):
        g = ts_s[i] - ts_s[i - 1]
        if g > 900:
            b_entries.append({
                "from_ts": dt.datetime.fromtimestamp(
                    int(ts_s[i - 1]), tz=dt.timezone.utc).isoformat(),
                "to_ts": dt.datetime.fromtimestamp(
                    int(ts_s[i]), tz=dt.timezone.utc).isoformat(),
                "gap_minutes": int(g // 60),
            })
    out["day_boundaries"] = {
        "count_gt_15m": len(b_entries),
        "gap_minutes_p50": float(np.median([e["gap_minutes"] for e in b_entries])) if b_entries else 0,
        "gap_minutes_max": max((e["gap_minutes"] for e in b_entries), default=0),
        "entries_capped_500": b_entries[:500],
    }

    # Friday close -> next open (weekend boundaries)
    dow = pd.to_datetime(df["ts"], utc=True).dt.dayofweek.to_numpy()
    wk_entries = []
    for i in range(1, len(ts_s)):
        if dow[i - 1] == 4 and dow[i] in (6, 0):
            wk_entries.append({
                "friday_close_ts": dt.datetime.fromtimestamp(
                    int(ts_s[i - 1]), tz=dt.timezone.utc).isoformat(),
                "next_open_ts": dt.datetime.fromtimestamp(
                    int(ts_s[i]), tz=dt.timezone.utc).isoformat(),
                "gap_hours": round((ts_s[i] - ts_s[i - 1]) / 3600, 3),
                "next_open_dow": int(dow[i]),
            })
    ghrs = [e["gap_hours"] for e in wk_entries]
    out["weekend_boundaries"] = {
        "count": len(wk_entries),
        "gap_hours_p50": float(np.median(ghrs)) if ghrs else None,
        "gap_hours_min": min(ghrs) if ghrs else None,
        "gap_hours_max": max(ghrs) if ghrs else None,
        "entries_capped_80": wk_entries[:80],
    }

    # DST-shift visibility: first bar of each transition Sunday (+neighbors)
    years = sorted(pd.to_datetime(df['ts'], utc=True).dt.year.unique().tolist())
    sundays_needed = {}
    for y in years:
        for d, region in dst_transition_sundays(int(y)):
            sundays_needed[d.isoformat()] = region
    seen_sunday_first = {}
    for i in range(len(ts_s)):
        if dow[i] == 6:
            key = dt.datetime.fromtimestamp(int(ts_s[i]), tz=dt.timezone.utc)\
                .date().isoformat()
            if key not in seen_sunday_first:
                seen_sunday_first[key] = int(hour[i])
    for ds, region in sorted(sundays_needed.items()):
        out["dst_shift_table"].append({
            "date": ds, "transition": region,
            "observed_first_sunday_bar_utc_hour": seen_sunday_first.get(ds),
            "in_panel": ds in seen_sunday_first,
        })
    return out


if __name__ == "__main__":
    sys.exit(main())
