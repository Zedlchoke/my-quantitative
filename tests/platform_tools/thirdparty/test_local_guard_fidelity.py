"""Fidelity port of upstream edge-scanner tests/test_local_guard.py — local_guard scope only.

Upstream test file (pinned c927dcb0c5e8122269812d2cdfdc4a3ae71b2ab3) is coupled
to the full scanner app (scanner.api.create_app, scanner.api_v2 static-route
helpers). This port reproduces EVERY case that exercises scanner/local_guard.py
— the only file vendored by EDGE-SCANNER-TOOLING-V1 — against a minimal pure-
ASGI recorder app, preserving upstream case names, header matrices, and
expected outcomes. The harness drives the ASGI interface directly (hand-built
scopes), which is the same interface the middleware defines; no HTTP client or
scanner app code is involved.

Tests named `test_*` mirror an upstream case (see each docstring for the
upstream counterpart). Tests named `test_comp_*` are complementary code-derived
cases (behavior read straight from local_guard.py) that upstream exercised only
indirectly; they strengthen the port but claim no upstream lineage.

Out of scope by plan §0 non_goals: upstream static-route UNC tests
(_safe_static_path / mount_v2_static) — not part of the vendored surface.
"""
import asyncio
import json

import pytest

import local_guard

LOCAL = "http://127.0.0.1:7777"
EVIL = "https://evil.example"


@pytest.fixture(autouse=True)
def _real_allowlist(monkeypatch):
    """Upstream _real_allowlist: no env extras, no --host extras, per test."""
    monkeypatch.delenv("SCANNER_ALLOWED_HOSTS", raising=False)
    monkeypatch.setattr(local_guard, "_extra_hosts", set())


# ── minimal pure-ASGI harness (replaces upstream's FastAPI TestClient) ───────

def make_scope(kind="http", method="GET", path="/", headers=None):
    merged = {"host": "127.0.0.1:7777"}          # what TestClient's base_url sent
    merged.update(headers or {})
    hs = [(k.lower().encode("latin-1"), v.encode("latin-1")) for k, v in merged.items()]
    scope = {"type": kind, "asgi": {"version": "3.0"}, "http_version": "1.1",
             "method": method, "path": path, "query_string": b"", "headers": hs,
             "client": ("127.0.0.1", 54321), "scheme": "http"}
    if kind == "websocket":
        scope["path"] = path
    return scope


class RecorderApp:
    """Stands in for the scanner app: records every scope that reaches it."""

    def __init__(self):
        self.calls = []

    async def __call__(self, scope, receive, send):
        self.calls.append(scope)
        if scope["type"] == "http":
            await send({"type": "http.response.start", "status": 200, "headers": []})
            await send({"type": "http.response.body", "body": b'{"ok": true}'})


def run_case(headers=None, kind="http", method="GET", path="/"):
    """Drive LocalOnlyMiddleware once. Returns (app, events)."""
    app = RecorderApp()
    guarded = local_guard.LocalOnlyMiddleware(app)
    events = []

    async def receive():
        if kind == "websocket":
            return {"type": "websocket.connect"}     # the connect event the guard awaits
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(event):
        events.append(event)

    asyncio.run(guarded(make_scope(kind, method, path, headers), receive, send))
    return app, events


def http_outcome(app, events):
    """(status, parsed_body_or_None, app_called)."""
    starts = [e for e in events if e["type"] == "http.response.start"]
    if starts:
        body = b"".join(e.get("body", b"") for e in events if e["type"] == "http.response.body")
        return starts[0]["status"], json.loads(body.decode("latin-1")), bool(app.calls)
    return 200, {"ok": True}, bool(app.calls)       # passthrough: recorder's own 200


# ── simple cross-origin POSTs (upstream: test_foreign_origin_cannot_post_...) ─

