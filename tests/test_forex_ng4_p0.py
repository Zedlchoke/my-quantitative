"""FOREX-NG4 P0 tests: EURUSD TD probe fail-closed law, EZ census
decision law, vintage-parser reuse and the 16:00-NY DST boundary.

All fixtures are synthetic (hand-computed, written under pytest's tmp
factories anchored at /tmp/forex_ng4_p0_tests); NO network, NO CADS
store reads, NO scored data, NO PnL.  Every expected value below was
computed by hand and is asserted exactly:

- key-absent fail-closed: a .env without TWELVE_DATA_API_KEY yields
  None and the probe returns UNAVAILABLE WITHOUT any transport call
  (asserted by a transport that fails the test if invoked);
- one-call law: a transport that times out once then answers records
  exactly 2 attempts (the single permitted timeout-only retry); a
  non-timeout HTTP error makes exactly 1 attempt (no retry);
- provider refusal (status != ok / HTTP 403) -> UNAVAILABLE;
- success path pins the exact response bytes and verify-on-read fails
  closed on drift;
- strict ng1 parser reuse on a synthetic EURUSD payload: duplicate
  dates, symbol mismatch and non-monotonic storage all refuse;
- DST boundary of the 16:00-NY decision clock: a normal Fri->Mon is
  72h, spring-forward 71h, fall-back 73h (hand-computed UTC instants);
- vintage parser reuse: a /tmp FRED-style vintaged JSON parses to
  VintageRows and a row missing the realtime window fails structurally
  (a current-vintage table is not an archive);
- EZ census decision: bytes absent -> BLOCKED_DATA with floors NOT_RUN
  and the ingest blocker; bytes present -> MEASURABLE; the
  dispatch-suggested series-id correction is carried in the artifact;
- 5-pair grid extension: adding a pair whose calendar misses one
  weekday removes exactly that day from the intersection grid.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error

import pytest

REPO_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from research.assets.forex_ng1 import plane_adapter as pa          # noqa: E402
from research.assets.forex_ng1 import spot_series as ss            # noqa: E402
from research.assets.forex_ng4 import ez_census as ez              # noqa: E402
from research.assets.forex_ng4 import td_probe as tp               # noqa: E402

TEST_ROOT = "/tmp/forex_ng4_p0_tests"


def _w(path: str, data) -> str:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if isinstance(data, bytes):
        with open(path, "wb") as fh:
            fh.write(data)
    elif isinstance(data, str):
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(data)
    else:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
    return path


# --------------------------------------------------------------------------- #
# synthetic EURUSD provider payload (hand-computed; newest-first like TD)
# --------------------------------------------------------------------------- #

def _eurusd_payload(values=None):
    if values is None:
        values = [
            {"datetime": "2024-03-11", "open": "1.0850", "high": "1.0870",
             "low": "1.0840", "close": "1.0860"},
            {"datetime": "2024-03-08", "open": "1.0820", "high": "1.0830",
             "low": "1.0810", "close": "1.0825"},
        ]
    return {
        "meta": {"symbol": "EUR/USD", "interval": "1day",
                 "currency_base": "Euro", "currency_quote": "US Dollar",
                 "type": "Physical Currency"},
        "values": values,
        "status": "ok",
    }


class _FakeResp:
    def __init__(self, body: bytes):
        self._body = body

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


# --------------------------------------------------------------------------- #
# 1. key-absent fail-closed + one-call law (NO network: injected transport)
# --------------------------------------------------------------------------- #

def test_key_absent_env_returns_none(tmp_path_factory):
    env = _w(f"{TEST_ROOT}/env_absent/.env", "OTHER_KEY=xyz\n# comment\n")
    assert tp.load_api_key(env) is None


def _scrub(rec: dict) -> dict:
    """The runner's evidence shape: payload bytes/payload never embed."""
    return {k: v for k, v in rec.items()
            if k not in ("payload_bytes", "payload")}


def test_key_present_env_loads_and_never_leaks_into_evidence():
    env = _w(f"{TEST_ROOT}/env_present/.env",
             "TWELVE_DATA_API_KEY=test-key-value-123\n")
    key = tp.load_api_key(env)
    assert key == "test-key-value-123"
    body = json.dumps(_eurusd_payload()).encode()
    rec = tp.probe_eurusd(
        key, transport=lambda url, timeout: _FakeResp(body))
    assert rec["status"] == "OK"
    # the recorded evidence NEVER carries the key value (name-only law)
    blob = json.dumps(_scrub(rec))
    assert "test-key-value-123" not in blob
    assert "apikey=" not in blob


def test_probe_key_absent_unavailable_without_any_call():
    calls = []

    def transport(url, timeout):
        calls.append(url)
        raise AssertionError("must not be called without a key")

    rec = tp.probe_eurusd(None, transport=transport)
    assert rec["status"] == "UNAVAILABLE"
    assert rec["key_present"] is False
    assert calls == []
    assert "TWELVE_DATA_API_KEY absent" in rec["reason"]


def test_probe_timeout_retry_once_then_success():
    body = json.dumps(_eurusd_payload()).encode()
    calls = []

    def transport(url, timeout):
        calls.append(url)
        if len(calls) == 1:
            raise TimeoutError("timed out")
        return _FakeResp(body)

    rec = tp.probe_eurusd("k", transport=transport)
    assert rec["status"] == "OK"
    assert len(calls) == 2                     # 1 call + 1 timeout retry
    assert len(rec["attempts"]) == 2
    assert rec["attempts"][0]["timeout"] is True
    assert rec["sha256"] == tp.hashlib.sha256(body).hexdigest()
    assert "apikey=" not in json.dumps(_scrub(rec))   # no key in evidence


def test_probe_non_timeout_error_never_retries():
    calls = []

    def transport(url, timeout):
        calls.append(url)
        raise urllib.error.HTTPError(
            url, 403, "Forbidden", hdrs=None, fp=None)

    rec = tp.probe_eurusd("k", transport=transport)
    assert rec["status"] == "UNAVAILABLE"
    assert len(calls) == 1                     # no retry on non-timeout
    assert rec["http_error"]["http_status"] == 403


def test_probe_provider_status_not_ok_unavailable():
    payload = _eurusd_payload()
    payload["status"] = "error"
    payload["message"] = "quota exceeded"
    body = json.dumps(payload).encode()

    rec = tp.probe_eurusd("k",
                          transport=lambda url, timeout: _FakeResp(body))
    assert rec["status"] == "UNAVAILABLE"
    assert rec["provider_status"] == "error"
    assert rec["http_error"]["class"] == "ProviderStatus"


