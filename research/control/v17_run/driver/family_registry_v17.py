"""CRYPTO-V17 family-exposure registry (A8 driver lane).

Maps ``formula_id -> pure function over panel rows`` for the family-agnostic
scored-cell driver ``run_v17_cell.py``.  A family spec (frozen selection JSON)
never embeds code: its arms reference exposures BY ``formula_id`` and the
driver resolves them HERE.

Contract of a registered formula (binding, checked by the driver):

* signature ``f(panels, params) -> Dict[str, List[Optional[float]]]``
  where ``panels`` maps symbol -> list of panel rows (H1 rows, or the H4 /
  D1 frames the driver derives in memory from those same H1 rows) and
  ``params`` is the arm spec's ``params`` mapping;
* the returned lists are index-aligned with the bucket grid of each symbol
  (the driver validates lengths and refuses on mismatch);
* values are the DESIRED POSITION over the bucket that FOLLOWS the row the
  information came from, typically in {-1, 0, +1}; ``None`` marks an honest
  warmup bucket (no decision possible there);
* PURE: no I/O, no wall clock, no randomness, no globals mutated.  The
  one-bar availability law (a decision at bucket t may only consume rows
  with close_ts <= t-1) is enforced by the DRIVER, never by the formula.

Registry discipline:

* ``@register(formula_id, example_only=False)``; duplicate ids refused;
* ``example_only=True`` formulas are EXAMPLES for the test suite ONLY --
  the scored emission path of the driver refuses them outright, so an
  example can never surface as a scored proposal; the sanitized dry-run
  (outcome-blind) may still execute them.

A8 families lane (cycle CRYPTO-V17) -- the two selected families ship here
as six scored formulas implementing the FROZEN proposal semantics 1:1
(proposal blob SHAs pinned in ``selection_freeze_v17.json``; the family
spec JSONs under ``driver/families/`` reference these ids):

``SILRES.anchor`` / ``SILRES.neighbour``   V17-A4-P2-SILRES post-silence
    quote-recentering drift (H1, BTCUSDT+ETHUSDT).  Trigger at bucket b:
    ``entry_gap_s(b) >= rolling Q{p} of the PRIOR ``warmup_buckets``
    buckets`` AND ``n_trades(b) >= m x rolling median of the PRIOR
    ``warmup_buckets`` buckets`` (strictly-prior trailing window,
    per-symbol); value = ``sign(last_price(b) - first_price(b))`` on a
    trigger, 0 elsewhere, ``None`` before the warmup.  Anchor freezes
    (P90, 1.5x, 720); neighbour freezes (P75, 1.2x, 720) -- the K holding
    difference lives in the arm exit override of the family spec, not
    here.
``SILRES.control``    Reshuffled-interval placebo: identical anchor
    trigger machinery, then within each symbol block of ``block_buckets``
    consecutive buckets the anchor's trigger positions are permuted across
    the block with ``numpy.default_rng(seed)`` (frozen seed 17040002, ONE
    permutation draw per block, symbols in sorted order, blocks
    ascending); the event count per block is preserved (bijection) and
    each placebo event's direction is recomputed from the RESAMPLED
    bucket's own ``sign(last_price - first_price)``.  No warmup ``None``:
    the placebo needs no rolling statistics at the resampled buckets.
``ATTN_PHASE.anchor`` / ``ATTN_PHASE.neighbour`` / ``ATTN_PHASE.control``
    V17-a5-P1-ATTN-PHASE SOL US-session attention-phase continuation
    (daily, SOLUSDT traded; BTCUSDT+ETHUSDT reference-only and pinned to
    zero position).  Needs H1 grain, so it declares the ``h1`` keyword and
    the driver passes the raw H1 rows through it.  Per day x:
    ``q[x] = SUM_{h in W(k[x+1])} [ n_SOL(x,h)/total_SOL(x)
    - (n_BTC+n_ETH)(x,h)/total_MAJ(x) ]`` over the 8h (anchor 14..21) /
    10h (neighbour 13..22) UTC window; the control rotates the window by
    the frozen sham offset ``k_t = day_index(t from 2025-08-22) mod 24``
    applied at the CONSUMING decision day (anchor/control-sham only
    difference).  Decision at day t: long/flat state ON iff
    ``q[t-1] > median(q[t-md .. t-1])`` (strict crossing, md = 60 anchor /
    90 neighbour, window inclusive of the fresh day), min-hold mh >= 1
    keeps the state ON for its first mh decisions (neighbour mh = 2).
    Series value = the STATE path (1.0 ON / 0.0 flat; ``None`` before the
    median window exists); hold-through days carry the state unchanged.

Percentile/median conventions (implementation pins, conservative): the
rolling quantile is ``numpy.percentile`` linear interpolation; the median
is ``numpy.median`` (average of the two middles).  The reshuffle PRNG is
exactly ``numpy.random.default_rng`` per the frozen proposal text.
"""

