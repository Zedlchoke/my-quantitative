"""The preregistered gate + causal-control falsification + price-only clause.

This module encodes the FROZEN Stage-A decision rule of the
BASISLV-PREMFADE family (``research/proposals/v14/a5/BASISLV-PREMFADE.md``
sections 2/6/7/9; PLAN_crypto_v14.md section 12) as a pure rule evaluator.
It consumes only hand-supplied fold-sign vectors (booleans: "the arm's
BTC-beta-context weekly excess was positive in this chronological fold")
and the hand-supplied expectancy split produced by the FUTURE scored layer
(Phase E, after the owner GO) -- it computes NO PnL, no return, no excess
and no expectancy itself.

Preregistered binding gate (Stage-A, unrelaxed):

* the ANCHOR passes the incremental gate iff its BTC-beta-context weekly
  excess is positive in >= 2 of the 3 chronological folds; the raw excess
  vs the BTCUSDT buy-and-hold benchmark must additionally be positive in
  >= 2/3 folds for the family to advance;
* the NEIGHBOUR (``BASISLV-PREMFADE-56D``) supports the mechanism iff it
  carries the same sign; a flipped/failed neighbour means the premium level
  is formation-window fragile and the family is rejected;
* the CAUSAL NEGATIVE CONTROL (``BASISLV-PREMFADE-28D-INV``) MUST NOT
  reproduce the anchor: if the inverted book ALSO passes the incremental
  gate while the anchor passes, the premium ordering carries no directional
  crowding information, the anchor FAILS and the family is FALSIFIED.  The
  control is NEVER promotable to a family regardless of its own result
  (L-V11-3 / L-V12-1);
* the PRICE-ONLY FAILURE CLAUSE is a REQUIRED gate input (binding, declared
  ex ante): price-only expectancy <= 0 while total expectancy is positive
  only through native funding credits => carry-harvest artifact => the
  family is REJECTED.  The price-only / total split is computed by the
  scored layer and passed in here; when the inputs are missing this module
  refuses to advance the family (BLOCKED, fail-closed) -- missing evidence
  is never an inferred PASS.
"""

from __future__ import annotations

import math
from typing import Any, Optional, Sequence

from research.adapter_v10.protocol import ContractViolation

from research.v14.families.basislv_premfade.strategy import (
    ANCHOR_ARM,
    CONTROL_ARM,
    MIN_FOLDS,
    NEIGHBOUR_ARM,
    PRICE_ONLY_CLAUSE_TEXT,
)

GATE_SCHEMA = "v14i.basislv_premfade.gate.v1"

#: The frozen incremental gate (Stage-A, unrelaxed; proposal section 7).
INCREMENTAL_GATE_RULE = (
    "an arm passes the incremental gate iff its BTC-beta-context weekly "
    "excess is positive in >= 2 of the 3 frozen chronological folds "
    "(Stage-A, unrelaxed); the raw excess vs the BTCUSDT buy-and-hold "
    "benchmark must additionally be positive in >= 2/3 folds for the family "
    "to advance"
)

#: The preregistered causal-control rule (proposal section 6, verbatim intent).
CONTROL_RULE = (
    "control MUST NOT reproduce the anchor: if BASISLV-PREMFADE-28D-INV "
    "passes the same incremental gate (BTC-beta-context excess positive in "
    ">= 2/3 folds) while the anchor passes, the premium ordering carries no "
    "directional crowding information, any anchor result is a generic "
    "tilt/cost artifact, the anchor FAILS and the family is rejected; the "
    "control is never promotable to a family regardless of its own result"
)

NEIGHBOUR_RULE = (
    "the neighbour (BASISLV-PREMFADE-56D) supports the mechanism iff it "
    "shows the same sign (incremental gate passed); a flipped/failed "
    "neighbour means the premium level is formation-window fragile -- not "
    "the persistent crowding state the mechanism requires -- and the family "
    "is rejected"
)

#: Verdict vocabulary.
VERDICT_FAMILY_ADVANCES = "FAMILY_ADVANCES_TO_STAGE_A"
VERDICT_FALSIFIED_TILT = "FALSIFIED_CONTROL_REPRODUCED_TILT_ARTIFACT"
VERDICT_REJECTED_ANCHOR = "REJECTED_ANCHOR_FAIL"
VERDICT_REJECTED_NEIGHBOUR = "REJECTED_NEIGHBOUR_SIGN_FLIP"
VERDICT_REJECTED_CARRY_HARVEST = "REJECTED_PRICE_ONLY_CARRY_HARVEST"
VERDICT_BLOCKED_CLAUSE_INPUTS = "BLOCKED_PRICE_ONLY_CLAUSE_INPUTS_MISSING"

