"""RATES-NG1 E-phase SCORED EXECUTION driver (task rates-ng1-e-scored).

Lane E consumes the GO phrase "GO RATES NG1 SCORED EXECUTION" -- typed by
the A1 Lead at this cycle's OWN gate under owner standing delegation
after the A7 prelaunch audit returned RATES_NG1_S0_LAUNCH_AUTHORIZED
(zero unresolved HIGH/CRITICAL; adjudication committed at
research/control/rates_ng1_run/audits/lead_adjudication_a7.json, base
f4a5ba0d) -- and computes the 3 FROZEN scored cells ONE AT A TIME
through the FROZEN I-phase runners only (research/assets/rates_ng1/ is
READ-ONLY; this module never edits it) on the REAL frozen substrate:

  RATESNG1-A5-P1-ARM-NEUTRAL      33b78baa  (anchor variant)
  RATESNG1-A5-P1-ARM-CONSERVATIVE 54ef5def  (anchor variant)
  RATESNG1-A5-P1-ARM-AGGRESSIVE   cfdad940  (anchor variant)

Laws enforced here (all inherited, none invented):

- machine-wide heavy lock held for the whole scored run (RATES-NG1 /
  E_SCORED); pre-run inspect must be FREE_PROVEN; refusal is
  NOT_RUN_RESOURCE_CONFLICT, never a spin, never contention;
- every arm_config_digest must reproduce the committed S-freeze pin AND
  the dispatch-packet digest prefix before any PnL (fail-closed);
- committed-artifact pins re-measured (freeze / census / cost contract /
  substrate manifest) and the plane verify-on-read gate re-run before
  any PnL;
- PnL identity: tier-2.0 PRIMARY, once-per-fill spread on BOTH legs +
  ACT/365F expense drag, through the P1 DualBookLedger exactly as the
  Z rehearsed it; the per-leg mirror arithmetic is tied back to the
  kernel's own recorded rows (signed_surface_reconciled) or TECHABORT;
- DETERMINISM GATE: every per-cell outcome digest produced here must
  equal the sha256 pin committed in the Z report
  (research/control/rates_ng1_run/z/z_report.json): per-decision edges,
  round-trip outcome structure, every control's edge series, the frozen
  battery comparator verdict, and every kernel ledger digest.  Any
  mismatch is a genuine technical failure => TECHABORT, no numbers
  published.  This proves the scored run executes the exact rehearsed
  pipeline before the numbers are revealed.
- R1-R6 evaluated by the FROZEN evaluator
  (runners.rules.evaluate_r1_r6) on the real per-decision after-cost
  edge series, fail-closed: a rule whose metric is missing/not
  computable is NOT_RUN, never an inferred PASS; any NOT_RUN blocks
  survivor; PBO is NOT_RUN_FAIL_CLOSED (3 < 8 cells, frozen law);
- A7-R1 BINDING (adjudication, pre-scored, carried verbatim from the
  dispatch packet): any control row with n_pairs == 0 is NOT_EXECUTABLE
  and contributes NEITHER a kill NOR a pass; R2 for the affected arm is
  decided by the remaining executable limbs only; the NOT_EXECUTABLE
  disclosure travels into every affected artifact row.
- NO rescue, NO threshold move, NO re-run for bad numbers (P-15).  The
  ONLY phase where outcome numbers are lawful is this scored run; they
  are cited in the committed e/ artifacts.

Conventions this lane fixes (disclosed in every artifact that uses
them):

- the per-decision after-cost edge of a round trip (BOTH legs, tier
  2.0) is attributed to its ENTRY decision instant; the persisted
  per-period series is aligned to the 1918 bookable instants (None =
  no edge defined at the instant: no entry or UNDEFINED upstream state
  -- Q-11: never inferred as zero); persisted for the future DSR P-11
  pass;
- expectancy = mean defined per-decision net tier-2.0 edge (R1);
- profit factor = gross win / gross loss of the per-decision net
  tier-2.0 edge series; with NO losing edge it is UNDEFINED (None, the
  frozen rules.profit_factor law: Q-11 -- never inferred infinite) and
  R4 is NOT_RUN;
- R6 gross concentration: per-instant GROSS = before-cost signed
  BOTH-leg figure (mirror arithmetic pre-cost, sign-applied)
  attributed to the entry instant; share = instant gross / total gross;
  total gross <= 0 makes shares undefined (fail-closed, R6 not passed);
- drop-one-fold survival is the frozen evaluator's own semantics
  (mean excluding each fold > 0).

Usage:
    .venv/bin/python research/control/rates_ng1_run/e/run_scored.py
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import time
import traceback

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.rates_ng1 import plane_adapter as pa     # noqa: E402
from research.assets.rates_ng1.runners.battery import (       # noqa: E402
    KILLER_ROLES,
    battery_verdict,
)
from research.assets.rates_ng1.runners.rules import (         # noqa: E402
    FROZEN_RULE_ORDER,
    PBO_MIN_CELLS,
    R1_EXPECTANCY_GT,
    R3_MIN_POSITIVE_FOLDS,
    R4_PF_MIN,
    R6_MAX_SINGLE_INSTANT_GROSS_SHARE,
    evaluate_r1_r6,
    pbo_record,
)
from research.assets.rates_ng1.runners.runner import (        # noqa: E402
    FOLD_WINDOWS,
    RunnerLawError,
    assemble_cell_configs,
    book_round_trips,
    clock_only_state,
    curve_coordinates,
    fold_of_session,
    level_control_state,
    load_representation,
    misaligned_state,
    positions_from_states,
    round_trip_leg_signed_pnl,
    run_arm,
)
from research.control.rates_ng1_run.z import z_run            # noqa: E402
from research.governance import heavy_lock                    # noqa: E402

SCHEMA = "rates_ng1_run/e_scored@1"
CELL_SCHEMA = "rates_ng1_run/e_cell@1"
FAMILY_SCHEMA = "rates_ng1_run/e_family_verdicts@1"
GATE_SCHEMA = "rates_ng1_run/e_gate@1"

CYCLE_ID = "RATES-NG1"
TASK_ID = "rates-ng1-e-scored"
ROLE = "quant-implementer"
LANE = "e"

DISPATCH_SHA = "f4a5ba0dc52d67f938726d9de440da8d41f4b0b8"
BRANCH = "orca/rates-ng1-integration"
WORKTREE = "/Users/hoangminhlong/my-quantitative/.worktrees/rates-ng1/integration"

E_DIR = os.path.dirname(os.path.abspath(__file__))
CONTROL_DIR = os.path.dirname(E_DIR)
REPO = REPO_ROOT
FREEZE_PATH = os.path.join(CONTROL_DIR, "s", "selection_freeze.json")
CENSUS_PATH = os.path.join(CONTROL_DIR, "p2_grid_census.json")
CONTRACT_PATH = os.path.join(CONTROL_DIR, "p1_cost_contract.json")
MANIFEST_PATH = os.path.join(CONTROL_DIR, "substrate_manifest.json")
Z_REPORT_PATH = os.path.join(CONTROL_DIR, "z", "z_report.json")
ADJUDICATION_PATH = os.path.join(CONTROL_DIR, "audits",
                                 "lead_adjudication_a7.json")
A7_AUDIT_PATH = os.path.join(CONTROL_DIR, "audits",
                             "a7_prelaunch_rates_ng1.json")

#: The dispatch packet's frozen cell digests (integrity law: the cells
#: computed here must be EXACTLY these 3, in this order).
CELL_ORDER = (
    "RATESNG1-A5-P1-ARM-NEUTRAL",
    "RATESNG1-A5-P1-ARM-CONSERVATIVE",
    "RATESNG1-A5-P1-ARM-AGGRESSIVE",
)
PACKET_DIGEST_PREFIXES = {
    "RATESNG1-A5-P1-ARM-NEUTRAL": "33b78baa",
    "RATESNG1-A5-P1-ARM-CONSERVATIVE": "54ef5def",
    "RATESNG1-A5-P1-ARM-AGGRESSIVE": "cfdad940",
}

CONTROL_ARM_SUFFIXES = {
    "LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL": "LEVEL-CTL",
    "CLOCK_ONLY_SHADOW": "CLOCK-CTL",
    "PLACEBO": "PLACEBO-CTL",
}

BUDGET_PLANNED = 6
BUDGET_BOOKED = 3
BUDGET_UNBOOKED = 3

GO_AUTHORITY = {
    "go_phrase": "GO RATES NG1 SCORED EXECUTION",
    "go_typed_by": "A1 Lead under owner standing delegation (P-8 at "
                   "this cycle's own gate)",
    "audit_artifact":
        "research/control/rates_ng1_run/audits/a7_prelaunch_rates_ng1.json",
    "audit_verdict_key": "RATES_NG1_S0_LAUNCH_AUTHORIZED",
    "adjudication_artifact":
        "research/control/rates_ng1_run/audits/"
        "lead_adjudication_a7.json",
    "base_sha": DISPATCH_SHA,
}

A7_R1_CITATION = (
    "research/control/rates_ng1_run/audits/lead_adjudication_a7.json#"
    "adjudications.A7-R1 (BOUND pre-scored): any control row with "
    "n_pairs == 0 is NOT_EXECUTABLE and contributes NEITHER a kill NOR "
    "a pass; R2 for the affected arm is decided by the remaining "
    "executable limbs only; this NOT_EXECUTABLE disclosure travels "
    "into every E artifact row")

ADJUDICATION_RESIDUAL_NOTE = (
    "adjudication A7-R1 residual_note: CONSERVATIVE fired all 3 events "
    "in fold 2 alone, so R3 (2-of-3 folds) bars it from survivor "
    "status independently of this binding")

P11_LAW = (
    "P-11 LAUNCH REQUIREMENT: per-period series persisted -- the "
    "per-decision after-cost edge series (tier-2.0 PRIMARY, entry-"
    "instant attribution) and the per-instant gross series are persisted "
    "in full in each cell artifact for the future DSR pass")


class RunLawError(Exception):
    """Fail-closed scored-run construction/execution error."""


# ------------------------------------------------------------------- #
# small helpers                                                        #
# ------------------------------------------------------------------- #

def utcnow() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _git(*args: str) -> str:
    out = subprocess.run(["git", "-C", REPO, *args],
                         capture_output=True, text=True, check=True)
    return out.stdout.strip()


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_json(path: str, payload: dict) -> str:
    data = (json.dumps(payload, indent=1, sort_keys=True,
                       ensure_ascii=True) + "\n").encode("utf-8")
    tmp = path + ".tmp"
    with open(tmp, "wb") as fh:
        fh.write(data)
    os.replace(tmp, path)
    return hashlib.sha256(data).hexdigest()


# ------------------------------------------------------------------- #
# A7-R1 binding (adjudication, pre-scored).                            #
# ------------------------------------------------------------------- #

def apply_a7_r1_binding(verdict_full: dict) -> dict:
    """Apply the A7-R1 adjudication binding to the FROZEN battery
    comparator verdict, WITHOUT modifying any frozen module.

    Rows with n_pairs_used == 0 are NOT_EXECUTABLE: they contribute
    NEITHER a kill NOR a pass and are EXCLUDED from the R2 evaluator
    input.  R2 is decided by the remaining executable limbs only.  If
    NO limb is executable, the evaluator input is None (the frozen
    evaluator records R2 NOT_RUN with pass False -- fail-closed, never
    an inferred PASS).
    """
    rows = list(verdict_full["comparisons"])
    executable = [r for r in rows if int(r["n_pairs_used"]) >= 1]
    not_executable = [r for r in rows if int(r["n_pairs_used"]) < 1]
    killed_by = [r["control_role"] for r in executable if r["kill"]]
    family_kill_exec = bool(killed_by)

    if executable:
        evaluator_input = {
            "schema": verdict_full["schema"],
            "falsification_rule_citation":
                verdict_full["falsification_rule_citation"],
            "k_misalign_sessions": verdict_full["k_misalign_sessions"],
            "comparisons": executable,
            "killed_by": killed_by,
            "family_kill": family_kill_exec,
            "q11_note": verdict_full["q11_note"],
            "a7_r1_binding_applied": True,
        }
    else:
        evaluator_input = None

    return {
        "citation": A7_R1_CITATION,
        "applied": True,
        "executable_roles": [r["control_role"] for r in executable],
        "not_executable_roles": [
            {"control_role": r["control_role"],
             "n_pairs_used": int(r["n_pairs_used"]),
             "status": "NOT_EXECUTABLE",
             "contributes": "NEITHER a kill NOR a pass",
             "disclosure": A7_R1_CITATION}
            for r in not_executable],
        "family_kill_frozen_comparator_value":
            bool(verdict_full["family_kill"]),
        "family_kill_executable_limbs_only": family_kill_exec,
        "equality_note":
            "the frozen comparator mechanically yields kill=False for a "
            "0-pair row (mean undefined), so family_kill over all rows "
            "equals family_kill over executable limbs only; the "
            "binding's substantive effect is the recorded "
            "NOT_EXECUTABLE exclusion of the row from BOTH the kill "
            "AND the pass side (no pass limb is credited to a row that "
            "cannot run)",
        "evaluator_input": evaluator_input,
    }


# ------------------------------------------------------------------- #
# verdict classification + margins (lane layer over the frozen         #
# evaluator; never alters a rule outcome)                              #
# ------------------------------------------------------------------- #

def classify_cell_verdict(evaluation: dict) -> dict:
    rules = evaluation["rules"]
    failed: list[str] = []
    not_run: list[str] = []
    for r in ("R1", "R2", "R3", "R4", "R5", "R6"):
        rule = rules[r]
        if rule["pass"]:
            continue
        if r == "R2" and str(rule.get("status", "")).startswith("NOT_RUN"):
            not_run.append(r)
        elif r == "R4" and rule.get("profit_factor") is None:
            not_run.append(r)
        else:
            failed.append(r)
    if not failed and not not_run:
        verdict = "SURVIVOR"
        basis = "passes ALL six frozen rules R1-R6"
    elif failed:
        verdict = "KILL(" + ",".join(failed) + ")"
        basis = "fails the frozen rule order on measured evidence: " + \
            ",".join(failed)
        if not_run:
            basis += "; additionally NOT_RUN (disclosed, never inferred): " \
                + ",".join(not_run)
    else:
        verdict = "NOT_SURVIVOR_NOT_RUN(" + ",".join(not_run) + ")"
        basis = "no measured rule failure, but NOT_RUN evidence blocks " \
                "survivor (fail-closed: missing evidence is NOT_RUN, " \
                "never inferred PASS): " + ",".join(not_run)
    return {"verdict": verdict, "basis": basis,
            "failed_rules": failed, "not_run_rules": not_run,
            "evaluator_survivor": evaluation["survivor"],
            "evaluator_failed_rules": evaluation["failed_rules"]}


def rule_citations(evaluation: dict, binding: dict) -> dict:
    """Per-rule cited bound + measured value + margin (P-2), read from
    the FROZEN evaluator's own rule dicts (verbatim) + lane margins."""
    rules = evaluation["rules"]
    out: dict[str, dict] = {}
    r1 = rules["R1"]
    out["R1"] = {
        "rule_text": FROZEN_RULE_ORDER[0],
        "bound": R1_EXPECTANCY_GT,
        "measured_mean_edge_net_tier2": r1["mean_edge"],
        "n_defined": r1["n_defined"],
        "margin": r1["margin"],
        "pass": r1["pass"],
    }
    r2 = rules["R2"]
    out["R2"] = {
        "rule_text": FROZEN_RULE_ORDER[1],
        "pass": r2["pass"],
        "family_kill": r2.get("family_kill"),
        "killed_by": r2.get("killed_by"),
        "decided_by_executable_limbs_only":
            binding["applied"],
        "executable_roles": binding["executable_roles"],
        "not_executable_rows": binding["not_executable_roles"],
        "citation": A7_R1_CITATION if binding["not_executable_roles"]
        else A7_R1_CITATION + " (no row triggered: every comparator "
             "executable on >=1 aligned pair)",
        "status": r2.get("status"),
    }
    r3 = rules["R3"]
    out["R3"] = {
        "rule_text": FROZEN_RULE_ORDER[2],
        "bound": f">= {R3_MIN_POSITIVE_FOLDS} of {len(FOLD_WINDOWS)} "
                 "folds with positive after-cost expectancy",
        "measured_positive_folds": r3["positive_folds"],
        "folds_present": r3["folds_present"],
        "per_fold_means_net_tier2": r3["per_fold_means"],
        "fold_windows": r3["fold_windows"],
        "margin": (r3["positive_folds"] - R3_MIN_POSITIVE_FOLDS
                   if r3["positive_folds"] is not None else None),
        "pass": r3["pass"],
    }
    r4 = rules["R4"]
    out["R4"] = {
        "rule_text": FROZEN_RULE_ORDER[3],
        "bound": R4_PF_MIN,
        "measured_profit_factor": r4["profit_factor"],
        "gross_win": r4["gross_win"],
        "gross_loss": r4["gross_loss"],
        "margin_recorded": r4["margin_recorded"],
        "undefined_note": r4["undefined_note"],
        "pass": r4["pass"],
    }
    r5 = rules["R5"]
    out["R5"] = {
        "rule_text": FROZEN_RULE_ORDER[4],
        "measured_mean_edge_net_tier2": r5["mean_edge"],
        "coincidence_note": r5["coincidence_note"],
        "pass": r5["pass"],
    }
    r6 = rules["R6"]
    conc = r6["concentration"]
    max_share = conc.get("max_single_instant_share")
    out["R6"] = {
        "rule_text": FROZEN_RULE_ORDER[5],
        "drop_one_fold": r6["drop_one_fold"],
        "drop_one_all_positive": r6["drop_one_all_positive"],
        "concentration": conc,
        "bound_max_single_instant_gross_share":
            R6_MAX_SINGLE_INSTANT_GROSS_SHARE,
        "margin_to_bound": (R6_MAX_SINGLE_INSTANT_GROSS_SHARE - max_share
                            if max_share is not None else None),
        "pass": r6["pass"],
    }
    return out


