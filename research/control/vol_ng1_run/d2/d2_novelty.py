"""VOL-NG1 D2 novelty measurement library (task vol-ng1-d2-novelty).

The DECISIVE SELECTION GATE of the cycle: for each of the four D1
proposals (``research/control/vol_ng1_run/d1/proposals/*.json``) the
five ancestry kill-shadows named in the proposal's own
``ancestry_risk_statement`` are reconstructed ON THE PROPOSAL'S OWN
DECLARED REPRESENTATION (same grid, same bookable instants, same
event-adjusted ETP consumption law) and correlated with the proposal's
own decision-state series.

P-12 LAW (representation before numbers): this file is committed BEFORE
any measurement is run.  It contains the frozen default parameters
(documented below), the shadow-reconstruction definitions, the
representation mapping and the correlation law.  It contains NO
measured numbers: every correlation value lives only in the committed
panel ``d2_novelty_panel.json`` (the second, results commit).

Q-6 NO-PnL LAW: decision-STATE series only.  No returns conditional on
states, no expectancies, no scoring, no PnL numbers anywhere.

FREEZE LAW: all D1 parameters were symbolic.  They are frozen HERE, at
declared neutral defaults, BEFORE any correlation is computed; no
threshold moves after any number is seen.  Each default documents its
neutral-choice basis.  No default is fitted, calibrated or adapted to
the measurement sample in any way (round constants only, or forms
already committed in P0/P1/P2 artifacts).

FAIL-CLOSED LAW: a shadow that cannot be lawfully reconstructed on a
proposal's representation is UNMEASURABLE and the proposal is
VETO-pending unless the shadow is provably inapplicable (documented);
absence is never PASS.  An uncomputable state (warmup, refused tail,
missing session) is INVALID and refused -- never coerced to flat/NULL
and never scored (Q-11).
"""

from __future__ import annotations

import math
from datetime import date

import numpy as np

SCHEMA = "vol_ng1_run/d2_novelty@1"
TASK_ID = "vol-ng1-d2-novelty"
CYCLE_ID = "VOL-NG1"

# --------------------------------------------------------------------------- #
# Frozen decision-axis encodings (declared, pre-measurement)
# --------------------------------------------------------------------------- #
#: Common axis for A4-P1 / A4-P2 / A5-P1 (and the per-leg shadow axis):
#: the vol-complex position implied by a decision.
SHORT_VOL = 1.0    # long the short-vol leg(s)
FLAT = 0.0
LONG_VOL = -1.0    # long the long-vol leg(s)

#: A5-P2 bucket-allocation axis, encoded on the SAME poles by the
#: proposal's own declared semantics: its front bucket carries the
#: short-vol roll-carry / crowded-seller complex and its mid bucket
#: carries the institutional protection buyer, so front == the
#: short-vol pole and mid == the long-vol pole.
FRONT_BUCKET = 1.0
MID_BUCKET = -1.0

