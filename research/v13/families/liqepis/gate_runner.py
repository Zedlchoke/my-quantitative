"""The preregistered incremental gate + causal-control falsification rule.

This module encodes the FROZEN Stage-A decision rule of the LIQEPIS family
(``research/proposals/v13/a5/LIQEPIS.md`` sections 2/6/7; PLAN_crypto_v13.md
section 12) as a pure rule evaluator.  It consumes only hand-supplied
fold-sign vectors (booleans: "the arm's BTC-beta-context weekly excess was
positive in this chronological fold") produced by the FUTURE scored layer
(Phase E, after the owner GO) -- it computes NO PnL, no return and no
excess itself.

Preregistered binding gate (Stage-A, unrelaxed):

* the ANCHOR passes the incremental gate iff its BTC-beta-context weekly
  excess is positive in >= 2 of the 3 chronological folds;
* the NEIGHBOUR supports the mechanism iff it carries the same sign
  (>= 2/3 folds positive);
* the CAUSAL NEGATIVE CONTROL (``LIQEPIS-SIGN-INV``) MUST NOT reproduce the
  anchor: if the inverted book ALSO passes the incremental gate while the
  anchor passes, the smooth-vs-episodic ordering carries no directional
  liquidity information, the anchor's result is a generic tilt artifact,
  the anchor FAILS and the family is FALSIFIED.  The control is NEVER
  promotable to a family regardless of its own result.
"""

from __future__ import annotations

from typing import Any, Sequence

from research.adapter_v10.protocol import ContractViolation

from research.v13.families.liqepis.strategy import (
    ANCHOR_ARM,
    CONTROL_ARM,
    MIN_FOLDS,
    NEIGHBOUR_ARM,
)

GATE_SCHEMA = "v13i.liqepis.gate.v1"

#: The frozen incremental gate (Stage-A, unrelaxed; proposal item 07).
INCREMENTAL_GATE_RULE = (
    "an arm passes the incremental gate iff its BTC-beta-context weekly "
    "excess is positive in >= 2 of the 3 frozen chronological folds "
    "(Stage-A, unrelaxed); the raw excess vs the BTCUSDT buy-and-hold "
    "benchmark must additionally be positive in >= 2/3 folds for the family "
    "to advance"
)

#: The preregistered causal-control rule (proposal item 06, verbatim intent).
CONTROL_RULE = (
    "control MUST NOT reproduce the anchor: if LIQEPIS-SIGN-INV passes the "
    "same incremental gate (BTC-beta-context excess positive in >= 2/3 "
    "folds) while the anchor passes, the episodic-liquidity mechanism is "
    "falsified (the ordering carries no directional liquidity information; "
    "any anchor result is a tilt/cost artifact), the anchor FAILS and the "
    "family is rejected; the control is never promotable to a family "
    "regardless of its own result"
)

NEIGHBOUR_RULE = (
    "the neighbour (LIQEPIS-56D) supports the mechanism iff it shows the "
    "same sign (incremental gate passed); a flipped/failed neighbour means "
    "the shape is formation-window fragile and the family is rejected"
)

#: Verdict vocabulary.
VERDICT_FAMILY_ADVANCES = "FAMILY_ADVANCES_TO_STAGE_A"
VERDICT_FALSIFIED_TILT = "FALSIFIED_CONTROL_REPRODUCED_TILT_ARTIFACT"
VERDICT_REJECTED_ANCHOR = "REJECTED_ANCHOR_FAIL"
VERDICT_REJECTED_NEIGHBOUR = "REJECTED_NEIGHBOUR_SIGN_FLIP"

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


def evaluate_family_gate(
    *,
    anchor_fold_positive: Sequence[bool],
    control_fold_positive: Sequence[bool],
    neighbour_fold_positive: Sequence[bool],
) -> dict[str, Any]:
    """The preregistered family verdict over the three arms' fold signs.

    Rule order (first hit wins, exactly as preregistered):

    1. anchor fails its incremental gate -> ``REJECTED_ANCHOR_FAIL``
       (no after-cost directional edge; family rejected, no parameter
       search);
    2. anchor passes AND the sign-inverted control passes -> the
       preregistered falsification fires: ``FALSIFIED_CONTROL_REPRODUCED_
       TILT_ARTIFACT`` (the anchor is a tilt artifact; family rejected; the
       control is never promotable);
    3. anchor passes, control fails, neighbour fails its gate -> the shape
       is formation-window fragile: ``REJECTED_NEIGHBOUR_SIGN_FLIP``;
    4. otherwise -> ``FAMILY_ADVANCES_TO_STAGE_A`` (remaining Stage-A gates
       -- expectancy, PF, MDD, concentration, stress set, drop-one
       survival, reproduction -- are evaluated by the scored layer).
    """
    anchor = incremental_gate(anchor_fold_positive)
    control = incremental_gate(control_fold_positive)
    neighbour = incremental_gate(neighbour_fold_positive)

    if not anchor["passed"]:
        verdict = VERDICT_REJECTED_ANCHOR
        reason = (
            "anchor BTC-beta-context excess not positive in >= 2/3 folds; "
            "no after-cost directional liquidity edge (proposal item 09)"
        )
    elif control["passed"]:
        verdict = VERDICT_FALSIFIED_TILT
        reason = (
            "the sign-inverted control ALSO passes the incremental gate while "
            "the anchor passes: the smooth-vs-episodic ordering carries no "
            "directional liquidity information and the anchor's result is a "
            "generic tilt artifact (preregistered falsification, proposal "
            "item 06); the control is never promotable"
        )
    elif not neighbour["passed"]:
        verdict = VERDICT_REJECTED_NEIGHBOUR
        reason = (
            "neighbour sign flip/fragile: the shape is not the persistent "
            "characteristic the mechanism requires (proposal item 09)"
        )
    else:
        verdict = VERDICT_FAMILY_ADVANCES
        reason = (
            "anchor passes the incremental gate, the sign-inverted control "
            "does not reproduce it, and the 56d neighbour supports the sign"
        )
    return {
        "schema": GATE_SCHEMA,
        "anchor_arm": ANCHOR_ARM,
        "control_arm": CONTROL_ARM,
        "neighbour_arm": NEIGHBOUR_ARM,
        "anchor_gate": anchor,
        "control_gate": control,
        "neighbour_gate": neighbour,
        "control_rule": CONTROL_RULE,
        "neighbour_rule": NEIGHBOUR_RULE,
        "control_never_promotable": CONTROL_NEVER_PROMOTABLE,
        "verdict": verdict,
        "reason": reason,
    }


__all__ = [
    "CONTROL_NEVER_PROMOTABLE",
    "CONTROL_RULE",
    "GATE_SCHEMA",
    "INCREMENTAL_GATE_RULE",
    "NEIGHBOUR_RULE",
    "REQUIRED_FOLDS_POSITIVE",
    "VERDICT_FALSIFIED_TILT",
    "VERDICT_FAMILY_ADVANCES",
    "VERDICT_REJECTED_ANCHOR",
    "VERDICT_REJECTED_NEIGHBOUR",
    "evaluate_family_gate",
    "incremental_gate",
]
