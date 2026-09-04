"""Dollar-volume shock features and target books for SFV4-A5-H1 (A8).

Owner: lane A8, STOCKS-FREE-V4 family 1 (SFV4-A5-H1-PARTICIPATION-SHIFT).
Implements the frozen feature/ranking/book rules from
``research/control/stocks_free_v4_run/proposals/a5_h1.json`` ("anchor",
"neighbour", "causal_negative_control", "drop_one_design") on top of the
frozen windows in :mod:`research.stocks_free_v4.family_participation.config`.

This module is FEATURES + BOOKS only: deterministic arithmetic over
caller-supplied series.  No data access, no disk writes, no network, and NO
PnL of any kind (returns/factor helpers exist solely as synthetic-test
scaffolding mirroring the frozen benchmark contract and are never run
against real data in this lane).

Data-series contract (frozen in config.py, enforced structurally here)
----------------------------------------------------------------------
* ``DV_s(u) = close_s(u) * volume_s(u)`` is computed ONLY from the raw
  as-traded ``_none`` pair (close AND volume from the SAME series): a split
  moves raw close and raw volume in reciprocal directions on the effective
  date, so the raw pair is internally consistent and the dollar-volume path
  is (near-)continuous across splits.  Pairing an adjusted (``_all``) close
  with a raw volume would double-count the back-adjustment and jump the
  feature at every split — the distortion the proposal explicitly forbids
  ("the volume field of the _all files is NOT used").
* Leg/benchmark total returns use the ``_all`` adjusted close ONLY; the
  ``_all`` volume field is never read by this module.

PIT structure (proven by mutation tests)
----------------------------------------
Every series is passed as a positional sequence ALIGNED to the master session
calendar, and every read is an explicit closed index window
``[t - start_back, t - end_back]`` with ``end_back >= 0``.  No code path can
address an index greater than ``t``: mutating any session after ``t`` cannot
change a decision computed at ``t``.
"""

from __future__ import annotations

import math
from typing import Any, Mapping, Sequence

from research.assets.stocks.factory import CASH_SYMBOL
from research.stocks_free_v4.family_participation.config import (
    LONG_LEGS,
    MIN_RANK_SET,
    RISK_MATCH_SCALE,
    SECTOR_SYMBOLS,
    SHORT_LEGS,
    LEG_WEIGHT,
    WARMUP_SESSIONS,
    ShockWindows,
)


class FeatureError(ValueError):
    """Raised when a feature computation violates the frozen contract."""


