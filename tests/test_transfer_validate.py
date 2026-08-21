from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from unittest import TestCase

from research.transfer_validate import assert_frozen


class TransferFrozenTests(TestCase):
    @dataclass
    class Params:
        atr_stop_multiple: float = 1.5
        take_profit_multiple: float = 2.0
        vhf_max: float = 0.25
        adx_max: float = 20.0
        volume_max_ratio: float = 1.8
        htf_trend_filter: bool = True
        htf_ema_period: int = 200
        htf_minutes: int = 60
        wyckoff_gate: bool = True
        wyckoff_directional_bias: bool = True

    def test_accepts_frozen_parameters(self) -> None:
        settings = SimpleNamespace(mean_reversion=self.Params())
        assert_frozen(settings)

    def test_rejects_parameter_drift(self) -> None:
        settings = SimpleNamespace(mean_reversion=self.Params(atr_stop_multiple=1.0))
        with self.assertRaises(ValueError):
            assert_frozen(settings)