#: The control is never promotable, whatever its own result.
CONTROL_NEVER_PROMOTABLE = True

REQUIRED_FOLDS_POSITIVE = 2


def incremental_gate(fold_positive: Sequence[bool]) -> dict[str, Any]:
    """One arm's incremental gate over its chronological fold-sign vector."""
    signs = [bool(v) for v in fold_positive]
    if len(signs) != int(MIN_FOLDS):
        raise ContractViolation(
            f"the frozen family has exactly {MIN_FOLDS} chronological folds; "
            f"got {len(signs)} fold signs"
        )
    n_positive = sum(1 for v in signs if v)
    return {
        "schema": GATE_SCHEMA,
        "rule": INCREMENTAL_GATE_RULE,
        "fold_positive": signs,
        "n_folds": len(signs),
        "n_positive": int(n_positive),
        "required_positive": int(REQUIRED_FOLDS_POSITIVE),
        "passed": bool(n_positive >= REQUIRED_FOLDS_POSITIVE),
    }


def price_only_clause(
    *,
    price_only_expectancy: Optional[float],
    total_expectancy: Optional[float],
) -> dict[str, Any]:
    """The preregistered price-only failure clause (a gate INPUT).

    Fired iff ``price_only_expectancy <= 0`` while ``total_expectancy >
    0``: the anchor's total expectancy is then positive ONLY through native
    funding credits -- a carry harvest, not a price-unwind mechanism -- and
    the family is REJECTED as declared ex ante (V6 adjacency).  When either
    input is missing the clause reports ``status='NOT_EVALUATED'`` and the
    family verdict must be BLOCKED (never an inferred PASS).
    """
    if price_only_expectancy is None or total_expectancy is None:
        return {
            "schema": GATE_SCHEMA,
            "rule": PRICE_ONLY_CLAUSE_TEXT,
            "price_only_expectancy": None,
            "total_expectancy": None,
            "status": "NOT_EVALUATED",
            "fired": False,
            "inputs_missing": True,
        }
    po = float(price_only_expectancy)
    tot = float(total_expectancy)
    if not math.isfinite(po) or not math.isfinite(tot):
        raise ContractViolation(
            "price-only clause inputs must be finite numbers computed by the "
            "scored layer"
        )
    fired = bool(po <= 0.0 and tot > 0.0)
    return {
        "schema": GATE_SCHEMA,
        "rule": PRICE_ONLY_CLAUSE_TEXT,
        "price_only_expectancy": po,
        "total_expectancy": tot,
        "status": "APPLIED",
        "fired": fired,
        "inputs_missing": False,
    }


