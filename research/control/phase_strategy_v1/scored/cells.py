"""PSV1 scored: per-cell data/fold/label loaders (reuse of the LANES' frozen
machines verbatim; identity law). A1 scored namespace, post-GO.

Data roots: the raw/staged bytes live in the LANES' worktree-local
data_staging dirs (gitignored by law). The scored run's BINDING precondition
(scored_run_ingest_verification in evaluation_freeze) re-downloads every
manifest entry from data.binance.vision and re-hashes it against the
manifests AND the staged bytes before any of these loaders may run.
"""
from __future__ import annotations

import gzip
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASE = Path(__file__).resolve().parents[1]          # .../phase_strategy_v1
WT = Path("/Users/hoangminhlong/my-quantitative/.worktrees/phase-strategy-v1")
L1_CODE = WT / "lane-btc-h1" / "research/control/phase_strategy_v1/lane_btc_h1/code"
L2_PIPE = WT / "lane-btc-h4" / "research/control/phase_strategy_v1/lane_btc_h4"
L1_STAGE = Path(os.environ.get(
    "PSV1_L1_STAGING",
    str(WT / "lane-btc-h1/research/control/phase_strategy_v1/lane_btc_h1/data_staging")))
L2_STAGE = Path(os.environ.get(
    "PSV1_L2_STAGING",
    str(WT / "lane-btc-h4/research/control/phase_strategy_v1/lane_btc_h4/data_staging")))
SNAPSHOT = Path(os.environ.get(
    "PSV1_SPY_SNAPSHOT",
    "/Users/hoangminhlong/my-quantitative/.worktrees/jev-regime-router-v1/"
    "integration/research/control/jev_regime_router_v1/data_local/SPY.json.gz"))
SNAPSHOT_SHA256 = "3fd229f9a1b0188fd6037a9d642b144e85a596c4ac4fb9d5f00c7c97cced3803"

L1_FOLD_EDGES = ["2021-05-01", "2023-01-01", "2025-01-01"]  # run_lane fold law


def load_btc_h1() -> dict:
    """Vision 1h panel + frozen L1 labels + fold ids (fold law = eras)."""
    if str(L1_CODE) not in sys.path:
        sys.path.insert(0, str(L1_CODE))
    import phase_rule as pr1  # noqa
    vision = pd.read_parquet(L1_STAGE / "vision_1h.parquet")
    labels_df = pr1.compute_labels(vision)
    opens = pd.to_datetime(labels_df["open_time"], utc=True)
    fold_ids = np.zeros(len(labels_df), dtype=int)
    for i, edge in enumerate(L1_FOLD_EDGES, start=1):
        fold_ids[opens >= pd.Timestamp(edge, tz="UTC")] = i
    return {
        "cell": "BTC_H1",
        "open": labels_df["open"].to_numpy(float),
        "high": labels_df["high"].to_numpy(float),
        "low": labels_df["low"].to_numpy(float),
        "close": labels_df["close"].to_numpy(float),
        "open_ms": (opens.astype("int64") // 1_000_000).to_numpy(),
        "fold_ids": fold_ids,
        "labels_df": labels_df,
        "bps": 6.0,
        "funding_rate": 1.377e-5,
    }


def load_btc_h4() -> dict:
    """Aggregated H4 panel (scored representation) + frozen L2 labels/folds."""
    if str(L2_PIPE) not in sys.path:
        sys.path.insert(0, str(L2_PIPE))
    from pipeline import phase_rule as pr2, census as cen2, config as cfg2  # noqa
    h4 = pd.read_parquet(L2_STAGE / "scored_h4.parquet")
    data_end_ms = int(h4["bucket_ms"].iloc[-1] + cfg2.H4_MS - 1)
    assign = cen2.era_fold_assignment(h4["bucket_ms"], data_end_ms, int(cfg2.WARMUP))
    keep = assign["fold"].notna().to_numpy()
    if not keep.all():
        # lane convention: warmup buckets are excluded from floors/census and
        # from the scored window entirely (truncated, not refused)
        h4 = h4.loc[keep].reset_index(drop=True)
        assign = assign.loc[keep].reset_index(drop=True)
    labels = np.asarray(pr2.classify(h4["close"]))
    fold_ids = np.array([int(f[1:]) - 1 for f in assign["fold"]], dtype=int)
    return {
        "cell": "BTC_H4",
        "open": h4["open"].to_numpy(float),
        "high": h4["high"].to_numpy(float),
        "low": h4["low"].to_numpy(float),
        "close": h4["close"].to_numpy(float),
        "open_ms": h4["bucket_ms"].to_numpy(),
        "fold_ids": fold_ids,
        "labels": labels,
        "bps": 6.0,
        "funding_rate": 1.377e-5,
    }


def load_spy() -> dict:
    """Frozen SPY snapshot (digest-verified). Adjusted series used for BOTH
    signal and accounting (dividend-aware); raw open rescaled by the
    per-session adjustment factor (disclosed)."""
    raw = SNAPSHOT.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SNAPSHOT_SHA256:
        raise ValueError("SPY snapshot digest mismatch — fail closed")
    rows = json.loads(gzip.decompress(raw).decode())
    sessions = rows if isinstance(rows, list) else rows.get("sessions", rows.get("data"))
    dates = [s["date"] for s in sessions]
    close_raw = np.array([float(s["close"]) for s in sessions])
    adj = np.array([float(s.get("adjusted_close", s["close"])) for s in sessions])
    open_raw = np.array([float(s["open"]) for s in sessions])
    safe_raw = np.where(close_raw == 0.0, 1.0, close_raw)
    factor = np.where(close_raw > 0, adj / safe_raw, 1.0)
    fold_ids = np.full(len(sessions), -1, dtype=int)
    freeze = json.loads((BASE / "lane_spy_d1" / "freezes" / "era_fold_freeze.json").read_text())
    name_map = {}
    for i, f in enumerate(freeze["folds"]):
        fold_ids[f["session_index_start"]:f["session_index_end"] + 1] = i
        name_map[i] = f["fold_id"]
    if (fold_ids < 0).any():
        # lane convention: pre-warmup sessions (SMA200+slope warmup) are
        # excluded from the scored window (truncated at the first fold)
        start = int(np.argmax(fold_ids >= 0))
        cut = slice(start, len(sessions))
        sessions = sessions[cut]
        dates = dates[cut]
        close_raw = close_raw[cut]
        adj = adj[cut]
        open_raw = open_raw[cut]
        factor = factor[cut]
        fold_ids = fold_ids[cut]
    return {
        "cell": "SPY_D1",
        "open": open_raw * factor,
        "high": np.array([float(s["high"]) for s in sessions]) * factor,
        "low": np.array([float(s["low"]) for s in sessions]) * factor,
        "close": adj,
        "open_ms": np.zeros(len(sessions)),
        "fold_ids": fold_ids,
        "fold_names": name_map,
        "dates": dates,
        "labels": None,
        "bps": 10.0,
        "funding_rate": 0.0,
    }