# ------------------------------------------------------------------- #
# one scored cell (frozen machinery end-to-end, figures retained)      #
# ------------------------------------------------------------------- #

def _booked_control_run(ctl_id: str, states: list, instants: list,
                        leg_closes: dict, tiers: dict, er_daily: dict
                        ) -> dict:
    decisions, round_trips, meta = positions_from_states(
        states, instants, arm_id=ctl_id)
    books = book_round_trips(ctl_id, round_trips, leg_closes, tiers,
                             er_daily)
    edges = z_run.round_trip_edges(instants, round_trips, books, er_daily)
    reconciled = z_run.signed_surface_reconciled(round_trips, books,
                                                 er_daily)
    if not reconciled:
        raise RunLawError(
            f"{ctl_id}: control signed-surface reconciliation failed "
            "(TECHABORT: kernel tie-back refused)")
    struct = books.structural_view()
    return {
        "ctl_id": ctl_id,
        "decisions": decisions,
        "round_trips": round_trips,
        "meta": meta,
        "books": books,
        "edges": edges,
        "fills_total": sum(v["fills"] for v in struct.values()),
        "dual_book_ok": all(v["dual_book_equality_ok"]
                            for v in struct.values()),
    }


def per_instant_gross(instants: list, round_trips: list) -> list:
    """R6 concentration input: per-instant GROSS (before-cost signed
    BOTH-leg figure, mirror arithmetic pre-cost with the runner sign
    applied) attributed to the entry instant; 0.0 elsewhere (a true
    zero: a decision instant with no entry contributes no gross)."""
    pos_of_idx = {int(inst["session_index"]): k
                  for k, inst in enumerate(instants)}
    gross = [0.0] * len(instants)
    for rt in round_trips:
        total = 0.0
        for leg, info in rt["legs"].items():
            total += round_trip_leg_signed_pnl(
                info["orientation"], z_run._cached_signed(info))
        gross[pos_of_idx[int(rt["entry_session_index"])]] = total
    return gross


