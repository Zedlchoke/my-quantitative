"""RATES-NG1 P1 measured ETP cost constants (Q-8 law: measured, never
vendor-stated).

P1 work item 2 (dispatch packet RATES-NG1 / rates-ng1-p1-kernel-costs).
Because intraday/quote data is NOT entitled (EODHD family-1 EOD only),
the effective ETP spreads are ESTIMATED from the RAW EOD bars of the
P0 frozen substrate (consumed via ``plane_adapter``; never re-pulled):

- PRIMARY: Corwin-Schultz (2012, Journal of Finance) two-day high-low
  estimator.  Negative alpha values are floored at zero (standard
  practice; every floor is counted and disclosed).
- CROSS-CHECK: Roll (1984) implied effective spread from the lag-1
  autocovariance of close-to-close price changes, over rolling windows.
  Roll is undefined where the autocovariance is non-negative: those
  windows are counted, never imputed.

Stress tier: the 90th percentile of the per-ETP estimated (CS) spread
distribution -- the tier-2.0 cost ladder constant.  Expense-ratio daily
drag is an instrument FEE FACT (not a vendor spread claim): the annual
expense ratio comes from each issuer's official fund page with the
evidence URL recorded in the gate artifact.

This module is pure math + pure assembly: it reads no network and no
files.  ``p1_run.py`` feeds it plane-verified rows and writes the frozen
cost contract.  No proposals, no signals, no scoring here.
"""

from __future__ import annotations

import math
from typing import Any, Sequence

SCHEMA = "rates_ng1/cost_model@1"

#: Stress tier quantile of the estimated spread distribution (plan
#: section 5 + packet: stress tier = 90th percentile).
STRESS_TIER_QUANTILE = 0.90

#: Cost ladder tier carried by the assembled contract.
COST_LADDER_TIER = 2.0

#: Cost frequency law (plan section 5).
COST_FREQUENCY = "once_per_fill"

#: Days per year used for the expense-ratio daily drag conversion.
#: Declared basis: ACT/365 fixed.  The conversion is exact arithmetic.
DRAG_DAYS_BASIS = 365.0

METHOD_PRIMARY = "corwin_schultz_2012_highlow_two_day"
METHOD_CROSSCHECK = "roll_1984_autocovariance_effective_spread"

#: Default rolling window for the Roll cross-check (declared constant).
ROLL_WINDOW_DAYS_DEFAULT = 63

_DENOM = 3.0 - 2.0 * math.sqrt(2.0)


def percentile(values: Sequence[float], q: float) -> float:
    """Linear-interpolation percentile on an UNSORTED copy (inclusive
    endpoints; matches the committed forex-ng1 quantile convention)."""
    if not values:
        raise ValueError("percentile of empty sequence is undefined")
    if not 0.0 <= q <= 1.0:
        raise ValueError(f"quantile {q} outside [0, 1]")
    s = sorted(float(v) for v in values)
    pos = q * (len(s) - 1)
    lo = int(math.floor(pos))
    hi = min(lo + 1, len(s) - 1)
    frac = pos - lo
    return s[lo] * (1.0 - frac) + s[hi] * frac


