"""V12 P1 A3 tests -- data contract, staging manifests, fail-closed load
validation.

All fixtures are TINY SYNTHETIC artifacts built in ``tmp_path``; the real
local data stores are never touched by these tests.
"""

from __future__ import annotations

import json
import os

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from research.v12.data_contract import (
    BAR_INTERVAL_NS,
    DECLARED_REQUIREMENTS,
    REQUIRED_SYMBOLS,
    S0R_WINDOW_END_ISO,
    S0R_WINDOW_START_ISO,
    V11_SCORED_WINDOW_END_ISO,
    V11_SCORED_WINDOW_START_ISO,
    bar_gaps_global,
    build_file_manifest,
    ceil_to_monday_00z_ns,
    canonical_json_bytes,
    inventory_funding,
    load_funding_times_ns,
    ns_to_iso_utc,
    parse_iso_utc_ns,
    sha256_file,
    verify_against_manifest,
    warmup_first_served_stamp_ns,
    windows_overlap,
)
from research.v12.load_validation import (
    DataLoadError,
    validate_completed_bars,
    validate_funding_applicability,
    validate_funding_span_coverage,
    validate_manifest_hash,
    validate_no_partial_tail,
    validate_window_bounds,
    validate_window_non_overlap,
)

DAY_NS = 86_400_000_000_000
# A known Monday 00:00:00Z: 2024-08-19T00:00:00Z.
MONDAY_NS = parse_iso_utc_ns("2024-08-19T00:00:00Z")


# ---------------------------------------------------------------------------
# Helpers to build synthetic 15-minute bar-close series and parquets.
# ---------------------------------------------------------------------------


def make_close_series(
    start_ns: int, n_slots: int, interval_ns: int = BAR_INTERVAL_NS
) -> list[int]:
    return [start_ns + (k + 1) * interval_ns for k in range(n_slots)]


def write_bar_parquet(path: str, close_ns: list[int]) -> None:
    table = pa.table(
        {
            "ts_event": pa.array(close_ns, type=pa.uint64()),
            "close": pa.array([1.0] * len(close_ns), type=pa.float64()),
        }
    )
    os.makedirs(os.path.dirname(path), exist_ok=True)
    pq.write_table(table, path)


def write_funding_json(
    path: str, times_ms: list[int], *, rate: str = "0.0001"
) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {
        "schema_version": 1,
        "symbol": "TESTUSDT",
        "rows": [
            {"fundingTime": int(ms), "fundingRate": rate, "markPrice": "1.0"}
            for ms in times_ms
        ],
    }
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh)


# ---------------------------------------------------------------------------
# Frozen windows and declared symbol set.
# ---------------------------------------------------------------------------


class TestFrozenContract:
    def test_required_symbol_set_is_the_declared_twenty(self) -> None:
        assert len(REQUIRED_SYMBOLS) == 20
        assert len(set(REQUIRED_SYMBOLS)) == 20
        assert "BTCUSDT" in REQUIRED_SYMBOLS

    def test_s0r_window_declared_value(self) -> None:
        assert S0R_WINDOW_START_ISO == "2024-08-22T00:00:00Z"
        assert S0R_WINDOW_END_ISO == "2025-08-21T00:00:00Z"
        assert V11_SCORED_WINDOW_START_ISO == "2025-08-22T00:00:00Z"
        assert V11_SCORED_WINDOW_END_ISO == "2026-08-21T00:00:00Z"

    def test_s0r_window_does_not_overlap_v11_scored_window(self) -> None:
        s0r_s = parse_iso_utc_ns(S0R_WINDOW_START_ISO)
        s0r_e = parse_iso_utc_ns(S0R_WINDOW_END_ISO)
        v11_s = parse_iso_utc_ns(V11_SCORED_WINDOW_START_ISO)
        v11_e = parse_iso_utc_ns(V11_SCORED_WINDOW_END_ISO)
        assert not windows_overlap(s0r_s, s0r_e, v11_s, v11_e)
        # S0R ends a full day BEFORE the V11 scored window opens.
        assert s0r_e < v11_s
        assert v11_s - s0r_e == 1 * DAY_NS
        validate_window_non_overlap(s0r_s, s0r_e, v11_s, v11_e)

    def test_windows_overlap_positive_case(self) -> None:
        s = parse_iso_utc_ns("2025-08-21T00:00:00Z")
        e = parse_iso_utc_ns("2025-08-23T00:00:00Z")
        v11_s = parse_iso_utc_ns(V11_SCORED_WINDOW_START_ISO)
        v11_e = parse_iso_utc_ns(V11_SCORED_WINDOW_END_ISO)
        assert windows_overlap(s, e, v11_s, v11_e)
        with pytest.raises(DataLoadError):
            validate_window_non_overlap(s, e, v11_s, v11_e)

    def test_declared_requirements_precede_coverage(self) -> None:
        # The coverage requirements must be declared in the contract before
        # any coverage number exists: bar cadence, warmup horizons, funding
        # PIT rule, instrument metadata rule.
        req = DECLARED_REQUIREMENTS["bars"]
        assert req["interval_ns"] == BAR_INTERVAL_NS
        assert req["warmup_days_required"]["binding_max"] == 90
        assert "gaps" in DECLARED_REQUIREMENTS["bars"]["window_rule"]
        assert "pit_rule" in DECLARED_REQUIREMENTS["funding"]
        assert "tick size" in DECLARED_REQUIREMENTS["instrument_metadata"]["rule"]


