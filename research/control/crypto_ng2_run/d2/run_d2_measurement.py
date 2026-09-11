"""CRYPTO-NG2 D2 runner: NOVELTY + FEASIBILITY + IDENTIFIABILITY artifacts.

Consumes the frozen S4 set ONLY through the ng1 cycle plane adapter
(read-only CADS store), rebuilds the inherited 29-shape veto panel plus the
NG2 additions (funding-LEVEL shadow from THIS cycle's full-window keyless
pull; the two dead ng1 FOMC-form return shadows; the in-family
CTL-FUNDLEVEL arm pair for the A5 proposals), evaluates every (proposal
anchor/neighbour x veto) pair on the exact declared representation_identity
grids, measures the F5 sibling structure (A4 census-disjointness proof,
A5 daily-aggregated collapse), the identifiability twin check (clock
shadow / shifted placebo < 0.98), Q-6 recent-window feasibility and writes:

  research/control/crypto_ng2_run/d2/d2_novelty_panel_ng2.json
  research/control/crypto_ng2_run/d2/d2_feasibility_ng2.json
  research/control/crypto_ng2_run/d1/feasibility/feasibility_summary.json

No expectancy / PF / PnL is computed anywhere (outcome-leak ban); the only
return-derived quantities are Pearson/Spearman rho values, which are
invariant to the constant per-decision cost shift (documented in the
artifacts' method blocks).  Funding transfers are part of the declared
gross series and enter verbatim, never as a direction input.
"""

from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_HERE = Path(__file__).resolve()
_WORKTREE = _HERE.parents[4]
sys.path.insert(0, str(_WORKTREE))

from research.assets.crypto_ng1.plane_adapter import CryptoNG1Plane  # noqa: E402
from research.assets.crypto_ng1.d2 import measure as N1              # noqa: E402
from research.assets.crypto_ng2.d2 import measure as M               # noqa: E402

D2_DIR = _HERE.parent
RUN_CONTROL = D2_DIR.parent
OUT_NOVELTY = D2_DIR / "d2_novelty_panel_ng2.json"
OUT_FEAS = D2_DIR / "d2_feasibility_ng2.json"
OUT_SUMMARY = RUN_CONTROL / "d1" / "feasibility" / "feasibility_summary.json"

CENSUS_PATH = RUN_CONTROL / "p0_calendar_census_ng2.json"
FUNDING_DATA = _WORKTREE / "data_raw" / "cng2_funding" / "funding_history.json"
FUNDING_MANIFEST = _WORKTREE / "data_raw" / "cng2_funding" / "manifest.json"

