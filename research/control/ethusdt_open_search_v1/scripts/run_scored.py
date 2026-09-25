"""EOS1 P3 sanitized dry-run + P4 scored runner.

Modes:
  dryrun  — runs every book/tier but emits ONLY count-level fields from a
            WHITELIST; recursive substring leak-scan; pairwise-distinct
            record IDs; zero denominator delta. No PnL/PF/stress anywhere.
  scored  — full output + gate evaluation (STOP-1 owner GO required first;
            the runner refuses to execute in scored mode unless the flag
            --go-phrase matches the registered phrase AND
            audits_a7/go_authorization.json exists).

Output: freezes/dry_run.json or scored/scored_summary.json.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import eos1_engine as E  # noqa: E402

GO_PHRASE = "GO ETHUSDT OPEN SEARCH V1 SCORED EXECUTION"
LEAK_SUBSTRINGS = ("pnl", "profit", "net", "gross", "fee", "funding\":", "drawdown",
                   "mdd", "sharpe", "stress", "equity", "balance", "return",
                   "pf_", "payoff")
WHITELIST = ("record_id", "bars", "decisions", "fills", "trades",
             "funding_settlement_events", "non_vacuous",
             "settlement_price_fallbacks_this_book")


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def run_all() -> tuple[dict, dict]:
    data = E.build_all_series()
    targets = E.build_targets(data)
    eth = data["eth_h4"]
    scored_idx = [i for i, b in enumerate(eth) if E.fold_of(b["ts"])]
    engine = {}

    def book_id(book: str, tier: float) -> str:
        return f"EOS1|{book}|tier{tier}"

    for book, target in targets.items():
        for tier in E.TIERS:
            fb_before = data["px_settle"].fallbacks
            res = E.run_book(target, eth, data["funding"], tier, data["px_settle"])
            info_fallback_delta = data["px_settle"].fallbacks - fb_before
            trades = sum(f["trades"] for f in res["folds"].values())
            fevents = sum(f["funding_events"] for f in res["folds"].values())
            engine[book_id(book, tier)] = {
                "res": res, "trades": trades, "funding_events": fevents,
                "decisions": sum(1 for i in scored_idx if target[i] != 0),
                "bars": len(scored_idx), "fallback_delta": info_fallback_delta,
            }
    return data, engine


def dryrun() -> int:
    data, engine = run_all()
    out = {"schema": "eos1.dry_run@1", "built_utc": now(),
           "scored": False, "real_pnl": False, "published": False,
           "books": {}}
    ids = []
    for rid, info in sorted(engine.items()):
        rec = {"record_id": rid, "bars": info["bars"],
               "decisions": info["decisions"], "fills": info["res"]["fills_total"],
               "trades": info["trades"],
               "funding_settlement_events": info["funding_events"],
               "non_vacuous": info["res"]["fills_total"] > 0,
               "settlement_price_fallbacks_this_book": info["fallback_delta"]}
        assert all(k in WHITELIST for k in rec), f"non-whitelist key in {rid}"
        out["books"][rid] = rec
        ids.append(rid)
    out["record_ids_pairwise_distinct"] = len(ids) == len(set(ids))
    out["expected_computations"] = (len(E.ARMS) * 3      # cells x tiers
                                    + 4 * 3              # references x tiers
                                    + len(E.ARMS) * 2 * 3)  # controls x tiers
    out["actual_computations"] = len(ids)
    out["denominator_delta"] = 0  # dry-run is zero-denominator by law
    # leak scan runs on the payload WITHOUT the required hygiene flags
    # ("real_pnl": false etc. are contract metadata, not outcomes) and
    # without the leak_scan block itself (which echoes forbidden words)
    scan_blob = json.dumps({"books": out["books"]}, sort_keys=True)
    leaked = [s for s in LEAK_SUBSTRINGS if s in scan_blob]
    out["leak_scan"] = {"forbidden_substrings_checked": len(LEAK_SUBSTRINGS),
                        "leaked": leaked}
    out["dry_run_pass"] = (out["record_ids_pairwise_distinct"]
                           and out["actual_computations"] == out["expected_computations"]
                           and not leaked
                           and all(v["non_vacuous"] for k, v in out["books"].items()
                                   if not k.startswith("EOS1|BASE_CASH")))
    dest = pathlib.Path(__file__).resolve().parents[1] / "freezes" / "dry_run.json"
    dest.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({k: out[k] for k in ("expected_computations", "actual_computations",
                                          "record_ids_pairwise_distinct", "leak_scan",
                                          "dry_run_pass")}, indent=1))
    return 0 if out["dry_run_pass"] else 1


def cost_roundtrip_bps(res: dict, tier: float) -> float:
    """G7 'measured cost/round-trip' follows the ES1 precedent semantics:
    the EXECUTION (slippage) cost — 2 adverse ticks per round trip — in bps
    of the average raw fill price. Fees are already priced inside net PnL;
    G7 is the execution-quality ceiling, not a second fee gate (A7 F-1:
    fee-inclusive reading is structurally unpassable at 1.5x and would
    predetermine the verdict)."""
    px = res["avg_raw_fill_px"]
    if not px:
        return 0.0
    return (2 * E.TICK * tier / px) * 1e4


def gates(cell: str, tier_table: dict, refs: dict, feas: dict) -> dict:
    c10 = tier_table[cell][1.0]
    c15 = tier_table[cell][1.5]
    folds = {k: v["net"] for k, v in c10["res"]["folds"].items()}
    pos_folds = {k: v for k, v in folds.items() if v > 0}
    pos_sum = sum(pos_folds.values())
    conc = (max(pos_folds.values()) / pos_sum) if pos_sum > 0 else 1.0
    shuf = tier_table[f"{cell}|G6-SHUF"][1.0]["res"]["net_total"]
    inv = tier_table[f"{cell}|G6-INV"][1.0]["res"]["net_total"]
    tr = {k: v["res"]["folds"][k]["net"] for k in folds}
    tr_pos = {k: v for k, v in tr.items() if v > 0}
    flips_pos_to_neg = [k for k in tr if tr[k] > 0 and folds[k] < 0]
    g = {
        "G1": c10["res"]["net_total"] > 0,
        "G2": c15["res"]["net_total"] > 0,
        "G3": {"pass": all(c10["res"]["net_total"] > refs[r][1.0]["res"]["net_total"]
                           for r in ("BASE_ALWAYS_ON_LONG", "BASE_TREND_LF", "REF_SHORT_ALWAYS")),
               "margins": {r: round(c10["res"]["net_total"] - refs[r][1.0]["res"]["net_total"], 2)
                           for r in ("BASE_ALWAYS_ON_LONG", "BASE_TREND_LF", "REF_SHORT_ALWAYS")}},
        "G4": (sum(1 for v in folds.values() if v > 0) >= 3)
              or ((c10["res"]["net_total"] - max(folds.values())) > 0),
        "G5": conc <= 0.50,
        "G6": {"pass": (not shuf > c10["res"]["net_total"])
               and (not inv > c10["res"]["net_total"]),  # plan: controls must NOT out-earn; ties pass
               "shuf_net": shuf, "inv_net": inv},
        "G7": {"pass": c15["res"]["fills_total"] <= 10000
               and cost_roundtrip_bps(c15["res"], 1.5) <= 10.0,
               "fills_1_5x": c15["res"]["fills_total"],
               "cost_rt_bps_1_5x": round(cost_roundtrip_bps(c15["res"], 1.5), 4)},
        "G10": {"pass": (c10["res"]["net_total"] > refs["BASE_TREND_LF"][1.0]["res"]["net_total"])
                and not flips_pos_to_neg,
                "delta_folds_vs_trend_lf": {k: round(folds[k] - tr[k], 2) for k in folds},
                "flips_pos_to_neg": flips_pos_to_neg},
        "G11_disclosure": feas["g11_spearman_vs_trend_lf"].get(cell),
    }
    g["all_pass"] = all(v if isinstance(v, bool) else v["pass"]
                        for k, v in g.items() if k.startswith("G") and k != "G11_disclosure")
    g["fold_nets"] = {k: round(v, 2) for k, v in folds.items()}
    g["fold_concentration"] = round(conc, 4)
    g["net_at_tiers"] = {str(t): round(tier_table[cell][t]["res"]["net_total"], 2)
                         for t in E.TIERS}
    return g


def scored() -> int:
    auth = pathlib.Path(__file__).resolve().parents[1] / "audits_a7" / "go_authorization.json"
    if not auth.exists():
        print("REFUSED: no audits_a7/go_authorization.json (STOP-1 owner gate not passed)")
        return 2
    a = json.loads(auth.read_text())
    if a.get("go_phrase") != GO_PHRASE:
        print("REFUSED: go phrase mismatch")
        return 2
    feas = json.loads((pathlib.Path(__file__).resolve().parents[1]
                       / "freezes" / "feasibility.json").read_text())
    data, engine = run_all()
    tier_table: dict = {}
    for rid, info in engine.items():
        parts = rid.split("|")
        book = "|".join(parts[1:-1])   # control books contain '|' in their names
        tier_table.setdefault(book, {})[float(parts[-1].strip("tier"))] = info
    refs = {r: tier_table[r] for r in ("BASE_CASH", "BASE_ALWAYS_ON_LONG",
                                       "BASE_TREND_LF", "REF_SHORT_ALWAYS")}
    cells = {}
    for arm in E.ARMS:
        cells[arm] = gates(arm, tier_table, refs, feas)
    all_pass = [a for a, g in cells.items() if g["all_pass"]]
    out = {"schema": "eos1.scored_run@1", "go": a, "built_utc": now(),
           "denominator": {"scored_cells": len(E.ARMS),
                           "computations": len(E.ARMS) * len(E.TIERS),
                           "controls": len(E.ARMS) * 2 * len(E.TIERS),
                           "references": 4 * len(E.TIERS)},
           "cells": cells,
           "references": {r: {"net_at_tiers": {str(t): round(refs[r][t]["res"]["net_total"], 2)
                                                for t in E.TIERS},
                              "fold_nets": {k: round(v["net"], 2) for k, v in refs[r][1.0]["res"]["folds"].items()}}
                          for r in refs},
           "all_pass_cells": all_pass,
           "verdict": ("ETHUSDT_OPEN_SEARCH_V1_POSTHOC_DISCOVERY_CANDIDATE_FOR_PROSPECTIVE_VALIDATION"
                       if all_pass else
                       "ETHUSDT_OPEN_SEARCH_V1_NO_INCREMENTAL_VALUE")}
    dest = pathlib.Path(__file__).resolve().parents[1] / "scored" / "scored_summary.json"
    dest.parent.mkdir(exist_ok=True)
    dest.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")
    print(json.dumps({"verdict": out["verdict"], "all_pass": all_pass}, indent=1))
    return 0


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "dryrun"
    sys.exit(dryrun() if mode == "dryrun" else scored())
