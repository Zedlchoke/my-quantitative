"""Data-gate artifact tests: manifest digest chain, URL identity, 4h shadow
cross-check on synthetic frames, gate JSON schema. Live-staged zip digests are
re-verified on a sample; tests skip cleanly when staging is absent."""

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from research.control.phase_strategy_v1.lane_btc_h4.pipeline import config
from research.control.phase_strategy_v1.lane_btc_h4.pipeline.crosscheck import (
    compare_4h_shadow, compare_catalog)
from research.control.phase_strategy_v1.lane_btc_h4.pipeline.h4derive import derive_h4

LANE_DIR = Path(__file__).resolve().parents[1]
MANIFEST = LANE_DIR / "data" / "manifest.json"
GATE = LANE_DIR / "data" / "data_gate.json"
STAGING = LANE_DIR / "data_staging"

H1 = config.H1_MS
T0 = 1577836800000


def test_manifest_digest_chain():
    if not MANIFEST.exists():
        pytest.skip("manifest not built yet")
    m = json.loads(MANIFEST.read_text())
    assert m["schema"] == "psv1_lane_btc_h4_data_manifest@1"
    assert m["cell"] == "BTC_H4"
    assert m["first_month"] == "2020-01"
    files = m["files"]
    kinds = {}
    for e in files:
        kinds[e["kind"]] = kinds.get(e["kind"], 0) + 1
        assert e["url"].startswith("https://data.binance.vision/data/futures/um/")
        assert len(e["sha256"]) == 64 and e["bytes"] > 0
        assert e["http_status"] == 200
    assert kinds == {"1h_monthly": 80, "1h_daily": 22, "4h_monthly": 80}
    assert len(files) == 182
    # digest chain re-verified from staged bytes on a deterministic sample
    for e in files[::60]:
        staged = (STAGING / e["local"]).read_bytes()
        assert hashlib.sha256(staged).hexdigest() == e["sha256"]
    assert all(r["digest_match"] for r in m["deterministic_reretrieval_verification"])


def test_gate_verdict_and_pit_disclosure():
    if not GATE.exists():
        pytest.skip("gate not built yet")
    g = json.loads(GATE.read_text())
    assert g["verdict"] in ("PASS_WITH_DISCLOSURES", "BLOCKED")
    assert g["reretrieval_verdict"] == "DETERMINISTIC"
    assert "NEXT H4 bucket open" in g["pit_disclosure"]
    assert g["integrity"]["verdict"] == "PASS"
    assert g["shadow_4h_crosscheck"]["law"].startswith("aggregated-from-1h is the SCORED")


def _synthetic_pair(with_mismatch=False):
    rows1h, rows4h = [], []
    for b in range(6):
        base = T0 + b * config.H4_MS
        for s in range(4):
            px = 100.0 + b + s / 10
            rows1h.append({
                "open_time_ms": base + s * H1, "close_time_ms": base + s * H1 + H1 - 1,
                "open": px, "high": px + 1, "low": px - 1, "close": px + 0.5,
                "volume": 1.0, "quote_volume": px, "count": 5,
                "taker_buy_volume": 0.5, "taker_buy_quote_volume": px / 2,
            })
        o = 100.0 + b                    # slot-0 open
        c = 100.0 + b + 0.8              # slot-3 close (px=100+b+0.3, +0.5)
        rows4h.append({
            "open_time_ms": base, "close_time_ms": base + config.H4_MS - 1,
            "open": o, "high": 0.0, "low": 0.0,
            "close": c, "volume": 4.0, "quote_volume": 400.0, "count": 20,
            "taker_buy_volume": 2.0, "taker_buy_quote_volume": 200.0,
        })
    df1h = pd.DataFrame(rows1h)
    native = pd.DataFrame(rows4h)
    if with_mismatch:
        native.loc[3, "close"] = native.loc[3, "close"] + 1.0
    return df1h, native


def test_shadow_match_and_disclosed_mismatch():
    df1h, native = _synthetic_pair()
    h4, _ = derive_h4(df1h)
    nat = native.copy()
    agg = h4.set_index("bucket_ms")
    for col in ["high", "low"]:  # native highs/lows aligned to the aggregate
        nat[col] = [agg.loc[ms, col] for ms in nat["open_time_ms"]]
    res = compare_4h_shadow(h4, nat)
    assert res["verdict"] == "MATCH_EXACT"
    assert res["n_shared_buckets"] == 6

    nat2 = nat.copy()
    bad_ms = int(agg.index[2])
    nat2.loc[nat2["open_time_ms"] == bad_ms, "close"] += 1.0
    res2 = compare_4h_shadow(h4, nat2)
    assert res2["verdict"] == "MATCH_EXCEPT_1_DISCLOSED_BUCKETS"
    assert res2["mismatch_counts"]["close"] == 1
    assert res2["n_buckets_with_any_mismatch"] == 1


def test_gitignore_keeps_raw_zips_out_of_git():
    gi = (LANE_DIR / ".gitignore").read_text()
    assert "data_staging/" in gi
