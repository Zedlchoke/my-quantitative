"""Task 0 — build the ANCESTRY-convention bar planes (signal plane).

LINEAGE-NOTE-1 resolution: the ancestor build_bars.py decoded the 24-byte
M1 record as (sec, o, c, l, h, v) and aggregated the 15m bar as
  b_o = first OPEN, b_h = max(CLOSE column), b_l = min(LOW column),
  b_c = last CLOSE          (build_bars.py ancestor, rows tuple).
I.e. the ancestor quirk is precisely: HIGH FROM THE CLOSE COLUMN; the LOW
is the true low column. This builder reproduces that convention exactly
(15m and, by max/min aggregation, H1) on the cohort pairs' raw M1 bytes,
with the port's per-pair tradability band (the band is a per-pair probe
fix, not part of the H/L quirk).

Decision rule (frozen by A1): the ANCESTRY-convention H1 plane is the
SIGNAL plane of all arms (R-ORIG stays a faithful ancestor
instantiation); the port's true-H/L H1 plane remains the COST plane
(spread charging unchanged — s_open/s_close derive from opens/closes and
are identical in both conventions; verified numerically).

Heavy job: scans every downloaded byte -> machine-wide heavy lock.
Output (machine-local, gitignored): bars15_ANC_{SYM}.parquet,
bars1h_ANC_{SYM}.parquet + a diff report vs the port's planes.
"""
from __future__ import annotations

import argparse
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
from build_bars import RAW, DERIVED, load_day, session_bucket  # noqa: E402


