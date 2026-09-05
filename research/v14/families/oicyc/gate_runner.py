"""The preregistered Stage-A gates + causal-control falsification rule.

This module encodes the FROZEN Stage-A decision rules of the OICYC family
(``research/proposals/v14/a8/OICYC.md`` sections 2/6/7; PLAN_crypto_v14.md
section 12) as pure rule evaluators.  They consume only hand-supplied
fold-sign vectors and per-arm metric scalars produced by the FUTURE scored
layer (Phase E, after the owner GO) -- they compute NO PnL, no return, no
excess and no metric themselves.

Frozen Stage-A gate set (plan section 12; V13 set unchanged, unrelaxed --
proposal section 2):

* anchor passes its three headline gates iff {after-cost expectancy > 0,
  position PF >= 1.10, >= 2/3 chronological folds positive};
* incremental-context gate (decisive for OICYC's identity, proposal
  section 7): BOTH excess series -- ``arm_net - BTC_buy_and_hold`` and
  ``arm_net - beta_p * BTC`` (trailing 90d PIT beta held fixed per fold) --
  must be positive in >= 2/3 folds; positive raw PnL NEVER overrides a
  failed incremental context;
* neighbour supports iff it carries the same sign (headline gates pass);
  a contradictory or fold-unstable neighbour is falsifier #4;
* causal negative control ``CTL-OISHARE`` MUST NOT reproduce the anchor:
  if the control ALSO passes all three headline gates while the anchor
  passes, the edge is an OI-dominance/size artifact and the family is
  FALSIFIED; the control is NEVER promotable;
* largest fold-positive share of PnL > 50% is a falsifier (single-regime
  artifact);
* every verdict carries the preregistered CONFIRMATORY status (plan
  Section 1.1) so the driver records it in the verdict and denominator.
"""

from __future__ import annotations

from typing import Any, Sequence

from research.adapter_v10.protocol import ContractViolation

from research.v14.families.oicyc.strategy import (
    ANCHOR_ARM,
    CONFIRMATORY,
    CONTROL_ARM,
    MIN_FOLDS,
    NEIGHBOUR_ARM,
    SECTION_1_1_DISCLOSURE,
)

GATE_SCHEMA = "v14i.oicyc.gate.v1"

#: The frozen headline gate (Stage-A, unrelaxed).
HEADLINE_GATE_RULE = (
    "an arm passes the headline gates iff {after-cost expectancy > 0, "
    "position PF >= 1.10, >= 2/3 chronological folds positive} (Stage-A, "
    "unrelaxed)"
)

#: The frozen incremental-context gate (OICYC.md section 7, decisive).
INCREMENTAL_GATE_RULE = (
    "both excess series (vs BTC buy-and-hold AND vs the BTC-beta context) "
    "must be positive in >= 2 of the 3 frozen chronological folds; a "
    "non-positive beta-context excess in >= 2 folds is PRICE-beta "
    "repackaging and falsifies"
)

#: The preregistered causal-control rule (OICYC.md section 6, verbatim).
CONTROL_RULE = (
    "control MUST NOT reproduce the anchor: if CTL-OISHARE passes all "
    "three headline gates while the anchor passes, the edge is an "
    "OI-dominance/size effect, the co-movement information is redundant, "
    "and A14-V14-A8-OICYC is FALSIFIED as a cycle-participation mechanism; "
    "the control is never promotable regardless of its own result"
)

NEIGHBOUR_RULE = (
    "the neighbour (CYC-14D) supports the mechanism iff it carries the "
    "anchor's sign (headline gates pass); a contradicting or fold-unstable "
    "neighbour means the slope estimate is window-fragile and the family "
    "is falsified (OICYC.md falsifier 4)"
)

CONCENTRATION_RULE = (
    "largest fold-positive share of PnL <= 50%; a larger share is a "
    "single-regime artifact and falsifies (OICYC.md falsifier 5)"
)

#: Verdict vocabulary.
VERDICT_FAMILY_ADVANCES = "FAMILY_ADVANCES_TO_STAGE_A"
VERDICT_FALSIFIED_CONTROL = "FALSIFIED_CONTROL_REPRODUCES_OI_DOMINANCE"
VERDICT_REJECTED_ANCHOR = "REJECTED_ANCHOR_FAIL"
VERDICT_REJECTED_NEIGHBOUR = "REJECTED_NEIGHBOUR_SIGN_FLIP"
VERDICT_FALSIFIED_REGIME = "FALSIFIED_SINGLE_REGIME_ARTIFACT"

#: The control is never promotable, whatever its own result.
CONTROL_NEVER_PROMOTABLE = True

REQUIRED_FOLDS_POSITIVE = 2
MAX_FOLD_POSITIVE_SHARE = 0.50


