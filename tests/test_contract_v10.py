"""V10 canonical contract authority tests (A5, H07).

Regression coverage for the three V9 A7 audit gaps plus the H07 runner
rules: direction REQUIRED, purge/embargo invariant, cost floor, family
allowlist (archived/unfrozen rejected even though code supports them) and
the honest multiple-testing denominator (idempotent add, decrement refused,
byte-deterministic append-only replay across two temp roots).

Synthetic fixtures only — no scored backtests, no results/ writes.
"""

from __future__ import annotations

import json

import pytest

from research.contract_v10 import (
    ADVERSE_TICKS_SLIPPAGE_FLOOR_V10,
    BASE_DENOMINATOR_V10,
    BAR_CLOCK_V10,
    CANONICAL_CONTRACT_V10,
    CAPS_V10,
    ContractViolation,
    DIRECTION_VALUES_V10,
    FILL_CLOCK_V10,
    FUNDING_SETTLEMENT_V10,
    PF_DEFINITION_V10,
    STRESS_MATRIX_V10,
    TAKER_FEE_FLOOR_BPS_V10,
    FamilyAllowlist,
    MultipleTestingDenominator,
    TrialRegistry,
    contract_dict,
    resolve_s0_window,
    validate_trial_spec,
)

SPEC_HASH_A = "aa" * 32
SPEC_HASH_B = "bb" * 32
FAMILY_ID = "FAM-V10-TEST"


def make_folds():
    return [
        {
            "fold_id": "F1",
            "start_utc": "2025-01-02T00:00:00+00:00",
            "end_utc": "2025-02-15T00:00:00+00:00",
        },
        {
            "fold_id": "F2",
            "start_utc": "2025-02-15T00:00:00+00:00",
            "end_utc": "2025-03-28T00:00:00+00:00",
        },
        {
            "fold_id": "F3",
            "start_utc": "2025-03-28T00:00:00+00:00",
            "end_utc": "2025-05-10T00:00:00+00:00",
        },
        {
            "fold_id": "F4",
            "start_utc": "2025-05-10T00:00:00+00:00",
            "end_utc": "2025-06-21T00:00:00+00:00",
        },
    ]


def make_costs(**over):
    costs = {
        "taker_fee_bps": 5.0,
        "adverse_ticks_slippage": 1,
        "funding": FUNDING_SETTLEMENT_V10,
    }
    costs.update(over)
    return costs


def make_spec(**over):
    spec = {
        "trial_id": "TRIAL-V10-001",
        "family_id": FAMILY_ID,
        "direction": "LONG",
        "window_start": "2025-01-01T00:00:00+00:00",
        "window_end": "2025-07-01T00:00:00+00:00",
        "bar_clock": BAR_CLOCK_V10,
        "fill_clock": FILL_CLOCK_V10,
        "warmup_bars": 96,
        "holding_horizon_bars": 8,
        "purge_periods": 8,
        "embargo_periods": 12,
        "costs": make_costs(),
        "folds": make_folds(),
    }
    spec.update(over)
    return spec


@pytest.fixture()
def frozen_allowlist():
    allowlist = FamilyAllowlist()
    allowlist.register_family(FAMILY_ID, SPEC_HASH_A, role="candidate")
    return allowlist


# --------------------------------------------------------------------------- #
# Frozen authority shape
# --------------------------------------------------------------------------- #
def test_canonical_contract_pins_h07_vocabulary():
    contract = CANONICAL_CONTRACT_V10
    assert contract.bar_clock == "completed_15m_bars_only"
    assert contract.fill_clock == "next_allowed_event_after_signal_bar_close"
    assert contract.direction_required == ("LONG", "SHORT", "BOTH_WITH_SIGN_SEMANTICS")
    assert contract.baseline_costs["taker_fee_bps"] == 5.0
    assert contract.baseline_costs["adverse_ticks_slippage"] == 1
    assert contract.baseline_costs["funding"] == "native_intrarun_settlement"
    assert STRESS_MATRIX_V10 == (
        "fee_slippage_x1_5",
        "plus_2_ticks",
        "plus_1_event_delay",
        "drop_one_symbol",
        "drop_one_fold",
    )
    assert CAPS_V10 == {
        "max_symbol_positive_pnl_share": 0.40,
        "max_fold_positive_contribution": 0.50,
    }
    assert "position_level_profit_factor" in PF_DEFINITION_V10
    assert contract.folds["min_folds"] >= 3
    assert contract.benchmarks["flat_hard"]["mandatory"] is True
    assert contract.benchmarks["buy_and_hold"]["role"] == "context_only"
    assert contract.benchmarks["btc_beta_neutral"]["role"] == "context_only"
    assert contract.base_denominator == BASE_DENOMINATOR_V10 == 117


