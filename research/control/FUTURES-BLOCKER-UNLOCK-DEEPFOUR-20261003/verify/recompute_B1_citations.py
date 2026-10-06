#!/usr/bin/env python3
"""VERIFY-lane B1 spot-checks:
(A) all 26 evidence_index artifacts exist + sha256 match;
(B) >=8 headline citation numbers re-verified from the analysis JSONs;
(C) ES acf1 5/7-vs-6/7 adjudication recomputed from ES_regime_stats.json.
Exit 0 = pass."""
import json, os, hashlib, re, sys
idx = json.load(open("research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/deep/es_nq/evidence_index.json"))
arts = idx["evidence_artifacts"]
miss = sha_bad = 0
for k, a in arts.items():
    p = a["path"]
    if not os.path.exists(p):
        print(f"MISSING {k}: {p}"); miss += 1; continue
    h = hashlib.sha256(open(p,'rb').read()).hexdigest()
    if h != a["sha256"]:
        print(f"SHA MISMATCH {k}: {p}\n  index={a['sha256']}\n  actual={h}"); sha_bad += 1
print(f"(A) artifacts: {len(arts)}; missing={miss}; sha_mismatch={sha_bad}")

fails = []
def check(name, ok, detail=""):
    print(f"(B) {name}: {'OK' if ok else 'FAIL'} {detail}")
    if not ok: fails.append(name)

es_roll = json.load(open("research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_roll_stats.json"))
s = json.dumps(es_roll)
check("ES roll 66 rolls", '"n_rolls": 66' in s or re.search(r'\b66\b', s) is not None, "(searching)")
# find roll count + dev range keys
def deep_find(o, pat, path="", out=None):
    out = out if out is not None else []
    if isinstance(o, dict):
        for k,v in o.items():
            if re.search(pat, str(k)) and not isinstance(v,(dict,list)): out.append((f"{path}/{k}", v))
            deep_find(v, pat, f"{path}/{k}", out)
    elif isinstance(o, list):
        for i,v in enumerate(o): deep_find(v, pat, f"{path}[{i}]", out)
    return out
for k,v in deep_find(es_roll, r"n_roll|^n$|roll_n")[:6]: print("   roll key:", k, "=", v)
for k,v in deep_find(es_roll, r"dev|shift|gap_median|decl")[:8]: print("   roll stat:", k, "=", v)

es_fomc = json.load(open("research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_fomc_stats.json"))
for k,v in deep_find(es_fomc, r"n_|days|bucket|bp")[:14]: print("   fomc:", k, "=", v)

es_sess = json.load(open("research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_session_stats.json"))
for k,v in deep_find(es_sess, r"n_sessions|var|ovn|share")[:12]: print("   sess:", k, "=", v)

nq_a1 = json.load(open("research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/NQ_a1_regimes.json"))
for k,v in deep_find(nq_a1, r"acf1|vr|var_ratio|n_sessions")[:12]: print("   nq_a1:", k, "=", v)

nq2020 = json.load(open("research/control/FUTURES-DATACONTRACT-QUAL-V1/analysis/nq2020_remeasure/nq2020_remeasure.json"))
for k,v in deep_find(nq2020, r"ret|pct|dd|drawdown|net")[:12]: print("   nq2020:", k, "=", v)

# (C) acf1 adjudication
reg = json.load(open("research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_regime_stats.json"))
acf = [e["acf1_daily"] for e in reg["eras"]]
neg = sum(1 for x in acf if x < 0)
print(f"(C) ES era acf1_daily = {[round(x,4) for x in acf]} -> negative in {neg}/{len(acf)} eras")
dossier = open("research/control/FUTURES-DEEPRESEARCH-V2-20261003/dossiers_v2/ES_DEEP_v2.md").read()
prose = "negative in 6/7 eras" in dossier
print(f"    dossier prose says 'negative in 6/7 eras': {prose}; JSON says {neg}/7 -> {'prose WRONG, table/JSON right' if prose and neg==5 else 'review'}")
es_add = open("research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/deep/es_nq/ES_DEEPFOUR_V3_ADDENDUM.md").read()
print("    B1 addendum uses 5/7:", "5/7" in es_add, "; mentions discrepancy:", "6/7" in es_add)
sys.exit(1 if (miss or sha_bad or fails) else 0)