def test_pin_and_verify_pinned_bytes_fail_closed_on_drift(tmp_path):
    pin_dir = os.path.join(TEST_ROOT, "pin")
    body = json.dumps(_eurusd_payload()).encode()
    ev = tp.pin_probe_bytes(body, pin_dir)
    assert ev["copy_sha256"] == tp.hashlib.sha256(body).hexdigest()
    ok = tp.verify_pinned_bytes(pin_dir, ev["copy_sha256"])
    assert ok["bytes"] == len(body)
    # drift a single byte -> fail-closed
    path = os.path.join(pin_dir, tp.PIN_FILE)
    with open(path, "wb") as fh:
        fh.write(body[:-1] + b"X")
    with pytest.raises(tp.ProbeError):
        tp.verify_pinned_bytes(pin_dir, ev["copy_sha256"])


def test_strict_payload_check():
    assert tp.strict_payload_check(_eurusd_payload())["ok"] is True
    bad = _eurusd_payload()
    bad["meta"]["symbol"] = "GBP/USD"
    assert tp.strict_payload_check(bad)["ok"] is False


# --------------------------------------------------------------------------- #
# 2. strict ng1 parser reuse on the EURUSD payload class
# --------------------------------------------------------------------------- #

def test_parse_spot_payload_eurusd_ok():
    bars = ss.parse_spot_payload(_eurusd_payload(), "EURUSD")
    assert [b["date"].isoformat() for b in bars] == ["2024-03-08",
                                                     "2024-03-11"]
    assert bars[0]["close"] == 1.0825


def test_parse_spot_payload_duplicate_refuses():
    values = [
        {"datetime": "2024-03-11", "open": "1", "high": "2",
         "low": "0.5", "close": "1"},
        {"datetime": "2024-03-11", "open": "1", "high": "2",
         "low": "0.5", "close": "1"},
    ]
    with pytest.raises(ss.SpotStructureError):
        ss.parse_spot_payload(_eurusd_payload(values), "EURUSD")


def test_parse_spot_payload_symbol_mismatch_refuses():
    payload = _eurusd_payload()
    payload["meta"]["symbol"] = "GBP/USD"
    with pytest.raises(ss.SpotStructureError):
        ss.parse_spot_payload(payload, "EURUSD")


def test_parse_spot_payload_non_monotonic_storage_refuses():
    values = [
        {"datetime": "2024-03-11", "open": "1", "high": "2",
         "low": "0.5", "close": "1"},
        {"datetime": "2024-03-08", "open": "1", "high": "2",
         "low": "0.5", "close": "1"},
        {"datetime": "2024-03-12", "open": "1", "high": "2",
         "low": "0.5", "close": "1"},
    ]
    with pytest.raises(ss.SpotStructureError):
        ss.parse_spot_payload(_eurusd_payload(values), "EURUSD")


# --------------------------------------------------------------------------- #
# 3. 16:00-NY DST boundary (hand-computed UTC instants)
# --------------------------------------------------------------------------- #

def test_dst_boundary_spring_forward_71h():
    from datetime import date as D
    fri, mon = D(2024, 3, 8), D(2024, 3, 11)
    i_fri = ss.ny_decision_instant_utc(fri)
    i_mon = ss.ny_decision_instant_utc(mon)
    assert ss.instant_iso(i_fri) == "2024-03-08T21:00:00Z"  # EST (UTC-5)
    assert ss.instant_iso(i_mon) == "2024-03-11T20:00:00Z"  # EDT (UTC-4)
    gap = (i_mon - i_fri).total_seconds() / 3600
    assert gap == 71.0                                        # spring-forward


def test_dst_boundary_fall_back_73h():
    from datetime import date as D
    fri, mon = D(2024, 11, 1), D(2024, 11, 4)
    i_fri = ss.ny_decision_instant_utc(fri)
    i_mon = ss.ny_decision_instant_utc(mon)
    assert ss.instant_iso(i_fri) == "2024-11-01T20:00:00Z"  # EDT (UTC-4)
    assert ss.instant_iso(i_mon) == "2024-11-04T21:00:00Z"  # EST (UTC-5)
    gap = (i_mon - i_fri).total_seconds() / 3600
    assert gap == 73.0                                        # fall-back


def test_dst_boundary_normal_weekend_72h():
    from datetime import date as D
    fri, mon = D(2024, 6, 7), D(2024, 6, 10)
    gap = ((ss.ny_decision_instant_utc(mon)
            - ss.ny_decision_instant_utc(fri)).total_seconds() / 3600)
    assert gap == 72.0


# --------------------------------------------------------------------------- #
# 4. vintage parser reuse (/tmp FRED-style fixture)
# --------------------------------------------------------------------------- #

def _vintaged_fixture(path: str) -> str:
    payload = {"observations": [
        {"date": "2020-01-01", "realtime_start": "2020-02-15",
         "realtime_end": "2020-03-14", "value": "104.0"},
        {"date": "2020-01-01", "realtime_start": "2020-03-15",
         "realtime_end": "9999-12-31", "value": "104.2"},
        {"date": "2020-02-01", "realtime_start": "2020-03-15",
         "realtime_end": "9999-12-31", "value": "104.4"},
    ]}
    return _w(path, payload)


def test_vintage_parser_reuse_ok():
    path = _vintaged_fixture(f"{TEST_ROOT}/vintage/ok.json")
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    rows = pa.parse_fred_vintaged(payload["observations"])
    assert len(rows) == 3
    assert rows[0].obs_date == "2020-01-01"
    assert rows[0].realtime_start == "2020-02-15"
    assert rows[1].value == "104.2"


def test_vintage_parser_reuse_current_vintage_table_refused():
    # a current-vintage revised-in-place table has no realtime window
    path = _w(f"{TEST_ROOT}/vintage/current.json", {"observations": [
        {"date": "2020-01-01", "value": "104.2"},
    ]})
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    with pytest.raises(pa.VintageStructureError):
        pa.parse_fred_vintaged(payload["observations"])


# --------------------------------------------------------------------------- #
# 5. EZ census decision law (fail-closed honesty)
# --------------------------------------------------------------------------- #

BYTE_SEARCH_ABSENT = {
    "series_file": ez.EZ_SERIES_FILE,
    "pinned_dir_listing": ["GBRCPIALLMINMEI.json", "CANCPIALLMINMEI.json",
                           "AUSCPIALLQINMEI.json", "NZLCPIALLQINMEI.json"],
    "in_pinned_vintaged_dir": False,
    "matches_elsewhere": [],
    "bytes_resolvable": False,
}
BYTE_SEARCH_PRESENT = dict(BYTE_SEARCH_ABSENT,
                           in_pinned_vintaged_dir=True,
                           bytes_resolvable=True)