# --------------------------------------------------------------------------- #
# Frozen default parameters (P-12 freeze -- BEFORE any rho exists).
# Every value is a neutral round constant or a constant already
# committed in a P0/P1/P2 artifact; none is derived from the sample.
# --------------------------------------------------------------------------- #
FROZEN_DEFAULTS: dict = {
    # -- A4 slope family (shared functional) --------------------------------
    # Signed log-ratio combination of ALL THREE same-session tenor
    # closes: the average pairwise upward-slope of the term structure
    # (positive == contango).  Uses VIX9D, VIX and VIX3M exactly as the
    # D1 state_definition_symbolic declares.
    "slope_functional_form": (
        "S_t = 0.5*(ln(VIX_t/VIX9D_t) + ln(VIX3M_t/VIX_t))"),
    # Bucket thresholds {steep, mild, flat, inverted}: neutral round
    # constants on the log-spread scale (~1% and ~5% curve steepness).
    "theta_1": 0.02,
    "theta_2": 0.05,
    # Bucket -> position map (declared monotone in carry): deep or
    # moderate contango carries positive roll to the short-vol side;
    # near-flat carries ~none; inversion flips long-vol.
    "bucket_action_map": {"steep": SHORT_VOL, "mild": SHORT_VOL,
                          "flat": FLAT, "inverted": LONG_VOL},
    # A4-P1 minimum holding h_min: neutral round default limiting round
    # trips (5 sessions), per the D1 symbolic h_min.
    "h_min_sessions": 5,
    # A4-P2 second difference, latch and threshold: pure sign test at
    # zero threshold (the neutral threshold) recognised after m=3
    # consecutive same-sign sessions (the neutral smallest persistent
    # run); R is latch-coincident (position held exactly while the
    # recognised regime persists).
    "second_difference_form": "D_t = S_t - 2*S_(t-1) + S_(t-2)",
    "a4p2_d_threshold": 0.0,
    "a4p2_latch_m_sessions": 3,
    "a4p2_regime_action_map": {
        "accelerating_steepening": SHORT_VOL,
        "decelerating": FLAT,
        "accelerating_flattening": LONG_VOL},
    # -- A5 spread family ----------------------------------------------------
    # Standardization: PIT-clean expanding-window z-score over the
    # common grid up to and including t (population std, ddof=0),
    # requiring >= 63 prior valid observations (63 < the committed 252
    # warmup, so every bookable instant is computable).  No look-ahead.
    "standardization_form": ("expanding z-score over the common grid "
                             "up to and including t (ddof=0)"),
    "standardization_min_history": 63,
    # Realized side of the short bucket: the P2-DECLARED C7 proxy,
    # committed (not frozen here): trailing 21-common-grid-session
    # realized volatility of the event-adjusted VXX close, annualized
    # x sqrt(252) (feasibility.py C7 constants).
    # A5-P2 mid-bucket extension (frozen HERE at D2, before any rho):
    # the SAME declared proxy family on the mid reference leg VXZ (the
    # mid-bucket sibling of the declared short reference leg VXX; both
    # are VIX-mid-term-futures legs of the event-adjusted layer).
    "a5p2_mid_reference_leg": "VXZ",
    # Spread-state thresholds: half a standardized sigma, the neutral
    # round default for z-scored states.
    "a5p1_spread_threshold": 0.5,
    "a5p1_hysteresis_sessions": 2,
    "a5p1_state_action_map": {"expanded": SHORT_VOL, "neutral": FLAT,
                              "compressed": LONG_VOL},
    "a5p2_asym_threshold": 0.5,
    "a5p2_latch_sessions": 2,
    "a5p2_state_action_map": {"short_extreme": FRONT_BUCKET,
                              "aligned": FLAT,
                              "mid_extreme": MID_BUCKET},
    # -- ancestry kill-shadow forms ------------------------------------------
    # (a) v16: short-horizon close-displacement fade on the
    #     event-adjusted legs: z of the close vs its trailing 5-session
    #     window (population std); fade beyond 1 sigma.
    "v16_window_sessions": 5,
    "v16_z_threshold": 1.0,
    # (b) v17: position-level conditioning on vol-complex LEVEL states,
    #     mapped to the granted VIX index level: short-vol below 20,
    #     long-vol above 30 (neutral round constants on the VIX scale).
    "v17_level_low": 20.0,
    "v17_level_high": 30.0,
    # (c) dvol shock: large-jump reaction mapped to VIX index jumps:
    #     |daily VIX return| >= 5% flips the position AGAINST the
    #     jump's sign (buy protection after a vol spike, sell vol after
    #     a vol collapse) and holds the reaction for 3 grid sessions;
    #     later shocks refresh the window.
    "dvol_jump_threshold": 0.05,
    "dvol_hold_sessions": 3,
    # (d) momentum: trailing 63-common-grid-session return sign on the
    #     event-adjusted legs, momentum-CHASE form (positive leg
    #     momentum -> long the leg == the long-vol pole).
    "momentum_lookback_sessions": 63,
    # (e) generic dow/tue: calendar-clock position, long the short-vol
    #     pole on Tuesday sessions only (the frozen calendar slot).
    "dow_tue_weekday": 1,
    # -- gate law -------------------------------------------------------------
    "margin_abs_rho": 0.20,
    "min_valid_overlap_instants": 200,
}

#: Leg subsets per proposal representation (frozen mapping; buckets are
#: the cost contract's own committed bucket assignment).
SHORT_BUCKET_LEGS = ("SVXY", "UVXY", "VIXY", "VXX")
MID_BUCKET_LEGS = ("VIXM", "VXZ")
ALL_SIX_LEGS = SHORT_BUCKET_LEGS + MID_BUCKET_LEGS

PROPOSAL_LEG_SUBSETS = {
    "VOLNG1-A4-P1": SHORT_BUCKET_LEGS,
    "VOLNG1-A4-P2": SHORT_BUCKET_LEGS,
    "VOLNG1-A5-P1": SHORT_BUCKET_LEGS,
    "VOLNG1-A5-P2": ALL_SIX_LEGS,
}

PROPOSAL_AXIS = {
    "VOLNG1-A4-P1": "short_vol_pos_long_vol_neg",
    "VOLNG1-A4-P2": "short_vol_pos_long_vol_neg",
    "VOLNG1-A5-P1": "short_vol_pos_long_vol_neg",
    "VOLNG1-A5-P2": "front_bucket_pos_mid_bucket_neg",
}