def test_canonical_contract_is_frozen_dataclass():
    with pytest.raises(Exception):
        CANONICAL_CONTRACT_V10.bar_clock = "mutated"
    payload = contract_dict()
    assert payload["contract_sha256"]
    repayload = contract_dict()
    assert json.dumps(repayload, sort_keys=True) == json.dumps(payload, sort_keys=True)


def test_s0_window_parameterized_fail_closed():
    resolved = resolve_s0_window(
        "2025-01-01T00:00:00+00:00", "2025-07-01T00:00:00+00:00"
    )
    assert resolved["days"] == pytest.approx(181.0)
    assert CANONICAL_CONTRACT_V10.s0_window_start_utc is None
    assert CANONICAL_CONTRACT_V10.s0_window_end_utc is None
    with pytest.raises(ContractViolation):
        resolve_s0_window("not-a-date", "2025-07-01T00:00:00+00:00")
    with pytest.raises(ContractViolation):
        resolve_s0_window(
            "2025-07-01T00:00:00+00:00", "2025-01-01T00:00:00+00:00"
        )


# --------------------------------------------------------------------------- #
# V9 gap (a): direction REQUIRED
# --------------------------------------------------------------------------- #
def test_direction_missing_rejected_v9_gap_regression(frozen_allowlist):
    spec = make_spec()
    del spec["direction"]
    violations = validate_trial_spec(spec, allowlist=frozen_allowlist)
    assert any(
        v.startswith("missing_required_field:direction") for v in violations
    ), violations


def test_direction_present_accepted(frozen_allowlist):
    assert validate_trial_spec(make_spec(), allowlist=frozen_allowlist) == []


def test_direction_must_be_known_enum(frozen_allowlist):
    violations = validate_trial_spec(
        make_spec(direction="LONG_ONLY_SILENT"), allowlist=frozen_allowlist
    )
    assert any(v.startswith("direction_must_be_one_of:") for v in violations)


# --------------------------------------------------------------------------- #
# Purge/embargo invariant at spec time
# --------------------------------------------------------------------------- #
def test_purge_and_embargo_below_holding_horizon_rejected(frozen_allowlist):
    violations = validate_trial_spec(
        make_spec(purge_periods=4, embargo_periods=2),
        allowlist=frozen_allowlist,
    )
    assert any(v.startswith("purge_periods_below_holding_horizon:4<8") for v in violations)
    assert any(v.startswith("embargo_periods_below_holding_horizon:2<8") for v in violations)
    ok = validate_trial_spec(
        make_spec(purge_periods=8, embargo_periods=8), allowlist=frozen_allowlist
    )
    assert ok == []


# --------------------------------------------------------------------------- #
# Family allowlist: archived/unfrozen rejected even though code supports them
# --------------------------------------------------------------------------- #
def test_unknown_family_rejected():
    allowlist = FamilyAllowlist()
    assert len(allowlist.families()) == 0
    with pytest.raises(ContractViolation):
        allowlist.validate_family("NEVER-REGISTERED")


def test_register_then_archive_then_validate_raises():
    allowlist = FamilyAllowlist()
    allowlist.register_family(FAMILY_ID, SPEC_HASH_A, role="candidate")
    allowlist.validate_family(FAMILY_ID)
    allowlist.archive_family(FAMILY_ID)
    with pytest.raises(ContractViolation) as excinfo:
        allowlist.validate_family(FAMILY_ID)
    assert "archived" in str(excinfo.value)


def test_registered_archived_status_rejected_directly():
    allowlist = FamilyAllowlist()
    allowlist.register_family(FAMILY_ID, SPEC_HASH_B, role="negative_control",
                              status="archived")
    with pytest.raises(ContractViolation):
        allowlist.validate_family(FAMILY_ID)
    violations = validate_trial_spec(
        make_spec(), allowlist=allowlist
    )
    assert any(v.startswith("unknown_or_unfrozen_family:") for v in violations)


