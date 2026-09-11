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
