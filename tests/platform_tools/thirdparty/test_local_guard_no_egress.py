"""Permanent no-egress property for the vendored local_guard.

The vendored middleware must never open a network connection: neither at
import time nor while serving any request the guard itself handles (refusals
are produced in-process via starlette's JSONResponse). This test makes that a
permanent, enforced property by denying every outbound socket path and then
fresh-importing the module and driving the full behavioral matrix through it.
"""
import socket
import sys

import pytest

from tests.platform_tools.thirdparty import test_local_guard_fidelity as fid
from tests.platform_tools.thirdparty.test_local_guard_fidelity import (
    EVIL, LOCAL, local_guard, run_case, http_outcome)


def _deny(*args, **kwargs):
    raise AssertionError(f"egress attempted via socket: {args!r} {kwargs!r}")


@pytest.fixture(autouse=True)
def _real_allowlist(monkeypatch):
    monkeypatch.delenv("SCANNER_ALLOWED_HOSTS", raising=False)
    monkeypatch.setattr(local_guard, "_extra_hosts", set())


@pytest.fixture
def no_sockets(monkeypatch):
    """Deny every outbound connect path: socket.connect, connect_ex, create_connection."""
    monkeypatch.setattr(socket.socket, "connect", _deny, raising=False)
    monkeypatch.setattr(socket.socket, "connect_ex", _deny, raising=False)
    monkeypatch.setattr(socket, "create_connection", _deny, raising=False)


def test_no_egress_during_import(no_sockets):
    sys.modules.pop("local_guard", None)
    import local_guard as fresh  # noqa: F401  — import itself must not dial out
    assert fresh.LOOPBACK_HOSTS == {"localhost", "127.0.0.1", "::1"}


def test_no_egress_during_full_request_matrix(no_sockets):
    """Every guard branch — host refusal, origin refusal, content-type refusal,
    passthroughs (GET/POST/OPTIONS/WebSocket) — runs with sockets denied."""
    cases = [
        dict(method="POST", headers={"Origin": EVIL}),                              # 403 origin
        dict(method="POST", headers={"Content-Type": "text/plain"}),               # 415 ctype
        dict(method="GET", headers={"Host": "rebind.evil.example:7777"}),          # 400 host
        dict(method="POST", headers={"Origin": "http://127.0.0.1:7777",
                                     "Content-Type": "application/json"}),         # pass
        dict(method="GET", headers={}),                                            # pass
        dict(method="OPTIONS", headers={"Origin": "http://localhost:5174"}),       # pass
        dict(kind="websocket", headers={"Origin": EVIL}),                          # ws close
        dict(kind="websocket", headers={"Origin": "http://127.0.0.1:7777"}),       # ws pass
    ]
    for kwargs in cases:          # any socket use inside raises AssertionError
        app, events = run_case(**kwargs)
        assert app is not None
    # sanity: the denial is live (a real connect attempt would have raised above
    # before any assertion in this test could pass vacuously)
    with pytest.raises(AssertionError):
        socket.create_connection(("127.0.0.1", 1), timeout=0.01)


def test_comp_guard_module_has_no_network_imports(no_sockets):
    """Complementary static check: the vendored module imports no networking
    library (socket/http/urllib.request/requests) — only os, typing, urllib.parse,
    starlette.responses."""
    import importlib
    sys.modules.pop("local_guard", None)
    mod = importlib.import_module("local_guard")
    src_files = [getattr(mod, "__file__", "")]
    import pathlib
    text = pathlib.Path(src_files[0]).read_text()
    for banned in ("import socket", "import http", "import requests",
                   "import urllib.request", "from urllib.request"):
        assert banned not in text, f"vendored local_guard gained: {banned}"
