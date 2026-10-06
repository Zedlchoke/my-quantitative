"""test_adapter_f3 — pytest proofs for the NQ-F3 RUN-REV adapter (synthetic)."""
from __future__ import annotations

import copy
import json

import pytest

import nq_common as nc
from conftest import load_expected, load_fixture
from expwitch_refusal import ExpwitchDeadAtGate
from f3_run_rev.adapter import (CONTROL_IDS, CORE_IDS, DRAFT_IDS, RunRevAdapter)

AD = RunRevAdapter()
PANEL = None


def panel() -> dict:
    return load_fixture("f3", "f3_panel_daily.json")


def trunc_sessions(p: dict, asof: str) -> dict:
    """Truncate the held series (and bars) to sessions <= asof's date."""
    cut = nc.parse_ts(asof).date().isoformat()
    out = copy.deepcopy(p)
    out["sessions"] = [s for s in out["sessions"] if s["session_date"] <= cut]
    out["bars"] = [b for b in out["bars"] if b.get("session_date", "") <= cut]
    return out


def synth_gross(entry: float, exit_: float, direction: int) -> float:
    return round((exit_ - entry) * direction * 20.0, 6)


def test_identity_enumeration_matches_budget():
    assert CORE_IDS == ["FBNQ1-F3-CONT-UP-D0-S2", "FBNQ1-F3-CONT-DN-D0-S2",
                        "FBNQ1-F3-REV-UP-D0-S2", "FBNQ1-F3-REV-DN-D0-S2"]
    assert CONTROL_IDS == ["FBNQ1-F3-SHDW-D0-S2", "FBNQ1-F3-ALW-D0-S2",
                           "FBNQ1-F3-FLAT"]
    assert len(DRAFT_IDS) == 7


def test_triggers_match_manifest():
    exp = load_expected("f3")["expected"]
    obs = AD.build_observables(panel(), panel()["calendar"])
    got = [t["session_date"] for t in obs["triggers"]]
    assert got == exp["triggers"]
    assert obs["rebuild_precondition_reference"].startswith("FUTURES-K6GATE-PREP-20261004")


def test_run1_roll_cross_dropped():
    exp = load_expected("f3")["expected"]["run1_roll_cross"]
    p = panel()
    for iid in ("FBNQ1-F3-REV-DN-D0-S2", "FBNQ1-F3-CONT-DN-D0-S2"):
        it = AD.order_intent(p, p["calendar"], iid, exp["trigger_session"])
        assert it["no_trade"] and it["no_trade_reason"] == exp["no_trade_reason"]
        assert it["entry_session"] == exp["entry_session"]
        assert it["exit_session"] == exp["exit_session"]


def test_run2_clean_intents_match_manifest():
    exp = load_expected("f3")["expected"]["run2_clean"]
    p = panel()
    for iid, gexp in exp["gross_synthetic_usd"].items():
        it = AD.order_intent(p, p["calendar"], iid, exp["trigger_session"])
        assert it["no_trade"] is False, (iid, it["no_trade_reason"])
        assert it["entry_session"] == exp["entry_session"]
        assert it["exit_session"] == exp["exit_session"]
        assert it["entry_ref_price"] == exp["entry_ref_price"]
        assert it["exit_ref_price"] == exp["exit_ref_price"]
        assert it["exit_reason"] == exp["exit_reason"]
        assert it["holding_held_sessions"] == exp["holding_held_sessions"]
        assert nc.on_tick_grid(it["entry_ref_price"])
        assert nc.on_tick_grid(it["exit_ref_price"])
        assert synth_gross(it["entry_ref_price"], it["exit_ref_price"],
                           it["direction"]) == gexp
    for iid in exp["tail_mismatch_ids"]:
        it = AD.order_intent(p, p["calendar"], iid, exp["trigger_session"])
        assert it["no_trade"] and it["no_trade_reason"] == "TAIL_MISMATCH"


def test_k4_run_does_not_trigger():
    exp = load_expected("f3")["expected"]["no_trigger_k4"]
    p = panel()
    sig = AD.signal(p, p["calendar"], exp["session_date"], None)
    assert sig["trigger"] is False and sig["run_len"] == exp["run_len"]
    it = AD.order_intent(p, p["calendar"], "FBNQ1-F3-REV-DN-D0-S2", exp["session_date"])
    assert it["no_trade"] and it["no_trade_reason"] == exp["reason"]


