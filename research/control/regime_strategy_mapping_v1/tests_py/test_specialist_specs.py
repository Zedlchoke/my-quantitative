"""SPEC-level tests for the A4 specialist library proposal.

Validates the STRUCTURE and LAWS of freezes/specialist_library_proposal.json
(schema rsmv1_specialist_library_proposal@1). No engine, no market data, no
outcomes: these are pure spec checks an implementer (and A1 at freeze time)
can run anywhere.
"""

from __future__ import annotations

import json
from pathlib import Path

CYCLE_DIR = Path(__file__).resolve().parents[1]
PROPOSAL_PATH = CYCLE_DIR / "freezes" / "specialist_library_proposal.json"

REGIMES = ["ACCUMULATION", "UPTREND", "DISTRIBUTION", "DOWNTREND"]
MACHINE_MIN_DWELL_REGIME_BARS = 6
MIN_HOLDING_FLOOR_REGIME_BARS = 6
VALID_ASSETS = {"BTCUSDT", "SPY"}
LONG_ONLY_ASSETS = {"SPY"}
TREND_UP_REGIMES = {"ACCUMULATION", "UPTREND"}
TREND_DOWN_REGIMES = {"DISTRIBUTION", "DOWNTREND"}

REQUIRED_SPECIALIST_FIELDS = [
    "id",
    "regime",
    "direction",
    "assets",
    "economic_mechanism",
    "entry",
    "exits",
    "sizing",
    "stop",
    "maximum_holding",
    "minimum_holding_regime_bars",
    "transition_delay_regime_bars",
    "next_bar_execution_ack",
    "noop_target_behavior",
    "costs_funding_ack",
    "expected_failure_mode",
    "required_tests",
]


def _load() -> dict:
    with open(PROPOSAL_PATH, encoding="utf-8") as fh:
        return json.load(fh)


def _all_specialists(lib: dict) -> list[dict]:
    out = []
    for regime_name, block in lib["regimes"].items():
        for spec in block["specialists"]:
            out.append((regime_name, spec))
    return out


# --------------------------------------------------------------------------
# identity and knowledge boundary
# --------------------------------------------------------------------------


def test_schema_and_identity():
    lib = _load()
    assert lib["schema"] == "rsmv1_specialist_library_proposal@1"
    assert lib["cycle_id"] == "REGIME-STRATEGY-MAPPING-V1"
    assert lib["role"] == "A4"
    assert lib["lane"] == "a4-specialists"
    assert lib["status"].startswith("PROPOSAL")
    assert lib["knowledge_boundary"]["outcome_blind"] is True
    not_read = lib["knowledge_boundary"]["not_read"]
    assert any("evidence/" in item for item in not_read)
    assert any("runtime/" in item for item in not_read)
    assert any("attribution.py" in item for item in not_read)


def test_execution_law_constants():
    lib = _load()
    law = lib["execution_law"]
    assert law["one_position_per_asset"] is True
    assert law["notional_fraction"] == 1.0
    assert law["regime_machine"]["min_dwell_regime_bars"] == (
        MACHINE_MIN_DWELL_REGIME_BARS
    )
    assert "next exec bar open" in law["fill"].lower()
    assert "no close/reopen" in law["anti_churn_law"]
    assert law["exit_precedence"].startswith("fold force-flat > price stop")
    assert lib["assets"]["BTCUSDT"]["funding"]["cadence_exec_bars_15m_clock"] == 32


def test_asset_contract():
    lib = _load()
    assert set(lib["assets"]) == VALID_ASSETS
    btc = lib["assets"]["BTCUSDT"]
    spy = lib["assets"]["SPY"]
    assert set(btc["authority"]) == {"LONG", "SHORT"}
    assert set(spy["authority"]) == {"LONG"}
    assert btc["costs"]["round_trip_bps"] == 12.0
    assert btc["funding"]["rate_per_8h_signed"] == 1.377e-05
    assert "LONG pays" in btc["funding"]["sign_convention"]
    assert spy["costs"]["cost_bps_per_fill"] == 10.0


# --------------------------------------------------------------------------
# bounded library
# --------------------------------------------------------------------------


def test_regimes_complete_and_bounded():
    lib = _load()
    assert list(lib["regimes"].keys()) == REGIMES
    for regime_name, block in lib["regimes"].items():
        n = len(block["specialists"])
        assert 1 <= n <= 2, f"{regime_name} has {n} specialists (bound is 2)"
        assert block["definition_basis"]


def test_transition_unknown_fixed_flat():
    lib = _load()
    policy = lib["transition_unknown_policy"]
    assert policy["fixed_target"] == "FLAT"
    assert policy["selectable_in_library"] is False
    assert "TRANSITION_UNKNOWN" not in lib["regimes"]
    for _, spec in _all_specialists(lib):
        assert spec["regime"] in REGIMES
        assert "UNK" not in spec["id"]


