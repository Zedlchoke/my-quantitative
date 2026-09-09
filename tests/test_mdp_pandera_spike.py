"""Pandera compatibility spike test: runs the differential, writes NO verdict.

The measured evidence (per-fixture accepted/rejected equality, timings,
criteria checklist) is reported as a dict for A1's P5A decision.  This test
asserts only execution integrity: the runner runs, the input is never
mutated, and the evidence bundle has the frozen criteria checklist.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "research"))

import pytest  # noqa: E402

from market_data_plane import _pandera_spike as spike  # noqa: E402
from market_data_plane import models  # noqa: E402

pytest.importorskip("pandera", reason="pandera spike requires the pinned install")
pytest.importorskip("pandas", reason="pandera spike requires the pinned install")


def test_spike_module_constants_match_the_freeze():
    assert spike.SPIKE_SCOPE == ("batch/DataFrame ingestion boundary only; "
                                 "strict=True; no implicit column addition; "
                                 "coerce=False by default")
    assert spike.FIXTURE_NAMES == ("crypto trades", "forex bid/ask",
                                   "stocks quotes", "macro series")
    assert len(spike.ADOPT_REQUIRES_ALL) == 7
    assert spike.FAILURE_VERDICT == "PANDERA_EVALUATED_NOT_ADOPTED"
    assert spike.TIMING_REPEATS >= 5


def test_trade_and_quote_schemas_exist_and_are_strict_non_coercing():
    for build in (spike.trade_schema, spike.quote_schema):
        schema = build()
        assert schema.strict == "strict" or schema.strict is True
        assert schema.coerce is False


def test_differential_runs_on_all_four_frozen_fixture_sets():
    fixtures = spike.build_fixtures(rows_per_fixture=12)
    assert tuple(fixtures) == spike.FIXTURE_NAMES
    for name, rows in fixtures.items():
        evidence = spike.differential(rows)
        assert set(evidence) >= {"raw_boundary", "canonical_control",
                                 "duplicate_note"}
        for mode in ("raw_boundary", "canonical_control"):
            result = evidence[mode]
            assert result["rows"] == len(rows) or mode == "canonical_control"
            assert "same_row_sets" in result
            assert "same_reason_attribution" in result
            assert "native_rejected" in result
            assert "pandera_rejected" in result


def test_native_and_pandera_runs_never_mutate_the_input():
    fixtures = spike.build_fixtures(rows_per_fixture=8)
    import copy
    snapshot = copy.deepcopy(fixtures)
    for name, rows in fixtures.items():
        spike.run_native(rows)
        spike.run_pandera(rows)
    assert fixtures == snapshot  # no mutation of the input (frozen criterion)


def test_canonical_control_agrees_on_market_fixtures():
    """Measured evidence: on canonical batches pandera matches native exactly.

    This is reported as evidence, not adopted as a verdict: the frozen spike
    scope is the RAW ingestion boundary, where batch-level dtype poisoning
    changes accepted/rejected row sets (see the evidence bundle below).
    """
    fixtures = spike.build_fixtures(rows_per_fixture=24)
    for name in ("crypto trades", "forex bid/ask", "stocks quotes"):
        control = spike.differential(fixtures[name])["canonical_control"]
        assert control["rows"] > 0
        assert control["same_row_sets"], (name, control)
        assert control["same_reason_attribution"], (name, control)


def test_evidence_bundle_reports_measured_criteria_without_deciding():
    evidence = spike.collect_evidence(rows_per_fixture=10)
    # verdict authority recorded for A1; this test writes no verdict
    assert evidence["verdict_authority"].startswith("A1 at P5A")
    candidate = evidence["candidate_verdict_if_a1_follows_the_frozen_rule"]
    assert candidate in ("ADOPTED", "PANDERA_EVALUATED_NOT_ADOPTED")
    checklist = evidence["criteria_checklist"]
    for criterion in spike.ADOPT_REQUIRES_ALL:
        assert criterion in checklist, criterion
    for name, entry in evidence["per_fixture"].items():
        timing = entry["timing"]
        assert timing["repeats"] >= 5
        assert timing["native_median_s"] > 0
        assert timing["pandera_median_s"] > 0
        assert timing["pandera_over_native_ratio"] > 0
        assert entry["no_input_mutation"] is True
        assert entry["dtype_preservation"]["timestamp_timezone_loss"] in \
            (True, False)
        assert entry["dtype_preservation"]["decimal_to_float"] in (True, False)
    # determinism measured per fixture
    for name, det in evidence["determinism_vs_row_order"].items():
        assert det["deterministic"] in (True, False)
        assert det["native_stable"] is True
    # report the measured evidence for the run log
    ratios = {name: round(entry["timing"]["pandera_over_native_ratio"], 1)
              for name, entry in evidence["per_fixture"].items()}
    print("\n[pandera-spike evidence] candidate verdict:", candidate)
    print("[pandera-spike evidence] failing criteria:",
          evidence["failing_criteria"])
    print("[pandera-spike evidence] pandera/native timing ratios:", ratios)
    print("[pandera-spike evidence] canonical-control agreement:",
          {name: (entry["canonical_control"]["same_row_sets"]
                  and entry["canonical_control"]["same_reason_attribution"])
           for name, entry in evidence["per_fixture"].items()})
    print("[pandera-spike evidence] raw-boundary agreement:",
          {name: (entry["raw_boundary"]["same_row_sets"]
                  and entry["raw_boundary"]["same_reason_attribution"])
           for name, entry in evidence["per_fixture"].items()})
