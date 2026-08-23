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
    compute_continuous_clean_intersection,
    funding_completeness_for_window,
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


# --------------------------------------------------------------------------- #
# Sprint V2: clean-window rule + funding completeness
# --------------------------------------------------------------------------- #
DS = pd.Timestamp("2025-08-21T00:00:00Z")
DE = pd.Timestamp("2026-08-21T00:00:00Z")
ETH_G1_AFTER = "2025-08-20T23:59:59.999000064+00:00"
ETH_G1_BEFORE = "2025-08-21T14:29:59.999000064+00:00"


def _sym_entry(gaps=None, status="COMPLETED"):
    return {
        "status": status,
        "bars": {"gap_details": gaps or []},
    }


def _coverage(symbols: dict) -> dict:
    return {"symbols": symbols}


def _eth_like_gaps(with_post_window_gaps=True):
    gaps = [
        {
            "after_ts_utc": ETH_G1_AFTER,
            "before_ts_utc": ETH_G1_BEFORE,
            "gap_minutes": 870.0,
        }
    ]
    if with_post_window_gaps:
        gaps += [
            {
                "after_ts_utc": "2026-08-21T13:59:59.999000064+00:00",
                "before_ts_utc": "2026-08-21T15:14:59.999000064+00:00",
                "gap_minutes": 75.0,
            },
            {
                "after_ts_utc": "2026-08-23T05:44:59.999000064+00:00",
                "before_ts_utc": "2026-08-23T06:29:59.999000064+00:00",
                "gap_minutes": 45.0,
            },
        ]
    return gaps


def test_clean_window_trims_boundary_gap_and_ignores_post_window_gaps():
    symbols = {name: _sym_entry() for name in S0_SYMBOLS[:-1]}
    symbols["ETHUSDT"] = _sym_entry(_eth_like_gaps(), status="DATA_INCOMPLETE")
    result = compute_continuous_clean_intersection(_coverage(symbols), DS, DE)

    eth = result["per_symbol"]["ETHUSDT"]
    assert eth["excluded"] is False
    assert eth["trimmed_start"] is True
    assert eth["scored_start_utc"] == ETH_G1_BEFORE  # ~14:30Z trim
    assert eth["scored_end_utc"] == DE.isoformat()

    for name in S0_SYMBOLS[:-1]:
        entry = result["per_symbol"][name]
        assert entry["scored_start_utc"] == DS.isoformat()
        assert entry["scored_end_utc"] == DE.isoformat()

    assert result["universe_scored"] == list(S0_SYMBOLS)
    inter = result["intersection"]
    assert inter["start_utc"] == ETH_G1_BEFORE
    assert inter["end_utc"] == DE.isoformat()
    assert inter["covers_declared_window"] is False


def test_clean_window_excludes_symbol_with_midwindow_gap():
    mid_gap = {
        "after_ts_utc": "2026-03-01T10:14:59.999000064+00:00",
        "before_ts_utc": "2026-03-01T18:14:59.999000064+00:00",
        "gap_minutes": 480.0,
    }
    symbols = {name: _sym_entry() for name in ("SOLUSDT", "ETHUSDT")}
    symbols["BNBUSDT"] = _sym_entry([mid_gap], status="DATA_INCOMPLETE")
    result = compute_continuous_clean_intersection(_coverage(symbols), DS, DE)

    bnb = result["per_symbol"]["BNBUSDT"]
    assert bnb["excluded"] is True
    assert bnb["exclusion_reason"] == "unexplained_gap"
    assert bnb["scored_start_utc"] is None and bnb["scored_end_utc"] is None
    assert result["universe_scored"] == ["SOLUSDT", "ETHUSDT"]
    assert result["intersection"]["symbol_count"] == 2


def test_clean_window_repaired_gap_class_passes_through():
    mid_gap = {
        "after_ts_utc": "2026-03-01T10:14:59.999000064+00:00",
        "before_ts_utc": "2026-03-01T18:14:59.999000064+00:00",
        "gap_minutes": 480.0,
        "classification": "exchange_outage_repaired",
        "repair_segment_sha256": "deadbeef",
    }
    symbols = {name: _sym_entry() for name in ("SOLUSDT", "BNBUSDT")}
    symbols["BNBUSDT"]["bars"]["gap_details"] = [mid_gap]
    result = compute_continuous_clean_intersection(_coverage(symbols), DS, DE)

    bnb = result["per_symbol"]["BNBUSDT"]
    assert bnb["excluded"] is False
    assert bnb["scored_start_utc"] == DS.isoformat()
    assert result["universe_scored"] == ["SOLUSDT", "BNBUSDT"]
    assert result["intersection"]["covers_declared_window"] is True

    # Unrepaired exchange_outage is treated as unexplained per the rule.
    unrepaired = dict(mid_gap, classification="exchange_outage")
    symbols["BNBUSDT"]["bars"]["gap_details"] = [unrepaired]
    result2 = compute_continuous_clean_intersection(_coverage(symbols), DS, DE)
    assert result2["per_symbol"]["BNBUSDT"]["excluded"] is True


def test_clean_window_exclude_only_rule_and_validation():
    symbols = {
        "A": _sym_entry(_eth_like_gaps()),
        "B": _sym_entry(),
    }
    strict = compute_continuous_clean_intersection(
        _coverage(symbols), DS, DE, rule="exclude_only"
    )
    assert strict["per_symbol"]["A"]["excluded"] is True
    assert strict["universe_scored"] == ["B"]

    import pytest

    with pytest.raises(ValueError):
        compute_continuous_clean_intersection(_coverage(symbols), DS, DE, rule="nonsense")


def test_funding_completeness_for_window(tmp_path):
    start = pd.Timestamp("2025-08-21T00:00:00Z")
    end = pd.Timestamp("2025-09-20T00:00:00Z")  # 30 days -> 90 settlements @8h (+1)
    day_ms = 86_400_000
    anchor = int(pd.Timestamp("2025-08-20T00:00:00Z").value // 1e6)

    def write_bundle(symbol, times):
        d = tmp_path / symbol
        d.mkdir(parents=True)
        (d / "funding.json").write_text(json.dumps({
            "requested_start_ms": anchor,
            "requested_end_ms": anchor + 400 * day_ms,
            "rows": [{"fundingTime": t, "fundingRate": "0.0001"} for t in times],
        }))

    full = [anchor + i * 8 * 3_600_000 for i in range(120)]
    write_bundle("FULLUSDT", full)
    stats = funding_completeness_for_window(tmp_path, "FULLUSDT", start, end)
    assert stats["complete"] is True
    assert stats["missing_settlements_estimate"] == 0
    assert stats["observed_settlements"] == 91  # closed-interval grid points

    # contiguous outage: remove 30 consecutive settlements inside the window
    # (realistic downloader/exchange gap shape; a periodic-drop pattern would
    # be indistinguishable from a genuine slower settlement cadence)
    block = {anchor + i * 8 * 3_600_000 for i in range(30, 60)}
    holed = [t for t in full if t not in block]
    write_bundle("HOLEUSDT", holed)
    stats_hole = funding_completeness_for_window(tmp_path, "HOLEUSDT", start, end)
    assert stats_hole["complete"] is False
    assert stats_hole["missing_settlements_estimate"] == 30
    assert stats_hole["observed_settlements"] == 61

    missing_bundle = funding_completeness_for_window(tmp_path, "NOPEUSDT", start, end)
    assert missing_bundle["complete"] is False
    assert missing_bundle["bundle_present"] is False
    assert missing_bundle["missing_settlements_estimate"] == -1
