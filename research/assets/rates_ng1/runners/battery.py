"""RATES-NG1 I-phase control battery: the declared + secondary
executioners, with Q-11 invalid-vs-null discipline.

Cycle RATES-NG1, task rates-ng1-i-implementation.  Implements the
freeze's section_6_control_battery_binding VERBATIM:

- LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL (MANDATORY, DECLARED_EXECUTIONER,
  V8 law adapted: falsification-by-control #14 FX-V8 / #15
  FOREX-NG1 CTL-DGS10LEVEL class): the same decomposition's LEVEL
  coordinate (10 Yr) traded on the identical grid with the identical
  leg-pair machinery, sign convention and cost treatment; the anchor
  arms trade only the orthogonalized shape residual.
- CLOCK_ONLY_SHADOW (SECONDARY_EXECUTIONER): the identical paired-leg
  machinery driven by a pure session-of-week clock with NO curve input
  (D2 frozen generic_dow_tue class: +1 on Tuesday decision sessions,
  0 otherwise).
- PLACEBO (SECONDARY_EXECUTIONER): the identical shape state evaluated
  with a FIXED k-session misalignment between state session and
  decision session; k_misalign_sessions = 5 := exactly one frozen
  holding period (frozen in the freeze; never tuned).

Kill semantics (the D1 falsification rule, declared before any
measurement): KILL if a killer control earns a STRICTLY GREATER
after-cost per-decision edge than the anchor arm on the identical
grid/window/cost treatment.  The comparator consumes per-decision
after-cost EDGE series (list aligned to the bookable instants; entries
may be None = UNDEFINED).  Q-11: alignment drops instants where EITHER
side is UNDEFINED and counts the drops -- never inferred as zero.

This module computes NO outcome numbers on real substrate anywhere in
I; the edge series it consumes exist only as synthetic fixtures in the
I tests.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from research.assets.rates_ng1.runners.runner import (
    K_MISALIGN_SESSIONS,
    misaligned_state,
)

SCHEMA = "rates_ng1/runners/battery@1"

#: The freeze's killer-control roles, in binding order.
KILLER_ROLES = ("LEVEL_VS_SHAPE_DECOMPOSITION_CONTROL",
                "CLOCK_ONLY_SHADOW",
                "PLACEBO")

#: Frozen placebo misalignment (section_6 of the freeze).
PLACEBO_K = K_MISALIGN_SESSIONS

FALSIFICATION_RULE_CITATION = (
    "D1 control_battery_spec + falsification_rule, sha-pinned in the "
    "selection freeze section_6_control_battery_binding.falsification_"
    "rule (declared before any measurement): KILL if the paired "
    "LEVEL-factor control earns a strictly greater after-cost "
    "per-decision edge than the orthogonalized-shape ANCHOR arm on the "
    "identical bookable grid and window under the identical frozen cost "
    "treatment; the clock-only shadow and the misaligned-state placebo "
    "carry the same out-earning kill semantics as secondary battery "
    "executioners.")


def placebo_state(state: Sequence[float | None],
                  k: int = PLACEBO_K) -> list[float | None]:
    """The misaligned-state placebo state series (runner machinery)."""
    return misaligned_state(state, k)


def align_defined_pairs(a: Sequence[float | None],
                        b: Sequence[float | None]) -> dict:
    """Q-11 alignment of two per-decision series: keep instants where
    BOTH sides are defined; count each side's UNDEFINED instants
    separately (invalid vs null DISTINCTLY, never inferred as zero)."""
    if len(a) != len(b):
        raise ValueError("series length mismatch")
    pairs_a: list[float] = []
    pairs_b: list[float] = []
    drop_a = drop_b = 0
    for va, vb in zip(a, b):
        if va is None and vb is None:
            drop_a += 1
            drop_b += 1
        elif va is None:
            drop_a += 1
        elif vb is None:
            drop_b += 1
        else:
            pairs_a.append(float(va))
            pairs_b.append(float(vb))
    return {
        "n_instants": len(a),
        "n_pairs_used": len(pairs_a),
        "dropped_undefined_side_a": drop_a,
        "dropped_undefined_side_b": drop_b,
        "pairs_a": pairs_a,
        "pairs_b": pairs_b,
    }


def _mean(vals: Sequence[float]) -> float | None:
    return sum(vals) / len(vals) if vals else None


def out_earning_kill(anchor_edges: Sequence[float | None],
                     control_edges: Sequence[float | None],
                     control_role: str) -> dict:
    """One executioner comparison (D1 falsification rule semantics).

    KILL iff the control's mean after-cost per-decision edge over the
    Q-11-aligned defined pairs is STRICTLY greater than the anchor's
    (a tie is NOT a kill; the law says 'strictly greater').  Structural
    comparator only -- the edges passed in I are synthetic fixtures."""
    if control_role not in KILLER_ROLES:
        raise ValueError(f"unknown killer control role {control_role!r}")
    al = align_defined_pairs(anchor_edges, control_edges)
    mean_a = _mean(al["pairs_a"])
    mean_c = _mean(al["pairs_b"])
    kill = (mean_a is not None and mean_c is not None
            and mean_c > mean_a)
    return {
        "schema": SCHEMA,
        "control_role": control_role,
        "n_instants": al["n_instants"],
        "n_pairs_used": al["n_pairs_used"],
        "dropped_undefined_anchor": al["dropped_undefined_side_a"],
        "dropped_undefined_control": al["dropped_undefined_side_b"],
        "anchor_mean_edge": mean_a,
        "control_mean_edge": mean_c,
        "margin_control_minus_anchor": (
            None if (mean_a is None or mean_c is None)
            else mean_c - mean_a),
        "kill": bool(kill),
        "kill_law": "strictly greater after-cost per-decision edge "
                    "(tie is not a kill)",
    }


def battery_verdict(anchor_edges: Sequence[float | None],
                    control_edges_by_role: Mapping[
                        str, Sequence[float | None]]) -> dict:
    """Full battery verdict for ONE anchor arm: the declared executioner
    (level-vs-shape) plus both secondary executioners; family_kill is
    the R2 CONTROL_KILL input (any killer control out-earning the
    anchor kills the family).  Missing roles are fail-closed."""
    roles = sorted(control_edges_by_role)
    if roles != sorted(KILLER_ROLES):
        raise ValueError(
            f"battery requires exactly the frozen killer roles "
            f"{sorted(KILLER_ROLES)}, got {roles}")
    rows = [out_earning_kill(anchor_edges, control_edges_by_role[role],
                             role) for role in KILLER_ROLES]
    family_kill = any(r["kill"] for r in rows)
    return {
        "schema": SCHEMA,
        "falsification_rule_citation": FALSIFICATION_RULE_CITATION,
        "k_misalign_sessions": PLACEBO_K,
        "comparisons": rows,
        "killed_by": [r["control_role"] for r in rows if r["kill"]],
        "family_kill": bool(family_kill),
        "q11_note": "UNDEFINED instants are dropped from the aligned "
                    "denominators and counted per side, never inferred "
                    "as zero",
    }
