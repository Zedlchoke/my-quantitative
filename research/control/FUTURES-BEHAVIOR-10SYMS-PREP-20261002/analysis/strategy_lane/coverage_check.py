#!/usr/bin/env python3
"""coverage_check.py — STRATEGY-CONFIGS lane, FUTURES-BEHAVIOR-10SYMS-PREP-20261002.

Cross-checks every hypothesis's data requirements (configs/symbols/*.yaml)
against data/COVERAGE_MANIFEST.json (READ-ONLY, data lane authority, 2026-10-02)
and reports, per hypothesis:

  * minimal_test_verdict:  RUNNABLE_NOW | WAIT_DATA(missing classes) |
                           BLOCKED_NONDATA(blockers)
  * scored_run_verdict:    always blocked today (depth floor + slippage/fee
                           declarations + registration) — listed explicitly
  * config-vs-manifest disagreements on available_today (findings, not errors)

Recomputation rules (manifest statuses -> availability by declared use):
  daily_trades_per_contract / derived_roll_gaps:
      HAVE_PARTIAL -> true for use in {signal_reference, conditional_descriptive,
      construction_check}; false for backtest_fill (DAILY_BT floor >=24m vs
      measured 14-17m front-chain runs) and for intraday uses
  daily_bid_ask: true for {cost_evidence, conditional_descriptive, construction_check}
  minute_trades_m1 / hourly_trades_h1: HAVE_SNAPSHOT_ONLY -> true only for
      conditional_descriptive (snapshot caveat); false for event/execution uses
  definitions_reference: HAVE_MINIMAL -> true only for construction_check
  statistics_settlement_oi / open_interest: NOT_AVAILABLE -> always false
  settlement: HAVE_DERIVED_ONLY -> true for {signal_reference, conditional_descriptive}
  external classes: only event_release_calendars available (release schedules
      fetched 2026-10-02, FACT, per dossier S4s); everything else NOT acquired
  any requirement naming symbols absent from the manifest (RB/HO/HG/US/EU/UK/JP/AU)
      -> corpus class false ("symbol not in coverage manifest"), external class
      evaluated at class level

Everything offline/deterministic. Outputs:
  analysis/strategy_lane/coverage_report.json
  analysis/strategy_lane/coverage_summary.md
Exit 0 on completion (this is a REPORT, not a gate); 1 only on internal errors.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

CYCLE = Path(__file__).resolve().parents[2]
SYMBOLS_DIR = CYCLE / "configs" / "symbols"
MANIFEST_PATH = CYCLE / "data" / "COVERAGE_MANIFEST.json"
REPORT = CYCLE / "analysis" / "strategy_lane" / "coverage_report.json"
SUMMARY_MD = CYCLE / "analysis" / "strategy_lane" / "coverage_summary.md"

SYMS_10 = {"NQ", "ES", "CL", "NG", "GC", "SI", "6E", "6J", "6B", "6A"}

DAILY_USES_OK = {"signal_reference", "conditional_descriptive", "construction_check"}
BBO_USES_OK = {"cost_evidence", "conditional_descriptive", "construction_check"}
SNAPSHOT_USES_OK = {"conditional_descriptive"}

GAP_FOR_CLASS = {
    "daily_trades_per_contract": "DEPTH_WALL_EXPIRED_RESOLUTION + SETTLEMENT_ONLY_DEEP_BARS",
    "daily_bid_ask": "BID_ASK_NONSYNCHRONOUS_1Y",
    "minute_trades_m1": "INTRADAY_VINTAGE_WALL (2-day snapshots; RTH-only)",
    "hourly_trades_h1": "INTRADAY_VINTAGE_WALL (30-day snapshots; RTH-only)",
    "definitions_reference": "CLASS_PARTIAL_DEFINITIONS",
    "statistics_settlement_oi": "CLASS_ABSENT_STATISTICS",
    "open_interest": "CLASS_ABSENT_OPEN_INTEREST",
    "settlement": "SETTLEMENT_ONLY_DEEP_BARS (derived, not official)",
    "derived_roll_gaps": "derived from daily_trades_per_contract (same gaps)",
}


def corpus_available(cls: str, use: str, symbols: list, manifest: dict) -> tuple:
    """Returns (available: bool, detail: str)."""
    msyms = manifest["symbols"]
    # symbols not in the manifest at all (RB/HO/HG/US/EU/UK/JP/AU macro codes)
    unknown = [s for s in symbols if s not in SYMS_10]
    if unknown and cls in {"daily_trades_per_contract", "daily_bid_ask",
                           "minute_trades_m1", "hourly_trades_h1",
                           "definitions_reference", "statistics_settlement_oi",
                           "open_interest", "settlement"}:
        return False, f"symbol(s) {unknown} not in coverage manifest corpus (10-symbol set)"
    sym = symbols[0] if symbols else None
    have = msyms.get(sym, {}).get("have", {})
    status_key = "daily_trades_per_contract" if cls == "derived_roll_gaps" else cls
    st = have.get(status_key, {}).get("status", "NOT_AVAILABLE")
    if cls in {"daily_trades_per_contract", "derived_roll_gaps"}:
        if use == "backtest_fill":
            run = have.get("daily_trades_per_contract", {}).get(
                "front_chain_real_volume_run_months", 0)
            return False, (f"use=backtest_fill requires DAILY_BT floor >=24m "
                           f"true-volume front chain; manifest run = {run} months "
                           f"(DEPTH_WALL_EXPIRED_RESOLUTION)")
        if use in DAILY_USES_OK:
            return (st != "NOT_AVAILABLE",
                    f"status {st} at legal descriptive depth (floor judgment separate: floor_met)")
        return False, f"use {use} not supported by daily class (status {st})"
    if cls == "daily_bid_ask":
        return (st == "HAVE_PARTIAL" and use in BBO_USES_OK,
                f"status {st}; non-synchronous caveat")
    if cls in {"minute_trades_m1", "hourly_trades_h1"}:
        ok = st == "HAVE_SNAPSHOT_ONLY" and use in SNAPSHOT_USES_OK
        return ok, f"status {st}; snapshot-only (2D M1 / 30D H1, RTH-only)"
    if cls == "definitions_reference":
        return (st == "HAVE_MINIMAL" and use == "construction_check",
                f"status {st}")
    if cls in {"statistics_settlement_oi", "open_interest"}:
        return False, f"status {st} (class absent from IBKR corpus)"
    if cls == "settlement":
        return (st == "HAVE_DERIVED_ONLY" and use in DAILY_USES_OK,
                f"status {st}")
    return False, f"unmapped corpus class {cls}"


def requirement_available(req: dict, manifest: dict) -> tuple:
    cls, use, symbols = req["class"], req["use"], req["symbols"]
    corpus = set(manifest["symbols"]["NQ"]["have"].keys())
    if cls in corpus or cls == "derived_roll_gaps":
        return corpus_available(cls, use, symbols, manifest)
    # external classes
    if cls == "event_release_calendars":
        return True, ("release schedules fetched 2026-10-02, FACT, per dossier S4s "
                      "(Fed/BLS/CFTC/EIA/RBA/ABS/BoE/ECB/BoJ)")
    return False, ("EXTERNAL_NOT_ACQUIRED — see DATA_ACQUISITION_SPEC.md "
                   "(incl. NOT_SOLVED_BY_VENDOR list)")


def verdict_of(requirements: list, manifest: dict, blockers: list) -> dict:
    missing, missing_detail, disagreements = [], {}, []
    for req in requirements:
        avail, detail = requirement_available(req, manifest)
        if not avail:
            key = req["class"] + "(" + ",".join(req["symbols"]) + ")"
            missing.append(key)
            missing_detail[key] = {
                "class": req["class"], "use": req["use"],
                "gap": GAP_FOR_CLASS.get(req["class"], "EXTERNAL_NOT_ACQUIRED"),
                "detail": detail,
                "acquisition": req.get("acquisition", "?"),
            }
        if bool(req.get("available_today")) != avail:
            disagreements.append({
                "class": req["class"], "use": req["use"],
                "config_available_today": bool(req.get("available_today")),
                "recomputed": avail, "detail": detail,
            })
    if missing:
        verdict = "WAIT_DATA"
    elif blockers:
        verdict = "BLOCKED_NONDATA"
    else:
        verdict = "RUNNABLE_NOW"
    return {"verdict": verdict, "missing_data_classes": sorted(set(missing)),
            "missing_detail": missing_detail, "nondata_blockers": blockers,
            "disagreements": disagreements}


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text())
    report = {
        "schema": "futures_behavior_coverage_report@1",
        "task_id": "FUTURES-BEHAVIOR-10SYMS-PREP-20261002",
        "generated_utc": "2026-10-02",
        "coverage_manifest": {
            "path": "data/COVERAGE_MANIFEST.json",
            "lane": manifest.get("lane"),
            "created_utc": manifest.get("created_utc"),
            "front_chain_real_volume_run_months":
                manifest["cross_symbol_observations"]["front_chain_real_volume_run_months"],
        },
        "rules": ("minimal-test availability recomputed from COVERAGE_MANIFEST statuses "
                  "per declared use; scored runs additionally gated by depth floor "
                  "(>=24m true volume), declared slippage, exchange fees, registration"),
        "symbols": {}, "totals": {}, "disagreements": [],
    }
    counts = {"RUNNABLE_NOW": 0, "WAIT_DATA": 0, "BLOCKED_NONDATA": 0}
    scored_blocked_everywhere = True

    for p in sorted(SYMBOLS_DIR.glob("*.yaml")):
        cfg = yaml.safe_load(p.read_text())
        sym = cfg["symbol"]
        run_m = manifest["symbols"][sym]["have"]["daily_trades_per_contract"][
            "front_chain_real_volume_run_months"]
        entry = {"front_chain_real_volume_run_months": run_m, "hypotheses": {}}
        for h in cfg["hypotheses"]:
            minimal = verdict_of(h["minimal_test"]["requirements"], manifest,
                                 h["minimal_test"]["nondata_blockers"])
            scored = verdict_of(h["scored_run"]["requirements"], manifest,
                                h["scored_run"]["nondata_blockers"])
            scored["verdict"] = "BLOCKED_TODAY"
            scored["reasons"] = sorted(set(scored["missing_data_classes"]) |
                                       set(scored["nondata_blockers"]))
            entry["hypotheses"][h["id"]] = {
                "rank": h["rank"],
                "hyp_kind": h["hypothesis_kind"],
                "minimal_test_kind": h["minimal_test"]["kind"],
                "minimal_test": minimal,
                "scored_run": scored,
                "floors_unmet": [
                    {"class": r["class"], "floor": r["floor"]}
                    for r in h["minimal_test"]["requirements"] if not r.get("floor_met", True)],
            }
            counts[minimal["verdict"]] += 1
            report["disagreements"].extend(
                {"hypothesis": h["id"], **d} for d in minimal["disagreements"])
        entry["counts"] = {
            v: sum(1 for x in entry["hypotheses"].values()
                   if x["minimal_test"]["verdict"] == v)
            for v in ("RUNNABLE_NOW", "WAIT_DATA", "BLOCKED_NONDATA")}
        report["symbols"][sym] = entry

    n_hyps = sum(len(e["hypotheses"]) for e in report["symbols"].values())
    report["totals"] = {
        "hypotheses": n_hyps,
        "minimal_test": counts,
        "scored_runs": ("0 possible today: every scored cell is gated by the DAILY_BT "
                        "admission bar (>=24m true-volume front chain; measured 14-17m "
                        "all symbols), owner-declared slippage, NQ/CL-class exchange "
                        "fees (only ES documented), and cycle registration"),
        "disagreements_config_vs_manifest": len(report["disagreements"]),
    }

    REPORT.write_text(json.dumps(report, indent=1) + "\n")

    lines = [
        "# Coverage summary — STRATEGY-CONFIGS lane (2026-10-02)", "",
        "Per-hypothesis data cross-check: `configs/symbols/*.yaml` minimal-test requirements",
        "vs `data/COVERAGE_MANIFEST.json` (data lane, 2026-10-02, read-only).",
        "Verdicts are DATA-AVAILABILITY verdicts for the minimal legal (descriptive) test;",
        "no hypothesis has been run. Scored runs are blocked today for ALL hypotheses",
        "(depth floor >=24m true-volume front chain vs measured 14-17m; declared slippage",
        "missing; exchange fees unfetched except ES; registration required).", "",
        "| symbol | front-chain real-volume (months) | hypotheses | RUNNABLE_NOW | WAIT_DATA | BLOCKED_NONDATA |",
        "|---|---|---|---|---|---|",
    ]
    for sym, e in report["symbols"].items():
        c = e["counts"]
        lines.append(f"| {sym} | {e['front_chain_real_volume_run_months']} | "
                     f"{len(e['hypotheses'])} | {c['RUNNABLE_NOW']} | {c['WAIT_DATA']} "
                     f"| {c['BLOCKED_NONDATA']} |")
    lines += ["", f"**Totals**: {n_hyps} hypotheses — "
              f"{counts['RUNNABLE_NOW']} RUNNABLE_NOW, {counts['WAIT_DATA']} WAIT_DATA, "
              f"{counts['BLOCKED_NONDATA']} BLOCKED_NONDATA (minimal-test level).", "",
              "## RUNNABLE_NOW hypotheses (minimal descriptive test, data in hand)", ""]
    for sym, e in report["symbols"].items():
        for hid, x in sorted(e["hypotheses"].items(), key=lambda kv: kv[1]["rank"]):
            if x["minimal_test"]["verdict"] == "RUNNABLE_NOW":
                lines.append(f"- **{hid}** (rank {x['rank']}) — {x['minimal_test_kind']}"
                             + (f"; floors unmet: " + "; ".join(
                                 f"{f['class']}" for f in x["floors_unmet"])
                                if x["floors_unmet"] else ""))
    lines += ["", "## Top blocking data classes (count of hypotheses waiting)", ""]
    from collections import Counter
    blocker_counts = Counter()
    for sym, e in report["symbols"].items():
        for hid, x in e["hypotheses"].items():
            for cls in x["minimal_test"]["missing_data_classes"]:
                blocker_counts[cls] += 1
    for cls, n in blocker_counts.most_common():
        lines.append(f"- {cls}: {n}")
    lines += ["", f"Config-vs-manifest `available_today` disagreements: "
              f"{len(report['disagreements'])} (recorded as findings in coverage_report.json)", ""]
    SUMMARY_MD.write_text("\n".join(lines) + "\n")

    print(json.dumps({"report": str(REPORT.relative_to(CYCLE)),
                      "summary_md": str(SUMMARY_MD.relative_to(CYCLE)),
                      "totals": report["totals"],
                      "per_symbol_counts": {s: e["counts"] for s, e in report["symbols"].items()}},
                     indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
