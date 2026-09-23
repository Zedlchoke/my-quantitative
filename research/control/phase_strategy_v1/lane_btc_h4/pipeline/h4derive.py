"""PSV1 lane_btc_h4 — H4 derivation (binding law, from the V2 census) + integrity.

Derivation law (binding): H4 bucket = floor(open/4h) UTC (00/04/08/12/16/20);
a bucket is COMPLETE iff it contains exactly 4 aligned 1h bars (open times
b, b+1h, b+2h, b+3h); partial buckets are excluded from floors/census.
Aggregated-from-1h is the SCORED representation; native Vision 4h is a shadow.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config
from .ingest import utc_ms_to_iso


def assign_bucket(open_time_ms: pd.Series) -> pd.Series:
    return (open_time_ms // config.H4_MS) * config.H4_MS


def derive_h4(df1h: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """Aggregate complete 1h bars into H4 buckets per the binding law.

    Returns (h4_frame, derivation_report). h4_frame columns:
    bucket_ms, open, high, low, close, volume, quote_volume, count,
    taker_buy_volume, taker_buy_quote_volume.
    """
    df = df1h.copy()
    df["bucket_ms"] = assign_bucket(df["open_time_ms"])
    df["slot_in_bucket"] = (df["open_time_ms"] - df["bucket_ms"]) // config.H1_MS

    g = df.groupby("bucket_ms", sort=True)
    agg = g.agg(
        high=("high", "max"), low=("low", "min"),
        volume=("volume", "sum"), quote_volume=("quote_volume", "sum"),
        count=("count", "sum"),
        taker_buy_volume=("taker_buy_volume", "sum"),
        taker_buy_quote_volume=("taker_buy_quote_volume", "sum"),
    )
    agg["n_bars"] = g.size()

    slot0 = df.loc[df["slot_in_bucket"] == 0].set_index("bucket_ms")["open"]
    slot3 = df.loc[df["slot_in_bucket"] == 3].set_index("bucket_ms")["close"]
    agg["open"] = slot0.reindex(agg.index)
    agg["close"] = slot3.reindex(agg.index)

    # Complete iff exactly 4 distinct aligned slots {0,1,2,3}: n_bars==4 and
    # both the slot-0 open and slot-3 close exist (duplicates already rejected).
    complete = (agg["n_bars"] == 4) & agg["open"].notna() & agg["close"].notna()
    partial = (~complete) & (agg["n_bars"] < 4)
    misaligned = (~complete) & (agg["n_bars"] >= 4)

    h4 = agg.loc[complete, [
        "open", "high", "low", "close", "volume", "quote_volume",
        "count", "taker_buy_volume", "taker_buy_quote_volume",
    ]].reset_index().rename(columns={"bucket_ms": "bucket_ms"})
    h4["count"] = h4["count"].astype("int64")

    report = {
        "law": "bucket=floor(open/4h) UTC; complete iff exactly 4 aligned 1h bars; partial excluded",
        "n_1h_bars_input": int(len(df)),
        "n_h4_complete": int(len(h4)),
        "n_partial_buckets_excluded": int(partial.sum()),
        "n_misaligned_excluded": int(misaligned.sum()),
        "first_bucket": utc_ms_to_iso(int(h4["bucket_ms"].iloc[0])) if len(h4) else None,
        "last_bucket": utc_ms_to_iso(int(h4["bucket_ms"].iloc[-1])) if len(h4) else None,
    }
    return h4, report


def integrity_report(df1h: pd.DataFrame, h4: pd.DataFrame,
                     data_end_ms: int) -> dict:
    """Fail-closed integrity law (plan §9.1). No repair, no smoothing."""
    problems: list[str] = []

    # OHLC sanity on 1h and H4
    for name, d in [("1h", df1h), ("H4", h4)]:
        bad_hl = int((d["high"] < d["low"] - config.PRICE_ATOL).sum())
        bad_c = int(((d["close"] > d["high"] + config.PRICE_ATOL) |
                     (d["close"] < d["low"] - config.PRICE_ATOL)).sum())
        bad_o = int(((d["open"] > d["high"] + config.PRICE_ATOL) |
                     (d["open"] < d["low"] - config.PRICE_ATOL)).sum())
        neg = int((d[["open", "high", "low", "close"]] <= 0).any(axis=1).sum())
        if bad_hl or bad_c or bad_o or neg:
            problems.append(f"{name}: OHLC violations hl={bad_hl} close={bad_c} open={bad_o} nonpos={neg}")

    # Duplicate timestamps (fail-closed — raise upstream, counted here for the report)
    dup1h = int(df1h["open_time_ms"].duplicated().sum())

    # Gap census vs 1h calendar (interior)
    t1 = df1h["open_time_ms"].to_numpy()
    missing_1h, max_run_1h = _gap_stats(t1, config.H1_MS, data_end_ms)

    # Gap census vs 4h UTC calendar over the COMPLETE-bucket span
    t4 = h4["bucket_ms"].to_numpy()
    missing_4h, max_run_4h = _gap_stats(t4, config.H4_MS, data_end_ms)

    # Zero-volume flags
    zv1h = int((df1h["volume"] <= 0).sum())
    zv4h = int((h4["volume"] <= 0).sum())

    # Tolerance law
    n_slots_1h = int((data_end_ms - t1[0]) // config.H1_MS) + 1
    frac_missing = missing_1h / max(1, n_slots_1h)
    verdict = "PASS"
    if frac_missing > config.GAP_TOLERANCE_FRAC:
        verdict = "BLOCKED"
        problems.append(
            f"interior 1h gap fraction {frac_missing:.6f} > tolerance {config.GAP_TOLERANCE_FRAC}")
    if max_run_1h > config.GAP_MAX_RUN_H1:
        verdict = "BLOCKED"
        problems.append(f"longest interior 1h gap run {max_run_1h}h > {config.GAP_MAX_RUN_H1}h")
    if dup1h:
        verdict = "BLOCKED"
        problems.append("duplicate 1h timestamps present")

    return {
        "verdict": verdict,
        "problems": problems,
        "ohlc_checks": "high>=low, close/open in [low,high], all prices > 0 — applied to 1h and H4",
        "duplicates_1h": dup1h,
        "gap_census_1h": {
            "missing_slots": missing_1h,
            "calendar_slots": n_slots_1h,
            "missing_fraction": frac_missing,
            "longest_run_h": max_run_1h,
            "tolerance": {"max_fraction": config.GAP_TOLERANCE_FRAC, "max_run_h": config.GAP_MAX_RUN_H1},
        },
        "gap_census_4h": {
            "missing_slots": missing_4h,
            "longest_run_buckets": max_run_4h,
        },
        "zero_volume_bars": {"h1": zv1h, "h4": zv4h, "note": "flagged, not dropped"},
        "data_end": utc_ms_to_iso(data_end_ms),
    }


def _gap_stats(times_ms: np.ndarray, step_ms: int, data_end_ms: int) -> tuple[int, int]:
    """Interior missing slots and longest missing run within [first, data_end]."""
    if len(times_ms) == 0:
        return 0, 0
    start, end = int(times_ms[0]), min(int(times_ms[-1]), data_end_ms)
    expected = np.arange(start, end + 1, step_ms, dtype=np.int64)
    present = np.unique(times_ms[(times_ms >= start) & (times_ms <= end)])
    missing = np.setdiff1d(expected, present)
    n_missing = len(missing)
    longest = 0
    if n_missing:
        runs = np.split(missing, np.where(np.diff(missing) != step_ms)[0] + 1)
        longest = max(len(r) for r in runs)
    return n_missing, longest