def test_registration_immutability():
    allowlist = FamilyAllowlist()
    allowlist.register_family(FAMILY_ID, SPEC_HASH_A, role="candidate")
    with pytest.raises(ContractViolation):
        allowlist.register_family(FAMILY_ID, SPEC_HASH_B, role="candidate")
    with pytest.raises(ContractViolation):
        allowlist.register_family(FAMILY_ID, SPEC_HASH_A, role="rescue")
    with pytest.raises(ContractViolation):
        allowlist.register_family(FAMILY_ID, "short-hash", role="candidate")


def test_allowlist_round_trip_through_explicit_tmp_path(tmp_path):
    path = tmp_path / "registry" / "family_allowlist.json"
    allowlist = FamilyAllowlist()
    allowlist.register_family("FAM-A", SPEC_HASH_A, role="candidate")
    allowlist.register_family("FAM-N", SPEC_HASH_B, role="negative_control")
    allowlist.archive_family("FAM-N")
    assert allowlist.save(path) == path
    loaded = FamilyAllowlist.load(path)
    assert loaded.families() == allowlist.families()
    loaded.validate_family("FAM-A")
    with pytest.raises(ContractViolation):
        loaded.validate_family("FAM-N")
    with pytest.raises(ContractViolation):
        FamilyAllowlist.load(tmp_path / "missing.json")


# --------------------------------------------------------------------------- #
# Freeze -> validate passes; clocks/warmup/fold layout enforced
# --------------------------------------------------------------------------- #
def test_freeze_then_validate_full_spec_passes(frozen_allowlist):
    registry = TrialRegistry()
    spec = make_spec(trial_id="TRIAL-V10-002")
    assert validate_trial_spec(
        spec, allowlist=frozen_allowlist, trial_registry=registry
    ) == []
    registry.register("TRIAL-V10-002", spec)
    dup = validate_trial_spec(
        spec, allowlist=frozen_allowlist, trial_registry=registry
    )
    assert any(v.startswith("duplicate_trial_id:TRIAL-V10-002") for v in dup)
    with pytest.raises(ContractViolation):
        registry.register("TRIAL-V10-002", spec)


def test_drifted_clocks_and_warmup_inside_oos_rejected(frozen_allowlist):
    drifted = validate_trial_spec(
        make_spec(bar_clock="incomplete_bars", fill_clock="same_bar_fill"),
        allowlist=frozen_allowlist,
    )
    assert any("bar_clock_must_equal:" in v for v in drifted)
    assert any("fill_clock_must_equal:" in v for v in drifted)

    early_warmup = validate_trial_spec(
        make_spec(warmup_bars=20000), allowlist=frozen_allowlist
    )
    assert any(v.startswith("folds.warmup_inside_scored_oos:") for v in early_warmup)

    missing_field = validate_trial_spec({k: v for k, v in make_spec().items() if k != "costs"})
    assert "missing_required_field:costs" in missing_field
    unexpected = validate_trial_spec(make_spec(rescue_param=1))
    assert "unexpected_field:rescue_param" in unexpected
    ragged_folds = validate_trial_spec(
        make_spec(folds=make_folds()[:2]), allowlist=frozen_allowlist
    )
    assert any(v.startswith("folds.insufficient_folds:2<3") for v in ragged_folds)


# --------------------------------------------------------------------------- #
# Cost floor enforcement
# --------------------------------------------------------------------------- #
def test_cost_floor_enforcement(frozen_allowlist):
    looser = validate_trial_spec(
        make_spec(costs=make_costs(taker_fee_bps=4.0)), allowlist=frozen_allowlist
    )
    assert any(
        v.startswith("costs.taker_fee_bps_below_baseline_floor:4.0<>5.0")
        for v in looser
    )

    documented = validate_trial_spec(
        make_spec(
            costs={
                **make_costs(taker_fee_bps=4.0),
                "stricter_frozen": {
                    "frozen_before_score": True,
                    "rationale": "pre-registered V8 basis replayed verbatim",
                },
            }
        ),
        allowlist=frozen_allowlist,
    )
    assert documented == []

    underdocumented = validate_trial_spec(
        make_spec(
            costs={
                **make_costs(taker_fee_bps=4.0),
                "stricter_frozen": {"rationale": ""},
            }
        ),
        allowlist=frozen_allowlist,
    )
    assert any(v.startswith("costs.cost_floor_exception_not_documented") for v in underdocumented)

    stricter = validate_trial_spec(
        make_spec(costs=make_costs(taker_fee_bps=6.0, adverse_ticks_slippage=2)),
        allowlist=frozen_allowlist,
    )
    assert stricter == []

    zero_slippage = validate_trial_spec(
        make_spec(costs=make_costs(adverse_ticks_slippage=0)),
        allowlist=frozen_allowlist,
    )
    assert any(
        v.startswith("costs.adverse_ticks_slippage_below_baseline_floor:0<>1")
        for v in zero_slippage
    )
    wrong_funding = validate_trial_spec(
        make_spec(costs=make_costs(funding="assumed_mark")),
        allowlist=frozen_allowlist,
    )
    assert any("costs.funding_must_equal:native_intrarun_settlement" in v for v in wrong_funding)
    assert TAKER_FEE_FLOOR_BPS_V10 == 5.0
    assert ADVERSE_TICKS_SLIPPAGE_FLOOR_V10 == 1