def headline_gate(
    *,
    expectancy: float,
    position_pf: float,
    fold_positive: Sequence[bool],
) -> dict[str, Any]:
    """One arm's headline gates {expectancy > 0, PF >= 1.10, >= 2/3 folds}."""
    signs = [bool(v) for v in fold_positive]
    if len(signs) != int(MIN_FOLDS):
        raise ContractViolation(
            f"the frozen family has exactly {MIN_FOLDS} chronological folds; "
            f"got {len(signs)} fold signs"
        )
    n_positive = sum(1 for v in signs if v)
    e = float(expectancy)
    pf = float(position_pf)
    passed = bool(e > 0.0 and pf >= 1.10 and n_positive >= REQUIRED_FOLDS_POSITIVE)
    return {
        "schema": GATE_SCHEMA,
        "rule": HEADLINE_GATE_RULE,
        "expectancy": e,
        "expectancy_pass": bool(e > 0.0),
        "position_pf": pf,
        "position_pf_pass": bool(pf >= 1.10),
        "fold_positive": signs,
        "n_folds": len(signs),
        "n_positive": int(n_positive),
        "required_positive": int(REQUIRED_FOLDS_POSITIVE),
        "folds_pass": bool(n_positive >= REQUIRED_FOLDS_POSITIVE),
        "passed": passed,
    }


def incremental_context_gate(
    *,
    excess_bh_fold_positive: Sequence[bool],
    excess_beta_fold_positive: Sequence[bool],
) -> dict[str, Any]:
    """The decisive incremental gate (OICYC.md section 7, unrelaxed)."""
    bh = [bool(v) for v in excess_bh_fold_positive]
    beta = [bool(v) for v in excess_beta_fold_positive]
    for name, signs in (("buy_and_hold", bh), ("beta_context", beta)):
        if len(signs) != int(MIN_FOLDS):
            raise ContractViolation(
                f"the frozen family has exactly {MIN_FOLDS} chronological "
                f"folds; got {len(signs)} {name} fold signs"
            )
    bh_pos = sum(1 for v in bh if v)
    beta_pos = sum(1 for v in beta if v)
    return {
        "schema": GATE_SCHEMA,
        "rule": INCREMENTAL_GATE_RULE,
        "excess_bh_fold_positive": bh,
        "excess_bh_positive_folds": int(bh_pos),
        "excess_beta_fold_positive": beta,
        "excess_beta_positive_folds": int(beta_pos),
        "required_positive": int(REQUIRED_FOLDS_POSITIVE),
        "passed": bool(
            bh_pos >= REQUIRED_FOLDS_POSITIVE
            and beta_pos >= REQUIRED_FOLDS_POSITIVE
        ),
    }


def fold_concentration_check(
    *, largest_fold_positive_share: float
) -> dict[str, Any]:
    """The single-regime falsifier (largest fold-positive share <= 50%)."""
    share = float(largest_fold_positive_share)
    if not 0.0 <= share <= 1.0:
        raise ContractViolation(
            f"largest_fold_positive_share must be within [0, 1]; got {share}"
        )
    return {
        "schema": GATE_SCHEMA,
        "rule": CONCENTRATION_RULE,
        "largest_fold_positive_share": share,
        "max_allowed": MAX_FOLD_POSITIVE_SHARE,
        "passed": bool(share <= MAX_FOLD_POSITIVE_SHARE),
    }


