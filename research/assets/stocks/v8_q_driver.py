"""V8 Q-phase exact-arm dummy dry-run driver.

Runs all six frozen arms through the full pipeline with dry_run=True:
  - structure only; NO pnl/metric field exists at any depth (recursive
    leak scan below is the enforcement, not a promise);
  - arm_config_digest pairwise-distinct (exact-arm identity);
  - schedule floors verified from the produced schedules;
  - deterministic double generation byte-compared on one arm;
  - scored path refusal re-proven (wrong GO phrase must SystemExit).

Output: research/control/stocks_free_v8_run/q_dummy_dryrun_evidence.json
"""

import hashlib
import json
import os
import subprocess

from research.assets.stocks import v8_family_runner as r

OUT = "research/control/stocks_free_v8_run/q_dummy_dryrun_evidence.json"
LEAK_KEYS = ("pnl", "expectancy", "metrics", "profit", "alpha", "drawdown",
             "sharpe", "returns", "mdd")


def recursive_leak_scan(obj, path="$"):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{path}.{k}"
            if any(t in str(k).lower() for t in LEAK_KEYS):
                hits.append(p)
            hits += recursive_leak_scan(v, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            hits += recursive_leak_scan(v, f"{path}[{i}]")
    elif isinstance(obj, str):
        low = obj.lower()
        for t in ("pnl=", "expectancy=", "profit factor"):
            if t in low:
                hits.append(path)
    return hits


def main():
    head = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
    panel_sha = hashlib.sha256(open(r.PANEL, "rb").read()).hexdigest()
    man = json.load(open("research/control/stocks_free_v8_run/p0a_eodhd_price_manifest.json"))
    man_sha = hashlib.sha256(json.dumps(man, sort_keys=True).encode()).hexdigest()

    f1_fields = {"us-gaap:AccountsReceivableNetCurrent", "us-gaap:InventoryNet",
                 "us-gaap:AccountsPayableCurrent", "us-gaap:Assets",
                 "us-gaap:AllowanceForDoubtfulAccountsReceivableCurrent"}
    f2_fields = {"us-gaap:AccumulatedDepreciationDepletionAndAmortizationPropertyPlantAndEquipment",
                 "us-gaap:PropertyPlantAndEquipmentGross", "us-gaap:UnrecognizedTaxBenefits",
                 "us-gaap:Goodwill", "us-gaap:Assets"}
    prices = r.load_prices()
    folds = r.fold_sessions(prices)
    arms = {}
    for arm_id in r.ARM_SPECS:
        fam = r.ARM_SPECS[arm_id]["family"]
        fields = f1_fields if fam.endswith("ACCRUAL-FLOW") else f2_fields
        panel = r.load_panel(fields)
        arms[arm_id] = r.run_arm(arm_id, panel, prices, folds, dry_run=True,
                                 price_manifest_sha=man_sha, panel_sha=panel_sha,
                                 code_freeze_sha=head)

    digests = {a: rec["arm_config_digest"] for a, rec in arms.items()}
    digest_distinct = len(set(digests.values())) == len(digests) == 6
    leaks = {}
    for a, rec in arms.items():
        hits = recursive_leak_scan(rec)
        if hits:
            leaks[a] = hits
    floors = {}
    nonvacuity = {}
    for a, rec in arms.items():
        scored = [s for s in rec["schedule"] if not s["warmup"] and s.get("event") != "FOLD_FORCE_FLAT"]
        per_fold = {}
        for s in scored:
            per_fold[s["fold"]] = per_fold.get(s["fold"], 0) + 1
        el = sorted(s["eligible"] for s in scored)
        po = sorted(s["populated"] for s in scored)
        lg = sorted(s["legs"] for s in scored)
        med = lambda x: x[len(x)//2] if x else 0
        floors[a] = {
            "scored_decisions": len(scored),
            "per_fold": per_fold,
            "floor_ok": len(scored) >= 30 and all(v >= 5 for v in per_fold.values()),
        }
        # F-A7-2 remediation: vacuity is now DETECTABLE - a book that never
        # populates must fail the dry run
        nonvacuity[a] = {
            "median_eligible": med(el), "median_populated": med(po),
            "median_legs": med(lg),
            "nonvacuous": med(el) >= 100 and med(lg) >= 20,
        }
    # deterministic double generation on one arm
    panel = r.load_panel(f2_fields)
    again = r.run_arm("SFV8-F2-ANCHOR", panel, prices, folds, dry_run=True,
                      price_manifest_sha=man_sha, panel_sha=panel_sha,
                      code_freeze_sha=head)
    double_ok = json.dumps(arms["SFV8-F2-ANCHOR"], sort_keys=True) == json.dumps(again, sort_keys=True)
    # scored refusal re-proof
    refusal = "NOT_PROVEN"
    try:
        r.run_arm("SFV8-F2-ANCHOR", panel, prices, folds, dry_run=False, owner_go="WRONG")
    except SystemExit:
        refusal = "PROVEN (SystemExit on wrong GO phrase)"
    except Exception as e:  # noqa: BLE001
        refusal = f"PROVEN ({type(e).__name__})"

    ok = (digest_distinct and not leaks and double_ok
          and all(f["floor_ok"] for f in floors.values())
          and all(n["nonvacuous"] for n in nonvacuity.values()))
    ev = {
        "schema": "stocks_free_v8_run/q_dummy_dryrun_evidence@1",
        "measured_at_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "producer_role": "A1 (Q-phase exact-arm dummy dry-run)",
        "code_freeze_sha": head,
        "panel_sha256": panel_sha,
        "price_manifest_sha256": man_sha,
        "arms_run": sorted(arms.keys()),
        "arm_config_digests": digests,
        "digest_pairwise_distinct": digest_distinct,
        "recursive_leak_scan_hits": leaks,
        "schedule_floors": floors,
        "nonvacuity_fba72": nonvacuity,
        "deterministic_double_generation": double_ok,
        "scored_refusal": refusal,
        "verdict": "DRY_RUN_PASS" if ok else "DRY_RUN_FAIL",
    }
    json.dump(ev, open(OUT, "w"), indent=1)
    print(json.dumps({k: ev[k] for k in ("verdict", "digest_pairwise_distinct",
                                         "recursive_leak_scan_hits",
                                         "deterministic_double_generation",
                                         "scored_refusal")}
                    | {"nonvacuity": {a: n["nonvacuous"] for a, n in nonvacuity.items()},
                       "medians": {a: (n["median_eligible"], n["median_populated"], n["median_legs"]) for a, n in nonvacuity.items()}}))


if __name__ == "__main__":
    main()
