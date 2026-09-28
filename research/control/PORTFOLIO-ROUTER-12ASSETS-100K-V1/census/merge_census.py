#!/usr/bin/env python3
"""A1 integration for PORTFOLIO-ROUTER-12ASSETS-100K-V1 census.

Merges 12 lane TSVs (100 rows each), repairs the known BRENT s_id omission
(mechanical insert derived from gid — no content change), validates globally,
computes the frozen priority rubric (CENSUS_PROTOCOL §5), dedups cross-symbol
by (family, mech_key), writes census/CENSUS_1200.tsv + counts JSON.
Run: python3 merge_census.py  (from anywhere; paths are repo-relative to this file's parent)
"""
import glob, json, os, sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
PARTS = os.path.join(HERE, "parts")
HDR = ["symbol","s_id","gid","family","title_short","mech_key","mechanism","payer_or_flow",
       "horizon","signal_available_at","vehicle","required_pit_data","costs_to_measure",
       "causal_control","ancestry_hits","data_status","verdict","verdict_reason",
       "exemplar_ref","priority_score","source_ref"]
VERDICTS = {"DISTINCT_TESTABLE","VARIANT_OR_DUPLICATE","BLOCKED_DATA","PIT_UNPROVEN","BLOCKED_COST","NOT_FALSIFIABLE"}
DATA_ST = {"HAVE_REPO","PARTIAL_REPO","PUBLIC_UNEVIDENCED","PROSPECTIVE_ONLY","MISSING","NA"}
FAMS = {"A-TREND","B-MEANREV","C-BREAKOUT","D-CARRY_TERM","E-SESSION","F-EVENT","G-XASSET","H-POSITIONING","I-STATARB","J-REGIME_OPT"}

def load_parts():
    rows = []
    incidents = []
    for f in sorted(glob.glob(os.path.join(PARTS, "census_*.tsv"))):
        lines = open(f, encoding="utf-8").read().rstrip("\n").split("\n")
        hdr, body = lines[0].split("\t"), [l.split("\t") for l in lines[1:]]
        if hdr == HDR:
            recs = body
        elif hdr == [h for i,h in enumerate(HDR) if i != 1] and all(len(r)==len(HDR)-1 for r in body):
            # BRENT defect: s_id column omitted -> insert derived from gid
            for r in body: r.insert(1, r[1].split("-S")[-1].join(["S",""]) if False else "S"+r[1].split("-S")[-1])
            recs = body
            incidents.append(f"{os.path.basename(f)}: header/rows missing s_id column; inserted s_id derived from gid (mechanical, no content change)")
        else:
            sys.exit(f"FATAL {f}: unrecognized header/shape")
        if len(recs) != 100:
            sys.exit(f"FATAL {f}: {len(recs)} rows != 100")
        for r in recs:
            if len(r) != 21: sys.exit(f"FATAL {f}: row has {len(r)} cols")
            d = dict(zip(HDR, r))
            if d["verdict"] not in VERDICTS: sys.exit(f"FATAL {f} {d['gid']}: bad verdict {d['verdict']}")
            if d["data_status"] not in DATA_ST: sys.exit(f"FATAL {f} {d['gid']}: bad data_status {d['data_status']}")
            if d["family"] not in FAMS: sys.exit(f"FATAL {f} {d['gid']}: bad family {d['family']}")
            rows.append(d)
    return rows, incidents

def priority(d):
    """Frozen CENSUS_PROTOCOL §5 subscores (deterministic implementation v2,
    aligned to the published formula after skeptic F-3; deviation recorded in
    CENSUS_SUMMARY erratum)."""
    Pmap = {"HAVE_REPO":3,"PARTIAL_REPO":2,"PUBLIC_UNEVIDENCED":1,"PROSPECTIVE_ONLY":0,"MISSING":0,"NA":0}
    P = Pmap[d["data_status"]]
    payer = d["payer_or_flow"].strip()
    mech = d["mechanism"].strip()
    if payer in ("","NA","-"): M = 0
    elif "UNCLEAR" in payer.upper(): M = 1
    elif len(mech) >= 60: M = 3            # payer named + substantive mechanism
    else: M = 2                            # payer named but thin
    ctrl = d["causal_control"].strip()
    if d["verdict"] == "NOT_FALSIFIABLE": F = 0
    elif d["signal_available_at"].strip() in ("","NA","-"): F = 1
    elif len(ctrl) >= 20: F = 3            # decidable timestamp + real control
    else: F = 2                            # decidable timestamp, weak control
    v = d["vehicle"].strip()
    if v in ("","NA","-"): C = 0
    elif "TBC" in v.upper(): C = 1         # vehicle TBD
    else: C = 2                            # vehicle known; components UNMEASURED (incl. FX-spot: spread 1/24 buckets only)
    has_hit = d["ancestry_hits"].strip() not in ("","none-found","NA")
    if d["verdict"]=="VARIANT_OR_DUPLICATE": A = 0       # frozen text: "VARIANT rows inherit 0"
    elif has_hit: A = 1
    else: A = 3
    return round(10.0*(3*P + 2.5*M + 2*F + 1.5*C + 1*A)/32.5, 2)