def test_run3_entry_on_fomc_day_excluded():
    exp = load_expected("f3")["expected"]["no_trade"]["run3_fomc_entry"]
    p = panel()
    sig = AD.signal(p, p["calendar"], exp["trigger_session"], None)
    assert sig["trigger"] is True and sig["tail"] == "DN"
    it = AD.order_intent(p, p["calendar"], "FBNQ1-F3-REV-DN-D0-S2",
                         exp["trigger_session"])
    assert it["no_trade"]
    assert it["no_trade_reason"] == exp["reason"]
    assert it["entry_session"] == exp["entry_session"]


def test_shdw_and_flat():
    exp = load_expected("f3")["expected"]
    p = panel()
    it = AD.order_intent(p, p["calendar"], "FBNQ1-F3-SHDW-D0-S2",
                         exp["shdw"]["session_date"])
    assert it["no_trade"] is False
    assert it["direction"] == exp["shdw"]["shadow_direction"]
    assert it["entry_ref_price"] == exp["shdw"]["entry_ref_price"]
    assert synth_gross(it["entry_ref_price"], it["exit_ref_price"],
                       it["direction"]) == exp["shdw"]["gross_synthetic_usd"]["FBNQ1-F3-SHDW-D0-S2"]
    nt = exp["no_trade"]["flat_anchor"]
    it = AD.order_intent(p, p["calendar"], nt["identity"], "2023-08-24")
    assert it["no_trade"] and it["no_trade_reason"] == nt["reason"]


@pytest.mark.parametrize("asof", ["2023-08-24T16:00:00-05:00",
                                  "2023-08-28T20:00:00-05:00",
                                  "2023-09-01T20:00:00-05:00"])
def test_pit_truncated_series_identical(asof):
    p = panel()
    for iid in ("FBNQ1-F3-REV-UP-D0-S2", "FBNQ1-F3-CONT-UP-D0-S2"):
        a = json.dumps(AD.signal(p, p["calendar"], "2023-08-24", asof), sort_keys=True)
        b = json.dumps(AD.signal(trunc_sessions(p, asof), p["calendar"],
                                 "2023-08-24", asof), sort_keys=True)
        assert a == b
        a = json.dumps(AD.order_intent(p, p["calendar"], iid, "2023-08-24", asof=asof),
                       sort_keys=True)
        b = json.dumps(AD.order_intent(trunc_sessions(p, asof), p["calendar"], iid,
                                       "2023-08-24", asof=asof), sort_keys=True)
        assert a == b


def test_signal_knowable_only_at_close():
    p = panel()
    early = AD.signal(p, p["calendar"], "2023-08-24", "2023-08-24T15:00:00-05:00")
    assert early["knowable"] is False
    at_close = AD.signal(p, p["calendar"], "2023-08-24", "2023-08-24T16:00:00-05:00")
    assert at_close["knowable"] is True and at_close["trigger"] is True


def test_gates_and_determinism():
    p = panel()
    with pytest.raises(nc.RefusedPendingOwnerDecision) as ei:
        AD.build_observables({**p, "provenance": "nq_held_daily_v3"}, p["calendar"])
    assert ei.value.slot_id == "P5-NQ1"
    with pytest.raises(nc.RefusedPendingOwnerDecision):
        nc.bind_option("NQ-C")
    with pytest.raises(ExpwitchDeadAtGate):
        nc.bind_option("NQ-D")
    a = json.dumps(AD.order_intent(p, p["calendar"], "FBNQ1-F3-REV-UP-D0-S2",
                                   "2023-08-24"), sort_keys=True)
    b = json.dumps(AD.order_intent(p, p["calendar"], "FBNQ1-F3-REV-UP-D0-S2",
                                   "2023-08-24"), sort_keys=True)
    assert a == b


def test_horizon_beyond_panel():
    p = panel()
    it = AD.order_intent(p, p["calendar"], "FBNQ1-F3-REV-UP-D0-S2", "2023-09-12")
    assert it["no_trade"] and it["no_trade_reason"] in ("HORIZON_BEYOND_PANEL",
                                                        "NO_TRIGGER")
