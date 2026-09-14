"""RATES-NG1 I-phase R1-R6 scaffolding + the PBO law + emission
compliance scanner.

Cycle RATES-NG1, task rates-ng1-i-implementation.  Scaffolds the frozen
Stage-A rule order (freeze section_3_stage_a_rule_order_frozen, adapted
from the FOREX-NG1 selection-freeze precedent -- commit d0992d17df8e2d
fde57c9a0806a5798f14021a4f, content sha256 5d7eb5793e02e7919d59ba16a9f
a8c3041e3d7e23274c605fbec639c81d2c8ee -- with the declared adaptations:
this cycle's window/folds, the frozen tier-2.0 cost contract, R2
restated as this family's own declared executioner (D1 falsification
rule), R6 unit adapted from event to decision instant.  NO threshold was
moved: 0 / 2-of-3 / 1.10 / 50% carry over unchanged):

- R1 EXPECTANCY: after-cost expectancy > 0 per decision at the frozen
  tier-2.0 cost treatment (PRIMARY).
- R2 CONTROL_KILL: the declared executioner battery (battery.py) --
  level-vs-shape decomposition control + clock-only shadow + k=5
  misaligned placebo, same out-earning kill semantics.
- R3 FOLDS: at least 2 of 3 temporal folds positive; folds frozen by
  equal calendar-day thirds of 2019-01-07..2026-09-11 (2804 days);
  force-flat at fold ends.
- R4 PROFIT FACTOR: >= 1.10 with margin recorded (P-2).
- R5 STRESS: retained for rule-order fidelity -- the frozen RATES-NG1
  ladder has a SINGLE tier (tier 2.0), which is both PRIMARY and the
  stress ceiling, so R5's treatment coincides with R1's (disclosed
  coincidence in the freeze; never silently dropped).
- R6 NON_CONCENTRATION: drop-one-fold survival + no single decision
  instant contributing more than 50% of gross.
- survivor := passes ALL six rules -> PROVISIONAL_STAGE_A_SURVIVOR;
  S1 stays SEALED; no rescue, no threshold move (P-15).

PBO LAW (read from the cited precedent chain and followed exactly):
PBO is FAIL-CLOSED NOT_RUN when cells < 8.  With the 3 booked cells of
this cycle (3 < 8), the PBO diagnostic is recorded
NOT_RUN_FAIL_CLOSED_CELLS_LT_8 -- never estimated, never imputed.
Sources (frozen law, cited not modified): plans/PLAN_rates_ng1.md sec5
"PBO fail-closed < 8 cells"; plans/PLAN_forex_ng1.md sec5 "PBO
fail-closed when cells < 8" (the FOREX-NG1 precedent the freeze cites
for the rule order); plans/PLAN_crypto_ng1.md sec5 "PBO fail-closed
NOT_RUN when cells < 8 (V17 contract)" (the law the rates plan adopts
by reference in its sec7-9 'identical law' clause).

This module computes NO outcome numbers on real substrate anywhere in
I; its comparators run on synthetic edge fixtures in the I tests only.
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

from research.assets.rates_ng1.runners.battery import KILLER_ROLES
from research.assets.rates_ng1.runners.runner import (
    FOLD_WINDOWS,
    RunnerLawError,
    fold_of_session,
)

SCHEMA = "rates_ng1/runners/rules@1"

# ------------------------------------------------------------------ #
# Frozen rule bounds (carry over unchanged from the FOREX-NG1          #
# precedent; a move after any scored number is forbidden -- P-15).     #
# ------------------------------------------------------------------ #

R1_EXPECTANCY_GT = 0.0
R3_FOLDS_TOTAL = 3
R3_MIN_POSITIVE_FOLDS = 2
R4_PF_MIN = 1.10
R6_MAX_SINGLE_INSTANT_GROSS_SHARE = 0.5
PBO_MIN_CELLS = 8

#: The frozen rule order, verbatim in substance (see module docstring
#: for the adaptation provenance).
FROZEN_RULE_ORDER = (
    "R1 EXPECTANCY: after-cost expectancy > 0 per decision at the "
    "frozen tier-2.0 cost treatment (PRIMARY), on the identical "
    "bookable grid and window.",
    "R2 CONTROL_KILL (declared executioner, V8 law adapted): the "
    "MANDATORY level-vs-shape decomposition control arm earns a "
    "strictly greater after-cost per-decision edge than the anchor arm "
    "it is paired against -> the family fails; the clock-only shadow "
    "and the misaligned-state placebo carry the same out-earning kill "
    "semantics as secondary executioners (D1 falsification rule).",
    "R3 FOLDS: at least 2 of 3 temporal folds with positive after-cost "
    "expectancy; folds frozen by equal calendar-day thirds of the "
    "bookable window 2019-01-07..2026-09-11 (2804 days); force-flat at "
    "fold ends.",
    "R4 PROFIT FACTOR: profit factor >= 1.10 with margin recorded "
    "(P-2).",
    "R5 STRESS: after-cost expectancy under the stress-tier cost "
    "treatment still > 0 (single-tier ladder: coincides with R1; "
    "retained for rule-order fidelity, never silently dropped).",
    "R6 NON_CONCENTRATION: drop-one-fold survival + no single decision "
    "instant contributing more than 50% of gross (unit adapted from "
    "the precedent's 'event' to 'decision instant').",
)

PBO_CITATIONS = (
    {"path": "plans/PLAN_rates_ng1.md", "section": "sec5",
     "law": "PBO fail-closed < 8 cells"},
    {"path": "plans/PLAN_forex_ng1.md", "section": "sec5",
     "law": "PBO fail-closed when cells < 8",
     "role": "FOREX-NG1 precedent the freeze cites for the rule order"},
    {"path": "plans/PLAN_crypto_ng1.md", "section": "sec5",
     "law": "PBO fail-closed NOT_RUN when cells < 8 (V17 contract)",
     "role": "law the rates plan adopts by reference (sec7-9 identical "
             "law clause)"},
    {"path": "research/control/forex_ng1_run/selection_freeze.json",
     "commit_sha": "d0992d17df8e2dfde57c9a0806a5798f14021a4f",
     "content_sha256": "5d7eb5793e02e7919d59ba16a9fa8c3041e3d7e23274c"
                       "605fbec639c81d2c8ee",
     "role": "stage_a_rule_order_frozen source (R1-R6 precedent)"},
)

#: Emission-compliance tokens (FOREX-NG1 I-phase leak-scan method,
#: adapted): an emitted structural payload must carry NO key matching
#: these outcome-field patterns at any depth.
EMISSION_FORBIDDEN_PATTERNS = (
    "pnl", "profit_?factor", "^pf$", "expectancy", "sharpe",
    "drawdown", "win_?rate", "total_?return",
    "breakeven|break_?even",
)


def fold_bounds() -> tuple[tuple[str, str], ...]:
    """The frozen equal-thirds fold windows (R3), verbatim."""
    return FOLD_WINDOWS


def fold_of_session(session_iso: str) -> int:
    """Fold index (1-based) of a decision session; outside the frozen
    windows is fail-closed."""
    return fold_of_session(session_iso)


def pbo_record(n_cells: int) -> dict:
    """The PBO law, applied exactly: with fewer than PBO_MIN_CELLS
    cells the diagnostic is FAIL-CLOSED NOT_RUN (never estimated, never
    imputed).  With >= 8 cells it is still not computable at I (I
    computes no diagnostics on any outcome series): the scaffold
    records NOT_RUN_I_NO_MEASUREMENT and the computation stays an E/T
    phase surface.  Both states are NOT_RUN with DISTINCT reasons
    (Q-11 spirit)."""
    n_cells = int(n_cells)
    if n_cells < PBO_MIN_CELLS:
        status = "NOT_RUN_FAIL_CLOSED_CELLS_LT_8"
        reason = (f"{n_cells} booked cells < {PBO_MIN_CELLS}: the CSCV/"
                  f"PBO diagnostic is fail-closed NOT_RUN by the frozen "
                  f"ng1 plan law; never estimated, never imputed")
    else:
        status = "NOT_RUN_I_NO_MEASUREMENT"
        reason = ("cells suffice for PBO, but I computes no diagnostic "
                  "on any outcome series; requires E-phase per-cell "
                  "after-cost per-decision series")
    return {
        "schema": SCHEMA + ":pbo",
        "n_cells": n_cells,
        "pbo_min_cells": PBO_MIN_CELLS,
        "status": status,
        "reason": reason,
        "citations": PBO_CITATIONS,
    }


def _mean(vals: Sequence[float]) -> float | None:
    return sum(vals) / len(vals) if vals else None


def profit_factor(edges: Sequence[float]) -> dict:
    """R4 profit factor on per-decision after-cost edges: gross win /
    gross loss.  With NO losing edge the ratio is UNDEFINED (recorded
    None, Q-11: never inferred as infinite)."""
    wins = sum(e for e in edges if e > 0.0)
    losses = -sum(e for e in edges if e < 0.0)
    pf = (wins / losses) if losses > 0.0 else None
    margin = None if pf is None else pf - R4_PF_MIN
    return {
        "gross_win": wins,
        "gross_loss": losses,
        "profit_factor": pf,
        "pf_min": R4_PF_MIN,
        "margin_recorded": margin,
        "undefined_note": None if pf is not None
        else "no losing edge in the series: PF undefined (Q-11: not "
             "inferred)",
    }


def evaluate_r1_r6(edges: Sequence[float | None],
                   fold_ids: Sequence[int],
                   battery: Mapping[str, Any] | None = None,
                   single_instant_gross: Sequence[float] | None = None,
                   ) -> dict:
    """Evaluate the frozen R1-R6 order on ONE per-decision after-cost
    edge series (synthetic fixtures only in I).  ``battery`` is the
    battery_verdict dict for R2 (required for a survivor verdict; None
    records R2 NOT_RUN).  ``single_instant_gross`` (E-phase input)
    enables the R6 concentration leg; None records that leg NOT_RUN
    without blocking the drop-one-fold leg."""
    if len(edges) != len(fold_ids):
        raise RunnerLawError("edges/fold_ids length mismatch")
    defined = [(float(e), int(f)) for e, f in zip(edges, fold_ids)
               if e is not None]
    values = [e for e, _ in defined]

    # R1 (and R5's disclosed single-tier coincidence).
    mean_edge = _mean(values)
    r1_pass = mean_edge is not None and mean_edge > R1_EXPECTANCY_GT
    r1 = {
        "rule": "R1",
        "n_defined": len(values),
        "mean_edge": mean_edge,
        "bound": R1_EXPECTANCY_GT,
        "pass": bool(r1_pass),
        "margin": None if mean_edge is None else mean_edge
        - R1_EXPECTANCY_GT,
    }
    r5 = {
        "rule": "R5",
        "coincidence_note": "single-tier ladder (tier 2.0 is both "
                            "PRIMARY and the stress ceiling): R5's "
                            "treatment coincides with R1; retained for "
                            "rule-order fidelity",
        "mean_edge": mean_edge,
        "pass": bool(r1_pass),
    }

    # R2 (battery-executed declared executioner).
    if battery is None:
        r2 = {"rule": "R2", "status": "NOT_RUN_NO_BATTERY_INPUT",
              "pass": False,
              "note": "requires battery_verdict on after-cost edge "
                      "series (E-phase input; synthetic-only in I)"}
    else:
        roles_seen = [c.get("control_role")
                      for c in battery.get("comparisons", [])]
        unexpected = sorted(set(roles_seen) - set(KILLER_ROLES))
        if unexpected:
            raise RunnerLawError(
                f"battery carries unknown killer roles {unexpected}")
        r2 = {
            "rule": "R2",
            "family_kill": bool(battery.get("family_kill")),
            "killed_by": list(battery.get("killed_by", [])),
            "pass": not bool(battery.get("family_kill")),
        }

    # R3 (frozen equal-thirds folds).
    folds_present = sorted({f for _, f in defined})
    per_fold_means: dict[str, float | None] = {}
    positive_folds = 0
    for f in folds_present:
        vals = [e for e, ff in defined if ff == f]
        m = _mean(vals)
        per_fold_means[str(f)] = m
        if m is not None and m > 0.0:
            positive_folds += 1
    r3 = {
        "rule": "R3",
        "fold_windows": [list(w) for w in fold_bounds()],
        "folds_present": folds_present,
        "per_fold_means": per_fold_means,
        "positive_folds": positive_folds,
        "required": R3_MIN_POSITIVE_FOLDS,
        "pass": positive_folds >= R3_MIN_POSITIVE_FOLDS,
    }

    # R4 (profit factor with recorded margin, P-2).
    pf = profit_factor(values)
    r4 = {
        "rule": "R4",
        **pf,
        "pass": pf["profit_factor"] is not None
        and pf["profit_factor"] >= R4_PF_MIN,
    }

    # R6 (drop-one-fold survival + single-instant concentration).
    drop_one: dict[str, Any] = {}
    for f in folds_present:
        rest = [e for e, ff in defined if ff != f]
        m = _mean(rest)
        drop_one[str(f)] = {
            "mean_excl_fold": m,
            "positive": bool(m is not None and m > 0.0),
        }
    if single_instant_gross is not None:
        gross = [float(g) for g in single_instant_gross]
        total = sum(gross)
        shares = {i: (g / total if total > 0 else None)
                  for i, g in enumerate(gross)}
        defined_shares = [s for s in shares.values() if s is not None]
        max_share = max(defined_shares) if defined_shares else None
        concentration = {
            "status": "MEASURED",
            "max_single_instant_share": max_share,
            "bound": R6_MAX_SINGLE_INSTANT_GROSS_SHARE,
            "pass": bool(max_share is not None
                         and max_share <=
                         R6_MAX_SINGLE_INSTANT_GROSS_SHARE),
        }
    else:
        concentration = {
            "status": "NOT_RUN_NO_GROSS_INPUT",
            "note": "requires E-phase per-instant gross series; "
                    "synthetic-only in I",
        }
    r6 = {
        "rule": "R6",
        "drop_one_fold": drop_one,
        "drop_one_all_positive": all(v["positive"]
                                     for v in drop_one.values()),
        "concentration": concentration,
    }
    # R6 passes iff drop-one survival holds AND the concentration leg
    # does not FAIL (MEASURED and within bound, or NOT_RUN at I --
    # a NOT_RUN leg is recorded, never promoted to a failure).
    r6["pass"] = bool(r6["drop_one_all_positive"]
                      and concentration.get("pass") is not False)

    rules = {"R1": r1, "R2": r2, "R3": r3, "R4": r4, "R5": r5, "R6": r6}
    all_pass = all(rules[r]["pass"] for r in
                   ("R1", "R2", "R3", "R4", "R5", "R6"))
    return {
        "schema": SCHEMA,
        "frozen_rule_order": list(FROZEN_RULE_ORDER),
        "rules": rules,
        "survivor": "PROVISIONAL_STAGE_A_SURVIVOR" if all_pass
        else "NOT_A_SURVIVOR",
        "failed_rules": [r for r in ("R1", "R2", "R3", "R4", "R5", "R6")
                         if not rules[r]["pass"]],
        "p15_note": "S1 stays SEALED; no rescue, no threshold move, no "
                    "variant addition after any scored number is seen",
    }


def scan_emission_for_outcome_tokens(payload: Any) -> dict:
    """Emission compliance (FOREX-NG1 I-phase leak-scan method,
    adapted): recursive walk (dicts + lists, every depth) of an emitted
    structural payload; every KEY is case/underscore/hyphen-normalized
    and matched against the forbidden outcome-field patterns; any hit
    is a LEAK (non-null value law: a hit on any key is a violation in
    this structural-only emission)."""
    patterns = [re.compile(p, re.IGNORECASE) for p
                in EMISSION_FORBIDDEN_PATTERNS]
    leaks: list[dict] = []

    def norm(k: str) -> str:
        return re.sub(r"[-_\s]+", "_", str(k)).strip("_").lower()

    def walk(node: Any, path: str) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                nk = norm(k)
                for pat in patterns:
                    if pat.search(nk):
                        leaks.append({"path": f"{path}.{k}",
                                      "pattern": pat.pattern})
                        break
                walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")

    walk(payload, "$")
    return {
        "schema": SCHEMA + ":emission_scan",
        "patterns": list(EMISSION_FORBIDDEN_PATTERNS),
        "leaks": leaks,
        "clean": not leaks,
    }
