"""COMMODITIES-NG1 frozen decision-rule machinery (family COMMNG1-A4-P2).

Semantic provenance (P-12): the decision-STATE machinery below is pinned
VERBATIM to the committed D2 measurement code
``research/control/commodities_ng1_run/d2/measure_novelty.py``
(``percentile_tail`` + ``state_a4p2``), the exact machinery whose
decision-state correlations carried the S freeze.  The D2 file is frozen
run evidence and is deliberately NOT imported here (assets never depend
on control-run scripts); instead this module re-states the identical
semantics and the I tests pin them with hand-computed synthetic series.

Frozen rule family (S freeze section2, D1 decision_rule_family,
verbatim intent): hold the crowd-carry direction while the official
geometry sits in a symmetric extreme tail and no opposing
positioning-flow trigger has fired, up to ``h_max`` weekly closes; on
trigger, terminate (flip under the same frozen convention -- frozen at
NO flip: trigger terminates to flat, the conservative D2 reading; a
direct transition into the OPPOSITE tail re-arms symmetrically);
symmetric in the two tails.

Geometry and flows use ONLY committed P0 report counts:

    g        = ((noncomm_long - noncomm_short)
                - (comm_long - comm_short)) / open_interest
    spec_net = noncomm_long - noncomm_short          (the crowd side)

NO price input enters the anchor state or trigger (D1 information
claim).  The price-only shadow (``price_only_positions``) is the
designated killer that replaces BOTH the state and the trigger with
price-only analogues (S freeze section6): persistence state = trailing
weekly RAW displacement beyond a displacement percentile tail; trigger
= opposing weekly RAW displacement >= ``tau_price_weekly_a4p2``
(D2 frozen default 0.02).
"""

from __future__ import annotations

SCHEMA = "commodities_ng1/runners/rule@1"

#: Frozen geometry keys consumed from a chain row (chain.py builds them
#: from the committed P0 count fields only).
GEOMETRY_KEY = "g"
SPEC_NET_KEY = "spec_net"


def sign(v) -> float:
    """Frozen sign convention (+1 / -1 / 0.0), identical to D2."""
    if v is None:
        return 0.0
    if v > 0:
        return 1.0
    if v < 0:
        return -1.0
    return 0.0


def percentile_tail(values: list, i: int, window: int, cut: float):
    """Symmetric tail bucket of ``values[i]`` inside the trailing
    ``window`` observations ENDING at i (INCLUSIVE), by percentile rank:
    ``rank = (# window values <= x) / n``.

    ``'lo'`` when ``rank <= cut``; ``'hi'`` when ``rank >= 1 - cut``;
    else ``None``.  Requires the FULL window; ``None`` entries in the
    window (or at i) make the bucket ``None`` (warmup-safe).  A bucket
    satisfying both cuts (only possible when ``cut >= 0.5``) is refused
    as degenerate by returning ``None`` -- identical to the D2 committed
    definition the S freeze froze.
    """
    if i + 1 < window or i >= len(values):
        return None
    w = values[i - window + 1:i + 1]
    x = values[i]
    if x is None or any(v is None for v in w):
        return None
    n = len(w)
    rank = sum(1 for v in w if v <= x) / n
    lo = rank <= cut
    hi = rank >= (1.0 - cut)
    if lo and hi:
        return None
    if lo:
        return "lo"
    if hi:
        return "hi"
    return None


def _run_carry_state_machine(series: list, side_at_entry: list,
                             window: int, cut: float, tau: float,
                             h_max: int, trigger_f) -> list:
    """The frozen continuation-until-trigger state machine.

    Shared shape for the anchor (official geometry) and the price-only
    shadow (price analogues): entry on a fresh TRANSITION into a tail
    bucket; direction = ``side_at_entry[i]``; exit on (a) an opposing
    trigger event of magnitude >= tau, (b) leaving the entered tail, or
    (c) the h_max bound; NO flip on trigger (terminate to flat); a fresh
    transition into a tail re-arms.

    ``series[i]`` is the tailed coordinate (may contain None);
    ``side_at_entry[i]`` the frozen side coordinate at i;
    ``trigger_f(i)`` the current trigger flow value at row i (may be
    None when undefined -> no trigger).
    """
    n = len(series)
    pos = [0.0] * n
    held_d = 0.0
    entered_bucket = None
    entry_i = -1
    prev_bucket = None
    for i in range(n):
        b = percentile_tail(series, i, window, cut)
        if held_d != 0.0:
            f = trigger_f(i)
            trigger = (f is not None and sign(f) == -held_d
                       and abs(f) >= tau)
            left_tail = (b != entered_bucket)
            bound = (i - entry_i) >= h_max
            if trigger or left_tail or bound:
                held_d = 0.0
            else:
                pos[i] = held_d
        if held_d == 0.0 and b is not None and b != prev_bucket:
            d = sign(side_at_entry[i])
            if d != 0.0:
                held_d = d
                entered_bucket = b
                entry_i = i
                pos[i] = d
        prev_bucket = b
    return pos


