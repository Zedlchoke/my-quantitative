"""test_adapter_f1 — pytest proofs for the NQ-F1 FOMC-ERA adapter (synthetic).

Run: /Users/hoangminhlong/.venv/bin/python -m pytest f1_fomc_era -q   (from adapt_nq/)
Exit code recorded in dispatch/handoff_ADAPT-NQ.json.
"""
from __future__ import annotations

import copy
import json

import pytest

import nq_common as nc
from conftest import load_expected, load_fixture
from f1_fomc_era.adapter import (CONTROL_IDS, CORE_IDS, DRAFT_IDS, FomcEraAdapter,
                                 shadow_direction)

AD = FomcEraAdapter()


def trunc(panel: dict, asof: str) -> dict:
    t = nc.parse_ts(asof)
    return {**panel, "bars": [b for b in panel["bars"] if nc.parse_ts(b["ts"]) <= t]}


def synth_gross(entry: float, exit_: float, direction: int) -> float:
    """SYNTHETIC-ARITHMETIC sanity number (runner formula shape); not a PnL claim."""
    return round((exit_ - entry) * direction * 20.0, 6)


# ------------------------------------------------------------------ identity
def test_identity_enumeration_matches_budget():
    assert CORE_IDS == [
        "FBNQ1-F1-CONT-UP-D0-S2", "FBNQ1-F1-CONT-UP-D30-S2",
        "FBNQ1-F1-CONT-DN-D0-S2", "FBNQ1-F1-CONT-DN-D30-S2",
        "FBNQ1-F1-REV-UP-D0-S2", "FBNQ1-F1-REV-UP-D30-S2",
        "FBNQ1-F1-REV-DN-D0-S2", "FBNQ1-F1-REV-DN-D30-S2"]
    assert CONTROL_IDS == ["FBNQ1-F1-SHDW-D0-S2", "FBNQ1-F1-ALW-D0-S2",
                           "FBNQ1-F1-FLAT"]
    assert len(DRAFT_IDS) == 11
    assert nc.family_identity_counts()["NQ-F1"] == {
        "core": 8, "controls": 3, "minimal_total": 11}


def test_contract_binding():
    c = nc.load_nq_contract()
    assert (c["tick_size"], c["tick_value_usd"], c["multiplier"],
            c["long_base_sign"]) == (0.25, 5.0, 20.0, 1)


# ----------------------------------------------------------------- economics
def test_up_day_intents_match_manifest():
    exp = load_expected("f1")["expected"]["up_day"]
    panel = load_fixture("f1", "f1_panel_core.json")
    cal = panel["calendar"]
    for iid, gexp in exp["gross_synthetic_usd"].items():
        it = AD.order_intent(panel, cal, iid, exp["session_date"])
        assert it["no_trade"] is False, (iid, it["no_trade_reason"])
        if iid.startswith("FBNQ1-F1-CONT") or iid.startswith("FBNQ1-F1-REV"):
            assert it["tail"] == "UP"
        else:  # ALW: signal ignored by law
            assert it["arm"] == "ALW"
        assert it["entry_ref_price"] == exp["entries"][it["delay"]]
        assert it["exit_ref_price"] == exp["exit_price"]
        assert it["exit_reason"] == exp["exit_reason"]
        assert it["sl_price"] == pytest.approx(exp["sl_by_id"][iid])
        assert it["tp_price"] == pytest.approx(exp["tp_by_id"][iid])
        assert nc.on_tick_grid(it["entry_ref_price"]) and nc.on_tick_grid(it["exit_ref_price"])
        assert synth_gross(it["entry_ref_price"], it["exit_ref_price"],
                           it["direction"]) == gexp
    for iid in exp["tail_mismatch_ids"]:
        it = AD.order_intent(panel, cal, iid, exp["session_date"])
        assert it["no_trade"] and it["no_trade_reason"] == "TAIL_MISMATCH"


