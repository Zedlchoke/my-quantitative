"""Adversarial no-order tests (plan G4).

- the real package scans clean (zero forbidden surfaces);
- a scratch module carrying forbidden surfaces FAILS CLOSED under the
  scanner;
- the only emitted action type is TARGET_INTENT; no order route can be
  constructed through the package.

NOTE: this test file intentionally contains forbidden literals; the
scanner only ever runs over research/shadow_v1/ and scratch dirs.
"""

import importlib
import pkgutil

import pytest

from research.shadow_v1 import no_order
from research.shadow_v1.events import (
    build_data_blocked_event,
    validate_event_record,
    EventContractError,
)
from research.shadow_v1.no_order import (
    NoOrderViolationError,
    emit_target_intent,
    forbidden_patterns,
)

PACKAGE_ROOT = "research/shadow_v1"


def test_real_package_scans_clean():
    report = no_order.assert_no_order_surface(PACKAGE_ROOT)
    assert report["verdict"] == "NO_ORDER_SURFACE_CLEAN"
    assert report["hits"] == 0
    assert report["files_scanned"] >= 8


def test_scratch_module_with_venue_sdk_fails_closed(tmp_path):
    bad = tmp_path / "rogue_adapter.py"
    bad.write_text(
        "import ccxt\n"
        "def route(intent):\n"
        "    client = ccxt.binance()\n"
        "    return client.create_order(intent['symbol'], 'market', 'buy', 1.0)\n",
        encoding="utf-8",
    )
    with pytest.raises(NoOrderViolationError) as excinfo:
        no_order.assert_no_order_surface(str(tmp_path))
    assert "sdk_cc_module" in str(excinfo.value)
    assert "order_verb_create" in str(excinfo.value)


def test_scratch_module_with_order_verbs_fails_closed(tmp_path):
    bad = tmp_path / "rogue_router.py"
    bad.write_text(
        "def place_order(symbol, qty):\n"
        "    return submit_order(symbol, qty)\n",
        encoding="utf-8",
    )
    with pytest.raises(NoOrderViolationError):
        no_order.assert_no_order_surface(str(tmp_path))


def test_scratch_module_with_credential_reads_fails_closed(tmp_path):
    bad = tmp_path / "rogue_creds.py"
    bad.write_text(
        "import os\n"
        "API_KEY = os.environ['FUTURES_TEST_KEY']\n"
        "API_SECRET = os.environ['FUTURES_TEST_SECRET']\n",
        encoding="utf-8",
    )
    with pytest.raises(NoOrderViolationError) as excinfo:
        no_order.assert_no_order_surface(str(tmp_path))
    assert "env_secret_read" in str(excinfo.value)


def test_package_exposes_no_order_route_attributes():
    import research.shadow_v1 as pkg

    order_verbs = ["create_order", "place_order", "submit_order", "cancel_order"]
    module_names = [info.name for info in pkgutil.iter_modules(pkg.__path__)]
    for name in module_names:
        module = importlib.import_module(f"research.shadow_v1.{name}")
        for verb in order_verbs:
            assert not hasattr(module, verb), f"{name}.{verb} exists"
        for attr in vars(module).values():
            if isinstance(attr, type):
                for verb in order_verbs:
                    assert not hasattr(attr, verb), f"{name}.{attr.__name__}.{verb}"


def test_emitted_action_type_is_target_intent_only():
    intent = emit_target_intent(
        cycle_id="PROSPECTIVE-SHADOW-V1",
        family_id="XSECT-FUND-CARRY-7D",
        arm_id="XSECT-FUND-CARRY-7D",
        event_id="0" * 32,
        generated_utc="2026-01-05T00:00:00Z",
        target_weights={"ETHUSDT": 0.1, "SOLUSDT": -0.1},
    )
    assert intent["action_type"] == "TARGET_INTENT"
    assert no_order.ALLOWED_ACTION_TYPES == ("TARGET_INTENT",)
    # intent record carries no executable venue fields
    for forbidden_key in ("route", "client_order_id", "endpoint", "credential"):
        assert forbidden_key not in intent


def test_event_contract_refuses_any_other_action_type():
    rec = build_data_blocked_event(
        family_id="F", arm_id="A",
        scheduled_decision_utc="2026-01-05T00:00:00Z",
        observed_at_utc="2026-01-05T00:00:00Z",
        feature_cutoff_utc="2026-01-05T00:00:00Z",
        code_freeze_sha="x", config_digest="y", cost_regime_digest="z",
        blocked_reason="late",
    )
    rec["no_order_proof"]["emitted_action_types"].append("PLACE_ORDER")
    with pytest.raises(EventContractError):
        validate_event_record(rec)


def test_scanner_rules_are_nonempty_and_assembled():
    rules = forbidden_patterns()
    assert len(rules) >= 15
    literals = [lit for _, lit in rules]
    assert len(set(literals)) == len(literals)
    # the assembled literals are the real forbidden strings, e.g.:
    assert "import binance" in literals
    assert "os.environ" in literals
