"""Shared test helpers: fixture universe caching + in-memory contract builder
+ scripted strategies. Offline only — every test uses synthetic data."""
from __future__ import annotations

import datetime as dt
import tempfile
import unittest
from pathlib import Path

from futbt.calendarx import WeekdayCalendar
from futbt.engine import Decision
from futbt.rawdata import Bar, ContractData, ContractIdentity, load_contract_directory
from futbt.synth import build_universe

FIXTURE_SEED = 20261002


class FixtureTestCase(unittest.TestCase):
    """Builds the deterministic synthetic universe once per class into a
    temp dir; loads it through the real raw adapter."""

    _tmp: tempfile.TemporaryDirectory | None = None
    _uni = None
    _contracts = None

    @classmethod
    def setUpClass(cls):
        cls._tmp = tempfile.TemporaryDirectory(prefix="futbt_fix_")
        cls._uni = build_universe(cls._tmp.name, seed=FIXTURE_SEED)
        cls._contracts = load_contract_directory(cls._tmp.name)

    @classmethod
    def tearDownClass(cls):
        cls._tmp.cleanup()
        cls._uni = None
        cls._contracts = None

    @property
    def uni(self):
        return self._uni

    @property
    def contracts(self):
        return self._contracts


def make_bar(d: dt.date, o: float, h: float, l: float, c: float,
             v: float = 100.0) -> Bar:
    b = Bar(t=d, t_raw=d.isoformat(), t_iso=None, o=o, h=h, l=l, c=c,
            v=v, wap=c, n=v)
    return b.validate()


def flat_bar(d: dt.date, c: float, v: float = 100.0) -> Bar:
    return make_bar(d, c, c, c, c, v=v)


def close_only_bar(d: dt.date, c: float) -> Bar:
    return make_bar(d, c, c, c, c, v=0)


def make_contract(symbol: str, local_symbol: str, conid: int,
                  last_trade_date: dt.date, bars: list[Bar]) -> ContractData:
    ident = ContractIdentity(symbol=symbol, local_symbol=local_symbol,
                             conid=conid, last_trade_date=last_trade_date)
    return ContractData(identity=ident, daily_trades=list(bars))


def weekday_cal(start: dt.date, end: dt.date) -> WeekdayCalendar:
    return WeekdayCalendar(start, end)


class ScriptedStrategy:
    """Strategy whose decisions are scripted per session date; records every
    context it was called with (for PIT-abuse tests)."""

    def __init__(self, script: dict[dt.date, Decision]):
        self.script = script
        self.calls: list[dt.date] = []
        self.abuse_at: dt.date | None = None  # if set, read next session

    def __call__(self, ctx):
        self.calls.append(ctx.asof)
        if self.abuse_at is not None and ctx.asof == self.abuse_at:
            nxt = ctx.asof + dt.timedelta(days=1)
            ctx.view.close(nxt)  # deliberate future access
        d = self.script.get(ctx.asof)
        return d if d is not None else Decision(action="none")
