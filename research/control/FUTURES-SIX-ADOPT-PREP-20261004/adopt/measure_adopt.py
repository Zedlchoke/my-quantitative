"""ADOPT lane re-measurement — FUTURES-SIX-ADOPT-PREP-20261004.

Measures EVERYTHING itself from committed bytes; round-1 JSONs are used ONLY
as claims to compare against (deltas recorded, never trusted).

Reads:
  * <READINESS>/nq/cache_v3/**            (live + _repro_run1 stash)
  * <DEEPRESEARCH-V2>/analysis/NQ_cache/* (baseline v2 caches, read-only)
Writes:
  * adopt/cache_v3_hashes.json  (sha256 of every cache_v3 file + re-measures + deltas)
No other writes. No network. No PnL.
"""
from __future__ import annotations

import hashlib
import json
import os

import pandas as pd
import pyarrow.parquet as pq
from pandas.testing import assert_frame_equal

WT = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-adopt/prep"
READY = os.path.join(WT, "research/control/FUTURES-SIX-READINESS-20261004")
V3 = os.path.join(READY, "nq/cache_v3")
STASH = os.path.join(V3, "_repro_run1")
V2 = os.path.join(WT, "research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/NQ_cache")
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "cache_v3_hashes.json")

ALIAS_CUTOVER = pd.Timestamp("2020-06-01", tz="UTC")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def hash_tree(root: str) -> dict:
    out = {}
    for dirpath, _dirs, files in os.walk(root):
        for fn in sorted(files):
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, root)
            out[rel] = {"sha256": sha256_file(p), "bytes": os.path.getsize(p)}
    return out


# ---- lane's disclosed digest method (verbatim re-implementation) -----------
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
    m = pq.read_metadata(path)
    t = pq.read_table(path, columns=["ts_event"])
    ts = pd.to_datetime(t["ts_event"], unit="ns", utc=True)
    return {"rows": int(m.num_rows), "ts_min": str(ts.min()), "ts_max": str(ts.max())}