SHADOW_IDS = ("v16_close_displace_fade", "v17_oi_level", "dvol_shock",
              "momentum_63s", "generic_dow_tue")

#: The frozen mapping of each shadow onto a proposal representation.
SHADOW_MAPPINGS: dict = {
    "v16_close_displace_fade": (
        "short-horizon close-displacement fade: per event-adjusted leg, "
        "z = (close_t - mean(trailing {w} closes)) / stdev(trailing {w} "
        "closes, ddof=0); position +1 (short-vol pole) if z >= +{zthr}, "
        "-1 (long-vol pole) if z <= -{zthr}, else flat; INVALID inside "
        "the window or when the window stdev is 0"),
    "v17_oi_level": (
        "position-level conditioning on vol-complex LEVEL states mapped "
        "to the granted VIX index close: +1 (short-vol pole) when "
        "VIX_t < {lo}, -1 (long-vol pole) when VIX_t > {hi}, else flat"),
    "dvol_shock": (
        "large-jump reaction mapped to VIX index jump events: when "
        "|VIX_t/VIX_(t-1) - 1| >= {jthr}, hold position -sign(jump) for "
        "{hold} grid sessions (buy protection after a vol spike, sell "
        "vol after a vol collapse); later shocks refresh the window; "
        "flat outside reaction windows; INVALID before the first "
        "previous session"),
    "momentum_63s": (
        "trailing {lb}-common-grid-session return sign on the "
        "event-adjusted legs, chase form: position -sign(c_t/c_(t-{lb}) "
        "- 1) (positive leg momentum -> long the leg == long-vol pole), "
        "0 at exactly zero; INVALID inside the lookback"),
    "generic_dow_tue": (
        "calendar-clock position: +1 (short-vol pole) on Tuesday "
        "sessions (weekday == {dow}), flat otherwise; always computable "
        "on any grid session"),
}


class D2NoveltyError(Exception):
    """Fail-closed D2 novelty state: nothing inferred, nothing repaired."""


# --------------------------------------------------------------------------- #
# correlation law (hand-computable, no external stats dependency)
# --------------------------------------------------------------------------- #
def pearson(x: list[float], y: list[float]) -> float | None:
    """Pearson product-moment correlation; None when either side has
    zero variance (structurally undefined, never coerced)."""
    if len(x) != len(y) or not x:
        raise D2NoveltyError("pearson needs equal-length nonempty series")
    xa = np.asarray(x, dtype=float)
    ya = np.asarray(y, dtype=float)
    xc = xa - xa.mean()
    yc = ya - ya.mean()
    denom = math.sqrt(float(xc @ xc) * float(yc @ yc))
    if denom == 0.0:
        return None
    return float((xc @ yc) / denom)


def average_ranks(values: list[float]) -> np.ndarray:
    """Ranks with average tie handling (1-based, mergesort-stable)."""
    a = np.asarray(values, dtype=float)
    order = np.argsort(a, kind="mergesort")
    sa = a[order]
    ranks = np.empty(len(a), dtype=float)
    i = 0
    while i < len(a):
        j = i
        while j + 1 < len(a) and sa[j + 1] == sa[i]:
            j += 1
        ranks[order[i:j + 1]] = (i + j) / 2.0 + 1.0
        i = j + 1
    return ranks


def spearman(x: list[float], y: list[float]) -> float | None:
    """Spearman rank correlation = Pearson on average ranks; None when
    either rank series has zero variance."""
    return pearson(list(average_ranks(x)), list(average_ranks(y)))


def pooled_abs(spearman_r: float | None, pearson_r: float | None) -> float | None:
    """Pooled |rho| per shadow = max(|spearman|, |pearson|); None when
    both are structurally undefined (degenerate zero-variance pair)."""
    vals = [abs(v) for v in (spearman_r, pearson_r) if v is not None]
    return max(vals) if vals else None


# --------------------------------------------------------------------------- #
# pure frozen decision machines (unit-testable, hand-computable)
# --------------------------------------------------------------------------- #
def slope_state(s9: float, vix: float, vix3m: float) -> float:
    """The frozen A4 slope functional (positive == contango)."""
    for v in (s9, vix, vix3m):
        if v is None or v <= 0:
            raise D2NoveltyError("slope functional needs positive closes")
    return 0.5 * (math.log(vix / s9) + math.log(vix3m / vix))


def bucket4(s: float, theta_1: float, theta_2: float) -> str:
    """The frozen 4-bucket law: inverted / flat / mild / steep."""
    if s < 0.0:
        return "inverted"
    if s < theta_1:
        return "flat"
    if s < theta_2:
        return "mild"
    return "steep"


