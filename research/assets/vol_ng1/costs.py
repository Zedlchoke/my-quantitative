"""VOL-NG1 P1 measured ETP cost constants (Q-8 + Q-16).

Laws encoded here:

- Q-8: costs are MEASURED, never vendor-stated.  Intraday/quote data
  is NOT entitled (EODHD family-1 only), so effective spreads are
  estimated from RAW EOD bars: Corwin-Schultz (2015) high-low primary,
  Roll (1984) serial-covariance cross-check; stress tier = 90th
  percentile of the monthly estimates.
- Q-16: the instrument is the asset -- the ETP roll/decay path is the
  DOMINANT cost mechanism for this family.  The path-cost ladder
  component is measured from the term-structure convergence behavior
  observable in the GRANTED CBOE index series (VIX9D/VIX for the
  short-term bucket, VIX3M/VIX6M for the mid-term bucket), with the
  method + provenance recorded.
- Expense drag comes from OFFICIAL fund fee facts only (issuer pages
  / SEC-filed prospectuses); these URLs are the ONLY network reads of
  this cycle (no price pulls anywhere).

No proposals, no signals, no scoring, no outcome numbers anywhere.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import urllib.request

SCHEMA = "vol_ng1/costs@1"

#: Living legs (P0 floor F3 census) and their futures-maturity bucket.
LIVING_LEGS = ("VXX", "UVXY", "SVXY", "VIXY", "VIXM", "VXZ")
LEG_BUCKETS = {
    "VXX": "SHORT", "UVXY": "SHORT", "SVXY": "SHORT", "VIXY": "SHORT",
    "VIXM": "MID", "VXZ": "MID",
}

# ------------------------------------------------------------------ #
# Q-16 measured roll/decay path-cost ladder component
# ------------------------------------------------------------------ #
# Convergence geometry of the official CBOE term structure: the
# constant-maturity points sit 21 days apart (VIX9D 9d -> VIX 30d)
# and 90 days apart (VIX3M 90d -> VIX6M 180d).  A position at the
# shorter point rolls toward the longer point; its per-day log carry
# from pure convergence is the log level gap divided by the day gap.
PATH_COST_MODELS = {
    "SHORT": {
        "numerator": ("VIX9D", "VIX"),
        "day_gap": 21.0,
        "formula": "ln(VIX9D/VIX)/21",
        "legs": ("VXX", "UVXY", "SVXY", "VIXY"),
    },
    "MID": {
        "numerator": ("VIX3M", "VIX6M"),
        "day_gap": 90.0,
        "formula": "ln(VIX3M/VIX6M)/90",
        "legs": ("VIXM", "VXZ"),
    },
}

# ------------------------------------------------------------------ #
# Official fund fee facts (the ONLY network reads of this cycle)
# ------------------------------------------------------------------ #
SEC_USER_AGENT = "vol-ng1-research admin@example.com"

FEE_FACT_SOURCES = {
    "UVXY": {
        "kind": "ETF expense ratio",
        "url": "https://www.proshares.com/our-etfs/strategic/uvxy",
        "extract": ("snapshot-expenseRatio",),
        "pattern": (r'id="snapshot-expenseRatio"[^>]*>\s*([0-9.]+)\s*%'
                    r'</span>'),
        "as_of_pattern": r'[Aa]s of ([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})',
    },
    "SVXY": {
        "kind": "ETF expense ratio",
        "url": "https://www.proshares.com/our-etfs/strategic/svxy",
        "extract": ("snapshot-expenseRatio",),
        "pattern": (r'id="snapshot-expenseRatio"[^>]*>\s*([0-9.]+)\s*%'
                    r'</span>'),
        "as_of_pattern": r'[Aa]s of ([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})',
    },
    "VIXY": {
        "kind": "ETF expense ratio",
        "url": "https://www.proshares.com/our-etfs/strategic/vixy",
        "extract": ("snapshot-expenseRatio",),
        "pattern": (r'id="snapshot-expenseRatio"[^>]*>\s*([0-9.]+)\s*%'
                    r'</span>'),
        "as_of_pattern": r'[Aa]s of ([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})',
    },
    "VIXM": {
        "kind": "ETF expense ratio",
        "url": "https://www.proshares.com/our-etfs/strategic/vixm",
        "extract": ("snapshot-expenseRatio",),
        "pattern": (r'id="snapshot-expenseRatio"[^>]*>\s*([0-9.]+)\s*%'
                    r'</span>'),
        "as_of_pattern": r'[Aa]s of ([0-9]{1,2}/[0-9]{1,2}/[0-9]{4})',
    },
    # VXX / VXZ are Barclays iPath ETNs: the official fee fact is the
    # investor fee in the SEC-filed 424B2 prospectus (accession
    # 0001104659-18-006905, filed 2018-02-07): 0.89% per annum,
    # accruing daily at rate/365.
    "VXX": {
        "kind": "ETN investor fee",
        "url": ("https://www.sec.gov/Archives/edgar/data/312070/"
                "000110465918006905/a18-5178_53424b2.htm"),
        "pattern": (r'investor fee for each series of ETNs will be '
                    r'equal to \(1\)(?:&nbsp;|\s)*([0-9.]+)%'),
        "as_of_pattern": None,
        "as_of_fixed": "2018-02-07 (SEC filing date, accession "
                       "0001104659-18-006905)",
    },
    "VXZ": {
        "kind": "ETN investor fee",
        "url": ("https://www.sec.gov/Archives/edgar/data/312070/"
                "000110465918006905/a18-5178_53424b2.htm"),
        "pattern": (r'investor fee for each series of ETNs will be '
                    r'equal to \(1\)(?:&nbsp;|\s)*([0-9.]+)%'),
        "as_of_pattern": None,
        "as_of_fixed": "2018-02-07 (SEC filing date, accession "
                       "0001104659-18-006905)",
    },
}


class CostsError(Exception):
    """Fail-closed cost-constant error: nothing inferred."""


# ------------------------------------------------------------------ #
# Corwin-Schultz (2015) high-low spread estimator, monthly
# ------------------------------------------------------------------ #
_CS_DENOM = 3.0 - 2.0 * math.sqrt(2.0)


def _cs_alpha(beta: float, gamma: float) -> float:
    return (math.sqrt(2.0 * beta) - math.sqrt(beta)) / _CS_DENOM \
        - math.sqrt(gamma / _CS_DENOM)


def _cs_spread_from_alpha(alpha: float) -> float:
    e = math.exp(alpha)
    return 2.0 * (e - 1.0) / (1.0 + e)


def corwin_schultz_monthly(bars: list[dict]) -> dict:
    """Monthly Corwin-Schultz effective-spread estimates from RAW EOD
    high/low (RAW primary; no quote data used anywhere).

    Per month: beta = mean over consecutive-day pairs of
    ``ln(H1/L1)^2 + ln(H2/L2)^2``; gamma = mean of
    ``ln(max(H)/min(L))^2`` over the same 2-day windows;
    ``alpha`` per Corwin-Schultz; ``spread = 2(e^a - 1)/(1 + e^a)``.
    A negative alpha is floored to a 0.0 spread (CS convention) and
    counted.  Months with fewer than 2 usable bars are skipped.
    """
    by_month: dict[str, list[tuple[str, float, float]]] = {}
    clean = sorted(
        (b for b in bars
         if isinstance(b, dict) and b.get("date")
         and isinstance(b.get("high"), (int, float))
         and isinstance(b.get("low"), (int, float))
         and b["high"] > 0 and b["low"] > 0),
        key=lambda b: b["date"])
    for b in clean:
        ym = str(b["date"])[:7]
        by_month.setdefault(ym, []).append(
            (b["date"], float(b["high"]), float(b["low"])))
    months = []
    floored = 0
    skipped = 0
    for ym in sorted(by_month):
        rows = by_month[ym]
        if len(rows) < 2:
            skipped += 1
            continue
        betas, gammas = [], []
        for (d1, h1, l1), (d2, h2, l2) in zip(rows, rows[1:]):
            if l1 <= 0 or l2 <= 0:
                continue
            betas.append(math.log(h1 / l1) ** 2 + math.log(h2 / l2) ** 2)
            gammas.append(math.log(max(h1, h2) / min(l1, l2)) ** 2)
        if not betas:
            skipped += 1
            continue
        beta = sum(betas) / len(betas)
        gamma = sum(gammas) / len(gammas)
        alpha = _cs_alpha(beta, gamma)
        if alpha < 0.0:
            months.append({"month": ym, "spread": 0.0, "floored": True})
            floored += 1
        else:
            months.append({"month": ym,
                           "spread": _cs_spread_from_alpha(alpha),
                           "floored": False})
    if not months:
        raise CostsError("Corwin-Schultz produced zero monthly "
                         "estimates (high/low unusable?)")
    return {"months": months, "floored_months": floored,
            "skipped_months": skipped}


def percentile(sorted_vals: list[float], q: float) -> float:
    """Linear-interpolation percentile on a pre-sorted list (numpy
    'linear' convention, deterministic)."""
    if not sorted_vals:
        raise CostsError("percentile of empty list")
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    pos = (len(sorted_vals) - 1) * q
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return sorted_vals[int(pos)]
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) \
        * (pos - lo)


def cs_stress_tier(monthly: dict) -> dict:
    """Q-8 stress tier = 90th percentile of the monthly estimates.

    Measured reality on RAW vol-ETP bars: the CS negative-alpha regime
    dominates (~95% of months floor to 0.0 -- the documented CS
    limitation on high-volatility series).  The floors are DISCLOSED,
    never repaired: the stress reading is the p90 of the MEASURABLE
    (non-floored) months, with the all-months percentiles and the
    floored share recorded beside it.
    """
    spreads = sorted(m["spread"] for m in monthly["months"])
    meas = sorted(m["spread"] for m in monthly["months"]
                  if not m["floored"])
    if not meas:
        raise CostsError(
            "every monthly Corwin-Schultz estimate floored to zero: "
            "no measurable month in this window (fail-closed)")
    return {
        "stress_tier": "p90",
        "stress_basis": "p90 of the measurable (non-floored) monthly "
                        "Corwin-Schultz estimates",
        "p50_spread_frac": round(percentile(meas, 0.50), 8),
        "p90_spread_frac": round(percentile(meas, 0.90), 8),
        "p50_all_months_frac": round(percentile(spreads, 0.50), 8),
        "p90_all_months_frac": round(percentile(spreads, 0.90), 8),
        "max_measured_frac": round(meas[-1], 8),
        "n_months": len(spreads),
        "n_measurable_months": len(meas),
        "floored_months": monthly["floored_months"],
        "skipped_months": monthly["skipped_months"],
        "instability_note": "CS floors on the negative-alpha months "
                            "of these high-volatility bars; floors "
                            "are disclosed, not repaired (Q-8)",
    }


# ------------------------------------------------------------------ #
# Roll (1984) serial-covariance cross-check
# ------------------------------------------------------------------ #
def roll_spread(closes: list[float]) -> dict:
    """Roll effective-spread cross-check: ``2*sqrt(-gamma)`` with
    ``gamma`` the lag-1 serial covariance of close-to-close price
    changes (population form, mean-centred).  A non-negative gamma
    yields a 0.0 spread (the estimator is undefined there)."""
    if len(closes) < 3:
        raise CostsError("Roll needs >= 3 closes")
    dp = [b - a for a, b in zip(closes, closes[1:])]
    n = len(dp)
    mu = sum(dp) / n
    gamma = sum((x - mu) * (y - mu)
                for x, y in zip(dp, dp[1:])) / (n - 1)
    spread = 2.0 * math.sqrt(-gamma) if gamma < 0 else 0.0
    return {"spread_frac": spread, "lag1_autocov": gamma, "n_changes": n}


# ------------------------------------------------------------------ #
# Q-16 measured path-cost ladder component
# ------------------------------------------------------------------ #
def path_cost_series(index_closes: dict[str, dict[str, float]],
                     bucket: str) -> dict:
    """Daily convergence carry for one bucket, measured on the granted
    CBOE series only.

    ``index_closes`` maps index name -> {iso_date: close}.  Per day
    (both points present)::

        c = ln(level_short / level_long) / day_gap

    negative in contango (the dominant long-ETP decay drag), positive
    in backwardation.  Provenance = the CBOE CSV digests of the two
    consumed series.
    """
    model = PATH_COST_MODELS.get(bucket)
    if model is None:
        raise CostsError(f"unknown path-cost bucket {bucket!r}")
    a_name, b_name = model["numerator"]
    a = index_closes.get(a_name)
    b = index_closes.get(b_name)
    if not a or not b:
        raise CostsError(
            f"path-cost bucket {bucket} needs series {a_name} and "
            f"{b_name}; got {sorted(index_closes)}")
    days = sorted(set(a) & set(b))
    if not days:
        raise CostsError(
            f"empty common-date intersection for {a_name}/{b_name}")
    series = {}
    for d in days:
        if a[d] <= 0 or b[d] <= 0:
            raise CostsError(f"non-positive index close at {d}")
        series[d] = math.log(a[d] / b[d]) / model["day_gap"]
    vals = sorted(series.values())
    n = len(vals)
    mean = sum(vals) / n
    return {
        "bucket": bucket,
        "formula": model["formula"],
        "day_gap": model["day_gap"],
        "series_names": [a_name, b_name],
        "first_day": days[0],
        "last_day": days[-1],
        "days": n,
        "mean_daily_log": mean,
        "mean_daily_bps": round(mean * 1e4, 6),
        "p10_daily_bps": round(percentile(vals, 0.10) * 1e4, 6),
        "p90_daily_bps": round(percentile(vals, 0.90) * 1e4, 6),
    }


# ------------------------------------------------------------------ #
# official fee facts (bounded network reads)
# ------------------------------------------------------------------ #
def _fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers={
        "User-Agent": SEC_USER_AGENT,
        "Accept": "text/html,application/pdf,*/*",
    })
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()


def fetch_fee_facts(cache_dir: str | None = None,
                    sources: dict | None = None) -> dict:
    """One bounded GET per official source; extract the fee fact;
    record URL + sha256 + extraction snippet.  No price endpoints, no
    keyed calls, no .env reads (issuer/SEC pages only)."""
    out = {}
    for leg, src in sorted((sources or FEE_FACT_SOURCES).items()):
        try:
            body = _fetch(src["url"])
        except Exception as exc:  # noqa: BLE001 -- fail-closed per leg
            out[leg] = {"leg": leg, "url": src["url"],
                        "verdict": "NOT_RUN", "error": repr(exc)}
            continue
        sha = hashlib.sha256(body).hexdigest()
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)
            with open(os.path.join(
                    cache_dir, f"{leg}_feefact.bin"), "wb") as fh:
                fh.write(body)
        text = body.decode("utf-8", "replace")
        m = re.search(src["pattern"], text, re.IGNORECASE)
        if m is None:
            out[leg] = {"leg": leg, "url": src["url"],
                        "sha256": sha, "verdict": "NOT_RUN",
                        "error": "fee pattern not found in official "
                                 "bytes"}
            continue
        pct = float(m.group(1))
        as_of = src.get("as_of_fixed")
        if as_of is None and src.get("as_of_pattern"):
            m2 = re.search(src["as_of_pattern"], text)
            as_of = m2.group(1) if m2 else None
        out[leg] = {
            "leg": leg,
            "kind": src["kind"],
            "url": src["url"],
            "sha256": sha,
            "percent_per_annum": pct,
            "bps_per_day": round(pct * 100.0 / 365.0, 6),
            "as_of": as_of,
            "snippet": m.group(0)[:160],
            "verdict": "MEASURED",
        }
    return out


def load_fee_facts(path: str) -> dict:
    """Committed fee-fact evidence (no network): fail-closed load."""
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    if data.get("schema") != "vol_ng1_run/p1_fee_facts@1":
        raise CostsError(f"fee-fact artifact schema mismatch: {path}")
    return data["legs"]


# ------------------------------------------------------------------ #
# tier-2.0 cost contract assembly
# ------------------------------------------------------------------ #
COST_TIER_LADDER = (1.0, 1.5, 2.0)
PRIMARY_TIER = 2.0


def build_leg_cost(leg: str, cs: dict, roll: dict, fee: dict,
                   path: dict) -> dict:
    """One leg's measured cost block; the tier ladder scales the
    EXECUTION frictions (uncertainty), while the measured expense drag
    and the Q-16 path component are carried EXPLICITLY and unchanged
    at every tier (they are mechanisms, not uncertainty)."""
    if leg not in LEG_BUCKETS:
        raise CostsError(f"leg {leg!r} outside the living-leg census")
    stress = cs["p90_spread_frac"]
    if fee.get("verdict") != "MEASURED":
        raise CostsError(
            f"leg {leg}: expense fact not MEASURED ({fee.get('verdict')})")
    tiers = {}
    for t in COST_TIER_LADDER:
        tiers[str(t)] = {
            "execution_spread_bps_per_fill": round(
                stress * 1e4 / 2.0 * t, 6),
            "expense_bps_per_day": fee["bps_per_day"],
            "path_mean_daily_bps": path["mean_daily_bps"],
            "primary": t == PRIMARY_TIER,
        }
    return {
        "leg": leg,
        "bucket": LEG_BUCKETS[leg],
        "spread": {
            "method": "Corwin-Schultz (2015) monthly effective spread "
                      "on RAW EOD high/low (no quote data)",
            "stress_tier": "p90",
            **cs,
        },
        "roll_crosscheck": {
            "method": "Roll (1984) lag-1 serial-covariance cross-check "
                      "on RAW closes",
            **roll,
        },
        "expense": {
            "kind": fee["kind"],
            "percent_per_annum": fee["percent_per_annum"],
            "bps_per_day": fee["bps_per_day"],
            "source_url": fee["url"],
            "source_sha256": fee["sha256"],
            "as_of": fee.get("as_of"),
            "provenance": "official issuer page / SEC-filed "
                          "prospectus (the only network reads of "
                          "this cycle)",
        },
        "path_cost": {
            "method": "Q-16 measured convergence carry on the granted "
                      "CBOE term structure",
            **path,
        },
        "tiers": tiers,
    }


def build_cost_contract(legs: dict) -> dict:
    """The tier-2.0 cost contract over all living legs (fail-closed:
    every leg must carry every measured component)."""
    if set(legs) != set(LIVING_LEGS):
        raise CostsError(
            f"cost contract needs exactly the living legs "
            f"{LIVING_LEGS}; got {sorted(legs)}")
    return {
        "schema": "vol_ng1_run/p1_cost_contract@1",
        "cycle_id": "VOL-NG1",
        "tier_ladder": list(COST_TIER_LADDER),
        "primary_tier": PRIMARY_TIER,
        "q8_law": "costs measured from RAW EOD bars, never vendor-"
                  "stated; stress tier = p90 of monthly Corwin-Schultz",
        "q16_law": "the ETP roll/decay path is the dominant cost "
                   "mechanism; its measured component is carried "
                   "explicitly at every tier",
        "execution_note": "execution spread charged once per fill "
                          "(half-spread per fill, full spread per "
                          "round trip); tier ladder scales execution "
                          "frictions only",
        "legs": {leg: legs[leg] for leg in LIVING_LEGS},
    }
