"""VERIFY-A7READY T2 — NQ spot-recomputes from the COMMITTED cache_v3 parquets.

(a) panel row count == 6,780,608 and id-16908 pre-2020-06-01 rows
    (the relabeled NQM0 alias window) count == 92,075 — counted directly off
    nq_outright_1m_v3.parquet (instrument_id + ts_event columns; raw_symbol
    NOT used so the count is independent of the relabel).
(b) held chain v3 roll count == 66 and the NQH0_2020->NQM0_2020 roll dated
    2020-03-19 (first session NQM0_2020 held), from held_volume_k5_v3.parquet.
(c) cease_guard_audit.json claims: recompute the BEFORE violation from the
    baseline cache FUTURES-DEEPRESEARCH-V2-20261003/analysis/NQ_cache/
    held_volume_k5.parquet — count sessions 2020-03-27..2020-05-29 with
    held == NQH0_2020 (expect 49) plus the audit's own window 03-23..05-29.
(d) reproduction.json digests: recompute the held-chain digest with the SAME
    method as nq_reproduce_digest.py (sorted fixed-dtype CSV sha256) and
    compare; also recompute sessions digest + panel summary.
Writes verify/nq_recompute.json. Read-only everywhere.
"""
import hashlib
import json
import os

import pandas as pd

WT = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness/prep"
ROUND = os.path.join(WT, "research/control/FUTURES-SIX-READINESS-20261004")
V3 = os.path.join(ROUND, "nq/cache_v3")
BASE = os.path.join(WT, "research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/NQ_cache")
CUT = pd.Timestamp("2020-06-01", tz="UTC")

res = {"schema": "verify_nq_recompute@1", "inputs": {}, "checks": {}}

# ---------- (a) panel ----------
panel_path = os.path.join(V3, "nq_outright_1m_v3.parquet")
res["inputs"]["panel_sha256_file_bytes"] = hashlib.sha256(
    open(panel_path, "rb").read()).hexdigest()
t = pd.read_parquet(panel_path, columns=["ts_event", "instrument_id", "raw_symbol"])
n_rows = len(t)
dtu = pd.to_datetime(t["ts_event"], unit="ns", utc=True)
m_alias = (t["instrument_id"] == 16908) & (dtu < CUT)
n_alias = int(m_alias.sum())
vol_alias = None
if "volume" in pd.read_parquet(panel_path).columns or True:
    vv = pd.read_parquet(panel_path, columns=["volume"])
    vol_alias = int(vv.loc[m_alias, "volume"].sum())
# those alias rows must all carry raw_symbol NQM0 in the committed cache
sym_vals = t.loc[m_alias, "raw_symbol"].unique().tolist()
res["checks"]["a_panel"] = {
    "rows": n_rows, "rows_expect": 6780608, "rows_ok": n_rows == 6780608,
    "id16908_pre_cutover_rows": n_alias, "expect": 92075,
    "ok": n_alias == 92075,
    "alias_volume": vol_alias, "alias_volume_expect": 24686121,
    "volume_ok": vol_alias == 24686121,
    "raw_symbols_on_alias_rows": sym_vals,
    "alias_rows_labeled_NQM0": sym_vals == ["NQM0"],
}
del t

# ---------- (b) held chain v3 rolls ----------
hc = pd.read_parquet(os.path.join(V3, "held_volume_k5_v3.parquet"))
hc = hc.sort_values("session_date").reset_index(drop=True)
held = hc["held"].astype(str)
switch = held != held.shift()
# first row is not a roll
roll_idx = hc.index[switch & (hc.index > 0)]
rolls = [{"session_date": str(hc.loc[i, "session_date"]),
          "from": held[i - 1], "to": held[i]} for i in roll_idx]
target = [r for r in rolls if r["from"] == "NQH0_2020" and r["to"] == "NQM0_2020"]
res["checks"]["b_rolls_v3"] = {
    "sessions": int(len(hc)),
    "roll_count": len(rolls), "expect": 66, "ok": len(rolls) == 66,
    "NQH0_to_NQM0_rolls": target,
    "expected": {"from": "NQH0_2020", "to": "NQM0_2020", "session_date": "2020-03-19"},
    "ok_target": len(target) == 1 and target[0]["session_date"].startswith("2020-03-19"),
}
# cg chain roll count too
hcg = pd.read_parquet(os.path.join(V3, "held_volume_k5_cg_v3.parquet")).sort_values("session_date")
h_cg = hcg["held"].astype(str)
sw_cg = h_cg != h_cg.shift()
res["checks"]["b_rolls_v3_cg"] = {
    "sessions": int(len(hcg)), "roll_count": int(sw_cg.sum() - 1),
}
# which sessions did NQM0_2020 get held from?
first_nqm0 = hc.loc[held == "NQM0_2020", "session_date"].min()
res["checks"]["b_rolls_v3"]["first_NQM0_2020_session"] = str(first_nqm0)