def min_hold_filter(raw_by_date: dict[str, float | None],
                    grid: list[str], h_min: int) -> dict[str, float | None]:
    """Frozen h_min minimum-holding law: a position change is adopted
    only when >= h_min grid sessions have elapsed since the last
    adopted change.  INVALID instants pass INVALID through and do not
    touch the machine."""
    out: dict[str, float | None] = {}
    cur: float | None = None
    last_change_i = -10**9
    for i, d in enumerate(grid):
        raw = raw_by_date.get(d, ...)
        if raw is ...:
            raise D2NoveltyError(f"date {d} missing from raw series")
        if raw is None:
            out[d] = None
            continue
        if cur is None:
            cur = float(raw)
            last_change_i = i
        elif float(raw) != cur and (i - last_change_i) >= h_min:
            cur = float(raw)
            last_change_i = i
        out[d] = cur
    return out


def second_difference(series_by_date: dict[str, float | None],
                      grid: list[str]) -> dict[str, float | None]:
    """D_t = S_t - 2 S_(t-1) + S_(t-2); INVALID before two prior
    valid observations (fail-closed, never coerced)."""
    out: dict[str, float | None] = {}
    for i, d in enumerate(grid):
        if i < 2:
            out[d] = None
            continue
        s0, s1, s2 = (series_by_date.get(grid[i - 2]),
                      series_by_date.get(grid[i - 1]),
                      series_by_date.get(d))
        if s0 is None or s1 is None or s2 is None:
            out[d] = None
        else:
            out[d] = s2 - 2.0 * s1 + s0
    return out


def regime_by_run(d_by_date: dict[str, float | None], grid: list[str],
                  m: int, threshold: float) -> dict[str, float | None]:
    """Frozen A4-P2 latch: +1 when the trailing m VALID d-values are
    all > threshold (accelerating steepening), -1 when all <
    -threshold (accelerating flattening), else 0 (decelerating).  Any
    INVALID inside the trailing window -> INVALID (Q-11)."""
    out: dict[str, float | None] = {}
    for i, d in enumerate(grid):
        if i < m - 1:
            out[d] = None
            continue
        window = [d_by_date.get(grid[i - k]) for k in range(m)]
        if any(v is None for v in window):
            out[d] = None
            continue
        if all(v > threshold for v in window):
            out[d] = SHORT_VOL
        elif all(v < -threshold for v in window):
            out[d] = LONG_VOL
        else:
            out[d] = FLAT
    return out


def expanding_z(series_by_date: dict[str, float | None],
                grid: list[str], min_history: int) -> dict[str, float | None]:
    """Frozen standardization: expanding z-score over all valid values
    up to and including t (population std, ddof=0), requiring >=
    min_history VALID observations strictly before t.  No look-ahead;
    zero-variance history -> INVALID (never coerced)."""
    out: dict[str, float | None] = {}
    history: list[float] = []
    for d in grid:
        v = series_by_date.get(d)
        if v is None:
            out[d] = None
            continue
        if len(history) < min_history:
            history.append(float(v))
            out[d] = None
            continue
        arr = np.asarray(history + [float(v)], dtype=float)
        mu = float(arr.mean())
        sd = float(arr.std(ddof=0))
        if sd == 0.0:
            out[d] = None
        else:
            out[d] = (float(v) - mu) / sd
        history.append(float(v))
    return out


def realized_vol(close_by_date: dict[str, float], grid: list[str],
                 lookback: int, annualization: float) -> dict[str, float | None]:
    """The P2-declared C7 proxy family: annualized trailing
    ``lookback``-common-grid-session realized volatility of a series of
    closes (population std of the ``lookback`` daily log returns).
    INVALID until ``lookback``+1 consecutive grid closes exist."""
    out: dict[str, float | None] = {}
    for i, d in enumerate(grid):
        if i < lookback:
            out[d] = None
            continue
        # lookback PRIOR closes (i-lookback .. i-1) + the current close
        window = [close_by_date.get(grid[i - k])
                  for k in range(1, lookback + 1)]
        window.append(close_by_date.get(d))
        if any(v is None for v in window):
            out[d] = None
            continue
        rets = [math.log(window[k + 1] / window[k])
                for k in range(lookback)]
        arr = np.asarray(rets, dtype=float)
        out[d] = float(arr.std(ddof=0)) * math.sqrt(annualization)
    return out


