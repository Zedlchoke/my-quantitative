"""RMM tests — Role-A machinery (mode split, switch-session exclusion law),
Role-B refusal (P5-FXEB-OD5 + interaction NOT_RUN), PB2 refusal."""
import copy

import fx_common
from fx_common import RefusedPendingOwnerDecision
from conftest import load_fixture
from rmm_roll_migration import adapter as rmm

import pytest


@pytest.fixture(scope="module")
def ctx():
    panels = {sym: load_fixture("rmm_roll_migration", f"panel_{sym}.json")
              for sym in ("6E", "6B")}
    tables = {sym: load_fixture("rmm_roll_migration",
                                f"switch_table_{sym}.json")["switches"]
              for sym in ("6E", "6B")}
    expected = load_fixture("rmm_roll_migration", "EXPECTED_MANIFEST.json")["expected"]
    return panels, tables, expected


@pytest.mark.parametrize("sym", ["6E", "6B"])
def test_role_a_ledger_machinery(ctx, sym):
    panels, tables, expected = ctx
    obs = rmm.build_observables(panels[sym], panels[sym]["calendar"], sym,
                                tables[sym])
    assert obs["kind"] == "ROLE_A_CONSTRUCTION_LEDGER"
    assert obs["standalone_identities"] == 0
    assert obs["cited_mode_ledger"] == expected["cited_ledger"][sym]
    assert obs["measured_switches"] == 27
    assert obs["fixture_mode_split"] == expected["fixture_mode_split"]
    # strict-past DC s.1.3 timing law carried
    assert "close t, effective t+1" in obs["timing_law"]


def test_switch_session_exclusion_law(ctx):
    panels, tables, expected = ctx
    obs6e = rmm.build_observables(panels["6E"], panels["6E"]["calendar"], "6E",
                                  tables["6E"])
    assert "EVENT_STACKING_EXCLUDED" in \
        obs6e["switch_flags"][expected["event_stacking_excluded_date"]]
    obs6b = rmm.build_observables(panels["6B"], panels["6B"]["calendar"], "6B",
                                  tables["6B"])
    assert "HOLIDAY_ADJACENT_SWITCH_EXCLUDED_6B" in \
        obs6b["switch_flags"][expected["holiday_adjacent_excluded_date_6B"]]


@pytest.mark.parametrize("sym,rb", [("6E", "RB1"), ("6E", "RB4"),
                                    ("6B", "RB2"), ("6B", "RB3")])
def test_role_b_identity_mint_refusal(ctx, sym, rb):
    with pytest.raises(RefusedPendingOwnerDecision) as ei:
        rmm.request_rmm_role_b_identity(sym, rb)
    assert ei.value.slot_id == "P5-FXEB-OD5"
    assert "DC s.1.3" in ei.value.detail
    assert "NOT_RUN" in ei.value.detail


@pytest.mark.parametrize("sym", ["6E", "6B"])
def test_no_own_signal_role_a_construction_only(ctx, sym):
    panels, tables, _ = ctx
    obs = rmm.build_observables(panels[sym], panels[sym]["calendar"], sym,
                                tables[sym])
    sig = rmm.signal(obs, "2026-03-09", {}, sym, panels[sym]["calendar"],
                     panels[sym])
    assert sig["status"] == "NO_TRADE"
    assert sig["blocking"] == ["ROLE_A_CONSTRUCTION_ONLY"]
    assert sig["identity_draft_ids"] == [f"FXRMM-{sym}-RB{k}" for k in (1, 2, 3, 4)]
    assert any("P5-FXEB-OD1" in b for b in sig["role_b_blockers"])


def test_pb2_refusal_real_data_path(ctx):
    panels, tables, _ = ctx
    panel = copy.deepcopy(panels["6E"])
    panel["provenance"] = "REAL_6E_CACHE"
    with pytest.raises(RefusedPendingOwnerDecision) as ei:
        rmm.build_observables(panel, panel["calendar"], "6E", tables["6E"])
    assert ei.value.slot_id == "P5-FXEB-OD1"
