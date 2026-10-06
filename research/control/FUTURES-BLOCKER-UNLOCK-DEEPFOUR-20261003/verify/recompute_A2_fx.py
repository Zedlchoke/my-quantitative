#!/usr/bin/env python3
"""VERIFY-lane independent recompute of A2-CMECAL-FX (final):
coverage components vs declared total; per-date rule check vs 3rd-Wednesday arithmetic.
Exit 0 = internally consistent; exit 2 = counting discrepancy found."""
import json, sys, datetime, calendar
base = "research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/cme_cal/fx"
d = json.load(open(f"{base}/fx_cal_coverage.json"))
cv = d["expirations_coverage"]["per_symbol_quarters_obtained_of_68"]
tot = sum(cv.values())
print(f"declared per-symbol coverage {cv} -> component sum = {tot}")
print("handoff/verdict claim: 96 (18+31+13+35) -- arithmetic check: 18+31+13+35 =", 18+31+13+35)

def third_wed(y,m):
    last = calendar.monthrange(y,m)[1]
    ws = [datetime.date(y,m,dd) for dd in range(1,last+1) if datetime.date(y,m,dd).weekday()==2]
    return ws[2]

by_year = d["expirations_coverage"]["per_symbol_by_year"]
bad=[]; n_rows=0; per_sym={}
for sym, years in sorted(by_year.items()):
    c=0
    for y, info in sorted(years.items()):
        for q in info["quarters"]:
            mtxt, dtxt = q.split()
            m = {"MAR":3,"JUN":6,"SEP":9,"DEC":12}[mtxt]
            dt = datetime.datetime.strptime(dtxt, "%m/%d/%Y").date()
            tw = third_wed(dt.year, m)
            mon = tw - datetime.timedelta(days=2); fri = mon - datetime.timedelta(days=3); tue = tw - datetime.timedelta(days=1)
            c += 1; n_rows += 1
            if dt not in (mon, fri, tue): bad.append((sym, q, "3rdWed="+str(tw)))
    per_sym[sym]=c
print("RECOUNT from per_symbol_by_year rows:", per_sym, "total =", n_rows)
print("expirations flat-list len:", len(d["expirations"]))
print("rule deviations (not Mon-before-3rd-Wed / Fri-fallback / Tue-edge):", bad or "NONE")
declared_vs_recount = {s:(cv[s], per_sym.get(s)) for s in cv}
print("declared vs recounted:", declared_vs_recount)
# where does the 96 come from? scan all keys for a '96' total
s=json.dumps(d)
import re
print("occurrences of 96/272-style totals in md:")
md=open(f"{base}/FX_CALENDAR_EVIDENCE.md").read()
for line in md.splitlines():
    if "96" in line and ("272" in line or "18" in line or "quarters" in line.lower()):
        print("  >", line.strip()[:220])
sys.exit(2 if (tot!=96 or n_rows!=96) else 0)