def debounce_latch(raw_by_date: dict[str, float | None], grid: list[str],
                   confirm_sessions: int) -> dict[str, float | None]:
    """Frozen hysteresis latch (A5): a state change from ``cur`` is
    adopted only after the candidate raw state holds on
    ``confirm_sessions`` CONSECUTIVE valid sessions.  INVALID breaks a
    candidate run (consecutive means consecutive-valid)."""
    out: dict[str, float | None] = {}
    cur: float | None = None
    pending: float | None = None
    pending_run = 0
    for d in grid:
        raw = raw_by_date.get(d, ...)
        if raw is ...:
            raise D2NoveltyError(f"date {d} missing from raw state series")
        if raw is None:
            pending = None
            pending_run = 0
            out[d] = None
            continue
        raw = float(raw)
        if cur is None:
            cur = raw
            pending = None
            pending_run = 0
        elif raw == cur:
            pending = None
            pending_run = 0
        elif raw == pending:
            pending_run += 1
            if pending_run >= confirm_sessions:
                cur = raw
                pending = None
                pending_run = 0
        else:
            pending = raw
            pending_run = 1
        out[d] = cur
    return out


def threshold_states(centered_by_date: dict[str, float | None],
                     grid: list[str], threshold: float,
                     high_state: float, low_state: float,
                     mid_state: float) -> dict[str, float | None]:
    """Frozen threshold law on an already-centered state variable:
    > +threshold -> high_state, < -threshold -> low_state, else
    mid_state."""
    out: dict[str, float | None] = {}
    for d in grid:
        v = centered_by_date.get(d)
        out[d] = None if v is None else (
            high_state if v > threshold else
            low_state if v < -threshold else mid_state)
    return out


# --------------------------------------------------------------------------- #
# proposal decision-state builders (frozen-default instantiations)
# --------------------------------------------------------------------------- #
def _close_getter(series: dict[str, float], grid: list[str]) -> dict:
    return {d: series.get(d) for d in grid}


def build_a4p1_state(ctx: dict) -> tuple[dict[str, float | None], dict]:
    """VOLNG1-A4-P1 at frozen defaults: slope buckets + h_min."""
    grid = ctx["grid"]
    s_by_date: dict[str, float | None] = {}
    for d in grid:
        s9 = ctx["index"]["VIX9D"].get(d)
        vx = ctx["index"]["VIX"].get(d)
        v3 = ctx["index"]["VIX3M"].get(d)
        s_by_date[d] = None if None in (s9, vx, v3) else slope_state(
            s9, vx, v3)
    raw_pos: dict[str, float | None] = {}
    bucket_by_date: dict[str, str | None] = {}
    for d in grid:
        s = s_by_date[d]
        if s is None:
            raw_pos[d] = None
            bucket_by_date[d] = None
        else:
            b = bucket4(s, FROZEN_DEFAULTS["theta_1"],
                        FROZEN_DEFAULTS["theta_2"])
            bucket_by_date[d] = b
            raw_pos[d] = FROZEN_DEFAULTS["bucket_action_map"][b]
    state = min_hold_filter(raw_pos, grid,
                            FROZEN_DEFAULTS["h_min_sessions"])
    meta = {"slope_by_date": s_by_date, "bucket_by_date": bucket_by_date}
    return state, meta


def build_a4p2_state(ctx: dict) -> tuple[dict[str, float | None], dict]:
    """VOLNG1-A4-P2 at frozen defaults: second-difference regimes."""
    grid = ctx["grid"]
    s_by_date: dict[str, float | None] = {}
    for d in grid:
        s9 = ctx["index"]["VIX9D"].get(d)
        vx = ctx["index"]["VIX"].get(d)
        v3 = ctx["index"]["VIX3M"].get(d)
        s_by_date[d] = None if None in (s9, vx, v3) else slope_state(
            s9, vx, v3)
    d_by_date = second_difference(s_by_date, grid)
    state = regime_by_run(
        d_by_date, grid, FROZEN_DEFAULTS["a4p2_latch_m_sessions"],
        FROZEN_DEFAULTS["a4p2_d_threshold"])
    return state, {"slope_by_date": s_by_date, "d_by_date": d_by_date}


def _spread_state(ctx: dict, proxy_leg: str) -> dict[str, float | None]:
    """The declared A5 spread functional at frozen defaults:
    expanding-z(VIX close) - expanding-z(realized proxy of leg)."""
    grid = ctx["grid"]
    z_impl = expanding_z(_close_getter(ctx["index"]["VIX"], grid), grid,
                         FROZEN_DEFAULTS["standardization_min_history"])
    rv = realized_vol(ctx["adj"][proxy_leg], grid,
                      ctx["proxy_lookback_sessions"],
                      ctx["proxy_annualization"])
    z_rv = expanding_z(rv, grid,
                       FROZEN_DEFAULTS["standardization_min_history"])
    spread: dict[str, float | None] = {}
    for d in grid:
        a, b = z_impl.get(d), z_rv.get(d)
        spread[d] = None if (a is None or b is None) else a - b
    return spread