def round_trip_records(round_trips: list, er_daily: dict) -> list:
    """Full per-round-trip records (recomputable PnL arithmetic)."""
    out = []
    for rt in round_trips:
        net_total = 0.0
        gross_total = 0.0
        legs_out = {}
        for leg, info in sorted(rt["legs"].items()):
            mirror = z_run._leg_mirror_long_pnl(info, er_daily, leg)
            signed = round_trip_leg_signed_pnl(info["orientation"], mirror)
            net_total += signed
            gross_total += round_trip_leg_signed_pnl(
                info["orientation"], z_run._cached_signed(info))
            legs_out[leg] = {
                "orientation": info["orientation"],
                "qty": info["qty"],
                "entry_price": info["entry_price"],
                "exit_price": info["exit_price"],
                "side_entry_kernel": info["side_entry_kernel"],
                "side_exit_kernel": info["side_exit_kernel"],
                "spread_cost_entry": info["spread_cost_entry"],
                "spread_cost_exit": info["spread_cost_exit"],
                "drag_days": info["drag_days"],
                "drag_notional": info["drag_notional"],
                "tenor_bracket": info["tenor_bracket"],
                "gross_leg_usd": round_trip_leg_signed_pnl(
                    info["orientation"], z_run._cached_signed(info)),
                "net_tier2_leg_usd": signed,
            }
        out.append({
            "rt_id": rt["rt_id"],
            "direction": rt["direction"],
            "fold": rt["fold"],
            "entry_session": rt["entry_session"],
            "entry_session_index": rt["entry_session_index"],
            "exit_session": rt["exit_session"],
            "exit_session_index": rt["exit_session_index"],
            "exit_reason": rt["exit_reason"],
            "legs": legs_out,
            "gross_both_legs_usd": gross_total,
            "net_tier2_both_legs_usd": net_total,
        })
    return out


