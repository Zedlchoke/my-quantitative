"""A3 data-authority gate (FOREX-FREE-V2 F2-P2).

Covers:
* full staged-manifest replay against the READ-ONLY V1 snapshot (the
  byte-level authority proof: 156/156 digests);
* fail-closed replay on tampered/missing files (tiny synthetic manifests);
* td_loader determinism spot check (same pair loaded twice -> identical
  digests via digest_bars);
* H1 grid audit on a tiny SYNTHETIC fixture (weekend vs missing
  classification; missing -> NO_TRADE sentinel);
* last_flat_bar_index across BOTH 2025 US DST transitions (2025-03-09 spring
  forward, 2025-11-02 fall back) and BOTH 2025 EU transitions (2025-03-30,
  2025-10-26), with the 16:00-New-York -> UTC mapping recomputed
  independently via zoneinfo (computed, never guessed);
* completed-bar rule (next_actionable_index), fold/purge boundaries,
  D1 classification guard, S1 boundary guard, offline (no-network) guard.

Real-data tests read ONLY the read-only V1 snapshot under SNAPSHOT_ROOT.
No network anywhere; the offline guard itself is exercised in-process.
"""
import datetime as dt
import json
import os
import socket
import sys
import tempfile
import unittest
from zoneinfo import ZoneInfo

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from research.assets.forex_free_v2 import data_authority as DA  # noqa: E402
from research.assets.forex_free_v1 import td_loader  # noqa: E402

UTC = dt.timezone.utc
NY = ZoneInfo("America/New_York")


def _bar(stamp_utc: dt.datetime, price: float = 1.0) -> dict:
    return {"datetime": stamp_utc.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S"),
            "open": price, "high": price, "low": price, "close": price}


def _hourly(start: dt.datetime, end: dt.datetime, skip=()):
    out, t = [], start
    while t <= end:
        if t not in skip:
            out.append(_bar(t))
        t += dt.timedelta(hours=1)
    return out


def ny_to_utc(year, month, day, hour, minute=0):
    """Independent zoneinfo recompute: New York wall time -> exact UTC instant."""
    return dt.datetime(year, month, day, hour, minute, tzinfo=NY).astimezone(UTC)


class TestStagedManifestReplay(unittest.TestCase):
    """The byte-level authority proof: V2 reuses the V1 snapshot byte-for-byte."""

    def test_full_replay_156_of_156(self):
        results = DA.replay_staged_manifest()
        self.assertEqual(results["manifest_schema"], "forex_free_v1_staged_data_manifest_v2")
        self.assertEqual(results["checked"], 156)
        self.assertEqual(results["matched"], 156)
        self.assertEqual(results["mismatches"], 0)
        self.assertEqual(results["missing"], 0)
        self.assertTrue(results["fail_closed_ok"])
        self.assertEqual(results["exec_vs_repro_disagreements"], 0)
        self.assertEqual(len(results["files"]), 156)
        self.assertTrue(all(f["status"] == "MATCH" for f in results["files"]))
        self.assertTrue(all(f["observed_sha256"] == f["expected_sha256"]
                            for f in results["files"]))
        # every hashed data file stayed inside the read-only snapshot data root
        for f in results["files"]:
            full = os.path.join(results["snapshot_root"], f["path"])
            self.assertTrue(full.startswith(os.path.abspath(DA.SNAPSHOT_ROOT) + os.sep),
                            full)

    def test_replay_fail_closed_on_tampered_file(self):
        with tempfile.TemporaryDirectory(prefix="fxv2_replay_") as tmp:
            good = os.path.join(tmp, "good.json")
            evil = os.path.join(tmp, "evil.json")
            open(good, "w").write("{}")
            open(evil, "w").write("tampered")
            manifest = os.path.join(tmp, "staged_data_manifest.json")
            import hashlib
            json.dump({
                "schema": "test", "digests_exec2": {
                    "good.json": hashlib.sha256(open(good, "rb").read()).hexdigest(),
                    "evil.json": "0" * 64,
                }}, open(manifest, "w"))
            with self.assertRaises(DA.StagedManifestReplayError) as ctx:
                DA.replay_staged_manifest(manifest, snapshot_root=tmp)
            results = ctx.exception.results
            self.assertEqual((results["checked"], results["matched"],
                              results["mismatches"], results["missing"]), (2, 1, 1, 0))
            self.assertFalse(results["fail_closed_ok"])

    def test_replay_fail_closed_on_missing_file(self):
        with tempfile.TemporaryDirectory(prefix="fxv2_replay_") as tmp:
            manifest = os.path.join(tmp, "staged_data_manifest.json")
            json.dump({"schema": "test", "digests_exec2":
                       {"ghost.json": "1" * 64}}, open(manifest, "w"))
            with self.assertRaises(DA.StagedManifestReplayError) as ctx:
                DA.replay_staged_manifest(manifest, snapshot_root=tmp)
            self.assertEqual(ctx.exception.results["missing"], 1)

    def test_replay_refuses_s1_paths_inside_manifest(self):
        with tempfile.TemporaryDirectory(prefix="fxv2_replay_") as tmp:
            manifest = os.path.join(tmp, "staged_data_manifest.json")
            json.dump({"schema": "test", "digests_exec2":
                       {"s1/secret.json": "2" * 64}}, open(manifest, "w"))
            with self.assertRaises(DA.S1BoundaryViolation):
                DA.replay_staged_manifest(manifest, snapshot_root=tmp)


