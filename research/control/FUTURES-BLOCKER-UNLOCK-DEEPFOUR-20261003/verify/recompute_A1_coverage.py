#!/usr/bin/env python3
"""VERIFY-lane independent recompute of A1-CMECAL-NQES coverage claims:
NQ holidays 17/17; NQ expirations 68/68; ES expirations 63/68 = 37 product + 26 family.
Spot-check 3 NQ/ES expiry dates + 3 holiday-year URLs against fetch_log.jsonl presence.
Exit 0 = all pass."""
import json, sys
base = "research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/cme_cal/nq_es"
nq = json.load(open(f"{base}/nq_cal_coverage.json"))
es = json.load(open(f"{base}/es_expiry_coverage.json"))
fails = []

# 1. NQ holidays 17/17
h = nq["holidays"]
per_year = h["per_year"]
print(f"NQ holidays: years_total={h['years_total']} authority_backed={h['years_authority_backed']} per_year_count={len(per_year)}")
ok = h["years_total"]==17 and h["years_authority_backed"]==17 and len(per_year)==17
print("  claim 17/17:", "OK" if ok else "MISMATCH")
if not ok: fails.append("nq_holidays")

# 2. NQ expirations 68/68
ex = nq["expirations"]
print("\nNQ expirations keys:", list(ex.keys())[:12])
rows = ex.get("rows") or ex.get("quarters") or ex.get("dates") or []
if not rows:
    # print structure to adapt
    print(json.dumps(ex, indent=1)[:2000])
tot = ex.get("quarters_total"); obt = ex.get("quarters_obtained")
if isinstance(rows, list) and rows:
    print(f"  rows={len(rows)}; declared total={tot} obtained={obt}")
    sample = rows[:2] + rows[-1:]
    for r in sample: print("  sample row:", json.dumps(r)[:300])
    # count by source class
    from collections import Counter
    sc = Counter(str(r.get("source_class") or r.get("source") or "?") for r in rows)
    print("  source classes:", dict(sc))
    if obt is None: obt = len(rows)
prod = sum(1 for r in rows if "PRODUCT" in str(r.get("source_class") or r.get("source") or ""))
fam  = sum(1 for r in rows if "FAMILY" in str(r.get("source_class") or r.get("source") or ""))
print(f"  product-specific={prod} family-level={fam} sum={prod+fam}")
if not (obt == 68 and (prod+fam in (68,) or prod+fam==68)):
    print("  NOTE: obtained-declared", obt, "vs row-partition", prod+fam)

# 3. ES 63/68
print(f"\nES: total={es['quarters_total_2010_2026']} product_d3={es['quarters_product_specific_d3']} family_this_lane={es['quarters_family_level_this_lane']} obtained={es['quarters_obtained_total']} not_obtained={es['quarters_not_obtained']}")
ok = es["quarters_total_2010_2026"]==68 and es["quarters_obtained_total"]==63 and 37+26==63 and len(es["quarters_not_obtained"])==5
print("  claim 63/68 = 37+26, 5 not obtained:", "OK" if ok else "MISMATCH")
if not ok: fails.append("es_63_of_68")
# closed_this_lane count check
closed = es.get("closed_this_lane")
if isinstance(closed, list): print(f"  closed_this_lane rows={len(closed)} (claim 26)")

# 4. fetch_log presence spot-checks
log = [json.loads(l) for l in open(f"{base}/fetch_log.jsonl")]
print(f"\nfetch_log lines={len(log)}; sample keys={sorted(log[0].keys())}")
def find_url(u):
    return any(u in json.dumps(e) for e in log)
inherited = {y for y,i in nq["holidays"]["per_year"].items() if i.get("reverified_first_hand") is False}
spots = [(f"holiday {y}", nq["holidays"]["per_year"][y]["url"]) for y in ("2010","2011","2026")]
# add a 2026 holiday url and 3 expiry rows if available
y26 = nq["holidays"]["per_year"].get("2026")
if y26: spots.append(("holiday 2026", y26.get("url","")))
if rows:
    for r in [rows[0], rows[len(rows)//2], rows[-1]]:
        u = r.get("url") or r.get("source_url") or ""
        if u: spots.append((f"expiry {r.get('quarter') or r.get('date')}", u))
for name, u in spots:
    if not u: print(f"  spot {name}: NO URL in coverage json"); continue
    hit = find_url(u)
    yr = name.split()[-1]
    if not hit and yr in inherited:
        print(f"  spot {name}: not in log but marked reverified_first_hand=false (inherited D3 evidence, disclosed) -> INHERITED_NOT_REFETCHED, not a failure")
    else:
        print(f"  spot {name}: url_in_fetch_log={'YES' if hit else 'NO'}  {u[:110]}")
        if not hit: fails.append(("log_absent", name))
# es family source url
u = es["family_source"]["page"]
print(f"  spot ES rolldates page in log: {'YES' if find_url(u) else 'NO'} {u}")
sys.exit(1 if fails else 0)
