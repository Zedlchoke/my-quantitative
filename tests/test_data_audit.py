"""Tests for the data coverage audit (owner: A2)."""

from __future__ import annotations

import json

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from contracts.protocol import CellStatus
from research.data_audit import (
    S0_SYMBOLS,
    bar_stats,
    build_coverage,
    classify_symbol,
    funding_stats,
    instrument_metadata_present,
    load_universe_symbols,
)

STEP_NS = 15 * 60 * 1_000_000_000
BASE = int(pd.Timestamp("2025-01-01T00:00:00Z").value)


def _clean_series(count: int) -> list[int]:
    # Close stamps sit ~61ms before their nominal grid point (Binance style).
    return [BASE + (i + 1) * STEP_NS - 61_000_064 for i in range(count)]


def test_bar_stats_counts_duplicates_and_gaps():
    stamps = _clean_series(10)
    stats = bar_stats(stamps)
    assert stats["bar_count"] == 10
    assert stats["duplicate_timestamps"] == 0
    assert stats["gaps_over_interval"] == 0

    duped = stamps + [stamps[3]]
    assert bar_stats(duped)["duplicate_timestamps"] == 1

    gapped = stamps[:5] + [stamps[4] + 4 * STEP_NS] + stamps[6:]
    gapped_stats = bar_stats(gapped)
    assert gapped_stats["gaps_over_interval"] == 1
    assert gapped_stats["gap_details"][0]["gap_minutes"] == 60.0

    assert bar_stats([])["bar_count"] == 0


def test_classify_symbol_reason_codes_and_eligibility():
    declared_start = pd.Timestamp("2025-08-21T00:00:00Z")
    declared_end = pd.Timestamp("2026-08-21T00:00:00Z")
    good_stats = {
        "bar_count": 35040,
        "first_ts_utc": pd.Timestamp(BASE, unit="ns", tz="UTC").isoformat(),
        "last_ts_utc": declared_end.isoformat(),
        "duplicate_timestamps": 0,
        "gaps_over_interval": 0,
    }
    good_funding = {"bundle_present": True, "covers_declared_window": True}

    status, reasons = classify_symbol(good_stats, True, good_funding, declared_start, declared_end)
    assert status == CellStatus.COMPLETED and reasons == []

    dup = dict(good_stats, duplicate_timestamps=2)
    assert CellStatus.DATA_INCOMPLETE in [
        classify_symbol(dup, True, good_funding, declared_start, declared_end)[0]
    ]
    assert "duplicate_bars" in classify_symbol(dup, True, good_funding, declared_start, declared_end)[1]

    gap = dict(good_stats, gaps_over_interval=1)
    assert "unexplained_gap" in classify_symbol(gap, True, good_funding, declared_start, declared_end)[1]

    no_inst = classify_symbol(good_stats, False, good_funding, declared_start, declared_end)
    assert "missing_instrument_metadata" in no_inst[1]

    bad_funding = classify_symbol(
        good_stats, True, {"bundle_present": False}, declared_start, declared_end
    )
    assert "funding_coverage_insufficient" in bad_funding[1]

    late_start = dict(good_stats, first_ts_utc=(declared_start + pd.Timedelta(days=1)).isoformat())
    narrow = classify_symbol(late_start, True, good_funding, declared_start, declared_end)
    assert "coverage_below_declared" in narrow[1]


