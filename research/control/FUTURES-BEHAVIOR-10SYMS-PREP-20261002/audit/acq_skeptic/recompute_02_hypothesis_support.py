#!/usr/bin/env python3
"""ACQ-SKEPTIC recomputation 02: independent re-derivation of the 50
hypothesis vendor-support verdicts from configs/symbols/*.yaml floors +
package windows, with per-requirement symbol handling (does NOT assume the
hypothesis's own root covers cross-symbol requirements).

Read-only against inputs; writes only this audit namespace.
"""
import glob
import json
from collections import Counter
from pathlib import Path

import yaml

CTRL = Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
            "futures-behavior/prep/research/control/"
            "FUTURES-BEHAVIOR-10SYMS-PREP-20261002")
SUMMARY = json.loads((CTRL / "acquisition_optimization/analysis_summary.json").read_text())

VENDOR_CLASSES = {"daily_trades_per_contract", "minute_trades_m1",
                  "full_session_globex_intraday", "synchronous_bbo"}
ROOTS = {"NQ", "ES", "CL", "NG", "GC", "SI", "6E", "6J", "6B", "6A"}

# floors in months re-derived from the yaml floor STRINGS
def floor_months(floor_str, cls, hyp_id):
    s = str(floor_str).lower()
    if cls == "daily_trades_per_contract" and hyp_id == "SI-H2":
        return 120.0  # >=10y two-leg
    if cls == "minute_trades_m1" and hyp_id == "NG-H1":
        return 60.0   # >=5y, >=100 events
    return 24.0       # default admission bar

hyps = []
for f in sorted(glob.glob(str(CTRL / "configs/symbols/*.yaml"))):
    cfg = yaml.safe_load(Path(f).read_text())
    for h in cfg["hypotheses"]:
        needs = []
        for section in ("minimal_test", "scored_run"):
            for req in h.get(section, {}).get("requirements", []):
                if req.get("class") in VENDOR_CLASSES:
                    needs.append({"class": req["class"],
                                  "use": req.get("use"),
                                  "symbols": req.get("symbols", [cfg["symbol"]]),
                                  "floor": req.get("floor"),
                                  "acquisition": req.get("acquisition")})
        needs = sorted({(n["class"], n["use"], tuple(n["symbols"])) for n in needs})
        hyps.append({"id": h["id"], "needs": [
            {"class": c, "use": u, "symbols": list(s)} for c, u, s in needs]})

print(f"total hypotheses: {len(hyps)}")
nvg = [h["id"] for h in hyps if not h["needs"]]
print(f"NOT vendor-gated ({len(nvg)}): {nvg}")

# distinct floor strings per (class) to sanity-check the 24m default
floor_strings = {}
for h in hyps:
    for n in h["needs"]:
        # recover floor string by re-scanning (needs lost it in dedupe); rescan
        pass
floor_str_scan = Counter()
for f in sorted(glob.glob(str(CTRL / "configs/symbols/*.yaml"))):
    cfg = yaml.safe_load(Path(f).read_text())
    for h in cfg["hypotheses"]:
        for section in ("minimal_test", "scored_run"):
            for req in h.get(section, {}).get("requirements", []):
                if req.get("class") in VENDOR_CLASSES:
                    floor_str_scan[(req["class"], str(req.get("floor"))[:60])] += 1
print("\nfloor strings per (class, floor):")
for k, v in sorted(floor_str_scan.items()):
    print(f"  {v}x {k}")

# any requirement symbols outside the 10-root corpus?
outside = []
for f in sorted(glob.glob(str(CTRL / "configs/symbols/*.yaml"))):
    cfg = yaml.safe_load(Path(f).read_text())
    for h in cfg["hypotheses"]:
        for section in ("minimal_test", "scored_run"):
            for req in h.get(section, {}).get("requirements", []):
                if req.get("class") in VENDOR_CLASSES:
                    for s in req.get("symbols", []):
                        if s not in ROOTS:
                            outside.append((h["id"], req["class"], s, req.get("floor")))
print("\nrequirements on symbols OUTSIDE the 10-root corpus:")
for o in outside:
    print("  ", o)

# package windows (ohlcv months per root; bbo availability), from analysis_summary
MONTHS = SUMMARY["pkg_ohlcv_months"]
BBO_NQ = {"A": None, "A_variant_24m_floor": None,
          "B": 24.02, "C": 195.88}   # window lengths of the NQ bbo lines
BBO_CL = {"A": None, "A_variant_24m_floor": None,
          "B": "ROLLWINDOWS", "C": "ROLLWINDOWS"}

def req_ok(pkg, hyp_id, cls, symbols):
    floor = floor_months(None, cls, hyp_id)
    if cls == "synchronous_bbo":
        if "NQ" in symbols:
            return BBO_NQ[pkg] is not None and BBO_NQ[pkg] >= floor
        if "CL" in symbols:
            return BBO_CL[pkg] is not None
        return False
    # depth classes: EVERY required symbol must be in the package with months>=floor
    for s in symbols:
        if s not in ROOTS:
            return False            # symbol not in corpus -> cannot be supported
        if MONTHS[pkg].get(s, 0) < floor:
            return False
    return True

my = {}
for pkg in ("A", "A_variant_24m_floor", "B", "C"):
    rows = {}
    for h in hyps:
        if not h["needs"]:
            rows[h["id"]] = "NOT_VENDOR_GATED"
            continue
        ok = all(req_ok(pkg, h["id"], n["class"], n["symbols"]) for n in h["needs"])
        rows[h["id"]] = "SUPPORTED" if ok else "UNSUPPORTED"
    my[pkg] = rows

print("\n=== MY INDEPENDENT COUNTS vs STORED ===")
for pkg in ("A", "A_variant_24m_floor", "B", "C"):
    mine = dict(Counter(my[pkg].values()))
    stored = SUMMARY["hypothesis_support_counts"][pkg]
    print(f"{pkg}: mine={mine}  stored={stored}")

print("\n=== PER-HYPOTHESIS DIFFERENCES ===")
for pkg in ("A", "A_variant_24m_floor", "B", "C"):
    for hid, v in my[pkg].items():
        sv = SUMMARY["hypothesis_support"][pkg][hid]["verdict"]
        if v != sv:
            print(f"  {pkg} {hid}: mine={v} stored={sv}")

print("\n=== SPOT CHECKS (>=8) with reasons ===")
spots = ["SI-H2", "NG-H1", "NQ-H5", "CL-H5", "CL-H3", "CL-H1", "GC-H2",
         "ES-H4", "6J-H5", "NG-H3"]
for pkg in ("A", "A_variant_24m_floor", "B", "C"):
    print(f"-- {pkg}")
    for hid in spots:
        print(f"   {hid}: mine={my[pkg][hid]} stored={SUMMARY['hypothesis_support'][pkg][hid]['verdict']}")
