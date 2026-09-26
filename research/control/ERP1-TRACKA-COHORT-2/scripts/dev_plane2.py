"""ERP1-TRACKA-COHORT-2 — dev-plane loader with sealed-window enforcement.

Law: the 2026-01-01..2026-06-30 holdout bars physically exist inside the
inherited parquets (lane-A finding). The ONLY thing that keeps them sealed
is the timestamp filter below plus the row-count assertion. Every consumer
of a DEV plane must go through this module (or re-assert the same two
checks); any direct parquet read for scoring purposes is a law violation.

Dev row-count pins (lane-A PITDATA_cohort2_REPORT.md A1, measured):
  bars1h_ANC AUDUSD 27608 / USDCAD 27583   (H1 signal-plane convention)
  bars15_ANC AUDUSD 118275 / USDCAD 118231 (15m cost-plane convention)
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

LANE = Path(__file__).resolve().parent.parent
DERIVED = LANE / "data_local" / "derived"
DEV_END = pd.Timestamp("2025-12-31 23:59:59Z")  # sealed filter boundary

DEV_ROW_PINS = {
    ("bars1h_ANC", "AUDUSD"): 27608,
    ("bars1h_ANC", "USDCAD"): 27583,
    ("bars15_ANC", "AUDUSD"): 118275,
    ("bars15_ANC", "USDCAD"): 118231,
}


def load_bars(stem: str, symbol: str, dev_only: bool = True) -> pd.DataFrame:
    """Load an inherited bars parquet. dev_only=True enforces the sealed law."""
    path = DERIVED / f"{stem}_{symbol}.parquet"
    df = pd.read_parquet(path)
    df = df.sort_values("ts").reset_index(drop=True)
    if dev_only:
        df = df[df["ts"] <= DEV_END].reset_index(drop=True)
        pin = DEV_ROW_PINS.get((stem, symbol))
        if pin is None:
            raise ValueError(f"no dev row pin for {stem}/{symbol} — add pin first")
        if len(df) != pin:
            raise AssertionError(
                f"sealed-window violation risk: {stem}/{symbol} dev rows "
                f"{len(df)} != pinned {pin}"
            )
    return df


def sealed_audit() -> dict:
    """Structural audit: dev counts + physical holdout presence (no prices)."""
    out = {"dev_end": str(DEV_END), "files": {}}
    for (stem, symbol), pin in DEV_ROW_PINS.items():
        df = pd.read_parquet(DERIVED / f"{stem}_{symbol}.parquet")
        dev = int((df["ts"] <= DEV_END).sum())
        hold = int((df["ts"] > DEV_END).sum())
        out["files"][f"{stem}_{symbol}"] = {
            "total_rows": int(len(df)),
            "dev_rows": dev,
            "dev_pin": pin,
            "dev_pin_match": dev == pin,
            "holdout_rows_physical": hold,
            "min_ts": str(df["ts"].min()),
            "max_ts": str(df["ts"].max()),
        }
    out["all_pins_match"] = all(v["dev_pin_match"] for v in out["files"].values())
    return out


if __name__ == "__main__":  # pragma: no cover
    print(json.dumps(sealed_audit(), indent=1))
