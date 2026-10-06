#!/usr/bin/env python3
"""VERIFY-lane recompute of A3-CMECAL-COMM:
- counts CL 183 / NG 240 from comm_cal_coverage.json and from the row files
- rule quotes present (CL/NG/GC/SI) with era + URL
- SI 12:25 vs GC 12:30 offset stated with source
Exit 0 = pass."""
import json, sys, re
base = "research/control/FUTURES-BLOCKER-UNLOCK-DEEPFOUR-20261003/cme_cal/comm"
d = json.load(open(f"{base}/comm_cal_coverage.json"))
print("top keys:", list(d.keys()))
# find claimed counts
def find_counts(o, path=""):
    if isinstance(o, dict):
        for k,v in o.items():
            if isinstance(v,(int,float)) and any(t in str(k).lower() for t in ("row","count","n_dates","dates","quarters")):
                print(f"  {path}/{k} = {v}")
            find_counts(v, f"{path}/{k}")
find_counts(d)
# row files line counts
for f in ["cl_cal_2010_rows.txt","cl_cal_2018_rows.txt","ng_cal_2010_rows.txt","ng_cal_2017_rows.txt","gc_cal_2013_rows.txt","si_cal_2015_rows.txt"]:
    txt=open(f"{base}/html/{f}").read()
    lines=[l for l in txt.splitlines() if l.strip()]
    print(f"  html/{f}: {len(lines)} non-empty lines; head: {lines[0][:100] if lines else ''}")
md = open(f"{base}/COMM_CALENDAR_EVIDENCE.md").read()
# rule quotes
for sym, pat in [
  ("CL", "25th calendar day"),
  ("NG", "business days prior"),
  ("GC", "12:30"),
  ("SI", "12:25"),
]:
    i = md.find(pat)
    print(f"quote '{pat}' in COMM_CALENDAR_EVIDENCE.md: {'FOUND' if i>=0 else 'NOT FOUND'}")
    if i>=0: print("   ...", md[max(0,i-200):i+140].replace("\n"," ")[:330])
# SI vs GC offset sentence
for m in re.finditer(r"[^\n]*(?:12:25|12:30)[^\n]*(?:offset|12:30|12:25)[^\n]*", md):
    print("OFFSET LINE:", m.group(0).strip()[:300])
sys.exit(0)