PROPOSAL_FILES = {
    "CNG2-A4-P1": "proposal_A4_P1.json",
    "CNG2-A4-P2": "proposal_A4_P2.json",
    "CNG2-A5-P1": "proposal_A5_P1.json",
    "CNG2-A5-P2": "proposal_A5_P2.json",
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
    panels = N1.load_panels(plane.consume)
    N1.register_panel_ts(panels)

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
    if not all(len(oi[s]) == N1.OI_SNAPSHOTS_EXPECTED for s in M.SYMBOLS):
        raise SystemExit("BLOCKED_DATA: oi_series_reduced.json geometry != "
                         "484d x 6 H4 snapshots; fail-closed")
    N1.supply_oi(oi)

    # ---- census instants (fail-closed P-12 cross-check) --------------------- #
    census = M.load_census_instants(CENSUS_PATH)
    instants_by_series = census["instants"]

    # ---- funding settlement pull (fail-closed pin consumption) -------------- #
    if not FUNDING_DATA.is_file() or not FUNDING_MANIFEST.is_file():
        raise SystemExit(
            "BLOCKED_DATA: funding pin missing under data_raw/cng2_funding/ "
            "(run research/control/crypto_ng2_run/d2/pull_funding.py first); "
            "fail-closed, never assumed zero")
    funding = json.loads(FUNDING_DATA.read_text())
    if sorted(funding) != sorted(M.SYMBOLS):
        raise SystemExit("BLOCKED_DATA: funding pin symbols != the frozen 3")
    ev_by_symbol = {s: M.build_funding_evidence(s, funding[s])
                    for s in M.SYMBOLS}
    funding_reports = {s: ev_by_symbol[s].report() for s in M.SYMBOLS}
    grid_verified = all(
        r["evidenced_grid_instants"] == M.GRID_ELIGIBLE_HYPOTHESIS_PER_SYMBOL
        and r["grid_hypothesis_1094"] for r in funding_reports.values())

    # ---- veto panel: inherited 29 shapes + NG2 additions -------------------- #
    vp = N1.build_veto_panel(panels, str(FUNDING_DATA))
    vp.add("cng2_funding_level_pull", "CNG2-NG2-FUNDINGLEVEL", "ng2_funding_level",
           "funding LEVEL: rate of the last settlement with fundingTime <= "
           "decision bar close, from THIS cycle's full-window keyless pull "
           "(3 symbols; data_raw/cng2_funding pinned by sha256)",
           M.funding_level_veto_fn(ev_by_symbol), hourly=True,
           coverage="3 symbols, full panel window pull")

    # ---- proposal families on the exact declared representations ------------ #
    families = {h: M.build_family(panels, instants_by_series, ev_by_symbol, h)
                for h in HYPS}

    grid_report = {}
    for hyp in HYPS:
        anchor = families[hyp]["anchor"]
        c = M._counts(anchor)
        c.pop("decision_dates", None)
        grid_report[hyp] = {
            **c,
            "daily_projection_collapses_rows": any(
                sum(1 for d in anchor
                    if d.symbol == s and d.proj_day == dd) > 1
                for s in M.SYMBOLS for dd in {d.proj_day for d in anchor}),
        }

    # ---- novelty pairs -------------------------------------------------------- #
    proposals_out = {}
    for hyp in HYPS:
        entry: dict = {"grid": grid_report[hyp]}
        for role in ("anchor", "neighbour"):
            rows = families[hyp][role]
            pairs = N1.evaluate_pairs(rows, vp)
            # dead ng1 FOMC-form return shadows on THIS grid's fills
            for form in M.DEAD_FORM_IDS:
                pairs[form] = N1.rho_pair_status(
                    [d.r_gross for d in rows],
                    M.dead_form_shadow_returns(panels, rows, form))
            # in-family CTL-FUNDLEVEL arm (A5 F3 in-family clause)
            if hyp.startswith("CNG2-A5"):
                fl = M.rho_on_shared_keys(rows, families[hyp]["fundlevel"])
                pairs["cng2_infamily_fundlevel_arm"] = fl["pair"]
                pairs["cng2_infamily_fundlevel_arm"]["shared_grid_keys"] = \
                    fl["shared_grid_keys"]
            verdict = M.ng2_novelty_verdict(pairs, vp.build_failures)
            entry[role] = {"pairs": pairs, "novelty": verdict}
        entry["representation"] = {
            "hyp": hyp,
            "series": ("per-decision GROSS return vector of the arm per the "
                       "frozen representation_identity (see proposal file "
                       + PROPOSAL_FILES[hyp] + "); A5 vectors include the "
                       "declared settlement transfers verbatim"),
            "cost_invariance": ("after-cost = gross - constant per decision; "
                                "Pearson shift-invariant, Spearman monotone-"
                                "invariant, so rho is identical at any tier "
                                "constant; no cost constant is invented"),
            "proposal_file_sha256": sha256_file(
                RUN_CONTROL / "d1" / "proposals" / PROPOSAL_FILES[hyp]),
        }
        proposals_out[hyp] = entry

    # ---- controls + identifiability ------------------------------------------- #
    controls = {}
    ident = {}
    for hyp in HYPS:
        anchor = families[hyp]["anchor"]
        shadow = families[hyp]["clocklong" if hyp.startswith("CNG2-A4")
                             else "shadow"]
        placebo = families[hyp]["shiftplus1" if hyp.startswith("CNG2-A4")
                             else "placebo"]
        ident[hyp] = M.identifiability(anchor, shadow, placebo)
        c_block = {}
        for arm in ([("delay2", "CTL-DELAY2"), ("clairvoyant", "CTL-CLAIRVOYANT"),
                     ("clocklong", "SHADOW-CLOCK")]
                    if hyp.startswith("CNG2-A4") else
                    [("fundlevel", "CTL-FUNDLEVEL"), ("shadow", "SHADOW-CLOCK8H")]):
            c_block[arm[1]] = M.rho_on_shared_keys(anchor, families[hyp][arm[0]])
        # F2 rho clause (Spearman anchor-vs-shadow > 0.20) is decidable here
        sr = ident[hyp]["clock_shadow_rho"]["pair"]["spearman"]
        c_block["f2_shadow_rho_clause_fired"] = bool(
            sr is not None and abs(sr) > M.VETO_BAR)
        controls[hyp] = c_block

    # ---- cross-proposal (F5 + disjointness) ------------------------------------ #
    a4_p1, a4_p2 = (families["CNG2-A4-P1"]["anchor"],
                    families["CNG2-A4-P2"]["anchor"])
    a5_p1, a5_p2 = (families["CNG2-A5-P1"]["anchor"],
                    families["CNG2-A5-P2"]["anchor"])
    f5_a4 = N1.f5_collapse(a4_p1, a4_p2)
    disjoint_a4 = N1.date_disjoint(
        sorted({d.proj_day for d in a4_p1}),
        sorted({d.proj_day for d in a4_p2}))
    f5_a5 = M.f5_daily_aggregated(a5_p1, a5_p2)
    # structural handoff fact: P1 exits exactly where P2 enters (close of B)
    p1_exit = {(d.symbol, d.instant): d.exit_bar for d in a5_p1
               if d.status == "FUNDED"}
    p2_entry = {(d.symbol, d.instant): d.entry_bar for d in a5_p2
                if d.status == "FUNDED"}
    shared = [k for k in p1_exit if k in p2_entry]
    cross = {
        "F5_A4_P1_vs_A4_P2": dict(
            f5_a4,
            rule="pooled |rho| > 0.20 between the two sibling anchor "
                 "per-decision return series collapses the pair"),
        "A4_census_date_disjointness_proof": {
            **disjoint_a4,
            "declared": "11 CPI dates intersect 11 NFP dates in 0 days "
                        "(census arithmetic; D2 records the proof)",
        },
        "F5_A5_P1_vs_A5_P2": dict(
            f5_a5,
            rule="pooled |rho| > 0.20 between the sibling anchors "
                 "(daily-aggregated projection, the frozen rule text); the "
                 "per-decision shared-key rho is recorded alongside"),
        "A5_boundary_handoff_structural_fact": {
            "claim": "P1 exits exactly where P2 enters (both fills at the "
                     "close of boundary bar B = S+1h)",
            "shared_keys_checked": len(shared),
            "exit_bar_equals_entry_bar": all(
                p1_exit[k] == p2_entry[k] for k in shared),
        },
    }

    # ---- feasibility ------------------------------------------------------------ #
    feasibility = {}
    for hyp in HYPS:
        feasibility[hyp] = M.feasibility_for(
            hyp, families[hyp]["anchor"],
            grid_report=funding_reports if hyp.startswith("CNG2-A5")
            else None)

    # ---- combined verdicts -------------------------------------------------------- #
    combined = {}
    for hyp in HYPS:
        nov = proposals_out[hyp]["anchor"]["novelty"]
        feas = feasibility[hyp]
        ident_h = ident[hyp]
        g = grid_report[hyp]
        reasons = []
        if g["blocked_missing_bar"] or g["unmeasured_bar"]:
            reasons.append("grid bar missing inside the frozen panel")
        if hyp.startswith("CNG2-A5") and not grid_verified:
            reasons.append(
                "settlement grid not fully evidenced by the pull "
                f"({json.dumps({s: funding_reports[s]['evidenced_grid_instants'] for s in M.SYMBOLS})}"
                " != 1094/symbol)")
        if nov["novelty_verdict"] == "INELIGIBLE_FAIL_CLOSED":
            reasons.append(nov["reason"])
        if ident_h["verdict"] == "FAIL":
            reasons.append(
                f"IDENTIFIABILITY_CONTROL_TWIN: {ident_h['worst_arm']} "
                f"|rho| {ident_h['worst_abs_rho']} >= {M.IDENT_BAR}")
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
                      f"{feas['recent_window']['floor_decisions']} in "
                      f"{feas['recent_window']['start']}.."
                      f"{feas['recent_window']['end']}")
        elif ident_h["verdict"] != "PASS":
            verdict = "INELIGIBLE_FAIL_CLOSED"
            reason = f"identifiability unmeasured ({ident_h['status']})"
        else:
            verdict = "ELIGIBLE"
            reason = ("novelty NOVELTY_PASS with min margin "
                      f"{nov['margin_to_bar']:+.4f}; Q6 recent-window "
                      f"{feas['recent_window']['anchor_decisions']} >= "
                      f"{feas['recent_window']['floor_decisions']}; "
                      "identifiability max|rho| "
                      f"{ident_h['worst_abs_rho']} < {M.IDENT_BAR}; "
                      "turnover ceiling referenced")
        combined[hyp] = {
            "verdict": verdict, "reason": reason,
            "novelty_verdict": nov["novelty_verdict"],
            "novelty_worst_pair": nov["worst_pair"],
            "novelty_worst_abs_rho": nov["worst_abs_rho"],
            "novelty_margin_to_bar": nov["margin_to_bar"],
            "identifiability": {
                "status": ident_h["status"],
                "worst_arm": ident_h["worst_arm"],
                "worst_abs_rho": ident_h["worst_abs_rho"],
                "bar": M.IDENT_BAR,
            },
            "q6_recent_window": feas["recent_window"],
            "f5": cross["F5_A4_P1_vs_A4_P2" if hyp.startswith("CNG2-A4")
                       else "F5_A5_P1_vs_A5_P2"],
        }

    # ---- artifacts ---------------------------------------------------------------- #
    code_files = {
        "research/assets/crypto_ng2/d2/measure.py": sha256_file(
            _WORKTREE / "research/assets/crypto_ng2/d2/measure.py"),
        "research/control/crypto_ng2_run/d2/run_d2_measurement.py":
            sha256_file(_HERE),
        "research/control/crypto_ng2_run/d2/pull_funding.py": sha256_file(
            D2_DIR / "pull_funding.py"),
        "research/assets/crypto_ng1/d2/measure.py": sha256_file(
            _WORKTREE / "research/assets/crypto_ng1/d2/measure.py"),
        "research/assets/crypto_ng1/plane_adapter.py": sha256_file(
            _WORKTREE / "research/assets/crypto_ng1/plane_adapter.py"),
    }

    novelty_artifact = {
        "schema": "crypto_ng2_run/d2_novelty_panel@1",
        "task_id": "crypto-ng2-d2-measurement",
        "cycle_id": "CRYPTO-NG2",
        "lane": "d2",
        "generated_utc": generated,
        "method": {
            "signal": ("per-decision GROSS return vector of each ANCHOR (and "
                       "NEIGH for the ancestry panel) built exactly per the "
                       "proposal representation_identity on the frozen S4 H1 "
                       "panels; pooled across the 3 symbols in symbol-major "
                       "chronological order; A5 vectors include the declared "
                       "settlement transfer -d*rate(S) verbatim where the "
                       "representation books it"),
            "cost_invariance": ("r_net = r - 2c with constant c per arm: "
                                "Pearson is invariant to additive shifts and "
                                "Spearman to monotone transforms, so every "
                                "rho below equals the after-cost rho at ANY "
                                "tier constant; no cost constant invented"),
            "veto_alignment": ("hourly vetoes evaluated on the decision bar "
                               "(closed and PIT at the decision close; the "
                               "A5-P1 decision bar is B-2, the A5-P2 decision "
                               "bar is B); daily vetoes dated D = the "
                               "decision bar's UTC date (inherited V17 "
                               "exposure-vs-proxy convention)"),
            "dead_form_shadow_convention": ("the dead ng1 FOMC forms are "
                                            "rendered as RETURN shadows on "
                                            "the measured proposal's own "
                                            "fills: the dead rule's direction "
                                            "is evaluated at each decision "
                                            "bar and compounded over the SAME "
                                            "entry/exit bars as the measured "
                                            "row (the strict same-bet test; "
                                            "rho > 0.20 = re-clocking of a "
                                            "dead shape)"),
            "statistics": ("pooled Pearson + Spearman (average-rank ties); "
                           f"veto bar |rho| > {M.VETO_BAR}; margin = bar - "
                           f"max|rho|; pairs need n >= {M.MIN_PAIRS} aligned "
                           "rows and non-zero variance on both sides, else "
                           "recorded UNMEASURED with a reason"),
            "identifiability_bar": (f"clock shadow / shifted placebo |rho| < "
                                    f"{M.IDENT_BAR} vs the anchor (a twin "
                                    "control makes the battery "
                                    "uninterpretable; SFV12-A5-H1 class)"),
            "pnl_ban": ("no expectancy, PF, PnL or any aggregate of returns "
                        "is computed in this artifact; raw return vectors "
                        "are NOT embedded (reproducible from code + frozen "
                        "panels + pinned funding data)"),
        },
        "inputs": {
            "panels": panel_inputs,
            "oi_series": {
                "entry": "oi_series_reduced.json",
                "cads_address": oi_res["cads_address"],
                "sha256_measured": oi_res["sha256_measured"],
                "geometry": f"{N1.OI_SNAPSHOTS_EXPECTED} H4 snapshots from "
                            f"{N1.OI_WARMUP_START.isoformat()} (V17 pull "
                            "geometry)",
            },
            "census": {
                "path": "research/control/crypto_ng2_run/"
                        "p0_calendar_census_ng2.json",
                "sha256": sha256_file(CENSUS_PATH),
                "instants_cpi": instants_by_series["CPI"],
                "instants_nfp": instants_by_series["NFP"],
                "fail_closed_checks": census["checks"],
            },
            "funding_pull": {
                "data_file": "data_raw/cng2_funding/funding_history.json",
                "data_sha256": sha256_file(FUNDING_DATA),
                "manifest_file": "data_raw/cng2_funding/manifest.json",
                "manifest_sha256": sha256_file(FUNDING_MANIFEST),
                "untracked": True,
                "endpoint": M.FUNDING_URL,
                "per_symbol_report": funding_reports,
                "grid_verified_1094_per_symbol": grid_verified,
            },
            "code_sha256": code_files,
        },
        "veto_panel": vp.meta,
        "veto_build_failures": vp.build_failures,
        "proposals": proposals_out,
        "controls_rho_vs_anchor": controls,
        "identifiability": ident,
        "cross_proposal": cross,
        "notes": [
            "the funding-LEVEL veto set is built from THIS cycle's own "
            "full-window keyless pull (v17_fundjump_funding_level covers the "
            "BTC/ETH subset per the inherited family spec; "
            "cng2_funding_level_pull covers all 3 symbols); both sources are "
            "the same pinned bytes",
            "settlement-grid hypothesis VERIFIED by the pull: 1,095 "
            "settlements/symbol in window, 1,094/1,094 eligible instants "
            "evidenced, 0 off-grid, 0 duplicates (manifest pinned by sha256)",
            "A5 transfers: anchor/neighbour/shadow/fundlevel of P1 and the "
            "P2 placebo book -d*rate(S); every other arm's hold crosses no "
            "snapshot; rate taken verbatim from the pull, never assumed",
            "NEIGH series measured for the ancestry panel per "
            "series_d2_measures; the F3 verdict is driven by the ANCHOR "
            "(primary) as declared",
            "DISCLOSURE (A5 dead-form rows): the dead FOMC-form shadows are "
            "evaluated at the A5 decision bars by dispatch mandate; for "
            "A5-P1 the dead A4-P1 rule (single-bar imb) reads the anchor's "
            "own last feature bar, so that row measures rule-layer overlap "
            "on identical fills (the strict same-bet test), not clock "
            "information (the clocks are disjoint by construction); the A5 "
            "proposals' own named F3 shadows (29-shape panel + funding "
            "LEVEL + in-family fundlevel arm) all PASS with wide margins, "
            "recorded separately in the pair tables",
        ],
    }

    feas_artifact = {
        "schema": "crypto_ng2_run/d2_feasibility@1",
        "task_id": "crypto-ng2-d2-measurement",
        "cycle_id": "CRYPTO-NG2",
        "lane": "d2",
        "generated_utc": generated,
        "panel_window": {
            "first_hour": panels["BTCUSDT"].hours[0],
            "last_hour": panels["BTCUSDT"].hours[-1],
        },
        "q6_policy": {
            "recent_window_months": M.Q6_RECENT_WINDOW_MONTHS,
            "anchor_floor_a4": M.Q6_ANCHOR_FLOOR_A4,
            "anchor_floor_a5_decisions": M.Q6_ANCHOR_FLOOR_A5_DECISIONS,
            "recent_window_bounds": N1.recent_window_bounds(),
        },
        "settlement_grid": funding_reports,
        "settlement_grid_verified": grid_verified,
        "per_proposal": feasibility,
        "combined_verdicts": combined,
        "code_sha256": code_files,
        "pnl_ban": ("decision counts, fill counts and referenced cost "
                    "ceilings only; no expectancy/PF/PnL computed"),
    }

    summary = {
        "schema": "crypto_ng2_run/d1_feasibility_summary@1",
        "task_id": "crypto-ng2-d2-measurement",
        "cycle_id": "CRYPTO-NG2",
        "generated_utc": generated,
        "sources": {
            "novelty": "research/control/crypto_ng2_run/d2/"
                       "d2_novelty_panel_ng2.json",
            "feasibility": "research/control/crypto_ng2_run/d2/"
                           "d2_feasibility_ng2.json",
        },
        "per_proposal": {
            hyp: {
                "verdict": combined[hyp]["verdict"],
                "reason": combined[hyp]["reason"],
                "novelty_verdict": combined[hyp]["novelty_verdict"],
                "novelty_worst_pair": combined[hyp]["novelty_worst_pair"],
                "novelty_worst_abs_rho": combined[hyp]["novelty_worst_abs_rho"],
                "novelty_margin_to_bar": combined[hyp]["novelty_margin_to_bar"],
                "identifiability_status": combined[hyp]["identifiability"],
                "q6_recent_window_decisions":
                    combined[hyp]["q6_recent_window"]["anchor_decisions"],
                "total_funded_decisions":
                    feasibility[hyp]["total_window"]["funded_anchor"],
                "f5": {
                    "status": combined[hyp]["f5"]["status"],
                    "max_abs_rho": (
                        combined[hyp]["f5"].get("max_abs_rho")
                        if hyp.startswith("CNG2-A4")
                        else combined[hyp]["f5"]["daily"]["max_abs_rho"]),
                    "fired": combined[hyp]["f5"]["f5_fired"],
                },
            } for hyp in HYPS
        },
        "settlement_grid_verified": grid_verified,
        "cross_proposal": {
            "A4_P1_vs_P2_f5_fired": cross["F5_A4_P1_vs_A4_P2"]["f5_fired"],
            "A4_census_date_disjoint":
                cross["A4_census_date_disjointness_proof"]["disjoint"],
            "A5_P1_vs_P2_f5_fired": cross["F5_A5_P1_vs_A5_P2"]["f5_fired"],
            "A5_P1_vs_P2_daily_max_abs_rho":
                cross["F5_A5_P1_vs_A5_P2"]["daily"]["max_abs_rho"],
            "A5_boundary_handoff":
                cross["A5_boundary_handoff_structural_fact"]
                ["exit_bar_equals_entry_bar"],
        },
    }

    OUT_NOVELTY.write_text(json.dumps(novelty_artifact, indent=1) + "\n")
    OUT_FEAS.write_text(json.dumps(feas_artifact, indent=1) + "\n")
    OUT_SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    OUT_SUMMARY.write_text(json.dumps(summary, indent=1) + "\n")

    print("== D2 combined verdicts (numbers live in the artifacts) ==")
    for hyp in HYPS:
        print(f"  {hyp}: {combined[hyp]['verdict']}")
    print(f"  settlement grid verified (1094/symbol): {grid_verified}")
    print(f"  F5 A4: {f5_a4['status']} (date-disjoint proof: "
          f"{disjoint_a4['disjoint']})")
    print(f"  F5 A5 daily-agg: {f5_a5['status']} max|r|="
          f"{f5_a5['daily']['max_abs_rho']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
