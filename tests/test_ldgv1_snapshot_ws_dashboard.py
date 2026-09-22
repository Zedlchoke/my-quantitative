"""LIVE-DATA-GATEWAY-V1 tests: snapshot/WS/dashboard/canary laws (§12)."""

from __future__ import annotations

import json

from research.live_gateway.dashboard_states import map_dashboard_status
from research.live_gateway.snapshot import SnapshotStore
from research.live_gateway.timeutils import ms_to_iso_z
from research.live_gateway.wsadapter import parse_mark_event


class FakeClock:
    def __init__(self, start_ms: int = 1_700_000_000_000):
        self.ms = start_ms

    def __call__(self) -> int:
        return self.ms

    def advance(self, delta_ms: int) -> None:
        self.ms += delta_ms


def _apply(store, symbol, e_ms, mark, received):
    d = store.datum(symbol)
    return d.apply_ws_event(e_ms, mark, None, None, None, received)


# ----------------------------------------------------------------------
# timestamp normalization
# ----------------------------------------------------------------------
def test_ms_to_iso_z_roundtrip():
    assert ms_to_iso_z(1_700_000_000_000) == "2023-11-14T22:13:20Z"
    from research.live_gateway.timeutils import iso_z_to_ms

    assert iso_z_to_ms("2023-11-14T22:13:20Z") == 1_700_000_000_000


# ----------------------------------------------------------------------
# duplicate / out-of-order handling
# ----------------------------------------------------------------------
def test_duplicate_ws_message_counted_not_reapplied():
    store = SnapshotStore(now_ms=FakeClock())
    assert _apply(store, "BTCUSDT", 1000, 100.0, 1500) == "applied"
    assert _apply(store, "BTCUSDT", 1000, 100.0, 1600) == "duplicate"
    d = store.datum("BTCUSDT")
    assert d.duplicates_seen == 1
    assert d.received_at_ms == 1500  # not overwritten by the replay


def test_out_of_order_ws_event_not_reapplied():
    store = SnapshotStore(now_ms=FakeClock())
    _apply(store, "BTCUSDT", 2000, 101.0, 2100)
    assert _apply(store, "BTCUSDT", 1500, 99.0, 2200) == "out_of_order"
    assert store.datum("BTCUSDT").mark_price == 101.0


def test_parse_mark_event_fields():
    data = {
        "e": "markPriceUpdate", "E": 1700000000000, "s": "BTCUSDT",
        "p": "27000.5", "i": "26999.9", "r": "0.0001",
        "T": 1700008000000,
    }
    parsed = parse_mark_event(data)
    assert parsed == {
        "symbol": "BTCUSDT", "event_e_ms": 1700000000000,
        "mark_price": 27000.5, "index_price": 26999.9,
        "funding_rate": 0.0001, "next_funding_time_ms": 1700008000000,
    }


# ----------------------------------------------------------------------
# staleness + last-known-value truth law
# ----------------------------------------------------------------------
def test_stale_after_10s_and_canonical_current_false():
    clock = FakeClock()
    store = SnapshotStore(now_ms=clock)
    _apply(store, "BTCUSDT", clock(), 100.0, clock())
    payload = store.build_payload("BTCUSDT", "HEALTHY", ws_connected=True)
    assert payload["status"] == "HEALTHY"
    assert payload["canonical_current"] is True
    clock.advance(11_000)
    payload2 = store.build_payload("BTCUSDT", "HEALTHY", ws_connected=True)
    assert payload2["status"] == "STALE"
    assert payload2["stale_reason"] and "no stream message" in payload2["stale_reason"]
    assert payload2["canonical_current"] is False
    # last-known value IS still served (dashboard law) but never current
    assert payload2["value"] == 100.0


def test_disconnected_surface_forces_disconnected_datum():
    store = SnapshotStore(now_ms=FakeClock())
    _apply(store, "BTCUSDT", 1_700_000_000_000, 100.0, 1_700_000_000_001)
    payload = store.build_payload(
        "BTCUSDT", "DISCONNECTED", ws_connected=False
    )
    assert payload["status"] == "DISCONNECTED"
    assert payload["canonical_current"] is False


def test_degraded_surface_serves_fresh_healthful_datum_with_surface_state():
    store = SnapshotStore(now_ms=FakeClock())
    clock_ms = 1_700_000_000_000
    _apply(store, "BTCUSDT", clock_ms, 100.0, clock_ms)
    payload = store.build_payload("BTCUSDT", "DEGRADED", ws_connected=True)
    assert payload["status"] == "HEALTHY"  # datum usable
    assert payload["surface_state"] == "DEGRADED"  # transition visible