def test_foreign_origin_cannot_post_even_without_a_body():
    """Upstream: evil Origin POST (bodyless, json, and Origin 'null') → 403, app untouched."""
    r = run_case(method="POST", path="/api/v2/settings/reset",
                 headers={"Origin": EVIL})                       # no body, no Content-Type
    status, body, called = http_outcome(*r)
    assert status == 403 and not called
    r = run_case(method="POST", path="/api/v2/settings/reset",
                 headers={"Origin": EVIL, "Content-Type": "application/json"})
    status, body, called = http_outcome(*r)
    assert status == 403 and not called and body == {"error": "origin not allowed"}
    r = run_case(method="POST", path="/api/v2/settings/reset",
                 headers={"Origin": "null", "Content-Type": "application/json"})
    status, _, called = http_outcome(*r)
    assert status == 403 and not called


@pytest.mark.parametrize("ctype", [None, "text/plain", "application/x-www-form-urlencoded",
                                   "multipart/form-data"])
def test_post_must_be_json(ctype):
    """Upstream: what a no-cors fetch can send without a preflight → 415, app untouched.

    (No Origin header: scripts are let in — so the 415 is the Content-Type rule
    firing on its own, exactly as upstream.)"""
    headers = {"Content-Type": ctype} if ctype else {}
    status, body, called = http_outcome(*run_case(method="POST", path="/api/v2/settings/reset",
                                                  headers=headers))
    assert status == 415 and not called and body == {"error": "POST needs Content-Type: application/json"}


def test_dashboard_and_scripts_still_write():
    """Upstream: loopback origins and no-Origin scripts all reach the app."""
    for origin in ("http://localhost:5174", "http://127.0.0.1:7777",
                   "http://[::1]:7777", None):
        headers = {"Origin": origin, "Content-Type": "application/json"} if origin \
            else {"Content-Type": "application/json"}
        status, body, called = http_outcome(*run_case(method="POST",
                                                      path="/api/v2/settings/reset",
                                                      headers=headers))
        assert status == 200 and called, origin


def test_preflight_from_the_vite_dev_server_still_passes():
    """Upstream: OPTIONS preflight (not an unsafe method) passes to the app."""
    status, _, called = http_outcome(*run_case(
        method="OPTIONS", path="/api/v2/settings",
        headers={"Origin": "http://localhost:5174",
                 "Access-Control-Request-Method": "PUT"}))
    assert status == 200 and called


# ── DNS rebinding: the attacker's name arrives as Host (upstream block) ──────

@pytest.mark.parametrize("method,path", [("GET", "/api/v2/version"), ("GET", "/api/v2/settings"),
                                         ("PUT", "/api/v2/settings"), ("DELETE", "/api/v2/layouts/x")])
def test_rebound_hostname_is_refused(method, path):
    """Upstream: Host + Origin both the attacker's rebound name → 400 before any route."""
    headers = {"Host": "rebind.evil.example:7777", "Origin": "http://rebind.evil.example:7777"}
    if method in ("POST", "PUT"):
        headers["Content-Type"] = "application/json"
    status, body, called = http_outcome(*run_case(method=method, path=path, headers=headers))
    assert status == 400 and not called and body == {"error": "host not allowed"}


def test_loopback_names_are_accepted():
    """Upstream: the four loopback spellings (case-insensitive) reach the app."""
    for host in ("localhost:7777", "127.0.0.1:7777", "[::1]:7777", "LOCALHOST:5174"):
        status, _, called = http_outcome(*run_case(method="GET", path="/api/v2/version",
                                                   headers={"Host": host}))
        assert status == 200 and called, host


