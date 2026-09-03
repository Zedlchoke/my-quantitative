"""Shared offline synthetic fixtures for the family_a4 test suite.

NO real market data, NO network, NO file IO beyond the frozen spec/config
artifacts inside the repo.  All price series are synthetic and hand-crafted
on the frozen ``US_EQUITY_REGULAR_V1`` calendar (imported read-only).
"""

from __future__ import annotations

import copy
import datetime as dt
import math

import pytest

from research.assets.stocks.calendar import US_EQUITY_REGULAR_V1
from research.stocks_free_v2.family_a4 import (
    FamilyInputs,
    PartitionSpec,
    load_frozen_spec,
)

CALENDAR = US_EQUITY_REGULAR_V1
COVERAGE_START = dt.date(2018, 1, 2)  # matches the frozen vendor coverage start


def calendar_sessions(count: int, start: dt.date = COVERAGE_START) -> tuple[str, ...]:
    """The first ``count`` frozen regular sessions from ``start`` (ISO)."""
    sessions: list[str] = []
    day = start
    while len(sessions) < count:
        if CALENDAR.is_session_day(day):
            sessions.append(day.isoformat())
        day += dt.timedelta(days=1)
    return tuple(sessions)


def full_s0_sessions() -> tuple[str, ...]:
    """All frozen regular sessions 2018-01-02 .. 2025-07-31 (2175 expected)."""
    sessions: list[str] = []
    day = COVERAGE_START
    end = dt.date(2025, 7, 31)
    while day <= end:
        if CALENDAR.is_session_day(day):
            sessions.append(day.isoformat())
        day += dt.timedelta(days=1)
    return tuple(sessions)


def jump_series(
    sessions: tuple[str, ...],
    jump_indices_by_symbol: dict[str, list[int]],
    jump_factor_by_symbol: dict[str, float],
    base: float = 100.0,
) -> dict[str, dict[str, float]]:
    """Piecewise-constant synthetic TR series: flat ``base`` with jumps.

    ``jump_indices_by_symbol[s]`` lists the session indices where the TR
    level of ``s`` multiplies by ``jump_factor_by_symbol[s]`` (one flat
    step per listed session).  A step between t-252 and t-21 therefore
    shows up in mom exactly once and in sigma as a single non-zero log
    return — fully hand-computable.
    """
    out: dict[str, dict[str, float]] = {}
    for symbol, indices in jump_indices_by_symbol.items():
        level = base
        series: dict[str, float] = {}
        factor = jump_factor_by_symbol[symbol]
        for index, day in enumerate(sessions):
            if index in set(indices):
                level *= factor
            series[day] = level
        out[symbol] = series
    return out


def wave_series(
    sessions: tuple[str, ...],
    symbols: list[str],
    drift_by_symbol=None,
    amp_by_symbol=None,
) -> dict[str, dict[str, float]]:
    """Deterministic non-degenerate TR series (sigma > 0 for every symbol).

    Daily multiplicative factor ``(1 + drift) * (1 +/- amp)`` alternating
    with session parity: strictly positive levels, non-zero sample vol in
    every window, distinct per symbol.  Used where only schedule invariants
    (not hand-computed scores) matter.
    """
    drift_by_symbol = drift_by_symbol or {}
    amp_by_symbol = amp_by_symbol or {}
    out: dict[str, dict[str, float]] = {}
    for j, symbol in enumerate(symbols):
        drift = drift_by_symbol.get(symbol, 0.0002 * (j + 1))
        amp = amp_by_symbol.get(symbol, 0.001 * (j + 1))
        level = 100.0
        series: dict[str, float] = {}
        for index, day in enumerate(sessions):
            sign = 1.0 if index % 2 == 0 else -1.0
            level *= (1.0 + drift) * (1.0 + sign * amp)
            series[day] = level
        out[symbol] = series
    return out


HAND_SYMBOLS = ["AAA", "BBB", "CCC", "DDD", "EEE"]
# Hand fixture (decision at session index 272 == 2019-01-31, the first
# session with the full 253-window [t-252, t] = [20, 272]):
#   - total growth c between t-252 (index 20) and t-21 (index 251) and the
#     number of equal log-jumps k per symbol (jump session indices below).
#   mom_i = c_i - 1 (exact by construction);
#   sigma_i = v_i * sqrt((231 - k_i) / (231 * k_i * 230)) with v_i = ln(c_i)
#     (sample std, ddof=1, of k_i jumps of v_i/k_i among 231 zero returns).
HAND_PLACEMENTS = {
    #  symbol: c, k, jump indices (all inside (20, 251])
    "AAA": (4.0, 4, [40, 90, 140, 190]),
    "BBB": (3.0, 2, [90, 190]),
    "CCC": (2.5, 2, [90, 190]),
    "DDD": (2.0, 8, [40, 70, 100, 130, 160, 190, 220, 250]),
    "EEE": (1.5, 4, [40, 90, 140, 190]),
}


