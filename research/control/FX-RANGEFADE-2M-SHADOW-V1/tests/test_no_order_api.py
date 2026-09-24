"""Static surface test: the Phorec stack has NO order/broker API.

Paper/shadow only (plan §4): no broker connectivity, no credentials,
no orders. This scans the actual sources for outbound order surface —
the only allowed outbound HTTP is the read-only TrueFX quote GET, and
the only server is the local read-only dashboard.
"""
import json
from pathlib import Path

CYCLE = Path(__file__).resolve().parent.parent
SOURCES = [
    CYCLE / "daemon" / "shadow_daemon.py",
    CYCLE / "daemon" / "fx_shadow_core.py",
    CYCLE / "dashboard" / "serve.py",
    CYCLE / "phorec_app_entry.py",
]

# capability markers only: bare words like "broker" appear legitimately
# in docstrings saying we DON'T have one — do not scan for those.
FORBIDDEN_MARKERS = [
    "requests.post(", "requests.put(", "requests.delete(",
    "urlopen(req, data=", "urlencode({", "http.client",
    "import mt5", "MetaTrader5", "oandapy", "oandapyV20", "fxcmpy",
    "import ccxt", "from ccxt",
    "api_key", "apikey", "access_token", "Authorization:",
    "place_order(", "create_order(", "submit_order(", "send_order(",
    "set_sl", "set_tp", "market_buy", "market_sell", "limit_buy", "limit_sell",
]


def test_sources_exist():
    for path in SOURCES:
        assert path.is_file(), f"missing source: {path}"


def test_no_order_surface_in_sources():
    for path in SOURCES:
        text = path.read_text()
        for marker in FORBIDDEN_MARKERS:
            assert marker not in text, f"{path.name}: forbidden marker {marker!r}"


def test_daemon_only_talks_to_truefx_readonly():
    text = (CYCLE / "daemon" / "shadow_daemon.py").read_text()
    assert "webrates.truefx.com" in text
    assert 'User-Agent": "phorec-shadow' in text
    # only GET-style urlopen(Request(...)) without data payload:
    assert "urlopen(req" in text


def test_server_is_local_read_only():
    text = (CYCLE / "dashboard" / "serve.py").read_text()
    assert "127.0.0.1" in text
    assert "do_POST" not in text and "do_PUT" not in text and "do_DELETE" not in text


def test_state_file_has_no_credentials():
    state = CYCLE / "shadow_state.json"
    if state.is_file():
        obj = json.loads(state.read_text())
        blob = json.dumps(obj).lower()
        for marker in ("api_key", "token", "password", "secret"):
            assert marker not in blob
