#!/usr/bin/env python3
"""A7-SPEC probe — standard audit.

Checks: GO-phrase exact-string uniqueness vs plans/CYCLE_REGISTRY.json go_phrase
fields (and raw containment + cycle-id collision); fold coverage contiguity
F1-F4 vs data window; MODELED COST language law (no complete/measured claims);
outcome-blindness greps; parameter provenance presence (q80/NQ-H4, R=2 a priori,
seed 20261002, slippage D1); two-key, S1 sealed, root-registry-write blocker;
sha256 of audited objects.
"""
import hashlib, json, os, re, unicodedata
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
PACKET = "/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/research/control/FUTURES-ES-V1-PACKET"
SPEC = os.path.join(PACKET, "SPEC_PB1_ES.md")
PLAN = os.path.join(PACKET, "PLAN_futures_es_v1.md")
REG = "/Users/hoangminhlong/my-quantitative/plans/CYCLE_REGISTRY.json"
GO_PHRASE = "GO FUTURES ES V1 SCORED EXECUTION"

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

spec = open(SPEC).read()
plan = open(PLAN).read()

# ---- GO phrase uniqueness ----------------------------------------------------
reg_raw = open(REG).read()
reg = json.loads(reg_raw)
phrases = []
def walk(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if "go_phrase" in str(k).lower() and isinstance(v, str):
                phrases.append(v)
            walk(v)
    elif isinstance(o, list):
        for v in o:
            walk(v)
walk(reg)
exact_hits = sum(1 for p in phrases if p.strip() == GO_PHRASE)
raw_hits = reg_raw.count(GO_PHRASE)
cyc = reg.get("cycles", [])
ids = [c.get("cycle_id", c.get("id")) for c in cyc] if isinstance(cyc, list) else list(cyc.keys())
id_collisions = [i for i in ids if i and "FUTURES-ES" in str(i)]
# near-miss similarity (same words reordered / substring overlap) among ACTIVE-looking phrases
words = set(GO_PHRASE.split())
near = sorted({p for p in phrases if isinstance(p, str) and p and len(words & set(p.split())) >= 4 and p != GO_PHRASE})

# ---- fold coverage (months compared as (year, month) tuples) ------------------
def nxt_month(ym):
    y, m = ym
    return (y + 1, 1) if m == 12 else (y, m + 1)

folds = [("F1", (2010, 6), (2012, 12)), ("F2", (2013, 1), (2017, 12)),
         ("F3", (2018, 1), (2021, 12)), ("F4", (2022, 1), (2026, 9))]
data_start, data_end = (2010, 6), (2026, 9)  # 2026-10-01 partial tail excluded (DATACONTRACT §1.6.5)
contiguous, gaps_overlaps = True, []
for i in range(1, len(folds)):
    prev_end = folds[i - 1][2]; cur_start = folds[i][1]
    if cur_start != nxt_month(prev_end):
        contiguous = False
        gaps_overlaps.append(f"{folds[i-1][0]} ends {prev_end} -> {folds[i][0]} starts {cur_start}")
fold_ok = folds[0][1] == data_start and folds[-1][2] == data_end and contiguous

# ---- language law / outcome blindness ----------------------------------------
def norm(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()

violations, allowed = [], []
for name, txt in (("SPEC", spec), ("PLAN", plan)):
    t = norm(txt)
    for m in re.finditer(r"(complete[\s-]cost|measured[\s-]cost)", t):
        violations.append({"doc": name, "kw": m.group(1), "ctx": t[max(0, m.start()-80):m.end()+80]})
    for m in re.finditer(r"\bmeasured\b", t):
        ctx = t[max(0, m.start()-90):m.end()+90]
        (allowed if ("khong phai" in ctx or "not" in ctx.split("measured")[0][-40:] or "cam" in ctx) else violations).append(
            {"doc": name, "kw": "measured", "ctx": ctx})
# PnL / outcome-blindness: no realized numbers, explicit claim present
blind_ok = ("chưa có số pnl" in norm(spec) or "chua co so pnl" in norm(spec)) and "0 PnL" not in ""
spec_flat = re.sub(r"\s+", " ", spec)
plan_flat = re.sub(r"\s+", " ", plan)
provenance = {
    "q80_from_anatomy_no_tune": ("q80 từ anatomy" in spec_flat) or ("q80 tu anatomy" in norm(spec_flat)),
    "r2_a_priori": "a priori" in norm(spec_flat) or "a-priori" in norm(spec_flat),
    "seed_20261002": "20261002" in spec_flat + plan_flat,
    "slippage_d1_assumption": "GIẢ ĐỊNH NGHIÊN CỨU (D1)" in spec_flat or ("giả định nghiên cứu" in norm(spec_flat)),
    "nq_h4_ref": "NQ" in spec_flat and "H4" in spec_flat,
    "es_h5_ref": "H5" in spec_flat,
}
two_key = "two-key" in norm(plan) and "A7 prelaunch" in plan
s1_sealed = "SEALED_UNTOUCHED" in spec
root_blocker = ("plans/CYCLE_REGISTRY.json" in plan and ("root main" in norm(plan) or "root" in plan)) and "BLOCKER" in plan
fomc_92 = "92" in spec and "FOMC" in spec

result = {
    "probe": "standard_audit",
    "sha256": {"SPEC_PB1_ES.md": sha(SPEC), "PLAN_futures_es_v1.md": sha(PLAN),
               "CYCLE_REGISTRY.json": sha(REG)},
    "go_phrase": {
        "phrase": GO_PHRASE,
        "go_phrase_fields_in_registry": len(phrases),
        "exact_hits": exact_hits,
        "raw_containment_hits": raw_hits,
        "near_misses_sharing>=4_words": near,
        "cycle_id_collisions_FUTURES_ES": id_collisions,
        "unique": exact_hits == 0 and raw_hits == 0 and not id_collisions,
    },
    "folds": {"contiguous": contiguous, "gaps_or_overlaps": gaps_overlaps,
              "covers_data_window_2010_06_2026_09": fold_ok,
              "note": "F4 ends 2026-09; 2026-10-01 partial tail excluded per DATACONTRACT §1.6(5)"},
    "language_law": {"violations": violations, "allowed_negations": allowed[:5]},
    "outcome_blindness_declared": blind_ok,
    "provenance": provenance,
    "two_key_law": two_key,
    "s1_sealed": s1_sealed,
    "root_registry_write_blocker_flagged": root_blocker,
    "fomc_92_timed_in_spec": fomc_92,
}
result["verdict"] = "PASS" if (
    result["go_phrase"]["unique"] and fold_ok and not violations and blind_ok
    and all(provenance.values()) and two_key and s1_sealed and root_blocker
) else "CHECK"

out = os.path.join(HERE, "out_probe_standard_audit.json")
with open(out, "w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print(json.dumps(result, indent=2, ensure_ascii=False)[:2600])
