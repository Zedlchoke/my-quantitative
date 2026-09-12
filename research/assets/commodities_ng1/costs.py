"""COMMODITIES-NG1 P1 measured ETP cost constants (Q-8, Q-16).

Q-8 LAW: costs are MEASURED, never vendor-stated.  Intraday/quote data
is NOT entitled for this family, so effective spreads are estimated
from the RAW EOD bars of the P0 frozen substrate (committed
``etp_eod/*.csv`` consumed digest-verified through the P0 plane
adapter -- no new network pulls for prices):

- PRIMARY: Corwin-Schultz (2012) high-low spread estimator on 2-day
  windows; the daily estimates are clipped at zero (standard
  treatment) and the STRESS tier constant is the 90th percentile of
  the estimate distribution (plan section 5);
- CROSS-CHECK: Roll (1984) implied spread from the negative lag-1
  autocovariance of close-to-close price changes; when the covariance
  is non-negative the estimate is not identifiable and ``None`` is
  recorded with the reason (fail-closed honesty, never a fabricated
  cross-check).

Q-16 LAW (the instrument is the asset): roll/tracking drag is part of
the mechanism.  Where SAME-UNDERLYING ETP pairs exist in the P0 census
(equal CoT contract market code, both legs ETP-eligible, purity
"pure"), the pairwise cumulative-return divergence over the common
window is the tracking-cost proxy (signed total + annualized).  A leg
with no same-underlying peer gets ``None`` plus a disclosed limitation
-- never an inferred number.

Expense-ratio daily drag is an instrument fee FACT (official issuer
page, sha256-pinned, see ``fee_facts.json``): recorded as stated or
NOT_MEASURED, never guessed.
"""

from __future__ import annotations

import math
from datetime import date

SCHEMA = "commodities_ng1/costs@1"

#: Stress percentile for the transaction-tier constant (plan section 5).
STRESS_PERCENTILE = 0.90

#: Corwin-Schultz constant K = 3 - 2*sqrt(2) == (sqrt(2)-1)**2.
_CS_K = 3.0 - 2.0 * math.sqrt(2.0)


class CostMeasurementRefused(Exception):
    """Fail-closed cost measurement refusal (malformed bars, insufficient
    overlap, missing constant)."""


#: Adjustment-factor change >= this threshold marks a share-base event
#: (reverse split / share reconstitution) in the vendor surface.
SPLIT_FACTOR_THRESHOLD = 0.05


def split_events(bars: list[dict]) -> list[dict]:
    """Share-base events of one leg from the RAW/adjusted pair.

    The adjustment factor ``adj_close / close`` is constant between
    share-base events; a factor-LEVEL change between consecutive
    sessions (>= ``SPLIT_FACTOR_THRESHOLD``) marks a boundary across
    which RAW prices are not comparable (measured reverse splits in
    this substrate: IAU 2010-06-24 and 2021-05-24, BAR 2019-03-11,
    SLV 2008-07-24, USO 2020-04-29).  Estimators either exclude
    boundaries (spreads) or use the split-continuous adjusted surface
    (cross-sectional divergence); both disclose the event census.
    """
    events = []
    prev_factor = None
    prev_date = None
    for b in bars:
        close, adj = float(b["close"]), float(b["adj_close"])
        if close <= 0:
            raise CostMeasurementRefused(
                f"non-positive close at {b['date']}; fail closed")
        factor = adj / close
        if prev_factor is not None:
            change = factor / prev_factor - 1.0
            if abs(change) >= SPLIT_FACTOR_THRESHOLD:
                events.append({
                    "boundary_after": str(prev_date),
                    "boundary_date": str(b["date"]),
                    "factor_before": prev_factor,
                    "factor_after": factor,
                    "implied_share_base_change": change,
                })
        prev_factor = factor
        prev_date = b["date"]
    return events


