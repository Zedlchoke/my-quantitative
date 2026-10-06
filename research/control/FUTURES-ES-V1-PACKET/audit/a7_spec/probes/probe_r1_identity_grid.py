#!/usr/bin/env python3
"""A7-SPEC probe R1 — identity-grid arithmetic for SPEC_PB1_ES r2 §6.

Independent recomputation of the A-r4 identity set:
  P-A = {CONT,REV} x {UP,DN} x {D0,D30} x {S2}          -> 8
  P-B = {CONT,REV} x {UP,DN} x D0 x {S1,S3}             -> 8
  primary = 16; FOMC = arm x tail x D0 x S2 x FOMCIN    -> 4
  C1/C2/C3/C4                                            -> 4
  total 24; full 2x2x2x3 grid = 24 of which 8 (D30 x {S1,S3}) are
  declared non-existent.
Deterministic, no inputs beyond the enumeration itself.
"""
import itertools, json, os

ARMS = ["CONT", "REV"]
TAILS = ["UP", "DN"]
DELAYS = ["D0", "D30"]
TIERS = ["S1", "S2", "S3"]

p_a = [f"FBES1-PB1-{a}-{t}-{d}-S2" for a, t, d in itertools.product(ARMS, TAILS, DELAYS)]
p_b = [f"FBES1-PB1-{a}-{t}-D0-{s}" for a, t, s in itertools.product(ARMS, TAILS, ["S1", "S3"])]
primary = p_a + p_b
full_grid = [f"FBES1-PB1-{a}-{t}-{d}-{s}"
             for a, t, d, s in itertools.product(ARMS, TAILS, DELAYS, TIERS)]
omitted = sorted(set(full_grid) - set(primary))
fomc = [f"FBES1-PB1-{a}-{t}-D0-S2-FOMCIN" for a, t in itertools.product(ARMS, TAILS)]
controls = ["FBES1-PLA-D0-S2", "FBES1-ALW-D0-S2", "FBES1-FLAT", "FBES1-DOSE-D0-S2"]
all_ids = primary + fomc + controls

dupes = sorted({i for i in all_ids if all_ids.count(i) > 1})

result = {
    "probe": "r1_identity_grid",
    "counts": {
        "P_A": len(p_a), "P_B": len(p_b), "primary": len(primary),
        "FOMC": len(fomc), "controls_C1_C4": len(controls),
        "total": len(all_ids),
        "full_grid_2x2x2x3": len(full_grid),
        "omitted_from_full_grid": len(omitted),
    },
    "assertions": {
        "P_A_equals_8": len(p_a) == 8,
        "P_B_equals_8": len(p_b) == 8,
        "primary_equals_16": len(primary) == 16,
        "total_equals_24": len(all_ids) == 24,
        "omitted_equals_D30xS1S3_only": all(
            i.endswith(("-D30-S1", "-D30-S3")) for i in omitted) and len(omitted) == 8,
        "no_duplicate_ids": len(dupes) == 0,
        "budget_le_24": len(all_ids) <= 24,
    },
    "omitted_cells_declared_nonexistent": omitted,
    "ids": all_ids,
}
ok = all(result["assertions"].values())
result["verdict"] = "PASS" if ok else "FAIL"

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out_probe_r1_identity_grid.json")
with open(out, "w") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)
print(json.dumps({k: result[k] for k in ("probe", "counts", "assertions", "verdict")}, indent=2))