# --------------------------------------------------------------------------- #
# dollar volume (raw pair only)
# --------------------------------------------------------------------------- #
def dollar_volume(raw_rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    """Raw as-traded dollar volume per session: ``close * volume``.

    ``raw_rows`` are ``{SYM}_none_p1.json`` ``values`` entries with fields
    ``datetime``, ``close``, ``volume`` (strings or floats).  Fail-closed on
    missing fields, non-finite values, non-positive close or negative volume.
    Returns ``{iso_date: dv}``; the caller aligns to the master calendar.
    """
    out: dict[str, float] = {}
    for row in raw_rows:
        try:
            day = row["datetime"]
            close = float(row["close"])
            volume = float(row["volume"])
        except (KeyError, TypeError, ValueError) as exc:
            raise FeatureError(f"malformed raw row {row!r}: {exc}") from exc
        if not (math.isfinite(close) and math.isfinite(volume)):
            raise FeatureError(f"non-finite close/volume at {day!r}")
        if close <= 0.0:
            raise FeatureError(f"non-positive raw close at {day!r}: {close!r}")
        if volume < 0.0:
            raise FeatureError(f"negative raw volume at {day!r}: {volume!r}")
        out[day] = close * volume
    if not out:
        raise FeatureError("empty raw rows: no dollar volume computable")
    return out


def align_to_master(master_dates: Sequence[str],
                    dv_by_date: Mapping[str, float]) -> list[float | None]:
    """Align a ``{date: dv}`` map onto the master calendar (``None`` = absent).

    The result is a positional series; ``None`` marks a master session the
    symbol did not trade (e.g. XLC before its 2018-06-19 listing).  Fail-closed
    if the master calendar is unsorted/duplicated.
    """
    _validate_master_dates(master_dates)
    return [dv_by_date.get(d) for d in master_dates]


def _validate_master_dates(dates: Sequence[str]) -> None:
    if not dates:
        raise FeatureError("master calendar must be non-empty")
    if list(dates) != sorted(set(dates)):
        raise FeatureError("master calendar must be sorted ascending and unique")


# --------------------------------------------------------------------------- #
# shock ratio (PIT-structured window means)
# --------------------------------------------------------------------------- #
def mean_window(values: Sequence[float | None], t: int,
                start_back: int, end_back: int) -> float:
    """Mean of ``values[t - start_back .. t - end_back]`` (closed, inclusive).

    Fail-closed when any position in the window is missing (``None``), when
    the window would reach before the series start, or when ``end_back < 0``
    (future reads are structurally impossible and rejected outright).
    """
    if end_back < 0 or start_back < end_back:
        raise FeatureError(
            f"invalid window ({start_back=}, {end_back=}); windows grow "
            "backwards from t and never reach past t"
        )
    lo = t - start_back
    hi = t - end_back
    if t < 0 or t >= len(values):
        raise FeatureError(f"decision index {t} outside series of length {len(values)}")
    if lo < 0:
        raise FeatureError(
            f"window start t-{start_back} reaches before the series start "
            f"(index {lo} < 0): the {start_back + 1}-session lookback is not "
            "available at this decision"
        )
    window = values[lo:hi + 1]
    if len(window) != start_back - end_back + 1:
        raise FeatureError("window slice length mismatch (internal error)")
    if any(v is None for v in window):
        raise FeatureError(
            f"missing dollar volume inside the window t-{start_back}..t-{end_back} "
            "at decision index t=" f"{t}: warmup incomplete"
        )
    return math.fsum(float(v) for v in window) / len(window)


def shock_ratio(values: Sequence[float | None], t: int,
                windows: ShockWindows) -> float:
    """One arm's dollar-volume shock ratio at decision index ``t``.

    ``numerator_mean / denominator_mean`` over the arm's frozen windows.  The
    denominator must be strictly positive (a zero baseline is a data defect,
    never a rankable ratio).
    """
    num = mean_window(values, t, windows.num_start_back, windows.num_end_back)
    den = mean_window(values, t, windows.den_start_back, windows.den_end_back)
    if den <= 0.0:
        raise FeatureError(
            f"non-positive shock denominator {den!r} at t={t}: not rankable"
        )
    return num / den


def eligibility(master_dates: Sequence[str], t_index: int,
                presence: Mapping[str, Mapping[str, bool]] | Mapping[str, set[str]],
                warmup: int = WARMUP_SESSIONS,
                symbols: Sequence[str] = SECTOR_SYMBOLS) -> list[str]:
    """Sector ETFs with a full ``warmup``-session window ending at ``t``.

    Fixed availability rule (proposal universe_and_schedule, NOT
    performance-based): a sector is eligible at decision index ``t`` iff its
    data covers EVERY master session in ``[t - warmup + 1, t]``.  Before its
    full warmup exists a sector is simply absent from the rank set (XLC enters
    only from the first anchored decision ~1 year after its 2018-06-19
    listing; on the real snapshot that is the 2019-07-05 decision).

    ``presence[s]`` is any container supporting ``in`` with the master dates
    that have data (a set, or a ``{date: True}`` map).  Presence is a
    dates/universe fact only — no feature values are read.
    """
    _validate_master_dates(master_dates)
    if t_index < warmup - 1 or t_index >= len(master_dates):
        return []
    needed = master_dates[t_index - warmup + 1: t_index + 1]
    out = []
    for s in symbols:
        have = presence.get(s)
        if have is not None and all(d in have for d in needed):
            out.append(s)
    return out


def cross_sectional_shocks(aligned: Mapping[str, Sequence[float | None]],
                           t: int, windows: ShockWindows,
                           eligible: Sequence[str]) -> dict[str, float]:
    """Shock ratios of the eligible sectors at decision index ``t``."""
    if len(eligible) < MIN_RANK_SET:
        raise FeatureError(
            f"eligible rank set {len(eligible)} below the frozen minimum "
            f"{MIN_RANK_SET}: 3v3 book not constructible; refusing to guess"
        )
    return {s: shock_ratio(aligned[s], t, windows) for s in eligible}


def rank_by_shock_desc(shocks: Mapping[str, float]) -> list[str]:
    """Rank symbols by shock DESCENDING; ties break ticker alphabetical ASC."""
    return sorted(shocks, key=lambda s: (-shocks[s], s))


def build_targets(ranked: Sequence[str],
                  long_legs: int = LONG_LEGS,
                  short_legs: int = SHORT_LEGS,
                  leg_weight: float = LEG_WEIGHT) -> dict[str, float]:
    """Frozen 3v3 dollar-neutral book: top-3 +1/6, bottom-3 -1/6, CASH residual.

    Gross 1.0, net 0.0, ``CASH = 1 - net`` absorbs the (float-noise) residual
    and is never a tradable leg.  Fail-closed unless at least
    ``MIN_RANK_SET`` symbols are provided.
    """
    if len(ranked) < MIN_RANK_SET:
        raise FeatureError(
            f"rank set {len(ranked)} below frozen minimum {MIN_RANK_SET}"
        )
    longs = list(ranked[:long_legs])
    shorts = list(ranked[len(ranked) - short_legs:])
    overlap = set(longs) & set(shorts)
    if overlap or len(set(longs)) != long_legs or len(set(shorts)) != short_legs:
        raise FeatureError(
            f"degenerate 3v3 book: longs {longs!r} shorts {shorts!r} overlap {overlap!r}"
        )
    net = math.fsum([leg_weight] * long_legs + [-leg_weight] * short_legs)
    targets: dict[str, float] = {}
    for s in longs:
        targets[s] = leg_weight
    for s in shorts:
        targets[s] = -leg_weight
    targets[CASH_SYMBOL] = 1.0 - net
    return targets


def decide_at(aligned: Mapping[str, Sequence[float | None]],
              t: int, windows: ShockWindows,
              eligible: Sequence[str]) -> dict[str, Any]:
    """One full decision: shocks, rank, and the frozen 3v3 target book."""
    shocks = cross_sectional_shocks(aligned, t, windows, eligible)
    ranked = rank_by_shock_desc(shocks)
    return {
        "t": t,
        "shocks": shocks,
        "ranked": ranked,
        "targets": build_targets(ranked),
        "eligible": list(eligible),
    }


def rebuild_targets_excluding(aligned: Mapping[str, Sequence[float | None]],
                              t: int, windows: ShockWindows,
                              eligible: Sequence[str],
                              excluded: str) -> dict[str, float]:
    """Drop-one rebuild: re-rank from scratch under the identical rule minus one.

    Frozen drop-one design (proposal): the remaining sectors are re-ranked
    from scratch under the identical rule (book still 3v3, membership may
    change), so survival requires the mechanism to survive the loss of its
    single best leg rather than mere deletion of one position.  Fail-closed
    if the excluded symbol is not an eligible leg or the remaining rank set
    falls below the frozen minimum.
    """
    if excluded not in eligible:
        raise FeatureError(
            f"drop-one refused: {excluded!r} is not in the eligible rank set"
        )
    remaining = [s for s in eligible if s != excluded]
    return decide_at(aligned, t, windows, remaining)["targets"]


# --------------------------------------------------------------------------- #
# frozen benchmark contract scaffolding (SYNTHETIC-TEST ONLY in this lane)
# --------------------------------------------------------------------------- #
def ew_sector_factor(returns: Mapping[str, Mapping[str, float]],
                     date: str,
                     symbols: Sequence[str] = SECTOR_SYMBOLS) -> float:
    """Equal-weight sector factor on one date: mean of the sector returns.

    Authorized as the optional sector factor by baseline_invariants.json
    ("equal-weight sector ETF total return"); inputs are TOTAL returns from
    the adjusted (_all) path.  Fail-closed unless every symbol has a finite
    return on the date (the real scorer may relax this; this lane never
    computes it on real data).
    """
    vals = []
    for s in symbols:
        r = returns.get(s, {}).get(date)
        if r is None or not math.isfinite(r):
            raise FeatureError(f"missing/non-finite return for {s!r} at {date!r}")
        vals.append(r)
    return math.fsum(vals) / len(vals)


def risk_matched_context(spy_return: float,
                         scale: float = RISK_MATCH_SCALE) -> float:
    """Frozen risk-matched SPY context: ``scale * r_SPY`` (ex-ante 0.5).

    Per the proposal factor_alpha_test: the declared frozen risk-match scale
    (the dollar-neutral book's long-leg gross exposure) applied ex ante to the
    SPY total-return path; realized arm volatility is never substituted.
    """
    if not math.isfinite(spy_return):
        raise FeatureError("non-finite SPY return")
    return scale * spy_return
