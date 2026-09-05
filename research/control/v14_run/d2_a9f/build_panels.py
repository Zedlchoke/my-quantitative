"""A9-F T3: per-proposal conditioning-feature rank panels (NO PnL).

For EACH of the six V14 D1 proposals, compute its frozen conditioning
feature at its frozen decision clock (weekly Monday 00:00:00Z stamps,
2025-08-25..2026-08-17, 52 stamps, blind-S0 screen window) using ONLY
fully-closed prior buckets/rows under each proposal's frozen lag
convention, and write a deterministic rank panel
(decision stamp x symbol -> feature rank) for A7-N cross-cluster
correlation.

Fail-closed eligibility: a symbol is eligible at a stamp only when every
bucket/row its frozen statistic requires exists in the staged observables
(L-V12-5; no back-fill, no synthesized tail).  Ranks are ascending
(rank 1 = lowest feature = the proposal's long side) with ties broken by
symbol id ascending (declared a priori in every proposal).

Feature definitions (frozen, from the proposals):
* BASISLV-PREMFADE  : mean over trailing 2688 completed 15m buckets of
                      p_b = (futuresPrice - indexPrice)/indexPrice from
                      /futures/data/basis (lag: close_time <= T).
* BASISLV-WIDTHGATE : mean over trailing 2688 completed 15m buckets of
                      m_b = markClose/indexClose - 1 (lag: close <= T);
                      sidecar: cross-sectional IQR D(T) and the frozen
                      expanding-median gate state (needs >= 6 prior stamps).
* BASISDYN-PREMREV  : (P(T) - P(T-72h)) / sigma_chg(T), P = premiumIndex
                      kline close, sigma_chg = std(ddof=1) over the 30
                      daily-sampled trailing 72h changes (declared staged
                      interpretation; lag: o + 15m < T strictly).
* BASISDYN-PREMVOL  : std(ddof=1) of consecutive 15m premium-close
                      changes over the trailing 30d window (lag: strict).
* OICH              : std(ddof=1) of the 28 most recent daily log OI
                      changes with end-row stamps <= T (v11_oi_staging_v1;
                      consecutive-ness by day-row index).
* OICYC             : OLS slope of the symbol's daily log OI changes on
                      the leave-one-out 18-symbol aggregate over the same
                      28 paired changes (needs the full 19-symbol
                      cross-section on every day-row in the window).

No positions, no weights that depend on returns, no PnL, no selection or
novelty verdicts.
"""

from __future__ import annotations

import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
STAGED = HERE / "staged"
PANELS = HERE / "panels"
PANELS.mkdir(parents=True, exist_ok=True)
OI_ROOT = Path("/Users/hoangminhlong/my-quantitative/oi_data/consolidated")

UNIVERSE = [
    "1000PEPEUSDT", "AAVEUSDT", "ACEUSDT", "ADAUSDT", "AVAXUSDT",
    "BCHUSDT", "BNBUSDT", "BOMEUSDT", "DOGEUSDT", "ENAUSDT",
    "ETHUSDT", "LINKUSDT", "NEARUSDT", "ONGUSDT", "SOLUSDT",
    "SUIUSDT", "WLDUSDT", "XRPUSDT", "ZECUSDT",
]
BUCKET_MS = 900_000
WINDOW_START_MS = 1724112000000
LAST_BUCKET_OPEN_MS = 1787355900000  # 2026-08-21T23:45Z
EXPECTED_BUCKETS = (LAST_BUCKET_OPEN_MS - WINDOW_START_MS) // BUCKET_MS + 1

FIRST_STAMP = "2025-08-25T00:00:00Z"
LAST_STAMP = "2026-08-17T00:00:00Z"
DAY = 86_400_000


def iso_ms(iso: str) -> int:
    dt = datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    return int(dt.timestamp()) * 1000


def ms_iso(ms: int) -> str:
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


STAMPS = list(range(iso_ms(FIRST_STAMP), iso_ms(LAST_STAMP) + 1, 7 * DAY))
assert len(STAMPS) == 52


def load_route(route: str, symbol: str, value_col: str) -> tuple[np.ndarray, np.ndarray]:
    path = STAGED / f"{symbol}_{route}_15m.parquet"
    table = pq.read_table(path)
    opens = np.asarray(table.column("open_time_ms").to_pylist(), dtype=np.int64)
    vals = np.asarray(table.column(value_col).to_pylist(), dtype=np.float64)
    return opens, vals