def build_a5p1_state(ctx: dict) -> tuple[dict[str, float | None], dict]:
    """VOLNG1-A5-P1 at frozen defaults: spread compression/expansion."""
    grid = ctx["grid"]
    spread = _spread_state(ctx, ctx["proxy_leg"])
    raw = threshold_states(spread, grid,
                           FROZEN_DEFAULTS["a5p1_spread_threshold"],
                           "expanded", "compressed", "neutral")
    # codes first, latch operates on codes
    raw_codes: dict[str, float | None] = {
        d: (None if raw[d] is None
            else FROZEN_DEFAULTS["a5p1_state_action_map"][raw[d]])
        for d in grid}
    state = debounce_latch(raw_codes, grid,
                           FROZEN_DEFAULTS["a5p1_hysteresis_sessions"])
    return state, {"spread_by_date": spread, "raw_state_by_date": raw}


def build_a5p2_state(ctx: dict) -> tuple[dict[str, float | None], dict]:
    """VOLNG1-A5-P2 at frozen defaults: short-vs-mid premium
    asymmetry, WITH the mid-bucket extension frozen here at D2 (the
    same declared proxy family on the mid reference leg)."""
    grid = ctx["grid"]
    spread_short = _spread_state(ctx, ctx["proxy_leg"])
    spread_mid = _spread_state(ctx, FROZEN_DEFAULTS["a5p2_mid_reference_leg"])
    asym: dict[str, float | None] = {}
    for d in grid:
        a, b = spread_short.get(d), spread_mid.get(d)
        asym[d] = None if (a is None or b is None) else a - b
    raw = threshold_states(asym, grid,
                           FROZEN_DEFAULTS["a5p2_asym_threshold"],
                           "short_extreme", "mid_extreme", "aligned")
    raw_codes: dict[str, float | None] = {
        d: (None if raw[d] is None
            else FROZEN_DEFAULTS["a5p2_state_action_map"][raw[d]])
        for d in grid}
    state = debounce_latch(raw_codes, grid,
                           FROZEN_DEFAULTS["a5p2_latch_sessions"])
    return state, {"asym_by_date": asym, "raw_state_by_date": raw}


PROPOSAL_BUILDERS = {
    "VOLNG1-A4-P1": build_a4p1_state,
    "VOLNG1-A4-P2": build_a4p2_state,
    "VOLNG1-A5-P1": build_a5p1_state,
    "VOLNG1-A5-P2": build_a5p2_state,
}


# --------------------------------------------------------------------------- #
# ancestry kill-shadow reconstructions (frozen forms)
# --------------------------------------------------------------------------- #
def shadow_v16_close_displace_fade(ctx: dict) -> dict[str, float | None]:
    """(a) Close-displacement fade on the event-adjusted legs."""
    grid = ctx["grid"]
    w = FROZEN_DEFAULTS["v16_window_sessions"]
    zthr = FROZEN_DEFAULTS["v16_z_threshold"]
    per_leg: dict[str, dict[str, float | None]] = {}
    for leg in ctx["leg_subset"]:
        closes = ctx["adj"][leg]
        z_by_date: dict[str, float | None] = {}
        for i, d in enumerate(grid):
            if i < w:
                z_by_date[d] = None
                continue
            window = [closes.get(grid[i - k]) for k in range(1, w + 1)]
            cur = closes.get(d)
            if cur is None or any(v is None for v in window):
                z_by_date[d] = None
                continue
            arr = np.asarray(window, dtype=float)
            mu = float(arr.mean())
            sd = float(arr.std(ddof=0))
            z_by_date[d] = None if sd == 0.0 else (float(cur) - mu) / sd
        per_leg[leg] = z_by_date
    return _aggregate_pole_positions(per_leg, grid, zthr, -zthr)


def shadow_v17_oi_level(ctx: dict) -> dict[str, float | None]:
    """(b) Level conditioning mapped to the granted VIX index level."""
    grid = ctx["grid"]
    lo = FROZEN_DEFAULTS["v17_level_low"]
    hi = FROZEN_DEFAULTS["v17_level_high"]
    out: dict[str, float | None] = {}
    for d in grid:
        v = ctx["index"]["VIX"].get(d)
        if v is None:
            out[d] = None
        elif v < lo:
            out[d] = SHORT_VOL
        elif v > hi:
            out[d] = LONG_VOL
        else:
            out[d] = FLAT
    return out


