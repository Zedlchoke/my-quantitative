"""Walk-forward acceptance criteria from NOTES.md §7 bước 3.

A parameter combo may be *promoted* as a default only when all of these hold:

1. Expectancy is positive on at least two-thirds of *folds*.
2. Expectancy is positive on every traded symbol (or use a per-symbol config).
3. Profit factor > 1.1 on a majority of (symbol, fold) cells.
4. Repeatable on a different data window — approximated here by walk-forward
   folds; a true extra OOS set is still a manual check.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

MIN_POSITIVE_FOLD_RATIO = 2.0 / 3.0
MIN_PROFIT_FACTOR = 1.1


def valid_ema_combo(params: dict) -> bool:
    """Reject EMA period triples that violate fast < slow < trend."""
    fast = params.get("fast_ema_period")
    slow = params.get("slow_ema_period")
    trend = params.get("trend_ema_period", 200)
    if fast is None or slow is None:
        return True
    return fast < slow < trend


@dataclass(frozen=True)
class AcceptanceResult:
    positive_fold_ratio: float
    all_symbols_positive: bool
    majority_pf_above_threshold: bool
    meets_acceptance: bool
    positive_folds: str
    pf_majority: str


def evaluate_combo_cells(group: pd.DataFrame) -> AcceptanceResult:
    """Evaluate NOTES.md acceptance on one combo's (symbol, window) cells."""
    fold_exp = group.groupby("window")["expectancy"].mean()
    n_folds = max(len(fold_exp), 1)
    n_pos_folds = int((fold_exp > 0).sum())
    positive_fold_ratio = n_pos_folds / n_folds

    symbol_exp = group.groupby("symbol")["expectancy"].mean()
    all_symbols_positive = bool(len(symbol_exp) > 0 and (symbol_exp > 0).all())

    n_cells = len(group)
    n_pf = int((group["profit_factor"] > MIN_PROFIT_FACTOR).sum())
    majority_pf = n_pf > (n_cells / 2.0) if n_cells else False

    meets = (
        positive_fold_ratio >= MIN_POSITIVE_FOLD_RATIO
        and all_symbols_positive
        and majority_pf
    )
    return AcceptanceResult(
        positive_fold_ratio=positive_fold_ratio,
        all_symbols_positive=all_symbols_positive,
        majority_pf_above_threshold=majority_pf,
        meets_acceptance=meets,
        positive_folds=f"{n_pos_folds}/{n_folds}",
        pf_majority=f"{n_pf}/{n_cells}",
    )
