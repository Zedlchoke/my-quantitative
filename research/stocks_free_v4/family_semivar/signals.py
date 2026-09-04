"""Pure signal mechanics for family SFV4-A4-H1-SEMIVARIANCE-SHARE (A9).

Owner: lane A9, STOCKS-FREE-V4 family 2.  Every function here is a PURE
function of its arguments: no data access, no clocks, no disk, no network,
no PnL.  All of them are byte-deterministic and testable on synthetic
series, exactly as the frozen ex-ante conditions require.

Implements the proposal's anchor rule verbatim:

* state statistic (anchor step 2): over the trailing ``state_window``
  sessions ending at the decision session ``t`` (t's own completed return
  included, nothing after t),

  ``SS_i = sum(r^2)`` (total second moment), ``DS_i = sum(r^2 for r < 0)``,
  semivariance share ``S_i = DS_i / SS_i``;  the CONTROL instead ranks by
  the LEVEL ``SS_i`` descending.  Ranks are descending by the statistic,
  ties broken lexicographically by symbol.

* hysteresis automaton (anchor step 3), evaluated only at decision ticks:
  seed (first tick of a fold) ``LONG := ranks 1-4, SHORT := ranks 8-11``
  (short band = ranks 8..10 when only 10 sectors are eligible, e.g. XLC
  before its availability date); subsequent ticks, applied in this fixed
  order — (i) EXITS: a LONG whose new rank >= 8 leaves LONG (to SHORT if
  ``|SHORT| < 4`` else FLAT); a SHORT whose new rank <= 4 leaves SHORT (to
  LONG if ``|LONG| < 4`` else FLAT); a leg whose new rank is in the buffer
  zone 5-7 is RETAINED (that retention is the +0.25 entry/exit buffer);
  (ii) ENTRIES: FLAT sectors with rank <= 4 enter LONG in ascending-rank
  order while ``|LONG| < 4``; FLAT sectors with rank >= 8 enter SHORT in
  descending-rank order while ``|SHORT| < 4``; ties lexicographic.
  Capacity checks are evaluated AT APPLICATION TIME while walking the exit
  and entry lists in rank order (byte-stable by construction).

* weights (anchor step 4): +0.25 per LONG leg, -0.25 per SHORT leg, CASH
  absorbs the residual (``1 - sum(w)``); gross ``<= 2.0``; weights static
  between ticks.

* frozen kappa fallback (selection_freeze.json condition 1):
  :func:`kappa_frozen` returns 1.0 flat until 252 scored sessions have
  accumulated, thereafter the trailing-252 OLS slope of the arm's daily
  return on the SPY return clipped to [0, 2]; the fallback is never refit
  in-sample (the function sees only data through ``t-1`` by construction of
  its caller).

* equal-weight sector factor (benchmark contract p2_a3: daily-rebalanced
  equal weight): :func:`ew_sector_return` is the unweighted mean of the
  available sector returns for one session.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from research.stocks_free_v4.family_semivar.config import (
    KAPPA_CLIP_HIGH,
    KAPPA_CLIP_LOW,
    KAPPA_FALLBACK_MIN_SCORED_SESSIONS,
    KAPPA_FALLBACK_VALUE,
    KAPPA_OLS_TRAILING_SESSIONS,
    LEG_WEIGHT,
    N_LONG_LEGS,
    N_SHORT_LEGS,
    SHORT_ENTRY_RANK_MIN,
    SORT_SEMIVARIANCE_SHARE,
    SORT_VARIANCE_LEVEL,
    CASH_SYMBOL,
)

#: A leg state inside the hysteresis book.
STATE_LONG = "LONG"
STATE_SHORT = "SHORT"
STATE_FLAT = "FLAT"

#: The rank window (1-based, inclusive) where incumbents are retained.
BUFFER_RANK_LOW = 5
BUFFER_RANK_HIGH = SHORT_ENTRY_RANK_MIN - 1   # 7


class SignalError(ValueError):
    """Raised when a signal input violates the frozen contract (fail closed)."""


# --------------------------------------------------------------------------- #
# state statistics (pure, hand-computable)
# --------------------------------------------------------------------------- #
def total_sum_sq(window_returns: Sequence[float]) -> float:
    """``SS = sum(r^2)`` over the trailing window (the LEVEL statistic)."""
    if not window_returns:
        raise SignalError("window_returns must be non-empty")
    bad = [r for r in window_returns if not isinstance(r, (int, float))
           or isinstance(r, bool) or not math.isfinite(float(r))]
    if bad:
        raise SignalError(f"non-finite returns in window: {bad[:5]!r}")
    return math.fsum(float(r) ** 2 for r in window_returns)


def semivariance_share(window_returns: Sequence[float]) -> float:
    """``S = DS / SS`` where ``DS = sum(r^2 for r < 0)`` (the SHAPE statistic).

    Exact invariance property (pinned by tests): the statistic depends only on
    the SIGNS and RELATIVE magnitudes of the returns — scaling every return by
    a constant c > 0 multiplies DS and SS by c^2 and leaves S unchanged, so
    scaling PRICES by any positive factor leaves the whole ranking (and hence
    every decision) invariant.
    """
    ss = total_sum_sq(window_returns)
    if ss <= 0.0:
        raise SignalError(
            "semivariance share undefined: the window has zero total second "
            "moment (all-zero returns); fail closed rather than guess"
        )
    ds = math.fsum(float(r) ** 2 for r in window_returns if float(r) < 0.0)
    return ds / ss


def feature_value(window_returns: Sequence[float], sort_statistic: str) -> float:
    """Dispatch the arm's ONE frozen statistic (anchor step 2 / control)."""
    if sort_statistic == SORT_SEMIVARIANCE_SHARE:
        return semivariance_share(window_returns)
    if sort_statistic == SORT_VARIANCE_LEVEL:
        return total_sum_sq(window_returns)
    raise SignalError(f"unknown sort statistic {sort_statistic!r}")


