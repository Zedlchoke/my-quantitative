"""VERIFY-A7READY T8 — gates + language scan over ALL round outputs
(nq/es/fx_eb/fx_ja *.md + *.json) for forbidden positive claims:
'scored', 'GO', 'edge', 'profitable', 'PnL positive' — expect only
negations/status uses. Also: S1/sealed mentions (expect 0), order/live/paper
claims (inspect), standing rulings restated (ES 24 frozen, PB2 HOLD, PB3 PARK,
6F NOT_RUN_DATA_ABSENT).
Writes verify/language_scan.json.
"""
import glob
import json
import os
import re

WT = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness/prep"
ROUND = os.path.join(WT, "research/control/FUTURES-SIX-READINESS-20261004")
LANES = ["nq", "es", "fx_eb", "fx_ja"]

TOKENS = {
    "scored": re.compile(r"\bscored\b", re.I),
    "GO": re.compile(r"\bGO\b"),
    "edge": re.compile(r"\bedge\b", re.I),
    "profitable": re.compile(r"\bprofitable\b", re.I),
    "PnL": re.compile(r"\bPnL\b", re.I),
    "S1": re.compile(r"\bS1\b"),
    "sealed": re.compile(r"\bsealed\b", re.I),
    "order": re.compile(r"\border(?:s|ed|ing)?\b", re.I),
    "live": re.compile(r"\blive\b", re.I),
    "paper": re.compile(r"\bpaper\b", re.I),
}

NEGATORS = ("no ", "not ", "never ", "zero ", "n't", "without", "forbidden",
            "≠", "!=", "NO_", "NOT_", "non-", "un-", " != ")
def classify(ctx):
    c = ctx.lower()
    # explicit negation within the context window, else 'inspect'
    if any(n in c for n in [x.lower() for x in NEGATORS]):
        return "NEGATION_OR_STATUS"
    return "INSPECT"

res = {"schema": "verify_language_scan@1", "scanned": {}, "hits": {},
       "standing_rulings": {}}

n_files = 0
for lane in LANES:
    files = sorted(glob.glob(f"{ROUND}/{lane}/**/*.md", recursive=True) +
                   glob.glob(f"{ROUND}/{lane}/**/*.json", recursive=True))
    n_files += len(files)
    lane_hits = {}
    for p in files:
        try:
            text = open(p, errors="replace").read()
        except Exception:
            continue
        for tok, rx in TOKENS.items():
            for m in rx.finditer(text):
                ctx = text[max(0, m.start() - 110): m.start() + 130]
                ctx = ctx.replace("\n", " ")
                lane_hits.setdefault(tok, []).append({
                    "file": p.replace(ROUND + "/", ""),
                    "ctx": ctx,
                    "class": classify(ctx),
                })
    res["hits"][lane] = lane_hits
res["scanned"] = {"n_files": n_files, "lanes": LANES}

for tok in res["hits"].get("nq", {}) and TOKENS:
    tot = 0
    inspect = 0
    for lane in LANES:
        for h in res["hits"][lane].get(tok, []):
            tot += 1
            if h["class"] == "INSPECT":
                inspect += 1
    res.setdefault("totals", {})[tok] = {"hits": tot, "inspect": inspect}

# standing rulings
es_cen = json.load(open(f"{ROUND}/es/es_trial_census.json"))
fee = json.load(open(f"{ROUND}/es/es_fee_status.json"))
fxeb_pb2 = json.load(open(f"{ROUND}/fx_eb/pb2/pb2_restate.json"))
fxja_r = json.load(open(f"{ROUND}/fx_ja/fx_ja_readiness.json"))
s_fxja = json.dumps(fxja_r)
s_fxeb = json.dumps(json.load(open(f"{ROUND}/fx_eb/fx_eb_readiness.json")))
res["standing_rulings"] = {
    "es_24_frozen": {
        "present": bool(re.search(r"24", json.dumps(es_cen))),
        "n_frozen_ids_field": es_cen.get("frozen_identities") or
        es_cen.get("frozen") or "check-keys",
        "keys": list(es_cen.keys()),
    },
    "pb2_hold": {"present_in_fxeb": "HOLD" in json.dumps(fxeb_pb2),
                 "keys": list(fxeb_pb2.keys()) if isinstance(fxeb_pb2, dict) else "?"},
    "pb3_park_6a": {"present": "PARK" in s_fxja},
    "six_f_not_run_data_absent": {
        "present_in_fxeb": "NOT_RUN_DATA_ABSENT" in s_fxeb or "6F" in s_fxeb,
        "present_in_fxja": "NOT_RUN_DATA_ABSENT" in s_fxja,
    },
}

with open(f"{ROUND}/verify/language_scan.json", "w") as fh:
    json.dump(res, fh, indent=1, default=str)
print("files scanned:", n_files)
for tok, t in res.get("totals", {}).items():
    print(f"{tok:12s} hits={t['hits']:4d} inspect={t['inspect']}")
print("standing:", json.dumps({k: (v.get('present') or v.get('present_in_fxeb') or v.get('present_in_fxja')) if isinstance(v, dict) else v for k, v in res['standing_rulings'].items()}, default=str))