# --------------------------------------------------------------------------- #
# Honest multiple-testing denominator
# --------------------------------------------------------------------------- #
def test_denominator_add_idempotent_refuse_decrement(tmp_path):
    denom = MultipleTestingDenominator(base=117)
    assert denom.N == 117
    assert denom.add_scored_cell("V10-CELL-1") is True
    assert denom.add_scored_cell("V10-CELL-2") is True
    assert denom.N == 119
    assert denom.add_scored_cell("V10-CELL-1") is False
    assert denom.N == 119
    assert denom.cells() == ("V10-CELL-1", "V10-CELL-2")
    with pytest.raises(ContractViolation):
        denom.remove_scored_cell("V10-CELL-1")
    with pytest.raises(ContractViolation):
        denom.decrement()
    with pytest.raises(ContractViolation):
        MultipleTestingDenominator(base=0)
    with pytest.raises(ContractViolation):
        denom.add_scored_cell("")
    with pytest.raises(ContractViolation):
        MultipleTestingDenominator(base=True)


def test_denominator_ledger_replay_byte_deterministic_across_two_roots(tmp_path):
    root_a = tmp_path / "root_a"
    root_b = tmp_path / "root_b"
    ops_a = ["V10-CELL-A", "V10-CELL-B", "V10-CELL-C"]
    ops_b = ["V10-CELL-A", "V10-CELL-B", "V10-CELL-C"]

    ledger_a = root_a / "denominator.jsonl"
    ledger_b = root_b / "denominator.jsonl"
    denom_a = MultipleTestingDenominator(base=117, ledger_path=ledger_a)
    denom_b = MultipleTestingDenominator(base=117, ledger_path=ledger_b)
    for cell in ops_a:
        denom_a.add_scored_cell(cell)
    for cell in ops_b:
        denom_b.add_scored_cell(cell)
        denom_b.add_scored_cell(cell)
    assert denom_a.N == 120
    assert denom_b.N == 120
    assert ledger_a.read_bytes() == ledger_b.read_bytes()

    lines = ledger_a.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 3
    parsed = [json.loads(line) for line in lines]
    assert parsed[0]["trial_id"] == "V10-CELL-A"
    assert parsed[0]["action"] == "add_scored_cell"
    assert lines[0] == json.dumps(parsed[0], sort_keys=True, separators=(",", ":"))

    replay_a = MultipleTestingDenominator(base=117, ledger_path=ledger_a)
    replay_b = MultipleTestingDenominator(base=117, ledger_path=ledger_b)
    assert replay_a.N == 120
    assert replay_b.N == 120
    assert replay_a.cells() == denom_a.cells()
    assert replay_a.cells() == replay_b.cells()


def test_denominator_ledger_corruption_fails_closed(tmp_path):
    ledger = tmp_path / "denominator.jsonl"
    denom = MultipleTestingDenominator(base=117, ledger_path=ledger)
    denom.add_scored_cell("V10-CELL-X")
    with open(ledger, "a", encoding="utf-8") as handle:
        handle.write("{corrupt\n")
    with pytest.raises(ContractViolation):
        MultipleTestingDenominator(base=117, ledger_path=ledger)
    bad_action = tmp_path / "bad_action.jsonl"
    bad_action.write_text(
        json.dumps({"schema_version": "v10.denominator.v1",
                    "action": "remove_scored_cell", "trial_id": "X"}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ContractViolation):
        MultipleTestingDenominator(base=117, ledger_path=bad_action)
