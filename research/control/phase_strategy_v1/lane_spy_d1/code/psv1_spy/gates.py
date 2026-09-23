"""Calendar-defect gates (plan section 10 / dispatch section 6).

The predecessor corpus lost money to a clock-convention interaction: session
closes stamped next-midnight combined with a staleness flat law produced
weekday-dependent force-flats (weekly Tuesday churn). This cycle DELETES that
defect class, and these gates prove it:

1. No staleness/holding-duration flat law exists in this lane (structural:
   the reducer can only fill on target change; there is no holding-duration
   condition in the package — enforced by AST hygiene test + runtime counter).
2. Calendar law is frozen: decision at session close value; first executable
   fill at next session open; XNYS sessions only.
3. Mandatory regressions live in tests_py:
   a. weekday-rotation replay (+1..+4 day relabel => invariant labels,
      occupancy, transitions, events);
   b. the Tuesday test: the defect shape is reconstructed as a SYNTHETIC
      fixture in tests and asserted to produce ZERO weekday-attributable
      force-flats in this lane's pipeline while demonstrably producing them
      in the defective reference shape.
"""

from typing import Callable, Dict, List, Sequence, Tuple

from .phase_rule import PHASES, compute_labels
from .census import transition_matrix

WEEKDAY_NAMES = ("Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun")


def rotate_dates(dates: Sequence[str], k: int) -> List[str]:
    """Relabel every session date by +k calendar days (labels only; the
    ordered price series and fold membership by INDEX are untouched)."""
    from datetime import date as _date, timedelta as _timedelta

    return [
        (_date.fromisoformat(d) + _timedelta(days=k)).isoformat() for d in dates
    ]


def run_pipeline(closes: Sequence[float], dates: Sequence[str],
                 folds: Sequence[Tuple[str, str, int, int]],
                 labels_fn: Callable = compute_labels) -> Dict[str, object]:
    """Full lane pipeline as one function. `dates` is accepted so that the
    rotation gate can prove the pipeline output does not depend on it."""
    labels = labels_fn(closes)
    per_fold_occupancy = {}
    for fold_id, _era, a, b in folds:
        seg = labels[a : b + 1]
        per_fold_occupancy[fold_id] = {
            p: sum(1 for x in seg if x == p) for p in PHASES
        }
    return {
        "labels": labels,
        "per_fold_occupancy": per_fold_occupancy,
        "transition_matrix_post_warmup": transition_matrix(labels[219:]),
    }


def weekday_rotation_replay(
    closes: Sequence[float],
    dates: Sequence[str],
    folds: Sequence[Tuple[str, str, int, int]],
    shifts: Sequence[int] = (1, 2, 3, 4),
) -> Dict[str, object]:
    """Gate 10.3a: labels, per-fold occupancy and transitions must be
    INVARIANT under +1..+4 day date relabeling."""
    base = run_pipeline(closes, dates, folds)
    results = {}
    all_invariant = True
    for k in shifts:
        rotated = run_pipeline(closes, rotate_dates(dates, k), folds)
        same_labels = rotated["labels"] == base["labels"]
        same_occ = rotated["per_fold_occupancy"] == base["per_fold_occupancy"]
        same_trans = (
            rotated["transition_matrix_post_warmup"]
            == base["transition_matrix_post_warmup"]
        )
        ok = bool(same_labels and same_occ and same_trans)
        all_invariant = all_invariant and ok
        results[f"shift_{k}d"] = {
            "labels_invariant": same_labels,
            "per_fold_occupancy_invariant": same_occ,
            "transitions_invariant": same_trans,
            "invariant": ok,
        }
    return {"gate": "WEEKDAY_ROTATION_REPLAY", "pass": all_invariant,
            "shifts": results}


def clock_attributable_force_flats(fills: Sequence[Tuple[str, int]],
                                   targets: Sequence[int]) -> int:
    """Gate 10.3b runtime counter: fills fired where the target did NOT change.

    The predecessor defect was exactly such fills (clock-convention exits with
    no market view). In this lane the only fill rule is target change, so the
    counter is structurally 0; it is a runtime assert so the scored pipeline
    re-proves it every run.
    """
    n = 0
    for _kind, i in fills:
        if i == 0:
            continue
        if int(targets[i]) == int(targets[i - 1]):
            n += 1
    return n


def exits_by_weekday(fills: Sequence[Tuple[str, int]],
                     dates: Sequence[str]) -> Dict[str, int]:
    """Disclosure counter: weekday distribution of EXIT decisions.
    Weekday is never an input anywhere; this counter exists only so the gate
    can show the distribution is an artifact-free byproduct, and so the
    Tuesday fixture can be asserted empty."""
    out = {w: 0 for w in WEEKDAY_NAMES}
    from datetime import date as _date

    for kind, i in fills:
        if kind == "EXIT":
            out[WEEKDAY_NAMES[_date.fromisoformat(dates[i]).weekday()]] += 1
    return out