def _split_boundaries(events: list[dict]) -> set[str]:
    """Dates (as ISO strings) whose PREVIOUS session starts a new share
    base: a window/delta spanning (boundary_after, boundary_date) is
    corrupted for RAW-surface estimation."""
    return {e["boundary_date"] for e in events}


def percentile_linear(values: list[float], q: float) -> float:
    """Percentile with linear interpolation (numpy 'linear' convention).

    Deterministic and dependency-free so the P1 hand-computed tests pin
    the exact definition: position ``p = q*(n-1)``; result is
    ``v[i] + (p - i) * (v[i+1] - v[i])`` for ``i = floor(p)``.
    """
    if not values:
        raise CostMeasurementRefused("percentile of empty values")
    if not 0.0 <= q <= 1.0:
        raise CostMeasurementRefused(f"q {q!r} outside [0, 1]")
    ordered = sorted(float(v) for v in values)
    p = q * (len(ordered) - 1)
    i = int(math.floor(p))
    if i >= len(ordered) - 1:
        return ordered[-1]
    frac = p - i
    return ordered[i] + frac * (ordered[i + 1] - ordered[i])


def corwin_schultz_daily_spreads(bars: list[dict],
                                 exclude_boundary_dates: set | None = None
                                 ) -> tuple[list[dict], int]:
    """Corwin-Schultz full-spread estimate per 2-day window.

    ``bars``: [{date, high, low, ...}] sorted by date; consecutive
    date pairs form the windows.  Non-consecutive-calendar gaps are
    allowed (weekends/holidays): the estimator uses consecutive
    OBSERVED sessions, as in the reference implementation.

    Windows spanning a share-base boundary (split/reconstitution) of
    the leg are EXCLUDED (the 2-day high/low would mix two share
    bases); the excluded count is returned for provenance.

    For window (t, t+1):
        beta_t  = ln(H_t/L_t)^2 + ln(H_{t+1}/L_{t+1})^2
        gamma_t = ln(max(H_t,H_{t+1}) / min(L_t,L_{t+1}))^2
        alpha_t = (sqrt(2*beta) - sqrt(beta)) / K - sqrt(gamma / K)
        S_t     = 2*(e^alpha - 1) / (1 + e^alpha), clipped at 0
    """
    out = []
    excluded = 0
    if len(bars) < 2:
        raise CostMeasurementRefused(
            "Corwin-Schultz needs >= 2 observed sessions")
    skip = exclude_boundary_dates or set()
    for a, b in zip(bars, bars[1:]):
        try:
            hi_a, lo_a = float(a["high"]), float(a["low"])
            hi_b, lo_b = float(b["high"]), float(b["low"])
            d_a, d_b = a["date"], b["date"]
        except (KeyError, TypeError, ValueError) as exc:
            raise CostMeasurementRefused(
                f"malformed bar pair {a!r}/{b!r}: {exc}") from exc
        if str(d_b) in skip:
            excluded += 1
            continue
        if min(hi_a, lo_a, hi_b, lo_b) <= 0:
            raise CostMeasurementRefused(
                f"non-positive high/low at {d_a}/{d_b}; fail closed")
        if hi_a < lo_a or hi_b < lo_b:
            raise CostMeasurementRefused(
                f"high < low at {d_a}/{d_b}; fail closed")
        beta = math.log(hi_a / lo_a) ** 2 + math.log(hi_b / lo_b) ** 2
        gamma = math.log(max(hi_a, hi_b) / min(lo_a, lo_b)) ** 2
        alpha = ((math.sqrt(2.0 * beta) - math.sqrt(beta)) / _CS_K
                 - math.sqrt(gamma / _CS_K))
        raw = 2.0 * (math.exp(alpha) - 1.0) / (1.0 + math.exp(alpha))
        spread = max(raw, 0.0)
        out.append({
            "window_start": d_a,
            "window_end": d_b,
            "beta": beta,
            "gamma": gamma,
            "alpha": alpha,
            "spread_frac_raw": raw,
            "spread_frac": spread,
            "clipped": raw < 0.0,
        })
    return out, excluded