class TestTdLoaderDeterminism(unittest.TestCase):
    def test_same_pair_loaded_twice_identical_digest(self):
        rows_a, quar_a = td_loader.load_pair_h1("EUR/USD", DA.SNAPSHOT_DATA_ROOT)
        rows_b, quar_b = td_loader.load_pair_h1("EUR/USD", DA.SNAPSHOT_DATA_ROOT)
        self.assertEqual(td_loader.digest_bars(rows_a), td_loader.digest_bars(rows_b))
        self.assertEqual(len(quar_a), len(quar_b))
        self.assertGreater(len(rows_a), 40000)


class TestH1GridAuditSynthetic(unittest.TestCase):
    """Tiny synthetic week: 2024-03-04..08 (EST, pre-spring-forward).

    Frozen window: Sun 2024-03-03 21:00 EST -> Fri 2024-03-08 16:00 EST
    half-open => in-open hourly grid stamps Mon 02:00Z .. Fri 20:00Z (115
    positions).  A Wednesday 15:00Z bar is absent (missing inside open);
    Sat 20:00Z, Sun 01:00Z and Sun 22:00Z stale provider bars exist outside
    the window (weekend classification, never 'missing').
    """

    def _fixture(self, extra_dup=False):
        # weekly open instant: Sun 2024-03-03 21:00 EST == Mon 2024-03-04 02:00Z
        start = dt.datetime(2024, 3, 4, 2, tzinfo=UTC)
        # last in-open stamp: window is half-open, closes Fri 2024-03-08 16:00 EST == 21:00Z
        end = dt.datetime(2024, 3, 8, 20, tzinfo=UTC)
        missing = dt.datetime(2024, 3, 6, 15, tzinfo=UTC)  # Wed 15:00Z (inside open)
        rows = _hourly(start, end, skip=(missing,))
        rows += [_bar(dt.datetime(2024, 3, 9, 20, tzinfo=UTC))]   # Sat stale
        rows += [_bar(dt.datetime(2024, 3, 10, 1, tzinfo=UTC))]   # Sun stale
        rows += [_bar(dt.datetime(2024, 3, 10, 22, tzinfo=UTC))]  # Sun stale (17:00 EST)
        if extra_dup:
            rows += [_bar(start)]  # duplicate of the first bar
        rows.sort(key=lambda r: r["datetime"])
        return rows, missing

    def test_weekend_vs_missing_classification(self):
        rows, missing = self._fixture()
        audit = DA.h1_grid_audit(rows)
        self.assertEqual(audit["n_bars"], 115 - 1 + 3)
        self.assertEqual(audit["duplicates"], 0)
        self.assertEqual(audit["non_hour_aligned"], 0)
        self.assertEqual(audit["inside_open_total"], 115)
        self.assertEqual(audit["inside_open_present"], 114)
        self.assertEqual(audit["inside_open_missing"], 1)
        self.assertEqual(len(audit["missing_inside_open"]), 1)
        only = audit["missing_inside_open"][0]
        self.assertEqual(only["stamp_utc"], "2024-03-06T15:00:00Z")
        self.assertEqual(only["action"], DA.NO_TRADE_SENTINEL)
        # weekend stale bars classified separately, never as missing
        self.assertEqual(audit["out_of_session_present"], 3)

    def test_duplicate_stamps_counted(self):
        rows, _ = self._fixture(extra_dup=True)
        audit = DA.h1_grid_audit(rows)
        self.assertEqual(audit["duplicates"], 1)

    def test_missing_maps_to_no_trade_fail_closed(self):
        rows, _ = self._fixture()
        audit = DA.h1_grid_audit(rows)
        self.assertTrue(all(
            m["action"] == DA.NO_TRADE_SENTINEL for m in audit["missing_inside_open"]))

    def test_real_pair_smoke_eurusd(self):
        rows, _ = td_loader.load_pair_h1("EUR/USD", DA.SNAPSHOT_DATA_ROOT)
        audit = DA.h1_grid_audit(rows)
        self.assertEqual(audit["duplicates"], 0)
        self.assertEqual(audit["non_hour_aligned"], 0)
        self.assertEqual(audit["first"][:16], "2020-01-30T07:00")
        self.assertEqual(audit["last"][:16], "2026-09-02T00:00")
        # missing inside-open bars exist (holidays) but are rare and enumerated
        self.assertGreater(audit["inside_open_missing"], 0)
        self.assertLess(audit["inside_open_missing"] / audit["inside_open_total"], 0.05)
        self.assertGreater(audit["out_of_session_present"], 0)