# --------------------------------------------------------------------------- #
# ranking (descending, ties lexicographic by symbol)
# --------------------------------------------------------------------------- #
def rank_symbols(features: Mapping[str, float]) -> tuple[str, ...]:
    """Symbols in rank order: rank 1 = highest feature, ties lexicographic.

    Determinism contract (pinned by tests): the sort key is
    ``(-value, symbol)`` so equal statistics resolve by ascending symbol and
    the output never depends on input mapping order.
    """
    unknown = [s for s, v in features.items()
               if not isinstance(v, (int, float)) or isinstance(v, bool)
               or not math.isfinite(float(v))]
    if unknown:
        raise SignalError(f"non-finite feature values: {unknown[:5]!r}")
    if len(set(features)) != len(features):
        raise SignalError("duplicate symbols in feature mapping")
    return tuple(sorted(features, key=lambda s: (-float(features[s]), s)))


def eligibility(sessions_history: Mapping[str, Sequence[str]],
                decision_session: str, state_window: int,
                symbols: Sequence[str]) -> tuple[str, ...]:
    """Symbols eligible at a decision session (the XLC availability rule).

    A symbol is eligible when its OWN authorized session history contains at
    least ``state_window`` sessions up to and including the decision session
    (the trailing window on the shared calendar is fully covered).  Before
    that a symbol is excluded from ranks and held FLAT — an availability
    rule, not a selection.  ``sessions_history`` values must be ascending ISO
    date strings; nothing after the decision session is inspected.
    """
    out = []
    for s in symbols:
        hist = sessions_history.get(s)
        if hist is None:
            raise SignalError(f"no session history provided for {s!r}")
        idx = _bisect_le(hist, decision_session)
        if idx + 1 >= state_window:
            out.append(s)
    return tuple(out)


def _bisect_le(sorted_dates: Sequence[str], session: str) -> int:
    """Last index i with sorted_dates[i] <= session, or -1 (binary search)."""
    lo, hi = 0, len(sorted_dates) - 1
    ans = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if sorted_dates[mid] <= session:
            ans = mid
            lo = mid + 1
        else:
            hi = mid - 1
    return ans