CV_ABSENT = {"series_file": ez.EZ_SERIES_FILE, "matches": [],
             "bytes_resolvable": False}
V8_DERIVED = {
    "v8_staged_manifest_entry": {
        "file": ez.EZ_SERIES_FILE,
        "sha256": "886f0afee88ac916a9aaeaabc57874ece6615b905c045b83a45551c3e72d5735",
        "binding_rows": 696,
    },
    "label": ("COMMITTED V8 DERIVED STATS -- recorded by V8 at its "
              "measurement time; NOT a re-measurement on bytes and never "
              "usable as a floor PASS"),
}


def test_ez_census_bytes_absent_blocked_not_run():
    dec = ez.ez_census_decision(BYTE_SEARCH_ABSENT, V8_DERIVED, CV_ABSENT)
    assert dec["status"] == "VINTAGED_BYTES_NOT_IN_PINNED_SET"
    assert dec["verdict"] == "BLOCKED_DATA"
    assert len(dec["blockers"]) == 2          # vintaged absent + DOI absent
    assert all(f["verdict"] == "NOT_RUN" and f["measured"] is None
               for f in dec["floors"].values())
    assert any("owner / A3-lane decision" in b for b in dec["blockers"])


def test_ez_census_bytes_present_measurable():
    dec = ez.ez_census_decision(BYTE_SEARCH_PRESENT, V8_DERIVED,
                                dict(CV_ABSENT, bytes_resolvable=True))
    assert dec["verdict"] == "MEASURABLE"
    assert dec["blockers"] == []


def test_ez_census_carries_dispatch_id_correction():
    dec = ez.ez_census_decision(BYTE_SEARCH_ABSENT, V8_DERIVED, CV_ABSENT)
    ident = dec["series_identification"]
    assert ident["ez_series_id"] == "CP0000EZ19M086NEST"
    assert ident["dispatch_suggested_series_id"] == "EZCPIALLMINMEI"
    assert "appears in NO manifest" in ident["dispatch_id_correction"]


def test_ez_census_evidence_never_infers_a_pass():
    dec = ez.ez_census_decision(BYTE_SEARCH_ABSENT, V8_DERIVED, CV_ABSENT)
    # the V8 derived sha is carried as evidence-about, but no floor can
    # become PASS/MEASURED from derived stats alone
    blob = json.dumps(dec["floors"])
    assert "PASS" not in blob
    assert "MEASURED" not in blob


def test_find_ez_bytes_on_fixture_roots(tmp_path):
    root = tmp_path / "roots" / "somewhere"
    root.mkdir(parents=True)
    (root / ez.EZ_SERIES_FILE).write_text("{}")
    res = ez.find_ez_bytes(
        vintaged_dir=str(tmp_path / "roots" / "vintaged"),
        search_roots=(str(tmp_path / "roots"),))
    assert res["bytes_resolvable"] is True
    assert res["matches_elsewhere"] == [str(root / ez.EZ_SERIES_FILE)]


# --------------------------------------------------------------------------- #
# 6. 5-pair grid extension law
# --------------------------------------------------------------------------- #

def _mk_series(pair, days):
    from datetime import date as D
    return ss.SpotSeries(
        pair=pair, bars=len(days), first_day=days[0], last_day=days[-1],
        days=tuple(days),
        closes={d: 1.0 for d in days}, sha256="0" * 64)


def test_grid_extension_eurusd_removes_only_its_missing_day():
    from datetime import date as D
    days = [D(2024, 3, 4), D(2024, 3, 5), D(2024, 3, 6),
            D(2024, 3, 7), D(2024, 3, 11)]
    four = {p: _mk_series(p, days) for p in
            ("GBPUSD", "USDCAD", "AUDUSD", "NZDUSD")}
    base = ss.common_weekday_grid(four, D(2024, 3, 1), D(2024, 3, 31))
    assert base == days
    eurusd_days = [d for d in days if d != D(2024, 3, 6)]
    five = dict(four)
    five["EURUSD"] = _mk_series("EURUSD", eurusd_days)
    grid5 = ss.common_weekday_grid(five, D(2024, 3, 1), D(2024, 3, 31))
    assert grid5 == eurusd_days          # exactly the EURUSD calendar


# --------------------------------------------------------------------------- #
# 7. ng1 pin-manifest verify-on-read law (drift refuses)
# --------------------------------------------------------------------------- #

def test_pin_manifest_verify_drift_refuses(tmp_path):
    body = json.dumps(_eurusd_payload()).encode()
    data_dir = os.path.join(TEST_ROOT, "pinmanifest")
    os.makedirs(data_dir, exist_ok=True)
    with open(os.path.join(data_dir, "EURUSD.json"), "wb") as fh:
        fh.write(body)
    manifest = {"schema": "forex_ng4_p0_spot_pin_manifest@1",
                "files": {"EURUSD": {
                    "file": "EURUSD.json",
                    "copy_path_absolute": os.path.join(
                        data_dir, "EURUSD.json"),
                    "copy_sha256": tp.hashlib.sha256(body).hexdigest()}}}
    assert ss.verify_spot_file(manifest, "EURUSD", data_dir=data_dir) == \
        manifest["files"]["EURUSD"]["copy_sha256"]
    # unpinned pair refuses (the ng1 structural-canary law)
    with pytest.raises(ss.SpotIntegrityError):
        ss.verify_spot_file(manifest, "XXXUSD", data_dir=data_dir)
    # drift refuses
    with open(os.path.join(data_dir, "EURUSD.json"), "wb") as fh:
        fh.write(body + b" ")
    with pytest.raises(ss.SpotIntegrityError):
        ss.verify_spot_file(manifest, "EURUSD", data_dir=data_dir)


# --------------------------------------------------------------------------- #
# 8. P0b EZ vintaged ingest law (etiquette, key hygiene, fail-closed)
# --------------------------------------------------------------------------- #

from research.assets.forex_ng2 import revision_series as ng2     # noqa: E402
from research.assets.forex_ng3 import revision_series as rs      # noqa: E402
from research.assets.forex_ng4 import ez_vintaged as ezv         # noqa: E402

FAKE_KEY = "TESTKEY_NEVER_REAL"


class _Resp:
    def __init__(self, body: bytes, status: int = 200):
        self._body, self.status = body, status

    def read(self) -> bytes:
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _snapshot_payload(vd: str, month_values: dict) -> bytes:
    """An ALFRED as-of snapshot response: rows clamped rs=re=vd."""
    obs = [{"realtime_start": vd, "realtime_end": vd,
            "date": m, "value": v}
           for m, v in sorted(month_values.items())]
    return json.dumps({"count": len(obs), "observations": obs}).encode()