from __future__ import annotations

import math

import numpy as np
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

Formula = Callable[
    [Mapping[str, Sequence[Mapping[str, Any]]], Mapping[str, Any]],
    Dict[str, List[Optional[float]]],
]

#: Prefix that marks a formula id as an example for tests only.  The scored
#: emission path of the driver refuses any id carrying this prefix.
EXAMPLE_ONLY_PREFIX = "EXAMPLE_TEST_ONLY."

_REGISTRY: Dict[str, dict] = {}


def register(formula_id: str, *, example_only: bool = False) -> Callable[[Formula], Formula]:
    """Register one exposure formula under a unique id (fail closed)."""
    if not isinstance(formula_id, str) or not formula_id.strip():
        raise ValueError("formula_id must be a non-empty string")
    if formula_id in _REGISTRY:
        raise ValueError(f"formula {formula_id!r} already registered")

    def deco(fn: Formula) -> Formula:
        if not callable(fn):
            raise ValueError(f"formula {formula_id!r} must be callable")
        _REGISTRY[formula_id] = {
            "fn": fn,
            "example_only": bool(example_only),
        }
        return fn

    return deco


def resolve(formula_id: str) -> Formula:
    """Registry lookup; an unknown id is a hard refusal (never a guess)."""
    entry = _REGISTRY.get(formula_id)
    if entry is None:
        raise KeyError(
            f"unknown formula_id {formula_id!r}; registered: {sorted(_REGISTRY)}"
        )
    return entry["fn"]


def is_example_only(formula_id: str) -> bool:
    """True iff the id is reserved for tests (prefix convention + registry flag)."""
    if formula_id.startswith(EXAMPLE_ONLY_PREFIX):
        return True
    entry = _REGISTRY.get(formula_id)
    return bool(entry and entry["example_only"])


def registered_ids() -> List[str]:
    return sorted(_REGISTRY)


def sign(x: float) -> int:
    if x > 0.0:
        return 1
    if x < 0.0:
        return -1
    return 0


# --------------------------------------------------------------------------- #
# V17-A4-P2-SILRES -- post-silence quote-recentering drift (frozen proposal)
# --------------------------------------------------------------------------- #
def _silres_trigger_series(
    rows: Sequence[Mapping[str, Any]],
    gap_percentile: float,
    resumption_multiple: float,
    warmup_buckets: int,
) -> List[Optional[float]]:
    """Frozen SILRES trigger mask, one value per H1 bucket of ONE symbol.

    Trigger(b) = [entry_gap_s(b) >= Q_p of the PRIOR warmup_buckets gaps]
             AND [n_trades(b)   >= m x median of the PRIOR warmup_buckets
                                                                n_trades],
    window strictly prior (b-warmup .. b-1 inclusive); direction =
    sign(last_price(b) - first_price(b)); 0.0 off-trigger; None before the
    warmup completes (no decision is taken before bucket index ``warmup``).
    """
    n = len(rows)
    out: List[Optional[float]] = [None] * n
    if n <= warmup_buckets:
        return out
    gaps = [float(r["entry_gap_s"]) for r in rows]
    counts = [float(r["n_trades"]) for r in rows]
    for b in range(warmup_buckets, n):
        win_g = gaps[b - warmup_buckets : b]
        win_n = counts[b - warmup_buckets : b]
        q = float(np.percentile(win_g, gap_percentile))
        m = float(np.median(win_n))
        if gaps[b] >= q and counts[b] >= resumption_multiple * m:
            out[b] = float(
                sign(float(rows[b]["last_price"]) - float(rows[b]["first_price"]))
            )
        else:
            out[b] = 0.0
    return out


