"""Dashboard acceptance tests for PROSPECTIVE-SHADOW-V1 (plan section 9.8).

Synthetic ledger fixtures only (temp dir) — production ledgers are never
touched. Every test treats the dashboard as a read-only view over the
append-only ledger bytes.
"""

from __future__ import annotations

import ast
import datetime as dt
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

from research.shadow_v1 import events as shv1_events
from research.shadow_v1 import ledger as shv1_ledger
from research.shadow_v1.dashboard import (
    build_dashboard_snapshot,
    generate_html,
    make_server,
    snapshot_json,
)
from research.shadow_v1.dashboard.server import ROUTES
from research.shadow_v1.families import FAMILY_REGISTRY

WORKTREE = Path(__file__).resolve().parents[1]
IDENTITY_MANIFEST = (
    WORKTREE / "research" / "control" / "prospective_shadow_v1" / "identity" / "identity_recovery.json"
)
FAMILY_IDS = sorted(FAMILY_REGISTRY)
NOW = "2026-09-13T20:00:00Z"

SL_NA = "N/A — frozen family has no native fixed stop"
TP_NA = "N/A — frozen family has no native fixed target"


# ----------------------------------------------------------------------
# fixture helpers
# ----------------------------------------------------------------------
def make_fill(**overrides):
    fill = {
        "virtual_trade_id": "VT-0001",
        "symbol": "BTCUSDT",
        "side": "buy",
        "qty": 0.01,
        "ref_price": 50000.0,
        "fill_price": 50005.0,
        "fee": 0.5,
        "slippage": 0.05,
        "ts_utc": "2026-09-07T00:00:05Z",
        "intended_fill_time": "2026-09-07T00:00:00Z",
        "signal_time": "2026-09-07T00:00:00Z",
        "status": "open",
        "signal_value": 1.25,
        "cross_sectional_rank": 3,
        "target_weight": 0.5,
        "previous_weight": 0.0,
        "realized_pnl": None,
        "unrealized_pnl": 0.4,
        "entry_reason_vi": "Vào vị thế theo tín hiệu thử nghiệm.",
        "funding_cashflows": [
            {
                "funding_time_utc": "2026-09-07T08:00:00Z",
                "rate": 0.0001,
                "notional": 500.0,
                "amount": -0.05,
            },
            {
                "funding_time_utc": "2026-09-07T16:00:00Z",
                "rate": 0.0002,
                "notional": 500.0,
                "amount": -0.1,
            },
        ],
        "funding": -0.15,
    }
    fill.update(overrides)
    return fill


def append_record(tmp: str, family_id: str, ts: str, *, equity=None, cash=None,
                  fills=(), targets=None, fee=None, slippage=None,
                  funding=0.0, data_status="OK", accounting_status="OK",
                  risk_status="OK", cost_digest="cost-regime-A", observed=None):
    fills = list(fills)
    if fee is None:
        fee = sum(float(f.get("fee") or 0.0) for f in fills)
    if slippage is None:
        slippage = sum(float(f.get("slippage") or 0.0) for f in fills)
    record = shv1_events.build_event(
        family_id=family_id,
        arm_id=family_id,
        scheduled_decision_utc=ts,
        observed_at_utc=observed or ts,
        feature_cutoff_utc=ts,
        data_snapshot_digest="data-snapshot-digest-" + ts,
        code_freeze_sha="code-freeze-sha",
        config_digest="config-digest",
        cost_regime_digest=cost_digest,
        eligible_symbols=["BTCUSDT", "ETHUSDT"],
        rejected_symbols_with_reason={},
        signal_values={"BTCUSDT": 1.25},
        target_weights=dict(targets or {}),
        previous_weights={},
        virtual_fill_events=fills,
        fee=fee,
        slippage=slippage,
        funding_cashflow=funding,
        price_pnl=0.0,
        total_pnl=(equity - 100000.0) if equity is not None else 0.0,
        cash=cash if cash is not None else equity,
        equity=equity,
        gross=0.5 if fills else 0.0,
        net=0.5 if fills else 0.0,
        btc_beta=0.1 if fills else 0.0,
        data_status=data_status,
        accounting_status=accounting_status,
        risk_status=risk_status,
    )
    shv1_ledger.append_event(shv1_ledger.ledger_path(tmp, family_id), record)
    return record