# ---------- (c) BEFORE violation from baseline cache ----------
bp = os.path.join(BASE, "held_volume_k5.parquet")
res["inputs"]["baseline_held_k5_path"] = bp
res["inputs"]["baseline_held_k5_exists"] = os.path.exists(bp)
if os.path.exists(bp):
    b = pd.read_parquet(bp)
    b["session_date"] = pd.to_datetime(b["session_date"])
    bh = b["held"].astype(str)
    win_task = b[(b["session_date"] >= "2020-03-27") & (b["session_date"] <= "2020-05-29")]
    n_task = int((win_task["held"].astype(str) == "NQH0_2020").sum())
    win_audit = b[(b["session_date"] >= "2020-03-23") & (b["session_date"] <= "2020-05-29")]
    n_audit = int((win_audit["held"].astype(str) == "NQH0_2020").sum())
    # dead window: sessions after cessation 2020-03-20 through 2020-05-29
    win_dead = b[(b["session_date"] > "2020-03-20") & (b["session_date"] <= "2020-05-29")]
    n_dead = int((win_dead["held"].astype(str) == "NQH0_2020").sum())
    last_nqh0 = b.loc[bh == "NQH0_2020", "session_date"].max()
    res["inputs"]["baseline_held_k5_rows"] = int(len(b))
    res["checks"]["c_before_violation"] = {
        "n_held_NQH0_2020_2020-03-27..05-29": n_task, "expect": 49,
        "ok": n_task == 49,
        "n_held_NQH0_2020_2020-03-23..05-29 (audit window)": n_audit,
        "n_held_NQH0_2020_dead window >2020-03-20..05-29": n_dead,
        "last_NQH0_2020_session": str(last_nqh0),
        "audit_json_claims": {"n_violations_before": 1,
                              "dead_held_sessions": 49,
                              "first_held": "2019-12-18", "last_held": "2020-05-29"},
        "audit_json_consistent": (n_audit == 49 and n_dead == 49),
    }

# ---------- (d) digest recompute (same method as lane) ----------
def chain_digest(path):
    h = pd.read_parquet(path).sort_values("session_date").reset_index(drop=True)
    key = h[["session_date", "held"]].copy()
    key["session_date"] = key["session_date"].astype(str)
    key["held"] = key["held"].astype(str)
    csv = key.to_csv(index=False).encode()
    return {"sha256": hashlib.sha256(csv).hexdigest(), "rows": int(len(key))}

def sessions_digest(path):
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

rep = json.load(open(os.path.join(ROUND, "nq/reproduction.json")))
mine = {
    "held_volume_k5_v3": chain_digest(os.path.join(V3, "held_volume_k5_v3.parquet")),
    "held_volume_k5_cg_v3": chain_digest(os.path.join(V3, "held_volume_k5_cg_v3.parquet")),
    "nq_sessions_v3": sessions_digest(os.path.join(V3, "nq_sessions_v3.parquet")),
}
claim = {k: v["run1"] for k, v in rep["digest_checks"].items()}
digest_cmp = {}
for k in mine:
    digest_cmp[k] = {"mine": mine[k], "lane_claim": claim.get(k),
                     "match": mine[k] == claim.get(k)}
res["checks"]["d_digests"] = digest_cmp
res["checks"]["d_all_match"] = all(v["match"] for v in digest_cmp.values())
# also compare the run1 stash copies byte-wise to the live chain files
import filecmp
stash = os.path.join(V3, "_repro_run1")
res["checks"]["d_stash_vs_live_byte_equal"] = {
    f: filecmp.cmp(os.path.join(stash, f), os.path.join(V3, f), shallow=False)
    for f in ("held_volume_k5_v3.parquet", "held_volume_k5_cg_v3.parquet")}

out = os.path.join(ROUND, "verify", "nq_recompute.json")
with open(out, "w") as fh:
    json.dump(res, fh, indent=1)
print(json.dumps(res["checks"], indent=1, default=str))