def test_p0b_key_law(tmp_path):
    env = tmp_path / "env"
    env.write_text(f"OTHER=1\n{ezv.KEY_NAME}={FAKE_KEY}\n")
    assert ezv.load_fred_key(str(env)) == FAKE_KEY
    env2 = tmp_path / "env2"
    env2.write_text("OTHER=1\n")
    assert ezv.load_fred_key(str(env2)) is None
    assert ezv.load_fred_key(str(tmp_path / "absent")) is None


def test_p0b_vintage_grid():
    grid = ezv.vintage_dates()
    assert len(grid) == 97                       # 96 + the 2017-12 warmup
    assert grid[0] == "2017-12-01" and grid[-1] == "2025-12-01"
    assert all(d[8:10] == "01" for d in grid)
    assert grid == sorted(grid) and len(set(grid)) == len(grid)


def test_p0b_fetch_ok_evidence_hygiene():
    body = _snapshot_payload("2018-03-01", {"2018-01-01": "101.77"})
    seen_urls = []

    def transport(url, timeout=30):
        seen_urls.append(url)
        return _Resp(body)

    rec = ezv.fetch_vintage("2018-03-01", FAKE_KEY, transport=transport,
                            sleep_fn=lambda s: None)
    assert rec["status"] == "OK"
    assert rec["observations_count"] == 1
    assert rec["count_declared"] == 1
    assert "api_key=" + FAKE_KEY in seen_urls[0]      # the real URL keys it
    blob = json.dumps(rec, default=lambda o: repr(o))
    assert FAKE_KEY not in blob                       # evidence never does
    assert "apikey" not in json.dumps(
        rec["params_recorded_without_apikey"])        # params record is keyless
    assert rec["endpoint"] == ezv.ENDPOINT            # name only, no query


def test_p0b_fetch_backoff_retry_then_ok():
    import io
    import urllib.error
    body = _snapshot_payload("2018-03-01", {"2018-01-01": "101.77"})
    calls = {"n": 0}
    sleeps = []

    def transport(url, timeout=30):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise urllib.error.HTTPError(
                url, 500, "Server Error", {}, io.BytesIO(b"{}"))
        return _Resp(body)

    rec = ezv.fetch_vintage("2018-03-01", FAKE_KEY, transport=transport,
                            sleep_fn=sleeps.append)
    assert rec["status"] == "OK"
    assert [a["outcome"] for a in rec["attempts"]] == \
        ["http_error", "http_error", "responded"]
    assert sleeps == [2.0, 4.0]                       # exponential backoff


def test_p0b_fetch_key_invalid_fatal_no_retry():
    import io
    import urllib.error
    err = json.dumps({
        "error_code": 400,
        "error_message": "The value for api_key is invalid. You must "
                         "register for a key."}).encode()
    calls = {"n": 0}

    def transport(url, timeout=30):
        calls["n"] += 1
        raise urllib.error.HTTPError(
            url, 400, "Bad Request", {}, io.BytesIO(err))

    rec = ezv.fetch_vintage("2018-03-01", FAKE_KEY, transport=transport,
                            sleep_fn=lambda s: pytest.fail("no retry"))
    assert rec["status"] == "FATAL_KEY_INVALID"
    assert calls["n"] == 1
    assert FAKE_KEY not in json.dumps(rec)


def test_p0b_fetch_quota_fatal_no_retry():
    import io
    import urllib.error
    err = json.dumps({
        "error_code": 429,
        "error_message": "Resource limit is exceeded. Requests per "
                         "minute quota."}).encode()
    calls = {"n": 0}

    def transport(url, timeout=30):
        calls["n"] += 1
        raise urllib.error.HTTPError(
            url, 429, "Too Many Requests", {}, io.BytesIO(err))

    rec = ezv.fetch_vintage("2018-03-01", FAKE_KEY, transport=transport,
                            sleep_fn=lambda s: pytest.fail("no retry"))
    assert rec["status"] == "FATAL_QUOTA_EXCEEDED"
    assert calls["n"] == 1


def test_p0b_fetch_no_key_refuses_without_call():
    def transport(url, timeout=30):
        pytest.fail("no network call may happen without a key")

    rec = ezv.fetch_vintage("2018-03-01", None, transport=transport,
                            sleep_fn=lambda s: None)
    assert rec["status"] == "FATAL_NO_KEY"
    assert rec["attempts"] == []


def _valid_snapshots():
    return [
        ("2018-03-01", _snapshot_payload("2018-03-01", {
            "2018-01-01": "101.77", "2018-02-01": ".",
            "2018-03-01": "100.0"})),
        ("2018-04-01", _snapshot_payload("2018-04-01", {
            "2018-01-01": "101.78", "2018-02-01": "103.0",
            "2018-03-01": "100.5"})),
        ("2018-05-01", _snapshot_payload("2018-05-01", {
            "2018-01-01": "101.78", "2018-02-01": "103.0",
            "2018-03-01": "100.5", "2018-04-01": "101.0"})),
    ]


def test_p0b_ingest_paces_writes_manifest_and_roundtrips(tmp_path):
    snaps = _valid_snapshots()
    calls = {"n": 0}
    sleeps = []
    mono = {"t": 0.0}

    def transport(url, timeout=30):
        calls["n"] += 1
        return _Resp(snaps[calls["n"] - 1][1])

    manifest_path = str(tmp_path / "manifest.json")
    ev = ezv.ingest_all(
        FAKE_KEY, manifest_path, vintages_dir=str(tmp_path / "vintages"),
        transport=transport, sleep_fn=sleeps.append,
        monotonic_fn=lambda: mono["t"],
        vintage_list=[vd for vd, _ in snaps])
    assert ev["status"] == "COMPLETE" and ev["vintage_count_fetched"] == 3
    # pacing: >= 1.2 s enforced before every request after the first
    assert sleeps == [1.2, 1.2]
    # raw bytes pinned untracked-side + manifest sha round trip
    for vd, body in snaps:
        p = tmp_path / "vintages" / ezv.vintage_file_name(vd)
        assert p.read_bytes() == body
        assert ev["files"][vd]["sha256"] == \
            __import__("hashlib").sha256(body).hexdigest()
    with open(manifest_path, "r", encoding="utf-8") as fh:
        on_disk = json.load(fh)
    assert on_disk["status"] == "COMPLETE"
    assert on_disk["raw_bytes_policy"].startswith("UNTRACKED")
    out = ezv.load_pinned_vintages(manifest_path,
                                   vintages_dir=str(tmp_path / "vintages"))
    assert [vd for vd, _ in out] == [vd for vd, _ in snaps]


