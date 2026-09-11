"""CRYPTO-NG1 D2 runner: measures NOVELTY + FEASIBILITY and writes artifacts.

Consumes the frozen S4 set ONLY through the cycle plane adapter (read-only
CADS store), rebuilds the inherited veto panel (V17 six families + V16 daily
forms + generic shadows + the full V17 d2 proxy set), evaluates every
(proposal anchor/neighbour x veto) pair on the exact declared
representation_identity grids, verifies the A5 expiry calendar against the
pinned venue numbers, and writes:

  research/control/crypto_ng1_run/d2/d2_novelty_panel_ng1.json
  research/control/crypto_ng1_run/d2/d2_feasibility_ng1.json
  research/control/crypto_ng1_run/d1/feasibility/feasibility_summary.json

No expectancy / PF / PnL is computed anywhere (outcome-leak ban); the only
return-derived quantities are Pearson/Spearman rho values, which are
invariant to the constant per-decision cost shift (documented in the
artifacts' method blocks).
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve()
_WORKTREE = _HERE.parents[4]
sys.path.insert(0, str(_WORKTREE))

from research.assets.crypto_ng1.plane_adapter import CryptoNG1Plane  # noqa: E402
from research.assets.crypto_ng1.d2 import measure as M               # noqa: E402

D2_DIR = _HERE.parent
RUN_CONTROL = D2_DIR.parent
OUT_NOVELTY = D2_DIR / "d2_novelty_panel_ng1.json"
OUT_FEAS = D2_DIR / "d2_feasibility_ng1.json"
OUT_SUMMARY = RUN_CONTROL / "d1" / "feasibility" / "feasibility_summary.json"

PROPOSAL_FILES = {
    "CNG1-A4-P1": "proposal_A4_P1.json",
    "CNG1-A4-P2": "proposal_A4_P2.json",
    "CNG1-A5-P1": "proposal_A5_P1.json",
    "CNG1-A5-P2": "proposal_A5_P2.json",
}

HYPS = list(PROPOSAL_FILES)


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # ---- data authority (fail-closed; CADS store read-only) ----------------
    plane = CryptoNG1Plane()
    panels = M.load_panels(plane.consume)
    M.register_panel_ts(panels)

    panel_inputs = {}
    for sym in M.SYMBOLS:
        entry = f"staging_v17/panel_{sym}_h1.csv"
        res = plane.consume(entry)
        panel_inputs[entry] = {
            "cads_address": res["cads_address"],
            "sha256_measured": res["sha256_measured"],
            "bytes": res["bytes"],
            "rows": len(panels[sym].hours),
            "first_hour": panels[sym].hours[0],
            "last_hour": panels[sym].hours[-1],
        }

    oi_res = plane.consume("oi_series_reduced.json")
    oi = json.loads(oi_res["data"])
    oi_geom_ok = all(len(oi[s]) == M.OI_SNAPSHOTS_EXPECTED for s in M.SYMBOLS)
    if not oi_geom_ok:
        raise SystemExit("BLOCKED_DATA: oi_series_reduced.json geometry != "
                         "484d x 6 H4 snapshots; fail-closed")
    M.supply_oi(oi)

    funding_path = Path(os.environ.get(
        "CRYPTO_NG1_D2_FUNDING_HISTORY", M.DEFAULT_FUNDING_HISTORY_PATH))

    vp = M.build_veto_panel(panels, str(funding_path))

    # ---- proposal series on the exact declared representations ------------- #
    series = {}
    grid_report = {}
    for hyp in HYPS:
        anchor = M.build_series(panels, hyp, role="anchor")
        neigh = M.build_series(panels, hyp, role="neighbour")
        series[hyp] = {"anchor": anchor, "neighbour": neigh}
        funded = [d for d in anchor if d.status == "FUNDED"]
        blocked = [d for d in anchor if d.status == "BLOCKED_MISSING_BAR"]
        dates = sorted({d.decision_date for d in anchor})
        grid_report[hyp] = {
            "instants": sorted({d.instant for d in anchor}),
            "decision_dates": dates,
            "rows_anchor": len(anchor),
            "funded_anchor": len(funded),
            "unfunded_tie_skips_anchor": sum(
                1 for d in anchor if d.status == "UNFUNDED_SKIP"),
            "blocked_missing_bar_anchor": len(blocked),
            "daily_projection_collapses_rows": any(
                sum(1 for d in anchor
                    if d.symbol == s and d.decision_date == dd) > 1
                for s in M.SYMBOLS for dd in dates),
        }

    # ---- novelty pairs ------------------------------------------------------ #
    proposals_out = {}
    for hyp in HYPS:
        entry = {"grid": grid_report[hyp]}
        for role in ("anchor", "neighbour"):
            pairs = M.evaluate_pairs(series[hyp][role], vp)
            verdict = M.novelty_verdict(pairs, vp)
            entry[role] = {
                "pairs": pairs,
                "novelty": verdict,
            }
        entry["representation"] = {
            "hyp": hyp,
            "series": ("per-decision gross return vector of the arm per the "
                       "frozen representation_identity (see proposal file "
                       + PROPOSAL_FILES[hyp] + ")"),
            "cost_invariance": ("after-cost = gross - constant per decision; "
                                "Pearson shift-invariant, Spearman monotone-"
                                "invariant, so rho is identical at any tier "
                                "constant; no cost constant is invented"),
            "proposal_file_sha256": sha256_file(
                RUN_CONTROL / "d1" / "proposals" / PROPOSAL_FILES[hyp]),
        }
        proposals_out[hyp] = entry

    # ---- cross-proposal (F5 + disjointness) --------------------------------- #
    a4_p1, a4_p2 = series["CNG1-A4-P1"]["anchor"], series["CNG1-A4-P2"]["anchor"]
    a5_p1, a5_p2 = series["CNG1-A5-P1"]["anchor"], series["CNG1-A5-P2"]["anchor"]
    f5_a4 = M.f5_collapse(a4_p1, a4_p2)
    f5_a5 = M.f5_collapse(a5_p1, a5_p2)
    disjoint_a4_a5 = M.date_disjoint(
        grid_report["CNG1-A4-P1"]["decision_dates"],
        sorted(set(grid_report["CNG1-A5-P1"]["decision_dates"])
               | set(grid_report["CNG1-A5-P2"]["decision_dates"])))
    disjoint_a5 = M.date_disjoint(
        grid_report["CNG1-A5-P1"]["decision_dates"],
        grid_report["CNG1-A5-P2"]["decision_dates"])
    cross = {
        "F5_A4_P1_vs_A4_P2": dict(
            f5_a4, rule="pooled |rho| > 0.20 between the two sibling anchor "
                        "per-decision return series collapses the pair"),
        "F5_A5_P1_vs_A5_P2": dict(
            f5_a5, rule="same, daily-aggregated projection; the declared "
                        "grids are quarterly vs non-quarterly last Fridays"),
        "A5_P1_vs_A5_P2_date_disjointness": disjoint_a5,
        "A4_vs_A5_date_disjointness": dict(
            disjoint_a4_a5,
            declared="FOMC instants disjoint from both derivatives grids",
            instant_level_check="FOMC dates are Wednesdays; all A5 grids are "
                                "Fridays (verified by set arithmetic above)"),
    }

    # ---- feasibility + expiry re-verification ------------------------------- #
    expiry = M.reverify_expiry_instants()
    feasibility = {}
    for hyp in HYPS:
        feasibility[hyp] = M.feasibility_for(
            hyp, series[hyp]["anchor"], series[hyp]["neighbour"])

    # ---- combined verdicts --------------------------------------------------- #
    combined = {}
    for hyp in HYPS:
        nov = proposals_out[hyp]["anchor"]["novelty"]
        feas = feasibility[hyp]
        f5_key = ("F5_A4_P1_vs_A4_P2" if hyp.startswith("CNG1-A4")
                  else "F5_A5_P1_vs_A5_P2")
        reasons = []
        if grid_report[hyp]["blocked_missing_bar_anchor"]:
            reasons.append("grid bar missing inside the frozen panel")
        if nov["novelty_verdict"] == "INELIGIBLE_FAIL_CLOSED":
            reasons.append(nov["reason"])
        if hyp.startswith("CNG1-A5") and expiry["verdict"] == "MISMATCH":
            reasons.append("A5 expiry rule/holiday handling does not "
                           "reproduce the pinned venue numbers")
        if reasons:
            verdict = "INELIGIBLE_FAIL_CLOSED"
            reason = "; ".join(reasons)
        elif nov["novelty_verdict"] == "VETO_MEASURED":
            verdict = (f"VETO(margin={nov['margin_to_bar']:+.4f}, worst="
                       f"{nov['worst_pair']}@{nov['worst_abs_rho']:.4f})")
            reason = (f"pooled |rho| {nov['worst_abs_rho']} > 0.20 vs "
                      f"{nov['worst_pair']}; vetoed pairs: "
                      + ", ".join(nov["vetoed_pairs"]))
        elif feas["recent_window"]["verdict"] == "FAIL":
            verdict = "INELIGIBLE_FAIL_CLOSED"
            reason = (f"Q6_RECENT_WINDOW_FLOOR_FAIL: anchor decisions "
                      f"{feas['recent_window']['anchor_decisions']} < floor "
                      f"{M.Q6_ANCHOR_FLOOR} in {feas['recent_window']['start']}"
                      f"..{feas['recent_window']['end']} (measured floor "
                      "failure, pre-disclosed by the lane; not a data gap)")
        else:
            verdict = "ELIGIBLE"
            reason = ("novelty NOVELTY_PASS with min margin "
                      f"{nov['margin_to_bar']:+.4f}; Q6 recent-window "
                      f"{feas['recent_window']['anchor_decisions']} >= "
                      f"{M.Q6_ANCHOR_FLOOR}; turnover ceiling referenced")
        combined[hyp] = {
            "verdict": verdict, "reason": reason,
            "novelty_verdict": nov["novelty_verdict"],
            "novelty_worst_pair": nov["worst_pair"],
            "novelty_worst_abs_rho": nov["worst_abs_rho"],
            "novelty_margin_to_bar": nov["margin_to_bar"],
            "q6_recent_window": feas["recent_window"],
            "f5": cross[f5_key],
        }

    # ---- artifacts ------------------------------------------------------------ #
    code_files = {
        "research/assets/crypto_ng1/d2/measure.py": sha256_file(
            _WORKTREE / "research/assets/crypto_ng1/d2/measure.py"),
        "research/control/crypto_ng1_run/d2/run_d2_measurement.py":
            sha256_file(_HERE),
        "research/assets/crypto_ng1/plane_adapter.py": sha256_file(
            _WORKTREE / "research/assets/crypto_ng1/plane_adapter.py"),
    }

    novelty_artifact = {
        "schema": "crypto_ng1_run/d2_novelty_panel@1",
        "task_id": "crypto-ng1-d2-measurement",
        "cycle_id": "CRYPTO-NG1",
        "lane": "d2",
        "generated_utc": generated,
        "method": {
            "signal": ("per-decision GROSS return vector of each ANCHOR (and "
                       "NEIGH for the ancestry panel) built exactly per the "
                       "proposal representation_identity on the frozen S4 H1 "
                       "panels; pooled across the 3 symbols in symbol-major "
                       "chronological order"),
            "cost_invariance": ("r_net = r - 2c with constant c per arm: "
                                "Pearson is invariant to additive shifts and "
                                "Spearman to monotone transforms, so every "
                                "rho below equals the after-cost rho at ANY "
                                "tier constant; no cost constant invented"),
            "veto_alignment": ("hourly vetoes evaluated on the decision bar "
                               "(closed and PIT at the decision close); "
                               "daily vetoes dated D = the decision's UTC "
                               "date (the inherited V17 exposure-vs-proxy "
                               "convention; level proxies describe the "
                               "decision-day state)"),
            "statistics": ("pooled Pearson + Spearman (average-rank ties); "
                           f"veto bar |rho| > {M.VETO_BAR}; margin = bar - "
                           f"max|rho|; pairs need n >= {M.MIN_PAIRS} aligned "
                           "rows and non-zero variance on both sides, else "
                           "recorded UNMEASURED with a reason (V17 used a "
                           "30-pair guard on multi-thousand-point grids; the "
                           "NG1 frozen D2 series are 12/24 rows by "
                           "declaration, so the guard is the cycle's own "
                           "floor of 8; the 0.20 bar is unchanged)"),
            "pnl_ban": ("no expectancy, PF, PnL or any aggregate of returns "
                        "is computed in this artifact; raw return vectors "
                        "are NOT embedded (reproducible from code + frozen "
                        "panels)"),
        },
        "inputs": {
            "panels": panel_inputs,
            "oi_series": {
                "entry": "oi_series_reduced.json",
                "cads_address": oi_res["cads_address"],
                "sha256_measured": oi_res["sha256_measured"],
                "geometry": f"{M.OI_SNAPSHOTS_EXPECTED} H4 snapshots from "
                            f"{M.OI_WARMUP_START.isoformat()} (V17 pull "
                            "geometry, manifest in the inherited d2 dir)",
            },
            "funding_history": {
                "path": str(funding_path),
                "sha256": (sha256_file(funding_path)
                           if funding_path.exists() else None),
                "role": ("FUNDJUMP funding-LEVEL veto source (V17 endpoint "
                         "pull, READ-ONLY inheritance; BTC/ETH only per the "
                         "family spec)"),
            },
            "fomc_instants": M.FOMC_INSTANTS,
            "code_sha256": code_files,
        },
        "veto_panel": vp.meta,
        "veto_build_failures": vp.build_failures,
        "proposals": proposals_out,
        "cross_proposal": cross,
        "notes": [
            "WKNDLIQ corrected construction: weekday computed from the date "
            "(the V17 D1 bug compared the date string to weekday names and "
            "the Sat/Sun arm never fired; corrected re-measure 0.5628 vs "
            "dvol_level_log). On the NG1 decision grids the flag (and the "
            "weekend/session/dow dummies) are constant by construction -- "
            "recorded DEGENERATE_ZERO_VARIANCE, and the liquidity-level "
            "content the flag proxied for is measured by the varying "
            "dvol_level_log / dvol_shock rows instead.",
            "FUNDJUMP funding-LEVEL veto covers BTCUSDT+ETHUSDT rows only "
            "(the V17 family spec pools BTC/ETH and never had SOL); SOL rows "
            "are excluded from that pair, never imputed (coverage recorded "
            "per pair).",
            "OICASCADE event exposure rebuilt with the SPEC sign (+1); the "
            "inherited V17 code painted -1 -- |rho| is sign-invariant, the "
            "discrepancy is disclosed.",
            "NEIGH series measured for the ancestry panel per "
            "series_d2_measures; the F3 verdict is driven by the ANCHOR "
            "(primary) as declared.",
        ],
    }

    feas_artifact = {
        "schema": "crypto_ng1_run/d2_feasibility@1",
        "task_id": "crypto-ng1-d2-measurement",
        "cycle_id": "CRYPTO-NG1",
        "lane": "d2",
        "generated_utc": generated,
        "panel_window": {
            "first_hour": panels["BTCUSDT"].hours[0],
            "last_hour": panels["BTCUSDT"].hours[-1],
        },
        "q6_policy": {
            "recent_window_months": M.Q6_RECENT_WINDOW_MONTHS,
            "anchor_floor": M.Q6_ANCHOR_FLOOR,
            "recent_window_bounds": M.recent_window_bounds(),
        },
        "per_proposal": feasibility,
        "expiry_reverification": expiry,
        "combined_verdicts": combined,
        "code_sha256": code_files,
        "pnl_ban": ("decision counts, fill counts and referenced cost "
                    "ceilings only; no expectancy/PF/PnL computed"),
    }

    summary = {
        "schema": "crypto_ng1_run/d1_feasibility_summary@1",
        "task_id": "crypto-ng1-d2-measurement",
        "cycle_id": "CRYPTO-NG1",
        "generated_utc": generated,
        "sources": {
            "novelty": "research/control/crypto_ng1_run/d2/d2_novelty_panel_ng1.json",
            "feasibility": "research/control/crypto_ng1_run/d2/d2_feasibility_ng1.json",
        },
        "per_proposal": {
            hyp: {
                "verdict": combined[hyp]["verdict"],
                "reason": combined[hyp]["reason"],
                "novelty_verdict": combined[hyp]["novelty_verdict"],
                "novelty_worst_pair": combined[hyp]["novelty_worst_pair"],
                "novelty_worst_abs_rho": combined[hyp]["novelty_worst_abs_rho"],
                "novelty_margin_to_bar": combined[hyp]["novelty_margin_to_bar"],
                "q6_recent_window_decisions":
                    combined[hyp]["q6_recent_window"]["anchor_decisions"],
                "total_funded_decisions":
                    feasibility[hyp]["total_window"]["funded_decisions_measured"],
                "declared_total_match":
                    feasibility[hyp]["total_window"]["declared_match"],
                "f5": {
                    "status": combined[hyp]["f5"]["status"],
                    "max_abs_rho": combined[hyp]["f5"]["max_abs_rho"],
                    "fired": combined[hyp]["f5"]["f5_fired"],
                },
            } for hyp in HYPS
        },
        "expiry_reverification_verdict": expiry["verdict"],
        "cross_proposal": {
            "A4_P1_vs_P2_f5_fired": cross["F5_A4_P1_vs_A4_P2"]["f5_fired"],
            "A5_P1_vs_P2_f5_status": cross["F5_A5_P1_vs_A5_P2"]["status"],
            "A4_vs_A5_disjoint": disjoint_a4_a5["disjoint"],
            "A5_P1_vs_P2_disjoint": disjoint_a5["disjoint"],
        },
    }

    OUT_NOVELTY.write_text(json.dumps(novelty_artifact, indent=1) + "\n")
    OUT_FEAS.write_text(json.dumps(feas_artifact, indent=1) + "\n")
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_SUMMARY.write_text(json.dumps(summary, indent=1) + "\n")

    print("== D2 combined verdicts (numbers live in the artifacts) ==")
    for hyp in HYPS:
        print(f"  {hyp}: {combined[hyp]['verdict']}")
    print(f"  expiry_reverification: {expiry['verdict']}")
    print(f"  F5 A4: {f5_a4['status']}"
          + (f" max|r|={f5_a4['max_abs_rho']}" if f5_a4["max_abs_rho"]
             is not None else ""))
    print(f"  F5 A5: {f5_a5['status']}")
    print(f"  A4 vs A5 date-disjoint: {disjoint_a4_a5['disjoint']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
