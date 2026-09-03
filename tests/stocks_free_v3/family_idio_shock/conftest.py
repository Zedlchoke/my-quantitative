"""Hand-computed synthetic fixtures for SFV3-A5-IDIO-SHOCK-REVERSAL.

Derivation of the exact closed forms (hand computation, reproduced in code)
---------------------------------------------------------------------------
The synthetic SPY issuer-TR return on session index ``k >= 1`` follows the
period-4 cycle ``(+a, -a, 0, 0)`` with ``a = 0.001``.  ANY contiguous
60-session window therefore holds exactly 15 of each cycle position, so for
every window: ``sum(x) = 0`` (mean 0), ``sum(x^2) = 30 a^2``.

A shocked sector ETF returns ``2 * r_SPY`` on every session except its shock
day(s), where — chosen only on cycle positions with ``r_SPY = 0`` (``k % 4``
in {2, 3}) — it returns ``-S`` (negative shock) or ``+S`` (positive shock).

Single shock at day t (inside the 60-session window ending at t):

* OLS slope: ``sum(x*y) = 2*sum(x^2) + x_t*y_t = 60 a^2 + 0`` over
  ``sum(x^2) = 30 a^2``  ->  ``beta = 2`` EXACTLY (the contamination term
  ``x_t * S / sum(x^2)`` vanishes because ``x_t = 0``);
* residuals: 59 exact zeros and ``eps_t = -S - 2*0 = -S``;
* population sigma (ddof=0, mean ``-S/60``):
  ``var = (59 (S/60)^2 + (59 S/60)^2) / 60 = 59 S^2 / 3600``
  -> ``sigma = S sqrt(59) / 60``;
* ``z_t = eps_t / sigma = -60 / sqrt(59) = -7.813834...``  (independent of S
  and a — the trigger is scale-free, exactly as the freeze claims).

Two equal shocks (both on ``r_SPY = 0`` days) inside one window:

* ``beta = 2`` still exactly (both ``x = 0`` on their shock days);
* residuals ``{-S, -S}`` at two known days, 58 zeros;
* ``var = (58 (2S/60)^2 + 2 (58 S/60)^2) / 60 = 29 S^2 / 900``
  -> ``sigma = S sqrt(29) / 30``;
* today's z on the later shock day: ``z = -S / sigma = -30 / sqrt(29)
  = -5.570714...``

Expected mechanism direction (static claim, never scored here): the frozen
mechanism is transitory idio overshoot + liquidity-provision reversion
(Lehmann 1990; Nagel 2012), so a book ENTERED LONG on a z <= -3 shock carries
a POSITIVE expected idio recovery over the hold, and the sign-inverted long
control C1 (entered on z >= +3) carries a NON-POSITIVE expected alpha.
"""

from __future__ import annotations

import math
from datetime import date, timedelta

import pytest

from research.stocks_free_v3.family_idio_shock.arms import ARM_A1, ARM_C1, ARM_N1

#: synthetic SPY cycle amplitude and pattern
SYN_A = 0.001
SYN_CYCLE = (SYN_A, -SYN_A, 0.0, 0.0)

#: exact closed forms derived above
Z_ONE_SHOCK = -60.0 / math.sqrt(59.0)
Z_TWO_SHOCKS = -30.0 / math.sqrt(29.0)
SIGMA_ONE_SHOCK_REL = math.sqrt(59.0) / 60.0  # sigma = |S| * this

#: first session index whose 60-session window is fully populated (session 0
#: carries no issuer-TR return, so the first complete window ends at index 60)
FIRST_FEATURE_INDEX = 60


def make_sessions(n: int, start: date = date(2018, 1, 2)) -> list[str]:
    """``n`` synthetic regular sessions (weekdays) as ISO date strings."""
    out: list[str] = []
    day = start
    while len(out) < n:
        if day.weekday() < 5:
            out.append(day.isoformat())
        day += timedelta(days=1)
    return out


def shock_fixture(n_sessions: int, shocks: dict[str, dict[int, float]]):
    """Synthetic issuer-TR returns with hand-computable idio shocks.

    All 10 FROZEN sector ETFs are present (so the frozen arm configs run
    unmodified); each follows ``2 * r_SPY`` everywhere except its shock
    day(s).  ``shocks`` maps sector symbol -> {session_index: signed shock
    return S} placed on ``r_SPY = 0`` cycle positions.  A perfect fit gives
    sigma = 0 -> z undefined -> the clean names never trigger.
    """
    from research.stocks_free_v3.authority import SECTOR_SYMBOLS

    sessions = make_sessions(n_sessions)
    spy = {s: SYN_CYCLE[k % 4] for k, s in enumerate(sessions) if k >= 1}
    returns: dict[str, dict[str, float]] = {"SPY": spy}
    for sym in sorted(SECTOR_SYMBOLS):
        series: dict[str, float] = {}
        day_shocks = shocks.get(sym, {})
        for k, s in enumerate(sessions):
            if k == 0:
                continue  # issuer TR has no return on the first observation
            if k in day_shocks:
                series[s] = day_shocks[k]
            else:
                series[s] = 2.0 * spy[s]
        returns[sym] = series
    _assert_zero_spy_positions(shocks, sessions, spy)
    return sessions, returns


def _assert_zero_spy_positions(shocks, sessions, spy) -> None:
    for sym, day_map in shocks.items():
        for k in day_map:
            assert k >= 1 and k < len(sessions), "shock outside the session list"
            assert spy[sessions[k]] == 0.0, (
                f"fixture bug: shock for {sym} at index {k} sits on a session "
                "with r_SPY != 0; the closed forms below would not hold")


@pytest.fixture
def single_shock():
    """One -0.06 idio shock on XLK at session index 62 (r_SPY = 0 there)."""
    return shock_fixture(80, {"XLK": {62: -0.06}})


@pytest.fixture
def arms():
    return (ARM_A1, ARM_N1, ARM_C1)