def test_not_subscribed_symbol_404_shape():
    store = SnapshotStore(now_ms=FakeClock())
    payload = store.build_payload(
        "NOPEUSDT", "HEALTHY", ws_connected=True, subscribed=False
    )
    assert payload["status"] == "NOT_SUBSCRIBED"
    assert payload["stale_reason"] == "not_subscribed"


def test_gap_detection_wall_clock():
    clock = FakeClock()
    store = SnapshotStore(now_ms=clock)
    _apply(store, "BTCUSDT", clock(), 100.0, clock())
    flagged = store.mark_gaps(["BTCUSDT"])
    assert flagged == []  # fresh: no gap
    clock.advance(15_000)  # silent > 10 s
    flagged = store.mark_gaps(["BTCUSDT"])
    assert flagged == ["BTCUSDT"]
    payload = store.build_payload("BTCUSDT", "HEALTHY", ws_connected=True)
    assert payload["status"] == "GAP_DETECTED"
    # fresh message heals
    _apply(store, "BTCUSDT", clock(), 101.0, clock())
    payload2 = store.build_payload("BTCUSDT", "HEALTHY", ws_connected=True)
    assert payload2["status"] == "HEALTHY"


# ----------------------------------------------------------------------
# dashboard mapping (§10 / §12 PARTIAL-state pure function)
# ----------------------------------------------------------------------
def test_dashboard_live():
    out = map_dashboard_status(
        {
            "pid": 1,
            "ws": {"state": "CONNECTED"},
            "stale_symbols": [],
            "rest_breaker": {"state": "HEALTHY"},
        },
        worker_heartbeat_age_s=5.0,
        decision_data_ok=True,
        accounting_ok=True,
    )
    assert out["badge"] == "LIVE"
    assert out["mark_price"] == "MARK PRICE OK"
    assert out["decision"] == "DECISION OK"


def test_dashboard_partial_rate_limited():
    out = map_dashboard_status(
        {
            "pid": 1,
            "ws": {"state": "CONNECTED"},
            "stale_symbols": [],
            "rest_breaker": {
                "state": "RATE_LIMITED",
                "allowed_retry_at_utc": "2026-09-21T12:06:00Z",
            },
        },
        worker_heartbeat_age_s=5.0,
        decision_data_ok=True,
    )
    assert out["badge"] == "PARTIAL"
    assert out["mark_price"] == "MARK PRICE RATE LIMITED"
    assert out["retry_allowed_at_utc"] == "2026-09-21T12:06:00Z"
    # the split chip law: decision stays OK while mark is rate-limited
    assert out["decision"] == "DECISION OK"


def test_dashboard_stale_badge():
    out = map_dashboard_status(
        {
            "pid": 1, "ws": {"state": "CONNECTED"},
            "stale_symbols": ["BTCUSDT"], "rest_breaker": {"state": "HEALTHY"},
        },
        worker_heartbeat_age_s=5.0,
    )
    assert out["badge"] == "STALE"
    assert out["mark_price"] == "MARK PRICE STALE"


def test_dashboard_offline_and_data_error():
    offline = map_dashboard_status(
        {}, worker_heartbeat_age_s=5000.0
    )
    assert offline["badge"] == "OFFLINE"
    data_err = map_dashboard_status(
        {"pid": 1}, schema_ok=False
    )
    assert data_err["badge"] == "DATA ERROR"


def test_dashboard_decision_blocked_split():
    out = map_dashboard_status(
        {
            "pid": 1, "ws": {"state": "CONNECTED"},
            "stale_symbols": [], "rest_breaker": {"state": "HEALTHY"},
        },
        worker_heartbeat_age_s=5.0,
        decision_data_ok=False,
    )
    # DATA BLOCKED for decision WITHOUT claiming mark price blocked
    assert out["decision"] == "DECISION DATA BLOCKED"
    assert out["mark_price"] == "MARK PRICE OK"
    assert out["badge"] == "PARTIAL"


# ----------------------------------------------------------------------
# canary laws (frozen thresholds, offline)
# ----------------------------------------------------------------------
def test_canary_compare_marks_and_verdict():
    import datetime as dt

    from research.live_gateway.canary import compare_marks, verdict_leg_a

    ts_ms = int(
        dt.datetime(2026, 9, 21, tzinfo=dt.timezone.utc).timestamp() * 1000
    )
    gw = {
        "BTCUSDT": {
            "value": 100.0,
            "provider_timestamp_utc": "2026-09-21T00:00:00Z",
            "status": "HEALTHY",
            "age_seconds": 0.5,
        },
        "ETHUSDT": {
            "value": 200.0,
            "provider_timestamp_utc": "2026-09-21T00:00:00Z",
            "status": "HEALTHY",
        },
    }
    rest = [
        {"symbol": "BTCUSDT", "markPrice": "100.001", "time": ts_ms + 500},
        {"symbol": "ETHUSDT", "markPrice": "200.0", "time": ts_ms},
    ]
    rows = compare_marks(gw, rest, ["BTCUSDT", "ETHUSDT"])
    compared = [r for r in rows if r["outcome"] == "compared"]
    assert len(compared) == 2
    # 0.001/100 = 0.1 bps: within 5
    verdict = verdict_leg_a(rows)
    assert verdict["pass"] and verdict["hard_violations_over_50bps"] == 0


