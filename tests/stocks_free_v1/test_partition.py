"""Synthetic goldens for the S0/warmup/S1 partition + S1 sealing (A3).

Coverage dates are INPUTS of the rule (never fabricated): every test
freezes a synthetic coverage span and asserts the exact partition the
rule must produce, including force-flat fold boundaries, declared purge,
and SealedWindowError on any S1 path.
"""

from __future__ import annotations

import importlib.util
import sys
from datetime import date
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

_MODULE_PATH = REPO_ROOT / "research" / "stocks_free_v1" / "partition.py"
_SPEC = importlib.util.spec_from_file_location("z1_a3_partition", _MODULE_PATH)
partition = importlib.util.module_from_spec(_SPEC)
sys.modules["z1_a3_partition"] = partition
_SPEC.loader.exec_module(partition)

from research.assets.stocks.calendar import US_EQUITY_REGULAR_V1 as CAL

# Synthetic coverage: 2014-01-02 .. 2025-12-31 (S1 = calendar 2025).
COVERAGE_START = date(2014, 1, 2)
COVERAGE_END = date(2025, 12, 31)


@pytest.fixture(scope="module")
def frozen() -> partition.Partition:
    return partition.freeze_partition(
        coverage_start=COVERAGE_START,
        coverage_end=COVERAGE_END,
        calendar=CAL,
    )


# --- golden layout -----------------------------------------------------------------


def test_s1_is_the_last_twelve_complete_months(frozen) -> None:
    assert frozen.s1_start == date(2025, 1, 1)
    assert frozen.s1_end == date(2025, 12, 31)


def test_s1_on_mid_month_coverage_ends_at_previous_month_end() -> None:
    part = partition.freeze_partition(
        coverage_start=COVERAGE_START,
        coverage_end=date(2025, 11, 14),
        calendar=CAL,
    )
    # coverage stops mid-November 2025 -> November is NOT complete ->
    # S1 = 2024-11-01 .. 2025-10-31
    assert part.s1_start == date(2024, 11, 1)
    assert part.s1_end == date(2025, 10, 31)


def test_warmup_precedes_s0_and_carries_no_scored_trades(frozen) -> None:
    assert frozen.warmup_sessions == partition.DEFAULT_WARMUP_SESSIONS
    assert frozen.warmup_start == COVERAGE_START
    assert frozen.warmup_end < frozen.s0_start
    assert frozen.s0_start > frozen.warmup_start
    # exactly DEFAULT_WARMUP_SESSIONS sessions belong to the warmup
    sessions = [
        s.start_utc.astimezone(partition.ET_ZONE).date()
        for s in CAL.sessions_in_range(frozen.coverage_start, frozen.s0_start)
    ]
    # sessions up to (not including) s0_start == warmup size
    assert len([d for d in sessions if d < frozen.s0_start]) == frozen.warmup_sessions


def test_s0_ends_strictly_before_sealed_s1(frozen) -> None:
    assert frozen.s0_end < frozen.s1_start
    assert frozen.s0_start < frozen.s0_end


def test_s0_complete_years_measured_and_minimum_gate(frozen) -> None:
    # S0 spans 2014-04 .. 2024-12 -> complete years 2015..2024 = 10
    assert frozen.s0_complete_years == 10
    assert frozen.s0_minimum_years_met is True
    assert frozen.warnings == ()


def test_short_coverage_records_unmet_minimum_without_silence() -> None:
    part = partition.freeze_partition(
        coverage_start=date(2020, 1, 2),
        coverage_end=date(2024, 6, 15),
        calendar=CAL,
    )
    assert part.s0_minimum_years_met is False
    assert part.s0_complete_years < partition.S0_MIN_COMPLETE_YEARS
    assert part.warnings and "NOT met" in part.warnings[0]
    manifest = part.as_manifest()
    assert manifest["s0_minimum_years_met"] is False


def test_impossible_s1_raises_blocked_s1_isolation_code() -> None:
    with pytest.raises(partition.PartitionError, match="S1_CANNOT_BE_FORMED"):
        partition.freeze_partition(
            coverage_start=date(2024, 1, 2),
            coverage_end=date(2024, 12, 31),
            calendar=CAL,
        )


# --- folds, force-flat boundaries and declared purge --------------------------------


def test_three_chronological_contiguous_folds(frozen) -> None:
    assert len(frozen.folds) == 3
    fold1, fold2, fold3 = frozen.folds
    assert fold1.fold_id == "S0_FOLD_1"
    assert fold1.start == frozen.s0_start
    assert fold3.end == frozen.s0_end
    # chronological, contiguous, non-overlapping
    assert fold1.start < fold1.end < fold2.start < fold2.end < fold3.start < fold3.end


def test_fold_scored_region_is_purged_force_flat(frozen) -> None:
    for fold in frozen.folds:
        assert fold.purge_sessions == partition.DEFAULT_PURGE_SESSIONS
        assert fold.scored_end < fold.end
        # purge spans exactly DEFAULT_PURGE_SESSIONS sessions
        between = [
            s.start_utc.astimezone(partition.ET_ZONE).date()
            for s in CAL.sessions_in_range(fold.scored_end, fold.end)
        ]
        assert len(between) == fold.purge_sessions + 1  # inclusive both ends