def test_funding_stats_missing_bundle_and_coverage(tmp_path):
    declared_start = pd.Timestamp("2025-08-21T00:00:00Z")
    declared_end = pd.Timestamp("2026-08-21T00:00:00Z")
    assert funding_stats(tmp_path, "NOPE", declared_start, declared_end)["bundle_present"] is False

    bundle_dir = tmp_path / "AAAUSDT"
    bundle_dir.mkdir()
    payload = {
        "requested_start_ms": int(declared_start.value // 1e6),
        "requested_end_ms": int(declared_end.value // 1e6),
        "rows": [
            {"fundingTime": int((declared_start - pd.Timedelta(hours=8)).value // 1e6),
             "fundingRate": "0.0001", "markPrice": "100"},
            {"fundingTime": int((declared_end + pd.Timedelta(hours=8)).value // 1e6),
             "fundingRate": "-0.0001", "markPrice": "100"},
        ],
    }
    (bundle_dir / "funding.json").write_text(json.dumps(payload))
    stats = funding_stats(tmp_path, "AAAUSDT", declared_start, declared_end)
    assert stats["bundle_present"] is True
    assert stats["covers_declared_window"] is True
    assert stats["row_count"] == 2
    assert stats["coverage_ratio"] > 1.0


def test_instrument_metadata_present(tmp_path):
    inst_dir = tmp_path / "data" / "crypto_perpetual" / "X-PERP.BINANCE"
    assert not instrument_metadata_present(tmp_path, "X-PERP.BINANCE")
    inst_dir.mkdir(parents=True)
    assert not instrument_metadata_present(tmp_path, "X-PERP.BINANCE")  # dir but no parquet
    pq.write_table(pa.table({"a": [1]}), inst_dir / "i.parquet")
    assert instrument_metadata_present(tmp_path, "X-PERP.BINANCE")


def _write_catalog(root, symbol, timestamps):
    bt_dir = root / "data" / "binance_bar" / f"{symbol}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    bt_dir.mkdir(parents=True)
    pq.write_table(
        pa.table({"ts_event": pa.array(timestamps, type=pa.int64())}),
        bt_dir / "bars.parquet",
    )
    inst_dir = root / "data" / "crypto_perpetual" / f"{symbol}-PERP.BINANCE"
    inst_dir.mkdir(parents=True, exist_ok=True)
    pq.write_table(pa.table({"a": [1]}), inst_dir / "i.parquet")


E2E_BASE = int(pd.Timestamp("2025-08-20T00:00:00Z").value)


def test_build_coverage_end_to_end_on_synthetic_catalog(tmp_path):
    catalog = tmp_path / "catalog_test"
    declared_start = pd.Timestamp("2025-08-21T00:00:00Z")
    declared_end = pd.Timestamp("2025-08-22T00:00:00Z")

    def series(count: int) -> list[int]:
        return [E2E_BASE + (i + 1) * STEP_NS - 61_000_064 for i in range(count)]

    ok = series(96 * 5)  # 2025-08-20 .. 2025-08-25 covers the window
    _write_catalog(catalog, "OKUSDT", ok)
    gapped = series(96 * 5)
    # Unexplained 2h outage inside the window: shift everything after bar 110.
    gapped = [ts + (8 * STEP_NS if i > 110 else 0) for i, ts in enumerate(gapped)]
    _write_catalog(catalog, "GAPUSDT", gapped)

    for name in ("OKUSDT", "GAPUSDT"):
        fund_dir = tmp_path / "funds" / name
        fund_dir.mkdir(parents=True)
        (fund_dir / "funding.json").write_text(json.dumps({
            "requested_start_ms": BASE // 1_000_000 - 86_400_000,
            "requested_end_ms": int(declared_end.value // 1e6) + 86_400_000,
            "rows": [
                {"fundingTime": BASE // 1_000_000, "fundingRate": "0.0001",
                 "markPrice": "10"},
                {"fundingTime": int(declared_end.value // 1e6),
                 "fundingRate": "0.0001", "markPrice": "10"},
            ],
        }))

    universe_cfg = tmp_path / "universe.yaml"
    universe_cfg.write_text(
        "market:\n  symbols:\n    - OKUSDT\n    - GAPUSDT\n"
    )
    assert load_universe_symbols(universe_cfg) == ["OKUSDT", "GAPUSDT"]

    coverage = build_coverage(
        universe_config=universe_cfg,
        catalog_path=catalog,
        funding_dir=tmp_path / "funds",
        declared_start=declared_start,
        declared_end=declared_end,
        symbols=["OKUSDT", "GAPUSDT"],
    )

    assert coverage["symbols"]["OKUSDT"]["status"] == CellStatus.COMPLETED.value
    gap_entry = coverage["symbols"]["GAPUSDT"]
    assert gap_entry["status"] == CellStatus.DATA_INCOMPLETE.value
    assert gap_entry["reason_codes"] == ["unexplained_gap"]

    intersections = coverage["intersections"]
    assert set(intersections["all_universe"]["symbols"]) == {"OKUSDT", "GAPUSDT"}
    assert (
        intersections["all_universe"]["start_utc"]
        == pd.Timestamp(ok[0], unit="ns", tz="UTC").isoformat()
    )
    assert coverage["summary"]["eligible_count"] == 1

    s0_names = [s for s in S0_SYMBOLS if s in {"OKUSDT", "GAPUSDT"}]
    assert intersections["s0_seven"]["symbols"] == []


def test_s0_set_matches_frozen_seven():
    assert S0_SYMBOLS == (
        "SOLUSDT", "BNBUSDT", "XRPUSDT", "DOGEUSDT", "LINKUSDT", "ADAUSDT", "ETHUSDT",
    )


def test_classify_requires_contract_known_reasons_only():
    from contracts.protocol import REASON_CODES

    declared_start = pd.Timestamp("2025-08-21T00:00:00Z")
    declared_end = pd.Timestamp("2026-08-21T00:00:00Z")
    bad = {
        "bar_count": 1,
        "first_ts_utc": "2026-01-01T00:00:00+00:00",
        "last_ts_utc": "2026-01-01T00:00:00+00:00",
        "duplicate_timestamps": 9,
        "gaps_over_interval": 9,
    }
    _, reasons = classify_symbol(
        bad, False, {"bundle_present": False}, declared_start, declared_end
    )
    for code in reasons:
        assert code in REASON_CODES
