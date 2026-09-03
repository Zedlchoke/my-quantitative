"""Integration with the REAL V2 staged snapshot (skipped when it is absent).

These tests revalidate the existing zero-cost snapshot in place — the V2
worktree staging directory referenced by absolute path — WITHOUT any network
fetch and WITHOUT copying raw payloads into this repository.  All reads run
through the sealed S0-only reader, so no S1 observation can surface; the
only post-S0 values read are the two pinned split-provenance closes per
split symbol.  When the snapshot or the V2 control artifacts are missing the
tests SKIP with an explicit UNAVAILABLE marker (never a silent pass).
"""

from __future__ import annotations

import json
import os
from datetime import date

import pytest

from research.assets.stocks.calendar import USEquityRegularCalendar
from research.stocks_free_v3.authority import (
    COHORT_SYMBOLS,
    SNAPSHOT_STAGING_PATH,
    V2_CONTROL_PATH,
    revalidate_license_evidence,
    verify_snapshot_pins,
)
from research.stocks_free_v3.cohort import verify_real_cohort
from research.stocks_free_v3.isolation import (
    S0WindowPolicy,
    S1Seal,
    S1SealError,
    SealedSnapshotReader,
)

STAGING = os.environ.get("V2_SNAPSHOT_STAGING", SNAPSHOT_STAGING_PATH)
CONTROL = os.environ.get("V2_CONTROL_DIR", V2_CONTROL_PATH)

pytestmark = pytest.mark.skipif(
    not os.path.isdir(STAGING),
    reason=f"UNAVAILABLE: V2 staging snapshot not present at {STAGING}",
)


@pytest.fixture(scope="module")
def reader() -> SealedSnapshotReader:
    return SealedSnapshotReader(
        STAGING, seal=S1Seal(date(2025, 8, 1), date(2026, 7, 31)), policy=S0WindowPolicy()
    )


def test_all_39_snapshot_pins_verify() -> None:
    report = verify_snapshot_pins(STAGING)
    assert report.verdict == "PASS", (
        f"pins mismatched={report.mismatched} unavailable={report.unavailable}"
    )
    assert len(report.verified) == 39


def test_license_evidence_revalidates() -> None:
    report = revalidate_license_evidence(CONTROL, staging_root=STAGING)
    if not (os.path.isfile(os.path.join(CONTROL, "da1_authority.json"))):
        pytest.skip(f"UNAVAILABLE: control artifacts absent at {CONTROL}")
    assert report.verdict == "PASS", [
        (c.name, c.verdict, c.detail) for c in report.checks if c.verdict != "PASS"
    ]


def test_cohort_verification_passes(reader: SealedSnapshotReader) -> None:
    distributions = json.load(open(os.path.join(STAGING, "distributions.json"), encoding="utf-8"))
    split_factors = json.load(
        open(os.path.join(STAGING, "split_factors.json"), encoding="utf-8")
    )
    report = verify_real_cohort(
        reader, distributions, split_factors, USEquityRegularCalendar()
    )
    assert report.verdict == "PASS", [
        (c.name, c.detail) for c in report.checks if c.verdict != "PASS"
    ]
    assert set(report.symbol_reports) == set(COHORT_SYMBOLS)


def test_s0_reads_allowed_and_s1_truncated(reader: SealedSnapshotReader) -> None:
    closes = reader.load_symbol_closes(
        "SPY_none_p1.json", start=date(2018, 4, 4), end=date(2025, 7, 31)
    )
    assert min(closes) == "2018-04-04"
    assert max(closes) == "2025-07-31"
    # the raw file carries post-S0 rows; the sealed reader must not return any
    assert not any(day >= "2025-08-01" for day in closes)
    with pytest.raises(S1SealError):
        reader.load_symbol_closes(
            "SPY_none_p1.json", start=date(2018, 4, 4), end=date(2025, 8, 1)
        )


def test_split_provenance_closes_match_pinned_ratios(reader: SealedSnapshotReader) -> None:
    from research.stocks_free_v3.cohort import PINNED_CLOSE_RATIOS, RATIO_TOLERANCE

    for symbol in PINNED_CLOSE_RATIOS:
        closes = reader.read_provenance_closes(f"{symbol}_none_p1.json")
        measured = closes["2025-12-05"] / closes["2025-12-04"]
        assert abs(measured - PINNED_CLOSE_RATIOS[symbol]) <= RATIO_TOLERANCE