class TestLastFlatBarDSTProbes(unittest.TestCase):
    """16:00 New York -> UTC mapping recomputed via zoneinfo on independent code.

    Exact truth (EST=UTC-5, EDT=UTC-4): the 16:00 NY bar stamps 21:00Z in EST
    weeks and 20:00Z in EDT weeks.  The mapping depends only on the NEW YORK
    offset, so the EU transitions (2025-03-30, 2025-10-26) provably do not
    alter it, including inside the brief EU/US desync windows.
    """

    PROBES = [
        # (entry_date, expected_utc_instant, note)
        (dt.date(2025, 1, 15), ny_to_utc(2025, 1, 15, 16), "deep winter EST"),
        (dt.date(2025, 3, 7), ny_to_utc(2025, 3, 7, 16), "last EST Friday before US spring forward -> 21:00Z"),
        (dt.date(2025, 3, 9), ny_to_utc(2025, 3, 9, 16), "US spring-forward day: 16:00 NY is EDT -> 20:00Z"),
        (dt.date(2025, 3, 10), ny_to_utc(2025, 3, 10, 16), "first full EDT Monday -> 20:00Z"),
        (dt.date(2025, 3, 28), ny_to_utc(2025, 3, 28, 16), "US-EDT/EU-GMT desync Friday -> 20:00Z (EU clock irrelevant)"),
        (dt.date(2025, 3, 30), ny_to_utc(2025, 3, 30, 16), "EU spring-forward Sunday (desync) -> 20:00Z unchanged"),
        (dt.date(2025, 3, 31), ny_to_utc(2025, 3, 31, 16), "Monday after EU spring forward -> 20:00Z unchanged"),
        (dt.date(2025, 7, 15), ny_to_utc(2025, 7, 15, 16), "deep summer EDT -> 20:00Z"),
        (dt.date(2025, 10, 24), ny_to_utc(2025, 10, 24, 16), "EU-GMT/US-EDT desync Friday -> 20:00Z"),
        (dt.date(2025, 10, 26), ny_to_utc(2025, 10, 26, 16), "EU fall-back Sunday (desync) -> 20:00Z unchanged"),
        (dt.date(2025, 10, 27), ny_to_utc(2025, 10, 27, 16), "Monday after EU fall back -> 20:00Z unchanged"),
        (dt.date(2025, 10, 31), ny_to_utc(2025, 10, 31, 16), "last EDT Friday -> 20:00Z"),
        (dt.date(2025, 11, 2), ny_to_utc(2025, 11, 2, 16), "US fall-back day: 16:00 NY is EST -> 21:00Z"),
        (dt.date(2025, 11, 3), ny_to_utc(2025, 11, 3, 16), "first full EST Monday -> 21:00Z"),
        (dt.date(2025, 12, 1), ny_to_utc(2025, 12, 1, 16), "deep winter EST -> 21:00Z"),
    ]

    def test_exact_instants_both_us_and_eu_transitions(self):
        for day, expected, note in self.PROBES:
            self.assertEqual(DA.flat_bar_instant_utc(day), expected,
                             f"{day} ({note}): expected {expected.isoformat()}")
            # EU transitions cannot move a New-York-anchored wall time
            self.assertEqual(expected.hour, 21 if self._is_est(day) else 20, note)

    @staticmethod
    def _is_est(day):
        return NY.utcoffset(dt.datetime(day.year, day.month, day.day, 16)) == dt.timedelta(hours=-5)

    def test_last_flat_bar_index_finds_exact_bar(self):
        for day, expected, _ in self.PROBES:
            rows = _hourly(expected - dt.timedelta(days=1), expected + dt.timedelta(hours=4))
            stamp_str = expected.strftime("%Y-%m-%d %H:%M:%S")
            want = next(i for i, r in enumerate(rows) if r["datetime"] == stamp_str)
            self.assertEqual(DA.last_flat_bar_index(rows, day), want, str(day))

    def test_missing_flat_bar_raises_no_trade(self):
        day, expected, _ = self.PROBES[4]  # 2025-03-28 20:00Z
        rows = _hourly(expected - dt.timedelta(days=1), expected + dt.timedelta(hours=4),
                       skip=(expected,))
        with self.assertRaises(DA.MissingBarNoTradeError) as ctx:
            DA.last_flat_bar_index(rows, day)
        self.assertIn(DA.MISSING_BAR_NO_TRADE, str(ctx.exception))

    def test_real_data_flat_bar_eurusd_winter_and_summer(self):
        rows, _ = td_loader.load_pair_h1("EUR/USD", DA.SNAPSHOT_DATA_ROOT)
        idx_w = DA.last_flat_bar_index(rows, dt.date(2025, 1, 15))
        idx_s = DA.last_flat_bar_index(rows, dt.date(2025, 7, 15))
        self.assertEqual(rows[idx_w]["datetime"], "2025-01-15 21:00:00")  # 16:00 EST
        self.assertEqual(rows[idx_s]["datetime"], "2025-07-15 20:00:00")  # 16:00 EDT
        # one-event lag: actionable only at the NEXT bar's open
        self.assertEqual(DA.next_actionable_index(idx_w), idx_w + 1)