def _silres_common_params(params: Mapping[str, Any]) -> Tuple[float, float, int]:
    gap_percentile = float(params["gap_percentile"])
    resumption_multiple = float(params["resumption_multiple"])
    warmup_buckets = int(params.get("warmup_buckets", 720))
    if not 0.0 < gap_percentile < 100.0:
        raise ValueError(f"gap_percentile must be in (0, 100), got {gap_percentile}")
    if not resumption_multiple > 0.0:
        raise ValueError(
            f"resumption_multiple must be > 0, got {resumption_multiple}"
        )
    if warmup_buckets < 1:
        raise ValueError(f"warmup_buckets must be >= 1, got {warmup_buckets}")
    return gap_percentile, resumption_multiple, warmup_buckets


@register("SILRES.anchor", example_only=False)
def silres_anchor(
    panels: Mapping[str, Sequence[Mapping[str, Any]]],
    params: Mapping[str, Any],
) -> Dict[str, List[Optional[float]]]:
    """V17-A4-P2-SILRES anchor: silence-trigger + resumption-masked drift.

    Frozen anchor parameters (proposal section ``anchor``): P90 silence
    threshold, 1.5x resumption multiple, 720-bucket trailing windows.
    Series[i] = dir of the trigger AT bucket i (the driver's one-bar lag
    puts the entry at bucket i+1 = the frozen next-bucket VWAP fill).
    """
    p, m, w = _silres_common_params(params)
    return {
        sym: _silres_trigger_series(rows, p, m, w) for sym, rows in panels.items()
    }


@register("SILRES.neighbour", example_only=False)
def silres_neighbour(
    panels: Mapping[str, Sequence[Mapping[str, Any]]],
    params: Mapping[str, Any],
) -> Dict[str, List[Optional[float]]]:
    """V17-A4-P2-SILRES neighbour: same mechanism, frozen (P75, 1.2x, 720).

    Holding K=4 (exit at bucket b+5 vwap) is pinned by the arm-level exit
    override in the family spec; the trigger mask differs from the anchor
    ONLY in the frozen threshold parameters.
    """
    p, m, w = _silres_common_params(params)
    return {
        sym: _silres_trigger_series(rows, p, m, w) for sym, rows in panels.items()
    }


@register("SILRES.control", example_only=False)
def silres_control(
    panels: Mapping[str, Sequence[Mapping[str, Any]]],
    params: Mapping[str, Any],
) -> Dict[str, List[Optional[float]]]:
    """V17-A4-P2-SILRES control: reshuffled-interval placebo (frozen).

    Per the proposal section ``control``: within each symbol block of
    ``block_buckets`` consecutive buckets, the anchor's trigger positions
    are permuted across the block by ONE ``numpy.random.default_rng(seed)``
    permutation draw per block (frozen seed 17040002; symbols iterated in
    sorted order, blocks ascending, one draw per block whether or not the
    block carries events).  Event count per block is preserved (the
    permutation is a bijection) while the alignment between the arrival
    signature and the hours it fired on is destroyed; each placebo event's
    direction is recomputed from the resampled bucket's own
    ``sign(last_price - first_price)``.
    """
    p, m, w = _silres_common_params(params)
    block = int(params.get("block_buckets", 720))
    if block < 1:
        raise ValueError(f"block_buckets must be >= 1, got {block}")
    seed = int(params["seed"])
    rng = np.random.default_rng(seed)
    out: Dict[str, List[Optional[float]]] = {}
    for sym in sorted(panels):
        rows = panels[sym]
        n = len(rows)
        anchor = _silres_trigger_series(rows, p, m, w)
        series: List[Optional[float]] = [0.0] * n
        for start in range(0, n, block):
            stop = min(start + block, n)
            perm = rng.permutation(stop - start)  # ONE draw per block, frozen
            events = [
                i - start
                for i in range(start, stop)
                if anchor[i] is not None and anchor[i] != 0.0
            ]
            for offset in events:
                dest = start + int(perm[offset])
                series[dest] = float(
                    sign(
                        float(rows[dest]["last_price"])
                        - float(rows[dest]["first_price"])
                    )
                )
        out[sym] = series
    return out