def build_basic_ledgers(tmp: str):
    """Three sleeves, one no-trade activation mark + later common marks."""
    for idx, fid in enumerate(FAMILY_IDS):
        append_record(tmp, fid, "2026-09-07T00:00:00Z", equity=100000.0)
        append_record(tmp, fid, "2026-09-10T00:00:00Z", equity=100000.0 + 10.0 * (idx + 1))
    return {fid: shv1_ledger.ledger_path(tmp, fid) for fid in FAMILY_IDS}


class ShV1DashboardTestBase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="shv1-dashboard-test-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def paths(self):
        return {fid: shv1_ledger.ledger_path(self.tmp, fid) for fid in FAMILY_IDS}


# ----------------------------------------------------------------------
# 1. initial combined chart point is exactly 300,000
# ----------------------------------------------------------------------
class TestInitialCombinedPoint(ShV1DashboardTestBase):
    def test_three_100k_sleeves_start_at_exactly_300k(self):
        build_basic_ledgers(self.tmp)
        snap = build_dashboard_snapshot(self.paths(), NOW)
        points = snap["combined"]["chart_points"]
        self.assertTrue(points)
        first = points[0]
        self.assertEqual(first["equity"], 300000.0)
        self.assertEqual(first["status"], "OK")
        self.assertTrue(first.get("kind", "").startswith("anchor"))
        for fid in FAMILY_IDS:
            self.assertEqual(
                snap["families"][fid]["starting_equity_usdt"], 100000.0
            )


# ----------------------------------------------------------------------
# 2. today PnL reconciles to the frozen local-day boundary (+ UTC toggle)
# ----------------------------------------------------------------------
class TestTodayPnlWindows(ShV1DashboardTestBase):
    def _ledger_with_marks(self):
        # HCMC midnight of 2026-09-13T20:00Z "now" is 2026-09-13T17:00:00Z.
        marks = [
            ("2026-09-13T16:00:00Z", 100000.0),
            ("2026-09-13T17:00:00Z", 100100.0),   # exact HCMC boundary mark
            ("2026-09-13T18:00:00Z", 100250.0),
            ("2026-09-13T19:30:00Z", 100200.0),
        ]
        for fid in FAMILY_IDS:
            for ts, eq in marks:
                append_record(self.tmp, fid, ts, equity=eq)
        return self.paths()

    def test_local_boundary_pnl_and_printed_stamps(self):
        self._ledger_with_marks()
        snap = build_dashboard_snapshot(self.paths(), NOW)
        combined_today = snap["combined"]["today"]["Asia/Ho_Chi_Minh"]
        self.assertEqual(combined_today["status"], "OK")
        self.assertEqual(combined_today["window_start_utc"], "2026-09-13T17:00:00Z")
        self.assertEqual(combined_today["window_end_utc"], NOW)
        self.assertEqual(combined_today["boundary_mark_ts"], "2026-09-13T17:00:00Z")
        # 3 sleeves x (100200 - 100100)
        self.assertAlmostEqual(combined_today["pnl_usdt"], 300.0, places=6)
        expected_pct = 300.0 / (3.0 * 100100.0) * 100.0
        self.assertAlmostEqual(
            combined_today["pnl_pct"], expected_pct, places=9
        )
        self.assertIn("+07:00", combined_today["window_start_local"])
        per_family = combined_today["per_family"]
        for fid in FAMILY_IDS:
            self.assertEqual(per_family[fid]["status"], "OK")
            self.assertAlmostEqual(per_family[fid]["pnl_usdt"], 100.0, places=6)
            self.assertEqual(per_family[fid]["window_start_utc"], "2026-09-13T17:00:00Z")
        fam_block = snap["families"][FAMILY_IDS[0]]["today"]["Asia/Ho_Chi_Minh"]
        self.assertEqual(fam_block["boundary_mark_ts"], "2026-09-13T17:00:00Z")
        self.assertEqual(fam_block["end_mark_ts"], "2026-09-13T19:30:00Z")
        self.assertAlmostEqual(fam_block["pnl_usdt"], 100.0, places=6)

    def test_utc_toggle_variant(self):
        # marks around UTC midnight 2026-09-14T00:00:00Z; no HCMC-boundary
        # mark exists, so the local window must fail closed in this fixture.
        marks = [
            ("2026-09-13T23:00:00Z", 100000.0),
            ("2026-09-14T00:00:00Z", 100050.0),
            ("2026-09-14T01:00:00Z", 100075.0),
            ("2026-09-14T02:00:00Z", 100060.0),
        ]
        for fid in FAMILY_IDS:
            for ts, eq in marks:
                append_record(self.tmp, fid, ts, equity=eq)
        snap = build_dashboard_snapshot(self.paths(), "2026-09-14T03:00:00Z")
        utc_today = snap["combined"]["today"]["UTC"]
        self.assertEqual(utc_today["status"], "OK")
        self.assertEqual(utc_today["window_start_utc"], "2026-09-14T00:00:00Z")
        self.assertEqual(utc_today["window_end_utc"], "2026-09-14T03:00:00Z")
        self.assertAlmostEqual(utc_today["pnl_usdt"], 3 * 10.0, places=6)
        local_today = snap["combined"]["today"]["Asia/Ho_Chi_Minh"]
        self.assertEqual(local_today["status"], "UNAVAILABLE_FAIL_CLOSED")
        self.assertIsNone(local_today["pnl_usdt"])
        self.assertIn("2026-09-13T17:00:00Z", local_today["window_start_utc"])

    def test_missing_midnight_mark_is_fail_closed(self):
        marks = [
            ("2026-09-13T16:00:00Z", 100000.0),
            # no mark at the exact boundary 17:00:00Z
            ("2026-09-13T17:00:01Z", 100100.0),
            ("2026-09-13T19:00:00Z", 100300.0),
        ]
        for fid in FAMILY_IDS:
            for ts, eq in marks:
                append_record(self.tmp, fid, ts, equity=eq)
        snap = build_dashboard_snapshot(self.paths(), NOW)
        block = snap["combined"]["today"]["Asia/Ho_Chi_Minh"]
        self.assertEqual(block["status"], "UNAVAILABLE_FAIL_CLOSED")
        self.assertIsNone(block["pnl_usdt"])
        self.assertIsNone(block["pnl_pct"])
        self.assertIn("UNAVAILABLE_FAIL_CLOSED", block["reason"])
        for fid in FAMILY_IDS:
            fam = snap["families"][fid]["today"]["Asia/Ho_Chi_Minh"]
            self.assertEqual(fam["status"], "UNAVAILABLE_FAIL_CLOSED")
            self.assertIsNone(fam["pnl_usdt"])


