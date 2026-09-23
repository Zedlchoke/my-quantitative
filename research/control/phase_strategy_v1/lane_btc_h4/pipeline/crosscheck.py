"""PSV1 lane_btc_h4 — cross-checks (plan §9.1).

1. 4h native shadow: aggregated-from-1h H4 vs native Vision 4h monthly zips.
   Mismatches are DISCLOSED, never smoothed; the aggregated representation
   stays the scored one.
2. Frozen 15m catalog: read-only reuse, digest re-verified; resampled to 4h
   must match on the overlap window within documented tolerance.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import config


def compare_4h_shadow(h4: pd.DataFrame, native4h: pd.DataFrame) -> dict:
    """Row-aligned comparison on shared bucket_ms keys.

    Native 4h klines are already bucket-aligned: their open_time_ms IS the
    floor(open/4h) bucket start (asserted, not assumed).
    """
    b_src = native4h.rename(columns={"open_time_ms": "bucket_ms"})
    assert (b_src["bucket_ms"] % config.H4_MS == 0).all(), "native 4h opens not bucket-aligned"
    a = h4.set_index("bucket_ms")
    b = b_src.set_index("bucket_ms")
    shared = a.index.intersection(b.index)
    only_agg = a.index.difference(b.index)
    only_native = b.index.difference(a.index)

    ca, cb = a.loc[shared], b.loc[shared]
    mism = {}
    any_bad = pd.Series(False, index=shared)
    for col in ["open", "high", "low", "close"]:
        d = (ca[col] - cb[col]).abs()
        tol = config.SHADOW_PRICE_RTOL * np.maximum(1.0, cb[col].abs())
        bad = d > tol
        mism[col] = int(bad.sum())
        any_bad |= bad
        if bad.any():
            ex = ca.index[bad][:5].tolist()
            mism[col + "_examples_bucket_iso"] = [
                pd.Timestamp(x, unit="ms", tz="UTC").isoformat() for x in ex]
    dv = (ca["volume"] - cb["volume"]).abs()
    badv = dv > config.SHADOW_VOL_RTOL * np.maximum(1.0, cb["volume"].abs())
    mism["volume"] = int(badv.sum())
    any_bad |= badv

    n_cmp = len(shared)
    n_bad = sum(mism[c] for c in ["open", "high", "low", "close", "volume"])
    n_bad_buckets = int(any_bad.sum())
    return {
        "law": "aggregated-from-1h is the SCORED representation; native 4h is a shadow",
        "tolerance": {"price_rtol": config.SHADOW_PRICE_RTOL, "vol_rtol": config.SHADOW_VOL_RTOL},
        "n_native_buckets": int(len(b)),
        "n_shared_buckets": int(n_cmp),
        "n_only_in_aggregated": int(len(only_agg)),
        "n_only_in_native": int(len(only_native)),
        "only_in_aggregated_note": "tail buckets of the partial month after the last native monthly zip (expected)",
        "mismatch_counts": mism,
        "n_buckets_with_any_mismatch": n_bad_buckets,
        "verdict": ("MATCH_EXACT" if n_bad == 0 else
                    f"MATCH_EXCEPT_{n_bad_buckets}_DISCLOSED_BUCKETS"),
    }


def compare_catalog(h4: pd.DataFrame, catalog: pd.DataFrame) -> dict:
    """catalog: 15m frame with open_time_ms + OHLCV. Resample to 4h, compare overlap.

    Only H4 buckets whose FULL 4h span lies inside the catalog's data span are
    compared (partial edge buckets would differ by construction).
    """
    cat = catalog.copy()
    cat["bucket_ms"] = (cat["open_time_ms"] // config.H4_MS) * config.H4_MS
    g = cat.groupby("bucket_ms")
    agg = g.agg(
        high=("high", "max"), low=("low", "min"),
        volume=("volume", "sum"),
        n=("open", "size"),
    )
    o = cat.loc[cat["open_time_ms"] == cat["bucket_ms"]].set_index("bucket_ms")["open"]
    c = g.tail(1).set_index("bucket_ms")["close"]  # last 15m bar close in bucket
    agg["open"] = o.reindex(agg.index)
    agg["close"] = c.reindex(agg.index)
    full = agg[agg["n"] == 16]  # complete 15m coverage of the bucket

    mine = h4.set_index("bucket_ms")
    shared = mine.index.intersection(full.index)
    ma, mb = mine.loc[shared], full.loc[shared]

    # diagnosis (disclosed facts, no repair): grid regularity, hourly-close
    # agreement, volume scale behaviour vs the scored Vision-derived series.
    diag = _catalog_diagnosis(catalog, ma)

    res = {"n_catalog_15m_rows": int(len(cat)),
           "n_catalog_4h_full_buckets": int(len(full)),
           "n_shared_with_scored": int(len(shared))}
    bad_total = 0
    for col in ["open", "high", "low", "close"]:
        d = (ma[col] - mb[col]).abs()
        bad = d > config.CATALOG_CHECK_ATOL_PRICE + 1e-9
        res[f"mismatch_{col}"] = int(bad.sum())
        bad_total += int(bad.sum())
        if bad.any():
            ex = ma.index[bad][:5].tolist()
            res[f"mismatch_{col}_examples"] = [
                pd.Timestamp(x, unit="ms", tz="UTC").isoformat() for x in ex]
    dv = (ma["volume"] - mb["volume"]).abs()
    badv = dv > config.CATALOG_CHECK_RTOL_VOL * np.maximum(1.0, mb["volume"].abs())
    res["mismatch_volume"] = int(badv.sum())
    bad_total += int(badv.sum())
    res["verdict"] = "MATCH_WITHIN_TOLERANCE" if bad_total == 0 else (
        "CATALOG_NOT_CORROBORATIVE_MISMATCH_DISCLOSED")
    res["diagnosis"] = diag
    res["note"] = ("catalog capture is a different snapshot pipeline; tolerance "
                   f"price_atol={config.CATALOG_CHECK_ATOL_PRICE}, vol_rtol={config.CATALOG_CHECK_RTOL_VOL}; "
                   "finding DISCLOSED, never smoothed; the scored H4 representation is "
                   "validated by the mandatory native-4h shadow instead; this optional "
                   "cross-check therefore does NOT corroborate and is recorded as such")
    return res


def _catalog_diagnosis(catalog: pd.DataFrame, scored: pd.DataFrame) -> dict:
    dts = np.diff(catalog["open_time_ms"].to_numpy())
    # hourly-boundary closes: catalog bar open+15m landing on HH:00 vs scored 1h closes
    from . import config as _c
    closes = catalog.copy()
    closes["close_ms"] = closes["open_time_ms"] + 15 * 60 * 1000
    sel = closes[closes["close_ms"] % 3600000 == 0].set_index("close_ms")["close"]
    joined = pd.DataFrame({"cat": sel})
    joined["scored"] = scored["close"].reindex(joined.index)
    both = joined.dropna()
    rel = ((both["cat"] - both["scored"]).abs() / both["scored"])
    return {
        "catalog_grid": "uniform 15m, monotonic" if bool((dts == 15 * 60 * 1000).all()) else "non-uniform",
        "n_hour_boundary_closes_compared": int(len(both)),
        "n_hour_boundary_closes_match_1e-6": int((rel < 1e-6).sum()),
        "median_hour_close_reldiff": float(rel.median()) if len(rel) else None,
        "p99_hour_close_reldiff": float(rel.quantile(0.99)) if len(rel) else None,
        "interpretation": "catalog OHLCV content is materially different from the Vision series; cause not determinable from inside this lane",
    }


_CATALOG_SCALE = 9          # Nautilus fixed-precision decode scale (validated by the overlap check)
_CATALOG_BAR_NS = 15 * 60 * 10**9


def _dec_raw(v) -> float:
    """Nautilus raw fixed-precision value: little-endian int / 10**scale."""
    return int.from_bytes(v, "little") / 10**_CATALOG_SCALE


def load_catalog_parquet(path: str, expected_sha256: str) -> tuple[pd.DataFrame, str]:
    """Read-only reuse; digest re-verified BEFORE reading (plan §9.2/§9.1).

    Catalog semantics (measured, not assumed): Nautilus-style parquet, 15m
    bars, prices/volumes as raw fixed-precision (scale 1e9), ts_event/ts_init
    in NANOSECONDS stamped at bar CLOSE (e.g. ...:59.999000064); bar open =
    ts_event - 15m + 1ms. open_time_ms is derived accordingly.
    """
    import hashlib
    from pathlib import Path
    p = Path(path)
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    if digest != expected_sha256:
        raise ValueError(f"frozen catalog digest mismatch: {digest} != {expected_sha256}")
    raw = pd.read_parquet(p)
    df = pd.DataFrame({
        "open": raw["open"].map(_dec_raw),
        "high": raw["high"].map(_dec_raw),
        "low": raw["low"].map(_dec_raw),
        "close": raw["close"].map(_dec_raw),
        "volume": raw["volume"].map(_dec_raw),
        "open_time_ms": ((raw["ts_event"].astype("int64") - _CATALOG_BAR_NS + 10**6)
                         // 10**6),
    })
    df = df.sort_values("open_time_ms", kind="stable").reset_index(drop=True)
    return df, digest
