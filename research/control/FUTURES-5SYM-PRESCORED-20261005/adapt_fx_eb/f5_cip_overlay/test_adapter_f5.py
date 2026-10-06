"""F5 overlay tests — machinery-only: strata split, no-own-signal law, evidence
refusal, PB2 refusal. Outcome-blind; synthetic only."""
import copy

from fx_common import RefusedPendingEvidence, RefusedPendingOwnerDecision
from conftest import load_fixture
from f5_cip_overlay import adapter as f5

import pytest


@pytest.fixture(scope="module")
def ctx():
    panels = {sym: load_fixture("f5_cip_overlay", f"panel_{sym}.json")
              for sym in ("6E", "6B")}
    series = {sym: load_fixture("f5_cip_overlay", f"series_{sym}.json")["series"]
              for sym in ("6E", "6B")}
    expected = load_fixture("f5_cip_overlay", "EXPECTED_MANIFEST.json")["expected"]
    return panels, series, expected


@pytest.mark.parametrize("sym", ["6E", "6B"])
def test_strata_split(ctx, sym):
    panels, series, expected = ctx
    obs = f5.build_observables(panels[sym], {}, sym, series[sym])
    assert obs["standalone_identities"] == 0
    highs = sorted(d for d, v in obs["strata"].items() if v["stratum"] == "HIGH")
    lows = sorted(d for d, v in obs["strata"].items() if v["stratum"] == "LOW")
    assert highs == expected["high_dates"]
    assert lows == expected["low_dates"]
    # boundary law: diff == 0 is LOW (diff <= 0)
    assert obs["strata"]["2026-03-04"]["stratum"] == "LOW"
    assert obs["strata"]["2026-03-10"]["stratum"] == "LOW"


@pytest.mark.parametrize("sym", ["6E", "6B"])
def test_no_own_signal_law(ctx, sym):
    panels, series, _ = ctx
    obs = f5.build_observables(panels[sym], {}, sym, series[sym])
    sig = f5.signal(obs, "2026-03-05", {}, sym, {}, panels[sym])
    assert sig["status"] == "NO_TRADE"
    assert sig["blocking"] == ["OVERLAY_NO_OWN_SIGNAL"]
    assert sig["host_stratum"] == "HIGH"
    assert "rows 56/64/65/83" in sig["ancestry_fence"]


def test_evidence_gate_refusal(ctx):
    with pytest.raises(RefusedPendingEvidence) as ei:
        f5.require_f5_evidence()
    assert ei.value.item == "F5_CIP_VINTAGE_QUANTIFICATION_NOT_RUN"
    assert "SOFR" in ei.value.detail and "court" in ei.value.detail


def test_pb2_refusal_real_data_path(ctx):
    panels, series, _ = ctx
    panel = copy.deepcopy(panels["6E"])
    panel["provenance"] = "REAL_6E_CACHE"
    with pytest.raises(RefusedPendingOwnerDecision) as ei:
        f5.build_observables(panel, {}, "6E", series["6E"])
    assert ei.value.slot_id == "P5-FXEB-OD1"
