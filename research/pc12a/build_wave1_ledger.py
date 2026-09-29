#!/usr/bin/env python
"""Stage-A wave-1 discovery ledger builder (run once after the two
full-window dry-run passes).

Consumes:
  /tmp/wave1_runA/DRY_RUN_REPORT.json   (75 legs, main set)
  /tmp/wave1_runB/DRY_RUN_REPORT.json   (USDJPY-S050, 3y-warmup pass)
  research/pc12a/legs_config/*.json     (arm digests, labels, params)

Emits one append-only JSON row per candidate into
  research/control/PORTFOLIO-COMPOSITE-12ASSETS-100K-V1/TRIAL_LEDGER.jsonl

result codes:
  IMPLEMENTED  - rule built + dry-run decisions >= 20 (F1 floor PASS), or
                 implemented on an un-staged symbol (floor NOT_RUN, data)
  FLOOR_FAIL   - dry-run decisions < 20 over the full window (pre-PnL kill)
  PARKED_IMPL  - triage-optimistic: required input series not staged
"""
import datetime as dt
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))))

from research.pc12a import legs as L  # noqa: E402

CYCLE = "PORTFOLIO-COMPOSITE-12ASSETS-100K-V1"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
CFG_DIR = os.path.join(ROOT, "research", "pc12a", "legs_config")
LEDGER = os.path.join(ROOT, "research", "control", CYCLE,
                      "TRIAL_LEDGER.jsonl")
F1_FLOOR = 20

PARKED = {
    "USDJPY-S064": ("core input Brent D1 close not staged on this checkout "
                    "(no audited oil panel); triage named it evidenced "
                    "(G-PIT-V3) but no Brent series exists here"),
    "USDJPY-S066": ("core input VIX daily close not staged on this checkout "
                    "(VIX is not among the 3 audited FX panels)"),
    "USDJPY-S070": ("core input AUDJPY requires AUDUSD D1 (derivable cross); "
                    "AUDUSD panels not staged on this checkout"),
    "AUDUSD-S066": ("core input AUDJPY requires AUDUSD panels; not staged "
                    "(the leg's own symbol AUDUSD is also un-staged)"),
    "AUDUSD-S069": ("core input USDCAD 20d-low confirmation; USDCAD panels "
                    "not staged (own symbol AUDUSD also un-staged)"),
    "AUDUSD-S082": ("core input AUDJPY regression residual requires AUDUSD "
                    "panels; not staged"),
    "AUDUSD-S083": ("core input EURAUD requires AUDUSD panels; not staged"),
    "AUDUSD-S091": ("core input VIX 20d-median not staged on this checkout"),
    "USDCAD-S068": ("core input CADJPY requires USDCAD panels (derivable "
                    "from USDCAD x USDJPY); not staged"),
}

UNSTAGED_SYMBOLS = {"AUDUSD", "USDCAD"}


def main():
    reports = {}
    for tag in ("EURUSD", "JPY", "GBPUSD", "S050", "S090"):
        p = f"/tmp/wave1_{tag}/DRY_RUN_REPORT.json"
        if os.path.exists(p):
            reports[tag] = json.load(open(p))
    merged = {}
    runtimes = {}
    for tag, rep in reports.items():
        runtimes[tag] = rep.get("elapsed_seconds")
        for lid, d in rep["legs"].items():
            if lid in merged and merged[lid]["decisions"] > d["decisions"]:
                continue
            merged[lid] = d
    not_run = {}
    for rep in reports.values():
        not_run.update(rep.get("legs_not_run", {}))

    cfgs = L.load_leg_configs(CFG_DIR)
    now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = []
    n = 0
    for cfg in sorted(cfgs, key=lambda c: c.get("corpus_gid")
                      or c.get("class_candidate_id")):
        gid = cfg.get("corpus_gid") or cfg.get("class_candidate_id")
        ident = L.make_identity(cfg)
        n += 1
        base = {
            "row_id": f"AMECH-W1-{n:03d}",
            "cycle_id": CYCLE,
            "stage": "A-MECH",
            "sleeve_id": cfg["sleeve_id"],
            "corpus_gid": gid,
            "arm_config_digest": ident.arm_config_digest,
            "outcome_exposed_label": cfg["outcome_exposed_label"],
            "fold_scope": "DISCOVERY_PRE_PNL",
            "recorded_utc": now,
        }
        psrc = cfg.get("param_source")
        if cfg["symbol"] in UNSTAGED_SYMBOLS and gid not in PARKED:
            # implemented on an un-staged symbol: never scheduled
            base.update({
                "result": "IMPLEMENTED",
                "detail": (f"rule implemented (archetype="
                           f"{cfg.get('archetype', 'legacy')}, param_source="
                           f"{psrc}); dry-run NOT_RUN: no staged M1 panel "
                           f"for {cfg['symbol']} on this checkout; F1 floor "
                           f"NOT_RUN (data, not a rule failure)"),
            })
            rows.append(base)
            continue
        if gid in PARKED:
            base.update({
                "result": "PARKED_IMPL",
                "detail": f"triage was optimistic on input availability: "
                          f"{PARKED[gid]}; no arm was forced",
            })
        elif gid in not_run:
            base.update({
                "result": "IMPLEMENTED",
                "detail": (f"rule implemented (archetype="
                           f"{cfg.get('archetype', 'legacy')}, param_source="
                           f"{psrc}); dry-run NOT_RUN: no staged M1 panel "
                           f"for {cfg['symbol']} on this checkout; F1 floor "
                           f"NOT_RUN (data, not a rule failure)"),
            })
        else:
            dec = merged.get(gid, {}).get("decisions", 0)
            votes = merged.get(gid, {}).get("votes", {})
            floor_ok = dec >= F1_FLOOR
            detail = (f"rule implemented (archetype="
                      f"{cfg.get('archetype', 'legacy')}, param_source="
                      f"{psrc}); full-window dry-run decisions={dec} "
                      f"(votes -1/0/+1: {votes.get('-1', 0)}/"
                      f"{votes.get('0', 0)}/{votes.get('+1', 0)})")
            base.update({
                "result": "IMPLEMENTED" if floor_ok else "FLOOR_FAIL",
                "detail": detail + ("" if floor_ok else
                                    f"; F1 floor {F1_FLOOR} NOT met "
                                    f"(pre-PnL kill)"),
            })
        rows.append(base)

    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    if os.path.exists(LEDGER):
        raise SystemExit(f"refusing to overwrite existing ledger {LEDGER}")
    with open(LEDGER, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, sort_keys=True) + "\n")
    counts = {}
    for r in rows:
        counts[r["result"]] = counts.get(r["result"], 0) + 1
    print(json.dumps({"rows": len(rows), "counts": counts,
                      "runtimes": runtimes}, indent=1))


if __name__ == "__main__":
    main()
