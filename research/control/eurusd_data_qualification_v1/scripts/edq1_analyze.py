#!/usr/bin/env python
"""EDQ1 P1 probe analysis — coverage census, timestamp proofs, indicative
reconciliation. Emits coverage_census.json + indicative_reconciliation.json
under probe/. No interpolation; no convention assumed — every convention is
measured from the decoded bytes and cross-source alignment.
"""
import datetime as dt
import json
import lzma
import math
import os
import statistics
import struct

WORKTREE = "/Users/hoangminhlong/my-quantitative/.worktrees/eurusd-data-qualification-v1/integration"
CYCLE = os.path.join(WORKTREE, "research/control/eurusd_data_qualification_v1")
RAW_DIR = os.path.join(CYCLE, "data_local/dukascopy")
TD_DIR = os.path.join(CYCLE, "data_local/twelvedata")
PROBE_DIR = os.path.join(CYCLE, "probe")

POINT = 1e5      # verified price scale (int/1e5)
PIP = 1e-4       # EURUSD pip
WINDOW_START = dt.datetime(2024, 3, 4, tzinfo=dt.timezone.utc)
WINDOW_END = dt.datetime(2024, 3, 14, tzinfo=dt.timezone.utc)


def hour_files():
    """(hour_dt_utc, path) for the 240 window files, ordered."""
    out = []
    cur = WINDOW_START
    while cur < WINDOW_END:
        p = os.path.join(RAW_DIR, "2024", cur.strftime("%Y%m%d_%H") + "h_ticks.bi5")
        out.append((cur, p))
        cur += dt.timedelta(hours=1)
    return out