# --------------------------------------------------------------------------- #
# V17-a5-P1-ATTN-PHASE -- SOL US-session attention phase (frozen proposal)
# --------------------------------------------------------------------------- #
ATTN_TRADED = "SOLUSDT"
ATTN_REFERENCE = ("BTCUSDT", "ETHUSDT")
ATTN_ROTATION_ORIGIN = "2025-08-22"  # S0 day 0 per the frozen sham definition


def _attn_hour_counts(
    h1: Mapping[str, Sequence[Mapping[str, Any]]],
    sym: str,
    days: Sequence[str],
) -> Dict[str, List[int]]:
    """n_SYM(day, hour) trade counts at H1 grain, per UTC day (24 slots)."""
    table: Dict[str, List[int]] = {day: [0] * 24 for day in days}
    for row in h1.get(sym, ()):
        day = str(row["day_utc"])
        if day not in table:
            continue
        table[day][int(str(row["hour_utc"])[11:13])] += int(row["n_trades"])
    return table


def _attn_q_series(
    h1: Mapping[str, Sequence[Mapping[str, Any]]],
    days: Sequence[str],
    window_start: int,
    window_end: int,
    *,
    sham_rotation: bool,
) -> List[Optional[float]]:
    """q[x] for x in 0..len(days)-1 (composition value of day x).

    q[x] = SUM_{h in W(k[x+1])} [ n_SOL(x,h)/total_SOL(x)
                              - (n_BTC+n_ETH)(x,h)/total_MAJ(x) ]
    where the window W is rotated by the sham offset of the CONSUMING
    decision day x+1: k = day_index(x+1 from 2025-08-22) mod 24 when the
    sham rotation is active, else k = 0 (frozen US window).  ``None`` on a
    degenerate day (zero SOL or zero majors trade count: the composition
    is undefined, no honest decision can consume it).
    """
    sol = _attn_hour_counts(h1, ATTN_TRADED, days)
    btc = _attn_hour_counts(h1, ATTN_REFERENCE[0], days)
    eth = _attn_hour_counts(h1, ATTN_REFERENCE[1], days)
    span = window_end - window_start + 1
    out: List[Optional[float]] = []
    for x, day in enumerate(days):
        ps, pb, pe = sol[day], btc[day], eth[day]
        tot_sol = sum(ps)
        tot_maj = sum(pb) + sum(pe)
        if tot_sol <= 0 or tot_maj <= 0:
            out.append(None)
            continue
        k = 0
        if sham_rotation:
            k = (day_index_from_origin(days[x + 1]) if x + 1 < len(days) else 0) % 24
        hours = [(window_start + k + j) % 24 for j in range(span)]
        out.append(
            math.fsum(
                ps[h] / tot_sol - (pb[h] + pe[h]) / tot_maj for h in hours
            )
        )
    return out


def day_index_from_origin(day_utc: str, origin: str = ATTN_ROTATION_ORIGIN) -> int:
    """Zero-based UTC day index of ``day_utc`` from the S0 origin."""
    from datetime import date

    return (date.fromisoformat(day_utc) - date.fromisoformat(origin)).days