def test_dn_day_intents_match_manifest():
    exp = load_expected("f1")["expected"]["dn_day"]
    panel = load_fixture("f1", "f1_panel_july_dn.json")
    for iid, gexp in exp["gross_synthetic_usd"].items():
        it = AD.order_intent(panel, panel["calendar"], iid, exp["session_date"])
        assert it["no_trade"] is False, (iid, it["no_trade_reason"])
        assert it["tail"] == "DN"
        assert it["entry_ref_price"] == exp["entries"][it["delay"]]
        assert it["exit_ref_price"] == exp["exit_price"]
        assert synth_gross(it["entry_ref_price"], it["exit_ref_price"],
                           it["direction"]) == gexp


def test_era_a_day_exit_at_measured_close():
    exp = load_expected("f1")["expected"]["era_a_day"]
    panel = load_fixture("f1", "f1_panel_era_boundary.json")
    assert nc.era_for_date(exp["session_date"]) == "A"
    assert nc.era_close_min(exp["session_date"]) == 975  # 16:15 CT era-A law
    for iid, gexp in exp["gross_synthetic_usd"].items():
        it = AD.order_intent(panel, panel["calendar"], iid, exp["session_date"])
        assert it["no_trade"] is False
        assert it["session_context"]["era"] == "A"
        assert it["session_context"]["last_bar_ct"] == exp["last_bar_ct"]
        assert it["exit_ref_price"] == exp["exit_price"]
        assert it["ts_exit"].endswith("16:14:00-05:00")
        assert synth_gross(it["entry_ref_price"], it["exit_ref_price"],
                           it["direction"]) == gexp


def test_era_boundary_era_b_first_session():
    panel = load_fixture("f1", "f1_panel_era_boundary.json")
    assert nc.era_for_date("2015-09-18") == "A"      # era-A Friday 15:15 class
    assert nc.era_for_date("2015-09-21") == "B"      # SESSION_SWITCH_DATE
    assert nc.era_close_min("2015-09-21") == 960


def test_controls_match_manifest():
    exp = load_expected("f1")["expected"]
    shdw = exp["shdw_wednesday"]
    assert shadow_direction(shdw["session_date"]) == shdw["shadow_direction"]
    panel = load_fixture("f1", "f1_panel_core.json")
    it = AD.order_intent(panel, panel["calendar"], "FBNQ1-F1-SHDW-D0-S2",
                         shdw["session_date"])
    assert it["no_trade"] is False
    assert it["direction"] == shdw["shadow_direction"]
    assert it["entry_ref_price"] == shdw["entry_price_D0"]
    assert it["exit_ref_price"] == shdw["exit_price"]
    assert synth_gross(it["entry_ref_price"], it["exit_ref_price"],
                       it["direction"]) == shdw["gross_synthetic_usd"]["FBNQ1-F1-SHDW-D0-S2"]
    # ALW always-on in-window (signal ignored): trades the FOMC day even flat-sign
    it = AD.order_intent(panel, panel["calendar"], "FBNQ1-F1-ALW-D0-S2", "2023-06-14")
    assert it["no_trade"] is False and it["direction"] == 1
    # FLAT anchor: zero trades
    it = AD.order_intent(panel, panel["calendar"], "FBNQ1-F1-FLAT", "2023-06-14")
    assert it["no_trade"] and it["no_trade_reason"] == "FLAT_ANCHOR_ZERO_TRADES"
    # SHDW refuses non-Wednesday and FOMC-day matches
    it = AD.order_intent(panel, panel["calendar"], "FBNQ1-F1-SHDW-D0-S2", "2023-06-15")
    assert it["no_trade"] and it["no_trade_reason"] == "SHDW_NOT_WEDNESDAY"
    it = AD.order_intent(panel, panel["calendar"], "FBNQ1-F1-SHDW-D0-S2", "2023-06-14")
    assert it["no_trade"] and it["no_trade_reason"] == "SHDW_FOMC_DAY_MATCH"
    dn = load_fixture("f1", "f1_panel_july_dn.json")
    it = AD.order_intent(dn, dn["calendar"], "FBNQ1-F1-SHDW-D0-S2", "2023-07-26")
    assert it["no_trade"] and it["no_trade_reason"] == "SHDW_FOMC_DAY_MATCH"