def evaluate_family_gate(
    *,
    anchor_fold_positive: Sequence[bool],
    control_fold_positive: Sequence[bool],
    neighbour_fold_positive: Sequence[bool],
    price_only_expectancy: Optional[float] = None,
    total_expectancy: Optional[float] = None,
    stress_passes: Optional[bool] = None,
) -> dict[str, Any]:
    """The preregistered family verdict over the three arms' fold signs.

    Rule order (first hit wins, exactly as preregistered):

    1. the price-only clause inputs are missing -> ``BLOCKED_PRICE_ONLY_
       CLAUSE_INPUTS_MISSING`` (the clause is a binding gate input; a family
       can never advance on missing evidence -- fail closed, never an
       inferred PASS);
    2. the clause FIRES (price-only <= 0 while total > 0) -> ``REJECTED_
       PRICE_ONLY_CARRY_HARVEST`` (declared ex ante, proposal section 9);
    3. anchor fails its incremental gate -> ``REJECTED_ANCHOR_FAIL``
       (no after-cost premium-level information at the weekly horizon; no
       parameter search, no window or universe retune);
    4. anchor passes AND the sign-inverted control passes -> the
       preregistered falsification fires: ``FALSIFIED_CONTROL_REPRODUCED_
       TILT_ARTIFACT`` (the anchor is a tilt artifact; family rejected; the
       control is never promotable);
    5. anchor passes, control fails, neighbour fails its gate -> the
       premium level is formation-window fragile:
       ``REJECTED_NEIGHBOUR_SIGN_FLIP``;
    6. otherwise -> ``FAMILY_ADVANCES_TO_STAGE_A`` (remaining Stage-A gates
       -- expectancy, PF, MDD, concentration, the stress set, drop-one
       survival, reproduction -- are evaluated by the scored layer; the
       optional ``stress_passes`` verdict is carried verbatim and recorded,
       ``None`` = NOT_EVALUATED).
    """
    anchor = incremental_gate(anchor_fold_positive)
    control = incremental_gate(control_fold_positive)
    neighbour = incremental_gate(neighbour_fold_positive)
    clause = price_only_clause(
        price_only_expectancy=price_only_expectancy,
        total_expectancy=total_expectancy,
    )

    if clause["inputs_missing"]:
        verdict = VERDICT_BLOCKED_CLAUSE_INPUTS
        reason = (
            "the price-only failure clause is a binding gate input and its "
            "expectancy split was not supplied; the family can never advance "
            "on missing evidence (fail closed, never an inferred PASS)"
        )
    elif clause["fired"]:
        verdict = VERDICT_REJECTED_CARRY_HARVEST
        reason = (
            "price-only expectancy <= 0 while total expectancy is positive "
            "only through native funding credits: the mechanism is a carry "
            "harvest, not a price-unwind mechanism; family rejected as "
            "declared ex ante (proposal sections 2(e)/9)"
        )
    elif not anchor["passed"]:
        verdict = VERDICT_REJECTED_ANCHOR
        reason = (
            "anchor BTC-beta-context excess not positive in >= 2/3 folds; "
            "no after-cost premium-level information at the weekly horizon "
            "(proposal section 9)"
        )
    elif control["passed"]:
        verdict = VERDICT_FALSIFIED_TILT
        reason = (
            "the sign-inverted control ALSO passes the incremental gate while "
            "the anchor passes: the premium ordering carries no directional "
            "crowding information and the anchor's result is a generic "
            "tilt/cost artifact (preregistered falsification, proposal "
            "section 6); the control is never promotable"
        )
    elif not neighbour["passed"]:
        verdict = VERDICT_REJECTED_NEIGHBOUR
        reason = (
            "neighbour sign flip/fragile: the premium level is not the "
            "persistent crowding state the mechanism requires (proposal "
            "section 9)"
        )
    else:
        verdict = VERDICT_FAMILY_ADVANCES
        reason = (
            "anchor passes the incremental gate, the price-only clause does "
            "not fire, the sign-inverted control does not reproduce it, and "
            "the 56d neighbour supports the sign"
        )
    return {
        "schema": GATE_SCHEMA,
        "anchor_arm": ANCHOR_ARM,
        "control_arm": CONTROL_ARM,
        "neighbour_arm": NEIGHBOUR_ARM,
        "anchor_gate": anchor,
        "control_gate": control,
        "neighbour_gate": neighbour,
        "price_only_clause": clause,
        "price_only_clause_required_input": (
            "the scored layer (Phase E) computes the price-only vs total "
            "expectancy split per arm and passes it here; this module never "
            "computes it"
        ),
        "control_rule": CONTROL_RULE,
        "neighbour_rule": NEIGHBOUR_RULE,
        "control_never_promotable": CONTROL_NEVER_PROMOTABLE,
        "stress_passes": (
            None if stress_passes is None else bool(stress_passes)
        ),
        "stress_rule": (
            "anchor passes base but fails stress => spread/slippage execution "
            "artifact; family rejected (proposal section 9; evaluated by the "
            "scored layer's stress set)"
        ),
        "verdict": verdict,
        "reason": reason,
    }


__all__ = [
    "CONTROL_NEVER_PROMOTABLE",
    "CONTROL_RULE",
    "GATE_SCHEMA",
    "INCREMENTAL_GATE_RULE",
    "NEIGHBOUR_RULE",
    "PRICE_ONLY_CLAUSE_TEXT",
    "REQUIRED_FOLDS_POSITIVE",
    "VERDICT_BLOCKED_CLAUSE_INPUTS",
    "VERDICT_FALSIFIED_TILT",
    "VERDICT_FAMILY_ADVANCES",
    "VERDICT_REJECTED_ANCHOR",
    "VERDICT_REJECTED_CARRY_HARVEST",
    "VERDICT_REJECTED_NEIGHBOUR",
    "evaluate_family_gate",
    "incremental_gate",
    "price_only_clause",
]
