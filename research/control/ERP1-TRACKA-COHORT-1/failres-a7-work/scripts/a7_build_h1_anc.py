"""A7 L1b — independent rebuild of the EURUSD H1 ANC plane from M1 bytes.

HEAVY JOB (full 4,014-file corpus scan) — holds the machine-wide heavy
lock (governance.heavy_lock) for its whole duration.

Independence: this is A7's OWN minimal aggregation code following the
documented ANC convention (committed build path, read for reference only,
NOT imported):
  - Dukascopy .bi5 day records, dtype sec,o,c,l,h,v big-endian (24 B),
    prices = int/1e5 (EURUSD);
  - a minute is TRADABLE iff vol>0 AND 0.80 < bid.open < 1.35 AND
    ask.open >= bid.open;
  - a 15m bar is VALID iff its 15 minutes are all tradable and
    consecutive (60 s); ANC convention: high = max of CLOSE column,
    low = min of LOW column (both sides);
  - an H1 bar is VALID iff exactly its four 15m bars exist, consecutive
    (900 s) within one UTC hour; s_open = a_o[0]-b_o[0],
    s_close = a_c[-1]-b_c[-1];
  - every day file sha256-verified against the manifest COMMITTED IN THE
    A7 WORKTREE before decoding (full corpus, not just the sample).

Reads corpus bytes from the diag lane's READ-ONLY data_local dir. Writes
ONLY into the A7 worktree namespace (failres-a7-work/derived/).
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

A7_WORK = Path(__file__).resolve().parent.parent
COHORT = A7_WORK.parent
CORPUS = Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
              "erp1-tracka-cohort-1/diag-daemon/research/control/"
              "ERP1-TRACKA-COHORT-1/diag/data_local/EURUSD")
MANIFEST = COHORT / "diag" / "data_local" / "EURUSD" / "m1_manifest.json"
OUT_PARQUET = A7_WORK / "derived" / "bars1h_ANC_EURUSD_A7.parquet"
RESULTS = A7_WORK / "layer_results"
REPO = Path("/Users/hoangminhlong/my-quantitative")
PANEL_END_TS = int(dt.datetime(2026, 6, 30, 23, 59, 59,
                               tzinfo=dt.timezone.utc).timestamp())

CANDLE = np.dtype([("sec", ">i4"), ("o", ">i4"), ("c", ">i4"),
                   ("l", ">i4"), ("h", ">i4"), ("v", ">f4")])
SCALE = 1e5
BAND_LO, BAND_HI = 0.80, 1.35

sys.path.insert(0, str(REPO / "research"))
from governance import heavy_lock  # noqa: E402


AUDITED_CANDS = [
    ("/Users/hoangminhlong/my-quantitative/.worktrees/"
     "erp1-tracka-cohort-1/failres-attrib/research/control/"
     "ERP1-TRACKA-COHORT-1/failres/data_local/derived/"
     "bars1h_ANC_EURUSD.parquet"),
    ("/Users/hoangminhlong/my-quantitative/.worktrees/"
     "erp1-tracka-cohort-1/diag-daemon/research/control/"
     "ERP1-TRACKA-COHORT-1/diag/data_local/derived/"
     "bars1h_ANC_EURUSD.parquet"),
]


def audited_plane():
    # audited object = the failres-attrib byte copy; fall back to the
    # diag lane's derived copy (sha-pinned identical, verified below)
    for c in AUDITED_CANDS:
        if Path(c).exists():
            return pd.read_parquet(c), c
    raise SystemExit("FAIL_CLOSED audited bars1h_ANC_EURUSD.parquet absent")


def main() -> int:
    RESULTS.mkdir(parents=True, exist_ok=True)
    lock = None
    status, note = "FAILED", ""
    try:
        try:
            lock = heavy_lock.acquire(
                cycle_id="ERP1-TRACKA-COHORT-1",
                role="a7-repro-plane-rebuild",
                worktree=str(Path(__file__).resolve().parents[3]),
                command=[sys.executable, str(Path(__file__).resolve()),
                         *sys.argv[1:]],
                expected_artifacts=[str(OUT_PARQUET)],
            )
        except heavy_lock.LockBusyError as e:
            print(json.dumps({"verdict": "NOT_RUN_RESOURCE_CONFLICT",
                              "reason": str(e)}))
            return 4

        man = json.loads(MANIFEST.read_text())
        bid_files = sorted(f.name for f in (CORPUS / "BID").glob("*.bi5"))
        ask_files = sorted(f.name for f in (CORPUS / "ASK").glob("*.bi5"))
        if bid_files != ask_files:
            raise SystemExit("FAIL_CLOSED BID/ASK day-file sets differ")

        sha_bad, rows = [], []
        n_short = {}
        for j, name in enumerate(bid_files):
            for side in ("BID", "ASK"):
                raw = (CORPUS / side / name).read_bytes()
                entry = man["files"].get(f"M1/{side}/{name}")
                if entry is None or \
                        entry.get("sha256") != hashlib.sha256(raw).hexdigest():
                    sha_bad.append(f"{side}/{name}")
            if sha_bad:
                raise SystemExit(f"FAIL_CLOSED manifest mismatch: {sha_bad}")
            b = np.frombuffer(lzma.decompress(
                (CORPUS / "BID" / name).read_bytes()), dtype=CANDLE)
            a = np.frombuffer(lzma.decompress(
                (CORPUS / "ASK" / name).read_bytes()), dtype=CANDLE)
            if len(b) != 1440 or len(a) != 1440:
                n_short[name] = [len(b), len(a)]
            n = min(len(b), len(a))
            bb, aa = b[:n], a[:n]
            secs = bb["sec"].astype(np.int64)
            bo = bb["o"].astype(np.float64) / SCALE
            bc = bb["c"].astype(np.float64) / SCALE
            bl = bb["l"].astype(np.float64) / SCALE
            ao = aa["o"].astype(np.float64) / SCALE
            ac = aa["c"].astype(np.float64) / SCALE
            al = aa["l"].astype(np.float64) / SCALE
            tradable = ((bb["v"].astype(np.float64) > 0)
                        & (bo > BAND_LO) & (bo < BAND_HI) & (ao >= bo))
            y, m, d = map(int, name[:-4].split("-"))
            day0 = int(dt.datetime(y, m, d,
                                   tzinfo=dt.timezone.utc).timestamp())
            for k in range(0, n - 14, 15):
                sl = slice(k, k + 15)
                if not tradable[sl].all() or \
                        not np.all(np.diff(secs[sl]) == 60):
                    continue
                rows.append((
                    day0 + int(secs[k]), bo[k], bc[sl].max(), bl[sl].min(),
                    bc[sl][-1], ao[k], ac[sl].max(), ac[sl].min(),
                    ac[sl][-1], ao[k] - bo[k], ac[sl][-1] - bc[sl][-1]))
            if (j + 1) % 500 == 0:
                lock.heartbeat(extra={"symbol": "EURUSD", "days": j + 1})

        cols15 = ["ts", "b_o", "b_h", "b_l", "b_c", "a_o", "a_h", "a_l",
                  "a_c", "s_open", "s_close"]
        df15 = pd.DataFrame(sorted(rows), columns=cols15)
        dup = int(df15["ts"].duplicated().sum())

        # ---- H1: exactly 4 consecutive 15m bars within one UTC hour ----
        ts_s = df15["ts"].to_numpy(dtype=np.int64)
        in_hour = ts_s // 3600
        out = []
        start = 0
        for i in range(1, len(df15) + 1):
            if i == len(df15) or in_hour[i] != in_hour[start]:
                if i - start == 4 and np.all(np.diff(ts_s[start:i]) == 900):
                    f, l = start, i - 1
                    out.append((
                        int(in_hour[start] * 3600),
                        df15["b_o"].iloc[f], df15["b_h"].iloc[start:i].max(),
                        df15["b_l"].iloc[start:i].min(), df15["b_c"].iloc[l],
                        df15["a_o"].iloc[f], df15["a_c"].iloc[l],
                        df15["a_o"].iloc[f] - df15["b_o"].iloc[f],
                        df15["a_c"].iloc[l] - df15["b_c"].iloc[l]))
                start = i
        h1 = pd.DataFrame(out, columns=["ts", "b_o", "b_h", "b_l", "b_c",
                                        "a_o", "a_c", "s_open", "s_close"])
        OUT_PARQUET.parent.mkdir(parents=True, exist_ok=True)
        h1.to_parquet(OUT_PARQUET, index=False)

        # ---- compare vs the audited plane (panel window) ----
        aud_full, aud_src = audited_plane()
        aud = aud_full
        ats = (aud["ts"].dt.tz_convert("UTC").dt.tz_localize(None)
               .to_numpy().astype("datetime64[s]").astype("int64"))
        msk = ats <= PANEL_END_TS
        aud = aud.loc[msk].reset_index(drop=True)
        ats = ats[msk]
        mine = h1[h1["ts"] <= PANEL_END_TS].reset_index(drop=True)
        cmp = {
            "audited_source": aud_src,
            "audited_rows_full": int(len(aud_full)),
            "audited_rows_panel": int(len(aud)),
            "rebuilt_rows_panel": int(len(mine)),
            "row_count_equal": int(len(aud)) == int(len(mine)),
            "ts_equal": bool(len(aud) == len(mine)
                             and np.array_equal(ats, mine["ts"].to_numpy())),
        }
        maxd = {}
        for c in ("b_o", "b_h", "b_l", "b_c", "a_o", "a_c",
                  "s_open", "s_close"):
            if cmp["row_count_equal"] and cmp["ts_equal"]:
                maxd[c] = float(np.abs(
                    mine[c].to_numpy(float) - aud[c].to_numpy(float)).max())
            else:
                maxd[c] = None
        cmp["max_abs_diff"] = maxd
        cmp["max_abs_diff_overall"] = max(
            v for v in maxd.values() if v is not None)
        cmp["rebuilt_parquet_sha256"] = hashlib.sha256(
            OUT_PARQUET.read_bytes()).hexdigest()

        res = {
            "schema": "a7_plane_rebuild@1",
            "labels": ["A7_INDEPENDENT_REPRODUCTION",
                       "FAILURE_ROOT_CAUSE_RESEARCH",
                       "DIAGNOSTIC_OUTCOME_EXPOSED"],
            "corpus_readonly": str(CORPUS),
            "manifest": str(MANIFEST),
            "day_files_processed": len(bid_files),
            "full_corpus_sha_verified": len(bid_files) * 2,
            "sha_mismatches": sha_bad,
            "days_short_records": n_short,
            "bars15_anc_rows": int(len(df15)),
            "bars15_duplicate_ts": dup,
            "bars1h_anc_rows": int(len(h1)),
            "comparison_vs_audited": cmp,
            "verdict": "PASS" if (cmp["row_count_equal"] and cmp["ts_equal"]
                                  and cmp["max_abs_diff_overall"] <= 1e-9
                                  and not sha_bad and dup == 0)
                        else "DIFFS",
        }
        (RESULTS / "a7_plane_rebuild.json").write_text(
            json.dumps(res, indent=1) + "\n")
        print(json.dumps({k: res[k] for k in
                          ("day_files_processed", "bars15_anc_rows",
                           "bars1h_anc_rows", "verdict")}))
        print(json.dumps(cmp["max_abs_diff"]))
        status = "FINISHED" if res["verdict"] == "PASS" else "FAILED"
        note = "" if status == "FINISHED" else f"verdict {res['verdict']}"
        return 0 if status == "FINISHED" else 1
    except Exception as e:  # noqa: BLE001
        status, note = "FAILED", f"{type(e).__name__}: {e}"[:400]
        raise
    finally:
        if lock is not None:
            lock.release(status=status, note=note)


if __name__ == "__main__":
    sys.exit(main())