#: Malformed-value classes discovered by A9-F staging evidence:
#: 'zero'         -- premiumIndexKlines close emits exact 0.0 when the
#:                   premium index did not update at the bucket boundary
#:                   (high/low carry real extremes; mark klines carry forward,
#:                   premium klines do not).  0.0 is a sentinel, never a real
#:                   premium rate.
#: 'nonpositive'  -- price-level fields (mark/index/futures prices) must be > 0.
MALFORMED_RULE = {
    "premium_close": "zero",
    "mark_close": "nonpositive",
    "index_close": "nonpositive",
    "futures_price": "nonpositive",
    "index_price": "nonpositive",
}


def malformed_mask(vals: np.ndarray, value_col: str) -> np.ndarray:
    rule = MALFORMED_RULE.get(value_col)
    if rule == "zero":
        return vals == 0.0
    if rule == "nonpositive":
        return vals <= 0.0
    return np.zeros(vals.shape, dtype=bool)


def route_quality(route: str, symbol: str, value_col: str) -> dict:
    opens, vals = load_route(route, symbol, value_col)
    bad = malformed_mask(vals, value_col) | ~np.isfinite(vals)
    count = int(np.sum(bad))
    out = {"malformed_or_nonfinite": count, "share": float(count) / len(vals)}
    if count:
        first = int(opens[bad][0])
        last = int(opens[bad][-1])
        out["first_utc"] = ms_iso(first)
        out["last_utc"] = ms_iso(last)
    return out


def trailing_window(
    opens: np.ndarray,
    vals: np.ndarray,
    first_open: int,
    last_open: int,
    value_col: str,
) -> np.ndarray:
    """Values for buckets opens in [first_open, last_open]; None when any slot
    is missing or malformed (fail-closed; L-V12-5)."""
    lo = np.searchsorted(opens, first_open, side="left")
    hi = np.searchsorted(opens, last_open, side="right")
    grid_expected = (last_open - first_open) // BUCKET_MS + 1
    if hi - lo != grid_expected:
        return None  # slot missing
    seg = vals[lo:hi]
    if not np.all(np.isfinite(seg)) or malformed_mask(seg, value_col).any():
        return None  # slot malformed (incl. premium-close 0.0 sentinel)
    return seg


def rank_map(values: dict[str, float]) -> dict[str, int]:
    items = sorted(values.items(), key=lambda kv: (kv[1], kv[0]))
    return {sym: idx + 1 for idx, (sym, _) in enumerate(items)}


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cross_stats(vals: dict[str, float]) -> dict:
    arr = np.asarray(sorted(vals.values()), dtype=np.float64)
    q1, q3 = np.percentile(arr, [25.0, 75.0])
    return {
        "n": int(arr.size),
        "iqr": float(q3 - q1),
        "std": float(np.std(arr, ddof=1)) if arr.size >= 2 else None,
        "min": float(arr[0]),
        "max": float(arr[-1]),
    }


def finalize(name: str, payload: dict) -> Path:
    payload.setdefault("deterministic", True)
    target = PANELS / name
    with open(target, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=1, sort_keys=True)
        handle.write("\n")
    return target


