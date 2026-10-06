"""test_adapter_f2 — pytest proofs for the NQ-F2 MACRO-0730 adapter (synthetic)."""
from __future__ import annotations

import copy
import json

import pytest

import nq_common as nc
from conftest import load_expected, load_fixture
from expwitch_refusal import ExpwitchDeadAtGate
from f2_macro_0730.adapter import (CONTROL_IDS, CORE_IDS, DRAFT_IDS, Macro0730Adapter,
                                   shadow_direction)

AD = Macro0730Adapter()


def trunc(panel: dict, asof: str) -> dict:
    t = nc.parse_ts(asof)
    return {**panel, "bars": [b for b in panel["bars"] if nc.parse_ts(b["ts"]) <= t]}


def synth_gross(entry: float, exit_: float, direction: int) -> float:
    return round((exit_ - entry) * direction * 20.0, 6)


def test_identity_enumeration_matches_budget():
    assert CORE_IDS == [
        "FBNQ1-F2-CONT-UP-D0-S2", "FBNQ1-F2-CONT-UP-D30-S2",
        "FBNQ1-F2-CONT-DN-D0-S2", "FBNQ1-F2-CONT-DN-D30-S2",
        "FBNQ1-F2-REV-UP-D0-S2", "FBNQ1-F2-REV-UP-D30-S2",
        "FBNQ1-F2-REV-DN-D0-S2", "FBNQ1-F2-REV-DN-D30-S2"]
    assert CONTROL_IDS == ["FBNQ1-F2-SHDW-D0-S2", "FBNQ1-F2-ALW-D0-S2",
                           "FBNQ1-F2-FLAT"]
    assert len(DRAFT_IDS) == 11


def test_cpi_up_day_intents_match_manifest():
    exp = load_expected("f2")["expected"]["cpi_up_day"]
    panel = load_fixture("f2", "f2_panel_core.json")
    cal = panel["calendar"]
    for iid, gexp in exp["gross_synthetic_usd"].items():
        it = AD.order_intent(panel, cal, iid, exp["session_date"])
        assert it["no_trade"] is False, (iid, it["no_trade_reason"])
        ex = exp["exits_by_id"][iid]
        assert it["entry_ref_price"] == exp["entries"][it["delay"]]
        assert it["exit_ref_price"] == ex["price"]
        assert it["exit_reason"] == ex["reason"]
        assert it["sl_price"] == pytest.approx(exp["sl_by_id"][iid])
        assert it["tp_price"] == pytest.approx(exp["tp_by_id"][iid])
        if ex["reason"] == "TP":
            assert it["ts_exit"] == exp["ts_exit_TP"]
        assert nc.on_tick_grid(it["entry_ref_price"]) and nc.on_tick_grid(it["exit_ref_price"])
        assert synth_gross(it["entry_ref_price"], it["exit_ref_price"],
                           it["direction"]) == gexp
    for iid in exp["tail_mismatch_ids"]:
        it = AD.order_intent(panel, cal, iid, exp["session_date"])
        assert it["no_trade"] and it["no_trade_reason"] == "TAIL_MISMATCH"


def test_cpi_dn_day_intents_match_manifest():
    exp = load_expected("f2")["expected"]["cpi_dn_day"]
    panel = load_fixture("f2", "f2_panel_core.json")
    for iid, gexp in exp["gross_synthetic_usd"].items():
        it = AD.order_intent(panel, panel["calendar"], iid, exp["session_date"])
        assert it["no_trade"] is False, (iid, it["no_trade_reason"])
        assert it["tail"] == "DN"
        assert it["entry_ref_price"] == exp["entries"][it["delay"]]
        assert it["exit_ref_price"] == exp["exit_price"]
        assert it["exit_reason"] == exp["exit_reason"]
        assert synth_gross(it["entry_ref_price"], it["exit_ref_price"],
                           it["direction"]) == gexp


def test_shdw_clock_day():
    exp = load_expected("f2")["expected"]["shdw_day"]
    assert shadow_direction(exp["session_date"]) == exp["shadow_direction"]
    panel = load_fixture("f2", "f2_panel_core.json")
    it = AD.order_intent(panel, panel["calendar"], "FBNQ1-F2-SHDW-D0-S2",
                         exp["session_date"])
    assert it["no_trade"] is False
    assert it["direction"] == exp["shadow_direction"]
    assert it["entry_ref_price"] == exp["entry_price_D0"]
    assert it["exit_ref_price"] == exp["exit_price"]
    assert synth_gross(it["entry_ref_price"], it["exit_ref_price"],
                       it["direction"]) == exp["gross_synthetic_usd"]["FBNQ1-F2-SHDW-D0-S2"]
    # SHDW refuses release days
    nt = load_expected("f2")["expected"]["no_trade"]["shdw_on_release_day"]
    it = AD.order_intent(panel, panel["calendar"], nt["identity"], nt["session_date"])
    assert it["no_trade"] and it["no_trade_reason"] == nt["reason"]


def test_fomc_overlap_excluded():
    exp = load_expected("f2")["expected"]["no_trade"]
    panel = load_fixture("f2", "f2_panel_core.json")
    it = AD.order_intent(panel, panel["calendar"], "FBNQ1-F2-CONT-UP-D0-S2", "2023-09-13")
    assert it["no_trade"]
    assert it["no_trade_reason"] == exp["fomc_overlap_2023-09-13"]


def test_canceled_day_control_stratum():
    exp = load_expected("f2")["expected"]["no_trade"]
    panel = load_fixture("f2", "f2_panel_canceled_2025.json")
    it = AD.order_intent(panel, panel["calendar"], "FBNQ1-F2-CONT-UP-D0-S2", "2025-10-15")
    assert it["no_trade"]
    assert it["no_trade_reason"] == exp["canceled_2025-10-15"]
    obs = AD.build_observables(panel, panel["calendar"])
    assert obs["canceled_control"][0]["stratum"] == "CANCELED_CONTROL"