# ----------------------------------------------------------------------
# 3. combined == strict sum at every valid mark; gaps never interpolated
# ----------------------------------------------------------------------
class TestCombinedStrictSum(ShV1DashboardTestBase):
    def test_sum_and_sleeve_gap(self):
        common = [
            ("2026-09-07T00:00:00Z", (100000.0, 100000.0, 100000.0)),
            ("2026-09-08T00:00:00Z", (100010.0, 100020.0, 100030.0)),
            # t2: sleeves 1 and 3 have marks, sleeve 2 does NOT
            ("2026-09-09T00:00:00Z", (100015.0, None, 100035.0)),
            ("2026-09-10T00:00:00Z", (100020.0, 100025.0, 100040.0)),
        ]
        for fid_idx, fid in enumerate(FAMILY_IDS):
            for ts, eqs in common:
                if eqs[fid_idx] is None:
                    continue
                append_record(self.tmp, fid, ts, equity=eqs[fid_idx])
        snap = build_dashboard_snapshot(self.paths(), "2026-09-11T00:00:00Z")
        by_ts = {p["ts"]: p for p in snap["combined"]["chart_points"]}
        # strict sum at every common valid mark (3 x ~100k sleeves)
        self.assertAlmostEqual(by_ts["2026-09-08T00:00:00Z"]["equity"], 300060.0, places=9)
        self.assertAlmostEqual(by_ts["2026-09-10T00:00:00Z"]["equity"], 300085.0, places=9)
        # gap at t2: fail closed, equity None, never interpolated
        gap = by_ts["2026-09-09T00:00:00Z"]
        self.assertEqual(gap["status"], "UNAVAILABLE_FAIL_CLOSED")
        self.assertIsNone(gap["equity"])
        self.assertIn(FAMILY_IDS[1], gap.get("missing_sleeves", []))
        # no fabricated number anywhere: every non-OK point has equity None
        for point in snap["combined"]["chart_points"]:
            if point["status"] != "OK":
                self.assertIsNone(point["equity"])