def build_basis_level_panels() -> dict[str, Path]:
    """PREMFADE (basis route) and WIDTHGATE (mark/index route) + gate sidecar."""
    basis_vals: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    mark_vals: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    index_vals: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    prem_vals: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    max_basis_identity_violation = 0.0
    max_premium_identity_violation = 0.0
    basis_identity_by_symbol: dict[str, float] = {}
    premium_identity_by_symbol: dict[str, float] = {}
    BASIS_IDENTITY_TOL = 1e-4    # basisRate is endpoint-rounded to 4 decimal places
    PREMIUM_IDENTITY_TOL = 1e-3  # measured abs deviation ~<= 4.2e-4 (probe sample, BTCUSDT)

    for sym in UNIVERSE:
        opens_b, fut = load_route("basis", sym, "futures_price")
        idx = load_route("basis", sym, "index_price")[1]
        basis_rate = np.asarray(
            pq.read_table(STAGED / f"{sym}_basis_15m.parquet").column("basis_rate").to_pylist(),
            dtype=np.float64,
        )
        basis_vals[sym] = (opens_b, fut, idx)
        with np.errstate(divide="ignore", invalid="ignore"):
            computed = (fut - idx) / idx
        mask = np.isfinite(computed) & np.isfinite(basis_rate)
        if mask.any():
            viol = float(np.max(np.abs(computed[mask] - basis_rate[mask])))
            basis_identity_by_symbol[sym] = viol
            max_basis_identity_violation = max(max_basis_identity_violation, viol)
        opens_m, mclose = load_route("mark_klines", sym, "mark_close")
        opens_i, iclose = load_route("index_klines", sym, "index_close")
        opens_p, pclose = load_route("premium_klines", sym, "premium_close")
        mark_vals[sym] = (opens_m, mclose)
        index_vals[sym] = (opens_i, iclose)
        prem_vals[sym] = (opens_p, pclose)
        if not (np.array_equal(opens_m, opens_i) and np.array_equal(opens_m, opens_p)):
            raise RuntimeError(f"{sym}: kline open grids differ across routes")
        # WIDTHGATE staging identity cross-check: m_b vs premiumIndex close.
        # Binance computes the premium kline from higher-frequency mark/index
        # snapshots, so it is NOT exactly markClose/indexClose - 1 per bucket;
        # the check verifies route/grid coherence at a declared absolute band.
        with np.errstate(divide="ignore", invalid="ignore"):
            m_b = mclose / iclose - 1.0
        # exclude sentinel closes (premium index not written at boundary):
        # comparing m_b against the 0.0 sentinel would manufacture violations
        mask = np.isfinite(m_b) & np.isfinite(pclose) & (pclose != 0.0)
        if mask.any():
            viol = float(np.max(np.abs(m_b[mask] - pclose[mask])))
            premium_identity_by_symbol[sym] = viol
            max_premium_identity_violation = max(max_premium_identity_violation, viol)

    def level_series(route_vals, kind: str) -> tuple[dict, dict]:
        values: dict[str, dict[str, float]] = {ms_iso(t): {} for t in STAMPS}
        eligible: dict[str, int] = {}
        for t in STAMPS:
            stamp_iso = ms_iso(t)
            last_open = t - BUCKET_MS  # close_time <= T
            first_open = last_open - (2688 - 1) * BUCKET_MS
            for sym in UNIVERSE:
                if kind == "basis":
                    opens, fut, idx = route_vals[sym]
                    seg_f = trailing_window(opens, fut, first_open, last_open, "futures_price")
                    seg_i = trailing_window(opens, idx, first_open, last_open, "index_price")
                    if seg_f is None or seg_i is None:
                        continue
                    with np.errstate(divide="ignore", invalid="ignore"):
                        p_b = (seg_f - seg_i) / seg_i
                    if not np.all(np.isfinite(p_b)):
                        continue
                    values[stamp_iso][sym] = float(np.mean(p_b))
                else:
                    opens_m, mclose = route_vals[sym]
                    opens_i, iclose = index_vals[sym]
                    seg_m = trailing_window(opens_m, mclose, first_open, last_open, "mark_close")
                    seg_i = trailing_window(opens_i, iclose, first_open, last_open, "index_close")
                    if seg_m is None or seg_i is None:
                        continue
                    with np.errstate(divide="ignore", invalid="ignore"):
                        m_b = seg_m / seg_i - 1.0
                    if not np.all(np.isfinite(m_b)):
                        continue
                    values[stamp_iso][sym] = float(np.mean(m_b))
            eligible[stamp_iso] = len(values[stamp_iso])
        return values, eligible

    fade_values, fade_eligible = level_series(basis_vals, "basis")
    width_values, width_eligible = level_series(mark_vals, "mark")

    # WIDTHGATE gate series (expanding strictly-prior median of D(T); >= 6 priors).
    gate = {}
    d_series: list[tuple[int, float]] = []
    for t in STAMPS:
        stamp_iso = ms_iso(t)
        vals = width_values[stamp_iso]
        d_t = cross_stats(vals)["iqr"] if len(vals) >= 2 else None
        priors = [d for ts, d in d_series]
        open_state = None
        if d_t is not None and len(priors) >= 6:
            med = float(np.median(priors))
            open_state = bool(d_t > med)
        if d_t is not None:
            d_series.append((t, d_t))
        gate[stamp_iso] = {
            "D_iqr": d_t,
            "n_prior_stamps": len(priors),
            "gate_open": open_state,
        }
    opens_count = sum(1 for g in gate.values() if g["gate_open"] is True)
    decided = sum(1 for g in gate.values() if g["gate_open"] is not None)

    staged_manifest = json.load(open(HERE / "staged_basis_manifest.json", encoding="utf-8"))
    input_shas = {
        key: entry["sha256"] for key, entry in staged_manifest["entries"].items()
    }
    quality_basis = {
        sym: {
            "futures_price": route_quality("basis", sym, "futures_price"),
            "index_price": route_quality("basis", sym, "index_price"),
        }
        for sym in UNIVERSE
    }
    quality_mark = {sym: route_quality("mark_klines", sym, "mark_close") for sym in UNIVERSE}
    quality_index = {sym: route_quality("index_klines", sym, "index_close") for sym in UNIVERSE}

    fade_payload = {
        "schema": "v14_d2_a9f_rank_panel_v1",
        "cycle": "CRYPTO-V14",
        "producer_role": "A9-F",
        "proposal": "BASISLV-PREMFADE",
        "hypothesis_id": "A14-V14-A5-BASISLV-PREMFADE",
        "feature_id": "premfade_28d_mean_premium_level",
        "feature_definition": "mean over trailing 2688 completed 15m buckets of p_b=(futuresPrice-indexPrice)/indexPrice from /futures/data/basis (contractType=PERPETUAL, pair=, period=15m)",
        "lag_convention": "bucket usable iff open+15m <= T (bar-close class; last bucket [Sun 23:45, Mon 00:00))",
        "stamp_calendar": {"first": FIRST_STAMP, "last": LAST_STAMP, "count": len(STAMPS), "step_days": 7},
        "universe": UNIVERSE,
        "decision_stamps_iso": [ms_iso(t) for t in STAMPS],
        "values": fade_values,
        "ranks": {ms_iso(t): rank_map(fade_values[ms_iso(t)]) for t in STAMPS},
        "eligible_count": fade_eligible,
        "eligibility_rule": "all 2688 buckets of the formation window exist and finite (fail-closed)",
        "cross_section_stats": {
            ms_iso(t): cross_stats(fade_values[ms_iso(t)]) for t in STAMPS if fade_values[ms_iso(t)]
        },
        "staging_identity_check": {
            "tolerance_abs": BASIS_IDENTITY_TOL,
            "max_abs_violation_all_symbols": max_basis_identity_violation,
            "per_symbol_max_abs_violation": basis_identity_by_symbol,
            "pass": max_basis_identity_violation <= BASIS_IDENTITY_TOL,
            "note": "p_b vs endpoint basisRate; basisRate is rounded to 4 decimal places by the endpoint, so the declared tolerance is absolute 1e-4",
        },
        "data_quality": {
            "basis_route": quality_basis,
            "note": "price-level fields must be > 0 (nonpositive counts malformed; premium rates may be negative and are not malformed)",
        },
        "inputs_sha256": input_shas,
        "no_pnl": True,
        "notes": [
            "rank 1 = lowest premium level = anchor long side",
            "BTCUSDT excluded (benchmark/context only, never ranked)",
        ],
    }
    width_payload = {
        "schema": "v14_d2_a9f_rank_panel_v1",
        "cycle": "CRYPTO-V14",
        "producer_role": "A9-F",
        "proposal": "BASISLV-WIDTHGATE",
        "hypothesis_id": "A14-V14-A5-BASISLV-WIDTHGATE",
        "feature_id": "widthgate_28d_mean_mark_index_premium_level",
        "feature_definition": "mean over trailing 2688 completed 15m buckets of m_b=markClose/indexClose-1 (markPriceKlines symbol= / indexPriceKlines pair=)",
        "lag_convention": "bucket usable iff open+15m <= T (bar-close class)",
        "stamp_calendar": {"first": FIRST_STAMP, "last": LAST_STAMP, "count": len(STAMPS), "step_days": 7},
        "universe": UNIVERSE,
        "decision_stamps_iso": [ms_iso(t) for t in STAMPS],
        "values": width_values,
        "ranks": {ms_iso(t): rank_map(width_values[ms_iso(t)]) for t in STAMPS},
        "eligible_count": width_eligible,
        "eligibility_rule": "all 2688 buckets of the formation window exist on BOTH routes at identical open times and finite (fail-closed)",
        "cross_section_stats": {
            ms_iso(t): cross_stats(width_values[ms_iso(t)]) for t in STAMPS if width_values[ms_iso(t)]
        },
        "gate_sidecar": {
            "rule": "gate OPEN iff D(T) = cross-sectional IQR of the 28d levels > median of strictly-prior stamp IQRs (expanding; requires >= 6 prior stamps; undecided stamps flat)",
            "series": gate,
            "open_stamps": opens_count,
            "decided_stamps": decided,
            "open_frequency_of_decided": (opens_count / decided) if decided else None,
        },
        "staging_identity_check": {
            "tolerance_abs": PREMIUM_IDENTITY_TOL,
            "max_abs_violation_all_symbols": max_premium_identity_violation,
            "per_symbol_max_abs_violation": premium_identity_by_symbol,
            "pass": max_premium_identity_violation <= PREMIUM_IDENTITY_TOL,
            "note": "m_b vs premiumIndexKlines close; Binance derives the premium kline from higher-frequency mark/index snapshots, so equality at close is not exact -- declared absolute band 1e-3 vs measured max ~4.2e-4 (probe sample); the check verifies route/grid coherence, not exact identity",
        },
        "data_quality": {
            "mark_klines": quality_mark,
            "index_klines": quality_index,
            "note": "price-level fields must be > 0 (nonpositive counts malformed); mark/index klines carry forward and showed no zero sentinels on staged symbols",
        },
        "inputs_sha256": input_shas,
        "no_pnl": True,
        "notes": [
            "rank 1 = lowest premium level = long side of the same inside book",
            "gate sidecar is conditioning-state measurement only (no PnL)",
        ],
    }
    return {
        "fade": finalize("panel_BASISLV-PREMFADE.json", fade_payload),
        "width": finalize("panel_BASISLV-WIDTHGATE.json", width_payload),
    }