class TestCompletedBarRule(unittest.TestCase):
    def test_one_event_lag(self):
        self.assertEqual(DA.next_actionable_index(0), 1)
        self.assertEqual(DA.next_actionable_index(41), 42)
        for bad in (-1, 1.5, "2", None, True):
            with self.assertRaises(ValueError):
                DA.next_actionable_index(bad)


class TestFoldsAndPurge(unittest.TestCase):
    FIRST = dt.datetime(2020, 1, 30, 7, tzinfo=UTC)
    LAST = dt.datetime(2026, 9, 2, tzinfo=UTC)

    def test_three_chronological_boundaries(self):
        bounds = DA.fold_boundaries(self.FIRST, self.LAST, n_folds=3)
        self.assertEqual(len(bounds), 3)
        self.assertEqual(bounds[0], self.FIRST)
        span = (self.LAST - self.FIRST) / 3
        self.assertEqual(bounds[1], self.FIRST + span)
        self.assertEqual(bounds[2], self.FIRST + 2 * span)
        self.assertTrue(bounds[0] < bounds[1] < bounds[2])
        for b in bounds:
            self.assertIsNotNone(b.tzinfo)

    def test_purge_ok(self):
        b1 = (self.FIRST + (self.LAST - self.FIRST) / 3)
        self.assertFalse(DA.purge_ok(b1, b1, warmup_hours=48))            # at boundary
        self.assertFalse(DA.purge_ok(b1 + dt.timedelta(hours=47), b1, 48))  # inside warmup
        self.assertTrue(DA.purge_ok(b1 + dt.timedelta(hours=48), b1, 48))   # exactly warmup clear
        self.assertTrue(DA.purge_ok(b1 - dt.timedelta(hours=1), b1, 48))    # earlier fold
        with self.assertRaises(ValueError):
            DA.purge_ok(b1, b1, warmup_hours=-1)