def evaluate_family_gate(
    *,
    anchor_headline: dict[str, Any],
    control_headline: dict[str, Any],
    neighbour_headline: dict[str, Any],
    anchor_incremental: dict[str, Any],
    anchor_fold_concentration: dict[str, Any],
) -> dict[str, Any]:
    """The preregistered family verdict over the frozen gate set.

    Rule order (first hit wins, exactly as preregistered in OICYC.md
    section 9's failure table):

    1. anchor headline gates fail -> ``REJECTED_ANCHOR_FAIL`` (the
       cycle-participation discount is absent or sign-wrong after costs;
       no rescue, no window or parameter search);
    2. anchor passes but the incremental-context gate fails ->
       ``REJECTED_ANCHOR_FAIL`` (PRICE-beta repackaging is not incremental;
       positive raw PnL never overrides a failed context);
    3. anchor passes both but CTL-OISHARE passes all three headline gates
       too -> ``FALSIFIED_CONTROL_REPRODUCES_OI_DOMINANCE`` (the edge is an
       OI-dominance artifact; the control is never promotable);
    4. anchor passes, control fails, the neighbour does not support ->
       ``REJECTED_NEIGHBOUR_SIGN_FLIP`` (window-fragile slope estimate);
    5. anchor passes all of the above but the largest fold-positive share
       exceeds 50% -> ``FALSIFIED_SINGLE_REGIME_ARTIFACT``;
    6. otherwise -> ``FAMILY_ADVANCES_TO_STAGE_A`` (remaining Stage-A
       gates -- MDD <= 20%, symbol concentration <= 0.70, stress set,
       drop-one survival, benchmark excess, reproduction -- are evaluated
       by the scored layer).

    EVERY verdict carries the preregistered CONFIRMATORY status (plan
    Section 1.1) for the driver's verdict record and denominator.
    """
    for name, gate in (
        ("anchor_headline", anchor_headline),
        ("control_headline", control_headline),
        ("neighbour_headline", neighbour_headline),
        ("anchor_incremental", anchor_incremental),
        ("anchor_fold_concentration", anchor_fold_concentration),
    ):
        if not isinstance(gate, dict) or "passed" not in gate:
            raise ContractViolation(f"{name} must be a gate payload with 'passed'")

    anchor_ok = bool(anchor_headline["passed"])
    control_ok = bool(control_headline["passed"])
    neighbour_ok = bool(neighbour_headline["passed"])
    incremental_ok = bool(anchor_incremental["passed"])
    concentration_ok = bool(anchor_fold_concentration["passed"])

    if not anchor_ok:
        verdict = VERDICT_REJECTED_ANCHOR
        reason = (
            "anchor CYC-28D fails at least one headline gate {expectancy>0, "
            "PF>=1.10, >=2/3 folds positive}: the cycle-participation "
            "discount is absent or sign-wrong after costs (OICYC.md 9.1)"
        )
    elif not incremental_ok:
        verdict = VERDICT_REJECTED_ANCHOR
        reason = (
            "anchor passes the headline gates but the incremental-context "
            "gate fails: non-positive BTC buy-and-hold or BTC-beta excess "
            "in >= 2 folds is PRICE-beta repackaging, not positioning-cycle "
            "information (OICYC.md 9.3); positive raw PnL never overrides "
            "a failed incremental context"
        )
    elif control_ok:
        verdict = VERDICT_FALSIFIED_CONTROL
        reason = (
            "CTL-OISHARE passes all three headline gates while the anchor "
            "passes: the edge is an OI-dominance/size artifact and the "
            "co-movement information is redundant (OICYC.md 9.2); the "
            "control is never promotable"
        )
    elif not neighbour_ok:
        verdict = VERDICT_REJECTED_NEIGHBOUR
        reason = (
            "neighbour CYC-14D contradicts the anchor or is fold-unstable: "
            "the slope estimate is window-fragile (OICYC.md 9.4)"
        )
    elif not concentration_ok:
        verdict = VERDICT_FALSIFIED_REGIME
        reason = (
            "largest fold-positive share of PnL exceeds 50%: "
            "single-regime artifact (OICYC.md 9.5)"
        )
    else:
        verdict = VERDICT_FAMILY_ADVANCES
        reason = (
            "anchor passes the headline and incremental-context gates, "
            "CTL-OISHARE does not reproduce the anchor, the neighbour "
            "supports the sign, and the fold-positive concentration is "
            "inside the frozen bound"
        )
    return {
        "schema": GATE_SCHEMA,
        "anchor_arm": ANCHOR_ARM,
        "control_arm": CONTROL_ARM,
        "neighbour_arm": NEIGHBOUR_ARM,
        "anchor_headline": anchor_headline,
        "control_headline": control_headline,
        "neighbour_headline": neighbour_headline,
        "anchor_incremental": anchor_incremental,
        "anchor_fold_concentration": anchor_fold_concentration,
        "control_rule": CONTROL_RULE,
        "neighbour_rule": NEIGHBOUR_RULE,
        "incremental_rule": INCREMENTAL_GATE_RULE,
        "concentration_rule": CONCENTRATION_RULE,
        "control_never_promotable": CONTROL_NEVER_PROMOTABLE,
        "verdict": verdict,
        "reason": reason,
        "confirmatory_status": CONFIRMATORY,
        "section_1_1_disclosure": SECTION_1_1_DISCLOSURE,
        "denominator_note": (
            "every scored cell of this CONFIRMATORY family is counted in "
            "the observed/published denominator accounting with "
            "confirmatory status recorded in the verdict"
        ),
    }


__all__ = [
    "CONCENTRATION_RULE",
    "CONTROL_NEVER_PROMOTABLE",
    "CONTROL_RULE",
    "GATE_SCHEMA",
    "HEADLINE_GATE_RULE",
    "INCREMENTAL_GATE_RULE",
    "MAX_FOLD_POSITIVE_SHARE",
    "NEIGHBOUR_RULE",
    "REQUIRED_FOLDS_POSITIVE",
    "VERDICT_FALSIFIED_CONTROL",
    "VERDICT_FALSIFIED_REGIME",
    "VERDICT_FAMILY_ADVANCES",
    "VERDICT_REJECTED_ANCHOR",
    "VERDICT_REJECTED_NEIGHBOUR",
    "evaluate_family_gate",
    "fold_concentration_check",
    "headline_gate",
    "incremental_context_gate",
]