def shadow_dvol_shock(ctx: dict) -> dict[str, float | None]:
    """(c) Large-jump reaction mapped to VIX index jump events."""
    grid = ctx["grid"]
    jthr = FROZEN_DEFAULTS["dvol_jump_threshold"]
    hold = FROZEN_DEFAULTS["dvol_hold_sessions"]
    out: dict[str, float | None] = {}
    holding_sign = 0.0
    remaining = 0
    for i, d in enumerate(grid):
        if i == 0:
            out[d] = None
            continue
        v0 = ctx["index"]["VIX"].get(grid[i - 1])
        v1 = ctx["index"]["VIX"].get(d)
        if v0 is None or v1 is None:
            # an INVALID break ends any open reaction window (fail-closed)
            holding_sign = 0.0
            remaining = 0
            out[d] = None
            continue
        jump = v1 / v0 - 1.0
        if abs(jump) >= jthr:
            holding_sign = -1.0 if jump > 0 else 1.0
            remaining = hold
        if remaining > 0:
            out[d] = holding_sign
            remaining -= 1
        else:
            out[d] = FLAT
    return out


def shadow_momentum_63s(ctx: dict) -> dict[str, float | None]:
    """(d) Trailing 63-session momentum sign on the event-adjusted
    legs (chase form)."""
    grid = ctx["grid"]
    lb = FROZEN_DEFAULTS["momentum_lookback_sessions"]
    per_leg: dict[str, dict[str, float | None]] = {}
    for leg in ctx["leg_subset"]:
        closes = ctx["adj"][leg]
        mom: dict[str, float | None] = {}
        for i, d in enumerate(grid):
            if i < lb:
                mom[d] = None
                continue
            c0 = closes.get(grid[i - lb])
            c1 = closes.get(d)
            mom[d] = None if (c0 is None or c1 is None) else c1 / c0 - 1.0
        per_leg[leg] = mom
    return _aggregate_chase_positions(per_leg, grid)


def shadow_generic_dow_tue(ctx: dict) -> dict[str, float | None]:
    """(e) Calendar-clock position: short-vol pole on Tuesdays."""
    grid = ctx["grid"]
    out: dict[str, float | None] = {}
    for d in grid:
        wd = date.fromisoformat(d).weekday()
        out[d] = SHORT_VOL if wd == FROZEN_DEFAULTS["dow_tue_weekday"] \
            else FLAT
    return out


def _aggregate_pole_positions(
        per_leg_z: dict[str, dict[str, float | None]], grid: list[str],
        upper: float, lower: float) -> dict[str, float | None]:
    """Per-leg fade positions then mean over the proposal's frozen leg
    subset; any INVALID leg makes the instant INVALID (fail-closed, no
    per-leg imputation)."""
    out: dict[str, float | None] = {}
    for d in grid:
        vals: list[float] = []
        for leg in sorted(per_leg_z):
            z = per_leg_z[leg].get(d)
            if z is None:
                vals = []
                break
            if z >= upper:
                vals.append(SHORT_VOL)
            elif z <= lower:
                vals.append(LONG_VOL)
            else:
                vals.append(FLAT)
        out[d] = None if not vals else sum(vals) / len(vals)
    return out


def _aggregate_chase_positions(
        per_leg_mom: dict[str, dict[str, float | None]],
        grid: list[str]) -> dict[str, float | None]:
    """Chase-form aggregation: positive leg momentum -> long the leg
    (long-vol pole), negative -> short-vol pole; mean over the frozen
    leg subset; any INVALID leg -> INVALID instant."""
    out: dict[str, float | None] = {}
    for d in grid:
        vals: list[float] = []
        for leg in sorted(per_leg_mom):
            m = per_leg_mom[leg].get(d)
            if m is None:
                vals = []
                break
            if m > 0:
                vals.append(LONG_VOL)
            elif m < 0:
                vals.append(SHORT_VOL)
            else:
                vals.append(FLAT)
        out[d] = None if not vals else sum(vals) / len(vals)
    return out


SHADOW_BUILDERS = {
    "v16_close_displace_fade": shadow_v16_close_displace_fade,
    "v17_oi_level": shadow_v17_oi_level,
    "dvol_shock": shadow_dvol_shock,
    "momentum_63s": shadow_momentum_63s,
    "generic_dow_tue": shadow_generic_dow_tue,
}


# --------------------------------------------------------------------------- #
# measurement law: overlap, correlation, pooling, verdicts
# --------------------------------------------------------------------------- #
STATUS_MEASURED = "MEASURED"
STATUS_DEGENERATE_SHADOW = "DEGENERATE_SHADOW"
STATUS_PROPOSAL_DEGENERATE = "PROPOSAL_DEGENERATE"
STATUS_INSUFFICIENT_OVERLAP = "UNMEASURABLE_INSUFFICIENT_OVERLAP"
STATUS_UNMEASURABLE = "UNMEASURABLE"
STATUS_INAPPLICABLE = "INAPPLICABLE"