# ----------------------------------------------------------------------
# 4. the four counters cannot be conflated
# ----------------------------------------------------------------------
class TestSeparateCounters(ShV1DashboardTestBase):
    def test_two_decisions_three_intents_four_fills_one_closed(self):
        fid = FAMILY_IDS[0]
        f1 = make_fill(virtual_trade_id="VT-A", status="open", fee=0.5, slippage=0.05)
        f2 = make_fill(virtual_trade_id="VT-B", symbol="ETHUSDT", side="sell",
                       status="open", fee=0.3, slippage=0.03)
        f3 = make_fill(virtual_trade_id="VT-C", symbol="ETHUSDT", side="buy",
                       status="closed", realized_pnl=5.0, fee=0.2, slippage=0.02)
        f4 = make_fill(virtual_trade_id="VT-D", symbol="BNBUSDT", status="open",
                       fee=0.1, slippage=0.01)
        append_record(self.tmp, fid, "2026-09-07T00:00:00Z", equity=100000.0,
                      fills=[f1, f2], targets={"BTCUSDT": 0.5})
        append_record(self.tmp, fid, "2026-09-08T00:00:00Z", equity=100001.0,
                      fills=[f3, f4],
                      targets={"BTCUSDT": 0.0, "ETHUSDT": 0.5})
        snap = build_dashboard_snapshot({fid: shv1_ledger.ledger_path(self.tmp, fid)}, NOW)
        counters = snap["families"][fid]["counters"]
        self.assertEqual(counters["decision_count"], 2)
        self.assertEqual(counters["order_intent_count"], 3)
        self.assertEqual(counters["fill_count"], 4)
        self.assertEqual(counters["closed_position_count"], 1)
        # the four numbers are distinct values carried under distinct keys
        self.assertEqual(len(set(counters.values())), 4)
        self.assertEqual(snap["counters"], counters)


# ----------------------------------------------------------------------
# 5. clicking a fill resolves the immutable event with all cost rows
# ----------------------------------------------------------------------
class TestDetailLookup(ShV1DashboardTestBase):
    def test_detail_matches_ledger_bytes(self):
        fid = FAMILY_IDS[0]
        fill = make_fill(virtual_trade_id="VT-X1")
        append_record(self.tmp, fid, "2026-09-07T00:00:00Z", equity=100000.0,
                      fills=[fill], targets={"BTCUSDT": 0.5}, funding=-0.15)
        path = shv1_ledger.ledger_path(self.tmp, fid)
        snap = build_dashboard_snapshot({fid: path}, NOW)

        detail = snap["trade_index"]["VT-X1"]
        # compare against the RAW ledger line (the authority bytes)
        raw_records = [json.loads(line) for line in
                       Path(path).read_bytes().decode("utf-8").splitlines()]
        raw_fill = None
        raw_record = None
        for rec in raw_records:
            for f in rec["virtual_fill_events"]:
                if f["virtual_trade_id"] == "VT-X1":
                    raw_fill, raw_record = f, rec
        self.assertIsNotNone(raw_fill)
        self.assertEqual(detail["fee"], raw_fill["fee"])
        self.assertEqual(detail["slippage"], raw_fill["slippage"])
        flows = detail["funding_cashflows"]
        self.assertEqual(len(flows), len(raw_fill["funding_cashflows"]))
        for got, want in zip(flows, raw_fill["funding_cashflows"]):
            self.assertEqual(got["amount"], want["amount"])
            self.assertEqual(got["funding_time_utc"], want["funding_time_utc"])
            self.assertEqual(got["rate"], want["rate"])
        expected_total = raw_fill["fee"] + raw_fill["slippage"] + raw_fill["funding"]
        self.assertAlmostEqual(detail["total_transaction_cost"], expected_total, places=12)
        self.assertEqual(detail["event_id"], raw_record["event_id"])
        self.assertEqual(detail["feature_cutoff_utc"], raw_record["feature_cutoff_utc"])
        self.assertEqual(detail["config_digest"], raw_record["config_digest"])
        self.assertEqual(detail["cost_regime_digest"], raw_record["cost_regime_digest"])
        self.assertEqual(detail["source_ledger"]["digest"], shv1_ledger.ledger_digest(path))
        self.assertEqual(Path(detail["source_ledger"]["path"]), Path(path))
        # table row resolves through the same id
        row = next(r for r in snap["trades"] if r["virtual_trade_id"] == "VT-X1")
        self.assertEqual(row["event_id"], raw_record["event_id"])

    def test_unknown_trade_id_is_not_found(self):
        build_basic_ledgers(self.tmp)
        snap = build_dashboard_snapshot(self.paths(), NOW)
        self.assertNotIn("NO-SUCH-ID", snap["trade_index"])