def build_planes(symbol: str, lock) -> dict:
    cfg = load_pair_config(symbol)
    man = json.loads(
        (LANE / "data_local" / "duka" / f"m1_manifest_{symbol}.json").read_text())
    bid_files = sorted(f.name for f in (RAW / "BID" / cfg.symbol).glob("*.bi5"))
    rows_anc = []       # ancestor convention: high = max(close)
    rows_port_hl = []   # port convention: high = max(true high)
    for name in bid_files:
        y, m, d = map(int, name[:-4].split("-"))
        day0 = dt_utc(y, m, d)
        b = load_day("BID", name, cfg, man)
        a = load_day("ASK", name, cfg, man)
        n = min(len(b), len(a))
        bb, aa = b[:n], a[:n]
        sc = cfg.price_scale
        secs = bb["sec"]
        bo = bb["o"].astype(np.float64) / sc
        ao = aa["o"].astype(np.float64) / sc
        tradable = (
            (bb["v"].astype(np.float64) > 0)
            & (bo > cfg.band_lo) & (bo < cfg.band_hi) & (ao >= bo)
        )
        bc = bb["c"].astype(np.float64) / sc
        ac = aa["c"].astype(np.float64) / sc
        bl = bb["l"].astype(np.float64) / sc
        bh = bb["h"].astype(np.float64) / sc
        for k in range(0, n - 14, 15):
            sl = slice(k, k + 15)
            if not tradable[sl].all() or not np.all(np.diff(secs[sl]) == 60):
                continue
            base = int(day0.timestamp()) + int(secs[k])
            # ancestor convention rows (bid side drives the signal plane)
            rows_anc.append((
                base, bo[k], bc[sl].max(), bl[sl].min(), bc[sl][-1],
                ao[k], ac[sl].max(), ac[sl].min(), ac[sl][-1],
                ao[k] - bo[k], ac[sl][-1] - bc[sl][-1],
            ))
            rows_port_hl.append((
                base, bo[k], bh[sl].max(), bl[sl].min(), bc[sl][-1],
            ))
        if len(rows_anc) % 20000 < 96:
            lock.heartbeat(extra={"symbol": symbol, "bars15": len(rows_anc)})
    cols = ["ts", "b_o", "b_h", "b_l", "b_c", "a_o", "a_h", "a_l", "a_c",
            "s_open", "s_close"]
    df = pd.DataFrame(rows_anc, columns=cols).sort_values("ts").reset_index(drop=True)
    df["ts"] = pd.to_datetime(df["ts"], unit="s", utc=True)

    def h1_agg(frame):
        ts_s = (frame["ts"].dt.tz_convert("UTC").dt.tz_localize(None)
                .to_numpy().astype("datetime64[s]").astype("int64"))
        in_hour = ts_s // 3600
        out = []
        start = 0
        for i in range(1, len(frame) + 1):
            if i == len(frame) or in_hour[i] != in_hour[start]:
                grp = slice(start, i)
                if i - start == 4 and all(np.diff(ts_s[grp]) == 900):
                    f, l = grp.start, grp.stop - 1
                    out.append((
                        int(in_hour[start] * 3600),
                        frame["b_o"].iloc[f], frame["b_h"].iloc[grp].max(),
                        frame["b_l"].iloc[grp].min(), frame["b_c"].iloc[l],
                        frame["a_o"].iloc[f], frame["a_c"].iloc[l],
                        frame["a_o"].iloc[f] - frame["b_o"].iloc[f],
                        frame["a_c"].iloc[l] - frame["b_c"].iloc[l],
                    ))
                start = i
        h = pd.DataFrame(out, columns=[
            "ts", "b_o", "b_h", "b_l", "b_c", "a_o", "a_c", "s_open", "s_close"])
        h["ts"] = pd.to_datetime(h["ts"], unit="s", utc=True)
        return h

    h1 = h1_agg(df)
    df.to_parquet(DERIVED / f"bars15_ANC_{symbol}.parquet", index=False)
    h1.to_parquet(DERIVED / f"bars1h_ANC_{symbol}.parquet", index=False)

    # ---- diff vs the port's true-H/L planes ----
    p15 = pd.read_parquet(DERIVED / f"bars15_{symbol}.parquet")
    p1h = pd.read_parquet(DERIVED / f"bars1h_{symbol}.parquet")
    m15 = df.merge(p15, on="ts", suffixes=("_anc", "_port"))
    m1h = h1.merge(p1h, on="ts", suffixes=("_anc", "_port"))
    diff = {
        "symbol": symbol,
        "bars15_rows_anc": int(len(df)), "bars15_rows_port": int(len(p15)),
        "bars15_ts_sets_equal": bool(set(df["ts"]) == set(p15["ts"])),
        "bars1h_rows_anc": int(len(h1)), "bars1h_rows_port": int(len(p1h)),
        "bars1h_ts_sets_equal": bool(set(h1["ts"]) == set(p1h["ts"])),
        "bars15_b_h": {
            "max_abs_diff": float((m15["b_h_anc"] - m15["b_h_port"]).abs().max()),
            "n_anc_below_port": int((m15["b_h_anc"] < m15["b_h_port"]).sum()),
            "n_equal": int((m15["b_h_anc"] == m15["b_h_port"]).sum()),
            "n_anc_above_port": int((m15["b_h_anc"] > m15["b_h_port"]).sum()),
            "mean_gap_pips": float(
                ((m15["b_h_port"] - m15["b_h_anc"]) / cfg.pip).mean()),
        },
        "bars15_b_l": {
            "max_abs_diff": float((m15["b_l_anc"] - m15["b_l_port"]).abs().max()),
            "n_differ": int((m15["b_l_anc"] != m15["b_l_port"]).sum()),
        },
        "bars1h_b_h": {
            "max_abs_diff": float((m1h["b_h_anc"] - m1h["b_h_port"]).abs().max()),
            "n_anc_below_port": int((m1h["b_h_anc"] < m1h["b_h_port"]).sum()),
            "n_equal": int((m1h["b_h_anc"] == m1h["b_h_port"]).sum()),
            "mean_gap_pips": float(
                ((m1h["b_h_port"] - m1h["b_h_anc"]) / cfg.pip).mean()),
        },
        "bars1h_b_l": {
            "max_abs_diff": float((m1h["b_l_anc"] - m1h["b_l_port"]).abs().max()),
            "n_differ": int((m1h["b_l_anc"] != m1h["b_l_port"]).sum()),
        },
        "spreads_identical": {
            "s_open_max_abs_diff_15m": float(
                (m15["s_open_anc"] - m15["s_open_port"]).abs().max()),
            "s_close_max_abs_diff_15m": float(
                (m15["s_close_anc"] - m15["s_close_port"]).abs().max()),
            "s_open_max_abs_diff_1h": float(
                (m1h["s_open_anc"] - m1h["s_open_port"]).abs().max()),
            "s_close_max_abs_diff_1h": float(
                (m1h["s_close_anc"] - m1h["s_close_port"]).abs().max()),
        },
    }
    return diff


def dt_utc(y, m, d):
    import datetime as _dt
    return _dt.datetime(y, m, d, tzinfo=_dt.timezone.utc)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    args = ap.parse_args()
    from governance import heavy_lock
    lock = None
    status, note = "FAILED", ""
    out_path = DERIVED / f"plane_diff_{args.symbol}.json"
    try:
        try:
            lock = heavy_lock.acquire(
                cycle_id="ERP1-TRACKA-COHORT-1",
                role="falsifier-plane",
                worktree=str(LANE),
                command=[sys.executable, str(Path(__file__).resolve()), args.symbol],
                expected_artifacts=[str(out_path)],
            )
        except heavy_lock.LockBusyError as e:
            print(json.dumps({"verdict": "NOT_RUN_RESOURCE_CONFLICT",
                              "reason": str(e)}))
            return 4
        diff = build_planes(args.symbol, lock)
        out_path.write_text(json.dumps(diff, indent=1))
        status = "FINISHED"
        print(json.dumps(diff, indent=1))
        return 0
    except Exception as e:  # noqa: BLE001
        status, note = "FAILED", f"{type(e).__name__}: {e}"[:400]
        raise
    finally:
        if lock is not None:
            lock.release(status=status, note=note)


if __name__ == "__main__":
    sys.exit(main())
