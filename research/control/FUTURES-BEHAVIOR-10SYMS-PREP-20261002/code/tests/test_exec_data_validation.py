"""EXEC-FIX review-extra: finite-OHLC validation at engine chain build.

Bar.validate (rawdata) only checks h >= l — an open/close OUTSIDE
[l,h] passes (e.g. o=105 with h=101/l=99). On base eae8c3d2 the engine
accepted such bars and evaluated barriers/MAE/MFE against impossible
extrema. Law after fix: every bar the engine can execute or mark against
(chain bars AND per-conid bars used for deferred rolls / held contracts)
is validated at construction: all OHLCV finite, h >= l, and o, c within
[l, h]; violations raise PolicyError before any replay step.
"""
import datetime as dt
import math
import unittest

from futbt.calendarx import WeekdayCalendar
from futbt.costs import CostBook
from futbt.engine import BacktestEngine, EngineConfig
from futbt.roll import RollEngine
from futbt.taxonomy import PolicyError

from .helpers import make_bar, make_contract
from .test_engine import es_engine, es_universe


def two_contract_engine(bars_a, bars_b):
    cal = WeekdayCalendar(dt.date(2026, 1, 1), dt.date(2026, 6, 30))
    a = make_contract("ES", "ESH6", 101, dt.date(2026, 3, 18), bars_a)
    b = make_contract("ES", "ESM6", 102, dt.date(2026, 6, 18), bars_b)
    re = RollEngine("ES", [a, b], cal)
    return BacktestEngine("ES", re, re.build_roll_table(),
                          CostBook.for_symbol("ES"), EngineConfig())


def staircase_bars():
    cal = WeekdayCalendar(dt.date(2026, 1, 1), dt.date(2026, 2, 28))
    out = []
    for i, s in enumerate(cal.sessions()):
        px = 5000.0 + 3.0 * i
        out.append(make_bar(s, px, px + 5, px - 5, px, v=1000))
    return out


class TestFiniteOHLCValidation(unittest.TestCase):
    def test_open_above_high_rejected(self):
        bars = staircase_bars()
        victim = bars[10].t
        bars[10] = make_bar(victim, 5010.0, 5009.0, 4995.0, 5000.0, v=1000)
        with self.assertRaisesRegex(PolicyError, "outside"):
            two_contract_engine(bars, staircase_bars())

    def test_close_below_low_rejected(self):
        bars = staircase_bars()
        victim = bars[10].t
        bars[10] = make_bar(victim, 5000.0, 5005.0, 4995.0, 4990.0, v=1000)
        with self.assertRaisesRegex(PolicyError, "outside"):
            two_contract_engine(bars, staircase_bars())

    def test_non_finite_price_rejected(self):
        bars = staircase_bars()
        victim = bars[10].t
        bars[10] = make_bar(victim, float("nan"), 5005.0, 4995.0, 5000.0,
                            v=1000)
        with self.assertRaisesRegex(PolicyError, "finite"):
            two_contract_engine(bars, staircase_bars())

    def test_infinite_price_rejected(self):
        bars = staircase_bars()
        victim = bars[10].t
        bars[10] = make_bar(victim, 5000.0, float("inf"), 4995.0, 5000.0,
                            v=1000)
        with self.assertRaisesRegex(PolicyError, "finite"):
            two_contract_engine(bars, staircase_bars())

    def test_non_contract_chain_bar_also_validated(self):
        """Bars of NON-front contracts are used for deferred rolls and
        held-contract marks — they must be validated too."""
        bars = staircase_bars()
        b_bars = staircase_bars()
        victim = b_bars[40].t
        b_bars[40] = make_bar(victim, 5120.0, 5110.0, 5095.0, 5100.0,
                              v=1000)
        with self.assertRaisesRegex(PolicyError, "outside"):
            two_contract_engine(staircase_bars(), b_bars)

    def test_valid_chain_accepted(self):
        # sanity: the standard fixture (and any valid OHLC) still builds
        cal, cons = es_universe()
        eng = es_engine(cons, cal)
        self.assertTrue(eng.sessions)


if __name__ == "__main__":
    unittest.main()