# ----------------------------------------------------------------------
# 6. missing marks => visible gap + UNAVAILABLE_FAIL_CLOSED status
# ----------------------------------------------------------------------
class TestMarkGapFailClosed(ShV1DashboardTestBase):
    def test_blocked_valuation_creates_gap(self):
        fid = FAMILY_IDS[0]
        fill = make_fill(status="open", fee=0.5, slippage=0.05)
        append_record(self.tmp, fid, "2026-09-07T00:00:00Z", equity=100000.0,
                      fills=[fill], targets={"BTCUSDT": 0.5})
        append_record(self.tmp, fid, "2026-09-08T00:00:00Z", equity=None,
                      data_status=shv1_events.DATA_STATUS_BLOCKED,
                      accounting_status=shv1_events.ACCOUNTING_STATUS_UNAVAILABLE)
        snap = build_dashboard_snapshot({fid: shv1_ledger.ledger_path(self.tmp, fid)}, NOW)
        block = snap["families"][fid]
        self.assertEqual(block["gap_status"], "UNAVAILABLE_FAIL_CLOSED")
        gap_points = [p for p in block["chart_points"] if p["status"] != "OK"]
        self.assertTrue(gap_points)
        self.assertIsNone(gap_points[-1]["equity"])
        combined = snap["combined"]["chart_points"]
        gap_combined = [p for p in combined if p["status"] == "UNAVAILABLE_FAIL_CLOSED"]
        self.assertTrue(gap_combined)
        self.assertIsNone(gap_combined[-1]["equity"])
        codes = {b["code"] for b in snap["banners"]}
        self.assertIn("UNAVAILABLE_FAIL_CLOSED", codes)


# ----------------------------------------------------------------------
# 7. SL/TP honesty + true frozen exit policy
# ----------------------------------------------------------------------
class TestSlTpHonesty(ShV1DashboardTestBase):
    def test_every_family_shows_na_and_true_exit_policy(self):
        build_basic_ledgers(self.tmp)
        manifest = json.loads(IDENTITY_MANIFEST.read_text())
        manifest_entries = {e["family_id"]: e for e in manifest["families"]}
        snap = build_dashboard_snapshot(self.paths(), NOW,
                                        identity_manifest_path=str(IDENTITY_MANIFEST))
        for fid in FAMILY_IDS:
            block = snap["families"][fid]
            self.assertEqual(block["stop_loss_price"], SL_NA)
            self.assertEqual(block["take_profit_price"], TP_NA)
            self.assertEqual(block["exit_policy"], FAMILY_REGISTRY[fid].EXIT_POLICY)
            self.assertEqual(
                block["historical_verdict_label"],
                manifest_entries[fid]["historical_verdict_label"],
            )
            self.assertEqual(
                block["historical_verdict_label"],
                FAMILY_REGISTRY[fid].HISTORICAL_VERDICT_LABEL,
            )
            self.assertTrue(
                snap["identity"]["families"][fid]["manifest_entry_found"]
            )
        for row in snap["trades"]:
            self.assertEqual(row["stop_loss_price"], SL_NA)
            self.assertEqual(row["take_profit_price"], TP_NA)
            self.assertEqual(row["exit_policy"], FAMILY_REGISTRY[row["family"]].EXIT_POLICY)
        # identity cross-check is clean
        self.assertEqual(snap["identity"]["identity_status"], "OK")
        self.assertEqual(snap["identity"]["identity_drift"], [])

    def test_identity_drift_is_reported(self):
        build_basic_ledgers(self.tmp)
        mutated = tempfile.mkdtemp(prefix="shv1-drift-")
        self.addCleanup(shutil.rmtree, mutated, True)
        payload = json.loads(IDENTITY_MANIFEST.read_text())
        payload["families"][0]["historical_verdict_label"] = "REWRITTEN_LABEL"
        drift_path = Path(mutated) / "identity_recovery.json"
        drift_path.write_text(json.dumps(payload))
        snap = build_dashboard_snapshot(self.paths(), NOW,
                                        identity_manifest_path=str(drift_path))
        self.assertEqual(snap["identity"]["identity_status"], "DRIFT")
        codes = {b["code"] for b in snap["banners"]}
        self.assertIn("IDENTITY_DRIFT", codes)


