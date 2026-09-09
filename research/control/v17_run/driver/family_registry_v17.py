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
``WKNDLIQ.anchor`` / ``WKNDLIQ.neighbour`` / ``WKNDLIQ.control``
    V17-A4-P1-WKNDLIQ weekend liquidity-participation cycle (H1,
    BTCUSDT+ETHUSDT, short-only session-conditioned book).  Pure calendar
    flag: -1.0 at exactly ONE decision bucket per week (anchor: the
    Friday hour_utc=21 bucket, decision at its close; neighbour: Friday
    19:00), 0.0 elsewhere, no warmup ``None`` (the trigger consumes no
    lookback).  No price/flow/size column is read, so the availability
    law holds trivially.  With the family's lag-0 + ``vwap`` fill law the
    driver fills at the NEXT bucket's published VWAP (Friday 22:00 /
    Friday 20:00) and the family holding (50 / 54 buckets; the
    neighbour's is an arm-level exit override) realizes the frozen cover
    calendar (Monday 00:00 / Monday 02:00 bucket VWAP).  The control is
    the randomized session-boundary sham: ONE
    ``numpy.random.default_rng(17040001)`` uniform draw per week over
    exactly the weekly entry offsets whose equally-long window does NOT
    overlap the true anchor window (formula docstring: full arithmetic
    and the frozen-constant reconciliation note).
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

``OICASCADE.anchor`` / ``OICASCADE.neighbour`` / ``OICASCADE.control``
    V17-A6-P2-OICASCADE OI-collapse cascade-exhaustion event book (H4,
    BTCUSDT+ETHUSDT+SOLUSDT, long-only 24h event book; selection v3 --
    implemented 1:1 from the frozen proposal blob ff38f2c5c7d617fa2fbf2de
    bff0007f3d73a003f).  Needs the REDUCED open-interest endpoint series
    (data.binance.vision futures metrics, 1,095-file sha-manifested pull,
    reduced cache referenced by the family spec's per-arm
    ``endpoint_series`` path), so the formulas declare the ``endpoint``
    keyword and the driver passes the availability-aligned series through
    (one value per H4 bucket: the last metrics snapshot with create_time
    tau <= that bucket's close; null = no admissible snapshot within the
    frozen +/-30 min endpoint tolerance).  Gate at H4 close T:
    ``r_OI(T) = OI(T)/OI(T-24h) - 1`` (both endpoint buckets present, else
    the frozen substitution "undefined = 0") must be <= the rolling P10
    (neighbour P5) of the PRIOR 720 strictly-past H4 closes AND the panel
    24h return ``R_24h(T) = last_price(T)/last_price(T-24h) - 1 < 0``.
    Series = +1.0 at a TAKEN event (driver lag 0 + vwap fill => entry at
    the next H4 bucket's published VWAP; exit span holding_buckets 5/11 =
    the first bucket close >= T+24h / T+48h), 0.0 elsewhere, ``None``
    before the quantile window exists.  One position per symbol: events
    firing while a position is open are ignored (0.0), re-arm after flat.
    The control is the randomized-event-time sham: per symbol,
    ``numpy.random.default_rng(1717)`` (fresh per symbol -- the sham is
    per-symbol), rejection-sampling the anchor's TAKEN-window count of 24h
    long windows uniformly over S0, excluding +/-1-day fold purge zones,
    closes within +/-3 days of any true gate-fired event, and closes
    within 24h of an accepted window (redraw on collision; exhausted draw
    space = hard error).  DATA AUTHORITY (remediated, A8 r2): the CORRECTED
    reduced cache is warmup-EXTENDED -- 2,904 H4 snapshots per symbol
    (484 days from 2025-04-25T00:00Z = 119 pre-S0 warmup days + the 365-day
    S0), per-symbol distinct; the family spec's endpoint_series blocks pin
    the alignment hints (series_start_utc 2025-04-25T00:00:00Z +
    bucket_hours 4) and the loader returns the full warmup+S0 array.  The
    formulas index S0 ordinal i at the fixed warmup offset
    ``w = i + (len(endpoint) - len(grid))`` (714 = 119 x 6 on the real
    authority) so the T-24h endpoint denominator and the trailing 720-close
    P10 window CONSUME pre-S0 slots: the first decidable S0 ordinal is
    ``max(0, 720 - warmup)`` (6 on the real authority) instead of 720, so
    fold F0 is tradeable, while decisions remain S0-only (grid-aligned
    series, fold force-flat unchanged).  Old stale notes (byte-identical
    arrays / S0-only pull) were remediated by the D2 re-pull + this lane;
    they ride the family spec's recorded reconciliation text.

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
# V17-A4-P1-WKNDLIQ -- weekend liquidity-participation cycle (frozen proposal
# research/control/v17_run/d1/a4/proposal_P1.json, blob efb773bcc3d70ae1c348b
# e5ba0c99a7ee5efda47)
# --------------------------------------------------------------------------- #
WKND_WEEKDAYS = (
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday",
    "Sunday",
)
#: The sham's week clock: 168-bucket windows anchored at Friday 00:00 UTC
#: (the anchor mechanism's own weekly boundary).  Consecutive such windows
#: tile the timeline without overlap.
WKND_WEEK_ANCHOR_WEEKDAY = "Friday"
#: Frozen sham PRNG seed (proposal section ``control``, verbatim).
WKND_SHAM_SEED = 17040001


def _wknd_weekday_of(day_utc: str) -> str:
    from datetime import date

    name = date.fromisoformat(day_utc).strftime("%A")
    if name not in WKND_WEEKDAYS:  # pragma: no cover - strftime total
        raise ValueError(f"unrecognised weekday for {day_utc!r}: {name!r}")
    return name


def _wknd_params(params: Mapping[str, Any]) -> Tuple[str, int]:
    """Validate one arm's frozen entry calendar; return (weekday, entry_hour).

    The formula emits at the DECISION bucket = the hour BEFORE the entry
    bucket (the proposal's "decision at the close of the entry-hour-minus-1
    bucket"), so the entry hour must be >= 1 inside its own day.
    """
    weekday = str(params.get("entry_weekday_utc", "Friday"))
    entry_hour = int(params.get("entry_hour_utc", 22))
    if weekday not in WKND_WEEKDAYS:
        raise ValueError(
            f"entry_weekday_utc {weekday!r} not a UTC weekday name"
        )
    if not 1 <= entry_hour <= 23:
        raise ValueError(
            f"entry_hour_utc must be in 1..23 (decision = entry hour - 1), "
            f"got {entry_hour}"
        )
    return weekday, entry_hour


def _wknd_calendar_series(
    rows: Sequence[Mapping[str, Any]],
    weekday: str,
    entry_hour: int,
) -> List[float]:
    """Short-only calendar flag over ONE symbol's H1 rows.

    series[i] = -1.0 iff row i's (day_utc, hour_utc) == (weekday,
    entry_hour - 1) -- the decision bucket whose close fills at the next
    bucket's published VWAP (the driver's lag-0 + vwap law); 0.0
    elsewhere.  Exactly one decision bucket per calendar week; no
    re-entry, no pyramiding; the series consumes NO price/flow/size
    column (availability law trivially satisfied).
    """
    decision_hour = entry_hour - 1
    out: List[float] = []
    for row in rows:
        if (
            _wknd_weekday_of(str(row["day_utc"])) == weekday
            and int(str(row["hour_utc"])[11:13]) == decision_hour
        ):
            out.append(-1.0)
        else:
            out.append(0.0)
    return out


@register("WKNDLIQ.anchor", example_only=False)
def wkndliq_anchor(
    panels: Mapping[str, Sequence[Mapping[str, Any]]],
    params: Mapping[str, Any],
) -> Dict[str, List[Optional[float]]]:
    """V17-A4-P1-WKNDLIQ anchor: Friday 22:00 -> Monday 00:00 weekend short.

    Frozen anchor parameters (proposal sections ``entry_exit_fills`` /
    ``anchor``): decision at the Friday hour_utc=21 close, entry fill at
    the Friday 22:00 bucket's published vwap (driver lag 0 + fill_price
    vwap), cover at the Monday 00:00 bucket's published vwap -- exactly
    50 held H1 buckets on the UTC grid, pinned by the family spec's
    ``exit.holding_buckets`` (the frozen text's "26 buckets" label
    under-counts its own Friday 22:00 -> Monday 00:00 calendar anchors by
    exactly one 24h day; the calendar boundaries are implemented
    verbatim -- QUESTION_FOR_A1).  Short-only, 1 unit per symbol
    independently, one entry per week, no re-entry.
    """
    weekday, entry_hour = _wknd_params(params)
    return {
        sym: _wknd_calendar_series(rows, weekday, entry_hour)
        for sym, rows in panels.items()
    }


@register("WKNDLIQ.neighbour", example_only=False)
def wkndliq_neighbour(
    panels: Mapping[str, Sequence[Mapping[str, Any]]],
    params: Mapping[str, Any],
) -> Dict[str, List[Optional[float]]]:
    """V17-A4-P1-WKNDLIQ neighbour: Friday 20:00 -> Monday 02:00 window.

    Same mechanism, frozen neighbour window parameters (proposal section
    ``neighbour``): decision at the Friday 19:00 close, entry fill at the
    Friday 20:00 bucket vwap, cover at the Monday 02:00 bucket vwap --
    54 held H1 buckets, pinned by the neighbour arm's exit override in
    the family spec.  Everything else identical to the anchor.
    """
    weekday, entry_hour = _wknd_params(params)
    return {
        sym: _wknd_calendar_series(rows, weekday, entry_hour)
        for sym, rows in panels.items()
    }


def _wknd_admissible_offsets(
    anchor_entry_hour: int, holding_buckets: int
) -> List[int]:
    """Weekly entry offsets (Friday-anchored, 0..167) whose equally-long
    window does NOT overlap the true anchor window.

    Week frame: offsets 0..167 from Friday 00:00 UTC.  The true anchor
    window is the held arc [a, a+H-1] (mod 168) with a =
    ``anchor_entry_hour`` (the anchor enters on the week-anchor day) and
    H = ``holding_buckets``.  A sham entry at offset k holds [k, k+H-1]
    (mod 168); the excluded starts form the arc [a-H+1, a+H-1] (2H-1
    offsets, cyclic), so the no-overlap admissible set is the contiguous
    arc [a+H, a+168-H] (mod 168) of 169-2H offsets, empty (refused) once
    H > 84.

    Reconciliation note (recorded, not hidden): the frozen control text
    says "144 hourly offsets" -- the same one-day-under-count of the
    weekend span that labels the 50-bucket Friday 22:00 -> Monday 00:00
    window "26 buckets" (168 - 144 = 24 excluded offsets cannot realise
    "do not overlap the true anchor window" for any window length that
    matches the anchor's real 50-bucket span; the honest no-overlap set
    on the frozen calendar is these 69 offsets, Friday-relative
    72..140 = Monday 00:00 .. Wednesday 20:00 starts).  The frozen
    PRNG/seed/one-draw-per-week/no-overlap mechanics are implemented
    verbatim; the count is raised as QUESTION_FOR_A1.
    """
    a, holding = int(anchor_entry_hour), int(holding_buckets)
    if not 1 <= a <= 23:
        raise ValueError(f"anchor_entry_hour must be in 1..23, got {a}")
    if not 1 <= holding <= 167:
        raise ValueError(
            f"holding_buckets must be in 1..167, got {holding}"
        )
    if 2 * holding > 168:
        raise ValueError(
            f"holding_buckets {holding} too long for a no-overlap weekly "
            "sham window (2xH > 168); refusing"
        )
    return [(a + holding + j) % 168 for j in range(169 - 2 * holding)]


@register("WKNDLIQ.control", example_only=False)
def wkndliq_control(
    panels: Mapping[str, Sequence[Mapping[str, Any]]],
    params: Mapping[str, Any],
) -> Dict[str, List[Optional[float]]]:
    """V17-A4-P1-WKNDLIQ control: randomized session-boundary sham.

    Frozen control mechanics (proposal section ``control``), verbatim:
    identical book to the anchor (symbols, short-only direction, fill
    timing at the entry bucket's published vwap via the driver's lag-0 +
    vwap law, EQUAL holding duration via the family
    ``exit.holding_buckets``, once-per-fill tier-2.0 costs, force-flat
    law) but each week's window start is drawn with
    ``numpy.random.default_rng(seed)`` (frozen seed 17040001), ONE draw
    per week over S0, uniformly over exactly the weekly entry offsets
    whose equally-long window does not overlap the true anchor window
    (see ``_wknd_admissible_offsets``).  Weeks are the 168-bucket windows
    anchored at each Friday 00:00 UTC present in the panel (the anchor
    mechanism's own weekly clock, one week per anchor decision), iterated
    in ascending order; the draw is consumed for EVERY week (an
    off-grid entry after the last week is drawn then skipped -- the
    driver would refuse the trip anyway), so the stream is a pure
    function of the seed and the week count.  The drawn SHAM CALENDAR is
    ONE window per week shared by every symbol (the anchor's calendar is
    symbol-independent, and the sham replaces exactly that calendar --
    exactly one draw per week over S0, not one per symbol).  The shared
    bucket grid is a driver-validated invariant.  Deterministic: no wall
    clock, no global state.
    """
    seed = int(params.get("seed", WKND_SHAM_SEED))
    if seed != WKND_SHAM_SEED:
        raise ValueError(
            f"WKNDLIQ.control seed must be the frozen 17040001, got {seed}"
        )
    _, anchor_entry_hour = _wknd_params(params)
    holding = int(params["holding_buckets"])
    admissible = _wknd_admissible_offsets(anchor_entry_hour, holding)
    rng = np.random.default_rng(seed)
    from datetime import datetime, timedelta

    first = next(iter(panels))
    rows = panels[first]
    index_of = {str(r["hour_utc"]): i for i, r in enumerate(rows)}
    week_days = sorted(
        {
            str(r["day_utc"])
            for r in rows
            if _wknd_weekday_of(str(r["day_utc"])) == WKND_WEEK_ANCHOR_WEEKDAY
        }
    )
    decision_indices: List[int] = []
    for week_day in week_days:  # ONE draw per week, ascending, frozen
        k = int(admissible[int(rng.integers(0, len(admissible)))])
        entry_dt = (
            datetime.strptime(week_day, "%Y-%m-%d") + timedelta(hours=k)
        )
        entry_key = entry_dt.strftime("%Y-%m-%dT%H")
        decision_key = (entry_dt - timedelta(hours=1)).strftime(
            "%Y-%m-%dT%H"
        )
        d_idx = index_of.get(decision_key)
        e_idx = index_of.get(entry_key)
        if d_idx is None or e_idx is None or e_idx != d_idx + 1:
            continue  # entry window off-grid: decision never existed
        decision_indices.append(d_idx)
    out: Dict[str, List[Optional[float]]] = {}
    for sym, sym_rows in panels.items():
        if [str(r["hour_utc"]) for r in sym_rows] != [
            str(r["hour_utc"]) for r in rows
        ]:
            raise ValueError(
                f"WKNDLIQ.control: symbol {sym} grid differs from "
                f"{first}; refusing (the sham calendar is shared)"
            )
        series = [0.0] * len(sym_rows)
        for d_idx in decision_indices:
            series[d_idx] = -1.0
        out[sym] = series
    return out


# --------------------------------------------------------------------------- #
# V17-A6-P2-OICASCADE -- OI-collapse cascade-exhaustion event book (frozen
# proposal research/control/v17_run/d1/a6/proposal_P2.json, blob sha
# ff38f2c5c7d617fa2fbf2debff0007f3d73a003f; selection v3, never yet
# implemented before this lane)
# --------------------------------------------------------------------------- #
#: H4 buckets per UTC day on the frozen clock (24h / 4h).
OIC_H4_PER_DAY = 6
#: Frozen sham PRNG seed (proposal section ``control``, verbatim).
OIC_SHAM_SEED = 1717
#: Sham draws exclude any H4 close within +/-3 days of a true event.
OIC_SHAM_EVENT_EXCLUSION_DAYS = 3
#: Deterministic bound on rejection-sampling attempts per required window
#: (fail closed: an exhausted draw space is a hard error, never a shortfall).
OIC_MAX_DRAW_ATTEMPTS_PER_WINDOW = 200_000

_H4_MS = 4 * 3600 * 1000
_DAY_MS = 24 * 3600 * 1000


def _oic_bucket_close_ms(key: str) -> int:
    """UTC close (ms) of the H4 bucket whose START key is ``YYYY-MM-DDTHH``
    (the driver's H4 grid keys are bucket-start hours 00/04/08/12/16/20)."""
    from datetime import datetime, timezone

    dt = datetime.strptime(str(key), "%Y-%m-%dT%H").replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000) + _H4_MS


