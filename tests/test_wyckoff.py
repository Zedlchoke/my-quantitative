from __future__ import annotations

from unittest import TestCase

from regime_wyckoff import WyckoffPhase
from regime_wyckoff import classify_wyckoff_row
from regime_wyckoff import wyckoff_allows_entries
from regime_wyckoff import wyckoff_allows_long
from regime_wyckoff import wyckoff_allows_short
from regime_wyckoff import wyckoff_risk_scale


class WyckoffClassifierTests(TestCase):
    def test_markdown_priority_over_accumulation(self) -> None:
        phase = classify_wyckoff_row(
            close=100.0,
            ema_fast=110.0,
            ema_slow=120.0,
            return_pct=-10.0,
            range_position=0.10,
            adx=18.0,
        )
        self.assertEqual(phase, WyckoffPhase.MARKDOWN)

    def test_markup_detected(self) -> None:
        phase = classify_wyckoff_row(
            close=200.0,
            ema_fast=190.0,
            ema_slow=170.0,
            return_pct=12.0,
            range_position=0.90,
            adx=30.0,
        )
        self.assertEqual(phase, WyckoffPhase.MARKUP)

    def test_accumulation_at_range_low(self) -> None:
        phase = classify_wyckoff_row(
            close=100.0,
            ema_fast=102.0,
            ema_slow=105.0,
            return_pct=-2.0,
            range_position=0.20,
            adx=18.0,
        )
        self.assertEqual(phase, WyckoffPhase.ACCUMULATION)

    def test_distribution_at_range_high(self) -> None:
        phase = classify_wyckoff_row(
            close=200.0,
            ema_fast=198.0,
            ema_slow=190.0,
            return_pct=2.0,
            range_position=0.80,
            adx=20.0,
        )
        self.assertEqual(phase, WyckoffPhase.DISTRIBUTION)

    def test_transition_when_unclear(self) -> None:
        phase = classify_wyckoff_row(
            close=150.0,
            ema_fast=148.0,
            ema_slow=145.0,
            return_pct=3.0,
            range_position=0.50,
            adx=22.0,
        )
        self.assertEqual(phase, WyckoffPhase.TRANSITION)

    def test_gate_blocks_markdown(self) -> None:
        self.assertFalse(wyckoff_allows_entries(WyckoffPhase.MARKDOWN))
        self.assertTrue(wyckoff_allows_entries(WyckoffPhase.TRANSITION))
        self.assertEqual(wyckoff_risk_scale(WyckoffPhase.TRANSITION), 0.5)
        self.assertEqual(wyckoff_risk_scale(WyckoffPhase.MARKDOWN), 0.0)

    def test_directional_bias_distribution_short_only(self) -> None:
        self.assertFalse(wyckoff_allows_long(WyckoffPhase.DISTRIBUTION))
        self.assertTrue(wyckoff_allows_short(WyckoffPhase.DISTRIBUTION))

    def test_directional_bias_accumulation_long_only(self) -> None:
        self.assertTrue(wyckoff_allows_long(WyckoffPhase.ACCUMULATION))
        self.assertFalse(wyckoff_allows_short(WyckoffPhase.ACCUMULATION))

    def test_directional_bias_markup_flat(self) -> None:
        self.assertFalse(wyckoff_allows_long(WyckoffPhase.MARKUP))
        self.assertFalse(wyckoff_allows_short(WyckoffPhase.MARKUP))

    def test_directional_bias_transition_both(self) -> None:
        self.assertTrue(wyckoff_allows_long(WyckoffPhase.TRANSITION))
        self.assertTrue(wyckoff_allows_short(WyckoffPhase.TRANSITION))
