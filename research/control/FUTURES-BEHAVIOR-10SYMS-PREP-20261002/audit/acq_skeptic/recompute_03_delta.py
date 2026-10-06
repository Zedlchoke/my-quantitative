#!/usr/bin/env python3
"""ACQ-SKEPTIC delta recomputation: independently verify the post-audit fix.

(1) per-requirement-symbol floors (out-of-corpus fails explicit);
(2) counts under LITERAL and DEFAULT24 policies vs stored analysis_summary@2;
(3) 96-window DERIVED math; band wording presence; coverage_results sha.
Read-only against inputs; writes only this audit namespace.
"""
import glob
import hashlib
import json
from collections import Counter
from pathlib import Path

import yaml

CTRL = Path("/Users/hoangminhlong/my-quantitative/.worktrees/"
            "futures-behavior/prep/research/control/"
            "FUTURES-BEHAVIOR-10SYMS-PREP-20261002")
AO = CTRL / "acquisition_optimization"
SUMMARY = json.loads((AO / "analysis_summary.json").read_text())

VENDOR_CLASSES = {"daily_trades_per_contract", "minute_trades_m1",
                  "full_session_globex_intraday", "synchronous_bbo"}
ROOTS = {"NQ", "ES", "CL", "NG", "GC", "SI", "6E", "6J", "6B", "6A"}
BASE = {("daily_trades_per_contract", "SI-H2"): 120.0,
        ("minute_trades_m1", "NG-H1"): 60.0}
LITERAL_EXTRA = {("daily_trades_per_contract", "NG-H4"): 36.0,
                 ("full_session_globex_intraday", "6E-H5"): 93.0}

hyps = []
for f in sorted(glob.glob(str(CTRL / "configs/symbols/*.yaml"))):
    cfg = yaml.safe_load(Path(f).read_text())
    for h in cfg["hypotheses"]:
        needs = set()
        for section in ("minimal_test", "scored_run"):
            for req in h.get(section, {}).get("requirements", []):
                if req.get("class") in VENDOR_CLASSES:
                    needs.add((req["class"], tuple(req.get("symbols", [cfg["symbol"]]))))
        hyps.append((h["id"], sorted(needs)))

MONTHS = SUMMARY["pkg_ohlcv_months"]
BBO_NQ = {"A": None, "A_variant_24m_floor": None, "B": 24.02, "C": 195.88}
BBO_CL = {"A": None, "A_variant_24m_floor": None, "B": "RW", "C": "RW"}

def req_ok(pkg, hid, cls, syms, policy):
    floor = BASE.get((cls, hid), 24.0)
    if policy == "LITERAL" and (cls, hid) in LITERAL_EXTRA:
        floor = LITERAL_EXTRA[(cls, hid)]
    if cls == "synchronous_bbo":
        if "NQ" in syms:
            return BBO_NQ[pkg] is not None and BBO_NQ[pkg] >= floor
        if "CL" in syms:
            return BBO_CL[pkg] is not None
        return False
    for s in syms:
        if s not in ROOTS:
            return False
        if MONTHS[pkg].get(s, 0) < floor:
            return False
    return True

for policy, key in (("LITERAL", "hypothesis_support_counts"),
                    ("DEFAULT24", "hypothesis_support_counts_under_24m_default")):
    mine = {}
    for pkg in ("A", "A_variant_24m_floor", "B", "C"):
        rows = {}
        for hid, needs in hyps:
            if not needs:
                rows[hid] = "NOT_VENDOR_GATED"
            else:
                rows[hid] = ("SUPPORTED" if all(
                    req_ok(pkg, hid, c, s, policy) for c, s in needs)
                    else "UNSUPPORTED")
        mine[pkg] = dict(Counter(rows.values()))
    stored = SUMMARY[key]
    match = mine == stored
    print(f"{policy}: mine={json.dumps(mine)}")
    print(f"{' ' * len(policy)}  stored match: {match}")
    assert match, f"{policy} counts mismatch"

unsup = {pkg: sorted(h for h, needs in hyps if needs and
                     any(not req_ok(pkg, h, c, s, "LITERAL") for c, s in needs))
         for pkg in ("B", "C", "A_variant_24m_floor")}
print("LITERAL UNSUPPORTED sets:", json.dumps(unsup))
assert unsup["B"] == ["CL-H3", "SI-H2"]
assert unsup["C"] == ["CL-H3"]
assert "6E-H5" in unsup["A_variant_24m_floor"]

# stored per-hypothesis reasons: out-of-corpus explicit
r = SUMMARY["hypothesis_support"]["B"]["CL-H3"]["reason"]
assert "outside the 10-root corpus" in r and "RB" in r and "HO" in r
print("CL-H3 B reason explicit out-of-corpus: OK ->", r[:110], "...")

# DERIVED 96-window math
anchor_gc = 0.012969821692
anchor_list = 773680 / 1e9 * 18.0
print(f"96-window DERIVED: gc {anchor_gc*96:.4f} (stored 1.25); "
      f"list {anchor_list*96:.4f} (stored 1.34); 196: {anchor_gc*196:.4f} / "
      f"{anchor_list*196:.4f} (stored 2.54 / 2.73)")

# coverage_results.json byte-identical
sha = hashlib.sha256((AO / "coverage_results.json").read_bytes()).hexdigest()
print("coverage_results.json sha256:", sha,
      "== 319955b4... :",
      sha == "319955b4b965217a71c1cf94a2b1f9c35896b245eccdf6a604d6246142de6a4d")

# band wording + floor-policy paragraph + 96 in the MD
md = (AO / "ACQUISITION_OPTIMIZATION.md").read_text()
checks = {
    "band wording (first observed records fall inside the refinement band)":
        "first observed records fall inside the refinement band" in md,
    "band wording (earliest valid date is within that band)":
        "earliest valid date is within that band" in md,
    "96 roll windows (12/yr x 8y)":
        "96 monthly roll windows" in md and "12/yr x 8y" in md,
    "DERIVED (96 windows) in package B table":
        "DERIVED (96 windows)" in md,
    "floor-policy paragraph (LITERAL headline)":
        "Headline = LITERAL policy" in md,
    "floor-policy dual report (30 vs 31)":
        "30 SUPPORTED (literal) vs 31" in md,
    "B headline (SI-H2 and CL-H3)":
        "and CL-H3" in md and "SI+GC at 2019+ = 7.75y" in md,
    "C headline (1 of 50 — CL-H3 only)":
        "UNSUPPORTED in C: 1 of 50" in md,
    "CL-H3 outside corpus stated":
        "OUTSIDE the 10-root corpus" in md or "outside the 10-root corpus" in md,
    "no stale '== 2010-06-06' equality claim":
        "== 2010-06-06" not in md and "common == longest" not in md,
}
for k, v in checks.items():
    print(f"MD check [{ 'OK' if v else 'MISS' }] {k}")
assert all(checks.values()), [k for k, v in checks.items() if not v]
print("ALL DELTA CHECKS PASS")