def build_premrev_panel() -> Path:
    """PREMREV: standardized 72h premium change (strict lag, premium route)."""
    series: dict[str, tuple[np.ndarray, np.ndarray]] = {
        sym: load_route("premium_klines", sym, "premium_close") for sym in UNIVERSE
    }

    def P(sym: str, t: int) -> float | None:
        """Premium close of the last readable bucket at t (o + 15m < t strictly).

        Exact 0.0 closes are the endpoint's not-written sentinel (measured:
        open/high/low carry real values, close does not, when the premium
        index did not update at the boundary instant) -> malformed, refuse.
        """
        opens, vals = series[sym]
        idx = np.searchsorted(opens, t - BUCKET_MS, side="left") - 1
        if idx < 0:
            return None
        o = int(opens[idx])
        if o + BUCKET_MS >= t:
            return None
        v = float(vals[idx])
        if v == 0.0 or not math.isfinite(v):
            return None
        return v

    values: dict[str, dict[str, float]] = {ms_iso(t): {} for t in STAMPS}
    eligible: dict[str, int] = {}
    for t in STAMPS:
        stamp_iso = ms_iso(t)
        for sym in UNIVERSE:
            p_now = P(sym, t)
            p_72 = P(sym, t - 72 * 3600 * 1000)
            if p_now is None or p_72 is None:
                continue
            changes = []
            ok = True
            for k in range(30):
                t_hi = t - k * DAY
                t_lo = t_hi - 72 * 3600 * 1000
                hi = P(sym, t_hi)
                lo = P(sym, t_lo)
                if hi is None or lo is None or lo == 0.0 or hi == 0.0:
                    ok = False
                    break
                changes.append(hi - lo)
            if not ok or len(changes) < 2:
                continue
            sigma = float(np.std(np.asarray(changes), ddof=1))
            if not math.isfinite(sigma) or sigma <= 0.0:
                continue
            values[stamp_iso][sym] = float((p_now - p_72) / sigma)
        eligible[stamp_iso] = len(values[stamp_iso])

    quality = {sym: route_quality("premium_klines", sym, "premium_close") for sym in UNIVERSE}

    staged_manifest = json.load(open(HERE / "staged_basis_manifest.json", encoding="utf-8"))
    payload = {
        "schema": "v14_d2_a9f_rank_panel_v1",
        "cycle": "CRYPTO-V14",
        "producer_role": "A9-F",
        "proposal": "BASISDYN-PREMREV",
        "hypothesis_id": "A14-V14-A6-BASISDYN-PREMREV",
        "feature_id": "premrev_72h_standardized_premium_change",
        "feature_definition": "m_s(T) = (P_s(T) - P_s(T-72h)) / sigma_chg_s(T); P = premiumIndexKlines 15m close; sigma_chg = std(ddof=1) over the 30 daily-sampled trailing 72h changes (declared staged interpretation of 'consecutive 72h premium changes' over the trailing 30d)",
        "lag_convention": "bucket with open o readable at T iff o + 15m < T STRICTLY (proposal section 4; last readable bucket closes 23:45Z Sunday)",
        "stamp_calendar": {"first": FIRST_STAMP, "last": LAST_STAMP, "count": len(STAMPS), "step_days": 7},
        "universe": UNIVERSE,
        "decision_stamps_iso": [ms_iso(t) for t in STAMPS],
        "values": values,
        "ranks": {ms_iso(t): rank_map(values[ms_iso(t)]) for t in STAMPS},
        "eligible_count": eligible,
        "eligibility_rule": "P(T), P(T-72h) and all 30 daily-sampled 72h changes defined from strictly-closed prior buckets, none malformed (fail-closed; requires ~33d continuous history)",
        "cross_section_stats": {
            ms_iso(t): cross_stats(values[ms_iso(t)]) for t in STAMPS if values[ms_iso(t)]
        },
        "data_quality": {
            "premium_close_zero_sentinel": quality,
            "note": "exact 0.0 premium closes are the endpoint's not-written sentinel (verified against raw rows: open/high/low real, close 0, when the premium index did not update at the boundary); treated malformed fail-closed per L-V12-5",
        },
        "inputs_sha256": {
            key: entry["sha256"]
            for key, entry in staged_manifest["entries"].items()
            if key.startswith("premium_klines")
        },
        "no_pnl": True,
        "notes": [
            "rank 1 = most negative standardized 72h premium change = anchor long side",
            "sigma interpretation ambiguity declared: daily-sampled 72h changes (30 per 30d window); an every-15m-overlapping reading changes only the sigma scale, not the rank ordering of the numerator",
        ],
    }
    return finalize("panel_BASISDYN-PREMREV.json", payload)


