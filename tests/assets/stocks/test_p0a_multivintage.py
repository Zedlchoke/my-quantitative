"""P0a multi-vintage PIT tests: hand-computed fixtures, no production data.

Covers the mutation and lag fixtures required by the V6 plan (section 9) and
handbook section 14.2 for the remediated fundamentals panel:

- one-event/one-bar availability lag;
- multi-vintage availability-lag mutation (no-lookahead): moving a filed date
  after a decision date MUST change the observed vintage;
- age-bounded observation semantics (stale vintage is dropped, never
  backfilled from a newer one);
- deterministic byte emission of the census/clock helper outputs;
- sanitizer round-trip on a small synthetic companyfacts sample.

No production outcomes, no store bytes: every fixture below is hand-computed.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timezone

import pytest

from research.assets.stocks.p0a_multivintage import (
    AGE_GRID_DAYS,
    COVERAGE_FLOORS,
    FilerFieldSeries,
    VintageStamp,
    coverage_timeline,
    date_to_ord,
    first_cross_date,
    lag_stats,
    parse_iso_utc,
    session_gate_utc,
    stamp_is_eod_utc,
)
from research.assets.stocks.sec_sanitize import sanitize_companyfacts


def stamp(iso_avail: str, iso_eff: str, value: float | None) -> VintageStamp:
    return VintageStamp(
        available_ord=date_to_ord(date.fromisoformat(iso_avail)),
        effective_date=date.fromisoformat(iso_eff),
        value=value,
    )


def series(*stamps: VintageStamp, entity: str = "CIK0000000001") -> FilerFieldSeries:
    bucket = FilerFieldSeries(entity_id=entity)
    for item in stamps:
        bucket.add(item)
    return bucket.finalize()


# --------------------------------------------------------------------------
# one-event / one-bar lag fixture
# --------------------------------------------------------------------------

class TestOneEventOneBarLag:
    def test_filed_stamp_unusable_on_its_own_day(self):
        # A fact filed 2024-05-10 (end of day) first influences a decision on
        # 2024-05-13 (next session); on 2024-05-10 it is still invisible.
        bucket = series(stamp("2024-05-10", "2024-03-31", 100.0))
        assert bucket.observation_at(date(2024, 5, 10)) is None
        assert bucket.observation_at(date(2024, 5, 11)) is not None
        assert bucket.observation_at(date(2024, 5, 13)).value == 100.0

    def test_gate_matches_canonical_session_gate(self):
        bucket = series(stamp("2024-05-10", "2024-03-31", 100.0))
        gate = session_gate_utc(date(2024, 5, 11))
        # availability 2024-05-10T23:59:59Z is strictly before the 05-11 gate
        assert parse_iso_utc("2024-05-10T23:59:59+00:00") < gate
        assert bucket.observation_at(date(2024, 5, 11)) is not None


# --------------------------------------------------------------------------
# multi-vintage availability-lag mutation (no-lookahead)
# --------------------------------------------------------------------------

class TestAvailabilityLagMutation:
    def make_two_vintages(self) -> FilerFieldSeries:
        # Q1 vintage filed 2024-05-10 (value 100), Q2 vintage filed
        # 2024-08-09 (value 200).  Decisions between the two filings must
        # observe 100; decisions after the second filing observe 200.
        return series(
            stamp("2024-05-10", "2024-03-31", 100.0),
            stamp("2024-08-09", "2024-06-30", 200.0),
        )

    def test_observed_vintage_follows_filing_clock(self):
        bucket = self.make_two_vintages()
        # end-of-day filed stamps are usable only from the NEXT session
        assert bucket.observation_at(date(2024, 5, 10)) is None
        assert bucket.observation_at(date(2024, 5, 11)).value == 100.0
        assert bucket.observation_at(date(2024, 7, 1)).value == 100.0
        assert bucket.observation_at(date(2024, 8, 9)).value == 100.0
        assert bucket.observation_at(date(2024, 8, 12)).value == 200.0
        assert bucket.observation_at(date(2024, 8, 12)).effective_date == date(2024, 6, 30)

    def test_delaying_filed_date_changes_observed_vintage(self):
        # MUTATION: move the second vintage's filed date after the decision
        # date; the decision must fall back to the older vintage.  If the
        # panel ever read the LATEST vintage regardless of availability this
        # would return 200 and the test would fail.
        mutated = series(
            stamp("2024-05-10", "2024-03-31", 100.0),
            stamp("2024-09-30", "2024-06-30", 200.0),  # filed 2024-09-30 now
        )
        before = mutated.observation_at(date(2024, 8, 12))
        assert before.value == 100.0
        assert before.effective_date == date(2024, 3, 31)
        # and after the new filed date the newer vintage becomes observable
        assert mutated.observation_at(date(2024, 10, 1)).value == 200.0

    def test_pre_filing_decision_observes_nothing(self):
        bucket = self.make_two_vintages()
        assert bucket.observation_at(date(2024, 1, 2)) is None
        assert bucket.observation_at(date(2023, 12, 31)) is None


# --------------------------------------------------------------------------
# age-bounded multi-vintage semantics
# --------------------------------------------------------------------------

class TestAgeBoundedObservation:
    def test_stale_vintage_dropped_not_backfilled(self):
        # Only vintage is 400 days old at the decision: age bound 200 must
        # drop it (return None); bound 400 keeps it; unbounded keeps it.
        bucket = series(stamp("2024-01-10", "2023-12-31", 100.0))
        decision = date(2024, 2, 14)  # 35 days after filing
        assert bucket.observation_at(decision, max_age_days=200) is not None
        old_decision = date(2025, 2, 10)  # ~397 days after filing
        assert bucket.observation_at(old_decision, max_age_days=200) is None
        assert bucket.observation_at(old_decision, max_age_days=400) is not None
        assert bucket.observation_at(old_decision) is not None

    def test_off_cycle_filer_keeps_own_vintage(self):
        # Two filers, different fiscal calendars.  At 2024-08-12 filer B's
        # newest vintage (eff 2024-05-31) is NEWER than filer A's (eff
        # 2024-03-31); a single-vintage rule keyed on the newest effective
        # date would eject filer A.  The multi-vintage mix keeps both.
        filer_a = series(
            stamp("2024-05-10", "2024-03-31", 100.0),
            stamp("2024-08-09", "2024-06-30", 140.0),
            entity="CIK000000000A",
        )
        filer_b = series(
            stamp("2024-07-15", "2024-05-31", 300.0),
            entity="CIK000000000B",
        )
        timeline = coverage_timeline(
            {"CIK000000000A": filer_a, "CIK000000000B": filer_b},
            ["CIK000000000A", "CIK000000000B"],
            [date(2024, 8, 12)],
        )
        assert timeline == [(date(2024, 8, 12), 1.0)]

    def test_non_numeric_value_never_counts_as_coverage(self):
        bucket = series(stamp("2024-05-10", "2024-03-31", None))
        observation = bucket.observation_at(date(2024, 6, 3))
        assert observation is not None
        assert observation.value is None
        covered, mapped, numeric = __import__(
            "research.assets.stocks.p0a_multivintage", fromlist=["sector_asof_mix"]
        ).sector_asof_mix(
            {"CIK0000000001": bucket}, ["CIK0000000001"], date(2024, 6, 3)
        )
        assert (covered, mapped, numeric) == (1, 1, 0)

    def test_conflicting_same_rank_vintages_fail_closed(self):
        bucket = FilerFieldSeries(entity_id="CIK0000000001")
        bucket.add(stamp("2024-05-10", "2024-03-31", 100.0))
        bucket.add(stamp("2024-05-10", "2024-03-31", 200.0))
        with pytest.raises(ValueError):
            bucket.finalize(strict=True)

    def test_census_mode_counts_conflict_and_keeps_coverage(self):
        # Coverage-census mode: a same-rank conflicting pair (real store
        # case: a same-day restatement) is counted and kept; coverage is
        # invariant to which value wins.
        bucket = FilerFieldSeries(entity_id="CIK0000000001")
        bucket.add(stamp("2024-05-10", "2024-03-31", 100.0))
        bucket.add(stamp("2024-05-10", "2024-03-31", 200.0))
        bucket.finalize(strict=False)
        assert bucket.rank_conflicts == 1
        observation = bucket.observation_at(date(2024, 6, 3))
        assert observation is not None
        assert observation.value in (100.0, 200.0)

    def test_identical_duplicate_vintages_are_idempotent(self):
        bucket = series(
            stamp("2024-05-10", "2024-03-31", 100.0),
            stamp("2024-05-10", "2024-03-31", 100.0),
        )
        assert len(bucket.stamps) == 2
        assert bucket.observation_at(date(2024, 6, 3)).value == 100.0


class TestCensusHelpers:
    def test_first_cross_date(self):
        timeline = [
            (date(2024, 1, 2), 0.2),
            (date(2024, 4, 1), 0.6),
            (date(2024, 7, 1), 0.9),
        ]
        assert first_cross_date(timeline, 0.4) == date(2024, 4, 1)
        assert first_cross_date(timeline, 0.95) is None

    def test_lag_stats_percentiles_hand_computed(self):
        stats = lag_stats([10, 20, 30, 40, 100])
        assert stats.n == 5
        assert stats.p50_days == 30
        assert stats.p75_days == 40
        assert stats.p90_days == 100
        assert stats.max_days == 100
        assert stats.min_days == 10
        assert abs(stats.mean_days - 40.0) < 1e-9

    def test_lag_stats_empty_is_none(self):
        assert lag_stats([]) is None

    def test_ex_ante_grids_frozen(self):
        assert AGE_GRID_DAYS == (120, 200, 400, 550, 800, None)
        assert COVERAGE_FLOORS == (0.4, 0.6, 0.8)

    def test_eod_stamp_check(self):
        assert stamp_is_eod_utc(parse_iso_utc("2024-05-10T23:59:59+00:00"))
        assert not stamp_is_eod_utc(parse_iso_utc("2024-05-10T14:30:00+00:00"))


class TestDeterministicEmission:
    def test_series_observation_is_order_independent(self):
        forward = series(
            stamp("2024-05-10", "2024-03-31", 100.0),
            stamp("2024-08-09", "2024-06-30", 200.0),
        )
        backward = series(
            stamp("2024-08-09", "2024-06-30", 200.0),
            stamp("2024-05-10", "2024-03-31", 100.0),
        )
        sessions = [date(2024, 6, 3), date(2024, 9, 2)]
        for session in sessions:
            assert (
                forward.observation_at(session).value
                == backward.observation_at(session).value
            )

    def test_timeline_bytes_are_deterministic(self):
        bucket = series(
            stamp("2024-05-10", "2024-03-31", 100.0),
            stamp("2024-08-09", "2024-06-30", 200.0),
        )
        sessions = [date(2024, 6, 3), date(2024, 9, 2)]
        first = json.dumps(
            [[d.isoformat(), f] for d, f in coverage_timeline(
                {"e": bucket}, ["e"], sessions
            )],
            sort_keys=True,
        )
        second = json.dumps(
            [[d.isoformat(), f] for d, f in coverage_timeline(
                {"e": bucket}, ["e"], sessions
            )],
            sort_keys=True,
        )
        assert first.encode("utf-8") == second.encode("utf-8")


# --------------------------------------------------------------------------
# sanitizer round-trip on a synthetic companyfacts sample
# --------------------------------------------------------------------------

def _companyfacts_payload() -> dict:
    fact = {
        "label": "Assets",
        "description": "Total assets",
        "units": {
            "USD": [
                {
                    "end": "2023-12-31",
                    "val": 123456789,
                    "accn": "0000000000-24-000001",
                    "fy": 2024,
                    "fp": "FY",
                    "form": "10-K",
                    "filed": "2024-02-15",
                },
                # byte-identical duplicate the sanitizer must drop once
                {
                    "end": "2023-12-31",
                    "val": 123456789,
                    "accn": "0000000000-24-000001",
                    "fy": 2024,
                    "fp": "FY",
                    "form": "10-K",
                    "filed": "2024-02-15",
                },
                # null val the sanitizer must drop
                {
                    "end": "2022-12-31",
                    "val": None,
                    "accn": "0000000000-23-000001",
                    "fy": 2023,
                    "fp": "FY",
                    "form": "10-K",
                    "filed": "2023-02-15",
                },
                # empty fp the sanitizer must drop
                {
                    "end": "2021-12-31",
                    "val": 5,
                    "accn": "0000000000-22-000001",
                    "fy": 2022,
                    "fp": "",
                    "form": "10-K",
                    "filed": "2022-02-15",
                },
            ]
        },
    }
    return {
        "cik": 1,
        "entityName": "Fixture Co",
        "facts": {"dei": {}, "us-gaap": {"Assets": fact}},
    }


class TestSanitizerRoundTrip:
    def test_round_trip_keeps_vintages_and_drops_only_rejected(self):
        payload = _companyfacts_payload()
        sanitized, stats = sanitize_companyfacts(payload)
        assets = sanitized["facts"]["us-gaap"]["Assets"]["units"]["USD"]
        assert len(assets) == 1
        assert assets[0]["end"] == "2023-12-31"
        assert assets[0]["filed"] == "2024-02-15"
        assert stats.dropped_duplicate_identical == 1
        assert stats.dropped_null_val == 1
        assert stats.dropped_empty_fp == 1
        assert stats.total_dropped() == 3

    def test_round_trip_preserves_multi_vintage_history(self):
        # The sanitizer must NOT collapse vintages: two filings of the same
        # period end (an amendment) both survive with distinct filed dates -
        # this is the store property the F1 diagnosis relies on.
        payload = _companyfacts_payload()
        units = payload["facts"]["us-gaap"]["Assets"]["units"]["USD"]
        units.insert(
            1,
            {
                "end": "2023-12-31",
                "val": 124000000,
                "accn": "0000000000-24-000002",
                "fy": 2024,
                "fp": "FY",
                "form": "10-K/A",
                "filed": "2024-03-20",
            },
        )
        sanitized, stats = sanitize_companyfacts(payload)
        assets = sanitized["facts"]["us-gaap"]["Assets"]["units"]["USD"]
        assert [entry["filed"] for entry in assets] == ["2024-02-15", "2024-03-20"]
        assert stats.dropped_duplicate_identical == 1  # the byte-identical row
        assert stats.dropped_duplicate_conflicting == 0