def main() -> None:
    res: dict = {"schema": "adopt_cache_v3_hashes@1",
                 "cycle": "FUTURES-SIX-ADOPT-PREP-20261004",
                 "lane": "ADOPT",
                 "worktree": WT,
                 "method_note": "all values below measured by THIS lane from committed bytes; "
                                "round-1 JSONs read only as claims to diff"}

    # 1. hashes -----------------------------------------------------------------
    res["hashes_live"] = hash_tree(V3)
    res["hashes_repro_run1"] = hash_tree(STASH)
    # stash-vs-live byte equality for the two stashed chains
    stash_eq = {}
    for f in ("held_volume_k5_v3.parquet", "held_volume_k5_cg_v3.parquet"):
        stash_eq[f] = (res["hashes_live"][f]["sha256"]
                       == res["hashes_repro_run1"][f]["sha256"])
    res["stash_vs_live_byte_equal"] = stash_eq

    # 2. lane-method digests ----------------------------------------------------
    dig = {
        "held_volume_k5_v3": chain_digest(os.path.join(V3, "held_volume_k5_v3.parquet")),
        "held_volume_k5_cg_v3": chain_digest(os.path.join(V3, "held_volume_k5_cg_v3.parquet")),
        "nq_sessions_v3": sessions_digest(os.path.join(V3, "nq_sessions_v3.parquet")),
        "panel": panel_summary(os.path.join(V3, "nq_outright_1m_v3.parquet")),
    }
    res["digests_recomputed"] = dig
    run1 = json.load(open(os.path.join(STASH, "run1_digests.json")))
    repro = json.load(open(os.path.join(READY, "nq/reproduction.json")))
    deltas = {}
    for k, v in dig.items():
        deltas[k] = {
            "adopt_remeasure": v,
            "round1_run1": run1.get(k),
            "round1_run2": (repro.get("digest_checks", {}).get(k, {}).get("run2")
                            if isinstance(repro.get("digest_checks", {}).get(k), dict) else None),
            "match_run1": v == run1.get(k),
        }
    res["deltas_vs_round1"] = deltas

    # 3. panel re-verify: id-16908 pre-cutover ----------------------------------
    t = pq.read_table(os.path.join(V3, "nq_outright_1m_v3.parquet"),
                      columns=["instrument_id", "raw_symbol", "ts_event", "volume"])
    df = t.to_pandas()
    df["ts"] = pd.to_datetime(df["ts_event"], unit="ns", utc=True)
    m16908 = df["instrument_id"] == 16908
    pre = df[m16908 & (df["ts"] < ALIAS_CUTOVER)]
    post = df[m16908 & (df["ts"] >= ALIAS_CUTOVER)]
    res["id16908"] = {
        "pre_cutover_rows": int(len(pre)),
        "pre_cutover_volume": int(pre["volume"].sum()),
        "pre_cutover_raw_symbols": sorted(pre["raw_symbol"].unique().tolist()),
        "pre_cutover_all_NQM0": bool((pre["raw_symbol"] == "NQM0").all()),
        "pre_first_ts": str(pre["ts"].min()), "pre_last_ts": str(pre["ts"].max()),
        "post_cutover_rows": int(len(post)),
        "post_cutover_raw_symbols": sorted(post["raw_symbol"].unique().tolist()),
        "non16908_rows_labeled_NQM0_pre_cutover": int(
            ((df["instrument_id"] != 16908) & (df["ts"] < ALIAS_CUTOVER)
             & (df["raw_symbol"] == "NQM0")).sum()),
        "note": "panel cache dropped raw dash-spread rows at build time; instrument_id retained",
    }

    # 4. held chain + rolls -----------------------------------------------------
    plain = pd.read_parquet(os.path.join(V3, "held_volume_k5_v3.parquet"))
    cg = pd.read_parquet(os.path.join(V3, "held_volume_k5_cg_v3.parquet"))
    rolls = pd.read_parquet(os.path.join(V3, "v3_rolls_spread_stats.parquet"))
    afe = {}
    for name, a, b in (("plain_vs_cg", plain, cg),
                       ("plain_vs_stash", plain,
                        pd.read_parquet(os.path.join(STASH, "held_volume_k5_v3.parquet"))),
                       ("cg_vs_stash", cg,
                        pd.read_parquet(os.path.join(STASH, "held_volume_k5_cg_v3.parquet")))):
        try:
            assert_frame_equal(a, b, check_exact=True)
            afe[name] = "PASS"
        except AssertionError as e:
            afe[name] = f"FAIL: {str(e)[:200]}"
    res["chains"] = {
        "plain_rows": int(len(plain)), "cg_rows": int(len(cg)),
        "assert_frame_equal": afe,
        "n_rolls": int(len(rolls)),
        "target_roll": rolls.loc[(rolls["old"] == "NQH0_2020") & (rolls["new"] == "NQM0_2020"),
                                 ["roll_session", "days_to_expiry",
                                  "old_volume_roll_day", "new_volume_roll_day"]].to_dict("records"),
        "first_roll": rolls.iloc[0][["roll_session", "old", "new"]].to_dict(),
        "last_roll": rolls.iloc[-1][["roll_session", "old", "new"]].to_dict(),
    }

    # 5. baseline v2 caches (read-only metadata + small loads) -------------------
    v2 = {}
    p2 = pq.read_metadata(os.path.join(V2, "nq_outright_1m.parquet"))
    v2["nq_outright_1m_rows"] = int(p2.num_rows)
    h2 = pd.read_parquet(os.path.join(V2, "held_volume_k5.parquet"))
    v2["held_volume_k5_rows"] = int(len(h2))
    h2["session_date"] = h2["session_date"].astype(str)
    win = h2[(h2["session_date"] >= "2020-03-23") & (h2["session_date"] <= "2020-05-29")]
    v2["dead_held_sessions_2020_03_23__05_29"] = int((win["held"] == "NQH0_2020").sum())
    v2["held_2020_05_29"] = str(win[win["session_date"] == "2020-05-29"]["held"].iloc[0])
    v2["held_2020_06_01"] = str(h2[h2["session_date"] == "2020-06-01"]["held"].iloc[0])
    v2["nan_close_sessions_window"] = None  # filled below if close column exists
    s2 = pq.read_metadata(os.path.join(V2, "nq_sessions.parquet"))
    v2["nq_sessions_rows"] = int(s2.num_rows)
    try:
        hd2 = pd.read_parquet(os.path.join(V2, "nq_held_daily.parquet"))
        v2["nq_held_daily_rows"] = int(len(hd2))
        hd2["d"] = pd.to_datetime(hd2["d"]).astype(str)  # date col is named 'd'
        w = hd2[(hd2["d"] >= "2020-03-23") & (hd2["d"] <= "2020-05-29")]
        v2["nan_close_sessions_window"] = int(w["close"].isna().sum()) if len(w) else None
        v2["depleted_sessions_window"] = int(w["depleted"].sum()) if "depleted" in w else None
    except Exception as e:  # noqa: BLE001
        v2["nq_held_daily_rows"] = f"ERR {type(e).__name__}"
    res["baseline_v2_readonly_remeasure"] = v2

    # 6. v3 sessions + registry sanity ------------------------------------------
    res["sessions_rows"] = int(pq.read_metadata(
        os.path.join(V3, "nq_sessions_v3.parquet")).num_rows)
    reg = json.load(open(os.path.join(V3, "contract_registry_v3.json")))
    res["registry_clusters"] = int(len(reg))

    with open(OUT, "w") as fh:
        json.dump(res, fh, indent=1, default=str)

    # console summary
    print("hashes: live", len(res["hashes_live"]), "repro_run1", len(res["hashes_repro_run1"]))
    print("stash byte-equal:", stash_eq)
    for k, d in deltas.items():
        print(f"delta[{k}] match_run1={d['match_run1']} adopt={d['adopt_remeasure']}")
    print("id16908:", json.dumps(res["id16908"], indent=1))
    print("chains:", json.dumps(res["chains"], indent=1, default=str))
    print("v2:", json.dumps(v2, indent=1, default=str))
    print("sessions_rows", res["sessions_rows"], "registry", res["registry_clusters"])


if __name__ == "__main__":
    main()