def corwin_schultz_spread_series(
        highs: Sequence[float], lows: Sequence[float]) -> dict[str, Any]:
    """Corwin-Schultz (2012) two-day high-low spread series on RAW EOD
    bars.

    Returns ``{"spreads": [...], "estimable_pairs": int, "pairs": int,
    "floored": int, "mean": float|None, "p50": float|None,
    "p90": float|None}`` where ``spreads`` are relative (fraction of
    price) daily estimates for each consecutive two-day pair.  A pair is
    not estimable (None entry, excluded from the distribution) when
    either day lacks a positive high/low with high >= low.  Negative
    alpha is floored to 0.0 and counted in ``floored``.
    """
    if len(highs) != len(lows):
        raise ValueError("highs/lows length mismatch")
    n = len(highs)
    spreads: list[float | None] = []
    floored = 0
    pairs = max(0, n - 1)
    for t in range(pairs):
        h1, l1, h2, l2 = (float(highs[t]), float(lows[t]),
                          float(highs[t + 1]), float(lows[t + 1]))
        if min(h1, l1, h2, l2) <= 0 or h1 < l1 or h2 < l2:
            spreads.append(None)
            continue
        beta = math.log(h1 / l1) ** 2 + math.log(h2 / l2) ** 2
        hh, ll = max(h1, h2), min(l1, l2)
        gamma = math.log(hh / ll) ** 2 if hh > ll else 0.0
        alpha = ((math.sqrt(2.0 * beta) - math.sqrt(beta)) / _DENOM
                 - math.sqrt(gamma / _DENOM))
        if alpha < 0.0:
            alpha = 0.0
            floored += 1
        spreads.append(2.0 * (math.exp(alpha) - 1.0)
                       / (1.0 + math.exp(alpha)))
    valid = [s for s in spreads if s is not None]
    return {
        "spreads": spreads,
        "pairs": pairs,
        "estimable_pairs": len(valid),
        "floored": floored,
        "mean": (sum(valid) / len(valid)) if valid else None,
        "p50": percentile(valid, 0.50) if valid else None,
        "p90": percentile(valid, STRESS_TIER_QUANTILE) if valid else None,
    }


def roll_effective_spread_windows(
        closes: Sequence[float], window: int = 63) -> dict[str, Any]:
    """Roll (1984) implied effective spreads over rolling ``window``
    close-to-close windows.

    For each window, d_t = p_t - p_{t-1}; the lag-1 autocovariance
    ``cov = mean(d_t * d_{t-1}) - mean(d_t) * mean(d_{t-1})`` must be
    NEGATIVE for the estimator to exist: spread_price = 2 * sqrt(-cov)
    (PRICE units).  The relative-basis estimate divides by the window's
    mean close: ``spread_fraction = spread_price / mean(close_w)`` --
    the basis that is comparable to the Corwin-Schultz relative spread.
    Non-negative-covariance windows are counted (``undefined_cov``) and
    never imputed.  Returns price-unit and fraction medians plus
    coverage counters.
    """
    closes = [float(p) for p in closes]
    n = len(closes)
    if window < 2:
        raise ValueError("roll window must be >= 2")
    d = [closes[i] - closes[i - 1] for i in range(1, n)]
    est_price: list[float] = []
    est_frac: list[float] = []
    undefined_cov = 0
    windows = 0
    for start in range(0, max(0, len(d) - window + 1)):
        w = d[start:start + window]
        if len(w) < window:
            break
        windows += 1
        prod_mean = sum(w[i] * w[i - 1] for i in range(1, window)) \
            / (window - 1)
        mean1 = sum(w) / window
        mean2 = sum(w[:-1]) / (window - 1)
        cov = prod_mean - mean1 * mean2
        if cov < 0.0:
            spread_price = 2.0 * math.sqrt(-cov)
            ref = (sum(closes[start:start + window + 1])
                   / (window + 1))
            if ref <= 0:
                raise ValueError("non-positive reference close: refused")
            est_price.append(spread_price)
            est_frac.append(spread_price / ref)
        else:
            undefined_cov += 1
    return {
        "windows": windows,
        "estimable_windows": len(est_price),
        "undefined_cov": undefined_cov,
        "estimable_fraction": (len(est_price) / windows) if windows
        else None,
        "median_price_units": (percentile(est_price, 0.50)
                               if est_price else None),
        "median": percentile(est_frac, 0.50) if est_frac else None,
        "spreads_price_units": est_price,
        "spreads": est_frac,
        "units": "median is a fraction of price (window mean-close "
                 "basis); median_price_units is in the raw price units",
    }


def expense_drag_per_day(er_annual: float) -> float:
    """Daily expense drag from the official annual expense ratio (FEE
    FACT): ACT/365 fixed, exact arithmetic (``er / 365``)."""
    er = float(er_annual)
    if er < 0 or er > 0.05:
        raise ValueError(
            f"expense ratio {er} outside the sanity band [0, 5%]: refused")
    return er / DRAG_DAYS_BASIS


def bps(fraction: float | None) -> float | None:
    """Fraction -> basis points (x10^4), None-preserving."""
    return None if fraction is None else 10000.0 * float(fraction)