@register("ATTN_PHASE.anchor", example_only=False)
def attn_anchor(
    panels: Mapping[str, Sequence[Mapping[str, Any]]],
    params: Mapping[str, Any],
    *,
    h1: Optional[Mapping[str, Sequence[Mapping[str, Any]]]] = None,
) -> Dict[str, List[Optional[float]]]:
    """V17-a5-P1-ATTN-PHASE anchor: US-window composition double difference.

    Frozen anchor parameters (proposal section ``anchor``): US window
    W = hours 14..21 UTC (8h), 60-completed-day rolling median threshold,
    min-hold 1 decision (plain median-crossing long/flat).  The decision
    at day t uses ONLY day <= t-1 rows (q[t-1] vs the median of
    q[t-60..t-1]); fills are the driver's next-bucket fills at the day's
    published bucket-0 VWAP (family spec ``fill_price``).
    """
    return _attn_state_series(panels, params, h1, sham_rotation=False)


@register("ATTN_PHASE.neighbour", example_only=False)
def attn_neighbour(
    panels: Mapping[str, Sequence[Mapping[str, Any]]],
    params: Mapping[str, Any],
    *,
    h1: Optional[Mapping[str, Sequence[Mapping[str, Any]]]] = None,
) -> Dict[str, List[Optional[float]]]:
    """V17-a5-P1-ATTN-PHASE neighbour: W'=13..22 UTC, 90d median, min-hold 2d.

    Frozen neighbour parameters (proposal section ``neighbour``); all else
    identical to the anchor (same columns, lag law, fills, force-flat).
    """
    return _attn_state_series(panels, params, h1, sham_rotation=False)


@register("ATTN_PHASE.control", example_only=False)
def attn_control(
    panels: Mapping[str, Sequence[Mapping[str, Any]]],
    params: Mapping[str, Any],
    *,
    h1: Optional[Mapping[str, Sequence[Mapping[str, Any]]]] = None,
) -> Dict[str, List[Optional[float]]]:
    """V17-a5-P1-ATTN-PHASE control: randomized session-boundary sham.

    Frozen rotation (proposal section ``control``): on each day t the
    window offset k_t = (day_index of t from 2025-08-22) mod 24 is applied,
    i.e. the SAME double-difference profile evaluated over the rotated
    8-hour block (W + k_t) mod 24, every hourly activity level and the
    day's cross-sectional structure preserved.  Decision/fill/cost
    machinery is byte-identical to the anchor's (same median crossing,
    same min-hold law).
    """
    return _attn_state_series(panels, params, h1, sham_rotation=True)


def _attn_state_path(
    q: List[Optional[float]],
    median_days: int,
    min_hold: int,
) -> List[Optional[float]]:
    """Long/flat state per decision day t over the raw q series.

    path[t] = state of the decision at day t (t = 1..n-1; day 0 has no
    completed prior day): ON iff ``q[t-1] > median(q[t-md .. t-1])``
    (strict crossing; the median window is days t-md..t-1 INCLUSIVE of the
    fresh day).  ``None`` before the median window exists (t < md -- no
    decision).  A degenerate (``None``) q inside a window emits no
    decision for that day: the state is CARRIED unchanged (hold-through,
    no fill) rather than force-closed on absent data.  Min-hold: the state
    is carried ON for its first ``min_hold`` decisions (a position exits
    only at an OFF decision after >= min_hold complete held UTC days).
    """
    n = len(q)
    state = 0.0
    episode_start = -1
    path: List[Optional[float]] = [None] * n
    for t in range(1, n):
        if t < median_days:
            path[t] = None  # warmup: the median threshold does not exist yet
            continue
        window = q[t - median_days : t]
        if q[t - 1] is None or any(v is None for v in window):
            path[t] = state  # degenerate day: no decision, carry (hold-through)
            continue
        theta = float(np.median(window))
        raw_on = float(q[t - 1]) > theta
        if state > 0.0:
            if t - episode_start < min_hold:
                pass  # min-hold: no exit before mh complete held days
            elif raw_on:
                pass  # stay ON
            else:
                state = 0.0
                episode_start = -1
        elif raw_on:
            state = 1.0
            episode_start = t
        path[t] = state
    return path