def test_p0b_ingest_stops_fail_closed_on_fatal(tmp_path):
    import io
    import urllib.error
    err = json.dumps({"error_code": 400, "error_message":
                      "The value for api_key is not valid."}).encode()
    snaps = _valid_snapshots()
    calls = {"n": 0}

    def transport(url, timeout=30):
        calls["n"] += 1
        if calls["n"] == 1:
            return _Resp(snaps[0][1])
        raise urllib.error.HTTPError(
            url, 400, "Bad Request", {}, io.BytesIO(err))

    manifest_path = str(tmp_path / "manifest.json")
    ev = ezv.ingest_all(
        FAKE_KEY, manifest_path, vintages_dir=str(tmp_path / "vintages"),
        transport=transport, sleep_fn=lambda s: None,
        monotonic_fn=lambda: 0.0,
        vintage_list=[vd for vd, _ in snaps])
    assert ev["status"] == "FAILED"
    assert calls["n"] == 2                       # stopped at the refusal
    assert ev["failures"][0]["status"] == "FATAL_KEY_INVALID"
    with pytest.raises(ezv.PinnedBytesError):
        ezv.load_pinned_vintages(manifest_path,
                                 vintages_dir=str(tmp_path / "vintages"))


def test_p0b_validate_response_canaries():
    ok = json.loads(_snapshot_payload("2018-03-01",
                                      {"2018-01-01": "101.77"}))
    assert len(ezv.validate_vintage_response("2018-03-01", ok)) == 1
    # fabricated vintage: a row whose window is NOT clamped to VD
    doctored = {"count": 1, "observations": [
        {"realtime_start": "2018-02-15", "realtime_end": "9999-12-31",
         "date": "2018-01-01", "value": "101.77"}]}
    with pytest.raises(ezv.VintageResponseError):
        ezv.validate_vintage_response("2018-03-01", doctored)
    # truncated response (count != observations returned)
    truncated = {"count": 5, "observations": ok["observations"]}
    with pytest.raises(ezv.VintageResponseError):
        ezv.validate_vintage_response("2018-03-01", truncated)
    # non-monthly obs date
    offgrid = {"count": 1, "observations": [
        {"realtime_start": "2018-03-01", "realtime_end": "2018-03-01",
         "date": "2018-01-15", "value": "101.77"}]}
    with pytest.raises(ezv.VintageResponseError):
        ezv.validate_vintage_response("2018-03-01", offgrid)
    # unsorted obs dates
    unsorted = {"count": 2, "observations": [
        {"realtime_start": "2018-03-01", "realtime_end": "2018-03-01",
         "date": "2018-02-01", "value": "103.0"},
        {"realtime_start": "2018-03-01", "realtime_end": "2018-03-01",
         "date": "2018-01-01", "value": "101.77"}]}
    with pytest.raises(ezv.VintageResponseError):
        ezv.validate_vintage_response("2018-03-01", unsorted)


def test_p0b_load_pinned_drift_refuses(tmp_path):
    snaps = _valid_snapshots()
    vdir = tmp_path / "vintages"
    vdir.mkdir()
    files = {}
    for vd, body in snaps:
        (vdir / ezv.vintage_file_name(vd)).write_bytes(body)
        files[vd] = {"file": ezv.vintage_file_name(vd),
                     "sha256": __import__("hashlib").sha256(
                         body).hexdigest(),
                     "bytes": len(body), "observations": 3, "count": 3}
    manifest_path = str(tmp_path / "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump({"schema": ezv.MANIFEST_SCHEMA, "status": "COMPLETE",
                   "vintage_count_planned": len(snaps),
                   "files": files}, fh)
    assert len(ezv.load_pinned_vintages(manifest_path,
                                        vintages_dir=str(vdir))) == 3
    # drift one byte -> verify-on-read refuses
    p = vdir / ezv.vintage_file_name(snaps[0][0])
    p.write_bytes(snaps[0][1] + b" ")
    with pytest.raises(ezv.PinnedBytesError):
        ezv.load_pinned_vintages(manifest_path, vintages_dir=str(vdir))


# --------------------------------------------------------------------------- #
# 9. P0b realtime panel + census law (hand-computed fixtures)
# --------------------------------------------------------------------------- #

def test_p0b_panel_two_vintage_hand_computed():
    panel = ezv.build_realtime_panel([
        ("2018-03-01", json.loads(_snapshot_payload("2018-03-01", {
            "2018-01-01": "101.77", "2018-02-01": ".",
            "2018-03-01": "100.0"}))),
        ("2018-04-01", json.loads(_snapshot_payload("2018-04-01", {
            "2018-01-01": "101.78", "2018-02-01": "103.0",
            "2018-03-01": "100.5"}))),
    ])
    rows = {(r.obs_date, r.realtime_start): r for r in panel["rows"]}
    # hand-computed reconstruction:
    # 2018-01: 101.77 [2018-03-01, 2018-03-31] then 101.78 open
    assert rows[("2018-01-01", "2018-03-01")].realtime_end == "2018-03-31"
    assert rows[("2018-01-01", "2018-03-01")].value == "101.77"
    assert rows[("2018-01-01", "2018-04-01")].realtime_end == "9999-12-31"
    assert rows[("2018-01-01", "2018-04-01")].value == "101.78"
    # 2018-02: "." then 103.0 (first print at the second snapshot)
    assert rows[("2018-02-01", "2018-03-01")].value == "."
    assert rows[("2018-02-01", "2018-04-01")].value == "103.0"
    # 2018-03: 100.0 -> 100.5
    assert rows[("2018-03-01", "2018-04-01")].value == "100.5"
    assert panel["rows_count"] == 6 and panel["versions"] == 6
    assert panel["value_changes"] == 3

    stream = rs.build_restricted_stream(
        "EZ", panel["rows"], window=("2018-01-01", "2018-12-31"))
    events = {e.obs_month: e for e in stream["events_all"]}
    # hand-computed events: two v1->v2 gaps with differing values
    assert set(events) == {"2018-01-01", "2018-03-01"}
    e1, e3 = events["2018-01-01"], events["2018-03-01"]
    assert e1.v1_value == "101.77" and e1.v2_value == "101.78"
    assert e1.ratio == pytest.approx(0.01 / 101.77)
    assert e1.first_print_in_realtime_era is False   # obs < era start
    assert e3.v1_value == "100.0" and e3.v2_value == "100.5"
    assert e3.ratio == pytest.approx(0.005)
    assert e3.first_print_in_realtime_era is True    # obs >= era start
    assert e3.v2_realtime_start == "2018-04-01"      # availability day
    # restricted stream: era-eligible, non-bulk, S0-window-usable
    assert len(stream["restricted"]) == 1
    assert stream["restricted"][0].obs_month == "2018-03-01"
    # fabricated month canary
    assert rs.lookup_restricted(
        {"EZ": stream["restricted"]}, "EZ", "2018-06-01")["found"] is False