def main():
    rows, incidents = load_parts()
    gids = [r["gid"] for r in rows]
    assert len(rows) == 1200, len(rows)
    assert len(set(gids)) == 1200, "gid collision"
    # in-file exemplar resolution check (same symbol, same mech_key, exemplar is self)
    by_gid = {r["gid"]: r for r in rows}
    bad_ex = []
    for r in rows:
        e = r["exemplar_ref"]
        if e == "self": continue
        if e not in by_gid: bad_ex.append((r["gid"], e, "missing")); continue
        ex = by_gid[e]
        if ex["symbol"] != r["symbol"] or ex["mech_key"] != r["mech_key"]:
            bad_ex.append((r["gid"], e, "mismatch"))
    for r in rows: r["priority_score"] = str(priority(r))
    # cross-symbol dedup groups
    tier = {"DISTINCT_TESTABLE":0,"PIT_UNPROVEN":1,"BLOCKED_COST":2,"BLOCKED_DATA":3,"NOT_FALSIFIABLE":4,"VARIANT_OR_DUPLICATE":5}
    dsrank = {"HAVE_REPO":0,"PARTIAL_REPO":1,"PUBLIC_UNEVIDENCED":2,"PROSPECTIVE_ONLY":3,"NA":4,"MISSING":5}
    groups = defaultdict(list)
    for r in rows: groups[(r["family"], r["mech_key"])].append(r)
    exemplars = {}
    for k, g in groups.items():
        g2 = sorted(g, key=lambda r: (tier[r["verdict"]], dsrank[r["data_status"]], -float(r["priority_score"]), r["gid"]))
        exemplars[k] = g2[0]["gid"]
    counts = {
        "verdict_total": dict(Counter(r["verdict"] for r in rows)),
        "verdict_by_symbol": {s: dict(Counter(r["verdict"] for r in rows if r["symbol"]==s)) for s in sorted({r['symbol'] for r in rows})},
        "verdict_by_family": {f: dict(Counter(r["verdict"] for r in rows if r["family"]==f)) for f in sorted(FAMS)},
        "data_status_total": dict(Counter(r["data_status"] for r in rows)),
        "mech_keys_global": len(groups),
        "mech_keys_with_distinct_testable_exemplar": sum(1 for k in groups if by_gid[exemplars[k]]["verdict"]=="DISTINCT_TESTABLE"),
        "cross_symbol_groups_over_1": sum(1 for g in groups.values() if len({r['symbol'] for r in g})>1),
        "exemplar_refs_bad": bad_ex,
        "incidents": incidents,
    }
    # shortlist: global exemplars that are DISTINCT_TESTABLE, or PIT_UNPROVEN with named payer (dedup already by group)
    short = []
    for k, g in groups.items():
        ex = by_gid[exemplars[k]]
        named = ex["payer_or_flow"].strip() not in ("","NA","-") and "UNCLEAR" not in ex["payer_or_flow"].upper()
        if ex["verdict"]=="DISTINCT_TESTABLE" or (ex["verdict"]=="PIT_UNPROVEN" and named):
            short.append(ex)
    short.sort(key=lambda r: (-float(r["priority_score"]), r["gid"]))
    counts["shortlist_size"] = len(short)
    # write merged TSV sorted by tier, priority desc, gid
    rows.sort(key=lambda r: (tier[r["verdict"]], -float(r["priority_score"]), r["gid"]))
    out = os.path.join(HERE, "CENSUS_1200.tsv")
    with open(out,"w",encoding="utf-8") as f:
        f.write("\t".join(HDR)+"\n")
        for r in rows: f.write("\t".join(r[h] for h in HDR)+"\n")
    with open(os.path.join(HERE,"counts.json"),"w",encoding="utf-8") as f:
        json.dump(counts, f, ensure_ascii=False, indent=1)
    with open(os.path.join(HERE,"shortlist.tsv"),"w",encoding="utf-8") as f:
        f.write("\t".join(HDR)+"\n")
        for r in short: f.write("\t".join(r[h] for h in HDR)+"\n")
    print("merged rows:", len(rows), "->", out)
    print("verdict_total:", counts["verdict_total"])
    print("mech_keys_global:", counts["mech_keys_global"], "| shortlist:", counts["shortlist_size"])
    print("bad exemplar refs:", len(bad_ex))
    print("incidents:", incidents)

if __name__ == "__main__":
    main()
