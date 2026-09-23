"""Nested walk-forward selection law (plan §5; mirrored by A6 freeze).

For each cell, each outer fold k in {1..4}, each regime R with asset-eligible
specialists:
- inner-train set = folds 1..k-1 (expanding window);
- fold 1 (empty inner) -> FLAT for every selectable regime;
- inner floors (pooled over inner folds): >= INNER_EPISODE_FLOOR (5)
  episodes AND >= INNER_DECISION_FLOOR (150) eligible decisions for R;
  below -> FLAT for R in fold k;
- exactly one eligible specialist: take it iff floors met, else FLAT;
- two eligible: pick higher inner pooled NET (base-tier costs, inside
  R-windows only) iff strictly higher (>1e-9) AND stable: higher on every
  inner fold where both have >=1 episode when inner folds <= 2, else on
  >= 2/3 of such folds; tie/instability/floor-failure -> FLAT;
- tie-break (exact numeric tie only): FLAT > BTC-only-short > long-capable.

The selection runs ONLY inside the GO-gated scored run (arm C
construction); inner NETs are computed on inner folds only; the outer fold
is scored once and never retuned. Total search is bounded by construction:
<= 2 specialists/regime x 4 regimes x 3 cells.
"""

from __future__ import annotations

from dataclasses import dataclass

INNER_EPISODE_FLOOR = 5
INNER_DECISION_FLOOR = 150
NET_EPS = 1e-9
TIE_BREAK_ORDER = {"FLAT": 0, "BTC_ONLY_SHORT": 1, "LONG_CAPABLE": 2}

SELECTION_SCHEMA = "rsmv1_selection_law@1"


@dataclass
class SpecialistCandidate:
    specialist_id: str
    tie_break_class: str  # FLAT | BTC_ONLY_SHORT | LONG_CAPABLE
    inner_pooled_net: float
    inner_fold_nets: dict[int, float]  # fold_id -> net (only folds w/ episode)


@dataclass
class SelectionOutcome:
    regime: str
    fold_id: int
    selected: str  # specialist id or "FLAT"
    reason: str
    inner_episodes: int
    inner_eligible_decisions: int
    floor_ok: bool


def select_for_fold(
    regime: str,
    fold_id: int,
    candidates: list[SpecialistCandidate],
    inner_episodes: int,
    inner_eligible_decisions: int,
    inner_fold_count: int,
) -> SelectionOutcome:
    """Apply the frozen law for one (regime, outer fold)."""
    floor_ok = (
        inner_episodes >= INNER_EPISODE_FLOOR
        and inner_eligible_decisions >= INNER_DECISION_FLOOR
    )
    if fold_id == 1:
        return SelectionOutcome(regime, fold_id, "FLAT",
                                "fold1_empty_inner_default", inner_episodes,
                                inner_eligible_decisions, floor_ok)
    if not floor_ok:
        return SelectionOutcome(regime, fold_id, "FLAT",
                                "inner_floor_failure", inner_episodes,
                                inner_eligible_decisions, floor_ok)
    live = [c for c in candidates if c.specialist_id != "FLAT"]
    if not live:
        return SelectionOutcome(regime, fold_id, "FLAT",
                                "no_asset_eligible_specialist",
                                inner_episodes, inner_eligible_decisions,
                                floor_ok)
    if len(live) == 1:
        return SelectionOutcome(regime, fold_id, live[0].specialist_id,
                                "single_eligible_specialist",
                                inner_episodes, inner_eligible_decisions,
                                floor_ok)
    a, b = sorted(live, key=lambda c: -c.inner_pooled_net)[:2]
    if abs(a.inner_pooled_net - b.inner_pooled_net) <= NET_EPS:
        winner = min([a, b], key=lambda c: TIE_BREAK_ORDER.get(c.tie_break_class, 9))
        return SelectionOutcome(regime, fold_id, winner.specialist_id,
                                "exact_tie_tiebreak", inner_episodes,
                                inner_eligible_decisions, floor_ok)
    folds_both = [f for f in a.inner_fold_nets if f in b.inner_fold_nets]
    wins_a = sum(1 for f in folds_both
                 if a.inner_fold_nets[f] > b.inner_fold_nets[f])
    need = len(folds_both) if inner_fold_count <= 2 else max(
        1, -(-2 * len(folds_both) // 3))
    stable = wins_a >= need and len(folds_both) > 0
    if stable:
        return SelectionOutcome(regime, fold_id, a.specialist_id,
                                "inner_net_higher_stable", inner_episodes,
                                inner_eligible_decisions, floor_ok)
    return SelectionOutcome(regime, fold_id, "FLAT",
                            "inner_evidence_unstable", inner_episodes,
                            inner_eligible_decisions, floor_ok)