def _diff_trigger(series: list):
    """Trigger flow f(i) = series[i] - series[i-1] (0.0 at i == 0),
    matching the anchor's first-difference-of-geometry law."""
    def f(i: int):
        if i <= 0:
            return 0.0
        a, b = series[i - 1], series[i]
        if a is None or b is None:
            return None
        return b - a
    return f


def geometry(row: dict) -> float:
    """Official geometry g of one committed report row.

    ``g = ((noncomm_long - noncomm_short)
           - (comm_long - comm_short)) / open_interest``
    -- committed P0 counts only (D2 representation identity).
    """
    spec_net = row["noncomm_long"] - row["noncomm_short"]
    comm_net = row["comm_long"] - row["comm_short"]
    return (spec_net - comm_net) / row["open_interest"]


def crowd_carry_positions(chain: list, params: dict) -> list:
    """ANCHOR decision series of the frozen family (one position per
    weekly chain row; +1/-1 held, 0.0 flat).

    ``params`` keys (the frozen arm parameters, verbatim from the S
    freeze arm_config): ``percentile_window_weeks_w``,
    ``tail_q_lo``, ``tail_q_hi``, ``trigger_tau_geometry``,
    ``carry_bound_weeks_h_max``.  The symmetric tail convention uses
    ``cut = tail_q_lo`` (= 1 - ``tail_q_hi``; the freeze asserts
    symmetry).

    Entry side = sign of the speculative net (the crowd side; frozen).
    Trigger = opposing weekly geometry flow (first difference of g)
    with magnitude >= tau.  NO price input anywhere.
    """
    cut = float(params["tail_q_lo"])
    if abs((1.0 - float(params["tail_q_hi"])) - cut) > 1e-12:
        raise ValueError(
            "asymmetric tail cuts refuse the frozen symmetric family "
            f"(q_lo={params['tail_q_lo']}, q_hi={params['tail_q_hi']})")
    g = [row["g"] for row in chain]
    side = [row["spec_net"] for row in chain]
    return _run_carry_state_machine(
        series=g,
        side_at_entry=side,
        window=int(params["percentile_window_weeks_w"]),
        cut=cut,
        tau=float(params["trigger_tau_geometry"]),
        h_max=int(params["carry_bound_weeks_h_max"]),
        trigger_f=_diff_trigger(g),
    )


def displacement_series(chain: list) -> list:
    """Weekly RAW displacement series of the chain's readable closes:
    ``r[i] = cend_close[i] / cend_close[i-1] - 1`` (None where a
    readable close is missing).  RAW close only -- the trading surface
    (P0 census convention); no adjustment enters.
    """
    closes = [row.get("cend_close") for row in chain]
    out: list = [None] * len(chain)
    for i in range(1, len(chain)):
        a, b = closes[i - 1], closes[i]
        if a is not None and b is not None and a > 0 and b > 0:
            out[i] = b / a - 1.0
    return out


def price_only_positions(chain: list, params: dict) -> list:
    """PRICE_ONLY_SHADOW decision series (designated killer; S freeze
    section6): the SAME hold-until-trigger shape and the same symbolic
    parameters (w, tails, h_max) with BOTH the state and the trigger
    replaced by price-only analogues:

    - persistence state = trailing weekly RAW displacement beyond a
      displacement percentile tail (same percentile_tail machinery);
    - entry side = sign of the current weekly displacement (the price
      crowd direction);
    - trigger = opposing weekly RAW displacement of magnitude >=
      ``tau_price_weekly_a4p2`` (D2 frozen default 0.02, frozen in the
      S freeze section6 spec text);
    - same left-tail exit and h_max bound; NO CoT input whatsoever.
    """
    cut = float(params["tail_q_lo"])
    r = displacement_series(chain)
    return _run_carry_state_machine(
        series=r,
        side_at_entry=r,
        window=int(params["percentile_window_weeks_w"]),
        cut=cut,
        tau=float(params.get("tau_price_weekly_a4p2", 0.02)),
        h_max=int(params["carry_bound_weeks_h_max"]),
        trigger_f=lambda i: r[i],
    )