def _oic_common_params(params: Mapping[str, Any]) -> Tuple[float, int, int, int]:
    """Validate one arm's frozen gate parameters.

    ``oi_percentile``: the r_OI gate percentile (anchor 10.0 = P10,
    neighbour 5.0 = P5); ``window_closes``: strictly-past H4 closes funding
    the rolling quantile (frozen 720 = 120d x 6 H4, the proposal's "720 H4
    decisions of consumed lookback"); ``holding_buckets``: driver exit span
    entry->exit (5 = 24h held buckets t+1..t+6 for the anchor, 11 = 48h for
    the neighbour); ``h4_per_day``: 6 (frozen clock constant).
    """
    oi_percentile = float(params["oi_percentile"])
    window_closes = int(params.get("window_closes", 720))
    holding_buckets = int(params["holding_buckets"])
    h4_per_day = int(params.get("h4_per_day", OIC_H4_PER_DAY))
    if not 0.0 < oi_percentile < 100.0:
        raise ValueError(
            f"oi_percentile must be in (0, 100), got {oi_percentile}"
        )
    if window_closes < 1:
        raise ValueError(f"window_closes must be >= 1, got {window_closes}")
    if holding_buckets < 1:
        raise ValueError(f"holding_buckets must be >= 1, got {holding_buckets}")
    if h4_per_day < 1:
        raise ValueError(f"h4_per_day must be >= 1, got {h4_per_day}")
    return oi_percentile, window_closes, holding_buckets, h4_per_day