# --------------------------------------------------------------------------- #
# hysteresis book automaton (anchor step 3, fixed transition order)
# --------------------------------------------------------------------------- #
def seed_book(ranks: Sequence[str]) -> dict[str, str]:
    """Seed rule (first tick of a fold): LONG := ranks 1-4, SHORT := ranks 8+.

    The short band is ``ranks[7:7 + N_SHORT]`` in rank order — ranks 8-11 on
    a full 11-name ranking, ranks 8-10 when only 10 sectors are eligible
    (XLC unavailable), and it fails closed if fewer than 8 sectors are
    eligible (the 4/4 book shape could not be formed at all).  Every other
    eligible sector is FLAT.
    """
    if len(ranks) < SHORT_ENTRY_RANK_MIN:
        raise SignalError(
            f"seed needs at least {SHORT_ENTRY_RANK_MIN} eligible sectors to "
            f"form the 4/4 book, got {len(ranks)}"
        )
    longs = list(ranks[:N_LONG_LEGS])
    shorts = list(ranks[SHORT_ENTRY_RANK_MIN - 1:SHORT_ENTRY_RANK_MIN - 1 + N_SHORT_LEGS])
    state = {s: STATE_FLAT for s in ranks}
    for s in longs:
        state[s] = STATE_LONG
    for s in shorts:
        state[s] = STATE_SHORT
    return state


def step_book(prev_state: Mapping[str, str],
              ranks: Sequence[str]) -> dict[str, str]:
    """One hysteresis transition (subsequent ticks), fixed order (i) exits,
    (ii) entries; capacity checks evaluated at application time in rank
    order; ties lexicographic; buffer ranks 5-7 retain incumbents."""
    rank_of = {s: i + 1 for i, s in enumerate(ranks)}
    known = set(prev_state)
    if known != set(ranks):
        raise SignalError(
            "step_book requires the previous state to cover exactly the "
            "eligible set of this tick (eligibility changes re-seed); "
            f"state-only={sorted(known - set(ranks))[:3]} "
            f"rank-only={sorted(set(ranks) - known)[:3]}"
        )
    state: dict[str, str] = dict(prev_state)
    n_long = sum(1 for v in state.values() if v == STATE_LONG)
    n_short = sum(1 for v in state.values() if v == STATE_SHORT)

    # (i) EXITS — walked in ascending rank order (byte-stable).
    for s in ranks:
        r = rank_of[s]
        if state[s] == STATE_LONG and r >= SHORT_ENTRY_RANK_MIN:
            if n_short < N_SHORT_LEGS:
                state[s] = STATE_SHORT
                n_long -= 1
                n_short += 1
            else:
                state[s] = STATE_FLAT
                n_long -= 1
        elif state[s] == STATE_SHORT and r <= N_LONG_LEGS:
            if n_long < N_LONG_LEGS:
                state[s] = STATE_LONG
                n_short -= 1
                n_long += 1
            else:
                state[s] = STATE_FLAT
                n_short -= 1
        # ranks in the buffer zone 5-7 retain the incumbent (hysteresis).

    # (ii) ENTRIES — long band ascending rank, then short band DESCENDING
    # rank (proposal), each while capacity remains; ties lexicographic.
    for s in ranks:
        if state[s] == STATE_FLAT and rank_of[s] <= N_LONG_LEGS and n_long < N_LONG_LEGS:
            state[s] = STATE_LONG
            n_long += 1
    for s in reversed(ranks):
        if state[s] == STATE_FLAT and rank_of[s] >= SHORT_ENTRY_RANK_MIN \
                and n_short < N_SHORT_LEGS:
            state[s] = STATE_SHORT
            n_short += 1
    return state


def target_weights(state: Mapping[str, str],
                   leg_weight: float = LEG_WEIGHT) -> dict[str, float]:
    """Weights from a book state: +-leg_weight per leg, CASH residual.

    Gross ``= leg_weight x (n_long + n_short) <= 2.0``; net ``= leg_weight x
    (n_long - n_short)`` (exactly 0 on a full 4/4 book; the early fold-1
    stretches with a thinner short side are frozen expected behavior).  CASH
    absorbs ``1 - net`` and is never a symbol.
    """
    if leg_weight <= 0.0:
        raise SignalError("leg_weight must be positive")
    longs = sorted(s for s, v in state.items() if v == STATE_LONG)
    shorts = sorted(s for s, v in state.items() if v == STATE_SHORT)
    unknown = sorted(set(state) - set(longs) - set(shorts)
                     - {s for s, v in state.items() if v == STATE_FLAT})
    if unknown:
        raise SignalError(f"unknown leg states: {unknown[:5]!r}")
    gross = leg_weight * (len(longs) + len(shorts))
    if gross > 2.0 + 1e-12:
        raise SignalError(f"book gross {gross!r} exceeds the frozen cap 2.0")
    net = leg_weight * (len(longs) - len(shorts))
    weights = {s: leg_weight for s in longs}
    for s in shorts:
        weights[s] = -leg_weight
    weights[CASH_SYMBOL] = 1.0 - net
    return weights