def cs_stress_constant(bars: list[dict]) -> dict:
    """Measured CS constants for one leg from RAW EOD bars.

    Returns the stress-tier (p90) and median full-spread fractions over
    the leg's 2-day windows (share-base-boundary windows excluded),
    with the window, clipping and split-event census as provenance.
    """
    events = split_events(bars)
    boundaries = _split_boundaries(events)
    windows, excluded = corwin_schultz_daily_spreads(
        bars, exclude_boundary_dates=boundaries)
    if not windows:
        raise CostMeasurementRefused(
            "zero usable CS windows after boundary exclusion")
    spreads = [w["spread_frac"] for w in windows]
    clipped = sum(1 for w in windows if w["clipped"])
    return {
        "method": "corwin_schultz_2012_highlow_2day",
        "constant_bps_full_spread_p90": 1e4 * percentile_linear(
            spreads, STRESS_PERCENTILE),
        "constant_frac_full_spread_p90": percentile_linear(
            spreads, STRESS_PERCENTILE),
        "median_bps_full_spread": 1e4 * percentile_linear(spreads, 0.5),
        "windows": len(windows),
        "windows_clipped_at_zero": clipped,
        "windows_excluded_share_base_boundary": excluded,
        "share_base_events": events,
        "first_window": str(windows[0]["window_start"]),
        "last_window": str(windows[-1]["window_end"]),
        "percentile": STRESS_PERCENTILE,
        "input": "RAW EOD high/low (P0 frozen substrate; RAW primary "
                 "per etp_census convention)",
    }


def roll_spread_cross_check(bars: list[dict]) -> dict:
    """Roll (1984) implied-spread cross-check from RAW EOD closes.

    With dp_t = p_t - p_{t-1}: when cov(dp_t, dp_{t-1}) < 0 the
    implied effective spread is 2*sqrt(-cov) in price units, reported
    as a fraction of the mean close.  Close-to-close deltas spanning a
    share-base boundary are excluded (RAW deltas across a split are
    not price moves).  When cov >= 0 the spread is NOT identifiable
    and ``None`` is returned with the measured covariance as the
    reason (never a fabricated number).
    """
    if len(bars) < 3:
        raise CostMeasurementRefused("Roll needs >= 3 observed sessions")
    events = split_events(bars)
    boundaries = _split_boundaries(events)
    pairs = [(a, b) for a, b in zip(bars, bars[1:])
             if str(b["date"]) not in boundaries]
    excluded = (len(bars) - 1) - len(pairs)
    closes = [float(a["close"]) for a, _ in pairs]
    nexts = [float(b["close"]) for _, b in pairs]
    dp = [y - x for x, y in zip(closes, nexts)]
    n = len(dp)
    mean_dp = math.fsum(dp) / n
    cov = math.fsum(
        (x - mean_dp) * (y - mean_dp)
        for x, y in zip(dp[1:], dp[:-1])) / (len(dp[1:]) - 1)
    mean_close = math.fsum(float(b["close"]) for b in bars) / len(bars)
    out = {
        "method": "roll_1984_lag1_autocov",
        "surface": "RAW close deltas; share-base-boundary deltas "
                   "excluded",
        "deltas_excluded_share_base_boundary": excluded,
        "n_delta": n,
        "cov_lag1": cov,
        "mean_close": mean_close,
        "identifiable": bool(cov < 0.0),
    }
    if cov < 0.0:
        s_price = 2.0 * math.sqrt(-cov)
        out["spread_frac"] = s_price / mean_close
        out["constant_bps_full_spread"] = 1e4 * out["spread_frac"]
    else:
        out["spread_frac"] = None
        out["constant_bps_full_spread"] = None
        out["reason"] = (
            f"cov(dp_t, dp_(t-1)) = {cov:.3e} >= 0: Roll spread not "
            "identifiable on this series; cross-check recorded None "
            "(fail-closed, not fabricated)")
    return out