def _oic_check_grid_regular(closes: Sequence[int]) -> None:
    """The 24h-ago endpoint of bucket i is the series value 6 buckets back;
    that index arithmetic is only honest on a gap-free 4h grid (fail closed
    on any irregular spacing)."""
    for a, b in zip(closes, closes[1:]):
        if b - a != _H4_MS:
            raise ValueError(
                "OICASCADE: the H4 bucket grid is not a gap-free 4h UTC grid "
                f"({a} -> {b}); refusing (the 24h endpoint index law needs it)"
            )


def _oic_gate(
    rows: Sequence[Mapping[str, Any]],
    oi: Sequence[Optional[float]],
    *,
    oi_percentile: float,
    window_closes: int,
    holding_buckets: int,
    h4_per_day: int,
) -> Tuple[List[Optional[float]], List[int]]:
    """Frozen event gate + one-position book over ONE symbol's H4 frames.

    Availability law (endpoint series): value i is the LAST metrics
    snapshot with create_time tau <= close(i) (the reducer's own
    last-snapshot-at-or-before-close law); a None at bucket i means no
    admissible snapshot for that bucket (the freshest available snapshot
    would be a full bucket stale -- outside the frozen +/-30 min endpoint
    tolerance).

    Warmup-extended authority (A8 remediation r2): ``oi`` may carry MORE
    slots than the S0 grid -- the full warmup+S0 cache the loader returned
    under the family spec's alignment hints.  The fixed warmup offset is
    ``warmup = len(oi) - len(rows)`` (714 = 119 x 6 on the corrected real
    cache): S0 ordinal i reads its own endpoint at ``w = i + warmup`` and
    its 24h-ago denominator at ``w - h4_per_day``, and its trailing
    ``window_closes`` quantile window is the strictly-past slots
    ``r_oi[w - window_closes : w]`` -- so EARLY-S0 decisions consume
    pre-S0 warmup slots (both the denominator and the window reach back
    past the S0 start; that is the remediation's entire point).  A short
    window (``w < window_closes``) is an honest warmup None, never a
    partial quantile.  With ``len(oi) == len(rows)`` (no warmup) every
    index degenerates to the legacy S0-only arithmetic byte-identically.

    r_OI(T) = OI(T)/OI(T-24h) - 1 with BOTH endpoints present; otherwise
    the frozen substitution "undefined = 0" applies.  No value at a bucket
    AFTER its close can ever enter (the decision at S0 ordinal i reads
    only endpoint buckets w and w-6 for the endpoints and the
    strictly-past window [w-window_closes, w-1] for the threshold).

    Event(T) = 1 iff r_OI(T) <= rolling P(oi_percentile) of the PRIOR
    window_closes H4 closes AND R_24h(T) = last_price(T)/last_price(T-24h)
    - 1 < 0 (panel-side 24h lookback stays S0-only: the panel has no
    pre-S0 rows, so S0 ordinals < h4_per_day cannot fire).  The rolling
    quantile is numpy.percentile linear interpolation (the
    registry-standard convention pin).

    One position per symbol: an event firing while a position is open is
    IGNORED (series 0.0) and the book re-arms only after flat -- decisions
    at most ``holding_buckets`` closes after a taken event collide with its
    open window (entry fill at t+1 vwap .. exit fill at t+1+holding vwap),
    so the taken set is pairwise >= h4_per_day apart for the frozen 24h
    book.  Series[i] (S0-aligned, length len(rows)) = +1.0 at a TAKEN
    event (desired long over the bucket that follows -- the driver's
    one-bar lag fills at bucket i+1's published VWAP), 0.0 elsewhere,
    None before the quantile window exists (honest warmup; decisions
    themselves remain S0-only -- the fold force-flat law is untouched).
    Also returns ALL gate-fired event closes (suppressed ones included,
    S0 ordinals) -- the sham's "+/-3 days of a true event" exclusion set.
    """
    n = len(rows)
    if len(oi) < n:
        raise ValueError(
            f"OICASCADE: endpoint OI series length {len(oi)} is shorter "
            f"than the H4 grid {n}; refusing (the warmup-extended "
            "authority must cover the full S0 grid)"
        )
    warmup = len(oi) - n
    closes = [_oic_bucket_close_ms(str(r["hour_utc"])) for r in rows]
    _oic_check_grid_regular(closes)
    back = h4_per_day  # 24h-ago bucket offset on the regular grid
    r_oi: List[float] = []
    for k in range(len(oi)):  # full warmup+S0 authority
        j = k - back
        if j >= 0 and oi[k] is not None and oi[j] is not None:
            r_oi.append(float(oi[k]) / float(oi[j]) - 1.0)
        else:
            r_oi.append(0.0)  # frozen "undefined = 0" substitution
    r_24: List[Optional[float]] = []
    for i in range(n):
        j = i - back
        if j >= 0:
            prev = float(rows[j]["last_price"])
            r_24.append(
                float(rows[i]["last_price"]) / prev - 1.0 if prev > 0.0 else None
            )
        else:
            r_24.append(None)
    series: List[Optional[float]] = [None] * n
    events: List[int] = []
    last_taken: Optional[int] = None
    for i in range(n):
        w = i + warmup  # S0 ordinal i lives at authority slot w
        if w < window_closes:
            continue  # honest warmup: the window does not exist yet
        p = float(np.percentile(r_oi[w - window_closes : w], oi_percentile))
        if (
            r_oi[w] <= p
            and r_24[i] is not None
            and r_24[i] < 0.0
        ):
            events.append(i)
            if last_taken is None or i - last_taken > holding_buckets:
                series[i] = 1.0
                last_taken = i
            else:
                series[i] = 0.0  # event while open: ignored, no pyramiding
        else:
            series[i] = 0.0
    return series, events