# ----------------------------------------------------------------------
# 8. regeneration is byte-identical and leaves the worktree clean
# ----------------------------------------------------------------------
class TestIdempotentRegeneration(ShV1DashboardTestBase):
    def test_snapshot_bytes_stable_and_git_tree_unchanged(self):
        build_basic_ledgers(self.tmp)
        paths = self.paths()
        digests_before = {
            fid: shv1_ledger.ledger_digest(path) for fid, path in paths.items()
        }
        snap_a = build_dashboard_snapshot(paths, NOW,
                                          identity_manifest_path=str(IDENTITY_MANIFEST))
        snap_b = build_dashboard_snapshot(paths, NOW,
                                          identity_manifest_path=str(IDENTITY_MANIFEST))
        bytes_a = snapshot_json(snap_a).encode("utf-8")
        bytes_b = snapshot_json(snap_b).encode("utf-8")
        self.assertEqual(hashlib.sha256(bytes_a).hexdigest(),
                         hashlib.sha256(bytes_b).hexdigest())
        # generation is read-only: ledger bytes unchanged
        digests_after = {
            fid: shv1_ledger.ledger_digest(path) for fid, path in paths.items()
        }
        self.assertEqual(digests_before, digests_after)

        def git_status() -> str:
            proc = subprocess.run(
                ["git", "-C", str(WORKTREE), "status", "--porcelain=v1"],
                capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(proc.returncode, 0, msg=proc.stderr)
            return proc.stdout

        out_path = Path(tempfile.gettempdir()) / "shv1-dashboard-regen.html"
        out_path.unlink(missing_ok=True)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
        cli_cmd = [
            sys.executable, "-m", "research.shadow_v1.dashboard",
            "--ledgers", self.tmp, "--now", NOW, "--out", str(out_path),
        ]
        status_before = git_status()
        proc = subprocess.run(
            cli_cmd, cwd=str(WORKTREE), env=env,
            capture_output=True, text=True, timeout=120,
        )
        self.assertEqual(proc.returncode, 0, msg=proc.stderr)
        self.assertEqual(git_status(), status_before,
                         msg="generator changed the worktree state")
        self.assertTrue(out_path.exists())
        # two CLI runs produce byte-identical pages (refresh is idempotent)
        out2 = Path(tempfile.gettempdir()) / "shv1-dashboard-regen2.html"
        out2.unlink(missing_ok=True)
        subprocess.run(
            cli_cmd[:7] + ["--out", str(out2)],
            cwd=str(WORKTREE), env=env, capture_output=True, text=True,
            timeout=120, check=True,
        )
        self.assertEqual(
            hashlib.sha256(out_path.read_bytes()).hexdigest(),
            hashlib.sha256(out2.read_bytes()).hexdigest(),
        )


# ----------------------------------------------------------------------
# 9. adversarial: server is GET/HEAD read-only, no order surface
# ----------------------------------------------------------------------
class TestServerReadOnly(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="shv1-server-test-")
        for fid in FAMILY_IDS:
            append_record(cls.tmp, fid, "2026-09-07T00:00:00Z", equity=100000.0,
                          fills=[make_fill(virtual_trade_id="VT-SRV")],
                          targets={"BTCUSDT": 0.5})
        app_paths = {fid: shv1_ledger.ledger_path(cls.tmp, fid) for fid in FAMILY_IDS}
        cls.httpd = make_server(
            cls.tmp, 0, identity_manifest_path=str(IDENTITY_MANIFEST)
        )
        cls.port = cls.httpd.server_address[1]
        cls.thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        shutil.rmtree(cls.tmp, True)

    def _request(self, method: str, path: str):
        url = f"http://127.0.0.1:{self.port}{path}"
        req = urllib.request.Request(url, method=method, data=b"" if method != "GET" and method != "HEAD" else None)
        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return resp.status, dict(resp.headers), resp.read()
        except urllib.error.HTTPError as exc:
            return exc.code, dict(exc.headers), exc.read()

    def test_known_routes_answer_get(self):
        status, headers, body = self._request("GET", "/")
        self.assertEqual(status, 200)
        self.assertIn("text/html", headers.get("Content-Type", ""))
        self.assertIn(b"300,000", body)
        status, _, body = self._request("GET", "/api/snapshot.json")
        self.assertEqual(status, 200)
        payload = json.loads(body)
        self.assertEqual(payload["schema"], "shv1_dashboard_snapshot_v1")
        status, _, body = self._request("GET", "/api/export.csv")
        self.assertEqual(status, 200)
        self.assertIn(b"virtual_trade_id", body)
        status, _, body = self._request("GET", "/api/export.json")
        self.assertEqual(status, 200)
        self.assertIn("equity_series", json.loads(body))
        status, _, body = self._request("GET", "/api/trade/VT-SRV.json")
        self.assertEqual(status, 200)
        self.assertEqual(json.loads(body)["virtual_trade_id"], "VT-SRV")
        status, _, _ = self._request("GET", "/api/trade/NOPE.json")
        self.assertEqual(status, 404)
        status, _, _ = self._request("GET", "/static/anything.js")
        self.assertEqual(status, 404)
        status, _, _ = self._request("HEAD", "/")
        self.assertEqual(status, 200)

    def test_every_write_method_on_every_route_is_405(self):
        routes = ["/", "/api/snapshot.json", "/api/trade/VT-SRV.json",
                  "/api/export.csv", "/api/export.json"]
        for route in routes:
            for method in ("POST", "PUT", "DELETE", "PATCH"):
                status, headers, _ = self._request(method, route)
                self.assertEqual(status, 405, msg=f"{method} {route} -> {status}")
                self.assertEqual(headers.get("Allow"), "GET, HEAD")

    def test_route_table_is_exactly_read_only(self):
        self.assertEqual(
            set(ROUTES),
            {"/", "/api/snapshot.json", "/api/trade/", "/api/export.csv", "/api/export.json"},
        )

    def test_server_source_has_no_write_or_order_surface(self):
        server_src = (WORKTREE / "research" / "shadow_v1" / "dashboard" / "server.py").read_text()
        cli_src = (WORKTREE / "research" / "shadow_v1" / "dashboard" / "cli.py").read_text()
        forbidden_everywhere = [
            "os.remove", "os.unlink", "shutil.rmtree(", "subprocess",
            "place_order", "create_order", "submit_order", "cancel_order",
            "new_order", "send_order", "requests.post", "requests.put",
            "requests.delete", "urllib.request.urlopen", "api_key",
            "api_secret", "secret_key", "binance",
        ]
        for literal in forbidden_everywhere:
            self.assertNotIn(literal, server_src,
                             msg=f"server.py must not contain {literal!r}")
            self.assertNotIn(literal, cli_src,
                             msg=f"cli.py must not contain {literal!r}")
        # write-mode file opens are not allowed in the route/handler code
        tree = ast.parse(server_src)
        handler_nodes = [n for n in tree.body
                         if isinstance(n, ast.ClassDef)
                         and n.name in ("DashboardApp", "DashboardRequestHandler")]
        handler_src = "\n".join(ast.dump(n) for n in handler_nodes)
        for mode in ("'w'", '"w"', "'a'", '"a"', "'wb'", '"wb"', "'ab'", '"ab"', "'+'", '"+"'):
            self.assertNotIn(mode, handler_src,
                             msg=f"handler code must not open files in write mode {mode}")

    def test_snapshot_emits_target_intent_only(self):
        from research.shadow_v1.dashboard import build_dashboard_snapshot as build

        snap = build({fid: shv1_ledger.ledger_path(self.tmp, fid) for fid in FAMILY_IDS},
                     NOW)
        actions = []

        def walk(node):
            if isinstance(node, dict):
                for key, value in node.items():
                    if key in ("emitted_action_types", "action_type") and isinstance(value, (str, list)):
                        actions.extend(value if isinstance(value, list) else [value])
                    walk(value)
            elif isinstance(node, list):
                for item in node:
                    walk(item)

        walk(snap)
        self.assertTrue(actions)
        self.assertEqual(set(actions), {"TARGET_INTENT"})


# ----------------------------------------------------------------------
# 10. pre-activation: no fake zeros
# ----------------------------------------------------------------------
class TestPreActivation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="shv1-empty-")
        self.addCleanup(shutil.rmtree, self.tmp, True)

    def test_empty_ledgers_render_not_run_no_fake_zeros(self):
        paths = {fid: shv1_ledger.ledger_path(self.tmp, fid) for fid in FAMILY_IDS}
        snap = build_dashboard_snapshot(paths, NOW)
        self.assertTrue(snap["pre_activation"])
        self.assertEqual(snap["system_status"], "NOT_RUN")
        for fid in FAMILY_IDS:
            block = snap["families"][fid]
            self.assertEqual(block["status"], "NOT_RUN")
            self.assertIsNone(block["current_equity_usdt"])
            self.assertIsNone(block["total_pnl_usdt"])
            self.assertIsNone(block["counters"]["decision_count"])
            self.assertEqual(block["today"]["Asia/Ho_Chi_Minh"]["status"], "NOT_RUN")
            self.assertIsNone(block["today"]["Asia/Ho_Chi_Minh"]["pnl_usdt"])
        self.assertEqual(snap["combined"]["chart_points"], [])
        self.assertIsNone(snap["combined"]["current_equity_usdt"])
        self.assertIsNone(snap["counters"]["decision_count"])
        codes = {b["code"] for b in snap["banners"]}
        self.assertIn("NOT_RUN", codes)


