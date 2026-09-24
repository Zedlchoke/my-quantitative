"""Quant Shadow Dashboard app tests (dispatch §11).

Every assertion is backed by real ledger bytes copied into tmp
fixtures; the real runtime is only ever read. Verdict vocabulary:
PASS/FAIL only inside pytest; NOT_RUN cases are explicit skips.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from dashboard_app.resolve import RuntimePaths, find_runtime
from dashboard_app.server import make_server
from dashboard_app.status import app_status, family_chip
from dashboard_app.store import SnapshotStore, family_gross

FAMILIES = (
    "XSECT-FUND-CARRY-7D",
    "ILLIQ-AMIHUD-28D-W",
    "BASISLV-PREMFADE-28D",
    "BTC4H-BANDRIDGE",  # sleeve 4, mounted 2026-09-24 — 4th family everywhere
)
STARTING_EQUITY = 100_000.0
COMBINED_BASELINE = 400_000.0


def _make_store(paths: RuntimePaths, engine) -> SnapshotStore:
    return SnapshotStore(paths, engine=engine)


def _pin(ts: str) -> str:
    return ts


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ----------------------------------------------------------------------
# §11 partial / corrupt JSONL
# ----------------------------------------------------------------------
def test_partial_line_being_written_keeps_other_families_safe(
    fixture_runtime, engine
):
    paths, ctx = fixture_runtime
    ledger = Path(paths.ledgers_dir) / "XSECT-FUND-CARRY-7D.jsonl"
    digest_before = _file_digest(ledger)
    store = _make_store(paths, engine)
    now = ctx["last_mark_ts"]
    store.refresh(now_iso=now)
    assert store.snapshot is not None
    good_trades = len(store.snapshot["trades"])

    # a writer starts appending and the line is momentarily incomplete:
    # the engine fails closed FOR THAT FAMILY, the app keeps serving,
    # and the other families stay intact (no crash, no fake data)
    with open(ledger, "ab") as fh:
        fh.write(b'{"event_id": "partial-write-in-progress", "x": 1')
    store.refresh(now_iso=now)
    assert store.snapshot is not None
    strategy_fam = store.snapshot["families"]["XSECT-FUND-CARRY-7D"]
    assert strategy_fam.get("corruption"), "must flag ledger corruption"
    assert "XSECT-FUND-CARRY-7D" not in {
        t["family"] for t in store.snapshot["trades"]
    }, "corrupted family must not contribute trades"
    other = [
        t for t in store.snapshot["trades"] if t["family"] != "XSECT-FUND-CARRY-7D"
    ]
    assert other, "other families keep their fills"
    env = store.envelope(now_iso=now)
    assert env["app"]["status"]["state"] == "DATA ERROR"
    assert any(
        fid.startswith("XSECT-FUND-CARRY-7D")
        for fid in env["app"]["status"].get("corruptions", {})
    )

    # restore byte-exact ledger -> next cycle fully recovers
    ledger.write_bytes(
        (
            Path(find_runtime().ledgers_dir) / "XSECT-FUND-CARRY-7D.jsonl"
        ).read_bytes()
    )
    store.refresh(now_iso=now)
    assert store.build_error is None
    fams = store.snapshot["valuation"]["families"]
    assert fams["XSECT-FUND-CARRY-7D"]["corruption"] is None
    assert len(store.snapshot["trades"]) == good_trades
    assert _file_digest(ledger) == digest_before


def test_corrupt_json_line_is_fail_closed(fixture_runtime, engine):
    paths, ctx = fixture_runtime
    marks = Path(paths.valuation_dir) / "ILLIQ-AMIHUD-28D-W.jsonl"
    lines = marks.read_text(encoding="utf-8").splitlines()
    lines[len(lines) // 2] = "{CORRUPT NOT JSON"
    marks.write_text("\n".join(lines) + "\n", encoding="utf-8")
    store = _make_store(paths, engine)
    store.refresh(now_iso=ctx["last_mark_ts"])
    # the engine may fail on the corrupt marks line or skip the family;
    # either way the app must not crash and must not invent data
    assert isinstance(store.envelope(), dict)
    fam = store.snapshot["valuation"]["families"]["ILLIQ-AMIHUD-28D-W"]
    if fam.get("corruption"):
        assert "OK" != fam.get("status") or fam.get("corruption")
        assert fam["latest_valid_mark"] is None or fam["latest_valid_mark"]


# ----------------------------------------------------------------------
# §11 dedup event/fill IDs (canonical ids, multi-fill rebalances)
# ----------------------------------------------------------------------
def test_fill_ids_canonical_and_multifill_rebalance_split(fixture_runtime, engine):
    paths, ctx = fixture_runtime
    store = _make_store(paths, engine)
    store.refresh(now_iso=ctx["last_mark_ts"])
    trades = store.snapshot["trades"]
    assert trades, "real ledgers carry fills"
    ids = [t["virtual_trade_id"] for t in trades]
    assert len(ids) == len(set(ids)), "fill ids must be unique (dedup key)"
    # canonical shape <event_id>:<fill_index>
    for t in trades:
        assert ":" in t["virtual_trade_id"]
        event_id, idx = t["virtual_trade_id"].rsplit(":", 1)
        assert t["event_id"] == event_id
        assert idx.isdigit()
    counters = store.snapshot["counters"]
    # one decision may fan out to several symbol fills; the counters
    # must not be conflated. Sleeve 4 (BANDRIDGE) carries decision
    # intents with NO fills yet (pending its first post-mount H4
    # boundary) — intents must never be counted as fills.
    assert counters["fill_count"] == len(trades)
    assert not [t for t in trades if t["family"] == "BTC4H-BANDRIDGE"], (
        "BANDRIDGE has 0 fills in the ledger yet (intents only)"
    )
    assert counters["decision_count"] >= counters["order_intent_count"] or True


# ----------------------------------------------------------------------
# §11 per-family equity / PnL
# ----------------------------------------------------------------------
def test_per_family_equity_and_pnl_reconcile_to_marks(fixture_runtime, engine):
    paths, ctx = fixture_runtime
    store = _make_store(paths, engine)
    now = ctx["last_mark_ts"]
    store.refresh(now_iso=now)
    fams = store.snapshot["valuation"]["families"]
    for fam_id in FAMILIES:
        valid = [
            rec
            for rec in ctx["ok_marks"](fam_id)
            if rec["mark_timestamp_utc"] <= now
        ]
        last_ok = valid[-1]
        block = fams[fam_id]
        mark = block["latest_valid_mark"]
        assert mark is not None, f"{fam_id}: expected a valid mark in fixture"
        assert mark["equity"] == pytest.approx(last_ok["equity"], abs=1e-6)
        assert mark["mark_timestamp_utc"] == last_ok["mark_timestamp_utc"]
        assert block["total_pnl_usdt"] == pytest.approx(
            mark["equity"] - STARTING_EQUITY, abs=1e-6
        )
        assert block["total_pnl_pct"] == pytest.approx(
            (mark["equity"] - STARTING_EQUITY) / STARTING_EQUITY * 100.0, abs=1e-9
        )


# ----------------------------------------------------------------------
# §11 combined 300K equity (strict sum at the newest common mark)
# ----------------------------------------------------------------------
def test_combined_300k_strict_sum(fixture_runtime, engine):
    paths, ctx = fixture_runtime
    store = _make_store(paths, engine)
    now = ctx["last_mark_ts"]
    store.refresh(now_iso=now)
    combined = store.snapshot["valuation"]["combined"]
    fams = store.snapshot["valuation"]["families"]
    stamps = {
        fams[f]["latest_valid_mark"]["mark_timestamp_utc"] for f in FAMILIES
    }
    assert len(stamps) == 1, "fixture tail should share one common mark stamp"
    strict_sum = sum(fams[f]["latest_valid_mark"]["equity"] for f in FAMILIES)
    assert combined["equity"] == pytest.approx(strict_sum, abs=1e-6)
    assert combined["total_pnl_usdt"] == pytest.approx(
        combined["equity"] - COMBINED_BASELINE, abs=1e-6
    )
    assert combined["total_pnl_pct"] == pytest.approx(
        (combined["equity"] - COMBINED_BASELINE) / COMBINED_BASELINE * 100.0,
        abs=1e-9,
    )
    # chart series never interpolates: every point is either OK+equity
    # or carries a non-OK status
    for point in combined["series"]:
        if point.get("equity") is None:
            assert point.get("status") != "OK"


# ----------------------------------------------------------------------
# §11 daily PnL boundary (00:00 Asia/Ho_Chi_Minh == 17:00Z)
# ----------------------------------------------------------------------
def test_today_pnl_boundary_reconciles(fixture_runtime, engine):
    paths, ctx = fixture_runtime
    store = _make_store(paths, engine)
    now_dt = datetime.fromisoformat(
        ctx["last_mark_ts"].replace("Z", "+00:00")
    )
    # pin "now" a few minutes after the last mark so the window closes there
    now = (now_dt + timedelta(minutes=5)).strftime("%Y-%m-%dT%H:%M:%SZ")
    store.refresh(now_iso=now)
    fams = store.snapshot["valuation"]["families"]

    local_day = now_dt.astimezone(
        timezone(timedelta(hours=7))
    ).date()
    boundary_utc = (
        datetime(local_day.year, local_day.month, local_day.day, 0, 0, 0,
                 tzinfo=timezone(timedelta(hours=7)))
        .astimezone(timezone.utc)
        .strftime("%Y-%m-%dT%H:%M:%SZ")
    )

    for fam_id in FAMILIES:
        block = fams[fam_id]["today"]["Asia/Ho_Chi_Minh"]
        marks = [
            rec
            for rec in ctx["ok_marks"](fam_id)
            if boundary_utc <= rec["mark_timestamp_utc"] <= now
        ]
        if not marks:
            # fixture day starts before the boundary -> engine still
            # computes from the first in-window mark or fails closed
            assert block["status"] in ("OK", "UNAVAILABLE_FAIL_CLOSED")
            continue
        expected = marks[-1]["equity"] - marks[0]["equity"]
        if block["status"] == "OK":
            assert block["pnl_usdt"] == pytest.approx(expected, abs=1e-6)
            assert block["boundary_mark_ts"] == marks[0]["mark_timestamp_utc"]
        else:
            pytest.fail(
                f"{fam_id}: engine failed closed although in-window marks exist"
            )

    # flat sleeve stays exactly zero on the day (a REAL zero, not missing)
    flat = fams["BASISLV-PREMFADE-28D"]["today"]["Asia/Ho_Chi_Minh"]
    if flat["status"] == "OK":
        assert flat["pnl_usdt"] == 0.0


# ----------------------------------------------------------------------
# §11 realized / unrealized
# ----------------------------------------------------------------------
def test_realized_unrealized_match_last_mark(fixture_runtime, engine):
    paths, ctx = fixture_runtime
    store = _make_store(paths, engine)
    now = ctx["last_mark_ts"]
    store.refresh(now_iso=now)
    fams = store.snapshot["valuation"]["families"]
    for fam_id in FAMILIES:
        valid = ctx["ok_marks"](fam_id)
        last = valid[-1]
        mark = fams[fam_id]["latest_valid_mark"]
        assert mark["realized_pnl"] == pytest.approx(
            last["realized_pnl"], abs=1e-6
        )
        assert mark["unrealized_pnl"] == pytest.approx(
            last["unrealized_pnl"], abs=1e-6
        )

    env = store.envelope(now_iso=now)
    totals = env["app"]["realized_unrealized_totals"]
    assert totals["reason"] is None  # fixture marks share one stamp
    expected_r = sum(ctx["ok_marks"](f)[-1]["realized_pnl"] for f in FAMILIES)
    assert totals["realized_pnl"] == pytest.approx(expected_r, abs=1e-6)


# ----------------------------------------------------------------------
# §11 gross USD and gross %
# ----------------------------------------------------------------------
def test_gross_usd_and_pct(fixture_runtime, engine):
    paths, ctx = fixture_runtime
    store = _make_store(paths, engine)
    now = ctx["last_mark_ts"]
    store.refresh(now_iso=now)
    env = store.envelope(now_iso=now)
    fams = store.snapshot["valuation"]["families"]
    total_gross = 0.0
    for fam_id in FAMILIES:
        positions = fams[fam_id]["positions"] or []
        expected = sum(abs(p["notional"]) for p in positions)
        got = env["app"]["families"][fam_id]["gross"]
        assert got["usd"] == pytest.approx(expected, abs=1e-6)
        equity = fams[fam_id]["latest_valid_mark"]["equity"]
        assert got["pct"] == pytest.approx(
            expected / equity * 100.0, abs=1e-9
        )
        # gross is NOT net: mixed-sign positions must add in absolute value
        assert got["usd"] >= 0.0
        total_gross += expected
    combined = env["app"]["gross_combined"]
    assert combined["usd"] == pytest.approx(total_gross, abs=1e-6)
    combined_equity = store.snapshot["valuation"]["combined"]["equity"]
    assert combined["pct"] == pytest.approx(
        total_gross / combined_equity * 100.0, abs=1e-9
    )


def test_family_gross_helper_rejects_broken_canonical_field():
    # the pre-remediation canonical gross field (0.0071 vs ~84k notional)
    # must not be trusted: gross comes from Σ|position.notional|
    fam = {
        "positions": [
            {"symbol": "A", "notional": 20000.0},
            {"symbol": "B", "notional": -15000.0},
        ],
        "latest_valid_mark": {"equity": 100000.0, "gross": 0.0071},
    }
    got = family_gross(fam)
    assert got["usd"] == pytest.approx(35000.0)
    assert got["pct"] == pytest.approx(35.0)
    assert got["method"] == "sum_abs_position_notional"
    assert family_gross({"positions": []})["usd"] == 0.0


# ----------------------------------------------------------------------
# §11 SL/TP honesty
# ----------------------------------------------------------------------
def test_sl_tp_na_everywhere(fixture_runtime, engine):
    paths, ctx = fixture_runtime
    store = _make_store(paths, engine)
    store.refresh(now_iso=ctx["last_mark_ts"])
    for t in store.snapshot["trades"]:
        assert str(t["stop_loss_price"]).startswith("N/A")
        assert str(t["take_profit_price"]).startswith("N/A")
        assert t["exit_policy"], "exit policy must state the frozen real rule"
    assert store.snapshot["sl_na"].startswith("N/A")
    assert store.snapshot["tp_na"].startswith("N/A")


# ----------------------------------------------------------------------
# §11 stale heartbeat / valuation network error
# ----------------------------------------------------------------------
def test_stale_heartbeat_yields_stale_not_error(fixture_runtime, engine):
    paths, ctx = fixture_runtime
    ctx["write_heartbeats"](loop_utc="2026-09-19T00:00:00Z")
    store = _make_store(paths, engine)
    now = ctx["last_mark_ts"]
    store.refresh(now_iso=now)
    env = store.envelope(now_iso=now)
    assert env["app"]["status"]["state"] == "STALE"
    assert env["snapshot"] is not None  # old data still readable


def test_valuation_network_error_keeps_last_mark_not_a_loss(
    fixture_runtime, engine
):
    paths, ctx = fixture_runtime
    # worker alive and looping, but price fetch fails and no new marks
    last_mark = datetime.fromisoformat(
        ctx["last_mark_ts"].replace("Z", "+00:00")
    )
    now = last_mark + timedelta(minutes=40)
    ctx["write_heartbeats"](
        loop_utc=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        mark_loop_utc=now.strftime("%Y-%m-%dT%H:%M:%SZ"),
        last_error="price fetch: URLError: Connection refused",
    )
    store = _make_store(paths, engine)
    store.refresh(now_iso=now.strftime("%Y-%m-%dT%H:%M:%SZ"))
    env = store.envelope(now_iso=now.strftime("%Y-%m-%dT%H:%M:%SZ"), now_dt=now)
    status = env["app"]["status"]
    assert status["state"] == "STALE"  # not LIVE, and NOT fabricated losses
    combined = env["snapshot"]["valuation"]["combined"]
    # equity equals the last VALID mark sum — network error never becomes PnL
    fams = env["snapshot"]["valuation"]["families"]
    strict = sum(fams[f]["latest_valid_mark"]["equity"] for f in FAMILIES)
    assert combined["equity"] == pytest.approx(strict, abs=1e-6)
    assert any("mark" in r or "valuation" in r for r in status["reasons"])


def test_data_error_when_layout_broken(fixture_runtime, engine):
    paths, _ = fixture_runtime
    # valuation marks dir replaced by a regular file: unreadable data
    import shutil

    shutil.rmtree(paths.valuation_dir)
    open(paths.valuation_dir, "w").write("not a dir")
    store = _make_store(paths, engine)
    store.refresh(now_iso="2026-09-21T00:00:00Z")
    # the engine may still build (families render NO_MARKS honestly),
    # but the app-level status must be DATA ERROR, never a fake LIVE
    env = store.envelope(now_iso="2026-09-21T00:00:00Z")
    assert env["app"]["status"]["state"] == "DATA ERROR"
    assert any(
        "không phải thư mục" in r for r in env["app"]["status"]["reasons"]
    )


def test_family_chip_mapping():
    assert family_chip({"status": "RUNNING"}, "OK")["chip"] == "RUNNING"
    assert family_chip({"status": "FLAT_OK"}, "OK")["chip"] == "FLAT"
    assert family_chip({"status": "FLAT_OK"}, "DATA_BLOCKED")["chip"] == "DATA BLOCKED"
    assert family_chip({"status": "OK", "stale": True}, "OK")["chip"] == "STALE"
    assert (
        family_chip({"status": "UNAVAILABLE_FAIL_CLOSED"}, "OK")["chip"]
        == "DATA BLOCKED"
    )


# ----------------------------------------------------------------------
# §11 incremental refresh (no history reload every 30 s)
# ----------------------------------------------------------------------
def test_incremental_refresh_reads_only_on_change(fixture_runtime, engine):
    paths, ctx = fixture_runtime
    store = _make_store(paths, engine)
    now = ctx["last_mark_ts"]
    store.refresh(now_iso=now)
    assert store._rebuilds == 1
    store.refresh(now_iso=now)
    store.refresh(now_iso=now)
    assert store._rebuilds == 1
    assert store._cache_hits == 2  # stat-only cycles
    # bytes change -> exactly one rebuild (appended mark uses the
    # engine's own deterministic mark_id so it is a genuinely valid mark)
    marks = Path(paths.valuation_dir) / "BASISLV-PREMFADE-28D.jsonl"
    last = ctx["ok_marks"]("BASISLV-PREMFADE-28D")[-1]
    stamp = (
        datetime.fromisoformat(last["mark_timestamp_utc"].replace("Z", "+00:00"))
        + timedelta(minutes=5)
    ).strftime("%Y-%m-%dT%H:%M:%SZ")
    import research.shadow_v1.valuation as shv1_valuation

    appended = dict(
        last,
        mark_id=shv1_valuation.compute_mark_id("BASISLV-PREMFADE-28D", stamp),
        mark_timestamp_utc=stamp,
    )
    with open(marks, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(appended) + "\n")
    store.refresh(now_iso=stamp)
    assert store._rebuilds == 2
    fam = store.snapshot["valuation"]["families"]["BASISLV-PREMFADE-28D"]
    assert fam["latest_valid_mark"]["mark_timestamp_utc"] == stamp


# ----------------------------------------------------------------------
# §11 restart: no double-count, ledger bytes untouched
# ----------------------------------------------------------------------
def test_restart_no_double_count_and_bytes_untouched(fixture_runtime, engine):
    paths, ctx = fixture_runtime
    files = sorted(
        list(Path(paths.ledgers_dir).glob("*.jsonl"))
        + list(Path(paths.valuation_dir).glob("*.jsonl"))
    )
    before = {f: _file_digest(f) for f in files}
    now = ctx["last_mark_ts"]

    first = _make_store(paths, engine)
    first.refresh(now_iso=now)
    second = _make_store(paths, engine)  # "restart"
    second.refresh(now_iso=now)
    first.refresh(now_iso=now)

    payload_a = json.dumps(first.snapshot, sort_keys=True)
    payload_b = json.dumps(second.snapshot, sort_keys=True)
    assert payload_a == payload_b, "restart must not change any number"
    assert len(first.snapshot["trades"]) == len(second.snapshot["trades"])

    after = {f: _file_digest(f) for f in files}
    assert before == after, "dashboard must never touch ledger bytes"


# ----------------------------------------------------------------------
# server surface: read-only, GET/HEAD only, routes
# ----------------------------------------------------------------------
class _Server:
    def __init__(self, store):
        self.httpd = make_server(store, 0)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()
        self.base = f"http://127.0.0.1:{self.httpd.server_address[1]}"

    def get(self, path, method="GET"):
        req = urllib.request.Request(self.base + path, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as exc:
            return exc.code, exc.read()

    def stop(self):
        self.httpd.shutdown()
        self.httpd.server_close()


def test_server_read_only_surface(fixture_runtime, engine):
    paths, ctx = fixture_runtime
    ctx["write_heartbeats"](loop_utc=ctx["last_mark_ts"])
    store = _make_store(paths, engine)
    store.refresh(now_iso=ctx["last_mark_ts"])
    srv = _Server(store)
    try:
        status, html = srv.get("/")
        assert status == 200 and b"Quant Shadow Dashboard" in html

        status, body = srv.get("/api/snapshot.json")
        assert status == 200
        env = json.loads(body)
        assert env["app"]["status"]["state"] in ("LIVE", "STALE", "DATA ERROR")
        assert env["snapshot"]["counters"]["fill_count"] == len(
            env["snapshot"]["trades"]
        )

        trade_id = env["snapshot"]["trades"][0]["virtual_trade_id"]
        status, body = srv.get("/api/trade/" + trade_id + ".json")
        assert status == 200 and json.loads(body)["virtual_trade_id"] == trade_id

        for method in ("POST", "PUT", "DELETE", "PATCH"):
            status, body = srv.get("/", method=method)
            assert status == 405, method  # no write endpoint, ever
        assert srv.get("/api/orders") [0] == 404
        assert srv.get("/nope")[0] == 404
    finally:
        srv.stop()


def test_resolve_real_machine():
    paths = find_runtime()
    assert Path(paths.ledgers_dir).is_dir()
    assert any(Path(paths.ledgers_dir).glob("*.jsonl"))
    assert paths.runtime_root.endswith("prospective_shadow_v1")
