"""Z5/A8 conftest — offline, synthetic, hand-computed fixtures for family_a5.

Import contract: ``research/stocks_free_v2/__init__.py`` and
``tests/stocks_free_v2/__init__.py`` are owned by A6 and are NOT created by
this lane, so the family_a5 modules are loaded here via importlib/sys.path
(file-path loading with a package-import fallback).  No real-data IO, no
network, no keys: every TR/raw series below is synthetic.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
FAMILY_DIR = REPO_ROOT / "research" / "stocks_free_v2" / "family_a5"

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
if str(FAMILY_DIR) not in sys.path:
    sys.path.insert(0, str(FAMILY_DIR))

_SPEC_NAMES = ("signals", "portfolio", "schedule")


def _load_module(name: str):
    """Load a family_a5 module by file path (A6 owns the package __init__s)."""
    if name in sys.modules:
        return sys.modules[name]
    try:  # package import when the namespace resolves (post-integration)
        return importlib.import_module(f"research.stocks_free_v2.family_a5.{name}")
    except ImportError:
        spec = importlib.util.spec_from_file_location(name, FAMILY_DIR / f"{name}.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
        return module


signals = _load_module("signals")
portfolio = _load_module("portfolio")
schedule = _load_module("schedule")


class SyntheticCalendar:
    """Duck-typed stand-in for the frozen calendar over an injected session list.

    Only ``next_session(after)`` is consumed by the engine (the one-event-delay
    fill resolver); it fails closed past the end of the list, like the frozen
    table fails closed past its horizon.
    """

    def __init__(self, sessions):
        self.sessions = list(sessions)
        self._index = {d: i for i, d in enumerate(self.sessions)}

    class _Session:
        def __init__(self, day: date):
            self.start_utc = datetime(day.year, day.month, day.day)
            self.day = day

    def next_session(self, after: date):
        idx = self._index.get(after)
        start = 0 if idx is None else idx + 1
        for day in self.sessions[start:]:
            if day > after:
                return self._Session(day)
        raise ValueError(f"no session after {after.isoformat()} in synthetic calendar")


def make_sessions(start: date, count: int) -> list:
    """``count`` consecutive weekday sessions from ``start`` (weekends skipped).

    Deliberately holiday-free: the synthetic clock arithmetic in the tests is
    hand-computed on pure business days.
    """
    sessions = []
    day = start
    while len(sessions) < count:
        if day.weekday() < 5:
            sessions.append(day)
        day = day + timedelta(days=1)
    return sessions


def geo_tr_series(sessions, base: float = 100.0, daily: float = 1.01) -> dict:
    """Constant daily simple return ``daily`` -> realized vol == 0 (ddof=1)."""
    value = base
    out = {}
    for d in sessions:
        out[d] = value
        value = value * daily
    return out


@pytest.fixture(scope="session")
def a5():
    """The family_a5 modules plus shared synthetic-fixture helpers."""
    return SimpleNamespace(
        signals=signals,
        portfolio=portfolio,
        schedule=schedule,
        SyntheticCalendar=SyntheticCalendar,
        make_sessions=make_sessions,
        geo_tr_series=geo_tr_series,
        repo_root=REPO_ROOT,
    )


@pytest.fixture(scope="session")
def real_calendar():
    """The frozen US_EQUITY_REGULAR_V1 calendar, imported READ-ONLY (A4 owns it)."""
    from research.assets.stocks.calendar import USEquityRegularCalendar

    return USEquityRegularCalendar()
