"""NQ-ALIAS-REPAIR Task 6 — independent reproduction harness.

Usage:
  python nq_reproduce_digest.py save    # digest + stash run-1 artifacts
  python nq_reproduce_digest.py check   # re-digest after a FRESH full rebuild
                                        # (run 2), compare, assert_frame_equal

Deterministic logical-equality method (parquet byte-equality NOT required):
  * held chains (plain k5 + cease-guard): sorted, fixed-dtype CSV of the key
    columns (session_date, held) -> sha256;
  * sessions table key columns (contract, session_date, close, volume):
    sorted, fixed dtypes -> sha256;
  * panel: row count + ts min/max;
  * held chains additionally compared with pandas.testing.assert_frame_equal
    against the run-1 stash (check_exact dtypes, no fp relaxation needed —
    the chain columns are dates + strings).
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys

import pandas as pd
from pandas.testing import assert_frame_equal

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.join(HERE, "cache_v3")
STASH = os.path.join(V3, "_repro_run1")


def chain_digest(path: str) -> dict:
    h = pd.read_parquet(path).sort_values("session_date").reset_index(drop=True)
    key = h[["session_date", "held"]].copy()
    key["session_date"] = key["session_date"].astype(str)
    key["held"] = key["held"].astype(str)
    csv = key.to_csv(index=False).encode()
    return {"sha256": hashlib.sha256(csv).hexdigest(), "rows": int(len(key))}


def sessions_digest(path: str) -> dict:
    s = pd.read_parquet(path)
    key = s.sort_values(["contract", "session_date"]).reset_index(drop=True)
    fixed = pd.DataFrame({
        "contract": key["contract"].astype(str),
        "session_date": key["session_date"].astype(str),
        "close": key["close"].astype("float64"),
        "volume": key["volume"].astype("int64"),
    })
    csv = fixed.to_csv(index=False).encode()
    return {"sha256": hashlib.sha256(csv).hexdigest(), "rows": int(len(fixed))}


def panel_summary(path: str) -> dict:
    import pyarrow.parquet as pq
    m = pq.read_metadata(path)
    t = pq.read_table(path, columns=["ts_event"])
    ts = pd.to_datetime(t["ts_event"], unit="ns", utc=True)
    return {"rows": int(m.num_rows), "ts_min": str(ts.min()), "ts_max": str(ts.max())}


def compute() -> dict:
    return {
        "held_volume_k5_v3": chain_digest(os.path.join(V3, "held_volume_k5_v3.parquet")),
        "held_volume_k5_cg_v3": chain_digest(os.path.join(V3, "held_volume_k5_cg_v3.parquet")),
        "nq_sessions_v3": sessions_digest(os.path.join(V3, "nq_sessions_v3.parquet")),
        "panel": panel_summary(os.path.join(V3, "nq_outright_1m_v3.parquet")),
    }


def main() -> None:
    mode = sys.argv[1]
    out_path = os.path.join(HERE, "reproduction.json")
    if mode == "save":
        os.makedirs(STASH, exist_ok=True)
        dig = compute()
        for f in ("held_volume_k5_v3.parquet", "held_volume_k5_cg_v3.parquet"):
            shutil.copy2(os.path.join(V3, f), os.path.join(STASH, f))
        with open(os.path.join(STASH, "run1_digests.json"), "w") as fh:
            json.dump(dig, fh, indent=1)
        print(json.dumps(dig, indent=1))
        print("run-1 digests + chain stash saved")
        return
    # check mode
    run1 = json.load(open(os.path.join(STASH, "run1_digests.json")))
    run2 = compute()
    checks = {}
    for k in run1:
        checks[k] = {
            "run1": run1[k], "run2": run2[k],
            "identical": run1[k] == run2[k]}
    afe = {}
    for f in ("held_volume_k5_v3.parquet", "held_volume_k5_cg_v3.parquet"):
        a = pd.read_parquet(os.path.join(STASH, f))
        b = pd.read_parquet(os.path.join(V3, f))
        try:
            assert_frame_equal(a, b, check_exact=True)
            afe[f] = "PASS"
        except AssertionError as e:
            afe[f] = f"FAIL: {e}"
    res = {
        "schema": "nq_reproduction@1", "lane": "NQ-ALIAS-REPAIR",
        "method": "two independent full-rebuild executions in fresh python "
                  "processes (nq_rebuild_v3.py all: raw parquet load -> view "
                  "rule -> registry -> annotate -> sessions -> held chains); "
                  "logical equality via sorted fixed-dtype CSV sha256 of "
                  "chain key columns (session_date, held) + sessions key "
                  "columns (contract, session_date, close, volume) + panel "
                  "row-count/ts-min-max + assert_frame_equal(check_exact) on "
                  "both held chains; parquet byte equality NOT required",
        "digest_checks": checks,
        "assert_frame_equal": afe,
        "verdict": ("REPRODUCED" if all(c["identical"] for c in checks.values())
                    and all(v == "PASS" for v in afe.values())
                    else "MISMATCH"),
    }
    with open(out_path, "w") as fh:
        json.dump(res, fh, indent=1)
    print(json.dumps({k: c["identical"] for k, c in checks.items()}, indent=1))
    print(afe)
    print("verdict:", res["verdict"])


if __name__ == "__main__":
    main()