def test_specialist_ids_unique():
    lib = _load()
    ids = [spec["id"] for _, spec in _all_specialists(lib)]
    assert len(ids) == len(set(ids))


# --------------------------------------------------------------------------
# per-specialist field completeness
# --------------------------------------------------------------------------


def test_specialist_required_fields_present():
    lib = _load()
    for _, spec in _all_specialists(lib):
        for field in REQUIRED_SPECIALIST_FIELDS:
            assert field in spec, f"{spec.get('id')} missing {field}"
        assert isinstance(spec["economic_mechanism"], str)
        assert len(spec["economic_mechanism"].split()) >= 30
        assert spec["noop_target_behavior"]
        assert spec["costs_funding_ack"]
        assert spec["expected_failure_mode"]
        assert isinstance(spec["required_tests"], list)
        assert len(spec["required_tests"]) >= 3


def test_entry_wellformed():
    lib = _load()
    for _, spec in _all_specialists(lib):
        entry = spec["entry"]
        assert entry["clock"].startswith("exec")
        assert entry["side"] == spec["direction"]
        assert entry["condition"]
        assert entry["indicators"]
        for ind in entry["indicators"]:
            assert ind["name"]
            assert isinstance(ind["params"], dict) and ind["params"]


def test_exits_and_stop_declared():
    lib = _load()
    for _, spec in _all_specialists(lib):
        assert isinstance(spec["exits"], list) and len(spec["exits"]) >= 3
        names = {rule["name"] for rule in spec["exits"]}
        assert "fold_force_flat" in names
        assert any("stop" in name for name in names)
        stop = spec["stop"]
        assert stop["type"].startswith("price")
        assert stop["rule"]
        assert isinstance(stop["params"], dict) and stop["params"]
        sizing = spec["sizing"]
        assert sizing["notional_fraction"] == 1.0


def test_holding_and_transition_declared():
    lib = _load()
    for _, spec in _all_specialists(lib):
        min_hold = spec["minimum_holding_regime_bars"]
        assert isinstance(min_hold, int)
        assert min_hold >= MIN_HOLDING_FLOOR_REGIME_BARS
        delay = spec["transition_delay_regime_bars"]
        assert isinstance(delay, int) and delay >= 0
        max_hold = spec["maximum_holding"]
        assert max_hold["kind"] in {"regime_bars", "fold_force_flat"}
        if max_hold["kind"] == "regime_bars":
            assert max_hold["value"] > min_hold
        assert spec["next_bar_execution_ack"] is True


# --------------------------------------------------------------------------
# direction and eligibility laws
# --------------------------------------------------------------------------


def test_direction_consistency():
    lib = _load()
    for _, spec in _all_specialists(lib):
        assert spec["direction"] in {"LONG", "SHORT"}
        if spec["direction"] == "LONG":
            assert spec["id"].endswith("-L")
        else:
            assert spec["id"].endswith("-S")
        assert spec["entry"]["side"] == spec["direction"]


def test_eligibility_law_spy_never_short():
    lib = _load()
    for _, spec in _all_specialists(lib):
        assets = set(spec["assets"])
        assert assets and assets <= VALID_ASSETS
        if assets & LONG_ONLY_ASSETS:
            assert spec["direction"] == "LONG", (
                f"{spec['id']}: SPY is long-only"
            )
        if spec["direction"] == "SHORT":
            assert assets == {"BTCUSDT"}, f"{spec['id']}: shorts are BTC-only"


def test_regime_direction_law_no_counter_trend():
    lib = _load()
    for regime_name, spec in _all_specialists(lib):
        if spec["direction"] == "LONG":
            assert regime_name in TREND_UP_REGIMES
        else:
            assert regime_name in TREND_DOWN_REGIMES


def test_btc_specialists_acknowledge_funding():
    lib = _load()
    for _, spec in _all_specialists(lib):
        if "BTCUSDT" in spec["assets"]:
            ack = spec["costs_funding_ack"].lower()
            assert "funding" in ack
            if spec["direction"] == "LONG":
                assert "pays" in ack
            else:
                assert "receives" in ack


# --------------------------------------------------------------------------
# bounded-library rationale
# --------------------------------------------------------------------------


def test_rejected_alternatives_recorded():
    lib = _load()
    rejected = lib["rejected_alternatives"]
    assert len(rejected) >= 5
    ids = {item["id"] for item in rejected}
    assert any("counter-trend" in item["reason"].lower() for item in rejected)
    assert any("grid" in item["reason"].lower() for item in rejected)
    assert "REJ-DNT-DIPBUY-L" in ids and "REJ-UPT-FADE-S" in ids


def test_baseline_expressibility_documented():
    lib = _load()
    assert "baseline_expressibility_note" in lib
    assert "FLAT" in lib["baseline_expressibility_note"]
    assert lib["notes_for_a1"]