def test_exclusion_days_no_trade():
    exp = load_expected("f1")["expected"]["no_trade"]
    panel = load_fixture("f1", "f1_panel_core.json")
    it = AD.order_intent(panel, panel["calendar"], "FBNQ1-F1-CONT-UP-D0-S2", "2023-06-16")
    assert it["no_trade"] and it["no_trade_reason"] == exp["2023-06-16"]
    excl = load_fixture("f1", "f1_panel_exclusions_2026.json")
    it = AD.order_intent(excl, excl["calendar"], "FBNQ1-F1-CONT-UP-D0-S2", "2026-01-19")
    assert it["no_trade"] and it["no_trade_reason"] == exp["2026-01-19"]
    it = AD.order_intent(excl, excl["calendar"], "FBNQ1-F1-CONT-UP-D0-S2", "2023-11-24")
    assert it["no_trade"] and it["no_trade_reason"] == exp["2023-11-24"]


# ----------------------------------------------------------------------- PIT
@pytest.mark.parametrize("asof", ["2023-06-14T13:01:00-05:00",
                                  "2023-06-14T14:00:00-05:00",
                                  "2023-06-14T15:59:00-05:00"])
def test_pit_truncated_panels_identical(asof):
    panel = load_fixture("f1", "f1_panel_core.json")
    for iid in ("FBNQ1-F1-CONT-UP-D0-S2", "FBNQ1-F1-REV-UP-D30-S2",
                "FBNQ1-F1-ALW-D0-S2"):
        full_sig = json.dumps(AD.signal(panel, panel["calendar"], "2023-06-14", asof),
                              sort_keys=True)
        trunc_sig = json.dumps(AD.signal(trunc(panel, asof), panel["calendar"],
                                         "2023-06-14", asof), sort_keys=True)
        assert full_sig == trunc_sig
        full = json.dumps(AD.order_intent(panel, panel["calendar"], iid,
                                          "2023-06-14", asof=asof), sort_keys=True)
        tr = json.dumps(AD.order_intent(trunc(panel, asof), panel["calendar"], iid,
                                        "2023-06-14", asof=asof), sort_keys=True)
        assert full == tr


def test_pit_signal_knowability_boundary():
    panel = load_fixture("f1", "f1_panel_core.json")
    cal = panel["calendar"]
    s0 = AD.signal(panel, cal, "2023-06-14", "2023-06-14T13:00:00-05:00")
    assert s0["event"] and not s0["knowable"]        # anchor bar not yet closed
    s1 = AD.signal(panel, cal, "2023-06-14", "2023-06-14T13:01:00-05:00")
    assert s1["knowable"] and s1["tail"] == "UP"
    non = AD.signal(panel, cal, "2023-06-15", None)
    assert not non["event"] and non["no_trade_reason"] == "NOT_EVENT_MEMBER"


# ------------------------------------------------------------- decision gates
def test_p5nq1_real_provenance_refused():
    panel = load_fixture("f1", "f1_panel_core.json")
    bad = {**panel, "provenance": "cache_v3"}
    with pytest.raises(nc.RefusedPendingOwnerDecision) as ei:
        AD.build_observables(bad, panel["calendar"])
    assert ei.value.slot_id == "P5-NQ1"


def test_p5nq2_option_binding_refused():
    for opt in ("NQ-A", "NQ-B", "NQ-C"):
        with pytest.raises(nc.RefusedPendingOwnerDecision) as ei:
            nc.bind_option(opt)
        assert ei.value.slot_id == "P5-NQ2"


def test_nqd_expwitch_dead_at_gate():
    from expwitch_refusal import ExpwitchDeadAtGate
    with pytest.raises(ExpwitchDeadAtGate) as ei:
        nc.bind_option("NQ-D")
    assert ei.value.code == "EXPWITCH_DEAD_AT_GATE"


def test_p5nq3_variant_b_cost_refused_default_a():
    a = nc.cost_per_side_usd("S2")            # default while D3 unsigned
    assert a["variant"] == "A" and a["cost_per_side_usd"] == 28.50
    assert a["cost_rt_usd"] == 57.00
    assert a["labels"] == ["MODELED COST", "UNDER REVIEW", "VERIFIED_VS_ACCOUNT=NOT_RUN"]
    with pytest.raises(nc.RefusedPendingOwnerDecision) as ei:
        nc.cost_per_side_usd("S2", variant="B")
    assert ei.value.slot_id == "P5-NQ3"


