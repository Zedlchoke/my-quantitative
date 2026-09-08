#!/usr/bin/env python
"""A7 terminal audit: recompute Stage-A gates for the six FOREX-FREE-V4 cells.

Read-only.  Imports the hash-frozen V3 kernel (research/assets/forex_free_v3/
scored_runner.py, verified byte-identical to w3_freeze.json / w4_freeze.json)
and applies its own stage_a_gates() and mechanism_sanity() to the six
published ledger rows' own numbers.  Exit 0 iff every cell's recorded
gates/gate_reasons equal the kernel recomputation.

Usage:  /path/to/python a7_recompute_gates.py [repo_root]
"""
import json
import os
import sys


def sha256_file(path):
    import hashlib
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main(root):
    sys.path.insert(0, root)
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "scored_runner_frozen",
        os.path.join(root, "research/assets/forex_free_v3/scored_runner.py"))
    sr = importlib.util.module_from_spec(spec)
    sys.modules["scored_runner_frozen"] = sr
    spec.loader.exec_module(sr)

    ledger = os.path.join(
        root, "research/control/forex_free_v4_run/scored_ledger_published.jsonl")
    rows = [json.loads(l) for l in open(ledger, encoding="utf-8") if l.strip()]
    assert len(rows) == 6, f"expected 6 rows, got {len(rows)}"

    all_ok = True
    for r in rows:
        rec = {
            "base": r["base"],
            "base_price_only": r["base_price_only"],
            "incremental_alpha": r["incremental_alpha"],
            "n_decisions": r["n_decisions"],
            "folds": r["folds"],
            "mdd_usd": r["mdd_usd"],
            "fold_positive_share": r["fold_positive_share"],
            "pair_concentration": r["pair_concentration"],
            "stress": r["stress"],
            "dropout_scenarios": r["dropout_scenarios"],
            "usd_drift_diag": r["usd_drift_diag"],
        }
        passed, reasons = sr.stage_a_gates(rec)
        match = (passed == r["gates"]) and \
                (sorted(reasons) == sorted(r["gate_reasons"]))
        all_ok &= match
        print(f"{r['cell_id']}: kernel={passed} ledger={r['gates']} "
              f"match={match}")
        if not match:
            print("  kernel:", sorted(reasons))
            print("  ledger:", sorted(r["gate_reasons"]))

    by_fam = {}
    for r in rows:
        rec = {
            "base": r["base"], "base_price_only": r["base_price_only"],
            "incremental_alpha": r["incremental_alpha"],
            "n_decisions": r["n_decisions"], "folds": r["folds"],
            "mdd_usd": r["mdd_usd"],
            "fold_positive_share": r["fold_positive_share"],
            "pair_concentration": r["pair_concentration"],
            "stress": r["stress"],
            "dropout_scenarios": r["dropout_scenarios"],
            "usd_drift_diag": r["usd_drift_diag"],
        }
        by_fam.setdefault(r["family_id"], {})[r["arm"]] = rec
    for fam, cells in sorted(by_fam.items()):
        ok, reasons = sr.mechanism_sanity(cells)
        print(f"{fam} mechanism_sanity: pass={ok} reasons={reasons}")

    print("ALL_GATE_RECOMPUTATIONS_MATCH:", all_ok)
    return 0 if all_ok else 1


if __name__ == "__main__":
    root = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    sys.exit(main(root))