def fold_blocks(edges: list, fold_ids: list) -> dict:
    out = {}
    for f in (1, 2, 3):
        vals = [e for e, ff in zip(edges, fold_ids)
                if e is not None and ff == f]
        total = sum(vals) if vals else None
        out[str(f)] = {
            "window": list(FOLD_WINDOWS[f - 1]),
            "n_defined_edges": len(vals),
            "total_net_tier2_usd": total,
            "expectancy_net_tier2_usd":
                (total / len(vals)) if vals else None,
            "positive": bool(vals and total > 0.0),
        }
    return out


def run_cell_scored(cell: dict, rep: dict, cost: dict, zr_cell: dict
                    ) -> dict:
    """ONE frozen cell, scored, end-to-end.  Deterministic function of
    (substrate bytes, committed artifacts, frozen runner code)."""
    instants = rep["instants"]
    tiers = {leg: cost["per_etp"][leg]["stress_tier_bps"]
             for leg in ("SHY", "TLT")}
    er_daily = {leg: cost["per_etp"][leg]["expense_drag"][
        "drag_per_day_fraction"] for leg in ("SHY", "TLT")}

    arm = run_arm(arm_id=cell["arm_id"],
                  arm_role=cell["role"],
                  config=cell["config"],
                  curve_by_date=rep["curve_by_date"],
                  instants=instants,
                  leg_closes_by_date=rep["leg_closes"],
                  tiers_bps=tiers,
                  er_daily=er_daily)
    round_trips = arm["round_trips"]
    books = arm["books"]
    edges = z_run.round_trip_edges(instants, round_trips, books, er_daily)
    reconciled = z_run.signed_surface_reconciled(round_trips, books,
                                                 er_daily)
    if not reconciled:
        raise RunLawError(
            f"{cell['arm_id']}: signed-surface reconciliation failed "
            "(TECHABORT: kernel tie-back refused)")
    struct = books.structural_view()
    if not all(v["dual_book_equality_ok"] for v in struct.values()):
        raise RunLawError(
            f"{cell['arm_id']}: dual-book equality refused")

    # -- battery controls (identical machinery, identical cost law) --- #
    level_series = curve_coordinates(rep["curve_by_date"],
                                     instants)["level"]
    control_states = {
        "LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL":
            level_control_state(level_series),
        "CLOCK_ONLY_SHADOW": clock_only_state(instants),
        "PLACEBO": misaligned_state(arm["state_series"]),
    }
    control_runs: dict[str, dict] = {}
    for role in KILLER_ROLES:
        control_runs[role] = _booked_control_run(
            f"{cell['arm_id']}|{CONTROL_ARM_SUFFIXES[role]}",
            control_states[role], instants, rep["leg_closes"], tiers,
            er_daily)

    # -- frozen battery comparator (full, real figures) ---------------- #
    verdict_full = battery_verdict(
        edges, {role: control_runs[role]["edges"]
                for role in KILLER_ROLES})

    # -- DETERMINISM GATE vs the committed Z report pins --------------- #
    det = determinism_check(cell, zr_cell, arm, edges, verdict_full,
                            control_runs, struct)

    # -- A7-R1 binding + frozen R1-R6 evaluation ------------------------ #
    binding = apply_a7_r1_binding(verdict_full)
    fold_ids = [fold_of_session(str(inst["decision_session"]))
                for inst in instants]
    gross = per_instant_gross(instants, round_trips)
    evaluation = evaluate_r1_r6(
        edges, fold_ids, binding["evaluator_input"],
        single_instant_gross=gross)
    classification = classify_cell_verdict(evaluation)
    citations = rule_citations(evaluation, binding)

    # -- per-period series (P-11 persistence) --------------------------- #
    defined_edges = [e for e in edges if e is not None]
    per_decision = {
        "convention": "per-decision after-cost edge (tier-2.0 PRIMARY, "
                      "BOTH legs) attributed to the round trip's ENTRY "
                      "decision instant; aligned to the 1918 bookable "
                      "instants; None = no edge defined at the instant "
                      "(no entry or UNDEFINED upstream state -- Q-11: "
                      "never inferred as zero); persisted for the "
                      "future DSR P-11 pass",
        "decision_sessions": [str(inst["decision_session"])
                              for inst in instants],
        "fold_ids": fold_ids,
        "edges_net_tier2_aligned": edges,
        "gross_instant_aligned": gross,
        "n_defined_edges": len(defined_edges),
    }

    ledgers_out = {}
    for name, led in sorted(books.ledgers.items()):
        eq = led.dual_book_equality()
        ledgers_out[name] = {
            "fills": len(led.fills),
            "marks": len(led.marks),
            "cost_events": len(led.cost_events),
            "dual_book_equality": eq,
            "ledger_sha256": led.sha256(),
        }

    cell_artifact = {
        "schema": CELL_SCHEMA,
        "cycle_id": CYCLE_ID,
        "task_id": TASK_ID,
        "lane": LANE,
        "family_id": cell["family_id"],
        "arm_id": cell["arm_id"],
        "role": cell["role"],
        "cell_id": cell["cell_id"],
        "identity": {
            "arm_config_digest": cell["arm_config_digest"],
            "packet_digest_prefix": PACKET_DIGEST_PREFIXES[cell["arm_id"]],
            "packet_digest_prefix_match":
                cell["arm_config_digest"][:8]
                == PACKET_DIGEST_PREFIXES[cell["arm_id"]],
            "code_authority": "research/assets/rates_ng1/ FROZEN "
                              "(READ-ONLY; I-phase machinery, unmodified)",
            "cost_treatment": {
                "contract": "research/control/rates_ng1_run/"
                            "p1_cost_contract.json",
                "cost_ladder_tier": 2.0,
                "tier_2_0_primary": True,
                "cost_frequency": "once_per_fill",
                "both_legs_charged": True,
                "per_leg_stress_tier_bps": tiers,
                "per_leg_drag_per_day_fraction": er_daily,
                "drag_convention": "ACT/365F expense drag over the "
                                   "frozen 7-calendar-day holding "
                                   "convention, charged per leg per "
                                   "round trip",
            },
            "representation": {
                "bookable_instants": len(instants),
                "grid_dates": len(rep["grid_dates"]),
                "curve_dates_loaded": len(rep["curve_by_date"]),
                "leg_close_rows": {leg: len(rep["leg_closes"][leg])
                                   for leg in sorted(rep["leg_closes"])},
                "fold_windows": [list(w) for w in FOLD_WINDOWS],
                "tenor_bracket": {"2 Yr": "SHY", "30 Yr": "TLT"},
                "sign_convention": "state +1 => LONG SHY / SHORT TLT; "
                                   "-1 => reverse; 0 => flat; SHORT legs "
                                   "mirror-booked (true prices and "
                                   "quantities) with the disclosed "
                                   "runner-level sign",
            },
        },
        "state_counts": {
            "decisions_total": arm["meta"]["decisions_total"],
            "states_defined": arm["meta"]["states_defined"],
            "states_undefined": arm["meta"]["states_undefined"],
            "state_events_nonzero": arm["meta"]["state_events_nonzero"],
            "round_trips": arm["meta"]["round_trips"],
            "folds_decisions": arm["meta"]["folds_decisions"],
            "folds_state_events": arm["meta"]["folds_state_events"],
            "exit_reasons": arm["meta"]["exit_reasons"],
            "fold_force_flat_same_day":
                arm["meta"]["fold_force_flat_same_day"],
        },
        "books": {
            "ledgers": ledgers_out,
            "fills_total": sum(v["fills"] for v in struct.values()),
            "marks_total": sum(v["marks"] for v in struct.values()),
            "cost_events_total": sum(v["cost_events"]
                                     for v in struct.values()),
            "signed_surface_reconciliation_ok": reconciled,
        },
        "per_round_trips": round_trip_records(round_trips, er_daily),
        "per_decision_series": per_decision,
        "folds": fold_blocks(edges, fold_ids),
        "battery": {
            "anchor_arm": cell["arm_id"],
            "roles": list(KILLER_ROLES),
            "declared_executioner":
                "LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL",
            "k_misalign_sessions": int(verdict_full["k_misalign_sessions"]),
            "falsification_rule_citation":
                verdict_full["falsification_rule_citation"],
            "comparator_full": verdict_full,
            "a7_r1_binding": {k: v for k, v in binding.items()
                              if k != "evaluator_input"},
            "controls": {
                role: {
                    "ctl_id": control_runs[role]["ctl_id"],
                    "state_counts": {
                        "decisions_total":
                            control_runs[role]["meta"]["decisions_total"],
                        "states_defined":
                            control_runs[role]["meta"]["states_defined"],
                        "states_undefined":
                            control_runs[role]["meta"]["states_undefined"],
                        "state_events_nonzero":
                            control_runs[role]["meta"][
                                "state_events_nonzero"],
                        "round_trips":
                            control_runs[role]["meta"]["round_trips"],
                    },
                    "fills_total": control_runs[role]["fills_total"],
                    "dual_book_ok": control_runs[role]["dual_book_ok"],
                    "control_edges_net_tier2_aligned":
                        control_runs[role]["edges"],
                }
                for role in KILLER_ROLES},
        },
        "gates": {
            "frozen_rule_order": list(FROZEN_RULE_ORDER),
            "rule_citations": citations,
            "evaluator_rules": evaluation["rules"],
            "evaluator_survivor": evaluation["survivor"],
            "p15_note": evaluation["p15_note"],
            "pbo": pbo_record(BUDGET_BOOKED),
        },
        "cell_verdict": classification["verdict"],
        "cell_verdict_detail": classification,
        "conventions": {
            "expectancy": "mean defined per-decision net tier-2.0 edge "
                          "(R1); UNDEFINED instants dropped from the "
                          "denominator, never inferred as zero",
            "profit_factor": "gross win / gross loss of the "
                             "per-decision net tier-2.0 edge series; no "
                             "losing edge => None => R4 NOT_RUN (Q-11: "
                             "never inferred infinite)",
            "r6_gross_concentration": "per-instant before-cost signed "
                                      "BOTH-leg gross at the entry "
                                      "instant; share = instant gross / "
                                      "total gross; total <= 0 => "
                                      "shares undefined (fail-closed)",
            "edge_attribution": "the round trip's BOTH-leg after-cost "
                                "figure is attributed to its ENTRY "
                                "decision instant",
        },
        "determinism_vs_z_report": det,
    }
    return cell_artifact