def build_premvol_panel() -> Path:
    """PREMVOL: 30d std of consecutive 15m premium-close changes (strict lag)."""
    values: dict[str, dict[str, float]] = {ms_iso(t): {} for t in STAMPS}
    eligible: dict[str, int] = {}
    for sym in UNIVERSE:
        opens, vals = load_route("premium_klines", sym, "premium_close")
        for t in STAMPS:
            stamp_iso = ms_iso(t)
            last_open = t - 2 * BUCKET_MS  # o + 15m < T strictly
            first_open = last_open - (2880 - 1) * BUCKET_MS  # 30d of buckets
            seg = trailing_window(opens, vals, first_open, last_open, "premium_close")
            if seg is None:
                continue
            diffs = np.diff(seg)
            if diffs.size < 2 or not np.all(np.isfinite(diffs)):
                continue
            sigma = float(np.std(diffs, ddof=1))
            if math.isfinite(sigma) and sigma > 0.0:
                values[stamp_iso][sym] = sigma
    for t in STAMPS:
        eligible[ms_iso(t)] = len(values[ms_iso(t)])
    quality = {sym: route_quality("premium_klines", sym, "premium_close") for sym in UNIVERSE}
    staged_manifest = json.load(open(HERE / "staged_basis_manifest.json", encoding="utf-8"))
    payload = {
        "schema": "v14_d2_a9f_rank_panel_v1",
        "cycle": "CRYPTO-V14",
        "producer_role": "A9-F",
        "proposal": "BASISDYN-PREMVOL",
        "hypothesis_id": "A14-V14-A6-BASISDYN-PREMVOL",
        "feature_id": "premvol_30d_premium_volatility",
        "feature_definition": "sigma_prem_s(T) = std(ddof=1) of consecutive 15m premiumIndexKlines-close changes over the trailing 30d window of strictly-closed buckets",
        "lag_convention": "bucket with open o readable at T iff o + 15m < T STRICTLY (proposal section 4)",
        "stamp_calendar": {"first": FIRST_STAMP, "last": LAST_STAMP, "count": len(STAMPS), "step_days": 7},
        "universe": UNIVERSE,
        "decision_stamps_iso": [ms_iso(t) for t in STAMPS],
        "values": values,
        "ranks": {ms_iso(t): rank_map(values[ms_iso(t)]) for t in STAMPS},
        "eligible_count": eligible,
        "eligibility_rule": "all 2880 buckets of the trailing 30d window exist, finite and non-malformed (fail-closed; premium-close 0.0 sentinel refused)",
        "cross_section_stats": {
            ms_iso(t): cross_stats(values[ms_iso(t)]) for t in STAMPS if values[ms_iso(t)]
        },
        "data_quality": {
            "premium_close_zero_sentinel": quality,
            "note": "see PREMREV panel note; PREMVOL's 2880-slot window makes malformed-bucket refusal far more binding than PREMREV's 31-bucket footprint",
        },
        "inputs_sha256": {
            key: entry["sha256"]
            for key, entry in staged_manifest["entries"].items()
            if key.startswith("premium_klines")
        },
        "no_pnl": True,
        "notes": ["rank 1 = lowest premium volatility = anchor long side"],
    }
    return finalize("panel_BASISDYN-PREMVOL.json", payload)


