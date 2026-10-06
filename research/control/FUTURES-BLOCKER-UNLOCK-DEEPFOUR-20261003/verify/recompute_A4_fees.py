#!/usr/bin/env python3
"""VERIFY-lane independent recompute of A4-FEES all-in rows from components.
ALL_IN_COMPUTED(row) must equal commission(row) + EXCHANGE_FEE_OFFSET(code) + REGULATORY_FEE_OFFSET_NFA(code).
Also enforces the label law (SOURCE=PUBLIC_REFERENCE, VERIFIED_VS_ACCOUNT=NOT_RUN) on every row.
Exit 0 = pass."""
import json, sys
d = json.load(open("research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/fees/fees_table_all.json"))
rf = d["rows_flat"]
fails, label_fail = [], []
exch, reg = {}, {}
allin = []
for r in rf:
    if r["component"] == "EXCHANGE_FEE_OFFSET": exch[r["code"]] = r["value_usd"]
    elif r["component"] == "REGULATORY_FEE_OFFSET_NFA": reg[r["code"]] = r["value_usd"]
    elif r["component"] == "ALL_IN_COMPUTED": allin.append(r)
    if r.get("SOURCE") != "PUBLIC_REFERENCE" or r.get("VERIFIED_VS_ACCOUNT") != "NOT_RUN":
        label_fail.append((r["code"], r["plan"], r["tier"], r["component"]))
print(f"rows_flat={len(rf)} all_in_rows={len(allin)} codes_exch={sorted(exch)} codes_reg={sorted(reg)}")
print(f"exchange offsets: {exch}\nregulatory offsets: {reg}")
bad = 0
for r in allin:
    exp = round(r["value_usd"], 6)
    calc = round(r["commission_in_all_in"] if False else 0, 6)
    # commission is in the sibling row; find via same key
    calc = None
    for c in rf:
        if (c["code"], c["plan"], c["tier"]) == (r["code"], r["plan"], r["tier"]) and c["component"] == "IBKR_COMMISSION":
            calc = round(c["value_usd"] + exch[r["code"]] + reg[r["code"]], 6); break
    ok = calc is not None and abs(calc - exp) < 1e-9
    if not ok:
        bad += 1
        print(f"MISMATCH {r['code']} {r['plan']} {r['tier']}: all_in={exp} recomputed={calc}")
print(f"all-in arithmetic: {len(allin)-bad}/{len(allin)} OK")
# headline spot checks (handoff tier table)
expect = {("NQ","<=1,000/mo"):2.247,("6E","<=1,000/mo"):2.461,("6B","<=1,000/mo"):2.461,("6J","<=1,000/mo"):2.461,("6A","<=1,000/mo"):2.461,("CL","<=1,000/mo"):2.37,("NG","<=1,000/mo"):2.47,("GC","<=1,000/mo"):2.51,("SI","<=1,000/mo"):2.51,("NQ",">20,000/mo"):1.647,("GC","1,001-10,000/mo"):2.31,("CL","no volume tiers published"):2.37}
for (code,tier),exp in expect.items():
    got = [r["value_usd"] for r in allin if r["code"]==code and r["tier"]==tier and r["plan"] in ("Tiered","Fixed")]
    ok = any(abs(g-exp)<1e-9 for g in got)
    print(f"headline {code} {tier}: table={exp} json={got} {'OK' if ok else 'MISMATCH'}")
    if not ok: fails.append(code)
n = d.get("fx_mapping_note")
print("\nfx_mapping_note:", json.dumps(n)[:700])
if label_fail: fails.append(("label_law", label_fail[:5]))
sys.exit(1 if (fails or bad) else 0)