def _attn_state_series(
    panels: Mapping[str, Sequence[Mapping[str, Any]]],
    params: Mapping[str, Any],
    h1: Optional[Mapping[str, Sequence[Mapping[str, Any]]]],
    *,
    sham_rotation: bool,
) -> Dict[str, List[Optional[float]]]:
    """Series wrapper: the ATTN-PHASE decision path on the day grid.

    Series[i] = state of the decision at day i+1 (driver one-bar lag);
    reference symbols BTCUSDT/ETHUSDT are pinned to 0.0 at every bucket
    (frozen universe law: only SOLUSDT is traded).
    """
    if h1 is None:
        raise ValueError(
            "ATTN_PHASE formulas require the raw H1 rows (driver passes "
            "h1=...); refusing to approximate the hour composition from "
            "daily aggregates"
        )
    window_start = int(params["window_start"])
    window_end = int(params["window_end"])
    median_days = int(params["median_days"])
    min_hold = int(params.get("min_hold_days", 1))
    if not 0 <= window_start <= window_end <= 23:
        raise ValueError(
            f"window {window_start}..{window_end} not a non-empty intra-day "
            "UTC hour range"
        )
    if median_days < 1:
        raise ValueError(f"median_days must be >= 1, got {median_days}")
    if min_hold < 1:
        raise ValueError(f"min_hold_days must be >= 1, got {min_hold}")
    missing = [s for s in (ATTN_TRADED,) + ATTN_REFERENCE if s not in panels]
    if missing:
        raise ValueError(f"ATTN_PHASE universe lacks symbols {missing}")

    first = next(iter(panels))
    days = [str(r["day_utc"]) for r in panels[first]]
    q = _attn_q_series(
        h1, days, window_start, window_end, sham_rotation=sham_rotation
    )
    n = len(days)
    path = _attn_state_path(q, median_days, min_hold)
    series: List[Optional[float]] = [None] * n
    for t in range(1, n):
        series[t - 1] = path[t]  # decision at day t emitted at series[t-1]
    out: Dict[str, List[Optional[float]]] = {}
    for sym in panels:
        out[sym] = list(series) if sym == ATTN_TRADED else [0.0] * n
    return out




# --------------------------------------------------------------------------- #
# The EXAMPLE formula -- FOR TESTS ONLY (see module docstring)
# --------------------------------------------------------------------------- #
@register("EXAMPLE_TEST_ONLY.h1_vwap_revert", example_only=True)
def example_h1_vwap_revert(
    panels: Mapping[str, Sequence[Mapping[str, Any]]],
    params: Mapping[str, Any],
) -> Dict[str, List[Optional[float]]]:
    """EXAMPLE_TEST_ONLY hourly mean-reversion flag on close-vs-VWAP.

    signal[t] = -sign((last_price[t] - vwap[t]) / vwap[t])
                if |(last_price[t] - vwap[t]) / vwap[t]| >= threshold
            else 0.0;  None where vwap is undefined/non-positive.
    Params: {"threshold": float > 0}.  Memoryless; the driver's one-bar lag
    makes the decision at bucket t consume row t-1 only.
    """
    threshold = float(params["threshold"])
    if not threshold > 0.0:
        raise ValueError("EXAMPLE_TEST_ONLY.h1_vwap_revert threshold must be > 0")
    out: Dict[str, List[Optional[float]]] = {}
    for sym, rows in panels.items():
        series: List[Optional[float]] = []
        for row in rows:
            vwap = float(row["vwap"])
            last = float(row["last_price"])
            if not (vwap > 0.0) or not (last > 0.0):
                series.append(None)
                continue
            disp = (last - vwap) / vwap
            series.append(
                float(-sign(disp)) if abs(disp) >= threshold else 0.0
            )
        out[sym] = series
    return out


__all__ = [
    "ATTN_ROTATION_ORIGIN",
    "ATTN_REFERENCE",
    "ATTN_TRADED",
    "EXAMPLE_ONLY_PREFIX",
    "attn_anchor",
    "attn_control",
    "attn_neighbour",
    "day_index_from_origin",
    "example_h1_vwap_revert",
    "is_example_only",
    "register",
    "registered_ids",
    "resolve",
    "silres_anchor",
    "silres_control",
    "silres_neighbour",
    "sign",
]