def test_p0b_panel_value_flip_makes_three_versions():
    panel = ezv.build_realtime_panel([
        ("2018-03-01", json.loads(_snapshot_payload("2018-03-01",
                                                    {"2018-01-01": "10.0"}))),
        ("2018-04-01", json.loads(_snapshot_payload("2018-04-01",
                                                    {"2018-01-01": "10.5"}))),
        ("2018-05-01", json.loads(_snapshot_payload("2018-05-01",
                                                    {"2018-01-01": "10.0"}))),
    ])
    versions = sorted(panel["rows"], key=lambda r: r.realtime_start)
    assert [(v.realtime_start, v.realtime_end, v.value) for v in versions] == [
        ("2018-03-01", "2018-03-31", "10.0"),
        ("2018-04-01", "2018-04-30", "10.5"),
        ("2018-05-01", "9999-12-31", "10.0")]
    # the first-to-second-version event is 10.0 -> 10.5 (ratio 0.05)
    stream = rs.build_restricted_stream(
        "EZ", panel["rows"], window=("2018-01-01", "2018-12-31"))
    assert len(stream["events_all"]) == 1
    assert stream["events_all"][0].ratio == pytest.approx(0.05)


def test_p0b_realtime_window_law_monotonicity_fail_closed():
    # realtime-window law: conflicting vintages with the SAME
    # realtime_start (a same-day correction) raise and NOTHING is built
    rows = [
        pa.VintageRow(obs_date="2020-01-01", realtime_start="2020-02-15",
                      realtime_end="2020-03-14", value="104.0"),
        pa.VintageRow(obs_date="2020-01-01", realtime_start="2020-02-15",
                      realtime_end="2020-03-20", value="104.5"),
        pa.VintageRow(obs_date="2020-01-01", realtime_start="2020-03-15",
                      realtime_end="9999-12-31", value="104.6"),
    ]
    with pytest.raises(ng2.VintageMonotonicityError):
        rs.build_restricted_stream("EZ", rows)


def test_p0b_panel_refuses_fabricated_vintage_payloads():
    doctored = ("2018-04-01", {"count": 1, "observations": [
        {"realtime_start": "2018-04-01", "realtime_end": "2018-04-01",
         "date": "2018-01-01", "value": "101.78"},
        # a row whose window is NOT clamped to the snapshot day
        {"realtime_start": "2018-02-15", "realtime_end": "9999-12-31",
         "date": "2018-02-01", "value": "103.0"}]})
    with pytest.raises(ezv.VintageResponseError):
        ezv.build_realtime_panel([doctored])


def _mk_event(economy, obs_month, ratio):
    return ng2.RevisionEvent(
        economy=economy, obs_month=obs_month,
        v1_realtime_start="2018-06-01", v1_realtime_end="2018-06-30",
        v1_value="100.0", v2_realtime_start="2018-07-01",
        v2_realtime_end="9999-12-31", v2_value="100.5", ratio=ratio,
        first_print_in_realtime_era=True)


def test_p0b_ez_us_differential_join_hand_computed():
    ez_events = [_mk_event("EZ", "2018-05-01", 0.001),
                 _mk_event("EZ", "2018-06-01", 0.002),
                 _mk_event("EZ", "2019-01-01", 0.003)]
    us_events = [_mk_event("US", "2018-06-01", 0.004),
                 _mk_event("US", "2019-01-01", 0.005),
                 _mk_event("US", "2019-02-01", 0.006)]
    diff = ezv.ez_us_differential_months(ez_events, us_events)
    assert diff["differential_months"] == ["2018-06", "2019-01"]
    assert diff["total"] == 2


# --------------------------------------------------------------------------- #
# 10. P0c wide-window pull (A7-F1 remediation): query shape, paging,
#     pure merge + pure adapter, pin/verify-on-read, era comparison
# --------------------------------------------------------------------------- #

from research.assets.forex_ng4 import wide_pull as wp          # noqa: E402


def test_p0c_wide_query_shape_matches_the_a7_prescription():
    # realtime_start must predate the committed V8 earliest-vintage
    # bound 2015-02-27 so the pull captures the archive from its
    # true beginning; realtime_end open
    assert wp.WIDE_REALTIME_START <= "2015-02-27"
    assert wp.WIDE_REALTIME_START == "2015-01-01"
    assert wp.WIDE_REALTIME_END == "9999-12-31"
    assert wp.PAGE_LIMIT == 1000


def _wide_obs(date, rs_, re_, value):
    return {"date": date, "realtime_start": rs_, "realtime_end": re_,
            "value": value}


def _wide_page_payload(offset, observations, count=None, limit=None):
    return {"realtime_start": wp.WIDE_REALTIME_START,
            "realtime_end": wp.WIDE_REALTIME_END,
            "count": count if count is not None else offset + len(
                observations),
            "limit": limit if limit is not None else wp.PAGE_LIMIT,
            "offset": offset,
            "observations": observations}


#: hand-computed true-archive mini-world (5 obs months, true windows):
#: the 2015-01 print (2015-02-27) is the archive clock zero; the three
#: early months revise together at the 2019-03-20 re-publication.
_WIDE_TRUTH = [
    _wide_obs("2015-01-01", "2015-02-27", "2019-03-19", "99.0"),
    _wide_obs("2015-01-01", "2019-03-20", "9999-12-31", "99.4"),
    _wide_obs("2015-03-01", "2015-04-15", "2019-03-19", "100.0"),
    _wide_obs("2015-03-01", "2019-03-20", "9999-12-31", "100.5"),
    _wide_obs("2015-04-01", "2015-05-15", "2019-03-19", "100.8"),
    _wide_obs("2015-04-01", "2019-03-20", "9999-12-31", "101.1"),
    _wide_obs("2018-05-01", "2018-06-15", "2018-07-15", "102.0"),
    _wide_obs("2018-05-01", "2018-07-16", "9999-12-31", "102.3"),
    _wide_obs("2018-08-01", "2018-09-15", "2019-03-19", "103.0"),
    _wide_obs("2018-08-01", "2019-03-20", "9999-12-31", "103.2"),
]


def _wide_fixture_payload():
    return _wide_page_payload(0, list(_WIDE_TRUTH), count=10)