def hand_spec() -> dict:
    """The frozen spec with the rankable cross-section swapped to the five
    synthetic hand symbols (everything else frozen-identical)."""
    spec = copy.deepcopy(load_frozen_spec())
    spec["cohort"]["rankable_cross_section_10"] = list(HAND_SYMBOLS)
    # one synthetic fold spanning the whole 300-session fixture, scored end
    # at session index 292 (2019-02-28) and terminal at index 299
    sessions = calendar_sessions(300)
    spec["warmup_folds_terminal"]["s0_folds"] = [
        {
            "fold_id": "SYN_FOLD_1",
            "start": sessions[63],      # 2018-04-04, mirrors the real warmup end
            "end": sessions[299],
            "scored_end": sessions[292],
            "purge_sessions": 5,
        }
    ]
    spec["warmup_folds_terminal"]["force_flat_events"] = [
        f"SYN_FOLD_1 scored_end {sessions[292]} close",
        f"S0 terminal {sessions[299]} close",
    ]
    return spec


def hand_partition(sessions: tuple[str, ...]) -> PartitionSpec:
    return PartitionSpec(
        warmup_start=sessions[0],
        warmup_end=sessions[62],
        s0_start=sessions[63],
        s0_end=sessions[299],
        s1_start="2019-03-13",
        s1_end="2020-03-12",
    )


def hand_tr(sessions: tuple[str, ...]) -> dict[str, dict[str, float]]:
    placements = {
        symbol: (indices, HAND_PLACEMENTS[symbol][0])
        for symbol, (_, _, indices) in HAND_PLACEMENTS.items()
    }
    series = {}
    for symbol, (indices, c) in placements.items():
        k = len(indices)
        factor = c ** (1.0 / k)  # k equal log-jumps summing to ln(c)
        series[symbol] = jump_series(
            sessions, {symbol: indices}, {symbol: factor}
        )[symbol]
    return series


def hand_raw(sessions: tuple[str, ...]) -> dict[str, dict[str, float]]:
    """Raw closes for the hand fixture: the TR levels with a distribution
    gap on session index 150 (raw drops 3% on the ex-date; the TR series
    does not, because FD2 adds the distribution back)."""
    tr = hand_tr(sessions)
    raw: dict[str, dict[str, float]] = {}
    for symbol, series in tr.items():
        out = {}
        for index, day in enumerate(sessions):
            value = series[day]
            if index >= 150:
                value *= 0.97  # distribution gap: raw gapped, TR did not
            out[day] = value
        raw[symbol] = out
    return raw


def real_partition() -> PartitionSpec:
    """The frozen partition dates (read-only from the frozen control file
    values quoted in research/control/stocks_free_v2_run/partition.json)."""
    return PartitionSpec(
        warmup_start="2018-01-02",
        warmup_end="2018-04-03",
        s0_start="2018-04-04",
        s0_end="2025-07-31",
        s1_start="2025-08-01",
        s1_end="2026-07-31",
    )


def make_inputs(
    spec: dict,
    sessions: tuple[str, ...],
    tr: dict[str, dict[str, float]],
    raw: dict[str, dict[str, float]],
    partition: PartitionSpec,
) -> FamilyInputs:
    return FamilyInputs(
        sessions=sessions, tr=tr, raw_close=raw, spec=spec, partition=partition
    )


@pytest.fixture(scope="session")
def real_spec() -> dict:
    return load_frozen_spec()


@pytest.fixture(scope="session")
def hand_sessions() -> tuple[str, ...]:
    return calendar_sessions(300)


@pytest.fixture()
def hand_inputs(hand_sessions) -> FamilyInputs:
    return make_inputs(
        hand_spec(),
        hand_sessions,
        hand_tr(hand_sessions),
        hand_raw(hand_sessions),
        hand_partition(hand_sessions),
    )


@pytest.fixture(scope="session")
def s0_sessions() -> tuple[str, ...]:
    return full_s0_sessions()