def determinism_check(cell: dict, zr_cell: dict, arm: dict, edges: list,
                      verdict_full: dict, control_runs: dict,
                      struct: dict) -> dict:
    """Every outcome digest produced here must equal the sha256 pin the
    Z report committed for this cell (one-way determinism pins).  Any
    mismatch is a genuine technical failure => TECHABORT."""
    checks: list[dict] = []

    def chk(label: str, mine, pinned) -> None:
        checks.append({"check": label, "match": bool(mine == pinned),
                       "lane_value": mine, "z_report_pin": pinned})

    internals = z_run._outcome_internals(arm["round_trips"], edges)
    chk("per_decision_edges_sha256",
        internals["per_decision_edges_sha256"],
        zr_cell["outcome_internals"]["per_decision_edges_sha256"])
    chk("round_trip_outcome_sha256",
        internals["round_trip_outcome_sha256"],
        zr_cell["outcome_internals"]["round_trip_outcome_sha256"])
    chk("battery_verdict_internals_sha256", z_run._digest_of(verdict_full),
        zr_cell["battery"]["verdict_internals_sha256"])
    for role in KILLER_ROLES:
        chk(f"control_edges_sha256:{role}",
            z_run._digest_of(control_runs[role]["edges"]),
            zr_cell["battery"]["controls"][role]["control_edges_sha256"])
        chk(f"control_n_pairs_used:{role}",
            next(r["n_pairs_used"] for r in verdict_full["comparisons"]
                 if r["control_role"] == role),
            zr_cell["battery"]["controls"][role]["n_pairs_used"])
        chk(f"control_fills_total:{role}",
            control_runs[role]["fills_total"],
            zr_cell["battery"]["controls"][role]["control_fills_total"])
    for name, sha in zr_cell["fills"]["kernel_ledger_sha256"].items():
        chk(f"kernel_ledger_sha256:{name}",
            arm["books"].ledgers[name].sha256(), sha)
    chk("round_trips", arm["meta"]["round_trips"],
        zr_cell["state_counts"]["round_trips"])
    chk("fills_total", sum(v["fills"] for v in struct.values()),
        zr_cell["fills"]["fills_total"])
    chk("marks_total", sum(v["marks"] for v in struct.values()),
        zr_cell["fills"]["marks_total"])
    chk("cost_events_total", sum(v["cost_events"] for v in struct.values()),
        zr_cell["fills"]["cost_events_total"])
    chk("folds_state_events", arm["meta"]["folds_state_events"],
        zr_cell["fold_partition"]["folds_state_events"])
    chk("exit_reasons", arm["meta"]["exit_reasons"],
        zr_cell["fold_partition"]["exit_reasons"])

    mismatches = [c for c in checks if not c["match"]]
    if mismatches:
        raise RunLawError(
            f"{cell['arm_id']}: determinism gate FAILED vs the "
            f"committed z_report pins: "
            f"{[c['check'] for c in mismatches]} (TECHABORT: the scored "
            "run would not be executing the exact rehearsed pipeline; "
            "no numbers published)")
    return {
        "law": "every lane-computed outcome digest must equal the "
               "one-way sha256 pin committed in the Z report; a "
               "mismatch is TECHABORT before any number is published",
        "z_report_path": "research/control/rates_ng1_run/z/z_report.json",
        "checks": checks,
        "all_match": True,
    }