# ----------------------------------------------------------------------
# 11. render smoke: required literals, verdict labels, no winner ranking
# ----------------------------------------------------------------------
class TestRenderSmoke(ShV1DashboardTestBase):
    def _assert_static_literals(self, html: str, expect_no_trades: bool):
        self.assertIn("300,000", html)
        self.assertIn("Asia/Ho_Chi_Minh", html)
        self.assertIn("N/A", html)
        self.assertIn("V11_FAMILY_REJECT", html)
        self.assertIn("V14_FAMILY_REJECT", html)
        self.assertIn("CANDIDATE_FAIL", html)
        if expect_no_trades:
            self.assertTrue("NOT_RUN" in html or "NO_TRADES_YET" in html)
        self.assertNotIn("winner", html.lower())

    def test_empty_fixture_page(self):
        paths = {fid: shv1_ledger.ledger_path(self.tmp, fid) for fid in FAMILY_IDS}
        snap = build_dashboard_snapshot(paths, NOW)
        html = generate_html(snap)
        self.assertIsInstance(html, str)
        self.assertGreater(len(html), 10000)
        self._assert_static_literals(html, expect_no_trades=True)
        self.assertIn("NO_TRADES_YET", html)
        self.assertIn("NOT_RUN", html)

    def test_populated_fixture_page(self):
        build_basic_ledgers(self.tmp)
        snap = build_dashboard_snapshot(self.paths(), NOW,
                                        identity_manifest_path=str(IDENTITY_MANIFEST))
        html = generate_html(snap)
        self._assert_static_literals(html, expect_no_trades=False)

    def test_corrupt_ledger_refuses_red(self):
        build_basic_ledgers(self.tmp)
        path = Path(shv1_ledger.ledger_path(self.tmp, FAMILY_IDS[0]))
        with open(path, "ab") as fh:  # simulate crash mid-append
            fh.write(b'{"event_id": "truncated"')
        snap = build_dashboard_snapshot(self.paths(), NOW)
        self.assertEqual(snap["families"][FAMILY_IDS[0]]["status"], "STOPPED")
        codes = {b["code"] for b in snap["banners"]}
        self.assertIn("LEDGER_CORRUPT", codes)
        html = generate_html(snap)
        self.assertIn("LEDGER_CORRUPT", html)

    def test_accounting_mismatch_refuses_red(self):
        fid = FAMILY_IDS[0]
        append_record(self.tmp, fid, "2026-09-07T00:00:00Z", equity=-5.0)
        snap = build_dashboard_snapshot({fid: shv1_ledger.ledger_path(self.tmp, fid)}, NOW)
        block = snap["families"][fid]
        self.assertEqual(block["status"], "STOPPED")
        self.assertTrue(block["mismatch_reasons"])
        codes = {b["code"] for b in snap["banners"]}
        self.assertIn("ACCOUNTING_MISMATCH", codes)
        html = generate_html(snap)
        self.assertIn("ACCOUNTING_MISMATCH", html)


if __name__ == "__main__":
    unittest.main()