def tracking_divergence(bars_a: list[dict], bars_b: list[dict],
                        symbol_a: str, symbol_b: str) -> dict:
    """Pairwise cumulative-return divergence over the COMMON window.

    Surface: the vendor split-continuous ``adj_close`` reconstruction
    (the traded RAW close remains the primary surface for spreads and
    execution; cross-sectional return divergence MUST be share-base
    continuous or same-underlying pairs with measured reverse splits
    -- IAU/BAR/SLV/USO -- would report split artifacts as "tracking
    drag").  Both legs must trade on every common date; cumulative
    growth is the product of daily simple returns over the shared
    dates.  Signed divergence is growth_a - growth_b; the annualized
    divergence applies a 365.25-day Julian-year exponent.  Per Q-16
    the |annualized| divergence is the per-leg tracking-cost proxy.
    """
    if not bars_a or not bars_b:
        raise CostMeasurementRefused("empty leg series")
    idx_b = {b["date"]: b for b in bars_b}
    common = [b for b in bars_a if b["date"] in idx_b]
    if len(common) < 2:
        raise CostMeasurementRefused(
            f"{symbol_a}/{symbol_b}: common window {len(common)} days "
            "< 2; no measurable pair")
    first = common[0]["date"]

    def growth(seq):
        g = 1.0
        prev = None
        for bar in seq:
            c = float(bar["adj_close"])
            if prev is not None:
                g *= c / prev
            prev = c
        return g

    ga = growth(common)
    gb = growth([idx_b[b["date"]] for b in common])
    if ga <= 0 or gb <= 0:
        raise CostMeasurementRefused("non-positive cumulative growth")
    days = (common[-1]["date"] - first).days
    years = days / 365.25
    annualized_a = ga ** (1.0 / years) - 1.0
    annualized_b = gb ** (1.0 / years) - 1.0
    return {
        "pair": f"{symbol_a}/{symbol_b}",
        "surface": "split-continuous adj_close reconstruction "
                   "(RAW close is the trading surface, not the "
                   "cross-sectional return surface)",
        "first_common": str(first),
        "last_common": str(common[-1]["date"]),
        "common_days": days,
        "common_sessions": len(common),
        "growth_a": ga,
        "growth_b": gb,
        "divergence_total": ga - gb,
        "annualized_return_a": annualized_a,
        "annualized_return_b": annualized_b,
        "divergence_annualized": annualized_a - annualized_b,
        "years": years,
        "method": "cumulative-return divergence over the common EOD "
                  "window (signed; |annualized| is the per-leg drag "
                  "proxy)",
    }


def same_underlying_groups(pairs: list[dict], eligible_legs: set[str]
                           ) -> dict[str, list[str]]:
    """Group ETP legs by the SAME measured CoT contract market code.

    Derived from the committed P0 market-pair census (NOT hardcoded):
    a group is the set of ETP-eligible, purity-"pure" legs sharing one
    ``cot_market_code``.  Groups with >= 2 legs admit pairwise
    tracking-divergence measurement.
    """
    groups: dict[str, set[str]] = {}
    for p in pairs:
        code = p.get("cot_market_code")
        leg = p.get("etp")
        if not code or not leg or leg not in eligible_legs:
            continue
        if p.get("purity") != "pure":
            continue
        groups.setdefault(code, set()).add(leg)
    return {code: sorted(legs) for code, legs in sorted(groups.items())
            if len(legs) >= 2}


def half_spread_frac_from_leg(cs: dict) -> float:
    """Per-fill half-spread fraction: half of the CS p90 FULL spread.

    A round trip (2 fills) pays the full measured spread; a single
    fill pays the half-spread (kernel law: cost once per fill).
    """
    full = cs.get("constant_frac_full_spread_p90")
    if full is None or full <= 0:
        raise CostMeasurementRefused(
            "CS p90 full spread missing/non-positive; no per-fill "
            "constant may be derived (fail-closed)")
    return full / 2.0