class TestD1Guard(unittest.TestCase):
    def test_canonical_h1_names_pass(self):
        names = ["EURUSD_1h_2020-02-03_a.json", "AUDUSD_1h_2023-08-25_2023-08-27_a.json"]
        self.assertEqual(DA.d1_never_in_scored(names), names)

    def test_d1_h4_truncated_duplicate_fail_closed(self):
        for bad in ["EURUSD_1day_2018-09-01_a.json",     # D1 is CONTEXT_ONLY
                    "EURUSD_4h_2018-09-01_a.json",       # H4 UNAVAILABLE_FAIL_CLOSED
                    "EURUSD_1h_2025-10-14_2026-07-01_TRUNCATED_a.json",
                    "EURUSD_1h_2026-01-05_2026-07-01_DUPLICATE_COPIES_OF_2026-01-05_a.json",
                    "EURUSD_1h_2020-02-03_b.json"]:      # pull-B is not a canonical scored name
            with self.assertRaises(DA.DataClassificationError):
                DA.d1_never_in_scored(["EURUSD_1h_2020-02-03_a.json", bad])


class TestS1BoundaryGuard(unittest.TestCase):
    def test_is_s1_path(self):
        for sealed in ["s1/x.json", "S1/live/orders.json", "research/stage1/a.py",
                       "stage_1/blotter.db", "stage-1/x", "abs/path/stage1_live/y"]:
            self.assertTrue(DA.is_s1_path(sealed), sealed)
        for fine in ["research/assets/forex_free_v2/data_authority.py",
                     "data_raw/forex_free_v1/EURUSD_1h_2020-02-03_a.json",
                     "tests/assets/forex_free_v2/test_data_authority.py",
                     "results/session1/cache/x"]:
            self.assertFalse(DA.is_s1_path(fine), fine)

    def test_s1_boundary_assert_raises_and_passes(self):
        with self.assertRaises(DA.S1BoundaryViolation):
            DA.s1_boundary_assert("s1/state.json")
        self.assertTrue(os.path.isabs(DA.s1_boundary_assert("research/control/x.json")))

    def test_snapshot_root_is_not_s1(self):
        # the read-only snapshot itself must never be mistaken for a sealed area
        self.assertFalse(DA.is_s1_path(DA.STAGED_MANIFEST_RELPATH))


class TestNoNetworkGuard(unittest.TestCase):
    def test_guard_blocks_socket_chokepoints_then_restores(self):
        real_socket = socket.socket
        real_create = socket.create_connection
        real_getaddr = socket.getaddrinfo
        with DA.no_network_guard():
            for name in ("socket", "create_connection", "getaddrinfo", "gethostbyname"):
                Attr = getattr(socket, name)
                with self.assertRaises(DA.NetworkAccessForbidden, msg=name):
                    if callable(Attr):
                        Attr()
            # an HTTP-client-style call path dies before any syscall
            with self.assertRaises(DA.NetworkAccessForbidden):
                socket.create_connection(("127.0.0.1", 1), timeout=0.1)
        self.assertIs(socket.socket, real_socket)
        self.assertIs(socket.create_connection, real_create)
        self.assertIs(socket.getaddrinfo, real_getaddr)

    def test_guard_restores_on_exception(self):
        real_socket = socket.socket
        with DA.no_network_guard():
            try:
                raise RuntimeError("boom")
            except RuntimeError:
                pass
        self.assertIs(socket.socket, real_socket)

    def test_module_source_is_offline_by_construction(self):
        self.assertTrue(DA.assert_offline_source())


if __name__ == "__main__":
    unittest.main()
