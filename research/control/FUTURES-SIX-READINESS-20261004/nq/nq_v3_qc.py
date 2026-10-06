"""NQ-ALIAS-REPAIR — v3 panel price-sanity + remaining-hole inventory.

Evidence for DATA_READINESS_NQ.md dims 1-2. Read-only on cache_v3.
"""
from __future__ import annotations

import json
import os

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.join(HERE, "cache_v3")

hd = pd.read_parquet(os.path.join(V3, "nq_held_daily_v3.parquet"))
hd["d"] = pd.to_datetime(hd["d"])

# ---- price sanity on the v3 panel (column-read, chunked by parquet) ----
import pyarrow.parquet as pq  # noqa: E402
f = os.path.join(V3, "nq_outright_1m_v3.parquet")
t = pq.read_table(f, columns=["ts_event", "high", "low", "close", "volume"])
high = t["high"].to_numpy().astype("float64")
low = t["low"].to_numpy().astype("float64")
close = t["close"].to_numpy().astype("float64")
vol = t["volume"].to_numpy()
qc = {
    "schema": "nq_v3_qc@1",
    "rows": int(len(close)),
    "negative_prices": int(((low < 0) | (close < 0) | (high < 0)).sum()),
    "high_lt_low": int((high < low).sum()),
    "close_outside_hl": int(((close > high) | (close < low)).sum()),
    "zero_volume_bars": int((vol == 0).sum()),
    "min_close": float(np.nanmin(close)),
    "max_close": float(np.nanmax(close)),
    "baseline_reference": "NQ_a7_quality.json price_sanity (baseline panel): "
                          "all zero violations; min 1699.25 max 31454.75",
}

# ---- low-price investigation: rows below the baseline panel min (1699.25) ----
mask = close < 1699.25e9
odd = pd.DataFrame({
    "dt": pd.to_datetime(t["ts_event"].to_numpy()[mask], unit="ns", utc=True),
    "close": close[mask],
    "volume": vol[mask],
})
held_chk = hd[hd["d"].isin(odd["dt"].dt.normalize().dt.tz_localize(None))]
qc["rows_below_baseline_min_close"] = {
    "n_rows": int(len(odd)),
    "rows": [{"dt_utc": str(r.dt), "close_pts": r.close / 1e9,
              "volume": int(r.volume)} for r in odd.itertuples()],
    "note": "both are instrument-16908 listing-period single-contract prints "
            "(2018-08-15, 2018-09-13; volume 1 each) recovered from the alias "
            "window; the held chain on those sessions held NQM8_2018 / "
            "NQU8_2018, NOT NQM0_2020 -> zero impact on held closes, rolls, "
            "embed",
    "held_contracts_on_those_sessions":
        held_chk[["d", "contract"]].assign(
            d=lambda x: x["d"].astype(str)).to_dict("records"),
}

# ---- remaining holes on the v3 held chain ----
low_cov = hd[hd["cov"] < 0.6].copy()   # baseline a2 'clean' threshold
holes = {
    "held_sessions": int(len(hd)),
    "nan_close_sessions": int(hd["close"].isna().sum()),
    "low_coverage_sessions_lt_0p6": int(len(low_cov)),
    "low_coverage_dates": [str(x.date()) for x in low_cov["d"]],
    "recovered_window_2020_03_16_to_03_20": [
        {"date": str(r.d.date()), "contract": r.contract,
         "rth_coverage": float(r.cov), "volume": int(r.volume)}
        for r in hd[(hd["d"] >= "2020-03-16") & (hd["d"] <= "2020-03-20")]
        .itertuples()],
}
out = {"schema": "nq_v3_remaining_holes@1", "price_sanity_v3": qc,
       "remaining_holes": holes}
with open(os.path.join(HERE, "v3_qc.json"), "w") as fh:
    json.dump(out, fh, indent=1)
print(json.dumps(qc, indent=1))
print("low-cov sessions:", holes["low_coverage_sessions_lt_0p6"])
print("recovered window 03-16..03-20:", holes["recovered_window_2020_03_16_to_03_20"])