def decode(path):
    raw = open(path, "rb").read()
    if not raw:
        return []
    out = lzma.LZMADecompressor(format=lzma.FORMAT_AUTO).decompress(raw)
    return [struct.unpack(">5i", out[i * 20:(i + 1) * 20]) for i in range(len(out) // 20)]


def main():
    # ---------- 1. per-tick walk with monotonicity + duplicates ----------
    ticks_by_minute = {}          # minute_epoch_ms -> [ (ts_ms, bid, ask) ]
    per_file = []
    monotonic_within_viol = 0
    dup_exact = 0                 # same ts and same (bid,ask)
    prev_ts = prev_px = None
    spread_min = math.inf
    spread_vals = []
    gap = {"start": None, "end": None, "missing": None}

    for hour_dt, path in hour_files():
        if not os.path.exists(path):
            per_file.append({"hour_utc": hour_dt.isoformat(), "missing": True})
            continue
        ticks = decode(path)
        hour_ms = int(hour_dt.timestamp() * 1000)
        base = {"hour_utc": hour_dt.isoformat(), "tick_count": len(ticks)}
        if not ticks:
            per_file.append(base)
            continue
        offs = [t[0] for t in ticks]
        base["offset_monotonic_strict"] = all(b > a for a, b in zip(offs, offs[1:]))
        base["offset_first"] = offs[0]
        base["offset_last"] = offs[-1]
        if not base["offset_monotonic_strict"]:
            monotonic_within_viol += 1
        for off, ask_i, bid_i, _, _ in ticks:
            ts = hour_ms + off
            bid, ask = bid_i / POINT, ask_i / POINT
            if prev_ts is not None:
                if ts < prev_ts:
                    base["cross_file_nonmonotonic"] = True
                if ts == prev_ts and (bid, ask) == prev_px:
                    dup_exact += 1
            prev_ts, prev_px = ts, (bid, ask)
            sp = ask - bid
            spread_min = min(spread_min, sp)
            spread_vals.append(sp)
            m = ts // 60000
            ticks_by_minute.setdefault(m, []).append((ts, bid, ask))
        per_file.append(base)

    # weekend gap measured from the tick stream (keys are minute indices)
    all_ts_sorted_keys = sorted(ticks_by_minute.keys())
    if len(all_ts_sorted_keys) >= 2:
        prev_m = all_ts_sorted_keys[0]
        for m in all_ts_sorted_keys[1:]:
            if m - prev_m > 1:  # missing minutes between two consecutive covered minutes
                d = gap["missing"] or -1
                if (m - prev_m - 1) > d:
                    gap = {"start": prev_m, "end": m, "missing": m - prev_m - 1}
            prev_m = m

    # ---------- 2. 1-min bars (bid & ask), coverage census ----------
    bars = {}
    for m, tl in ticks_by_minute.items():
        tl.sort(key=lambda x: x[0])
        bid_px = [t[1] for t in tl]
        ask_px = [t[2] for t in tl]
        mid = [(b + a) / 2 for b, a in zip(bid_px, ask_px)]
        bars[m] = {
            "bid_open": bid_px[0], "bid_close": bid_px[-1],
            "bid_high": max(bid_px), "bid_low": min(bid_px),
            "ask_open": ask_px[0], "ask_close": ask_px[-1],
            "ask_high": max(ask_px), "ask_low": min(ask_px),
            "mid_close": mid[-1],
            "tick_count": len(tl),
        }
    bar_minutes = sorted(bars.keys())

    # gap census within measured trading segments (>1 min); keys are minute indices
    gaps = []
    for a, b in zip(bar_minutes, bar_minutes[1:]):
        missing = b - a - 1
        if missing > 0:
            gaps.append({
                "from_utc": dt.datetime.fromtimestamp(a * 60, dt.timezone.utc).isoformat(),
                "to_utc": dt.datetime.fromtimestamp(b * 60, dt.timezone.utc).isoformat(),
                "missing_minutes": missing,
            })

    # per-day census (UTC days); keys are minute indices
    per_day = {}
    for m in bar_minutes:
        day = dt.datetime.fromtimestamp(m * 60, dt.timezone.utc).strftime("%Y-%m-%d")
        d = per_day.setdefault(day, {"minutes_with_ticks": 0, "ticks": 0})
        d["minutes_with_ticks"] += 1
        d["ticks"] += bars[m]["tick_count"]

    total_ticks = sum(v["ticks"] for v in per_day.values())
    window_minutes = int((WINDOW_END - WINDOW_START).total_seconds() // 60)

    # weekend behavior from retrieval manifest (full UTC hour labels from URL)
    man = json.load(open(os.path.join(PROBE_DIR, "retrieval_manifest.json")))

    def hour_label(url):
        # .../EURUSD/2024/02/<DD>/<HH>h_ticks.bi5 -> 2024-03-<DD>T<HH>:00Z (month 0-indexed)
        parts = url.split("/")
        y, m0, d, hh = parts[-4], int(parts[-3]), parts[-2], parts[-1].split("h")[0]
        return f"{y}-{m0 + 1:02d}-{d}T{hh}:00Z"

    empty_hours = [hour_label(e["url"]) for e in man["entries"]
                   if e["file_role"] == "2024_20240304_20240314" and e["decode_status"] == "EMPTY_FILE_NO_TICKS"]
    e404_hours = [hour_label(e["url"]) for e in man["entries"] if e["http_status"] == 404]
    boundary = [{"role": e["file_role"], "http_status": e["http_status"],
                 "bytes": e["byte_count"], "ticks": e["tick_count"],
                 "sha256": e["sha256"]} for e in man["entries"] if e["file_role"].startswith("boundary")]

    coverage = {
        "schema": "edq1_coverage_census@1",
        "window_utc": [WINDOW_START.isoformat().replace("+00:00", "Z"),
                       WINDOW_END.isoformat().replace("+00:00", "Z")],
        "window_calendar_minutes": window_minutes,
        "total_ticks_decoded": total_ticks,
        "distinct_minutes_with_ticks": len(bar_minutes),
        "per_day_utc": per_day,
        "weekend_behavior": {
            "hours_with_zero_byte_file": sorted(set(empty_hours)),
            "hours_with_http_404": sorted(set(e404_hours)),
            "measured_gap": ({
                "last_tick_before_utc": dt.datetime.fromtimestamp(gap["start"] * 60, dt.timezone.utc).isoformat() if gap["start"] else None,
                "first_tick_after_utc": dt.datetime.fromtimestamp(gap["end"] * 60, dt.timezone.utc).isoformat() if gap["end"] else None,
                "gap_minutes": gap["missing"],
            }),
        },
        "tick_duplicates_exact_ts_px": dup_exact,
        "monotonicity": {
            "files_with_within_hour_violation": monotonic_within_viol,
            "cross_file_nonmonotonic_files": sum(1 for f in per_file if f.get("cross_file_nonmonotonic")),
        },
        "gap_census_within_trading": {
            "count": len(gaps),
            "max_missing_minutes": max([g["missing_minutes"] for g in gaps], default=0),
            "gaps": gaps[:50],
        },
        "spread_evidence_pips": {
            "min": spread_min / PIP,
            "median": statistics.median(spread_vals) / PIP,
            "negative_or_zero_ticks": sum(1 for s in spread_vals if s <= 0),
        },
        "boundary_probes": boundary,
        "per_file_detail_ref": "retrieval_manifest.json",
    }
    with open(os.path.join(PROBE_DIR, "coverage_census.json"), "w") as f:
        json.dump(coverage, f, indent=2)

    # ---------- 3. Twelve Data alignment + indicative reconciliation ----------
    td = json.load(open(os.path.join(TD_DIR, "values_1min.json")))
    seen = {}
    dups_td = 0
    for v in td:
        t = v["datetime"]
        if t in seen:
            dups_td += 1
        seen[t] = v
    td_close = {}
    nonaligned = 0
    for t, v in seen.items():
        dtp = dt.datetime.strptime(t, "%Y-%m-%d %H:%M:%S").replace(tzinfo=dt.timezone.utc)
        if dtp.second != 0:
            nonaligned += 1
        td_close[int(dtp.timestamp() * 1000)] = float(v["close"])
    td_minutes = sorted(td_close.keys())

    td_gaps = []
    for a, b in zip(td_minutes, td_minutes[1:]):
        dmin = (b - a) // 60000
        if dmin > 1:
            td_gaps.append((dt.datetime.fromtimestamp(a / 1000, dt.timezone.utc).isoformat(),
                            dt.datetime.fromtimestamp(b / 1000, dt.timezone.utc).isoformat(), dmin - 1))

    def diffs_for_alignment(shift_minutes):
        """TD bar labeled T compared to Duka close of minute T+shift.

        bars/ticks keys are minute indices (epoch_ms // 60000); td keys epoch ms.
        """
        out = []
        for t, c in td_close.items():
            dk = bars.get(t // 60000 + shift_minutes)
            if dk is None:
                continue
            out.append(abs(c - dk["mid_close"]) / PIP)
        return out

    alignA = diffs_for_alignment(0)   # TD bar T covers [T, T+1)
    alignB = diffs_for_alignment(-1)  # TD bar T covers [T-1, T)

    def dist(vals):
        if not vals:
            return {"count": 0}
        s = sorted(vals)
        return {"count": len(vals),
                "median_abs_pips": round(statistics.median(s), 3),
                "p95_abs_pips": round(s[int(0.95 * (len(s) - 1))], 3),
                "max_abs_pips": round(s[-1], 3)}

    reconc = {
        "schema": "edq1_indicative_reconciliation@1",
        "note": "INDICATIVE ONLY; formal tolerance test is P2 per plan §2. "
                "Compares Twelve Data 1min CLOSE vs Dukascopy 1min tick-derived MID close.",
        "twelvedata": {
            "values_returned": len(td), "unique_datetimes": len(seen),
            "duplicate_datetimes": dups_td,
            "labels_all_second_aligned": nonaligned == 0,
            "gap_count_within_span": len(td_gaps),
            "field_inventory": sorted({k for v in td for k in v.keys()}),
            "bid_ask_available": False,
            "volume_field_present": any("volume" in k.lower() or k in ("v", "vol") for v in td for k in v.keys()),
        },
        "bar_convention_test": {
            "hypothesisA_label_T_covers[T,T+1)": dist(alignA),
            "hypothesisB_label_T_covers[T-1,T)": dist(alignB),
            "winner": "A" if (statistics.median(alignA) if alignA else 9e9) <= (statistics.median(alignB) if alignB else 9e9) else "B",
        },
        "alignment_A": dist(alignA),
        "dukascopy_mid_basis": "1-min mid close = (bid_close+ask_close)/2 from decoded ticks",
    }
    with open(os.path.join(PROBE_DIR, "indicative_reconciliation.json"), "w") as f:
        json.dump(reconc, f, indent=2)

    # ---------- 4. timestamp sanity exports ----------
    sanity = {}
    # first tick of London 07:00 UTC on Tuesday 2024-03-05
    p0507 = os.path.join(RAW_DIR, "2024", "20240305_07h_ticks.bi5")
    t0 = decode(p0507)[0]
    sanity["london_0700_first_tick"] = {
        "hour_file_utc": "2024-03-05T07:00:00Z",
        "offset_ms": t0[0],
        "absolute_epoch_ms": int(dt.datetime(2024, 3, 5, 7, tzinfo=dt.timezone.utc).timestamp() * 1000) + t0[0],
        "absolute_utc": dt.datetime.fromtimestamp(
            (int(dt.datetime(2024, 3, 5, 7, tzinfo=dt.timezone.utc).timestamp() * 1000) + t0[0]) / 1000,
            dt.timezone.utc).isoformat(),
        "bid": t0[2] / POINT, "ask": t0[1] / POINT,
    }
    if gap["start"]:
        sanity["measured_weekend"] = coverage["weekend_behavior"]["measured_gap"]
    with open(os.path.join(PROBE_DIR, "timestamp_sanity.json"), "w") as f:
        json.dump(sanity, f, indent=2)

    print(json.dumps({
        "total_ticks": total_ticks,
        "distinct_minutes": len(bar_minutes),
        "dup_ticks": dup_exact,
        "monotonic_files_violating": monotonic_within_viol,
        "gap_count": len(gaps),
        "weekend_gap": sanity.get("measured_weekend"),
        "alignA": dist(alignA), "alignB": dist(alignB),
        "td_unique": len(seen), "td_dups": dups_td, "td_gaps": len(td_gaps),
        "spread_median_pips": coverage["spread_evidence_pips"]["median"],
    }, indent=2))


if __name__ == "__main__":
    main()