def test_p0c_adapter_hand_computed(tmp_path):
    path = _w(f"{TEST_ROOT}/wide/wide_window.json", _wide_fixture_payload())
    with open(path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    rows = wp.validate_wide_response(payload)
    # exact hand-computed VintageRows (the pure input adapter)
    assert [(r.obs_date, r.realtime_start, r.realtime_end, r.value)
            for r in rows] == [
        (r["date"], r["realtime_start"], r["realtime_end"], r["value"])
        for r in _WIDE_TRUTH]
    stats = wp.open_version_stat(rows)
    assert stats["open_version_rows"] == 5    # one open version per month


def test_p0c_adapter_refuses_wrong_shapes():
    # as-of CLAMPED shape (all rows one single day) = wrong query shape
    clamped = _wide_page_payload(0, [
        _wide_obs("2018-01-01", "2018-03-01", "2018-03-01", "101.77")],
        count=1)
    with pytest.raises(wp.WideResponseError):
        wp.validate_wide_response(clamped)
    # truncated response (count != observations)
    truncated = _wide_page_payload(0, list(_WIDE_TRUTH), count=99)
    with pytest.raises(wp.WideResponseError):
        wp.validate_wide_response(truncated)
    # non-monthly obs date
    offgrid = _wide_page_payload(0, [
        _wide_obs("2018-01-15", "2018-02-15", "9999-12-31", "101.0")],
        count=1)
    with pytest.raises(wp.WideResponseError):
        wp.validate_wide_response(offgrid)
    # invalid realtime window
    bad_window = _wide_page_payload(0, [
        _wide_obs("2018-01-01", "2018-03-15", "2018-02-01", "101.0")],
        count=1)
    with pytest.raises(wp.WideResponseError):
        wp.validate_wide_response(bad_window)
    # current-vintage table (no realtime keys) refuses structurally
    with pytest.raises(pa.VintageStructureError):
        wp.validate_wide_response({"count": 1, "observations": [
            {"date": "2018-01-01", "value": "101.0"}]})


def test_p0c_merge_pages_hand_computed():
    pages = [
        _wide_page_payload(0, _WIDE_TRUTH[:3], count=10, limit=3),
        _wide_page_payload(3, _WIDE_TRUTH[3:6], count=10, limit=3),
        _wide_page_payload(6, _WIDE_TRUTH[6:9], count=10, limit=3),
        _wide_page_payload(9, _WIDE_TRUTH[9:], count=10, limit=3),
    ]
    merged = wp.merge_wide_pages(pages, limit=3)
    assert merged["count"] == 10 == len(merged["observations"])
    assert merged["observations"] == list(_WIDE_TRUTH)
    # deterministic serialization round-trips
    again = wp.serialize_merged(
        json.loads(wp.serialize_merged(merged).decode("utf-8")))
    assert again == wp.serialize_merged(merged)
    # declared count changing across pages refuses
    with pytest.raises(wp.WideResponseError):
        wp.merge_wide_pages([pages[0], dict(pages[1], count=11)], limit=3)
    # offset gap refuses
    with pytest.raises(wp.WideResponseError):
        wp.merge_wide_pages([pages[0], dict(pages[1], offset=2)], limit=3)
    # merged total != declared count refuses (truncation/missing pages)
    with pytest.raises(wp.WideResponseError):
        wp.merge_wide_pages([pages[0], pages[1]], limit=3)


def test_p0c_fetch_paging_pacing_and_evidence_hygiene():
    obs = [_wide_obs(f"2018-{m:02d}-01", f"2018-{m:02d}-15",
                     "9999-12-31", "100.0") for m in range(1, 6)]
    full = json.dumps(_wide_page_payload(0, obs[:3], count=5,
                                         limit=3)).encode()
    last = json.dumps(_wide_page_payload(3, obs[3:], count=5,
                                         limit=3)).encode()
    seen_urls, sleeps, mono = [], [], {"t": 0.0}

    def transport(url, timeout=30):
        seen_urls.append(url)
        return _Resp(full if len(seen_urls) == 1 else last)

    ev = wp.fetch_wide_window(
        FAKE_KEY, transport=transport, sleep_fn=sleeps.append,
        monotonic_fn=lambda: mono["t"], limit=3)
    assert ev["status"] == "COMPLETE"
    assert ev["rows_total"] == 5 and ev["count_declared"] == 5
    assert len(ev["pages"]) == 2                       # paged, then short
    assert sleeps == [1.2]                             # inter-page pacing
    assert "api_key=" + FAKE_KEY in seen_urls[0]       # the real URL keys it
    assert "realtime_start=2015-01-01" in seen_urls[0]
    assert "realtime_end=9999-12-31" in seen_urls[0]
    blob = json.dumps({k: v for k, v in ev.items()
                       if k != "page_payloads"}, default=repr)
    assert FAKE_KEY not in blob                        # evidence never does
    assert len(ev["page_payloads"]) == 2


def test_p0c_fetch_backoff_retry_then_ok():
    obs = [_wide_obs("2018-01-01", "2018-02-15", "9999-12-31", "100.0")]
    body = json.dumps(_wide_page_payload(0, obs, count=1, limit=3)).encode()
    import io
    import urllib.error
    calls = {"n": 0}
    sleeps = []

    def transport(url, timeout=30):
        calls["n"] += 1
        if calls["n"] <= 2:
            raise urllib.error.HTTPError(
                url, 500, "Server Error", {}, io.BytesIO(b"{}"))
        return _Resp(body)

    ev = wp.fetch_wide_window(
        FAKE_KEY, transport=transport, sleep_fn=sleeps.append,
        monotonic_fn=lambda: 0.0, limit=3)
    assert ev["status"] == "COMPLETE"
    assert [a["outcome"] for a in ev["pages"][0]["attempts"]] == \
        ["http_error", "http_error", "responded"]
    assert sleeps[:2] == [2.0, 4.0]                    # exponential backoff


def test_p0c_fetch_key_invalid_fatal_stops_fail_closed():
    import io
    import urllib.error
    err = json.dumps({
        "error_code": 400,
        "error_message": "The value for api_key is invalid. You must "
                         "register for a key."}).encode()
    calls = {"n": 0}

    def transport(url, timeout=30):
        calls["n"] += 1
        raise urllib.error.HTTPError(
            url, 400, "Bad Request", {}, io.BytesIO(err))

    ev = wp.fetch_wide_window(
        FAKE_KEY, transport=transport, sleep_fn=lambda s: None,
        monotonic_fn=lambda: 0.0)
    assert ev["status"] == "FATAL_KEY_INVALID"
    assert calls["n"] == 1                    # deterministic refusal: no retry
    assert FAKE_KEY not in json.dumps(
        {k: v for k, v in ev.items() if k != "page_payloads"})


def test_p0c_fetch_no_key_refuses_without_call():
    def transport(url, timeout=30):
        pytest.fail("no network call may happen without a key")

    ev = wp.fetch_wide_window(None, transport=transport,
                              sleep_fn=lambda s: None)
    assert ev["status"] == "FATAL_NO_KEY"
    assert ev["pages"][0]["status"] == "FATAL_NO_KEY"
    assert ev["pages"][0]["attempts"] == []


def test_p0c_pin_roundtrip_and_drift_refuses(tmp_path):
    pages = [
        _wide_page_payload(0, _WIDE_TRUTH[:6], count=10, limit=6),
        _wide_page_payload(6, _WIDE_TRUTH[6:], count=10, limit=6),
    ]
    raw_pages = [json.dumps(p).encode() for p in pages]
    pin_dir = str(tmp_path / "ez")
    manifest_path = str(tmp_path / "manifest.json")
    manifest = wp.pin_wide_window(raw_pages, manifest_path, pin_dir=pin_dir)
    assert manifest["status"] == "COMPLETE"
    assert manifest["merged"]["observations"] == 10
    payload, rows = wp.load_pinned_wide(manifest_path, pin_dir=pin_dir)
    assert len(rows) == 10
    # drift the merged document -> verify-on-read refuses
    wide_path = os.path.join(pin_dir, wp.WIDE_FILE_NAME)
    with open(wide_path, "wb") as fh:
        fh.write(wp.serialize_merged(payload)[:-1] + b" \n")
    with pytest.raises(wp.PinnedWideBytesError):
        wp.load_pinned_wide(manifest_path, pin_dir=pin_dir)
    # drift a page -> refuses
    wp.pin_wide_window(raw_pages, manifest_path, pin_dir=pin_dir)
    page_path = os.path.join(pin_dir, wp.PAGES_DIR_NAME, "page_000.json")
    with open(page_path, "wb") as fh:
        fh.write(raw_pages[0] + b" ")
    with pytest.raises(wp.PinnedWideBytesError):
        wp.load_pinned_wide(manifest_path, pin_dir=pin_dir)
    # doctored merged document whose sha is ALSO updated in the manifest
    # (both drift together) still refuses: merged must BE merge(pages)
    wp.pin_wide_window(raw_pages, manifest_path, pin_dir=pin_dir)
    doctored = _wide_page_payload(0, list(_WIDE_TRUTH), count=10)
    doctored["observations"][0]["value"] = "999.9"
    doctored_bytes = wp.serialize_merged(doctored)
    with open(wide_path, "wb") as fh:
        fh.write(doctored_bytes)
    with open(manifest_path, "r", encoding="utf-8") as fh:
        m = json.load(fh)
    m["merged"]["sha256"] = __import__("hashlib").sha256(
        doctored_bytes).hexdigest()
    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(m, fh)
    with pytest.raises(wp.PinnedWideBytesError):
        wp.load_pinned_wide(manifest_path, pin_dir=pin_dir)


def test_p0c_era_comparison_wide_vs_clamped_hand_computed():
    """The A7-F1 mechanism on one hand-computed mini-world: the SAME
    truth measured under the two query shapes.  Wide TRUE windows:
    era start = the archive clock zero (2015-02-27); the as-of
    CLAMPED snapshots of the same truth: era start = the first
    snapshot day (2018-07-01) -- the pre-snapshot cohort (2015-03,
    2015-04) is era-excluded by the frozen law, an ingest-shape
    artifact, never feed truth."""
    window = ("2018-01-01", "2019-12-31")

    # wide basis: true-window rows fed UNMODIFIED to the machinery
    wide_rows = wp.validate_wide_response(_wide_fixture_payload())
    wide = rs.build_restricted_stream("EZ", wide_rows, window=window)
    wide_era = min(r.realtime_start for r in wide_rows)
    wide_months = sorted(e.obs_month for e in wide["restricted"])
    assert wide_era == "2015-02-27"
    assert wide["events_all_count"] == 5          # every month v1->v2
    assert wide["report"]["usable_events"] == 5   # v2 days inside window
    assert wide["report"]["first_print_era_events"] == 4   # 2015-01 backfill
    assert len(wide["restricted"]) == 4
    assert wide_months == ["2015-03-01", "2015-04-01", "2018-05-01",
                           "2018-08-01"]

    # clamped basis: monthly 1st-of-month as-of snapshots of the SAME
    # truth (values in force at each snapshot day)
    snapshots = [
        ("2018-07-01", _snapshot_payload("2018-07-01", {
            "2015-01-01": "99.0", "2015-03-01": "100.0",
            "2015-04-01": "100.8", "2018-05-01": "102.0"})),
        ("2018-10-01", _snapshot_payload("2018-10-01", {
            "2015-01-01": "99.0", "2015-03-01": "100.0",
            "2015-04-01": "100.8", "2018-05-01": "102.3",
            "2018-08-01": "103.0"})),
        ("2019-04-01", _snapshot_payload("2019-04-01", {
            "2015-01-01": "99.4", "2015-03-01": "100.5",
            "2015-04-01": "101.1", "2018-05-01": "102.3",
            "2018-08-01": "103.2"})),
        ("2019-05-01", _snapshot_payload("2019-05-01", {
            "2015-01-01": "99.4", "2015-03-01": "100.5",
            "2015-04-01": "101.1", "2018-05-01": "102.3",
            "2018-08-01": "103.2"})),
    ]
    panel = ezv.build_realtime_panel(
        [(vd, json.loads(body)) for vd, body in snapshots])
    clamped = rs.build_restricted_stream("EZ", panel["rows"],
                                         window=window)
    clamped_era = min(r.realtime_start for r in panel["rows"])
    clamped_months = sorted(e.obs_month for e in clamped["restricted"])
    assert clamped_era == "2018-07-01"           # the first snapshot day
    assert clamped["events_all_count"] == 5      # same five transitions
    assert clamped["report"]["first_print_era_events"] == 1
    assert len(clamped["restricted"]) == 1       # ONLY the post-snapshot
    assert clamped_months == ["2018-08-01"]      # first print survives

    # the cohort analog: restricted on wide, era-excluded on clamped
    cohort = ("2015-03-01", "2015-04-01")
    assert all(m in wide_months for m in cohort)
    assert all(m not in clamped_months for m in cohort)
    # and the archive clock zero itself is the mechanism, not the feed
    assert wide_era < clamped_era