# ------------------------------------------------------------------- #
# main                                                                 #
# ------------------------------------------------------------------- #

def main() -> int:
    started_utc = utcnow()
    t0 = time.time()
    incidents: list[dict] = [
        {
            "id": "E-DRIVER-SELF-PIN-ATTEMPT1",
            "when_utc": "2026-09-14T03:26:22Z",
            "detail": "attempt-1 TECHABORT (lock released TECHABORT, "
                      "history row present): lane driver bug -- the "
                      "integrity loop looked the S freeze up in its own "
                      "citation_pins, but the freeze pins only UPSTREAM "
                      "artifacts (full-path keyed); no PnL was computed "
                      "and no cell artifact written.",
            "outcome_influence": "none: failure is in artifact-pin "
                                 "bookkeeping before any measurement; "
                                 "no rescue, no threshold change, no "
                                 "frozen-code edit",
            "remediation": "freeze digest now cross-pinned against the "
                           "committed I gate and the committed A7 audit "
                           "(both must equal the measured bytes); "
                           "attempt-2 full deterministic recompute with "
                           "attempt-1 disclosed here",
        },
    ]
    cells_written: list[dict] = []
    gate_path = os.path.join(E_DIR, "e_gate.json")
    family_path = os.path.join(E_DIR, "family_verdicts.json")
    lock = None
    status = "TECHABORT"
    note = ""
    head_sha = _git("rev-parse", "HEAD")
    branch = _git("branch", "--show-current")

    def write_abort_gate() -> None:
        try:
            _write_json(gate_path, {
                "schema": GATE_SCHEMA,
                "cycle_id": CYCLE_ID, "task_id": TASK_ID, "lane": LANE,
                "verdict": status,
                "started_utc": started_utc, "ended_utc": utcnow(),
                "dispatch_sha": DISPATCH_SHA,
                "actual_start_sha": head_sha,
                "base_match": head_sha == DISPATCH_SHA,
                "branch": branch,
                "cells": cells_written,
                "incidents": incidents,
                "error": note,
                "exposure": "partial gate written by the abort handler; "
                            "cells written before the failure stand as "
                            "computed, no rescue, no re-run",
            })
        except Exception:
            pass

    if head_sha != DISPATCH_SHA:
        raise SystemExit(f"BASE MISMATCH: HEAD {head_sha} != dispatch "
                         f"{DISPATCH_SHA} (STOP: FROZEN_SHA_MISMATCH)")
    if branch != BRANCH:
        raise SystemExit(f"BRANCH MISMATCH: {branch} != {BRANCH} (STOP)")

    try:
        # -- heavy lock (machine-wide; FREE_PROVEN pre-inspect) -------- #
        pre_inspect = heavy_lock.inspect()
        if pre_inspect["verdict"] != heavy_lock.VERDICT_FREE_PROVEN:
            raise RunLawError(
                "pre-run lock inspect is "
                f"{pre_inspect['verdict']}: {pre_inspect['reason']} "
                "(NOT_RUN_RESOURCE_CONFLICT discipline: never contend)")
        lock = heavy_lock.acquire(
            cycle_id=CYCLE_ID, role="E_SCORED", worktree=REPO,
            command=sys.argv,
            expected_artifacts=[
                os.path.join(E_DIR, f"cell_{arm}.json")
                for arm in CELL_ORDER]
            + [family_path, gate_path])
        lock_started = lock.owner["started_at"]

        # -- integrity gates (before ANY PnL) --------------------------- #
        freeze = json.load(open(FREEZE_PATH, "r", encoding="utf-8"))
        pins = freeze["citation_pins"]
        # the S freeze does not pin ITSELF in citation_pins (full-path
        # keyed pins of UPSTREAM artifacts only); its digest is pinned
        # by the committed I gate and re-derived by the committed A7
        # audit -- both must equal the measured bytes (cross-artifact
        # pin equality, A7 method).
        i_gate = json.load(open(os.path.join(CONTROL_DIR, "i",
                                             "i_gate.json"), "r",
                                encoding="utf-8"))
        a7_audit = json.load(open(A7_AUDIT_PATH, "r", encoding="utf-8"))
        freeze_measured = _sha256_file(FREEZE_PATH)
        freeze_pins = {
            "i_gate.structural_values.committed_artifact_pins."
            "selection_freeze_sha256":
                i_gate["structural_values"]["committed_artifact_pins"][
                    "selection_freeze_sha256"],
            "a7_prelaunch.recomputed."
            "frozen_sha_chain_3way_pin_consistency.selection_freeze":
                a7_audit["recomputed_by_auditor"][
                    "frozen_sha_chain_3way_pin_consistency"][
                    "selection_freeze"]["sha256"],
        }
        pin_report = {"selection_freeze": {
            "measured": freeze_measured,
            "pinned_by": freeze_pins,
            "match": all(v == freeze_measured
                         for v in freeze_pins.values())}}
        if not pin_report["selection_freeze"]["match"]:
            raise RunLawError(
                f"selection_freeze drift: measured {freeze_measured} vs "
                f"committed pins {freeze_pins} (fail-closed, no PnL)")
        for label, path, key in (
                ("p2_grid_census", CENSUS_PATH,
                 "research/control/rates_ng1_run/p2_grid_census.json"),
                ("p1_cost_contract", CONTRACT_PATH,
                 "research/control/rates_ng1_run/"
                 "p1_cost_contract.json"),
                ("substrate_manifest", MANIFEST_PATH,
                 "research/control/rates_ng1_run/"
                 "substrate_manifest.json")):
            measured = _sha256_file(path)
            pin_report[label] = {"measured": measured,
                                 "pinned": pins[key],
                                 "match": measured == pins[key]}
            if measured != pins[key]:
                raise RunLawError(
                    f"{label} drift: measured {measured} != freeze pin "
                    f"{pins[key]} (fail-closed, no PnL)")
        contract = json.load(open(CONTRACT_PATH, "r", encoding="utf-8"))
        body_pin = freeze["section_4_cost_contract_binding"]["contract"][
            "sha256"]
        if pin_report["p1_cost_contract"]["measured"] != body_pin:
            raise RunLawError("cost contract body-pin drift (fail-closed)")
        # freeze-vs-contract cost constants equality (tier-2.0 legs)
        for leg in ("SHY", "TLT"):
            f_bps = freeze["section_4_cost_contract_binding"][
                "per_leg_stress_tier_bps"][leg]
            c_bps = contract["per_etp"][leg]["stress_tier_bps"]
            if float(f_bps) != float(c_bps):
                raise RunLawError(
                    f"stress tier drift for {leg}: freeze {f_bps} != "
                    f"contract {c_bps} (fail-closed, no PnL)")

        cells = assemble_cell_configs(freeze)  # fail-closed digest law
        by_arm = {c["arm_id"]: c for c in cells}
        if sorted(by_arm) != sorted(CELL_ORDER):
            raise RunLawError(
                f"cell identity drift: {sorted(by_arm)} != "
                f"{sorted(CELL_ORDER)} (the scored cells must be "
                "EXACTLY the packet's 3 frozen cells)")
        for arm_id, prefix in PACKET_DIGEST_PREFIXES.items():
            if by_arm[arm_id]["arm_config_digest"][:8] != prefix:
                raise RunLawError(
                    f"packet digest prefix drift for {arm_id} "
                    "(fail-closed, no PnL)")

        z_report = json.load(open(Z_REPORT_PATH, "r", encoding="utf-8"))
        zr_by_arm = {c["arm_id"]: c for c in z_report["cells"]}
        for arm_id in CELL_ORDER:
            if arm_id not in zr_by_arm:
                raise RunLawError(
                    f"z_report carries no committed pin set for "
                    f"{arm_id} (determinism gate impossible: TECHABORT)")

        adjudication = json.load(open(ADJUDICATION_PATH, "r",
                                      encoding="utf-8"))
        if adjudication["go_decision"]["go_phrase"] \
                != GO_AUTHORITY["go_phrase"]:
            raise RunLawError("GO phrase drift vs the committed "
                              "adjudication (STOP)")

        # -- plane verify-on-read + representation ---------------------- #
        plane = pa.RatesNG1Plane()
        census = json.load(open(CENSUS_PATH, "r", encoding="utf-8"))
        years = sorted({int(d[:4])
                        for d in census["census"]["grid_dates"]})
        entries = [f"treasury_curve/par_yields_{y}.csv" for y in years]
        entries += ["etp_eod/SHY.US.json", "etp_eod/TLT.US.json"]
        plane_records = []
        for entry in entries:
            res = plane.consume_via_plane(entry)
            plane_records.append({
                "entry": entry,
                "authority": res["authority"],
                "sha256_pinned": res["sha256_pinned"],
                "sha256_measured": res["sha256_measured"],
                "digest_verified": (res["sha256_pinned"]
                                    == res["sha256_measured"]),
            })
            if not plane_records[-1]["digest_verified"]:
                raise RunLawError(
                    f"plane digest drift for {entry} (BLOCKED_DATA: no "
                    "re-download, no repair; TECHABORT)")
        rep = load_representation(plane, census)

        # -- scored cells, ONE AT A TIME, serialized -------------------- #
        for arm_id in CELL_ORDER:
            cell_t0 = time.time()
            artifact = run_cell_scored(by_arm[arm_id], rep, contract,
                                       zr_by_arm[arm_id])
            artifact["execution"] = {
                "scored": True,
                "real_pnl": True,
                "real_substrate": True,
                "one_at_a_time": True,
                "started_utc": started_utc,
                "cell_finished_utc": utcnow(),
                "cell_runtime_seconds": round(time.time() - cell_t0, 3),
                "run_head_sha": head_sha,
                "run_branch": branch,
                "authority": GO_AUTHORITY,
                "p11_series_persistence": P11_LAW,
                "lock": {"cycle_id": CYCLE_ID, "role": "E_SCORED",
                         "started_at": lock_started},
            }
            path = os.path.join(E_DIR, f"cell_{arm_id}.json")
            sha = _write_json(path, artifact)
            cls = artifact["cell_verdict_detail"]
            cells_written.append({
                "arm_id": arm_id,
                "family_id": by_arm[arm_id]["family_id"],
                "arm_config_digest": by_arm[arm_id]["arm_config_digest"],
                "path": os.path.relpath(path, REPO),
                "sha256": sha,
                "decisions": artifact["state_counts"]["decisions_total"],
                "round_trips": artifact["state_counts"]["round_trips"],
                "n_defined_edges":
                    artifact["per_decision_series"]["n_defined_edges"],
                "cell_verdict": artifact["cell_verdict"],
                "failed_rules": cls["failed_rules"],
                "not_run_rules": cls["not_run_rules"],
                "runtime_seconds":
                    artifact["execution"]["cell_runtime_seconds"],
            })
            lock.heartbeat(extra={"cell_written": arm_id})

        # -- family verdicts -------------------------------------------- #
        survivors = [c for c in cells_written
                     if c["cell_verdict"] == "SURVIVOR"]
        per_cell = []
        for c in cells_written:
            path = os.path.join(REPO, c["path"])
            art = json.load(open(path, "r", encoding="utf-8"))
            per_cell.append({
                "arm_id": c["arm_id"],
                "arm_config_digest": c["arm_config_digest"],
                "cell_verdict": c["cell_verdict"],
                "verdict_basis": art["cell_verdict_detail"]["basis"],
                "survivor": c["cell_verdict"] == "SURVIVOR",
                "failed_rules": c["failed_rules"],
                "not_run_rules": c["not_run_rules"],
                "citations": art["gates"]["rule_citations"],
                "headline": {
                    "expectancy_net_tier2_usd_per_decision":
                        art["gates"]["rule_citations"]["R1"][
                            "measured_mean_edge_net_tier2"],
                    "profit_factor_net_tier2":
                        art["gates"]["rule_citations"]["R4"][
                            "measured_profit_factor"],
                    "fold_expectancies_net_tier2_usd":
                        art["gates"]["rule_citations"]["R3"][
                            "per_fold_means_net_tier2"],
                    "n_defined_edges":
                        art["per_decision_series"]["n_defined_edges"],
                    "max_single_instant_gross_share":
                        art["gates"]["rule_citations"]["R6"][
                            "concentration"].get(
                            "max_single_instant_share"),
                },
            })
        family_out = {
            "schema": FAMILY_SCHEMA,
            "cycle_id": CYCLE_ID,
            "task_id": TASK_ID,
            "lane": LANE,
            "family_id": "RATESNG1-A5-P1",
            "authority": GO_AUTHORITY,
            "survivor_law":
                "survivor := passes ALL six frozen rules R1-R6 "
                "(PROVISIONAL_STAGE_A_SURVIVOR); S1 stays SEALED; no "
                "rescue, no threshold move, no variant addition after "
                "any scored number is visible (P-15); a NOT_RUN rule "
                "blocks survivor (fail-closed: missing evidence is "
                "NOT_RUN, never inferred PASS)",
            "rule_bounds_frozen": {
                "r1_expectancy_gt": R1_EXPECTANCY_GT,
                "r3_min_positive_folds": R3_MIN_POSITIVE_FOLDS,
                "r4_pf_min": R4_PF_MIN,
                "r6_max_single_instant_gross_share":
                    R6_MAX_SINGLE_INSTANT_GROSS_SHARE,
                "provenance": "0 / 2-of-3 / 1.10 / 50% carried over "
                              "unchanged from the FOREX-NG1 precedent "
                              "(s freeze section_3; never moved)",
            },
            "a7_r1_binding": {
                "citation": A7_R1_CITATION,
                "adjudication_residual_note": ADJUDICATION_RESIDUAL_NOTE,
            },
            "pbo": pbo_record(BUDGET_BOOKED),
            "cells": per_cell,
            "family_has_survivor": bool(survivors),
            "survivor_arm_ids": [c["arm_id"] for c in survivors],
            "family_note":
                "all 3 cells are ANCHOR_VARIANT members of the ONE "
                "frozen family; R2 is each cell's own battery (the "
                "family kill semantics live per cell via the frozen "
                "comparator + the A7-R1 binding)",
        }
        _write_json(family_path, family_out)
        lock.heartbeat(extra={"family_verdicts": "written"})

        # -- e_gate ------------------------------------------------------ #
        gate = {
            "schema": GATE_SCHEMA,
            "cycle_id": CYCLE_ID,
            "task_id": TASK_ID,
            "lane": LANE,
            "role": ROLE,
            "started_utc": started_utc,
            "ended_utc": utcnow(),
            "runtime_seconds": round(time.time() - t0, 3),
            "dispatch_sha": DISPATCH_SHA,
            "actual_start_sha": head_sha,
            "base_match": head_sha == DISPATCH_SHA,
            "branch": branch,
            "worktree": WORKTREE,
            "authority": {
                **GO_AUTHORITY,
                "scope_reminder":
                    adjudication["go_decision"]["scope_reminder"],
                "adjudications": sorted(adjudication["adjudications"]),
            },
            "lock": {
                "mechanism": "machine-wide heavy lock "
                             "(research/governance/heavy_lock.py)",
                "pre_run_inspect": pre_inspect["verdict"],
                "cycle_id": CYCLE_ID,
                "role": "E_SCORED",
                "worktree": REPO,
                "started_at": lock_started,
                "cells_one_at_a_time": True,
                "release_status": "FINISHED (recorded at release)",
            },
            "integrity": {
                "artifact_pins": pin_report,
                "arm_config_digests": {
                    c["arm_id"]: c["arm_config_digest"] for c in cells},
                "packet_digest_prefix_match": True,
                "plane_entries_consumed": len(plane_records),
                "plane_all_digest_verified": all(
                    r["digest_verified"] for r in plane_records),
                "freeze_vs_contract_stress_tiers_equal": True,
                "assets_readonly": "research/assets/rates_ng1 untouched "
                                   "by this lane",
                "s1": "SEALED_UNTOUCHED",
            },
            "determinism_vs_z_report": {
                "law": "per-cell outcome digests equal the committed "
                       "z_report one-way pins (edges, round-trip "
                       "structure, control edge series, battery verdict "
                       "internals, kernel ledgers, structural counts); "
                       "mismatch => TECHABORT before publication",
                "per_cell_all_match": {
                    c["arm_id"]: True for c in cells_written},
            },
            "budget": {
                "planned": BUDGET_PLANNED,
                "booked": BUDGET_BOOKED,
                "unbooked": BUDGET_UNBOOKED,
                "unbooked_note": "exactly one family is ELIGIBLE at S; "
                                 "the remaining 3 cells stay UNBOOKED -- "
                                 "never padded with new families, "
                                 "sibling proposals, re-runs or "
                                 "threshold variants (freeze budget_law)",
                "observed": len(cells_written),
                "observed_expected": BUDGET_BOOKED,
                "published": len(cells_written),
                "published_basis": "published = cells included in this "
                                   "lane's single substance commit of "
                                   "research/control/rates_ng1_run/e/ "
                                   "(commit sha recorded in the lane "
                                   "handoff); re-verify with git",
                "unused_slots_never_reassigned": True,
            },
            "cells": cells_written,
            "pbo": pbo_record(BUDGET_BOOKED),
            "a7_r1_binding": {
                "citation": A7_R1_CITATION,
                "adjudication_residual_note": ADJUDICATION_RESIDUAL_NOTE,
                "rows_recorded_not_executable": [
                    {"arm_id": c["arm_id"], "row": row}
                    for c in cells_written
                    for row in json.load(
                        open(os.path.join(REPO, c["path"]),
                             "r", encoding="utf-8"))
                    ["gates"]["rule_citations"]["R2"][
                        "not_executable_rows"]
                ],
            },
            "p11": P11_LAW,
            "pnl_anywhere": True,
            "pnl_note": "scored lane: real after-cost PnL computed on "
                        "the 3 frozen booked cells from the pinned "
                        "bytes through the frozen kernel; the ONLY "
                        "phase where outcome numbers are lawful",
            "incidents": incidents,
        }
        _write_json(gate_path, gate)
        status = "FINISHED"
        note = (f"{len(cells_written)}/{BUDGET_BOOKED} frozen cells "
                "scored under the heavy lock; artifacts under "
                "research/control/rates_ng1_run/e/")
        print(json.dumps({
            "status": status,
            "cells": {c["arm_id"]: c["cell_verdict"]
                      for c in cells_written},
            "survivors": [c["arm_id"] for c in survivors],
        }, indent=1))
        return 0
    except heavy_lock.LockBusyError as exc:
        status = "TECHABORT"
        note = f"NOT_RUN_RESOURCE_CONFLICT: {exc}"
        incidents.append({"id": "E-LOCK-CONFLICT",
                          "detail": str(exc),
                          "verdict": "NOT_RUN_RESOURCE_CONFLICT"})
        write_abort_gate()
        print(note, file=sys.stderr)
        return 3
    except Exception as exc:                       # technical failure
        status = "TECHABORT"
        note = f"{type(exc).__name__}: {exc}"
        incidents.append({
            "id": "E-TECHABORT",
            "error": note,
            "traceback_tail": traceback.format_exc()[-2000:],
            "exposure": "cells written before the failure stand as "
                        "computed (see cells[]); no rescue, no re-run "
                        "for outcomes",
        })
        write_abort_gate()
        print(note, file=sys.stderr)
        return 2
    finally:
        if lock is not None:
            try:
                lock.release(status=status, note=note)
            except Exception:
                pass


if __name__ == "__main__":
    raise SystemExit(main())