def test_era_gated_outside_score_era():
    exp = load_expected("f2")["expected"]["no_trade"]
    panel = load_fixture("f2", "f2_panel_era_gated_2019.json")
    sig = AD.signal(panel, panel["calendar"], "2019-06-12", None)
    assert sig["event"] and sig["in_score_era"] is False
    it = AD.order_intent(panel, panel["calendar"], "FBNQ1-F2-CONT-UP-D0-S2", "2019-06-12")
    assert it["no_trade"] and it["no_trade_reason"] == exp["era_gated_2019-06-12"]


def test_vintage_known_by_law():
    exp = load_expected("f2")["expected"]["no_trade"]["vintage_unknown_at_decision_date"]
    panel = load_fixture("f2", "f2_panel_core.json")
    cal = copy.deepcopy(panel["calendar"])
    for r in cal["bls_vintage"]:
        if r["scheduled_date"] == "2023-06-13":
            r["known_by"] = exp["doctored_known_by"]   # not knowable at D
    it = AD.order_intent(panel, cal, "FBNQ1-F2-CONT-UP-D0-S2", "2023-06-13")
    assert it["no_trade"] and it["no_trade_reason"] == exp["reason"]
    obs = AD.build_observables(panel, cal)
    assert obs["vintage_unknown_at_decision_date"], "late-vintage row must be a stratum"


def test_d5_pin_law():
    exp = load_expected("f2")["expected"]["d5_pin"]
    panel = load_fixture("f2", "f2_panel_2026_d5.json")
    obs = AD.build_observables(panel, panel["calendar"])
    assert obs["scheduled_releases"][0]["scheduled_date"] == exp["pin_date"]
    it = AD.order_intent(panel, panel["calendar"], "FBNQ1-F2-CONT-UP-D0-S2", "2026-02-13")
    assert it["no_trade"]
    assert it["no_trade_reason"] == exp["with_pin_no_trade_reason"]
    stripped = copy.deepcopy(panel)
    stripped["calendar"]["bls_vintage"] = []
    with pytest.raises(nc.RefusedD5PinMissing):
        AD.build_observables(stripped, stripped["calendar"])
    with pytest.raises(nc.RefusedD5PinMissing):
        AD.order_intent(stripped, stripped["calendar"], "FBNQ1-F2-CONT-UP-D0-S2",
                        "2026-02-13")


def test_flat_anchor():
    panel = load_fixture("f2", "f2_panel_core.json")
    it = AD.order_intent(panel, panel["calendar"], "FBNQ1-F2-FLAT", "2023-06-13")
    assert it["no_trade"] and it["no_trade_reason"] == "FLAT_ANCHOR_ZERO_TRADES"


@pytest.mark.parametrize("asof", ["2023-06-13T07:31:00-05:00",
                                  "2023-06-13T09:00:00-05:00",
                                  "2023-06-13T15:59:00-05:00"])
def test_pit_truncated_panels_identical(asof):
    panel = load_fixture("f2", "f2_panel_core.json")
    for iid in ("FBNQ1-F2-CONT-UP-D0-S2", "FBNQ1-F2-REV-UP-D30-S2"):
        a = json.dumps(AD.signal(panel, panel["calendar"], "2023-06-13", asof),
                       sort_keys=True)
        b = json.dumps(AD.signal(trunc(panel, asof), panel["calendar"],
                                 "2023-06-13", asof), sort_keys=True)
        assert a == b
        a = json.dumps(AD.order_intent(panel, panel["calendar"], iid, "2023-06-13",
                                       asof=asof), sort_keys=True)
        b = json.dumps(AD.order_intent(trunc(panel, asof), panel["calendar"], iid,
                                       "2023-06-13", asof=asof), sort_keys=True)
        assert a == b


def test_p5nq1_real_provenance_refused():
    panel = load_fixture("f2", "f2_panel_core.json")
    with pytest.raises(nc.RefusedPendingOwnerDecision) as ei:
        AD.build_observables({**panel, "provenance": "cache_v3"}, panel["calendar"])
    assert ei.value.slot_id == "P5-NQ1"


def test_p5nq2_and_nqd_and_p5nq3_gates():
    with pytest.raises(nc.RefusedPendingOwnerDecision) as ei:
        nc.bind_option("NQ-B")
    assert ei.value.slot_id == "P5-NQ2"
    with pytest.raises(ExpwitchDeadAtGate):
        nc.bind_option("NQ-D")
    with pytest.raises(nc.RefusedPendingOwnerDecision) as ei:
        nc.cost_per_side_usd("S2", variant="B")
    assert ei.value.slot_id == "P5-NQ3"


def test_determinism_and_warmup():
    panel = load_fixture("f2", "f2_panel_core.json")
    a = json.dumps(AD.order_intent(panel, panel["calendar"], "FBNQ1-F2-CONT-UP-D0-S2",
                                   "2023-06-13"), sort_keys=True)
    b = json.dumps(AD.order_intent(panel, panel["calendar"], "FBNQ1-F2-CONT-UP-D0-S2",
                                   "2023-06-13"), sort_keys=True)
    assert a == b
    thin = {**panel, "sessions": panel["sessions"][:2]}
    it = AD.order_intent(thin, panel["calendar"], "FBNQ1-F2-CONT-UP-D0-S2", "2023-06-13")
    assert it["no_trade"] and it["no_trade_reason"] == "ATR_WARMUP_INSUFFICIENT"