# ---------------------------------------------------------------------------
# Time helpers.
# ---------------------------------------------------------------------------


class TestTimeHelpers:
    def test_parse_and_format_roundtrip(self) -> None:
        ns = parse_iso_utc_ns("2024-08-22T00:00:00Z")
        assert ns_to_iso_utc(ns) == "2024-08-22T00:00:00Z"

    def test_monday_ceil(self) -> None:
        # 2024-08-22 is a Thursday; first Monday 00Z at-or-after is 08-26.
        thursday = parse_iso_utc_ns("2024-08-22T00:00:00Z")
        assert ns_to_iso_utc(ceil_to_monday_00z_ns(thursday + 1)) == (
            "2024-08-26T00:00:00Z"
        )
        monday = parse_iso_utc_ns("2024-08-26T00:00:00Z")
        assert ceil_to_monday_00z_ns(monday) == monday


# ---------------------------------------------------------------------------
# Completed-bar validation (fail-closed).
# ---------------------------------------------------------------------------


class TestValidateCompletedBars:
    def test_full_window_passes(self) -> None:
        start = MONDAY_NS
        end = start + 4 * DAY_NS
        closes = make_close_series(start, 4 * 96)
        validate_completed_bars(closes, start, end)

    def test_internal_gap_fails(self) -> None:
        start = MONDAY_NS
        end = start + 4 * DAY_NS
        closes = make_close_series(start, 4 * 96)
        del closes[100]  # one missing 15m slot
        with pytest.raises(DataLoadError, match="missing completed 15m slot"):
            validate_completed_bars(closes, start, end)

    def test_partial_tail_fails(self) -> None:
        start = MONDAY_NS
        end = start + 4 * DAY_NS
        closes = make_close_series(start, 4 * 96)
        # A bar closing beyond the frozen end is a partial tail: the strict
        # (default) load rejects the whole slice.
        bad = closes + [end + BAR_INTERVAL_NS]
        with pytest.raises(DataLoadError, match="partial tail"):
            validate_completed_bars(bad, start, end)
        # an explicitly late-allowed series passes coverage
        validate_completed_bars(bad, start, end, allow_late_bars=True)
        # an off-grid close inside the window breaks the final slot
        offgrid = closes[:-1] + [end - BAR_INTERVAL_NS // 2]
        with pytest.raises(DataLoadError):
            validate_completed_bars(offgrid, start, end)

    def test_truncated_head_fails(self) -> None:
        start = MONDAY_NS
        end = start + 4 * DAY_NS
        closes = make_close_series(start, 4 * 96)[10:]
        with pytest.raises(DataLoadError):
            validate_completed_bars(closes, start, end)

    def test_window_bounds_fail_closed(self) -> None:
        with pytest.raises(DataLoadError):
            validate_window_bounds(
                parse_iso_utc_ns("2025-08-22T00:00:00Z"),
                parse_iso_utc_ns("2025-08-22T00:00:00Z"),
            )

    def test_no_partial_tail_vs_availability(self) -> None:
        closes = make_close_series(MONDAY_NS, 96)
        validate_no_partial_tail(
            closes, data_available_until_ns=closes[-1]
        )
        with pytest.raises(DataLoadError):
            validate_no_partial_tail(
                closes, data_available_until_ns=closes[-1] - BAR_INTERVAL_NS
            )


# ---------------------------------------------------------------------------
# Funding PIT validation.
# ---------------------------------------------------------------------------


class TestFundingPit:
    def test_settlement_inside_span_passes(self) -> None:
        opened = MONDAY_NS
        closed = opened + 2 * DAY_NS
        validate_funding_applicability(opened + 8 * 3600 * 10**9, opened, closed)

    def test_settlement_before_span_fails(self) -> None:
        opened = MONDAY_NS
        closed = opened + 2 * DAY_NS
        with pytest.raises(DataLoadError, match="PIT violation"):
            validate_funding_applicability(opened - 1, opened, closed)

    def test_settlement_after_span_fails(self) -> None:
        opened = MONDAY_NS
        closed = opened + 2 * DAY_NS
        with pytest.raises(DataLoadError, match="PIT violation"):
            validate_funding_applicability(closed + 1, opened, closed)

    def test_funding_hole_inside_span_fails(self) -> None:
        opened = MONDAY_NS
        closed = opened + 3 * DAY_NS
        eight_h = 8 * 3600 * 10**9
        # settlements exist at open and at close but nothing in between
        with pytest.raises(DataLoadError, match="funding hole"):
            validate_funding_span_coverage(
                [opened + eight_h, closed], opened, closed
            )
        # a dense settlement grid passes
        grid = [opened + k * eight_h for k in range(0, 10)]
        validate_funding_span_coverage(grid, opened, closed)


# ---------------------------------------------------------------------------
# Manifest generation, determinism and verification (equal-twin staging).
# ---------------------------------------------------------------------------


class TestStagingManifest:
    def _make_tree(self, root: str) -> None:
        write_bar_parquet(os.path.join(root, "a", "bars.parquet"), [1, 2, 3])
        write_funding_json(
            os.path.join(root, "b", "funding.json"), [1000, 2000]
        )

    def test_manifest_build_and_self_hash(self, tmp_path) -> None:
        root = str(tmp_path / "data")
        self._make_tree(root)
        manifest = build_file_manifest([("snap", root)])
        files = manifest["files"]
        assert "snap/a/bars.parquet" in files
        assert "snap/b/funding.json" in files
        bars_hash = files["snap/a/bars.parquet"]["sha256"]
        assert bars_hash == sha256_file(os.path.join(root, "a", "bars.parquet"))
        # manifest_sha256 hashes only the canonical files section
        import hashlib

        assert manifest["manifest_sha256"] == hashlib.sha256(
            canonical_json_bytes(files)
        ).hexdigest()

    def test_manifest_deterministic_and_order_independent(self, tmp_path) -> None:
        root = str(tmp_path / "data")
        self._make_tree(root)
        m1 = build_file_manifest([("snap", root)])
        m2 = build_file_manifest([("snap", root)])
        assert m1["files"] == m2["files"]
        assert m1["manifest_sha256"] == m2["manifest_sha256"]

    def test_verify_equal_twin_passes_and_detects_mutation(
        self, tmp_path
    ) -> None:
        root = str(tmp_path / "data")
        self._make_tree(root)
        manifest = build_file_manifest([("snap", root)])
        # equal twin: identical bytes elsewhere
        twin = str(tmp_path / "twin")
        self._make_tree(twin)
        assert verify_against_manifest([("snap", twin)], manifest) == []
        # mutation is detected
        write_bar_parquet(
            os.path.join(twin, "a", "bars.parquet"), [1, 2, 3, 4]
        )
        problems = verify_against_manifest([("snap", twin)], manifest)
        assert problems == ["sha_mismatch:snap/a/bars.parquet"]

    def test_validate_manifest_hash(self, tmp_path) -> None:
        f = tmp_path / "x.json"
        f.write_text("{}")
        expected = sha256_file(str(f))
        assert validate_manifest_hash(str(f), expected, label="x") == expected
        with pytest.raises(DataLoadError, match="mismatch"):
            validate_manifest_hash(str(f), "0" * 64, label="x")
        with pytest.raises(DataLoadError, match="missing"):
            validate_manifest_hash(str(tmp_path / "nope"), expected, label="y")


# ---------------------------------------------------------------------------
# Inventory helpers on synthetic data.
# ---------------------------------------------------------------------------


class TestInventoryHelpers:
    def test_load_funding_times_and_inventory(self, tmp_path) -> None:
        root = str(tmp_path / "fund")
        eight_h_ms = 8 * 3600 * 1000
        base_ms = MONDAY_NS // 10**6
        times = [base_ms + k * eight_h_ms for k in range(7)]
        write_funding_json(os.path.join(root, "TESTUSDT", "funding.json"), times)
        assert len(load_funding_times_ns(
            os.path.join(root, "TESTUSDT", "funding.json")
        )) == 7
        inv = inventory_funding(
            [("bundle", root)],
            "TESTUSDT",
            window_start_ns=MONDAY_NS,
            window_end_ns=MONDAY_NS + 2 * DAY_NS,
        )
        assert inv["present"] is True
        assert inv["window"]["missing_slots_at_cadence"] == 0
        # window (start, end] at 8h cadence holds exactly 6 settlement slots
        # (the settlement AT the window start belongs to the previous span)
        assert inv["window"]["settlements_in_window"] == 6

    def test_funding_gap_detected(self, tmp_path) -> None:
        root = str(tmp_path / "fund")
        eight_h_ms = 8 * 3600 * 1000
        base_ms = MONDAY_NS // 10**6
        times = [base_ms + k * eight_h_ms for k in range(7)]
        del times[3]  # one missing settlement inside the window
        write_funding_json(os.path.join(root, "TESTUSDT", "funding.json"), times)
        inv = inventory_funding(
            [("bundle", root)],
            "TESTUSDT",
            window_start_ns=MONDAY_NS,
            window_end_ns=MONDAY_NS + 2 * DAY_NS,
        )
        assert inv["present"] is True
        # the missing settlement shows up as a 16h coverage hole vs the
        # symbol's finest (8h) cadence
        assert inv["window"]["coverage_hole_count"] == 1
        assert inv["window"]["coverage_holes"][0]["hours"] == 16.0

    def test_funding_hour_jitter_is_snapped(self, tmp_path) -> None:
        root = str(tmp_path / "fund")
        eight_h_ms = 8 * 3600 * 1000
        base_ms = MONDAY_NS // 10**6
        # +7ms and -3ms jitter around the exact boundaries
        times = [base_ms + k * eight_h_ms + (7 if k % 2 else -3) for k in range(7)]
        write_funding_json(os.path.join(root, "TESTUSDT", "funding.json"), times)
        inv = inventory_funding(
            [("bundle", root)],
            "TESTUSDT",
            window_start_ns=MONDAY_NS,
            window_end_ns=MONDAY_NS + 2 * DAY_NS,
        )
        assert inv["window"]["coverage_hole_count"] == 0
        assert inv["bundles"]["bundle"]["snap"]["jitter_repairs"] >= 5
        # the boundary settlement at window end is not lost to jitter
        assert inv["window"]["last_settlement_iso"] == ns_to_iso_utc(
            MONDAY_NS + 2 * DAY_NS
        )

    def test_bar_global_gap_census(self) -> None:
        closes = make_close_series(MONDAY_NS, 20)
        gapped = closes[:10] + closes[11:]  # exactly one slot missing
        report = bar_gaps_global(gapped, BAR_INTERVAL_NS)
        assert report["gap_count"] == 1
        assert report["missing_slots_total"] == 1
        assert bar_gaps_global(closes, BAR_INTERVAL_NS)["gap_count"] == 0

    def test_warmup_first_served_stamp(self) -> None:
        # history starts Monday 00Z + 15m and runs 60 days contiguously
        start = MONDAY_NS
        closes = make_close_series(start, 60 * 96)
        served = warmup_first_served_stamp_ns(closes, 28)
        # formation (T-28d, T] needs completed bars strictly after start;
        # the first Monday whose trailing 28 days fit is start+28d (a Monday)
        assert ns_to_iso_utc(served) == ns_to_iso_utc(start + 28 * DAY_NS)
        # insufficient history -> None
        assert warmup_first_served_stamp_ns(closes[: 20 * 96], 28) is None

    def test_warmup_gap_resets_history(self) -> None:
        # 130 days of history with one missing slot at day 40: a 56-day
        # horizon can only be served by bars after the gap.
        start = MONDAY_NS
        closes = make_close_series(start, 130 * 96)
        clean = warmup_first_served_stamp_ns(closes, 56)
        assert ns_to_iso_utc(clean) == ns_to_iso_utc(start + 56 * DAY_NS)
        broken = closes[: 40 * 96 - 1] + closes[40 * 96 :]
        served = warmup_first_served_stamp_ns(broken, 56)
        # contiguous history resumes at day 40 + 15m; earliest origin is
        # resume + 56d - 15m = start + 96d (Saturday) -> next Monday.
        assert served is not None
        assert served > clean
        assert ns_to_iso_utc(served) == ns_to_iso_utc(
            ceil_to_monday_00z_ns(start + 96 * DAY_NS)
        )
        assert ns_to_iso_utc(served).endswith("T00:00:00Z")

    def test_synthetic_parquet_bar_inventory_roundtrip(self, tmp_path) -> None:
        from research.v12.data_contract import inventory_bars

        root = str(tmp_path / "bars")
        start = MONDAY_NS
        closes = make_close_series(start, 10 * 96)
        write_bar_parquet(
            os.path.join(root, "TESTUSDT-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL", "x.parquet"),
            closes,
        )
        ws = start + DAY_NS
        we = start + 3 * DAY_NS
        inv = inventory_bars(root, "TESTUSDT", window_start_ns=ws, window_end_ns=we)
        assert inv["present"] is True
        assert inv["rows"] == 10 * 96
        assert inv["window"]["missing_slots"] == 0
        assert inv["window"]["present_slots"] == 2 * 96