def test_p5nq4_tick_defect_refused(tmp_path):
    import pathlib
    src = pathlib.Path(nc.load_nq_contract()["source"])
    data = json.loads(src.read_text())
    data["contracts"]["NQ"]["tick_value_usd"] = 2.5
    bad = tmp_path / "bad_contracts.json"
    bad.write_text(json.dumps(data))
    with pytest.raises(nc.PanelError):
        nc.load_nq_contract(bad)


def test_p5nq6_2026_bypass_refused():
    with pytest.raises(nc.RefusedPendingOwnerDecision) as ei:
        nc.unexclude_2026("2026-01-19")
    assert ei.value.slot_id == "P5-NQ6"


# ------------------------------------------------- construction refuses / misc
def test_session_mask_mismatch_refused():
    panel = load_fixture("f1", "f1_panel_core.json")
    bad = copy.deepcopy(panel)
    for s in bad["sessions"]:
        if s["session_date"] == "2023-06-14":
            s["last_bar_ct"] = "15:58"        # disagrees with the bars
    with pytest.raises(nc.RefusedSessionMaskMismatch):
        AD.order_intent(bad, bad["calendar"], "FBNQ1-F1-CONT-UP-D0-S2", "2023-06-14")


def test_warmup_insufficient_no_trade():
    panel = load_fixture("f1", "f1_panel_core.json")
    thin = {**panel, "sessions": [s for s in panel["sessions"]
                                  if s["session_date"] < "2023-06-14"][-3:]}
    it = AD.order_intent(thin, panel["calendar"], "FBNQ1-F1-CONT-UP-D0-S2", "2023-06-14")
    assert it["no_trade"] and it["no_trade_reason"] == "ATR_WARMUP_INSUFFICIENT"


def test_determinism_two_calls_identical():
    panel = load_fixture("f1", "f1_panel_core.json")
    a = json.dumps(AD.order_intent(panel, panel["calendar"], "FBNQ1-F1-CONT-UP-D0-S2",
                                   "2023-06-14"), sort_keys=True)
    b = json.dumps(AD.order_intent(panel, panel["calendar"], "FBNQ1-F1-CONT-UP-D0-S2",
                                   "2023-06-14"), sort_keys=True)
    assert a == b


def test_fold_warmup_and_kviews():
    assert nc.fold_for_date("2011-06-01") == "F1"
    assert nc.fold_for_date("2016-06-01") == "F2"
    assert nc.fold_for_date("2020-06-01") == "F3"
    assert nc.fold_for_date("2024-06-03") == "F4"
    assert nc.fold_for_date("2026-10-01") is None   # partial tail excluded by law
    assert nc.WARMUP_HELD_SESSIONS == 252
    sessions = [f"2020-{m:02d}-{d:02d}" for m, d in
                [(1, 2), (1, 3), (1, 4), (1, 5)]]
    assert nc.scoreable_sessions(sessions, "F3", warmup=2) == sessions[2:]
    kv = nc.k_views("2023-06-14")
    assert kv["K-V1"] == "B" and kv["K-V2"] == "2022-26" and kv["K-V3"] == "2023-26"
    assert nc.k_views("2015-09-17")["K-V1"] == "A"
    assert nc.k_views("2020-03-19")["K-V4_covid_window"] is True
    assert nc.k_views("2019-05-05")["K-V5_alias_region"] is True
    assert nc.k_views("2016-06-14")["K-V6_reg_window"] is True


def test_cost_stress_ladder_matches_contract():
    assert nc.cost_per_side_usd("S1", 1.0)["cost_rt_usd"] == 47.00
    assert nc.cost_per_side_usd("S2", 1.5)["cost_rt_usd"] == 85.50
    assert nc.cost_per_side_usd("S3", 2.0)["cost_rt_usd"] == 134.00
