"""M0 test — gated plugin suppression semantics (offline, no engine data)."""
import importlib
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

gated_plugin = importlib.import_module("gated_plugin")


def test_gate_off_returns_engine_native_skip():
    p = gated_plugin.IlliqRegGatedPlugin.__new__(
        gated_plugin.IlliqRegGatedPlugin)
    p._gate_by_stamp_ns = {1: False}
    res = p.targets_at(1, universe=(), stress=MagicMock())
    assert res["status"] == "SKIP_NO_SELECTION"
    assert res["weights"] == {}
    assert res["reason_code"] == "GATE_OFF"


def test_gate_on_delegates(monkeypatch):
    p = gated_plugin.IlliqRegGatedPlugin.__new__(
        gated_plugin.IlliqRegGatedPlugin)
    p._gate_by_stamp_ns = {1: True}
    sentinel = {"status": "OK", "weights": {"X": 1.0}}
    monkeypatch.setattr(gated_plugin.Chr3fIlliqPlugin, "targets_at",
                        lambda self, ns, *, universe, stress: sentinel)
    assert p.targets_at(1, universe=(), stress=MagicMock()) is sentinel


def test_missing_stamp_fails_closed():
    p = gated_plugin.IlliqRegGatedPlugin.__new__(
        gated_plugin.IlliqRegGatedPlugin)
    import wiring
    p.schedule = lambda: MagicMock(instants=[1, 2])
    try:
        p.bind_gate({1: True})
    except wiring.WiringError:
        return
    raise AssertionError("expected WiringError for missing stamp")


def test_gate_counts():
    p = gated_plugin.IlliqRegGatedPlugin.__new__(
        gated_plugin.IlliqRegGatedPlugin)
    p._gate_by_stamp_ns = {1: True, 2: False, 3: False}
    assert p.gate_counts() == {"stamps": 3, "gate_on": 1, "gate_off": 2}
