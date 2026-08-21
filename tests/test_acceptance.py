from __future__ import annotations

from unittest import TestCase

import pandas as pd

from research.acceptance import evaluate_combo_cells
from research.acceptance import valid_ema_combo


def _cell(symbol: str, window: int, expectancy: float, profit_factor: float) -> dict:
    return {
        "symbol": symbol,
        "window": window,
        "expectancy": expectancy,
        "profit_factor": profit_factor,
        "trades": 10,
    }


class AcceptanceTests(TestCase):
    def test_fails_when_one_symbol_is_negative(self) -> None:
        df = pd.DataFrame(
            [
                _cell("BTCUSDT", 0, 0.2, 1.2),
                _cell("BTCUSDT", 1, 0.2, 1.2),
                _cell("BTCUSDT", 2, 0.2, 1.2),
                _cell("ETHUSDT", 0, -0.2, 0.8),
                _cell("ETHUSDT", 1, -0.2, 0.8),
                _cell("ETHUSDT", 2, -0.2, 0.8),
            ],
        )
        result = evaluate_combo_cells(df)
        self.assertFalse(result.all_symbols_positive)
        self.assertFalse(result.meets_acceptance)

    def test_passes_notes_criteria(self) -> None:
        df = pd.DataFrame(
            [
                _cell("BTCUSDT", 0, 0.2, 1.2),
                _cell("BTCUSDT", 1, 0.1, 1.15),
                _cell("BTCUSDT", 2, 0.05, 1.12),
                _cell("ETHUSDT", 0, 0.3, 1.3),
                _cell("ETHUSDT", 1, 0.2, 1.2),
                _cell("ETHUSDT", 2, 0.1, 1.11),
            ],
        )
        result = evaluate_combo_cells(df)
        self.assertEqual(result.positive_folds, "3/3")
        self.assertTrue(result.all_symbols_positive)
        self.assertTrue(result.majority_pf_above_threshold)
        self.assertTrue(result.meets_acceptance)

    def test_ema_grid_skips_invalid_periods(self) -> None:
        self.assertTrue(valid_ema_combo({"fast_ema_period": 10, "slow_ema_period": 40}))
        self.assertFalse(valid_ema_combo({"fast_ema_period": 50, "slow_ema_period": 40, "trend_ema_period": 200}))
