from __future__ import annotations

from unittest import TestCase

from config.settings import MarkdownBreakdownSettings
from config.settings import ReclaimMeanReversionSettings
from config.settings import STRATEGY_TYPES
from config.settings import TrendPullbackSettings


class BaselineSettingsTests(TestCase):
    def test_baseline_strategy_types_are_registered(self) -> None:
        self.assertIn("reclaim_mr", STRATEGY_TYPES)
        self.assertIn("trend_pullback", STRATEGY_TYPES)
        self.assertIn("markdown_breakdown", STRATEGY_TYPES)

    def test_frozen_baseline_defaults_validate(self) -> None:
        ReclaimMeanReversionSettings().validate()
        TrendPullbackSettings().validate()
        MarkdownBreakdownSettings().validate()

    def test_reclaim_rejects_inverted_rsi_levels(self) -> None:
        with self.assertRaises(ValueError):
            ReclaimMeanReversionSettings(
                rsi_oversold=90.0,
                rsi_overbought=10.0,
            ).validate()

    def test_pullback_rejects_invalid_ema_order(self) -> None:
        with self.assertRaises(ValueError):
            TrendPullbackSettings(
                fast_ema_period=50,
                slow_ema_period=20,
            ).validate()
