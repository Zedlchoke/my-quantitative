"""test_adapter_af4 — pytest proofs for the AF4 overlay machinery (synthetic).

Run: /Users/hoangminhlong/my-quantitative/.venv/bin/python -m pytest af4_tick_regime -q
Exit code recorded in dispatch/handoff_ADAPT-FXJA.json.
"""
from __future__ import annotations

import pytest

import fx_common as fc
from conftest import load_fixture
from af4_tick_regime.adapter import (AF4Adapter, DRAFT_IDS, af4_freeze_check)

AD = AF4Adapter()
P6A = load_fixture("af4_tick_regime", "af4_panel_6a.json")
P6J = load_fixture("af4_tick_regime", "af4_panel_6j.json")


def test_zero_standalone_identities():
    """The frozen table carries AF4_tick_regime_overlay = 0; NO C6A0 skeletons
    are minted for AF4 at all."""
    assert DRAFT_IDS == [] and callable(af4_freeze_check)
    assert fc.frozen_6a_table_citation()["identities_by_category"][
        "AF4_tick_regime_overlay"] == 0


def test_era_labels_measured_boundary():
    assert AD.era_label("2020-11-20") == "era1"
    assert AD.era_label("2020-11-23") == "era2"
    split = AD.host_split(["2020-06-02", "2024-05-06", "2020-11-20", "2020-11-23"])
    assert split["era1_descriptive_only"]["days"] == ["2020-06-02", "2020-11-20"]
    assert split["era2"]["days"] == ["2020-11-23", "2024-05-06"]
    assert split["era1_descriptive_only"]["fold_floor"]["passes"] is False


def test_era1_descriptive_only_forever_law():
    """K3 pre-declared: the era-1 stratum (231 measured sessions; ~11 era-1
    host events) never scores — fold floor fails."""
    assert fc.fold_floor_check(11, 4)["passes"] is False   # ~11 era-1 host events
    split = AD.host_split(["2020-06-02"] * 11)
    assert split["era1_descriptive_only"]["fold_floor"]["passes"] is False


def test_step_test_sixA_halves_sixJ_constant():
    """The K2 substrate: 6A USD step x0.50 (ticks x1.00); same-date 6J x1.00 /
    x1.00 — the constant-tick control holds on the fixture."""
    ctl = AD.same_date_control(P6A, P6J)
    assert ctl["sixA_usd_step_ratio_era2_over_era1"] == 0.5
    assert ctl["sixA_ticks_step_ratio"] == 1.0
    assert ctl["sixJ_usd_step_ratio_era2_over_era1"] == 1.0
    assert ctl["sixJ_ticks_step_ratio"] == 1.0
    s1 = AD.micro_step_stats(P6A, "2020-06-02")
    s2 = AD.micro_step_stats(P6A, "2024-05-06")
    assert s1["median_usd_step"] == 1e-04 and s1["tick_value_usd"] == 10.0
    assert s2["median_usd_step"] == 5e-05 and s2["tick_value_usd"] == 5.0


def test_no_entry_ever_defined_from_tick_era():
    with pytest.raises(fc.RefusedAf4NoStandaloneIntent) as ei:
        AD.order_intent(P6A, {}, "AF4-ERA2-CONDITIONED-ARM", "2024-05-06")
    assert ei.value.code == "REFUSED_AF4_NO_ENTRY_FROM_TICK_ERA"


def test_real_data_refusal_still_binds_first():
    real = {**P6A, "provenance": "REAL_CHAIN"}
    with pytest.raises(fc.RefusedPendingOwnerDecision) as ei:
        AD.order_intent(real, {}, "AF4-ARM", "2024-05-06")
    assert ei.value.slot_id == "P5-FXJA-D5"
    with pytest.raises(fc.RefusedPendingOwnerDecision):
        af4_freeze_check()
    assert all(v is None for v in fc.GUARDS.values())
