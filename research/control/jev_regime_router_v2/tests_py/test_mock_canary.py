"""Mock classifier + canary machinery: fixtures, perturbations, acceptance."""

from __future__ import annotations

import pytest

from jrv2.canary import perturbation_fixtures, run_canary_synthetic
from jrv2.features import normalize_semantic_state
from jrv2.mock_adapter import MOCK_MODEL, MockProvider, mock_answers, mock_decide
from jrv2.questionio import compute_input_digest, validate_response_line
from jrv2.safety import UNKNOWN, effective_from_response


PARAMS = {"min_confidence": 0.5, "min_margin": 0.2, "confirm_bars": 2, "min_dwell": 6, "cooldown": 3}


def _run_fixture(fz, fx):
    st = normalize_semantic_state(fx["state"])
    sid = "0123456789abcdef"
    resp = mock_decide(sid, st, MOCK_MODEL)
    digest = compute_input_digest(st, MOCK_MODEL)
    normalized, violation = validate_response_line(resp, sid, digest, None)
    label, eligible, reason = effective_from_response(normalized, PARAMS)
    return normalized, violation, label, reason


def test_mock_fixture_expectations(fz):
    """Every frozen fixture lands on its expected effective label via the
    deterministic mock (plumbing law)."""
    for fx in fz.canary_contract["synthetic_fixtures"]:
        expected = fx.get("expected", {}).get("effective")
        if fx["state"] is None:
            continue  # C8: never sent
        _, violation, label, _ = _run_fixture(fz, fx)
        assert violation is None, fx["id"]
        assert label == expected, fx["id"]
        # the raw phase choice is ALWAYS one of the 4 phases (forced choice)
        # even when the answer is a deliberate contradiction


def test_mock_raw_phase_never_abstains(fz):
    for fx in fz.canary_contract["synthetic_fixtures"]:
        if fx["state"] is None:
            continue
        st = normalize_semantic_state(fx["state"])
        resp = mock_decide("0123456789abcdef", st, MOCK_MODEL)
        choice = resp["answers"]["phase"]["choice"]
        assert choice in ("ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND")


def test_mock_deterministic_per_state():
    st = {"bins": {"fast_trend": "strong_up", "slow_trend": "weak_up", "trend_strength": "high"},
          "numerics": {"adx14": 40}, "prior_structure": "TREND_UP", "prior_direction": "UP"}
    r1 = mock_decide("aaaaaaaaaaaaaaaa", st, MOCK_MODEL)
    r2 = mock_decide("aaaaaaaaaaaaaaaa", st, MOCK_MODEL)
    assert r1 == r2


def test_mock_probabilities_sum_to_one_and_margin_ok():
    st = {"bins": {"fast_trend": "flat", "slow_trend": "flat", "trend_strength": "low"},
          "numerics": {}, "prior_structure": "RANGE", "prior_direction": "DOWN"}
    resp = mock_decide("aaaaaaaaaaaaaaaa", st, MOCK_MODEL)
    for q, block in resp["answers"].items():
        s = sum(block["probabilities"].values())
        assert abs(s - 1.0) <= 0.01, q
    phase = resp["answers"]["phase"]
    vals = sorted(phase["probabilities"].values(), reverse=True)
    assert vals[0] - vals[1] >= 0.20  # margin gate satisfiable by design


def test_mock_answers_rule_total_on_bins():
    """The rule covers the bin space deterministically; contradictions land on
    schema-valid answers that the safety layer abstains."""
    # agreement up
    a = mock_answers({"fast_trend": "strong_up", "slow_trend": "weak_up"}, "UP", "TREND_UP")
    assert a == {"structure": "TREND", "direction": "UP", "phase": "UPTREND"}
    # agreement down
    a = mock_answers({"fast_trend": "strong_down", "slow_trend": "weak_down"}, "DOWN", "TREND_DOWN")
    assert a == {"structure": "TREND", "direction": "DOWN", "phase": "DOWNTREND"}
    # flat fast + prior UP -> DISTRIBUTION proposal
    a = mock_answers({"fast_trend": "flat", "slow_trend": "weak_up"}, "UP", "RANGE")
    assert a == {"structure": "RANGE", "direction": "NEUTRAL", "phase": "DISTRIBUTION"}
    # flat fast + prior none -> contradiction proposal
    a = mock_answers({"fast_trend": "flat", "slow_trend": "flat"}, "none", "none")
    assert a["structure"] == "RANGE" and a["direction"] == "NEUTRAL"
    # mixed -> TREND+NEUTRAL contradiction
    a = mock_answers({"fast_trend": "strong_up", "slow_trend": "weak_down"}, "UP", "TREND_UP")
    assert (a["structure"], a["direction"]) == ("TREND", "NEUTRAL")


def test_perturbation_fixtures_deterministic_and_stable(fz):
    pf1 = perturbation_fixtures(fz)
    pf2 = perturbation_fixtures(fz)
    clear_ids = [fx["id"] for fx in fz.canary_contract["synthetic_fixtures"] if fx["class"] == "clear"]
    assert sorted(pf1.keys()) == sorted(clear_ids)
    for fid in clear_ids:
        assert len(pf1[fid]) == 8
        # determinism: identical numerics across calls
        n1 = [s.state["numerics"] for s in pf1[fid]]
        n2 = [s.state["numerics"] for s in pf2[fid]]
        assert n1 == n2
        # bins recomputed and consistent with the numerics
        for st in pf1[fid]:
            assert st.state["bins"] is not None
        # expected label of the family unchanged
        expected = next(
            fx["expected"]["effective"]
            for fx in fz.canary_contract["synthetic_fixtures"]
            if fx["id"] == fid
        )
        provider = MockProvider(MOCK_MODEL)
        kept = 0
        for fs in pf1[fid]:
            resp = provider("bbbbbbbbbbbbbbbb", fs.state)
            digest = compute_input_digest(fs.payload(), MOCK_MODEL)
            norm, viol = validate_response_line(resp, "bbbbbbbbbbbbbbbb", digest, None)
            label, _, _ = effective_from_response(norm, PARAMS)
            assert label == expected, (fid, viol)
            kept += label == expected
        assert kept == 8  # >= 6/8 threshold exceeded (mock is deterministic)


def test_canary_synthetic_all_criteria_pass_mock(fz):
    result = run_canary_synthetic(
        fz, MockProvider(MOCK_MODEL), MOCK_MODEL, None, mock=True
    )
    assert result["namespace"] == "MOCK"
    assert result["ok"] is True, [c for c in result["checks"] if not c["pass"]]
    assert len(result["checks"]) == 10
    # measured cost/latency recorded
    m = result["measured"]
    assert m["n_sent"] == 7 and m["n_not_sent"] == 1
    assert m["usage_totals"]["input_tokens"] > 0
    assert m["total_latency_ms"] >= 0


def test_canary_c8_missing_stale_never_sent(fz):
    result = run_canary_synthetic(fz, MockProvider(MOCK_MODEL), MOCK_MODEL, None, mock=True)
    c8 = next(r for r in result["rows"] if r["id"] == "C8_MISSING_STALE")
    assert c8["effective"] == UNKNOWN
    assert c8["reason"] == "missing_or_stale_state_not_sent"
    assert c8["state_id"] is None


def test_canary_no_single_raw_phase_above_70pct(fz):
    result = run_canary_synthetic(fz, MockProvider(MOCK_MODEL), MOCK_MODEL, None, mock=True)
    check = next(c for c in result["checks"] if "70%" in c["criterion"])
    assert check["pass"] is True
    assert check["measured"]["max_share"] <= 0.70