# --------------------------------------------------------------------------- #
# frozen kappa fallback (selection_freeze.json condition 1 — pure function)
# --------------------------------------------------------------------------- #
def kappa_frozen(arm_returns_so_far: Sequence[float],
                 spy_returns_so_far: Sequence[float]) -> float:
    """Risk-match multiple kappa_t under the FROZEN ex-ante rule.

    ``arm_returns_so_far`` / ``spy_returns_so_far`` are the SCORED daily
    returns of the arm and of SPY for all sessions BEFORE t (the caller passes
    data through ``t-1`` only, so the function is PIT by construction).  Rule:

    * fewer than 252 scored sessions accumulated -> ``1.0`` flat (the
      fallback; never refit in-sample, regardless of the data);
    * otherwise the OLS slope of the arm's last 252 daily returns on the
      aligned SPY returns, clipped to [0, 2].

    Fail-closed on misaligned inputs or a degenerate (zero-variance) SPY
    trailing window.
    """
    n = len(arm_returns_so_far)
    if len(spy_returns_so_far) != n:
        raise SignalError(
            f"arm ({n}) and SPY ({len(spy_returns_so_far)}) return counts "
            "disagree; kappa_t needs aligned scored histories"
        )
    for series, name in ((arm_returns_so_far, "arm"), (spy_returns_so_far, "SPY")):
        bad = [r for r in series if not isinstance(r, (int, float))
               or isinstance(r, bool) or not math.isfinite(float(r))]
        if bad:
            raise SignalError(f"non-finite {name} returns: {bad[:3]!r}")
    if n < KAPPA_FALLBACK_MIN_SCORED_SESSIONS:
        return KAPPA_FALLBACK_VALUE
    a = [float(r) for r in arm_returns_so_far[-KAPPA_OLS_TRAILING_SESSIONS:]]
    b = [float(r) for r in spy_returns_so_far[-KAPPA_OLS_TRAILING_SESSIONS:]]
    slope = _ols_slope(a, b)
    return min(max(slope, KAPPA_CLIP_LOW), KAPPA_CLIP_HIGH)


def _ols_slope(y: Sequence[float], x: Sequence[float]) -> float:
    """OLS slope of y on x (``sum((x-xb)(y-yb)) / sum((x-xb)^2)``)."""
    n = len(x)
    if n < 2:
        raise SignalError("OLS needs at least 2 observations")
    xb = math.fsum(x) / n
    yb = math.fsum(y) / n
    sxx = math.fsum((xi - xb) ** 2 for xi in x)
    if sxx <= 0.0:
        raise SignalError(
            "degenerate OLS: SPY trailing window has zero variance; fail "
            "closed rather than guess a slope"
        )
    return math.fsum((xi - xb) * (yi - yb) for xi, yi in zip(x, y)) / sxx


# --------------------------------------------------------------------------- #
# equal-weight sector factor (benchmark contract: daily-rebalanced EW)
# --------------------------------------------------------------------------- #
def ew_sector_return(session_returns: Mapping[str, float]) -> float:
    """Equal-weight mean of the AVAILABLE sector returns for one session.

    Each sector contributes only where its adjusted series produced a return
    that session (XLC contributes from its inception); the convention is the
    frozen daily-rebalanced equal weight, so the factor is the plain mean of
    the available contributions.
    """
    if not session_returns:
        raise SignalError("no sector returns available for this session")
    bad = [s for s, r in session_returns.items()
           if not isinstance(r, (int, float)) or isinstance(r, bool)
           or not math.isfinite(float(r))]
    if bad:
        raise SignalError(f"non-finite sector returns: {bad[:5]!r}")
    return math.fsum(float(r) for r in session_returns.values()) / len(session_returns)


__all__ = [
    "BUFFER_RANK_HIGH",
    "BUFFER_RANK_LOW",
    "STATE_FLAT",
    "STATE_LONG",
    "STATE_SHORT",
    "SignalError",
    "eligibility",
    "ew_sector_return",
    "feature_value",
    "kappa_frozen",
    "rank_symbols",
    "seed_book",
    "semivariance_share",
    "step_book",
    "target_weights",
    "total_sum_sq",
]