def test_canary_verdict_hard_fail_on_50bps():
    from research.live_gateway.canary import verdict_leg_a

    rows = [
        {"outcome": "compared", "rel_bps": 60.0},
    ] * 100
    verdict = verdict_leg_a(rows)
    assert verdict["pass"] is False
    assert verdict["hard_violations_over_50bps"] == 100


def test_canary_verdict_missingness_fail():
    from research.live_gateway.canary import verdict_leg_a

    rows = [{"outcome": "missing_side"}] * 10 + [{"outcome": "compared", "rel_bps": 0.0}] * 90
    verdict = verdict_leg_a(rows)
    assert verdict["pass"] is False  # presence 0.9 < 0.99


def test_canary_historical_equivalence_digest_and_numeric():
    from research.live_gateway.canary import compare_window

    rows = [{"open": 1, "close": "100.5"}, {"open": 2, "close": "101.0"}]
    gw = {"rows": rows, "complete": True, "cache_hit": True}
    same = compare_window(gw, [dict(r) for r in rows])
    assert same["pass"] and same["digest_equal"]
    numeric = compare_window(gw, [
        {"open": 1, "close": "100.5"},
        {"open": 2, "close": "101.0000000000001"},  # <= 1e-12 abs
    ])
    assert numeric["pass"] is True and numeric["digest_equal"] is False
    bad = compare_window(gw, [{"open": 1, "close": "999"}])
    assert bad["pass"] is False and bad["reason"] == "row_count_mismatch"


def test_canary_direct_fetcher_pacing_and_abort():
    """Rpm-cap PACE-WAITs (canary-pacing fix 2026-09-22): a full
    direct-leg window must WAIT for the sliding window to drain — the
    rpm cap alone may never abort a pass; abort is reserved for
    418-class venue responses."""
    import io
    import time as _time
    from unittest import mock

    from research.live_gateway.canary import (
        DIRECT_MAX_RPM,
        DirectLegAborted,
        PacedDirectFetcher,
    )

    fetcher = PacedDirectFetcher()
    fetcher.last_request_at = _time.time() - 10.0  # min-gap satisfied
    fetcher.window = [_time.time()] * DIRECT_MAX_RPM  # full, fresh
    slept = []
    real_time = _time.time  # capture BEFORE patching (the canary module
    # imports the GLOBAL stdlib time module; patching time.time there
    # would recurse into this lambda)

    class _FakeResp(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    with mock.patch(
        "research.live_gateway.canary.time.sleep",
        side_effect=lambda s: slept.append(s),
    ), mock.patch(
        "research.live_gateway.canary.time.time",
        side_effect=lambda: real_time() + 0.1,  # window stays FRESH:
        # the cap check MUST fire and sleep out the drain wait
    ), mock.patch(
        "urllib.request.urlopen",
        return_value=_FakeResp(b'[{"ok": true}]'),
    ):
        raised = None
        try:
            fetcher.get_json("https://example.invalid/x")
        except DirectLegAborted as exc:
            raised = exc
    # pace-wait happened with the full ~59.9s drain...
    assert slept and slept[0] > 50.0, "rpm cap must WAIT (drain), not abort"
    # ...and if the window never drains the guard fires — but the OLD
    # instant "canary rpm cap" abort is gone
    assert raised is None or "rpm window failed to drain" in str(raised)
    # 418-class abort law unchanged: a banned response still aborts
    fetcher3 = PacedDirectFetcher()
    with mock.patch("urllib.request.urlopen") as op:
        op.side_effect = urllib_error_418()
        try:
            fetcher3.get_json("https://example.invalid/x")
            raised = None
        except DirectLegAborted as exc:
            raised = exc
    assert raised is not None and "418" in str(raised)


def urllib_error_418():
    import io
    import urllib.error

    class _Resp(io.BytesIO):
        def __init__(self):
            super().__init__(b"banned until 9999999999999")
            self.headers = {"Retry-After": "60"}

        def read(self, *a):
            return b"banned until 9999999999999"

    return urllib.error.HTTPError(
        "url", 418, "I'm a teapot", {"Retry-After": "60"}, _Resp()
    )
