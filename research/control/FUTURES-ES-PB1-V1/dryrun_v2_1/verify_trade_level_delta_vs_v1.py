#!/usr/bin/env python
# DRYRUN-V2-1 post-hoc verification (M2(d) deep check): v2.1 per-identity trade
# lists must equal the v1 quarantine trade lists minus EXACTLY the trades dated
# 2015-07-02 (the v2 freeze repair), with every common trade BYTE-IDENTICAL
# (including sl_distance_pts — donor-set restored to v1's 139). Any other
# difference = CRITICAL (reported, never fixed by this lane).
# v1 dryrun/quarantine/ is HISTORY: read-only. QUARANTINED descriptive-only.
import hashlib, json

WT = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-es-reg/prep"
V1 = WT + "/research/control/FUTURES-ES-PB1-V1/dryrun/quarantine"
V21 = WT + "/research/control/FUTURES-ES-PB1-V1/dryrun_v2_1/quarantine"
HDR = ("QUARANTINED DESCRIPTIVE-ONLY — NOT SCORED — ZERO DENOMINATOR CONSUMPTION — "
       "pre-GO rehearsal per registered plan §4 gate 4")

def canon(t):
    return json.dumps(t, sort_keys=True, separators=(",", ":"))

digest = json.load(open(V21 + "/../dryrun_v2_1_digest.json"))
ids = list(json.load(open(WT + "/research/control/FUTURES-ES-PB1-V1/"
                         "repair/selection_freeze_v2.json"))
           ["identity_table"]["embedded"]["identities"][i]["id"] for i in range(24))

rows, all_ok, n_common, n_removed, n_sl_diff, mismatches = [], True, 0, 0, 0, []
for iid in ids:
    v1t = json.load(open(f"{V1}/{iid}.json"))["trades"]
    v2t = json.load(open(f"{V21}/{iid}.json"))["trades"]
    rem = [t for t in v1t if t["session_date"] == "2015-07-02"]
    kept = [t for t in v1t if t["session_date"] != "2015-07-02"]
    same_len = len(kept) == len(v2t)
    diff_at = [i for i, (a, b) in enumerate(zip(kept, v2t)) if canon(a) != canon(b)]
    ok = same_len and not diff_at
    n_common += len(kept)
    n_removed += len(rem)
    sl_diff = sum(1 for a, b in zip(kept, v2t)
                  if a.get("sl_distance_pts") != b.get("sl_distance_pts"))
    n_sl_diff += sl_diff
    for i in diff_at[:3]:
        mismatches.append({"identity": iid, "position": i,
                           "v1": kept[i], "v2_1": v2t[i]})
    all_ok = all_ok and ok
    rows.append({"identity": iid, "v1_trades": len(v1t), "v2_1_trades": len(v2t),
                 "removed_2015_07_02": len(rem),
                 "common_trades": len(kept),
                 "common_trade_dicts_value_identical": ok,
                 "sl_distance_differences_on_common": sl_diff})

out = {
    "quarantine": HDR,
    "check": "M2(d) deep trade-level delta vs v1 quarantine: v2.1 trade list == "
             "v1 trade list minus EXACTLY the 2015-07-02 trades; every common "
             "trade byte-identical (canonical JSON), sl_distance_pts identical "
             "on all common trades; ANY other difference = CRITICAL",
    "v1_baseline_dir": V1,
    "law": "donor-excluded set restored to v1's 139 sessions (D-V2-1 correction "
           "C1); the ONLY permitted surface change is the v2 freeze repair "
           "removing eval session 2015-07-02 (3 trades: PLA/ALW/DOSE D0-S2)",
    "n_common_trades_compared": n_common,
    "n_trades_removed_total": n_removed,
    "n_sl_distance_differences_on_common_trades": n_sl_diff,
    "per_identity": rows,
    "mismatch_samples": mismatches,
    "verdict": "PASS" if (all_ok and n_removed == 3 and n_sl_diff == 0) else "FAIL",
}
with open(V21 + "/../trade_level_delta_vs_v1.json", "w") as f:
    json.dump(out, f, indent=1, sort_keys=True)
print(json.dumps({k: out[k] for k in
                  ("verdict", "n_common_trades_compared",
                   "n_trades_removed_total",
                   "n_sl_distance_differences_on_common_trades")}, indent=1))
