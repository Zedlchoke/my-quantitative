"""DIAG census + bar planes — hardened tracka_census@2 schema, per pair.

Reuses the committed scripts (imported, never modified):
  - build_bars.CANDLE_DTYPE / session_bucket / bucket_entry / q3 /
    SESSION_BUCKETS / gap_census (the hardened census schema machinery);
  - the tradability law: minute TRADABLE iff vol>0 AND band_lo < bid.open
    < band_hi AND ask >= bid; 15m bar VALID iff all 15 minutes tradable
    and consecutive; H1 VALID iff exactly its four 15m bars, consecutive.

Builds BOTH plane conventions per pair (LINEAGE-NOTE-1 / A1 decision rule):
  bars15_{SYM}.parquet / bars1h_{SYM}.parquet   port true-H/L (COST plane)
  bars15_ANC_{SYM}.parquet / bars1h_ANC_{SYM}.parquet
      ANCESTRY convention (15m high = max CLOSE column, low = min LOW
      column) — the SIGNAL plane of all arms, per the cohort's plane pin.
  The s_open/s_close spreads are identical by construction in both
  conventions; the plane diff asserts max abs diff 0.0 (gate).

Heavy job: scans every copied byte -> machine-wide heavy lock (heartbeat).
Outputs under diag/data_local/derived/: census_{SYM}.json + 4 parquets +
plane_diff_{SYM}.json. Gates identical to the committed census
(midweek share > 0.90; nonpos-spread < 1%; bars15 > 100k; dup == 0;
reconcile p50 within rounding).
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import lzma
import sys
from pathlib import Path

import numpy as np
import pandas as pd

DIAG = Path(__file__).resolve().parent.parent          # .../ERP1-TRACKA-COHORT-1/diag
sys.path.insert(0, str(DIAG / "scripts"))
sys.path.insert(0, str(DIAG.parent / "scripts"))       # committed cycle scripts
sys.path.insert(0, "/Users/hoangminhlong/my-quantitative/research")

from pair_config_diag import load_pair_config  # noqa: E402
from build_bars import (  # noqa: E402
    CANDLE_DTYPE, MIN_BUCKET_N, QUANTILE_POINTS, SESSION_BUCKETS,
    bucket_entry, gap_census, q3, session_bucket,
)

RAW = DIAG / "data_local"
DERIVED = DIAG / "data_local" / "derived"


def load_day(pair: str, side: str, name: str, man: dict) -> np.ndarray:
    path = RAW / pair / side / name
    raw = path.read_bytes()
    entry = man["files"].get(f"M1/{side}/{name}")
    if entry is None or entry.get("sha256") != hashlib.sha256(raw).hexdigest():
        raise SystemExit(f"FAIL_CLOSED manifest mismatch: {pair}/{side}/{name}")
    plain = lzma.decompress(raw)
    if len(plain) % CANDLE_DTYPE.itemsize:
        raise SystemExit(
            f"FAIL_CLOSED {pair}/{side}/{name}: decompressed len {len(plain)}")
    return np.frombuffer(plain, dtype=CANDLE_DTYPE)


def h1_agg(df: pd.DataFrame) -> pd.DataFrame:
    ts_s = (df["ts"].dt.tz_convert("UTC").dt.tz_localize(None)
            .to_numpy().astype("datetime64[s]").astype("int64"))
    in_hour = ts_s // 3600
    out = []
    start = 0
    for i in range(1, len(df) + 1):
        if i == len(df) or in_hour[i] != in_hour[start]:
            grp = slice(start, i)
            if i - start == 4 and all(np.diff(ts_s[grp]) == 900):
                f, l = grp.start, grp.stop - 1
                out.append((
                    int(in_hour[start] * 3600),
                    df["b_o"].iloc[f], df["b_h"].iloc[grp].max(),
                    df["b_l"].iloc[grp].min(), df["b_c"].iloc[l],
                    df["a_o"].iloc[f], df["a_c"].iloc[l],
                    df["a_o"].iloc[f] - df["b_o"].iloc[f],
                    df["a_c"].iloc[l] - df["b_c"].iloc[l],
                ))
            start = i
    h = pd.DataFrame(out, columns=[
        "ts", "b_o", "b_h", "b_l", "b_c", "a_o", "a_c", "s_open", "s_close"])
    h["ts"] = pd.to_datetime(h["ts"], unit="s", utc=True)
    return h


def build_pair(pair: str, lock) -> dict:
    cfg = load_pair_config(pair)
    man = json.loads((RAW / pair / "m1_manifest.json").read_text())
    bid_files = sorted(f.name for f in (RAW / pair / "BID").glob("*.bi5"))
    ask_files = sorted(f.name for f in (RAW / pair / "ASK").glob("*.bi5"))
    if bid_files != ask_files:
        raise SystemExit("FAIL_CLOSED BID/ASK day file sets differ")

    census = {
        "schema": "tracka_census@2",
        "lane": "ERP1-TRACKA-COHORT-1/diag (DIAGNOSTIC_OUTCOME_EXPOSED)",
        "symbol": cfg.symbol,
        "pair_config": {
            "pip": cfg.pip, "price_scale": cfg.price_scale,
            "band_lo": cfg.band_lo, "band_hi": cfg.band_hi,
            "provenance": cfg.derivation,
        },
        "days": 0, "days_missing_both": [], "days_short_records": {},
        "days_zero_tradable": {"count": 0, "weekend": 0, "weekday": 0,
                               "weekday_dates": []},
        "min_tradable_by_dow": [0] * 7, "min_total_by_dow": [0] * 7,
        "nonpos_spread_minutes": 0, "price_range_violations": 0,
        "first_ts": None, "last_ts": None,
    }
    rows_port, rows_anc = [], []
    sc = cfg.price_scale

    for name in bid_files:
        y, m, d = map(int, name[:-4].split("-"))
        day0 = dt.datetime(y, m, d, tzinfo=dt.timezone.utc)
        b = load_day(pair, "BID", name, man)
        a = load_day(pair, "ASK", name, man)
        census["days"] += 1
        if len(b) != 1440 or len(a) != 1440:
            census["days_short_records"][name] = [len(b), len(a)]
        n = min(len(b), len(a))
        bb, aa = b[:n], a[:n]
        secs = bb["sec"]
        bo = bb["o"].astype(np.float64) / sc
        ao = aa["o"].astype(np.float64) / sc
        tradable = ((bb["v"].astype(np.float64) > 0)
                    & (bo > cfg.band_lo) & (bo < cfg.band_hi) & (ao >= bo))
        census["nonpos_spread_minutes"] += int(np.sum(ao < bo))
        census["price_range_violations"] += int(
            np.sum(~((bo > cfg.band_lo) & (bo < cfg.band_hi))))
        dow = day0.weekday()
        census["min_tradable_by_dow"][dow] += int(tradable.sum())
        census["min_total_by_dow"][dow] += n
        if tradable.any():
            ts_first = day0 + dt.timedelta(
                seconds=int(secs[int(np.argmax(tradable))]))
            census["first_ts"] = census["first_ts"] or ts_first.isoformat()
            census["last_ts"] = (
                day0 + dt.timedelta(seconds=int(secs[n - 1]))).isoformat()
        elif dow >= 5:
            census["days_zero_tradable"]["weekend"] += 1
        else:
            census["days_zero_tradable"]["weekday"] += 1
            census["days_zero_tradable"]["weekday_dates"].append(name[:-4])
        bc = bb["c"].astype(np.float64) / sc
        ac = aa["c"].astype(np.float64) / sc
        bl = bb["l"].astype(np.float64) / sc
        bh = bb["h"].astype(np.float64) / sc
        al = aa["l"].astype(np.float64) / sc
        ah = aa["h"].astype(np.float64) / sc
        for k in range(0, n - 14, 15):
            sl = slice(k, k + 15)
            if not tradable[sl].all() or not np.all(np.diff(secs[sl]) == 60):
                continue
            ts = int(day0.timestamp()) + int(secs[k])
            # port convention (true H/L) — the COST plane
            rows_port.append((
                ts, bo[k], bh[sl].max(), bl[sl].min(), bc[sl][-1],
                ao[k], ah[sl].max(), al[sl].min(), ac[sl][-1],
                ao[k] - bo[k], ac[sl][-1] - bc[sl][-1],
            ))
            # ANCESTRY convention (high = max CLOSE column) — SIGNAL plane
            rows_anc.append((
                ts, bo[k], bc[sl].max(), bl[sl].min(), bc[sl][-1],
                ao[k], ac[sl].max(), ac[sl].min(), ac[sl][-1],
                ao[k] - bo[k], ac[sl][-1] - bc[sl][-1],
            ))
        if census["days"] % 250 == 0:
            print(f"... {pair} {census['days']} days", file=sys.stderr)
            lock.heartbeat(extra={"symbol": pair, "days": census["days"]})

    cols = ["ts", "b_o", "b_h", "b_l", "b_c", "a_o", "a_h", "a_l", "a_c",
            "s_open", "s_close"]
    df = pd.DataFrame(rows_port, columns=cols).sort_values("ts").reset_index(drop=True)
    dup = int(df["ts"].duplicated().sum())
    if dup:
        census["gates"] = {"duplicate_15m_ts_eq_0": False}
        census["gate_margins"] = {"duplicate_15m_ts_eq_0": -dup}
        census["verdict"] = "BUILD_FAIL"
        (DERIVED / f"census_{cfg.symbol}.json").write_text(
            json.dumps(census, indent=1, default=str))
        print(f"FAIL_CLOSED duplicate 15m timestamps: {dup}")
        return census
    df["ts"] = pd.to_datetime(df["ts"], unit="s", utc=True)
    df_anc = pd.DataFrame(rows_anc, columns=cols).sort_values("ts").reset_index(drop=True)
    df_anc["ts"] = pd.to_datetime(df_anc["ts"], unit="s", utc=True)
    assert np.array_equal(df["ts"].to_numpy(), df_anc["ts"].to_numpy())

    DERIVED.mkdir(parents=True, exist_ok=True)
    df.to_parquet(DERIVED / f"bars15_{cfg.symbol}.parquet", index=False)
    df_anc.to_parquet(DERIVED / f"bars15_ANC_{cfg.symbol}.parquet", index=False)
    h1 = h1_agg(df)
    h1_anc = h1_agg(df_anc)
    assert np.array_equal(h1["ts"].to_numpy(), h1_anc["ts"].to_numpy())
    h1.to_parquet(DERIVED / f"bars1h_{cfg.symbol}.parquet", index=False)
    h1_anc.to_parquet(DERIVED / f"bars1h_ANC_{cfg.symbol}.parquet", index=False)

    # ---- plane diff: spreads identical across conventions (gate) ----
    md = df.merge(df_anc, on="ts", suffixes=("_port", "_anc"))
    mh = h1.merge(h1_anc, on="ts", suffixes=("_port", "_anc"))
    plane_diff = {
        "symbol": pair,
        "bars15_rows_port": int(len(df)), "bars15_rows_anc": int(len(df_anc)),
        "bars15_ts_equal": bool(np.array_equal(df["ts"].to_numpy(),
                                               df_anc["ts"].to_numpy())),
        "bars1h_rows_port": int(len(h1)), "bars1h_rows_anc": int(len(h1_anc)),
        "bars1h_ts_equal": bool(np.array_equal(h1["ts"].to_numpy(),
                                               h1_anc["ts"].to_numpy())),
        "s_open_max_abs_diff_15m": float(
            (md["s_open_port"] - md["s_open_anc"]).abs().max()),
        "s_close_max_abs_diff_15m": float(
            (md["s_close_port"] - md["s_close_anc"]).abs().max()),
        "s_open_max_abs_diff_1h": float(
            (mh["s_open_port"] - mh["s_open_anc"]).abs().max()),
        "s_close_max_abs_diff_1h": float(
            (mh["s_close_port"] - mh["s_close_anc"]).abs().max()),
        "b_h_anc_le_port_always": bool(
            (md["b_h_anc"] <= md["b_h_port"] + 1e-12).all()),
        "n_anc_high_below_port": int((md["b_h_anc"] < md["b_h_port"]).sum()),
        "mean_gap_pips_15m_high": float(
            ((md["b_h_port"] - md["b_h_anc"]) / cfg.pip).mean()),
    }
    (DERIVED / f"plane_diff_{cfg.symbol}.json").write_text(
        json.dumps(plane_diff, indent=1))

    # ---- hardened spread census (pips) on the port 15m plane ----
    s_open = df["s_open"].to_numpy() / cfg.pip
    s_close = df["s_close"].to_numpy() / cfg.pip
    hour = df["ts"].dt.hour.to_numpy()
    dow_arr = df["ts"].dt.dayofweek.to_numpy()
    masks = session_bucket(hour, dow_arr)
    by_session = {k: bucket_entry(s_open[mk], s_close[mk])
                  for k, mk in masks.items()}
    low_sample = sorted(k for k, v in by_session.items() if v.get("flag"))
    census["spread_pips"] = {
        "overall_open": q3(s_open), "overall_close": q3(s_close),
        "by_session": by_session,
        "by_session_open": {k: v["open"] for k, v in by_session.items()
                            if v["open"] is not None},
    }
    census["low_sample_buckets"] = low_sample
    ts_s = (df["ts"].dt.tz_convert("UTC").dt.tz_localize(None)
            .to_numpy().astype("datetime64[s]").astype("int64"))
    census["gap_census"] = gap_census(df, ts_s, hour)

    expected_midweek = (census["min_tradable_by_dow"][0]
                        + census["min_tradable_by_dow"][2])
    total_midweek = (census["min_total_by_dow"][0]
                     + census["min_total_by_dow"][2])
    share = expected_midweek / max(total_midweek, 1)
    census["midweek_tradable_share"] = round(share, 5)
    census["days_short_records_n"] = len(census["days_short_records"])
    census["bars15_valid"] = int(len(df))
    census["bars1h_valid"] = int(len(h1))
    nonpos_share = census["nonpos_spread_minutes"] / max(census["days"] * 1440, 1)

    # reconcile from the PERSISTED parquet
    rb = pd.read_parquet(DERIVED / f"bars15_{cfg.symbol}.parquet")
    r_open = rb["s_open"].to_numpy() / cfg.pip
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
        max_diff = max(max_diff, abs(med - by_session[k]["open"]["50"]))
    tol = 5e-4
    reconcile_pass = max_diff <= tol
    census["reconcile"] = {
        "method": ("per-bar s_open/pip medians recomputed from the "
                   "persisted bars15 parquet, bucketed per session, vs "
                   "census p50"),
        "max_abs_diff_pips": round(max_diff, 6), "tolerance": tol,
        "pass": reconcile_pass,
        "per_bucket_median_open_p50": per_bucket,
    }

    gates = {
        "midweek_tradable_share_gt_0.90": share > 0.90,
        "nonpos_spread_share_lt_1pct": nonpos_share < 0.01,
        "bars15_gt_100k": len(df) > 100_000,
        "duplicate_15m_ts_eq_0": dup == 0,
        "reconcile_p50_within_rounding": reconcile_pass,
        "plane_spreads_identical": (
            plane_diff["s_open_max_abs_diff_15m"] == 0.0
            and plane_diff["s_close_max_abs_diff_15m"] == 0.0
            and plane_diff["s_open_max_abs_diff_1h"] == 0.0
            and plane_diff["s_close_max_abs_diff_1h"] == 0.0),
    }
    census["gates"] = gates
    census["gate_margins"] = {
        "midweek_tradable_share_gt_0.90": round(share - 0.90, 6),
        "nonpos_spread_share_lt_1pct": round(0.01 - nonpos_share, 6),
        "bars15_gt_100k": int(len(df) - 100_000),
        "duplicate_15m_ts_eq_0": int(-dup),
        "reconcile_p50_within_rounding": round(tol - max_diff, 6),
        "plane_spreads_identical": 0,
    }
    census["nonpos_spread_share"] = round(nonpos_share, 8)
    census["data_manifest"] = {
        "bars15_rows": int(len(df)), "bars1h_rows": int(len(h1)),
        "m1_manifest_sha256": hashlib.sha256(
            (RAW / pair / "m1_manifest.json").read_bytes()).hexdigest(),
        "m1_manifest_path": f"diag/data_local/{pair}/m1_manifest.json",
        "day_files": len(bid_files),
        "window": "2021-01-01..2026-06-30 (2026-07+ ignored, diagnostic law)",
    }
    census["fixture_asserts"] = {
        "rollover_bucket_count_gt_0": by_session["rollover_21_22"]["n"] > 0,
        "sunday_open_cell_present": by_session["sunday_open_21_22"]["n"] > 0,
    }
    census["verdict"] = "BUILD_PASS" if all(gates.values()) else "BUILD_FAIL"
    (DERIVED / f"census_{cfg.symbol}.json").write_text(
        json.dumps(census, indent=1, default=str))
    print(json.dumps({
        "symbol": pair, "verdict": census["verdict"], "gates": gates,
        "gate_margins": census["gate_margins"],
        "bars15_valid": census["bars15_valid"],
        "bars1h_valid": census["bars1h_valid"],
        "midweek_tradable_share": census["midweek_tradable_share"],
        "overall_open_p50_pips": census["spread_pips"]["overall_open"]["50"],
        "price_range_violations": census["price_range_violations"],
        "days_zero_tradable_weekday": census["days_zero_tradable"]["weekday"],
    }, indent=1))
    return census


def main() -> int:
    from governance import heavy_lock
    lock = None
    status, note = "FAILED", ""
    try:
        try:
            lock = heavy_lock.acquire(
                cycle_id="ERP1-TRACKA-COHORT-1",
                role="diag-census",
                worktree=str(DIAG),
                command=[sys.executable, str(Path(__file__).resolve()),
                         *sys.argv[1:]],
                expected_artifacts=[str(DERIVED / "census_EURUSD.json"),
                                    str(DERIVED / "census_GBPUSD.json")],
            )
        except heavy_lock.LockBusyError as e:
            print(json.dumps({"verdict": "NOT_RUN_RESOURCE_CONFLICT",
                              "reason": str(e)}))
            return 4
        rc = 0
        for pair in sys.argv[1:] or ("EURUSD", "GBPUSD"):
            c = build_pair(pair, lock)
            if c["verdict"] != "BUILD_PASS":
                rc = 2
        status = "FINISHED" if rc == 0 else "FAILED"
        note = "" if rc == 0 else "at least one pair BUILD_FAIL"
        return rc
    except Exception as e:  # noqa: BLE001
        status, note = "FAILED", f"{type(e).__name__}: {e}"[:400]
        raise
    finally:
        if lock is not None:
            lock.release(status=status, note=note)


if __name__ == "__main__":
    sys.exit(main())
