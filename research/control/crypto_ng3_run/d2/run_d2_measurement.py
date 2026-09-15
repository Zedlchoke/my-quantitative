"""Run the CRYPTO-NG3 D2 measurement and emit d2_verdict.json.

Non-scored diagnostics only (plan sections 5-6).  No candidate return
performance, PnL, PF, Sharpe or drawdown is computed or reported.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

_WORKTREE = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_WORKTREE))

from research.assets.crypto_ng3.d2 import measure as M  # noqa: E402

DEFAULT_CADS_STORE = Path("/Users/hoangminhlong/my-quantitative/.runtime/v3_cads_store")

INVENTORY_SOURCES = {
    "ng1_29_shape_inventory": {
        "branch": "orca/crypto-ng1-integration",
        "path": "research/control/crypto_ng1_run/d2/d2_novelty_panel_ng1.json",
        "blob_sha": "6411e6854c422214a92e5bdd0a11d0413659c5c1",
        "shapes": 29, "build_status": "BUILT x29 (committed NG1 d2 artifact, read-only)",
    },
    "ng2_inventory_plus_funding_pull": {
        "branch": "orca/crypto-ng2-integration",
        "path": "research/control/crypto_ng2_run/d2/d2_novelty_panel_ng2.json",
        "blob_sha": "3e979d231413b147a66bfe89c42fbb0a71da1087",
        "shapes": 30, "note": "29-shape triad + cng2_funding_level_pull (funding leg blocked)",
    },
    "shape_definitions_code": {
        "ng1_blob_sha": "c2d16b9ce20cfa73c3baae8ba01fd7de76121c49",
        "ng2_blob_sha": "f595bb03636960846aef04a1ec3d7a8cd50edd21",
    },
    "f1_band_reference": {
        "commit": "5af32da7",
        "path": "research/control/v17_run/d2_a9f_feasibility_v17.json",
        "blob_sha": "a8d93ff94f0599a572ca290920ed95a754d1296c",
    },
    "access_note": ("root .worktrees/crypto-ng1|ng2 directories are empty "
                    "(cleaned); inventory representations consumed read-only "
                    "from the committed branch blobs pinned above"),
}


def main(cads_store: Path = DEFAULT_CADS_STORE, out_path: Path | None = None) -> dict:
    ctrl = _WORKTREE / "research" / "control" / "crypto_ng3_run"
    census_path = ctrl / "p0_census.json"
    dayrows_path = ctrl / "day_rows_usdc_ethereum.json"
    minter_path = ctrl / "minter_table.json"
    census = json.loads(census_path.read_text())
    if census.get("overall_verdict") != "P0_CENSUS_PASS":
        raise SystemExit("BLOCKED: P0 census verdict is not P0_CENSUS_PASS")

    days, net = M.load_day_rows(dayrows_path)
    panels = M.Panels(cads_store)
    a4 = M.build_a4(days, net)
    a5 = M.build_a5(days, net)
    decisions_a4 = M.a4_decisions(days, a4)
    episodes_a5 = a5["episodes"]

    vec4 = {(dec["day"], s): dec["e"] * panels.window_return(
        s, days[dec["entry_idx"]], days[dec["exit_idx"]])
        for dec in decisions_a4 for s in M.SYMBOLS}
    vec5 = {(ep["day"], s): ep["sign"] * panels.window_return(
        s, days[ep["entry_idx"]], days[ep["exit_idx"]])
        for ep in episodes_a5 for s in M.SYMBOLS}
    raw4 = {(dec["day"], s): panels.window_return(
        s, days[dec["entry_idx"]], days[dec["exit_idx"]])
        for dec in decisions_a4 for s in M.SYMBOLS}
    raw5 = {(ep["day"], s): panels.window_return(
        s, days[ep["entry_idx"]], days[ep["exit_idx"]])
        for ep in episodes_a5 for s in M.SYMBOLS}

    shapes = M.build_daily_shapes(panels)
    books4 = M.build_books(panels, decisions_a4, days, "e", shapes, vec4, raw4)
    books5 = M.build_books(panels, episodes_a5, days, "sign", shapes, vec5, raw5)
    table4 = {name: M.rho_pair(x, y) for name, (x, y) in books4.items()}
    table5 = {name: M.rho_pair(x, y) for name, (x, y) in books5.items()}

    # X3 -- rule declared in M.X3_RULE_DECLARED before any rho below is measured
    P = M.build_x3_proxy(panels)
    x3_4 = M.x3_books(panels, decisions_a4, days, "e", vec4, raw4, P)
    x3_5 = M.x3_books(panels, episodes_a5, days, "sign", vec5, raw5, P)
    x3_diag = M.x3_diagnostics(days, net, P, episodes_a5, decisions_a4)

    cal4 = M.calendar_geometry(decisions_a4, episodes_a5)
    q6_shared = M.q6_population(decisions_a4, episodes_a5, int(a4["decidable"].sum()))
    c6_shared = M.c6_strata(days, decisions_a4, episodes_a5, a5["void_counts"])

    out = {
        "schema": M.SCHEMA,
        "task_id": M.TASK_ID,
        "cycle_id": M.CYCLE_ID,
        "role": "d2-measurement (NON-SCORED diagnostics only)",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "worktree": str(_WORKTREE),
        "branch": "orca/cng3-d2",
        "base_head": "ffdf741d7f08192d858e0cef92af13bffd76db0c",
        "pnl_ban": ("no candidate return performance, PnL, PF, Sharpe or drawdown "
                    "computed or reported; only the control-book comparisons the "
                    "vetoes require (same-bet pooled rho) and cost/turnover counts"),
        "method": {
            "rho_bar": M.RHO_BAR,
            "min_pairs": M.MIN_PAIRS,
            "identifiability_bar": M.IDENTIFIABILITY_BAR,
            "shadow_rendering": M.SHADOW_RENDERING_DECLARED,
            "x3_rule_declared_before_measurement": M.X3_RULE_DECLARED,
            "inventory_sources": INVENTORY_SOURCES,
            "conventions": {
                "a4_entry": "close of panel day t+1 (first daily close >= decision_time = t+1 00:12:48Z, C8)",
                "a4_hold": "3 days close-to-close (exit close t+4)",
                "a5_entry": "close of panel day d+1 (first daily close > decision_time = d 23:59:59Z+768s, C8)",
                "a5_hold": "5 panel days (exit close d+6), one position at a time",
                "folds": "C10 frozen; full holding window inside a single fold; margin day 2026-08-22 never a decision/holding day",
                "a4_first_decidable_discrepancy": ("the A4 proposal pins 'first decidable "
                    "panel day = index 70 = 2025-10-31' while its own formula (t-63 >= "
                    "first S index) would admit index 69 (2025-10-30) one day earlier; the "
                    "pinned date governs here (can only remove decisions, never add); "
                    "under a formula-only reading A4 would gain at most 1 decision day"),
            },
        },
        "inputs_consumed": {
            "census_artifacts": {
                "p0_census.json": M.sha256_bytes(census_path.read_bytes()),
                "day_rows_usdc_ethereum.json": M.sha256_bytes(dayrows_path.read_bytes()),
                "minter_table.json": M.sha256_bytes(minter_path.read_bytes()),
                "convention": "digests match the D1 proposals' representation_identity pins (d7b3dd91..., c142ed46..., 9f82b582...)",
            },
            "frozen_panel_objects_readonly": panels.consumed,
            "frozen_panel_objects_source": str(cads_store),
            "funding_series": {"status": "ABSENT",
                               "expected_sha256": M.FUNDING_DIGEST_ABSENT,
                               "reason": M.BLOCKED_LEG_REASON},
        },
        "proposals": {},
        "pooled_rho_table": {"SCNG3-A4-P1": table4, "SCNG3-A5-P1": table5},
    }

    # ---------------- per-proposal verdicts ------------------------------
    for pid, decisions, episodes, table, x3b, vec, rvec in (
        ("SCNG3-A4-P1", decisions_a4, episodes_a5, table4, x3_4, vec4, raw4),
        ("SCNG3-A5-P1", episodes_a5, episodes_a5, table5, x3_5, vec5, raw5),
    ):
        if pid == "SCNG3-A4-P1":
            x5_nulls = {
                "delayed_state_plus1d": M.a4_delayed_null(a4, decisions, vec, rvec, 1),
                "delayed_state_plus3d": M.a4_delayed_null(a4, decisions, vec, rvec, 3),
                "shuffled_within_month": M.a4_shuffled_null(a4, decisions, vec, rvec),
            }
            measured_rts = float(len(decisions))
            declared = {"bound_state_changes_per_symbol_day": 0.4533,
                        "note": "data-free analytic null bound from the proposal (2*Phi(-0.75)); book-level upper bound ~165.5 RT/yr"}
        else:
            x5_nulls = {
                "delayed_state_plus1d": M.a5_delayed_null(panels, days, decisions, vec, rvec, 1),
                "delayed_state_plus3d": M.a5_delayed_null(panels, days, decisions, vec, rvec, 3),
                "shuffled_within_month": M.a5_shuffled_null(panels, days, decisions, vec, rvec),
            }
            measured_rts = float(len(decisions))
            declared = {"point_estimate_gross_round_trips_per_year": 15, "range": "12-18"}

        x1 = M.veto_x1(table)
        x2 = M.veto_x2(table)
        x3 = M.veto_x3(x3b, x3_diag)
        x4 = M.veto_x4(table, cal4)
        x5 = M.veto_x5(x5_nulls)
        f1 = M.veto_f1(measured_rts, declared)
        q6 = q6_shared
        c6 = c6_shared

        vetoes = {"X1_ANCESTRY_RHO": x1, "X2_OI_FUNDING_DEAD_FORMS": x2,
                  "X3_TAPE_FITTED_ISSUANCE": x3, "X4_CLOCK_CALENDAR": x4,
                  "X5_NULL_VALIDITY": x5, "F1_COST_CEILING": f1}
        kill_reasons = []
        for name, v in vetoes.items():
            if v["verdict"] in ("KILL", "INVALID_NULL_KILL"):
                kill_reasons.append(f"{name}:{v['verdict']}")
        # population falsifier (A4 falsifier g / A5 falsifier POPULATION)
        pop = q6["a4"] if pid == "SCNG3-A4-P1" else q6["a5"]
        floor = pop["per_fold_floor"]
        counts = pop["per_fold_eligible_decisions"] if pid == "SCNG3-A4-P1" else pop["per_fold_traded_episodes"]
        unpopulated = {f: c for f, c in counts.items() if c < floor}
        population_verdict = "POPULATED" if not unpopulated else (
            f"NOT_POPULATED folds {sorted(unpopulated)} below floor {floor}")
        if unpopulated:
            kill_reasons.append(f"POPULATION:{sorted(unpopulated)}")

        if kill_reasons:
            overall = "KILL"
            overall_note = "measured veto fired: " + "; ".join(kill_reasons)
        else:
            overall = "NOT_RUN_BLOCKED_FAIL_CLOSED"
            overall_note = ("no measured veto fired and folds populated, but "
                            "X1/X2/F1 carry NOT_RUN_BLOCKED legs (funding series "
                            "bytes absent, network pulls forbidden by lane budget) "
                            "-> survival cannot be certified from this lane; "
                            "measured margins recorded for the S lane")

        out["proposals"][pid] = {
            "anchor": ("aggregate 7d net-flow z-state, |z|>=0.75, entry close t+1, hold 3d"
                       if pid == "SCNG3-A4-P1" else
                       "burst-episode transition: b_d >= trailing P95 theta, entry close d+1, hold 5d"),
            "decision_counts": {"eligible_decisions" if pid == "SCNG3-A4-P1" else "traded_episodes": len(decisions)},
            "vetoes": vetoes,
            "q6_population": q6,
            "c6_strata": c6,
            "population_verdict": population_verdict,
            "verdict": overall,
            "verdict_note": overall_note,
        }

    kills = [p for p, v in out["proposals"].items() if v["verdict"] == "KILL"]
    if len(kills) == len(out["proposals"]):
        out["overall_verdict"] = "VETO_ALL"
    elif kills:
        out["overall_verdict"] = "PARTIAL_FAIL_CLOSED"
    else:
        out["overall_verdict"] = "PARTIAL_FAIL_CLOSED"
    out["overall_note"] = (
        "fail-closed: the frozen funding-rate series is not accessible in this "
        "lane (untracked bytes absent; network pulls forbidden), so X1/X2/F1 "
        "carry NOT_RUN_BLOCKED legs and no proposal can be certified SURVIVE; "
        "measured margins for every veto are recorded above. "
        + (f"Measured kills: {kills}. " if kills else "No measured veto fired. ")
        + "Plan sec 6: a measured kill is the system working."
    )

    if out_path is None:
        out_path = ctrl / "d2" / "d2_verdict.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(out, indent=1, default=str))
    return out


if __name__ == "__main__":
    store = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CADS_STORE
    result = main(store)
    print("overall_verdict:", result["overall_verdict"])
    for pid, v in result["proposals"].items():
        print(pid, "->", v["verdict"])
        for name, veto in v["vetoes"].items():
            print("  ", name, veto["verdict"], veto.get("margin"))