def release_clock_positions(n_rows: int, fixed_sign: float = 1.0) -> list:
    """RELEASE_CLOCK_SHADOW decision series (designated killer):
    identical holding shape and execution, FIXED direction sign, no
    state and no trigger -- every grid instant pooled (the bare
    Friday-release weekly clock).  The fixed sign is frozen at +1 (long
    the ETP leg every week); the pooled verdict of a fixed-sign clock
    is invariant to the sign choice up to the sign flip of the edge.
    """
    if fixed_sign not in (1.0, -1.0):
        raise ValueError("fixed sign must be +1/-1")
    return [float(fixed_sign)] * int(n_rows)


def shifted_release_positions(anchor_positions: list,
                              k: int = 4) -> list:
    """SHIFTED_RELEASE_PLACEBO decision series (designated killer):
    the identical state-and-trigger machinery fed reports ``k``
    release-instants OLDER than the PIT-visible one.  Exactly: the
    anchor machinery runs over the report chain, and decision row i
    reads the state as of report ``i - k`` -- ``pos[i] = pos_anchor[i-k]``
    (0.0 for i < k).  Preserves the weekly clock and the marginal
    geometry while destroying release-aligned information.

    ``k`` is FROZEN at 4 by the S freeze (the D1-declared minimum
    ">= 4 releases"; the floor is the declared a-priori value).
    """
    k = int(k)
    if k < 1:
        raise ValueError("stale-release shift k must be >= 1")
    n = len(anchor_positions)
    # decision row i reads the state as of report i-k: pos[i] = anchor[i-k]
    return [0.0] * k + [anchor_positions[i - k] for i in range(k, n)]


def clairvoyant_positions(chain: list, params: dict) -> list:
    """CLAIRVOYANT ceiling arm (diagnostic; Q-4, P-15): the same
    hold-until-trigger shape, but bucket membership is granted
    full-sample knowledge no live PIT process could have -- percentile
    ranks over the FULL sample instead of the trailing window.  The
    entry side stays the frozen convention (sign of spec_net) and the
    trigger machinery stays the live first-difference law, so the
    oracle bound isolates the bucket-membership knowledge (the entry
    condition).  Ceiling reference only: its numbers are smoke-class
    (kill + disclose, never select)."""
    cut = float(params["tail_q_lo"])
    g = [row["g"] for row in chain]
    side = [row["spec_net"] for row in chain]
    known = [v for v in g if v is not None]
    n_known = len(known)
    if n_known == 0:
        return [0.0] * len(chain)

    def full_sample_bucket(v):
        if v is None:
            return None
        rank = sum(1 for x in known if x <= v) / n_known
        lo = rank <= cut
        hi = rank >= (1.0 - cut)
        if lo and hi:
            return None
        if lo:
            return "lo"
        if hi:
            return "hi"
        return None

    buckets = [full_sample_bucket(v) for v in g]
    trigger_f = _diff_trigger(g)
    return _run_state_machine_from_buckets(
        buckets=buckets,
        side_at_entry=side,
        tau=float(params["trigger_tau_geometry"]),
        h_max=int(params["carry_bound_weeks_h_max"]),
        trigger_f=trigger_f,
    )


def _run_state_machine_from_buckets(buckets: list, side_at_entry: list,
                                    tau: float, h_max: int,
                                    trigger_f) -> list:
    """The carry state machine over PRE-COMPUTED buckets (the
    clairvoyant's full-sample membership).  Identical transition law to
    ``_run_carry_state_machine``."""
    n = len(buckets)
    pos = [0.0] * n
    held_d = 0.0
    entered_bucket = None
    entry_i = -1
    prev_bucket = None
    for i in range(n):
        b = buckets[i]
        if held_d != 0.0:
            f = trigger_f(i)
            trigger = (f is not None and sign(f) == -held_d
                       and abs(f) >= tau)
            left_tail = (b != entered_bucket)
            bound = (i - entry_i) >= h_max
            if trigger or left_tail or bound:
                held_d = 0.0
            else:
                pos[i] = held_d
        if held_d == 0.0 and b is not None and b != prev_bucket:
            d = sign(side_at_entry[i])
            if d != 0.0:
                held_d = d
                entered_bucket = b
                entry_i = i
                pos[i] = d
        prev_bucket = b
    return pos
