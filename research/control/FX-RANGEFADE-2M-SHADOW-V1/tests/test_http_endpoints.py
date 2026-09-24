"""HTTP contract of the Phorec dashboard server.

Owner order 2026-09-24: the EXACT URLs the browser calls — including
cache-buster query strings — must return HTTP 200 with data, never a
404 caused by the query string. Also pins /health.json (OFFLINE/STALE
honesty inputs) and the no-order-API surface.
"""
import json
import threading
import time
from http.server import ThreadingHTTPServer

import pytest

import serve as serve_mod


@pytest.fixture(scope="module")
def server(tmp_path_factory):
    root = tmp_path_factory.mktemp("phorec_root")
    dash = tmp_path_factory.mktemp("phorec_dash")
    state = {
        "schema": "phorec.shadow_state@2",
        "updated_utc": "2026-09-24T04:00:00+00:00",
        "data_stale": False,
        "marks_fresh": True,
        "account": {"seed_equity": 100000.0, "equity": 100045.0,
                    "pnl_today": 45.0, "pnl_total": 45.0},
        "sleeves": {"EURUSD": {}, "GBPUSD": {}},
    }
    (root / "shadow_state.json").write_text(json.dumps(state))
    (root / "shadow_journal.jsonl").write_text(
        json.dumps({"seq": 1, "event": "fill_open", "pair": "EURUSD"}) + "\n" +
        json.dumps({"seq": 2, "event": "fill_close", "pair": "EURUSD"}) + "\n")
    (root / "daemon_heartbeat.json").write_text(json.dumps(
        {"pid_heartbeat_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}))
    (dash / "index.html").write_text("<html>phorec</html>")

    serve_mod.STATE = root / "shadow_state.json"
    serve_mod.JOURNAL = root / "shadow_journal.jsonl"
    serve_mod.HEARTBEAT = root / "daemon_heartbeat.json"
    serve_mod.EQUITY_CURVE = root / "equity_curve.json"
    serve_mod.HERE = dash

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), serve_mod.Handler)
    port = httpd.server_address[1]
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()
    yield f"http://127.0.0.1:{port}"
    httpd.shutdown()


def _get(base, path):
    import urllib.request
    req = urllib.request.Request(base + path, headers={"User-Agent": "phorec-test/1.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        return r.status, dict(r.headers), r.read()


def test_exact_browser_urls_with_cache_buster_return_200(server):
    buster = str(int(time.time() * 1000))
    for path, ctype in [
        ("/", "text/html"),
        ("/index.html", "text/html"),
        ("/state.json?" + buster, "application/json"),
        ("/equity_curve.json?t=" + buster, "application/json"),
        ("/journal.jsonl?" + buster, "application/x-ndjson"),
        ("/journal.jsonl?limit=1&" + buster, "application/x-ndjson"),
        ("/health.json?" + buster, "application/json"),
    ]:
        status, headers, body = _get(server, path)
        assert status == 200, path
        assert headers.get("Content-Type", "").startswith(ctype), path
        assert body, path


def test_journal_limit_returns_tail_only(server):
    _, _, body = _get(server, "/journal.jsonl?limit=1&x=1")
    lines = [l for l in body.decode().splitlines() if l.strip()]
    assert len(lines) == 1
    assert json.loads(lines[0])["seq"] == 2


def test_health_reports_server_time_and_freshness(server):
    status, _, body = _get(server, "/health.json")
    h = json.loads(body)
    assert h["schema"] == "phorec.health@1"
    assert h["daemon_alive"] is True, "fresh heartbeat => daemon alive"
    assert h["heartbeat_age_s"] is not None and h["heartbeat_age_s"] < 90
    assert h["state_age_s"] is not None


def test_state_and_curve_missing_fail_open_to_placeholders_not_crash(tmp_path, server):
    serve_mod.STATE = tmp_path / "missing_state.json"
    serve_mod.EQUITY_CURVE = tmp_path / "missing_curve.json"
    try:
        status, _, body = _get(server, "/state.json?cb=1")
        assert status == 200
        d = json.loads(body)
        assert d["data_stale"] is True and d["marks_fresh"] is False
        assert d["account"] is None, "no state -> no fabricated equity"
        status, _, body = _get(server, "/equity_curve.json?cb=1")
        assert status == 200 and json.loads(body)["points"] == []
    finally:
        pass


def test_unknown_path_still_404_with_query(server):
    import urllib.error
    with pytest.raises(urllib.error.HTTPError) as ei:
        _get(server, "/nope.json?cb=1")
    assert ei.value.code == 404


def test_responses_are_no_store(server):
    _, headers, _ = _get(server, "/state.json?cb=2")
    assert headers.get("Cache-Control") == "no-store"
