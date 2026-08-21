from __future__ import annotations

from unittest import TestCase

from regime import AverageDirectionalIndex
from regime import HtfTrendTracker
from regime import VolumeSMA
from regime import is_ranging


class RegimeFilterTests(TestCase):
    def test_ranging_requires_all_three_filters(self) -> None:
        kwargs = dict(
            vhf=0.20,
            vhf_max=0.35,
            adx=15.0,
            adx_max=25.0,
            volume=100.0,
            volume_sma=100.0,
            volume_max_ratio=1.5,
        )
        self.assertTrue(is_ranging(**kwargs))
        self.assertFalse(is_ranging(**{**kwargs, "vhf": 0.50}))
        self.assertFalse(is_ranging(**{**kwargs, "adx": 40.0}))
        self.assertFalse(is_ranging(**{**kwargs, "volume": 200.0}))

    def test_volume_sma_warms_up(self) -> None:
        sma = VolumeSMA(period=3)
        sma.update(10)
        sma.update(20)
        self.assertFalse(sma.initialized)
        sma.update(30)
        self.assertTrue(sma.initialized)
        self.assertEqual(sma.value, 20.0)

    def test_adx_initializes_after_wilder_warmup(self) -> None:
        adx = AverageDirectionalIndex(period=5)
        price = 100.0
        for i in range(20):
            # Mild directional drift so TR / DM are non-zero.
            high = price + 1.0 + (0.2 * i)
            low = price - 0.5
            close = price + 0.3
            adx.update(high=high, low=low, close=close)
            price = close
        self.assertTrue(adx.initialized)
        self.assertGreater(adx.value, 0.0)
        self.assertLessEqual(adx.value, 100.0)


class HtfTrendFilterTests(TestCase):
    def test_blocks_long_below_ema_and_short_above(self) -> None:
        htf = HtfTrendTracker(base_minutes=15, htf_minutes=60, ema_period=3)
        # Warm up with rising prices → EMA below last close
        for px in [100, 101, 102, 103, 104, 105, 106, 107, 108, 109, 110, 111]:
            for _ in range(4):
                htf.update(px)
        self.assertTrue(htf.initialized)
        self.assertTrue(htf.allows_long())
        self.assertFalse(htf.allows_short())

        htf.reset()
        for px in [200, 199, 198, 197, 196, 195, 194, 193, 192, 191, 190, 189]:
            for _ in range(4):
                htf.update(px)
        self.assertFalse(htf.allows_long())
        self.assertTrue(htf.allows_short())