def assemble_cost_contract(
        *, cycle_id: str, window_by_ticker: dict[str, list[str]],
        cs_by_ticker: dict[str, dict[str, Any]],
        roll_by_ticker: dict[str, dict[str, Any]],
        er_by_ticker: dict[str, dict[str, Any]],
        substrate_provenance: dict[str, Any]) -> dict[str, Any]:
    """Assemble the frozen tier-2.0 cost contract: every constant carries
    its measured value, units and provenance.  Pure assembly -- no
    measurement happens here and no outcome number is produced."""
    per_etp: dict[str, Any] = {}
    for ticker in sorted(cs_by_ticker):
        cs, roll, er = (cs_by_ticker[ticker], roll_by_ticker[ticker],
                        er_by_ticker[ticker])
        cs_p50, cs_p90 = cs["p50"], cs["p90"]
        roll_med = roll["median"]
        # Cross-check basis: the CS p90 STRESS TIER.  The CS p50 is
        # routinely 0.0 for liquid ETPs (negative-alpha flooring), so a
        # p50 ratio is undefined; the stress tier is the constant the
        # cost ladder actually charges, so "Roll must not dwarf the
        # frozen tier" is the economically meaningful check.
        ratio = ((roll_med / cs_p90)
                 if (roll_med is not None and cs_p90) else None)
        per_etp[ticker] = {
            "spread_primary": {
                "method": METHOD_PRIMARY,
                "cs_p50_bps": bps(cs_p50),
                "cs_p90_bps": bps(cs_p90),
                "cs_mean_bps": bps(cs["mean"]),
                "estimable_pairs": cs["estimable_pairs"],
                "pairs": cs["pairs"],
                "estimable_fraction": (
                    cs["estimable_pairs"] / cs["pairs"]) if cs["pairs"]
                    and cs["pairs"] > 0 else None,
                "alpha_floored_days": cs["floored"],
                "window": window_by_ticker[ticker],
                "input": "RAW eod high/low (unadjusted primary channel)",
            },
            "spread_cross_check": {
                "method": METHOD_CROSSCHECK,
                "window_days": ROLL_WINDOW_DAYS_DEFAULT,
                "windows": roll["windows"],
                "estimable_windows": roll["estimable_windows"],
                "undefined_cov_windows": roll["undefined_cov"],
                "estimable_fraction": roll["estimable_fraction"],
                "roll_median_bps": bps(roll_med),
                "roll_over_cs_p90_ratio": ratio,
                "note": "Roll estimated on close-to-close changes per "
                        f"{ROLL_WINDOW_DAYS_DEFAULT}-day window; "
                        "2*sqrt(-cov) normalized by the window mean close "
                        "(fraction basis, CS-comparable); undefined where "
                        "the lag-1 autocovariance is non-negative "
                        "(counted, never imputed); ratio is vs the CS p90 "
                        "stress tier (CS p50 is routinely 0.0 after "
                        "negative-alpha flooring for liquid ETPs)",
            },
            "expense_drag": {
                "er_annual": er["er_annual"],
                "er_source": "issuer_official_fund_page",
                "er_evidence_url": er["evidence_url"],
                "er_page_title": er["page_title"],
                "er_page_sha256": er["page_sha256"],
                "er_page_bytes": er["page_bytes"],
                "er_fetch_utc": er["fetch_utc"],
                "drag_per_day_fraction": expense_drag_per_day(
                    er["er_annual"]),
                "drag_days_basis": "ACT/365F",
                "fee_fact_note": "instrument fee fact from the issuer's "
                                 "official page; NOT a vendor spread claim",
            },
            "stress_tier_bps": bps(cs_p90),
        }
    return {
        "schema": "rates_ng1_run/p1_cost_contract@1",
        "cycle_id": cycle_id,
        "cost_ladder_tier": COST_LADDER_TIER,
        "cost_frequency": COST_FREQUENCY,
        "stress_tier": {
            "quantile": STRESS_TIER_QUANTILE,
            "basis": "p90 of the Corwin-Schultz estimated spread "
                     "distribution on the RAW EOD bars of the P0 frozen "
                     "substrate (Q-8: measured, never vendor-stated)",
        },
        "per_etp": per_etp,
        "substrate_provenance": substrate_provenance,
    }