def test_lan_name_only_when_allowed_on_purpose(monkeypatch):
    """Upstream: LAN name refused → allow_hosts() (what --host does) admits it;
    wildcard names nothing; SCANNER_ALLOWED_HOSTS parses comma+space lists."""
    headers = {"Host": "192.168.1.5:7777", "Origin": "http://192.168.1.5:7777"}
    status, _, called = http_outcome(*run_case(method="GET", path="/api/v2/version", headers=headers))
    assert status == 400 and not called
    local_guard.allow_hosts("192.168.1.5")
    status, _, called = http_outcome(*run_case(method="GET", path="/api/v2/version", headers=headers))
    assert status == 200 and called
    status, _, called = http_outcome(*run_case(method="POST", path="/api/v2/settings/reset",
                                               headers={**headers, "Content-Type": "application/json"}))
    assert status == 200 and called
    local_guard.allow_hosts("0.0.0.0")            # a wildcard names nothing
    assert "0.0.0.0" not in local_guard.allowed_hosts()
    monkeypatch.setenv("SCANNER_ALLOWED_HOSTS", "trading-pc, trading-pc.lan")
    assert local_guard.host_allowed("trading-pc.lan:7777")


# ── WebSockets (upstream: test_foreign_websocket_is_closed) ──────────────────

@pytest.mark.parametrize("headers", [
    {"Origin": EVIL},
    {"Host": "rebind.evil.example:7777", "Origin": "http://rebind.evil.example:7777"},
])
def test_foreign_websocket_is_closed(headers):
    """Upstream: foreign WebSocket → close frame code 1008, app never sees the scope."""
    app, events = run_case(kind="websocket", path="/ws/alerts", headers=headers)
    closes = [e for e in events if e["type"] == "websocket.close"]
    assert closes and closes[0]["code"] == 1008 and not app.calls


def test_comp_loopback_websocket_passes_through():
    """Complementary (code-derived): loopback-origin WS upgrade reaches the app."""
    app, events = run_case(kind="websocket", path="/ws/alerts",
                           headers={"Origin": "http://127.0.0.1:7777"})
    assert app.calls and not [e for e in events if e["type"] == "websocket.close"]


# ── complementary unit-level fidelity (behaviors upstream exercised via HTTP) ─

def test_comp_hostname_parsing():
    """local_guard.hostname: 'localhost:7777'→'localhost', '[::1]:7777'→'::1', '::1'→'::1'."""
    assert local_guard.hostname("localhost:7777") == "localhost"
    assert local_guard.hostname("[::1]:7777") == "::1"
    assert local_guard.hostname("::1") == "::1"
    assert local_guard.hostname("LOCALHOST:5174") == "localhost"
    assert local_guard.hostname(None) == ""
    assert local_guard.hostname("") == ""


def test_comp_missing_host_passes_and_null_origin_fails():
    """host_allowed: missing Host is not a browser → passes. origin_allowed:
    no Origin passes; 'null' and non-http schemes do not."""
    assert local_guard.host_allowed(None) is True
    assert local_guard.origin_allowed(None) is True
    assert local_guard.origin_allowed("null") is False
    assert local_guard.origin_allowed("ftp://127.0.0.1") is False
    assert local_guard.origin_allowed("http://localhost:5174") is True
    assert local_guard.origin_allowed("http://evil.example") is False


def test_comp_get_with_foreign_origin_but_loopback_host_passes():
    """Complementary (upstream docstring logic): CORS stops READING, not SENDING;
    a simple GET with a foreign Origin is passed through — the guard only gates
    unsafe methods and WebSockets."""
    status, _, called = http_outcome(*run_case(method="GET", path="/api/v2/version",
                                               headers={"Origin": EVIL}))
    assert status == 200 and called


def test_comp_non_http_scope_passes_through_untouched():
    """Complementary: non-http/websocket scopes (e.g. lifespan) bypass the guard."""
    app = RecorderApp()
    guarded = local_guard.LocalOnlyMiddleware(app)

    async def noop():
        return {"type": "lifespan.startup"}

    seen = []
    asyncio.run(guarded({"type": "lifespan"}, noop, lambda ev: seen.append(ev)))
    assert len(app.calls) == 1 and app.calls[0]["type"] == "lifespan"