#: statuses that block an ELIGIBLE verdict (fail-closed: absence is
#: never PASS)
BLOCKING_STATUSES = (STATUS_PROPOSAL_DEGENERATE,
                     STATUS_INSUFFICIENT_OVERLAP,
                     STATUS_UNMEASURABLE)


def restrict_valid(series: dict[str, float | None],
                   instants: list[str]) -> list[str]:
    return [d for d in instants if series.get(d) is not None]


def state_distribution(series: dict[str, float | None],
                       instants: list[str]) -> dict[str, int]:
    dist: dict[str, int] = {}
    for d in instants:
        v = series.get(d)
        if v is None:
            continue
        key = repr(float(v))
        dist[key] = dist.get(key, 0) + 1
    return dist


def correlate_on_overlap(proposal_state: dict[str, float | None],
                         shadow_state: dict[str, float | None],
                         instants: list[str]) -> dict:
    """Correlate two decision-state series on the instants where BOTH
    are computable (each INVALID drops the pair and is counted, never
    coerced).  Returns the per-shadow measurement row body."""
    n_bookable = len(instants)
    overlap = [d for d in instants
               if proposal_state.get(d) is not None
               and shadow_state.get(d) is not None]
    n_used = len(overlap)
    n_dropped = n_bookable - n_used
    row = {
        "n_bookable_instants": n_bookable,
        "n_invalid_dropped": n_dropped,
        "n_used": n_used,
        "spearman": None,
        "pearson": None,
        "pooled_abs_max": None,
        "status": STATUS_MEASURED,
        "note": None,
    }
    if n_used < FROZEN_DEFAULTS["min_valid_overlap_instants"]:
        row["status"] = STATUS_INSUFFICIENT_OVERLAP
        row["note"] = (f"valid overlap {n_used} < frozen floor "
                       f"{FROZEN_DEFAULTS['min_valid_overlap_instants']}: "
                       "shadow UNMEASURABLE (fail-closed)")
        return row
    px = [float(proposal_state[d]) for d in overlap]
    sx = [float(shadow_state[d]) for d in overlap]
    sp = spearman(px, sx)
    pe = pearson(px, sx)
    row["spearman"] = sp
    row["pearson"] = pe
    pooled = pooled_abs(sp, pe)
    row["pooled_abs_max"] = pooled
    if pooled is None:
        # both correlations structurally undefined: at least one side
        # is constant on the overlap
        prop_const = len(set(px)) == 1
        shadow_const = len(set(sx)) == 1
        if prop_const and not shadow_const:
            row["status"] = STATUS_PROPOSAL_DEGENERATE
            row["note"] = ("proposal decision-state is constant on the "
                           "overlap: novelty not measurable "
                           "(fail-closed VETO-pending)")
        elif shadow_const:
            row["status"] = STATUS_DEGENERATE_SHADOW
            row["pooled_abs_max"] = 0.0
            row["note"] = ("mapped shadow decision-state is constant on "
                           "the overlap: co-movement with the proposal "
                           "state is structurally zero (reconstructed, "
                           "not absent); contribution |rho| = 0.0")
        else:
            row["status"] = STATUS_PROPOSAL_DEGENERATE
            row["note"] = "both series constant on the overlap"
    return row


def proposal_verdict(shadow_rows: list[dict]) -> dict:
    """The frozen gate law: pooled |rho| <= 0.20 == ELIGIBLE, else
    VETO; any blocking (unmeasurable) shadow -> VETO_PENDING unless
    documented inapplicable.  Absence is never PASS."""
    margin = FROZEN_DEFAULTS["margin_abs_rho"]
    blocking = [r for r in shadow_rows
                if r["status"] in BLOCKING_STATUSES]
    measured_pool = [r["pooled_abs_max"] for r in shadow_rows
                     if r["pooled_abs_max"] is not None]
    pooled = max(measured_pool) if measured_pool else None
    if blocking:
        return {
            "pooled_abs_max": pooled,
            "margin_to_gate": None,
            "verdict": "VETO_PENDING",
            "veto_reasons": [r["note"] or r["status"] for r in blocking],
        }
    if pooled is None:
        return {"pooled_abs_max": None, "margin_to_gate": None,
                "verdict": "VETO_PENDING",
                "veto_reasons": ["no shadow produced a measurable "
                                 "pooled |rho| (fail-closed)"]}
    return {
        "pooled_abs_max": pooled,
        "margin_to_gate": margin - pooled,
        "verdict": "ELIGIBLE" if pooled <= margin else "VETO",
        "veto_reasons": ([] if pooled <= margin
                         else [f"pooled |rho| {pooled} > margin {margin}"]),
    }