def load_oi_rows(sym: str) -> list[tuple[int, float]]:
    table = pq.read_table(OI_ROOT / f"{sym}_oi.parquet")
    rows = []
    for text, val in zip(
        table.column("create_time").to_pylist(),
        table.column("sum_open_interest").to_pylist(),
    ):
        ts = int(
            datetime.strptime(str(text).strip(), "%Y-%m-%d %H:%M:%S")
            .replace(tzinfo=timezone.utc)
            .timestamp()
        )
        rows.append((ts, float(val)))
    rows.sort()
    return rows


def build_oi_panels() -> dict[str, Path]:
    """OICH (churn dispersion) and OICYC (leave-one-out cycle slope)."""
    oi = {sym: load_oi_rows(sym) for sym in UNIVERSE}

    def dlog_series(sym: str, t: int) -> list[tuple[int, float]]:
        rows = [r for r in oi[sym] if r[0] <= t]
        out = []
        for (t0, v0), (t1, v1) in zip(rows, rows[1:]):
            if v0 > 0 and v1 > 0 and math.isfinite(v0) and math.isfinite(v1):
                out.append((t1, math.log(v1 / v0)))
            else:
                out.append((t1, float("nan")))
        return out

    dlog_cache: dict[str, dict[int, dict[int, float]]] = {sym: {} for sym in UNIVERSE}
    for t in STAMPS:
        for sym in UNIVERSE:
            dlog_cache[sym][t] = dict(dlog_series(sym, t))

    # OICH
    values_ch: dict[str, dict[str, float]] = {ms_iso(t): {} for t in STAMPS}
    for t in STAMPS:
        stamp_iso = ms_iso(t)
        for sym in UNIVERSE:
            series = sorted(dlog_cache[sym][t].items())
            last28 = [v for _, v in series[-28:]]
            if len(last28) < 28 or not all(math.isfinite(v) for v in last28):
                continue
            values_ch[stamp_iso][sym] = float(np.std(np.asarray(last28), ddof=1))
    eligible_ch = {ms_iso(t): len(values_ch[ms_iso(t)]) for t in STAMPS}

    # OICYC: leave-one-out aggregate over the last 28 paired day-rows
    values_cyc: dict[str, dict[str, float]] = {ms_iso(t): {} for t in STAMPS}
    for t in STAMPS:
        stamp_iso = ms_iso(t)
        base = dlog_cache[UNIVERSE[0]][t]
        common_days = set(base)
        for sym in UNIVERSE:
            common_days &= set(dlog_cache[sym][t])
        common_days = sorted(common_days)[-28:]
        if len(common_days) < 28:
            continue
        for sym in UNIVERSE:
            own = np.asarray([dlog_cache[sym][t][d] for d in common_days])
            if not np.all(np.isfinite(own)):
                continue
            agg_rows = []
            ok = True
            for d in common_days:
                others = [
                    dlog_cache[j][t][d] for j in UNIVERSE if j != sym
                ]
                if not all(math.isfinite(v) for v in others):
                    ok = False
                    break
                agg_rows.append(float(np.mean(others)))
            if not ok:
                continue
            m = np.asarray(agg_rows)
            var_m = float(np.var(m, ddof=1))
            if var_m <= 0.0:
                continue
            cov = float(np.cov(own, m, ddof=1)[0, 1])
            values_cyc[stamp_iso][sym] = cov / var_m
    eligible_cyc = {ms_iso(t): len(values_cyc[ms_iso(t)]) for t in STAMPS}

    oi_manifest = json.load(
        open(HERE.parents[2] / "control" / "v11_run" / "oi_staging_manifest.json", encoding="utf-8")
    )
    input_shas = {
        f"{s}_oi.parquet": spec["parquet_sha256"] for s, spec in oi_manifest["symbols"].items()
    }
    common = {
        "schema": "v14_d2_a9f_rank_panel_v1",
        "cycle": "CRYPTO-V14",
        "producer_role": "A9-F",
        "stamp_calendar": {"first": FIRST_STAMP, "last": LAST_STAMP, "count": len(STAMPS), "step_days": 7},
        "universe": UNIVERSE,
        "decision_stamps_iso": [ms_iso(t) for t in STAMPS],
        "lag_convention": "daily OI rows with create_time <= T; consecutive-ness by day-row index (stamps read per row, never assumed)",
        "inputs_sha256": input_shas,
        "no_pnl": True,
    }
    ch_payload = {
        **common,
        "proposal": "OICH",
        "hypothesis_id": "A14-V14-A8-OICH",
        "feature_id": "oich_28d_daily_oi_churn_dispersion",
        "feature_definition": "CH_s(T) = std(ddof=1) of the 28 most recent daily log open-interest changes whose end-row stamps <= T (v11_oi_staging_v1 sum_open_interest; requires 29 consecutive day-rows)",
        "values": values_ch,
        "ranks": {ms_iso(t): rank_map(values_ch[ms_iso(t)]) for t in STAMPS},
        "eligible_count": eligible_ch,
        "eligibility_rule": "29 consecutive day-rows <= T with positive finite OI on both rows of every pair (fail-closed)",
        "cross_section_stats": {
            ms_iso(t): cross_stats(values_ch[ms_iso(t)]) for t in STAMPS if values_ch[ms_iso(t)]
        },
        "notes": ["rank 1 = lowest churn = anchor long side"],
    }
    cyc_payload = {
        **common,
        "proposal": "OICYC",
        "hypothesis_id": "A14-V14-A8-OICYC",
        "feature_id": "oicyc_28d_leave_one_out_cycle_slope",
        "feature_definition": "CYC_s(T) = OLS slope of dlog_s on the leave-one-out mean aggregate M(d) (mean over the other 18 tradeable symbols' daily log OI changes) over the 28 most recent paired daily changes with end-row stamps <= T; defined iff Var(M) > 0",
        "values": values_cyc,
        "ranks": {ms_iso(t): rank_map(values_cyc[ms_iso(t)]) for t in STAMPS},
        "eligible_count": eligible_cyc,
        "eligibility_rule": "the full 19-symbol cross-section has finite log changes on EVERY day-row of the 28-change window (fail-closed, no partial aggregate)",
        "cross_section_stats": {
            ms_iso(t): cross_stats(values_cyc[ms_iso(t)]) for t in STAMPS if values_cyc[ms_iso(t)]
        },
        "notes": ["rank 1 = lowest cycle beta = anchor long side"],
    }
    return {
        "oich": finalize("panel_OICH.json", ch_payload),
        "oicyc": finalize("panel_OICYC.json", cyc_payload),
    }


def main() -> None:
    built: dict[str, str] = {}
    for name, path in build_basis_level_panels().items():
        built[f"BASISLV-{name}"] = str(path)
    built["BASISDYN-PREMREV"] = str(build_premrev_panel())
    built["BASISDYN-PREMVOL"] = str(build_premvol_panel())
    for name, path in build_oi_panels().items():
        built[f"A8-{name}"] = str(path)
    index = {
        "schema": "v14_d2_a9f_panel_index_v1",
        "cycle": "CRYPTO-V14",
        "producer_role": "A9-F",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "panels": {
            key: {"path": path, "sha256": sha256_file(Path(path))} for key, path in built.items()
        },
        "purpose": "A7-N cross-cluster rank correlation input (conditioning-feature ranks only; no PnL)",
    }
    with open(HERE / "panel_index.json", "w", encoding="utf-8") as handle:
        json.dump(index, handle, indent=1, sort_keys=True)
        handle.write("\n")
    print(json.dumps({k: v["sha256"][:12] for k, v in index["panels"].items()}, indent=1))


if __name__ == "__main__":
    main()
