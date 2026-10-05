"""T2 adapter tests — fake keys only; fail-closed behavior; no secret ever
echoed. Run: pytest lanes/T2_BDL_ADAPTER/test_bdl_adapter.py -q"""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))
from bdl_adapter import (  # noqa: E402
    BDLClient, BDLKeyUnavailable, ENV_VAR, _from_env, load_key,
)

FAKE = "fake-key-for-tests-only-0000000000"


def test_fail_closed_when_no_key(monkeypatch):
    monkeypatch.delenv(ENV_VAR, raising=False)
    monkeypatch.setattr("bdl_adapter._from_keychain", lambda: None)
    with pytest.raises(BDLKeyUnavailable) as ei:
        load_key()
    msg = str(ei.value)
    assert "fail" in msg.lower() and ENV_VAR in msg
    assert FAKE not in msg


def test_env_source(monkeypatch):
    monkeypatch.setenv(ENV_VAR, FAKE)
    assert _from_env() == FAKE
    c = BDLClient(base_url="https://unit.test")
    assert c.key_loaded


def test_keychain_source(monkeypatch):
    monkeypatch.delenv(ENV_VAR, raising=False)
    monkeypatch.setattr("bdl_adapter._from_keychain", lambda: FAKE)
    c = BDLClient(base_url="https://unit.test")
    assert c.key_loaded


def test_error_never_leaks_key(monkeypatch):
    monkeypatch.setenv(ENV_VAR, FAKE)
    c = BDLClient(base_url="https://unit.test")  # no network: force error path
    try:
        c._get("/games")
        raised = None
    except Exception as e:  # noqa: BLE001
        raised = str(e)
    assert raised is not None
    assert FAKE not in raised and "Authorization" not in raised


def test_no_key_in_repr_or_module_defaults():
    import bdl_adapter as m
    src = open(m.__file__).read()
    assert "abd6" not in src                    # no fragment of any real key
    assert "fake-key-for-tests-only" not in src  # fake constant lives ONLY in tests
    c = BDLClient.__new__(BDLClient)
    c._key = FAKE
    assert FAKE not in repr(c)
