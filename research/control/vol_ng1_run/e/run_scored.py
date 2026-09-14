"""VOL-NG1 E-phase SCORED EXECUTION driver (task vol-ng1-e-scored).

Lane E consumes GO ("GO VOL NG1 SCORED EXECUTION", typed at this
cycle's own gate under owner standing delegation after A7 v2
AUTHORIZED, adjudication lead_adjudication_a7v2.json committed at
0968cec9) and computes the SIX frozen budget cells ONE AT A TIME
(serialized) through the FROZEN code only:

  research/assets/vol_ng1/            (READ-ONLY: kernel + runners +
                                       battery + evaluator)
  research/control/vol_ng1_run/d2/    (READ-ONLY: committed D2 state
                                       builders re-used unchanged)

AUTHORITY CHAIN (carried verbatim into every artifact; binding M-B of
the adjudication: E artifacts cite THIS chain, never the stale
pre-remediation disclosures):

  1. selection_freeze.json              sha256 dd910bcb...abf5cc
     (bytes byte-identical; verified at every load)
  2. selection_freeze_addendum_a7r1.json  committed at 76c25540
     (pre-scored, disclosed; H1 index_point_book + M1
     EXPENSE_IN_NET_STRESS remediation)
  3. a7_prelaunch_v2_vol_ng1.json       VOL_NG1_S0_LAUNCH_AUTHORIZED,
     committed at a921bfa2 (0 HIGH/CRITICAL)
  4. lead_adjudication_a7v2.json        committed at 0968cec9 (BASE):
     M-A bound (A4-P2 R2 limb-(a) NOT_EXECUTABLE at E -- cross-unit
     comparison convention-dependent; contributes NEITHER kill NOR
     pass) + M-B resolved by authority-chain citation; GO typed.

  The pre-remediation gate artifacts (i_gate.json 287eb74a,
  z_report/z_cells 00e5f8c8) are cited ONLY as HISTORICAL EVIDENCE for
  the arm structural count reconciliation (the addendum left every arm
  config, digest, rule and bound byte-identical); they are never
  authority for control-battery semantics.

LAWS ENFORCED HERE (all inherited, none invented):

- machine-wide heavy lock held for the WHOLE scored run (VOL-NG1 /
  E_SCORED); FREE_PROVEN is verified before acquisition; refusal is
  NOT_RUN_RESOURCE_CONFLICT, never a spin; a foreign worker is never
  killed;
- every arm_config_digest must reproduce the freeze's recorded digest
  (recomputed fail-closed inside config.assemble_arm_configs) before
  any PnL;
- PnL identity, cost ladder and tier-2.0 PRIMARY come from the frozen
  P1 kernel (book_round_trip: gross price PnL, cost charged exactly
  once per fill, tier ladder {1.0,1.5,2.0} scaling execution
  frictions only); the Q-16 roll/decay path component and the expense
  drag are EXPLICIT mechanism lines (never folded into fills); lane
  aggregates must reconcile with an independent recomputation of the
  kernel identity AND with acc.dual_book_ledger (shared-module
  identity) or the lane TECHABORTs;
- execution through the P1 event-adjusted layer is MANDATORY
  (corp_actions.event_adjusted_closes; every leg fail-closed on any
  uncovered mechanical step);
- R1-R6 evaluated by the FROZEN evaluator, fail-closed: a rule whose
  metric is missing/uncomputable is NOT_RUN with reason, never an
  inferred PASS; any NOT_RUN blocks the survivor verdict;
- P-11 LAUNCH REQUIREMENT: per-period (per exit grid session) series
  of the PRIMARY NET book persisted in every cell artifact (for the
  future DSR pass);
- PBO is NOT_RUN_FAIL_CLOSED (6 booked cells < 8, V17 contract); the
  frozen alternative robustness rule is R6 NON_CONCENTRATION;
- NO rescue, NO threshold change, NO re-run for bad numbers.
  TECHABORT is for genuine technical failures only, with exposure
  recorded.

R2 REALIZATION UNDER THE BINDINGS (disclosed in every verdict that
uses it; fixed in this driver BEFORE execution, never after numbers):

- A5-P2 cells: the frozen three-limb evaluate_r2 is supplied COMPLETE:
  limb (a) the index-only-shadow state re-clocked onto the ETP
  buckets (the a5_p2_spec control book built at E under scored
  authority, same units as the arm) via the frozen control_reproduces;
  limb (b) the calendar-clock shadow distinctness; limb (c) see below.
- A4-P2 cells: adjudication M-A: limb (a) is NOT_EXECUTABLE (the
  index-point control book is not unit-comparable to the USD net arm
  and the program does not invent a convention post-freeze).  Limb (a)
  contributes NEITHER kill NOR pass; the index-point control book's
  native-unit expectancy is disclosed (labeled, never compared).  R2
  for A4-P2 rests on the measured books_distinct (addendum A1 law)
  plus the remaining veto limbs (b)/(c) and the remaining family kill
  sites (D1 falsification rule at R1/R5, cost-path control, R3 fold
  law).
- limb (c) realization (E-driver convention, frozen pieces only):
  the seeded placebo's induced placement (frozen
  default_rng(20260912) order shuffle of the arm's decision-state
  series) is scored through the ARM'S OWN book construction (identical
  placement surface, kernel books, tier-2.0 PRIMARY) and
  `placebo_differential_significant` := frozen evaluator
  control_reproduces(placebo_expectancy_net_tier2,
  arm_expectancy_net_tier2) -- the V8-law 0.5x same-sign reproduction
  test.  The veto fires ONLY on positive evidence: a
  destroyed-temporal-ordering (chance) state whose book reproduces the
  arm's net result same-sign at >= 0.5x per round trip falsifies the
  arm's persistence claim.  A non-firing draw is the ABSENCE OF
  POSITIVE VETO EVIDENCE, never an inferred PASS of a statistical
  null; the placebo book is committed alongside for audit.

Conventions this lane fixes (disclosed in every artifact that uses
them):

- the per-trade unit is the ROUND TRIP (freeze adaptation note:
  "per-trade -> per-round-trip on the P2 bookable decision grid");
  each round trip is 2 fills, cost charged once per fill;
- expectancy_net_tier2 = mean over the cell's round trips of the
  kernel NET(2.0) book PnL (USD; tier-2.0 PRIMARY);
- profit_factor = sum(positive net tier-2 PnL) / |sum(negative net
  tier-2 PnL)|; zero losing round trips -> None -> R4 NOT_RUN
  (conventionally infinite is an inference, not a measurement);
- R5 stress convention: battery.cost_path_control at tier 2.0
  (EXPENSE_IN_NET_STRESS pin): stress_tier2_expectancy_net =
  (gross - execution(2.0) - Q-16 path - expense) / n_round_trips;
- R6 max_single_round_trip_gross_share: signed share
  rt_gross/total_gross when total gross > 0 (None -> NOT_RUN,
  fail-closed); the |share| variant is disclosed for audit;
- R6 drop-one-fold survival: dropping fold k, the remaining book's net
  tier-2.0 total must be > 0 (0 remaining round trips -> False).

Usage:
    .venv/bin/python research/control/vol_ng1_run/e/run_scored.py
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import subprocess
import sys
import time
import traceback

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.vol_ng1 import accounting as acc             # noqa: E402
from research.assets.vol_ng1 import corp_actions as ca            # noqa: E402
from research.assets.vol_ng1 import feasibility as fb             # noqa: E402
from research.assets.vol_ng1 import plane_adapter as pa           # noqa: E402
from research.assets.vol_ng1.runners import arms as ar            # noqa: E402
from research.assets.vol_ng1.runners import battery as bat        # noqa: E402
from research.assets.vol_ng1.runners import config as cfg         # noqa: E402
from research.assets.vol_ng1.runners import evaluator as ev       # noqa: E402
from research.control.vol_ng1_run import p2_run as p2r            # noqa: E402
from research.governance import heavy_lock                        # noqa: E402

E_DIR = os.path.dirname(os.path.abspath(__file__))
CONTROL_DIR = os.path.dirname(E_DIR)
REPO = REPO_ROOT

DISPATCH_SHA = "0968cec9175ce36c488fde53572b9301ef580cf8"
BRANCH = "orca/vol-ng1-integration"

#: Authority chain (see module docstring; binding M-B).
FREEZE_SHA256 = ("dd910bcb9f5282f7f0e3bf8b8551ece1e46b7b24e9a39506af"
                 "05d77ed6abf5cc")
ADDENDUM_COMMIT = "76c25540"
A7V2_AUDIT_COMMIT = "a921bfa23f4e399bf8f7023892dd02f329f57caa"
ADJUDICATION_COMMIT = "0968cec9175ce36c488fde53572b9301ef580cf8"
GO_PHRASE = "GO VOL NG1 SCORED EXECUTION"
STALE_HISTORY_NOTE = (
    "pre-remediation gate artifacts (i_gate.json at 287eb74a, "
    "z_report/z_cells at 00e5f8c8) are HISTORICAL EVIDENCE ONLY: "
    "cited here solely for the arm structural-count reconciliation "
    "(every arm config, digest, rule and bound was left byte-identical "
    "by the addendum); they are never authority for control-battery "
    "semantics (adjudication M-B)")

Z_DIR = os.path.join(CONTROL_DIR, "z")
Z_CELL_FILES = {
    "VOLNG1-A4-P2-ANCHOR": "z_cell_1_VOLNG1-A4-P2-ANCHOR.json",
    "VOLNG1-A4-P2-NEIGH-PERSIST":
        "z_cell_2_VOLNG1-A4-P2-NEIGH-PERSIST.json",
    "VOLNG1-A4-P2-NEIGH-FAST": "z_cell_3_VOLNG1-A4-P2-NEIGH-FAST.json",
    "VOLNG1-A5-P2-ANCHOR": "z_cell_4_VOLNG1-A5-P2-ANCHOR.json",
    "VOLNG1-A5-P2-NEIGH-STRICT": "z_cell_5_VOLNG1-A5-P2-NEIGH-STRICT.json",
    "VOLNG1-A5-P2-NEIGH-FAST": "z_cell_6_VOLNG1-A5-P2-NEIGH-FAST.json",
}

#: The six frozen scored cells in budget-cell order.
CELLS = (
    ("VOLNG1-A4-P2-ANCHOR", 1),
    ("VOLNG1-A4-P2-NEIGH-PERSIST", 2),
    ("VOLNG1-A4-P2-NEIGH-FAST", 3),
    ("VOLNG1-A5-P2-ANCHOR", 4),
    ("VOLNG1-A5-P2-NEIGH-STRICT", 5),
    ("VOLNG1-A5-P2-NEIGH-FAST", 6),
)
FAMILY_OF = {
    "VOLNG1-A4-P2-ANCHOR": "VOLNG1-A4-P2",
    "VOLNG1-A4-P2-NEIGH-PERSIST": "VOLNG1-A4-P2",
    "VOLNG1-A4-P2-NEIGH-FAST": "VOLNG1-A4-P2",
    "VOLNG1-A5-P2-ANCHOR": "VOLNG1-A5-P2",
    "VOLNG1-A5-P2-NEIGH-STRICT": "VOLNG1-A5-P2",
    "VOLNG1-A5-P2-NEIGH-FAST": "VOLNG1-A5-P2",
}
BUDGET_CELL_OF = {aid: cell for aid, cell in CELLS}

C8_LIMITATION = (
    "STRUCTURAL LIMITATION (declared, C8): the realized proxy is the "
    "realized volatility of the event-adjusted VXX close.  An ETP-leg "
    "realized vol is NOT S&P 500 realized vol -- it is implied-complex "
    "realized vol: a leveraged, fee-bearing VIX-futures-complex "
    "instrument whose realized path embeds roll and decay.  The "
    "implied-vs-realized state computed from it is an "
    "implied-vs-implied-complex proxy, never the classic "
    "implied-vs-spot-realized variance risk premium.")

MA_BINDING_VERBATIM = (
    "BOUND pre-scored, fail-closed: for A4-P2 cells at E, R2 limb-(a) "
    "(control out-earning comparison) is NOT_EXECUTABLE -- the "
    "cross-unit (index points vs USD) ratio is convention-dependent "
    "and the program does not invent a convention post-freeze.  "
    "Limb-(a) contributes NEITHER kill NOR pass; R2 for A4-P2 rests "
    "on the distinctness limb (books_distinct, measured) and the "
    "remaining family kill sites (D1 falsification rule, R1/R5, "
    "cost-path control, R3 fold law).")
MB_BINDING_VERBATIM = (
    "RESOLVED by authority-chain citation: the post-remediation "
    "authority chain for S0 is selection_freeze_addendum_a7r1.json "
    "(76c25540) + this A7 v2 artifact (a921bfa2); the pre-remediation "
    "gate artifacts remain as HISTORICAL EVIDENCE and are never "
    "overwritten (P-13 convention). Every E artifact must cite the "
    "authority chain, not the stale disclosures.")
PLACEBO_LIMB_C_CONVENTION = (
    "limb (c) realization (E-driver convention, frozen pieces only): "
    "the seeded placebo placement (default_rng(20260912) order shuffle "
    "of the arm's decision-state series) is scored through the ARM'S "
    "OWN book construction (identical ETP placement surface, kernel "
    "books, tier-2.0 PRIMARY); placebo_differential_significant := "
    "frozen evaluator control_reproduces(placebo_expectancy_net_tier2,"
    " arm_expectancy_net_tier2), the V8-law 0.5x same-sign "
    "reproduction test.  The veto fires ONLY on positive evidence (a "
    "chance state reproducing the arm's net result same-sign at >= "
    "0.5x per round trip); a non-firing draw is the absence of "
    "positive veto evidence, never an inferred PASS of a statistical "
    "null.  The placebo book is committed alongside for audit.")
SURVIVOR_LAW = ("survivor := passes ALL rules R1-R6 "
                "(selection_freeze; S1 stays SEALED; no rescue after "
                "scored numbers visible)")


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
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)
        fh.write("\n")
    return _sha256_file(path)


def _close(a, b) -> bool:
    return a is not None and b is not None \
        and abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))


def locks_inspect() -> dict:
    """The machine-wide heavy-lock pre-acquisition proof (FREE_PROVEN
    required; never contended)."""
    out = subprocess.run(
        [sys.executable,
         os.path.join("/Users/hoangminhlong/my-quantitative",
                      "research", "researchctl.py"),
         "locks", "inspect"],
        capture_output=True, text=True, check=True)
    return json.loads(out.stdout)


# --------------------------------------------------------------------------- #
# scored books from the frozen kernel events
# --------------------------------------------------------------------------- #
def per_rt_rows(res: ar.CellResult) -> list[dict]:
    """Full after-cost per-round-trip ledger: the frozen kernel book
    per round trip plus the explicit Q-16 path / expense mechanism
    lines (never folded into fills)."""
    rows = []
    for i, rt in enumerate(res.round_trips):
        book = res.kernel_events[i]["book"]
        mech = res.mechanism_lines[i]
        rows.append({
            "round_trip_index": i,
            "leg": rt["leg"],
            "bucket": rt["bucket"],
            "direction": rt["direction"],
            "entry_session": rt["entry_session"],
            "entry_price": rt["entry_price"],
            "exit_session": rt["exit_session"],
            "exit_price": rt["exit_price"],
            "exit_reason": rt["exit_reason"],
            "fold": rt["fold"],
            "held_sessions": rt["held_sessions"],
            "notional_usd": rt["notional_usd"],
            "gross_usd": book["gross_pnl_usd"],
            "net_usd_tier1.0": book["net_pnl_usd_by_tier"]["1.0"],
            "net_usd_tier1.5": book["net_pnl_usd_by_tier"]["1.5"],
            "net_usd_tier2.0": book["net_pnl_usd_by_tier"]["2.0"],
            "q16_path_line_usd": mech["q16_path_line_bps"]
            * rt["notional_usd"] / 1e4,
            "expense_line_usd": mech["expense_line_bps"]
            * rt["notional_usd"] / 1e4,
        })
    return rows


def book_stats(nets: list[float]) -> dict:
    pos = math.fsum(x for x in nets if x > 0)
    neg = math.fsum(x for x in nets if x < 0)
    pf = None if neg == 0.0 else pos / abs(neg)
    return {
        "round_trips": len(nets),
        "total_usd": math.fsum(nets) if nets else None,
        "expectancy_usd": (math.fsum(nets) / len(nets)) if nets else None,
        "gross_profit_usd": pos if nets else None,
        "gross_loss_usd": neg if nets else None,
        "wins": sum(1 for x in nets if x > 0),
        "losses": sum(1 for x in nets if x < 0),
        "profit_factor": pf,
        "profit_factor_note": None if pf is not None else
            "no losing round trips: PF conventionally infinite is an "
            "inference, not a measurement -> NOT_RUN at R4",
    }


def fold_expectancies(rows: list[dict]) -> dict:
    out = {}
    for f in ("1", "2", "3"):
        nets = [r["net_usd_tier2.0"] for r in rows if str(r["fold"]) == f]
        out[f] = (math.fsum(nets) / len(nets)) if nets else None
    return out


def drop_one_fold(rows: list[dict]) -> dict:
    out = {}
    for f in ("1", "2", "3"):
        remaining = [r["net_usd_tier2.0"] for r in rows
                     if str(r["fold"]) != f]
        total = math.fsum(remaining) if remaining else None
        out[f] = {
            "remaining_round_trips": len(remaining),
            "remaining_total_net_tier2_usd": total,
            "positive": bool(remaining) and total > 0,
        }
    return out


def round_trip_concentration(rows: list[dict]) -> dict:
    total = math.fsum(r["gross_usd"] for r in rows)
    if total > 0:
        shares = {r["round_trip_index"]: r["gross_usd"] / total
                  for r in rows}
        top = max(shares, key=lambda k: shares[k])
        abs_top = max(shares, key=lambda k: abs(shares[k]))
        max_share = shares[top]
        max_abs = abs(shares[abs_top])
    else:
        top = abs_top = None
        max_share = max_abs = None
    return {
        "convention": "share = round-trip gross / total gross (signed); "
                      "the |share| variant is disclosed for audit; "
                      "total gross <= 0 -> None -> R6 NOT_RUN "
                      "(fail-closed)",
        "round_trips": len(rows),
        "total_gross_usd": total,
        "max_single_round_trip_gross_share": max_share,
        "max_single_round_trip_index": top,
        "max_single_round_trip_abs_gross_share": max_abs,
        "max_single_round_trip_abs_index": abs_top,
        "none_reason": None if total > 0 else
            "total gross <= 0: concentration share undefined -> R6 "
            "NOT_RUN (fail-closed)",
    }


def per_period_series(rows: list[dict], bookable: list[str]) -> dict:
    """P-11 per-period series: per-exit-session PRIMARY NET book rows
    over the frozen bookable grid (for the future DSR pass)."""
    by_day: dict[str, dict[str, float]] = {}
    for r in rows:
        agg = by_day.setdefault(r["exit_session"],
                                {"gross": 0.0, "net": 0.0})
        agg["gross"] += r["gross_usd"]
        agg["net"] += r["net_usd_tier2.0"]
    series, cg, cn = [], 0.0, 0.0
    for d in bookable:
        agg = by_day.get(d)
        if agg is None:
            continue
        cg += agg["gross"]
        cn += agg["net"]
        series.append({"session": d, "gross_usd": agg["gross"],
                       "net_tier2_usd": agg["net"],
                       "cum_gross_usd": cg, "cum_net_tier2_usd": cn})
    return {
        "convention": "per-round-trip PnL realized at the exit grid "
                      "session (P-11 per-period series persistence, "
                      "LAUNCH REQUIREMENT: persisted for the future "
                      "DSR pass); zero-activity sessions omitted from "
                      "the row list; cumulative curves carry them",
        "sessions_with_activity": len(series),
        "series": series,
        "final_cum_gross_usd": cg,
        "final_cum_net_tier2_usd": cn,
    }


# --------------------------------------------------------------------------- #
# state-swap runner adapter (frozen run_cell, externally supplied state)
# --------------------------------------------------------------------------- #
class _StateSwapRunner:
    """Drives the FROZEN ar.run_cell with an externally supplied
    decision-state series (the A5 index-only shadow state or the
    seeded placebo state) on the arm's own placement surface.  Nothing
    in the frozen modules is modified."""

    def __init__(self, base_runner, state: dict, label: str):
        self._base = base_runner
        self._state = state
        self.arm_id = f"{base_runner.arm_id}#{label}"
        self.family_key = base_runner.family_key
        self.leg_subset = base_runner.leg_subset

    def build_state(self, ctx: dict) -> dict:
        return self._state

    def target_weights(self, state: float) -> dict:
        return self._base.target_weights(state)


def run_shadow_book(base_runner, state: dict, label: str, ctx: dict,
                    cost_source: dict) -> ar.CellResult:
    return ar.run_cell(_StateSwapRunner(base_runner, state, label),
                       ctx, cost_source)


def shadow_book_stats(shadow_book: ar.CellResult) -> dict:
    return book_stats([r["net_usd_tier2.0"]
                       for r in per_rt_rows(shadow_book)])


# --------------------------------------------------------------------------- #
# R2 under the bindings
# --------------------------------------------------------------------------- #
def r2_metrics_and_verdict(family: str, arm_exp: float | None,
                           ctl_exp: float | None,
                           calendar_distinct, placebo_significant,
                           books_distinct_measured) -> dict:
    """R2 CONTROL_KILL with the adjudication bindings applied.

    A5-P2: the frozen three-limb evaluate_r2, fully supplied.
    A4-P2: adjudication M-A -- limb (a) NOT_EXECUTABLE (neither kill
    nor pass); verdict rests on measured books_distinct + limbs (b)/(c);
    fail-closed NOT_RUN on any unmeasurable limb.
    """
    limbs = {
        "arm_expectancy_net_tier2": arm_exp,
        "index_control_expectancy_net_tier2": ctl_exp,
        "placebo_differential_significant": placebo_significant,
        "calendar_shadow_placement_distinct": calendar_distinct,
        "limb_c_convention": PLACEBO_LIMB_C_CONVENTION,
    }
    if family == "VOLNG1-A5-P2":
        metrics = {
            "arm_expectancy_net_tier2": arm_exp,
            "index_control_expectancy_net_tier2": ctl_exp,
            "calendar_shadow_placement_distinct": calendar_distinct,
            "placebo_differential_significant": placebo_significant,
        }
        verdict = ev.evaluate_r2(metrics)
        basis = ("frozen evaluate_r2, three limbs fully supplied; limb "
                 "(a) control = the a5_p2_spec index-only-shadow state "
                 "re-clocked onto the ETP buckets (scored control book "
                 "built at E under scored authority, same units as the "
                 "arm); A5-P2 D1 falsification rule binding site")
    else:
        if books_distinct_measured is None \
                or calendar_distinct is None \
                or placebo_significant is None:
            verdict = ev.NOT_RUN
            basis = ("A4-P2 adjudicated wrapper: an unmeasurable limb "
                     "(books_distinct both-books-empty, calendar "
                     "distinct None, or placebo reproduction "
                     "uncomputable) is NOT_RUN fail-closed, never an "
                     "inferred PASS (Q-11)")
        elif (books_distinct_measured is False
              or calendar_distinct is False
              or placebo_significant is True):
            verdict = ev.FAIL
            basis = ("A4-P2 adjudicated wrapper: a VETO limb fired "
                     "(books_distinct False, calendar shadow not "
                     "distinct, or placebo reproduction significant)")
        else:
            verdict = ev.PASS
            basis = ("A4-P2 adjudicated wrapper: no veto limb fired; "
                     "limb (a) NOT_EXECUTABLE per adjudication M-A "
                     "(neither kill NOR pass); R2 rests on the "
                     "measured books_distinct (addendum A1 law) and "
                     "the remaining family kill sites (D1 "
                     "falsification rule at R1/R5, cost-path control, "
                     "R3 fold law)")
        limbs["limb_a_status"] = (
            "NOT_EXECUTABLE (adjudication M-A, "
            "lead_adjudication_a7v2.json, commit "
            + ADJUDICATION_COMMIT + "): the cross-unit (index points "
            "vs USD) ratio is convention-dependent; contributes "
            "NEITHER kill NOR pass")
        limbs["books_distinct_measured"] = books_distinct_measured
    return {"metrics": limbs, "verdict": verdict, "basis": basis}


# --------------------------------------------------------------------------- #
# main
# --------------------------------------------------------------------------- #
def main() -> int:
    started_utc = utcnow()
    t0 = time.time()
    incidents: list[dict] = []
    cells_written: list[dict] = []
    ledger_path = os.path.join(E_DIR, "execution_ledger.json")
    family_path = os.path.join(E_DIR, "family_verdicts.json")
    gate_path = os.path.join(E_DIR, "e_gate.json")
    lock = None
    status = "TECHABORT"
    note = ""

    head_sha = _git("rev-parse", "HEAD")
    branch = _git("branch", "--show-current")
    if head_sha != DISPATCH_SHA or branch != BRANCH:
        raise SystemExit(
            f"FROZEN_SHA_MISMATCH: HEAD {head_sha} / branch {branch} != "
            f"dispatch {DISPATCH_SHA} / {BRANCH} (STOP)")

    try:
        # -- heavy-lock law ---------------------------------------------- #
        pre = locks_inspect()
        if pre.get("verdict") != "FREE_PROVEN":
            status = "TECHABORT"
            note = ("NOT_RUN_RESOURCE_CONFLICT: locks inspect verdict "
                    f"{pre.get('verdict')!r}")
            incidents.append({"id": "E-LOCK-NOT-FREE",
                              "detail": json.dumps(pre)[:2000]})
            print(note)
            return 3

        lock = heavy_lock.acquire(
            cycle_id="VOL-NG1", role="E_SCORED", worktree=REPO,
            command=sys.argv,
            expected_artifacts=[
                os.path.join(E_DIR, f"cell_{aid}.json") for aid, _ in CELLS
            ] + [family_path, gate_path, ledger_path])
        lock_started = lock.owner["started_at"]

        # -- authority chain (binding M-B) -------------------------------- #
        freeze_path = cfg.SELECTION_FREEZE_PATH
        freeze_sha = _sha256_file(freeze_path)
        if freeze_sha != FREEZE_SHA256:
            raise RuntimeError(
                f"selection freeze sha drift: {freeze_sha} != "
                f"{FREEZE_SHA256} (STOP)")
        fz = cfg.load_selection_freeze()
        if fz["s1_status"] != "SEALED_UNTOUCHED":
            raise RuntimeError("S1 not SEALED_UNTOUCHED (STOP)")
        addendum_path = os.path.join(
            CONTROL_DIR, "s", "selection_freeze_addendum_a7r1.json")
        adjudication_path = os.path.join(
            CONTROL_DIR, "audits", "lead_adjudication_a7v2.json")
        a7v2_path = os.path.join(
            CONTROL_DIR, "audits", "a7_prelaunch_v2_vol_ng1.json")
        authority = {
            "go_phrase": GO_PHRASE,
            "go_typed_by": "A1 Lead under owner standing delegation "
                           "(P-8) at this cycle's own gate",
            "selection_freeze": {
                "path": "research/control/vol_ng1_run/s/"
                        "selection_freeze.json",
                "sha256": freeze_sha,
                "bytes_verified_at_load": True},
            "addendum_a7r1": {
                "path": "research/control/vol_ng1_run/s/"
                        "selection_freeze_addendum_a7r1.json",
                "committed_at_commit": ADDENDUM_COMMIT,
                "sha256": _sha256_file(addendum_path)},
            "a7v2_audit": {
                "path": "research/control/vol_ng1_run/audits/"
                        "a7_prelaunch_v2_vol_ng1.json",
                "verdict_key": "VOL_NG1_S0_LAUNCH_AUTHORIZED",
                "committed_at_commit": A7V2_AUDIT_COMMIT,
                "sha256": _sha256_file(a7v2_path)},
            "lead_adjudication_a7v2": {
                "path": "research/control/vol_ng1_run/audits/"
                        "lead_adjudication_a7v2.json",
                "committed_at_commit": ADJUDICATION_COMMIT,
                "sha256": _sha256_file(adjudication_path),
                "bindings": {"M-A": MA_BINDING_VERBATIM,
                             "M-B": MB_BINDING_VERBATIM}},
            "stale_pre_remediation_disclosures": STALE_HISTORY_NOTE,
        }
        with open(adjudication_path, "r", encoding="utf-8") as fh:
            adj = json.load(fh)
        if adj.get("go_decision", {}).get("go_phrase") != GO_PHRASE:
            raise RuntimeError("adjudication GO phrase mismatch (STOP)")

        # -- frozen cells (digest gate inside, before ANY PnL) ------------ #
        arms = cfg.assemble_arm_configs(fz)
        contract = cfg.load_cost_contract()
        cost_source = cfg.cost_source_from_contract(contract)

        # -- real frozen substrate (identical path to the committed Z) ---- #
        plane = pa.VolNg1Plane()
        plane_verdicts = {s: plane.verdict(s)
                          for s in sorted(pa.FROZEN_TARGET_SET)}
        if not all(v == "GRANTED" for v in plane_verdicts.values()):
            raise RuntimeError(
                f"plane verdicts not all GRANTED: {plane_verdicts} "
                "(STOP)")
        sub = p2r.consume_substrate(plane)
        _adj, evlaw = p2r.event_adjusted_legs(sub)
        table = ca.build_event_table(ca.load_inventory())
        full_adj = {leg: ca.event_adjusted_closes(bars, table[leg])
                    for leg, bars in sub["etp_bars"].items()}
        grid = fb.common_grid(sub["index_closes"], full_adj)
        window = fb.window_sessions(grid)
        bookable, v7_tail = fb.bookable_sessions(grid, window)
        rep = fz["representation_freeze"]["common_grid"]
        rep_ok = {
            "grid_sessions_total_matches_freeze":
                len(grid) == rep["grid_sessions_total"],
            "bookable_instants_matches_freeze":
                len(bookable) == rep["bookable_instants"],
            "first_bookable_matches_freeze":
                bookable[0] == rep["first_bookable_instant"],
            "last_bookable_matches_freeze":
                bookable[-1] == rep["last_bookable_instant"],
            "v7_tail_matches_freeze":
                v7_tail == rep["v7_tail_refused_sessions"],
        }
        if not all(rep_ok.values()):
            raise RuntimeError(
                f"representation drift vs the freeze: {rep_ok} (STOP)")
        series_ok = {}
        for name, digest in fz["representation_freeze"][
                "series_consumption_law"][
                "series_digests_consumed_via_plane"].items():
            measured = (sub["index_digests"].get(name)
                        or sub["etp_digests"].get(name))
            series_ok[name] = {"digest": measured,
                               "matches_freeze": measured == digest}
        if not all(v["matches_freeze"] for v in series_ok.values()):
            raise RuntimeError("series digest drift vs the freeze (STOP)")
        substrate = {
            "mode": "REAL_FROZEN (plane-verified, read-only, no "
                    "network; event-adjusted layer mandatory)",
            "plane_verdicts": plane_verdicts,
            "series_digests_matches_freeze": series_ok,
            "representation_matches_freeze": rep_ok,
            "corp_actions": {
                "inventory_total_steps": evlaw["inventory_total_steps"],
                "max_abs_mechanical_residual":
                    evlaw["max_abs_mechanical_residual"],
                "consumption_law": evlaw["consumption_law"]},
        }

        # -- historical structural reconciliation targets (M-B) ----------- #
        z_targets, z_file_shas = {}, {}
        for aid, fname in Z_CELL_FILES.items():
            p = os.path.join(Z_DIR, fname)
            z_file_shas[aid] = _sha256_file(p)
            with open(p, "r", encoding="utf-8") as fh:
                z_targets[aid] = json.load(fh)["structural_counts"]

        # -- per-cell scored computation, ONE AT A TIME -------------------- #
        per_cell: dict[str, dict] = {}
        for aid, budget_cell in CELLS:
            cell_t0 = time.time()
            arm = arms[aid]
            family = FAMILY_OF[aid]
            runner = ar.runner_for_arm(arm)
            legs = tuple(arm["config"]["leg_subset"])
            ctx = ar.build_context_from_raw(
                sub["index_closes"], sub["etp_bars"], table, legs)
            for series in (ctx["index"], ctx["adj"]):
                for name, s in series.items():
                    missing = [d for d in bookable if d not in s]
                    if missing:
                        raise RuntimeError(
                            f"{aid}: series {name} missing "
                            f"{len(missing)} bookable sessions "
                            "(fail-closed)")
            ctx["grid"] = list(bookable)

            res = ar.run_cell(runner, ctx, cost_source)

            # structural reconciliation vs the historical committed counts
            m = res.meta
            zc = z_targets[aid]
            struct = {
                "grid_sessions": len(ctx["grid"]),
                "decisions": m["decisions"],
                "invalid_instants": m["invalid_instants"],
                "refused_tail_decisions": m["refused_tail_decisions"],
                "fills": m["fills"],
                "round_trips": m["round_trips"],
                "kernel_events": m["kernel_events"],
                "by_exit_reason": m["by_exit_reason"],
                "by_fold": m["by_fold"],
            }
            recon = {k: {"measured": struct.get(k),
                         "z_committed": zc.get(k),
                         "match": struct.get(k) == zc.get(k)}
                     for k in struct}
            struct_all_match = all(v["match"] for v in recon.values())
            if not struct_all_match:
                raise RuntimeError(
                    f"{aid}: structural drift vs the committed Z "
                    "manifest (arm books must be unchanged): "
                    f"{recon} (TECHABORT)")

            # scored rows + independent kernel-identity reconciliation
            rows = per_rt_rows(res)
            for i, r in enumerate(rows):
                book = res.kernel_events[i]["book"]
                g = acc.price_pnl_usd(
                    r["direction"], r["notional_usd"],
                    r["entry_price"], r["exit_price"])
                once = acc.per_fill_cost_usd(
                    r["notional_usd"],
                    cost_source[r["leg"]]["stress_spread_frac"],
                    cfg.PRIMARY_TIER)
                if not (_close(g, r["gross_usd"])
                        and _close(g - 2.0 * once, r["net_usd_tier2.0"])
                        and _close(book["gross_pnl_usd"],
                                   r["gross_usd"])
                        and _close(book["net_pnl_usd_by_tier"]["2.0"],
                                   r["net_usd_tier2.0"])):
                    raise RuntimeError(
                        f"{aid}: kernel identity reconciliation failed "
                        f"at round trip {i} (TECHABORT)")
            ledger_books = [e["book"] for e in res.kernel_events]
            dbl = acc.dual_book_ledger(ledger_books, starting_equity=0.0)
            if not dbl["dual_book_equality_ok"]:
                raise RuntimeError(
                    f"{aid}: dual-book identity failed (TECHABORT)")

            nets2 = [r["net_usd_tier2.0"] for r in rows]
            stats2 = book_stats(nets2)
            gross_stats = book_stats([r["gross_usd"] for r in rows])
            stats_by_tier = {
                str(t): book_stats([r[f"net_usd_tier{t}"] for r in rows])
                for t in cfg.COST_TIER_LADDER}
            folds = fold_expectancies(rows)
            drop = drop_one_fold(rows)
            conc = round_trip_concentration(rows)
            pps = per_period_series(rows, bookable)
            arm_exp = stats2["expectancy_usd"]

            # controls (scored)
            cpc = bat.cost_path_control(res, cost_source)
            stress_exp = (cpc["totals_by_tier"]["2.0"]
                          ["net_stress_usd_total"] / len(rows)) \
                if rows else None
            shadow_i = bat.index_only_shadow(runner, ctx, arm_result=res)
            shadow_c = bat.calendar_clock_shadow(
                runner, ctx, k=cfg.CALENDAR_SHIFT_K_SESSIONS)
            shadow_p = bat.placebo(runner, ctx, seed=cfg.PLACEBO_SEED)
            inv = bat.invalid_null_audit(res)

            # scored control / placebo books (built at E under authority)
            ctl_book = None
            ctl_stats = None
            if family == "VOLNG1-A5-P2":
                ctl_book = run_shadow_book(
                    runner, shadow_i.decision_state,
                    "index_shadow_book", ctx, cost_source)
                ctl_stats = shadow_book_stats(ctl_book)
            placebo_book = run_shadow_book(
                runner, shadow_p.decision_state, "placebo_book",
                ctx, cost_source)
            placebo_rows = per_rt_rows(placebo_book)
            placebo_stats = book_stats(
                [r["net_usd_tier2.0"] for r in placebo_rows])

            # R2 under the bindings
            if family == "VOLNG1-A5-P2":
                ctl_exp = ctl_stats["expectancy_usd"]
                placebo_sig = ev.control_reproduces(
                    placebo_stats["expectancy_usd"], arm_exp)
                r2 = r2_metrics_and_verdict(
                    family, arm_exp, ctl_exp,
                    shadow_c.distinct_from_arm, placebo_sig,
                    shadow_i.distinct_from_arm)
                ctl_block = {
                    "index_only_shadow": {
                        "control": "a5_p2_spec index-only shadow "
                                   "(both spread sides proxied from the "
                                   "VIX close alone, committed lookbacks "
                                   "21/90)",
                        "state_distinct_from_arm_measured":
                            shadow_i.distinct_from_arm,
                        "no_etp_price_in_state":
                            shadow_i.notes.get("no_etp_price_in_state"),
                        "scored_control_book": {
                            "construction": "the shadow state re-clocked "
                                            "onto the ETP buckets through "
                                            "the arm's own frozen book "
                                            "construction (same units as "
                                            "the arm)",
                            "round_trips": ctl_stats["round_trips"],
                            "expectancy_net_tier2_usd_per_rt":
                                ctl_stats["expectancy_usd"],
                            "per_round_trip_rows":
                                per_rt_rows(ctl_book)}},
                }
            else:
                ip_rows = shadow_i.book.get("round_trips", [])
                ip_points = [rt_["gross_index_points"]
                             for rt_ in ip_rows]
                placebo_sig = ev.control_reproduces(
                    placebo_stats["expectancy_usd"], arm_exp)
                r2 = r2_metrics_and_verdict(
                    family, arm_exp, None,
                    shadow_c.distinct_from_arm, placebo_sig,
                    shadow_i.distinct_from_arm)
                ctl_block = {
                    "index_only_shadow": {
                        "control": "A7-R1 addendum A1 hypothetical "
                                   "index-point book on the VIX close "
                                   "(no ETP leg, no ETP costs)",
                        "books_distinct_measured":
                            shadow_i.distinct_from_arm,
                        "distinct_from_arm_law":
                            shadow_i.notes.get("distinct_from_arm_law"),
                        "scored_control_book_disclosure": {
                            "unit": "INDEX POINTS per round trip "
                                    "(1 unit = 1.0 point); NOT "
                                    "unit-comparable to the arm's USD "
                                    "net book (adjudication M-A: "
                                    "comparison NOT_EXECUTABLE, "
                                    "neither kill nor pass)",
                            "round_trips": len(ip_rows),
                            "expectancy_index_points_per_rt":
                                (math.fsum(ip_points) / len(ip_points))
                                if ip_points else None,
                            "round_trip_index_point_gross": ip_points}},
                }
            ctl_block["placebo_scored_book"] = {
                "construction": PLACEBO_LIMB_C_CONVENTION,
                "round_trips": len(placebo_rows),
                "expectancy_net_tier2_usd_per_rt":
                    placebo_stats["expectancy_usd"],
                "per_round_trip_rows": placebo_rows,
            }

            # R1-R6 per the frozen evaluator + the R2 wrapper
            metrics = {
                "expectancy_net_tier2": stats2["expectancy_usd"],
                "fold_expectancies_net_tier2": folds,
                "profit_factor_net_tier2": stats2["profit_factor"],
                "stress_tier2_expectancy_net": stress_exp,
                "drop_one_fold_positive": {f: drop[f]["positive"]
                                           for f in drop},
                "max_single_round_trip_gross_share":
                    conc["max_single_round_trip_gross_share"],
            }
            r4 = ev.evaluate_r4(metrics)
            rules = {
                "R1_EXPECTANCY": ev.evaluate_r1(metrics),
                "R2_CONTROL_KILL": r2["verdict"],
                "R3_FOLDS": ev.evaluate_r3(metrics),
                "R4_PF": r4["verdict"],
                "R5_STRESS": ev.evaluate_r5(metrics),
                "R6_NON_CONCENTRATION": ev.evaluate_r6(metrics),
            }
            if family == "VOLNG1-A5-P2":
                full = dict(metrics)
                full["arm_expectancy_net_tier2"] = arm_exp
                full["index_control_expectancy_net_tier2"] = ctl_exp
                full["calendar_shadow_placement_distinct"] = \
                    shadow_c.distinct_from_arm
                full["placebo_differential_significant"] = placebo_sig
                frozen_r2 = ev.evaluate_r2(full)
                if frozen_r2 != rules["R2_CONTROL_KILL"]:
                    raise RuntimeError(
                        f"{aid}: R2 wrapper/frozen-evaluator divergence "
                        f"on an A5-P2 cell: {frozen_r2} vs "
                        f"{rules['R2_CONTROL_KILL']} (TECHABORT)")
            failed = [r for r, v in rules.items() if v == ev.FAIL]
            not_run = [r for r, v in rules.items() if v == ev.NOT_RUN]
            if failed:
                cell_verdict = "CELL_FAIL(" + ",".join(failed) + ")"
            elif not_run:
                cell_verdict = "CELL_NOT_RUN(" + ",".join(not_run) + ")"
            else:
                cell_verdict = "CELL_PASS"

            margins = {
                "R1_EXPECTANCY": {
                    "metric": "expectancy_net_tier2_usd_per_rt",
                    "value": stats2["expectancy_usd"], "bar": "> 0"},
                "R2_CONTROL_KILL": {
                    "limbs": {
                        "calendar_shadow_placement_distinct":
                            shadow_c.distinct_from_arm,
                        "placebo_differential_significant": placebo_sig,
                        "books_distinct_measured":
                            shadow_i.distinct_from_arm},
                    "basis": r2["basis"]},
                "R3_FOLDS": {
                    "metric": "folds_positive", "bar": ">= 2 of 3",
                    "value": sum(1 for v in folds.values()
                                 if v is not None and v > 0),
                    "fold_expectancies_net_tier2": folds},
                "R4_PF": {
                    "metric": "profit_factor_net_tier2",
                    "bar": cfg.PF_BAR,
                    "value": stats2["profit_factor"],
                    "margin_to_bar": r4["margin_to_bar"]},
                "R5_STRESS": {
                    "metric": "stress_tier2_expectancy_net_usd_per_rt",
                    "bar": "> 0",
                    "value": stress_exp,
                    "convention": "cost_path_control tier-2.0 "
                                  "net_stress (EXPENSE_IN_NET_STRESS "
                                  "pin) / n_round_trips",
                    "totals_by_tier": cpc["totals_by_tier"]},
                "R6_NON_CONCENTRATION": {
                    "drop_one_fold_positive":
                        {f: drop[f]["positive"] for f in drop},
                    "min_remaining_total_net_tier2_usd":
                        min(drop[f]["remaining_total_net_tier2_usd"]
                            for f in drop),
                    "max_single_round_trip_gross_share":
                        conc["max_single_round_trip_gross_share"],
                    "bar": "<= " + str(cfg.MAX_ROUND_TRIP_GROSS_SHARE)
                           + " and drop-one-fold survival"},
            }

            decisions_blob = json.dumps(
                res.decisions, sort_keys=True,
                separators=(",", ":")).encode("utf-8")
            identity = {
                "arm_id": aid,
                "budget_cell": budget_cell,
                "family_id": family,
                "arm_role": arm["role"],
                "arm_config_digest": arm["arm_config_digest"],
                "freeze_sha256": freeze_sha,
                "run_head_sha": head_sha,
                "run_branch": branch,
                "series_digests_matches_freeze": series_ok,
                "representation_matches_freeze": rep_ok,
                "round_trips": len(rows),
                "decisions_ledger_sha256":
                    hashlib.sha256(decisions_blob).hexdigest(),
                "structural_reconciliation_vs_z": {
                    "authority": STALE_HISTORY_NOTE,
                    "all_match": struct_all_match,
                    "detail": recon},
            }
            execution = {
                "exit_code": 0,
                "runtime_seconds": round(time.time() - cell_t0, 3),
                "started_utc": started_utc,
                "ended_utc": utcnow(),
                "scored": True,
                "real_pnl": True,
                "substrate": substrate["mode"],
                "lock": {"cycle_id": "VOL-NG1", "role": "E_SCORED",
                         "started_at": lock_started},
                "serialized": True,
            }
            gates = {
                "R1_EXPECTANCY": {
                    "verdict": rules["R1_EXPECTANCY"],
                    "input": {"expectancy_net_tier2":
                              metrics["expectancy_net_tier2"]}},
                "R2_CONTROL_KILL": {
                    "verdict": rules["R2_CONTROL_KILL"],
                    "inputs": r2["metrics"],
                    "basis": r2["basis"]},
                "R3_FOLDS": {
                    "verdict": rules["R3_FOLDS"],
                    "input": {"fold_expectancies_net_tier2": folds}},
                "R4_PF": {
                    "verdict": rules["R4_PF"],
                    "input": {"profit_factor_net_tier2":
                              metrics["profit_factor_net_tier2"],
                              "margin_to_bar": r4["margin_to_bar"]}},
                "R5_STRESS": {
                    "verdict": rules["R5_STRESS"],
                    "input": {"stress_tier2_expectancy_net": stress_exp,
                              "cost_path_control_totals":
                                  cpc["totals_by_tier"],
                              "expense_in_net_stress":
                                  bat.EXPENSE_IN_NET_STRESS}},
                "R6_NON_CONCENTRATION": {
                    "verdict": rules["R6_NON_CONCENTRATION"],
                    "input": {"drop_one_fold_positive":
                              metrics["drop_one_fold_positive"],
                              "max_single_round_trip_gross_share":
                              conc["max_single_round_trip_gross_share"],
                              "concentration_detail": conc}},
            }

            cell = {
                "schema": "vol_ng1_e_cell@1",
                "cycle_id": "VOL-NG1",
                "task_id": "vol-ng1-e-scored",
                "lane": "e",
                "authority": authority,
                "identity": identity,
                "execution": execution,
                "budget_delta": {
                    "observed": 1,
                    "published": 1,
                    "note": "observed +1 at computation; published at "
                            "commit inclusion of this artifact (single "
                            "substance commit of the e/ directory; "
                            "commit sha recorded in the lane handoff)"},
                "books": {
                    "primary_tier": "2.0",
                    "net_tier2.0": stats2,
                    "gross": gross_stats,
                    "net_by_tier": stats_by_tier,
                    "dual_book_ledger_reconciliation": {
                        "shared_identity_ok":
                            dbl["dual_book_equality_ok"],
                        "gross_total":
                            dbl["books"]["GROSS"]["gross_total"],
                        "net_2.0_total":
                            dbl["books"]["NET_2.0"]["equity_delta"]},
                },
                "per_round_trip_rows": rows,
                "per_period_series": pps,
                "folds": folds,
                "gates": gates,
                "margins": margins,
                "rule_verdicts": rules,
                "cell_verdict": cell_verdict,
                "controls": {
                    "index_only_shadow":
                        ctl_block["index_only_shadow"],
                    "calendar_clock_shadow": {
                        "calendar_shift_k_sessions":
                            shadow_c.notes["calendar_shift_k_sessions"],
                        "common_valid_decision_sessions":
                            shadow_c.notes[
                                "common_valid_decision_sessions"],
                        "distinct_from_arm_measured":
                            shadow_c.distinct_from_arm},
                    "placebo": {
                        "placebo_seed": shadow_p.notes["placebo_seed"],
                        "rng_kind": shadow_p.notes["rng_kind"],
                        "order_destroyed_measured":
                            shadow_p.distinct_from_arm,
                        "scored_book":
                            ctl_block["placebo_scored_book"]},
                    "invalid_null_distinction": inv,
                    "cost_path_control": {
                        "n_round_trips": cpc["n_round_trips"],
                        "n_fills": cpc["n_fills"],
                        "rebalance_closes": cpc["rebalance_closes"],
                        "buckets_present": cpc["buckets_present"],
                        "both_bucket_paths_paid":
                            cpc["both_bucket_paths_paid"],
                        "tier_ladder": cpc["tier_ladder"],
                        "primary_tier": cpc["primary_tier"],
                        "expense_in_net_stress":
                            cpc["expense_in_net_stress"],
                        "totals_by_tier": cpc["totals_by_tier"],
                        "q16_law": cpc["q16_law"]},
                },
                "disclosures": {
                    "conventions": "per-round-trip net tier-2.0 "
                                   "expectancy (USD); PF signed-sum "
                                   "with NOT_RUN on zero losers; R6 "
                                   "signed RT gross share with |share| "
                                   "variant; R5 stress includes the "
                                   "Q-16 path component and the "
                                   "expense line; per-period series "
                                   "persisted (P-11)",
                    "c8_limitation_travels_with_family":
                        C8_LIMITATION if family == "VOLNG1-A5-P2" else
                        None,
                    "r2_bindings": {
                        "M-A_applies": family == "VOLNG1-A4-P2",
                        "M-A_verbatim": MA_BINDING_VERBATIM
                        if family == "VOLNG1-A4-P2" else None,
                        "limb_c_convention":
                            PLACEBO_LIMB_C_CONVENTION},
                },
            }
            path = os.path.join(E_DIR, f"cell_{aid}.json")
            sha = _write_json(path, cell)
            cells_written.append({
                "arm_id": aid, "budget_cell": budget_cell,
                "family_id": family,
                "path": os.path.relpath(path, REPO), "sha256": sha,
                "cell_verdict": cell_verdict,
                "round_trips": len(rows),
                "expectancy_net_tier2_usd_per_rt":
                    stats2["expectancy_usd"],
                "profit_factor_net_tier2": stats2["profit_factor"]})
            per_cell[aid] = {
                "rules": rules, "margins": margins,
                "stats2": stats2, "stress_exp": stress_exp,
                "family": family, "cell_verdict": cell_verdict,
                "artifact_sha256": sha}
            lock.heartbeat(extra={"cell_written": aid})
            print(f"  cell {budget_cell} {aid}: {cell_verdict} "
                  f"(exp/rt {stats2['expectancy_usd']}, "
                  f"PF {stats2['profit_factor']})")

        # -- family verdicts ---------------------------------------------- #
        family_out = build_family_verdicts(
            fz, per_cell, authority, head_sha)
        _write_json(family_path, family_out)

        # -- e_gate ---------------------------------------------------------#
        gate = {
            "schema": "vol_ng1_e_gate@1",
            "cycle_id": "VOL-NG1",
            "task_id": "vol-ng1-e-scored",
            "lane": "e",
            "started_utc": started_utc,
            "published_utc": utcnow(),
            "worktree": REPO,
            "git": {"branch": branch, "head_sha": head_sha},
            "authority": authority,
            "substrate": substrate,
            "lock": {
                "mechanism": "machine-wide heavy lock "
                             "(research/governance/heavy_lock.py)",
                "pre_acquisition_inspect_verdict": pre.get("verdict"),
                "pre_acquisition_inspect_reason": pre.get("reason"),
                "cycle_id": "VOL-NG1",
                "role": "E_SCORED",
                "worktree": REPO,
                "started_at": lock_started,
                "runtime_dir": pre.get("runtime_dir"),
                "registry_path": pre.get("registry_path"),
                "history_path": pre.get("history_path"),
                "held_for": "the WHOLE scored run (all 6 cells, "
                            "serialized); released in finally after "
                            "artifact publication; the authoritative "
                            "terminal row is heavy_worker.history.jsonl",
            },
            "budget": {
                "planned": 6,
                "observed": len(cells_written),
                "published": len(cells_written),
                "law": "6 frozen cells (2 families x 3 arms), trial "
                       "budget 6/6; no unused slots; never reassigned",
                "cells": [{k: c[k] for k in (
                    "arm_id", "budget_cell", "family_id", "path",
                    "sha256", "cell_verdict", "round_trips",
                    "expectancy_net_tier2_usd_per_rt",
                    "profit_factor_net_tier2")}
                    for c in cells_written],
            },
            "pbo": {
                "verdict": "NOT_RUN_FAIL_CLOSED",
                "reason": "6 booked cells < 8 (CSCV undefined; V17 "
                          "contract)",
                "alternative_rule": cfg.PBO_ALTERNATIVE_RULE,
                "alternative_binding_site": "R6_NON_CONCENTRATION",
            },
            "p11": {
                "requirement": "per-period series persistence is a "
                               "LAUNCH REQUIREMENT",
                "status": "SATISFIED",
                "where": "every cell artifact carries per_period_series "
                         "(per-exit-session gross and PRIMARY NET "
                         "tier-2.0 rows with cumulative curves over the "
                         "frozen bookable grid)",
            },
            "s1": "SEALED_UNTOUCHED",
            "pnl_anywhere": True,
            "pnl_note": "SCORED LANE: real after-cost PnL on the six "
                        "frozen budget cells from the pinned bytes "
                        "through the frozen kernel + battery; this is "
                        "the only phase where outcome numbers are "
                        "lawful",
            "survivor_law": SURVIVOR_LAW,
            "no_tuning_declaration":
                "NO threshold, fold, arm parameter or convention "
                "governing a kill route moved after any scored number "
                "was seen (the R2 limb-(c) realization and every "
                "convention above are fixed in the driver BEFORE "
                "execution and disclosed verbatim in the committed "
                "artifacts)",
            "test_command": "/Users/hoangminhlong/my-quantitative/"
                            ".venv/bin/python -m pytest "
                            "tests/test_vol_ng1_i.py "
                            "tests/test_vol_ng1_z.py -q",
            "incidents": incidents,
        }
        _write_json(gate_path, gate)

        ledger = {
            "schema": "vol_ng1_e_execution_ledger@1",
            "cycle_id": "VOL-NG1",
            "task_id": "vol-ng1-e-scored",
            "lane": "e",
            "started_utc": started_utc,
            "ended_utc": utcnow(),
            "runtime_seconds": round(time.time() - t0, 3),
            "dispatch_sha": DISPATCH_SHA,
            "actual_start_sha": head_sha,
            "base_match": head_sha == DISPATCH_SHA,
            "branch": branch,
            "authority": authority,
            "substrate": substrate,
            "cells": cells_written,
            "digest_gates": {
                "freeze_sha256": freeze_sha,
                "cost_contract_sha256":
                    cfg.FROZEN_COST_CONTRACT_SHA256,
                "arm_digests": {aid: arms[aid]["arm_config_digest"]
                                for aid, _ in CELLS},
                "z_manifest_sha256": z_file_shas,
            },
            "lock": gate["lock"],
            "denominators": gate["budget"],
            "s1": "SEALED_UNTOUCHED",
            "pnl_anywhere": True,
            "incidents": incidents,
        }
        _write_json(ledger_path, ledger)
        status = "FINISHED"
        note = ("6/6 frozen cells scored under the heavy lock; real "
                "after-cost numbers + R1-R6 verdicts under "
                "research/control/vol_ng1_run/e/")
        print(note)
        return 0
    except heavy_lock.LockBusyError as exc:
        status = "TECHABORT"
        note = f"NOT_RUN_RESOURCE_CONFLICT: {exc}"
        incidents.append({"id": "E-LOCK-CONFLICT", "detail": str(exc)})
        print(note)
        return 3
    except Exception as exc:                        # technical failure
        status = "TECHABORT"
        note = f"{type(exc).__name__}: {exc}"
        incidents.append({
            "id": "E-TECHABORT",
            "error": f"{type(exc).__name__}: {exc}",
            "traceback_tail": traceback.format_exc()[-2000:],
            "exposure": "cells computed before the failure are listed "
                        "in this process's stdout only; no rescue, no "
                        "re-run for outcomes",
        })
        print(f"E TECHABORT: {note}")
        try:
            _write_json(ledger_path, {
                "schema": "vol_ng1_e_execution_ledger@1",
                "cycle_id": "VOL-NG1", "task_id": "vol-ng1-e-scored",
                "lane": "e", "verdict": "TECHABORT",
                "started_utc": started_utc, "ended_utc": utcnow(),
                "dispatch_sha": DISPATCH_SHA,
                "actual_start_sha": head_sha, "branch": branch,
                "cells": cells_written, "incidents": incidents,
                "error": note})
        except Exception:
            pass
        return 2
    finally:
        if lock is not None:
            try:
                lock.release(status=status, note=note)
            except Exception:
                pass


def build_family_verdicts(fz: dict, per_cell: dict, authority: dict,
                          head_sha: str) -> dict:
    """family_verdicts.json: per-cell SURVIVOR/KILL with cited rule +
    margin; family falsification bindings; PBO law."""
    rule_texts = {}
    for text in fz["rule_set_r1_r6"]["rule_order"]:
        rule_texts[text.split(" ")[0]] = text
    cells_block = {}
    for aid, pc in per_cell.items():
        verdict = pc["cell_verdict"]
        if verdict == "CELL_PASS":
            status = "SURVIVOR"
        elif verdict.startswith("CELL_FAIL"):
            status = "KILL"
        else:
            status = "NOT_RUN"
        cells_block[aid] = {
            "budget_cell": BUDGET_CELL_OF[aid],
            "family_id": pc["family"],
            "status": status,
            "cited_rules": pc["rules"],
            "cited_rule_texts": {
                r: rule_texts.get(r.split("_")[0], r)
                for r, v in pc["rules"].items() if v != "PASS"},
            "margins": pc["margins"],
            "metrics": {
                "expectancy_net_tier2_usd_per_rt":
                    pc["stats2"]["expectancy_usd"],
                "profit_factor_net_tier2":
                    pc["stats2"]["profit_factor"],
                "total_net_tier2_usd": pc["stats2"]["total_usd"],
                "stress_tier2_expectancy_net_usd_per_rt":
                    pc["stress_exp"]},
            "cell_artifact_sha256": pc["artifact_sha256"],
        }

    a4 = {aid: pc for aid, pc in per_cell.items()
          if pc["family"] == "VOLNG1-A4-P2"}
    a5 = {aid: pc for aid, pc in per_cell.items()
          if pc["family"] == "VOLNG1-A5-P2"}
    a4_exps = [pc["stats2"]["expectancy_usd"] for pc in a4.values()]
    a4_family_killed = (
        all(e is not None and e <= 0 for e in a4_exps)
        if all(e is not None for e in a4_exps) else None)
    a5_non_novel_kill = any(
        pc["rules"]["R2_CONTROL_KILL"] == "FAIL" for pc in a5.values())

    return {
        "schema": "vol_ng1_e_family_verdicts@1",
        "cycle_id": "VOL-NG1",
        "task_id": "vol-ng1-e-scored",
        "lane": "e",
        "run_head_sha": head_sha,
        "authority": authority,
        "survivor_law": SURVIVOR_LAW,
        "survivor_law_note": "survivor semantics attach ONLY to cells "
                             "with every rule PASS; any NOT_RUN or "
                             "FAIL blocks; S1 stays SEALED",
        "cells": cells_block,
        "families": {
            "VOLNG1-A4-P2": {
                "falsification_binding":
                    fz["rule_set_r1_r6"][
                        "family_falsification_binding"][0],
                "binding_site": "R1/R5",
                "family_kill_fired": a4_family_killed,
                "family_kill_law": "FAMILY kill if NO placed arm "
                                   "clears its committed per-leg "
                                   "worst-case round-trip cost ceiling "
                                   "after the FULL measured path-cost "
                                   "ladder at the primary stress tier "
                                   "-- equivalently every arm's "
                                   "after-cost expectancy on the "
                                   "primary NET book is at or below "
                                   "zero",
                "arm_expectancies_net_tier2_usd_per_rt": {
                    aid: pc["stats2"]["expectancy_usd"]
                    for aid, pc in a4.items()},
                "r2_binding_note": ("adjudication M-A applies to every "
                                    "A4-P2 cell: limb (a) "
                                    "NOT_EXECUTABLE, neither kill nor "
                                    "pass"),
            },
            "VOLNG1-A5-P2": {
                "falsification_binding":
                    fz["rule_set_r1_r6"][
                        "family_falsification_binding"][1],
                "binding_site": "R2",
                "family_non_novel_kill_fired": a5_non_novel_kill,
                "r2_binding_note": ("per-cell R2 carried the frozen "
                                    "three-limb evaluate_r2 fully "
                                    "supplied; the D1 non-distinctness "
                                    "kill fires only on a measured "
                                    "non-distinct/collapse veto"),
                "c8_limitation_travels_with_every_artifact":
                    C8_LIMITATION,
            },
        },
        "pbo": {
            "verdict": "NOT_RUN_FAIL_CLOSED",
            "reason": "6 booked cells < 8 (CSCV undefined; V17 "
                      "contract); frozen alternative robustness rule "
                      "R6 NON_CONCENTRATION applied in its place",
            "alternative_rule": cfg.PBO_ALTERNATIVE_RULE},
    }


if __name__ == "__main__":
    raise SystemExit(main())