def test_no_scored_position_crosses_into_s1(frozen) -> None:
    # the LAST fold's force-flat scored end is also strictly before S1
    last = frozen.folds[-1]
    assert last.scored_end < frozen.s1_start


def test_fold_smaller_than_purge_fails_closed() -> None:
    with pytest.raises(partition.PartitionError, match="FOLD_CANNOT_BE_FORMED"):
        partition.freeze_partition(
            coverage_start=date(2020, 1, 2),
            coverage_end=date(2024, 6, 15),
            calendar=CAL,
            purge_sessions=100_000,
        )


# --- digest + manifest ---------------------------------------------------------------


def test_partition_digest_stable_and_sensitive(frozen) -> None:
    again = partition.freeze_partition(
        coverage_start=COVERAGE_START,
        coverage_end=COVERAGE_END,
        calendar=CAL,
    )
    assert frozen.digest == again.digest
    moved = partition.freeze_partition(
        coverage_start=COVERAGE_START,
        coverage_end=date(2025, 11, 30),
        calendar=CAL,
    )
    assert frozen.digest != moved.digest
    manifest = frozen.as_manifest()
    assert manifest["partition_digest"] == frozen.digest
    assert manifest["s1_status"] == "SEALED_NO_RESEARCH_READ"
    assert manifest["warmup_may_contribute_scored_trades"] is False


# --- coverage outside the calendar horizon fails closed ------------------------------


def test_coverage_outside_calendar_table_rejected() -> None:
    with pytest.raises(partition.PartitionError, match="frozen calendar table"):
        partition.freeze_partition(
            coverage_start=date(2004, 1, 2),
            coverage_end=date(2025, 12, 31),
            calendar=CAL,
        )


# --- S1 filesystem sealing -----------------------------------------------------------


def test_sealed_path_filter_denies_s1_dated_paths(frozen) -> None:
    allow = partition.build_research_allowlist(frozen, data_root="/data/etf-staged")
    # S0-dated files are readable
    assert allow.is_readable("/data/etf-staged/spy/2024-06-03.parquet") is True
    # S1-dated files are SEALED
    for path in (
        "/data/etf-staged/spy/2025-03-14.parquet",
        "/data/etf-staged/spy/close_20250602.csv",
        "/data/etf-staged/S1/close_2025-12-31.csv",
    ):
        with pytest.raises(partition.SealedWindowError):
            allow.check(path)
        assert allow.is_readable(path) is False


def test_sealed_path_filter_denies_sealed_roots_and_outside_roots(frozen) -> None:
    allow = partition.SealedPathFilter(
        allowed_roots=("/data/etf-staged",),
        sealed_roots=("/data/etf-staged/sealed-s1",),
    )
    with pytest.raises(partition.SealedWindowError):
        allow.check("/data/etf-staged/sealed-s1/spy.parquet")
    with pytest.raises(partition.SealedWindowError, match="outside every allowed root"):
        allow.check("/etc/passwd")


def test_sealed_filter_read_only_and_open_enforcement(frozen, tmp_path) -> None:
    s0_file = tmp_path / "s0" / "2024-06-03.csv"
    s0_file.parent.mkdir()
    s0_file.write_text("open,close\n1.0,1.1\n")
    s1_file = tmp_path / "s1" / "2025-06-02.csv"
    s1_file.parent.mkdir()
    s1_file.write_text("open,close\n1.0,1.1\n")

    allow = partition.build_research_allowlist(frozen, data_root=str(tmp_path))
    # S0 opens fine (read mode)
    with allow.open(s0_file, "r") as handle:
        assert "open" in handle.readline()
    # S1 is unreadable through the filter
    with pytest.raises(partition.SealedWindowError):
        allow.open(s1_file, "r")
    # write modes are rejected for ANY path (research is read-only)
    with pytest.raises(partition.SealedWindowError, match="read-only"):
        allow.open(s0_file, "w")


def test_sealed_range_boundaries_are_inclusive(frozen) -> None:
    allow = partition.build_research_allowlist(frozen, data_root="/data/x")
    # exact S1 boundaries are sealed
    with pytest.raises(partition.SealedWindowError):
        allow.check(f"/data/x/day_{frozen.s1_start.isoformat()}.csv")
    with pytest.raises(partition.SealedWindowError):
        allow.check(f"/data/x/day_{frozen.s1_end.isoformat()}.csv")
    # one session before S1 stays readable
    assert allow.is_readable(f"/data/x/day_{frozen.s0_end.isoformat()}.csv") is True


def test_filter_requires_allowed_roots() -> None:
    with pytest.raises(ValueError):
        partition.SealedPathFilter(allowed_roots=())


def test_dates_outside_s1_in_name_are_readable(frozen) -> None:
    allow = partition.build_research_allowlist(frozen, data_root="/data/x")
    # date-like tokens OUTSIDE the S1 range do not seal the file
    assert allow.is_readable("/data/x/day_2016-02-15.csv") is True
    assert allow.is_readable("/data/x/not-a-date-20250.csv") is True