def _oic_endpoint_or_refuse(
    endpoint: Optional[Mapping[str, Sequence[Optional[float]]]],
    panels: Mapping[str, Sequence[Mapping[str, Any]]],
) -> None:
    if endpoint is None:
        raise ValueError(
            "OICASCADE formulas require the reduced OI endpoint series "
            "(driver passes endpoint=... from the arm's endpoint_series "
            "path); refusing to approximate the OI-collapse gate from "
            "panel columns alone"
        )
    missing = [s for s in panels if s not in endpoint]
    if missing:
        raise ValueError(f"OICASCADE endpoint series lacks symbols {missing}")


def _oic_purged_bucket_days(n_days: int) -> frozenset:
    """Mirror of the driver's 1-day purge (run_v17_cell.purged_day_indices):
    +/-1 full UTC day around each internal fold boundary at floor(i*N/3)."""
    if n_days < 3:
        raise ValueError(f"cannot form 3 folds from {n_days} days")
    edges = [i * n_days // 3 for i in range(3)] + [n_days]
    purged = {edges[1] - 1, edges[1], edges[2] - 1, edges[2]}
    return frozenset(p for p in purged if 0 <= p < n_days)


@register("OICASCADE.anchor", example_only=False)
def oicascade_anchor(
    panels: Mapping[str, Sequence[Mapping[str, Any]]],
    params: Mapping[str, Any],
    *,
    endpoint: Optional[Mapping[str, Sequence[Optional[float]]]] = None,
) -> Dict[str, List[Optional[float]]]:
    """V17-A6-P2-OICASCADE anchor: bottom-decile 24h OI collapse AND
    negative 24h panel return -> LONG 24h.

    Frozen anchor parameters (proposal section ``anchor``): gate at the
    trailing-120d P10 of r_OI_24h (window_closes 720, strictly-past), R_24h
    < 0; entered at the NEXT H4 bucket's VWAP (driver lag 0 + fill_price
    vwap), exit at the first bucket whose close >= T + 24h => exit span
    holding_buckets 5 on the H4 grid (entry bucket t+1, exit bucket t+6:
    exactly the buckets whose VWAPs the frozen text fills at).  Long-only
    +1, one position per symbol, overlapping events ignored.
    """
    _oic_endpoint_or_refuse(endpoint, panels)
    pct, win, holding, per_day = _oic_common_params(params)
    return {
        sym: _oic_gate(
            rows,
            endpoint[sym],
            oi_percentile=pct,
            window_closes=win,
            holding_buckets=holding,
            h4_per_day=per_day,
        )[0]
        for sym, rows in panels.items()
    }


@register("OICASCADE.neighbour", example_only=False)
def oicascade_neighbour(
    panels: Mapping[str, Sequence[Mapping[str, Any]]],
    params: Mapping[str, Any],
    *,
    endpoint: Optional[Mapping[str, Sequence[Optional[float]]]] = None,
) -> Dict[str, List[Optional[float]]]:
    """V17-A6-P2-OICASCADE neighbour: frozen (P5, 48h) variant.

    Same mechanism, frozen neighbour parameters (proposal section
    ``neighbour``): gate at trailing-120d P5 of r_OI_24h with 48h holding
    => exit span holding_buckets 11 (entry t+1, exit t+12 = the first
    bucket close >= T + 48h); identical long direction, fills and costs.
    Roughly half the events with twice the holding.
    """
    _oic_endpoint_or_refuse(endpoint, panels)
    pct, win, holding, per_day = _oic_common_params(params)
    return {
        sym: _oic_gate(
            rows,
            endpoint[sym],
            oi_percentile=pct,
            window_closes=win,
            holding_buckets=holding,
            h4_per_day=per_day,
        )[0]
        for sym, rows in panels.items()
    }


@register("OICASCADE.control", example_only=False)
def oicascade_control(
    panels: Mapping[str, Sequence[Mapping[str, Any]]],
    params: Mapping[str, Any],
    *,
    endpoint: Optional[Mapping[str, Sequence[Optional[float]]]] = None,
) -> Dict[str, List[Optional[float]]]:
    """V17-A6-P2-OICASCADE control: randomized-event-time sham (frozen).

    Frozen control mechanics (proposal section ``control``), verbatim:
    with ``numpy.random.default_rng(1717)`` (seed pinned to the frozen
    1717; ONE fresh generator per symbol -- the sham is per-symbol, so
    each symbol's stream is a pure function of the seed and its own true
    event set), draw per symbol the SAME number of 24h LONG windows as the
    anchor book's taken windows, at H4 closes sampled uniformly over S0,
    EXCLUDING (redraw on collision, rejection sampling):
      * closes inside the +/-1-day fold purge zones (the driver's frozen
        purged UTC days, mirrored by ``_oic_purged_bucket_days``);
      * closes within +/-3 days of ANY true gate-fired event of that
        symbol (18 H4 buckets);
      * closes closer than 24h (6 buckets) to an already-accepted sham
        window (the anchor's own no-pyramiding geometry: taken events are
        pairwise >= 6 buckets apart).
    Direction always +1; identical next-H4-VWAP fills, once-per-fill
    tier-2.0 costs and force-flat law (the driver's).  This severs the
    conditioning link (OI collapse + down-move) while preserving
    unconditional long exposure; per G11, if the sham earns the same
    (positive) sign with |sham exp| >= 0.5 x |anchor exp| the family DIES.
    No warmup None: the placebo consumes no rolling statistics of its own
    (the true-event set comes from the anchor gate).  An exhausted draw
    space is a hard error (fail closed, never a shortfall in windows).
    """
    _oic_endpoint_or_refuse(endpoint, panels)
    pct, win, holding, per_day = _oic_common_params(params)
    seed = int(params["seed"])
    if seed != OIC_SHAM_SEED:
        raise ValueError(
            f"OICASCADE.control seed must be the frozen 1717, got {seed}"
        )
    exclusion = int(params.get("event_exclusion_days", OIC_SHAM_EVENT_EXCLUSION_DAYS))
    if exclusion < 0:
        raise ValueError(f"event_exclusion_days must be >= 0, got {exclusion}")
    max_attempts = int(
        params.get("max_draw_attempts", OIC_MAX_DRAW_ATTEMPTS_PER_WINDOW)
    )
    out: Dict[str, List[Optional[float]]] = {}
    for sym, rows in panels.items():
        gate, events = _oic_gate(
            rows,
            endpoint[sym],
            oi_percentile=pct,
            window_closes=win,
            holding_buckets=holding,
            h4_per_day=per_day,
        )
        needed = sum(1 for v in gate if v == 1.0)  # anchor TAKEN windows
        n = len(rows)
        if needed == 0:
            out[sym] = [0.0] * n  # nothing to match: the honest mirror
            continue
        closes = [_oic_bucket_close_ms(str(r["hour_utc"])) for r in rows]
        _oic_check_grid_regular(closes)
        first_start = closes[0] - _H4_MS
        day_of = [(c - _H4_MS - first_start) // _DAY_MS for c in closes]
        purged_days = _oic_purged_bucket_days(
            len({str(r["day_utc"]) for r in rows})
        )
        excl_buckets = exclusion * per_day
        rng = np.random.default_rng(seed)  # frozen seed, fresh per symbol
        accepted: List[int] = []
        attempts = 0
        budget = max_attempts * needed
        while len(accepted) < needed:
            if attempts >= budget:
                raise ValueError(
                    f"OICASCADE.control[{sym}]: sham draw space exhausted "
                    f"({attempts} draws for {needed} windows); refusing "
                    "(fail closed)"
                )
            attempts += 1
            k = int(rng.integers(0, n))
            if day_of[k] in purged_days:
                continue  # +/-1-day fold purge zone
            if any(abs(k - e) <= excl_buckets for e in events):
                continue  # within +/-3 days of a true event
            if any(abs(k - a) < per_day for a in accepted):
                continue  # overlaps an accepted 24h sham window
            accepted.append(k)
        series: List[Optional[float]] = [0.0] * n
        for k in accepted:
            series[k] = 1.0
        out[sym] = series
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
    "OIC_H4_PER_DAY",
    "OIC_MAX_DRAW_ATTEMPTS_PER_WINDOW",
    "OIC_SHAM_EVENT_EXCLUSION_DAYS",
    "OIC_SHAM_SEED",
    "WKND_SHAM_SEED",
    "WKND_WEEKDAYS",
    "WKND_WEEK_ANCHOR_WEEKDAY",
    "attn_anchor",
    "attn_control",
    "attn_neighbour",
    "day_index_from_origin",
    "example_h1_vwap_revert",
    "is_example_only",
    "oicascade_anchor",
    "oicascade_control",
    "oicascade_neighbour",
    "register",
    "registered_ids",
    "resolve",
    "silres_anchor",
    "silres_control",
    "silres_neighbour",
    "sign",
    "wkndliq_anchor",
    "wkndliq_control",
    "wkndliq_neighbour",
]
