"""Near-real MTM valuation tests (task shv1-mtm-valuation).

ALL OFFLINE: prices are synthetic, hand-computed; the real Binance
network is never touched. The REAL strategy ledger of XSECT-FUND-CARRY-7D
is used READ-ONLY through its frozen byte-identical evidence copy
(sha256-pinned) and, when present on this machine, through the live
file with a before/after digest proof. The valuation pass NEVER writes
to ``results/``: appends go to a sandbox runtime root.
"""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path

import pytest

from research.shadow_v1 import events as shv1_events
from research.shadow_v1 import no_order
from research.shadow_v1 import valuation
from research.shadow_v1.dashboard import build_dashboard_snapshot, generate_html
from research.shadow_v1.families import FAMILY_CARRY, FAMILY_REGISTRY

WORKTREE = Path(__file__).resolve().parents[1]
FROZEN_CARRY_LEDGER = (
    WORKTREE
    / "research"
    / "control"
    / "prospective_shadow_v1"
    / "e"
    / "carry_ledger_frozen_XSECT-FUND-CARRY-7D.jsonl"
)
EXPECTED_CARRY_SHA256 = "7ea6b5023677082b5246826bcd044ef643ae66c3c91990f1c01d3296635f6068"
EXPECTED_CARRY_BYTES = 2445

#: Where the live strategy ledger may exist (first hit wins; may be
#: absent — the frozen copy above is the pinned evidence either way).
LIVE_CARRY_CANDIDATES = (
    WORKTREE / "results" / "prospective_shadow_v1" / "ledgers" / "XSECT-FUND-CARRY-7D.jsonl",
    WORKTREE.parent
    / "integration"
    / "results"
    / "prospective_shadow_v1"
    / "ledgers"
    / "XSECT-FUND-CARRY-7D.jsonl",
)

PRICE_SOURCE = "binance_fapi_premium_index_bulk"
MARK_TS = "2026-09-15T00:15:00Z"
OBSERVED_TS = "2026-09-15T00:15:27Z"
SOURCE_TS = "2026-09-15T00:15:25Z"
SOURCE_DIGEST = "ab" * 32

PACKAGE_ROOT = str(WORKTREE / "research" / "shadow_v1")


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------
def _event(family_id, scheduled, observed, fills, cash, equity, **overrides):
    payload = dict(
        family_id=family_id,
        arm_id=family_id,
        scheduled_decision_utc=scheduled,
        observed_at_utc=observed,
        feature_cutoff_utc=scheduled,
        data_snapshot_digest="d" * 64,
        code_freeze_sha="c" * 64,
        config_digest="1" * 64,
        cost_regime_digest="2" * 64,
        eligible_symbols=[],
        rejected_symbols_with_reason={},
        signal_values={},
        target_weights={},
        previous_weights={},
        virtual_fill_events=fills,
        fee=sum(f["fee"] for f in fills),
        slippage=sum(f["slippage_amount"] for f in fills),
        funding_cashflow=0.0,
        price_pnl=0.0,
        total_pnl=0.0,
        cash=cash,
        equity=equity,
        gross=0.0,
        net=0.0,
        btc_beta=None,
    )
    payload.update(overrides)
    return shv1_events.build_event(**payload)


def _fill(symbol, side, qty, ref, fill, fee, slip, ts="2026-09-15T00:00:00Z"):
    return {
        "symbol": symbol,
        "side": side,
        "qty": qty,
        "ref_price": ref,
        "fill_price": fill,
        "fee": fee,
        "slippage_amount": slip,
        "ts_utc": ts,
        "fill_id": None,
        "tick_size": 0.01,
    }


def write_ledger(path: Path, records):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as fh:
        for rec in records:
            line = json.dumps(rec, sort_keys=True, separators=(",", ":"))
            fh.write((line + "\n").encode("utf-8"))


def build_mark(family_id, ledger_path, prices, mark_ts=MARK_TS):
    return valuation.build_valuation_mark(
        family_id,
        str(ledger_path),
        prices,
        mark_ts,
        OBSERVED_TS,
        PRICE_SOURCE,
        SOURCE_TS,
        SOURCE_DIGEST,
    )


# ----------------------------------------------------------------------
# hand-computed sign correctness
# ----------------------------------------------------------------------
class TestSignCorrectness:
    def test_long_with_price_up_has_positive_unrealized_exact(self, tmp_path):
        # buy 2.0 @ fill 100.0, fee 0.6, slippage 0.4
        # cash = 100000 - (2*100 + 0.6) = 99799.4 (EXACT)
        ledger = tmp_path / "ledgers" / "FAM-X.jsonl"
        ev = _event(
            "FAM-X", "2026-09-15T00:00:00Z", "2026-09-15T00:15:15Z",
            [_fill("BTCUSDT", "buy", 2.0, 100.0, 100.0, 0.6, 0.4)],
            cash=100000.0 - (2.0 * 100.0 + 0.6),
            equity=100000.0 - 1.0,
        )
        write_ledger(ledger, [ev])
        mark = build_mark("FAM-X", ledger, {"BTCUSDT": 110.0})
        assert mark["status"] == "RUNNING"
        assert mark["accounting_status"] == "OK"
        assert mark["unrealized_pnl"] == pytest.approx(2.0 * (110.0 - 100.0))  # +20
        assert mark["unrealized_pnl"] > 0
        assert mark["equity"] == pytest.approx(99799.4 + 2.0 * 110.0)  # 100019.4
        assert mark["cash"] == pytest.approx(99799.4)
        assert mark["fees"] == 0.6 and mark["slippage"] == 0.4

    def test_short_with_price_down_has_positive_unrealized_exact(self, tmp_path):
        # sell 1.0 @ fill 50.0, fee 0.25, slippage 0.25
        # cash = 100000 + (1*50 - 0.25) = 100049.75 (EXACT)
        ledger = tmp_path / "ledgers" / "FAM-S.jsonl"
        ev = _event(
            "FAM-S", "2026-09-15T00:00:00Z", "2026-09-15T00:15:15Z",
            [_fill("ETHUSDT", "sell", 1.0, 50.0, 50.0, 0.25, 0.25)],
            cash=100000.0 + (1.0 * 50.0 - 0.25),
            equity=100000.0 - 0.5,
        )
        write_ledger(ledger, [ev])
        mark = build_mark("FAM-S", ledger, {"ETHUSDT": 45.0})
        assert mark["status"] == "RUNNING"
        assert mark["unrealized_pnl"] == pytest.approx((-1.0) * (45.0 - 50.0))  # +5
        assert mark["unrealized_pnl"] > 0
        assert mark["equity"] == pytest.approx(100049.75 - 45.0)  # 100004.75

    def test_short_with_price_up_has_negative_unrealized(self, tmp_path):
        ledger = tmp_path / "ledgers" / "FAM-S2.jsonl"
        ev = _event(
            "FAM-S2", "2026-09-15T00:00:00Z", "2026-09-15T00:15:15Z",
            [_fill("ETHUSDT", "sell", 1.0, 50.0, 50.0, 0.25, 0.25)],
            cash=100049.75, equity=99999.5,
        )
        write_ledger(ledger, [ev])
        mark = build_mark("FAM-S2", ledger, {"ETHUSDT": 55.0})
        assert mark["unrealized_pnl"] == pytest.approx(-5.0)


# ----------------------------------------------------------------------
# fees/slippage are cumulative books, NEVER recharged by marking
# ----------------------------------------------------------------------
class TestCostBooksNotRecharged:
    def test_two_consecutive_marks_identical_fee_fields(self, tmp_path):
        ledger = tmp_path / "ledgers" / "FAM-C.jsonl"
        ev = _event(
            "FAM-C", "2026-09-15T00:00:00Z", "2026-09-15T00:15:15Z",
            [_fill("BTCUSDT", "buy", 2.0, 100.0, 100.0, 0.6, 0.4)],
            cash=99799.4, equity=99999.4,
        )
        write_ledger(ledger, [ev])
        m1 = build_mark("FAM-C", ledger, {"BTCUSDT": 110.0}, "2026-09-15T00:15:00Z")
        m2 = build_mark("FAM-C", ledger, {"BTCUSDT": 120.0}, "2026-09-15T00:20:00Z")
        for key in ("fees", "slippage", "funding", "cash", "realized_pnl"):
            assert m1[key] == m2[key]
        assert m1["mark_id"] != m2["mark_id"]
        assert m2["unrealized_pnl"] == pytest.approx(40.0)
        assert m2["fees"] == 0.6  # still the booked fee, charged once

    def test_rebuild_twice_same_state(self, tmp_path):
        ledger = tmp_path / "ledgers" / "FAM-C2.jsonl"
        ev = _event(
            "FAM-C2", "2026-09-15T00:00:00Z", "2026-09-15T00:15:15Z",
            [_fill("BTCUSDT", "buy", 2.0, 100.0, 100.0, 0.6, 0.4)],
            cash=99799.4, equity=99999.4,
        )
        write_ledger(ledger, [ev])
        s1 = valuation.rebuild_positions(str(ledger))
        s2 = valuation.rebuild_positions(str(ledger))
        assert valuation.positions_digest(s1) == valuation.positions_digest(s2)


# ----------------------------------------------------------------------
# REAL CARRY reconciliation (read-only; byte-preservation proof)
# ----------------------------------------------------------------------
class TestRealCarryReconciliation:
    def test_frozen_copy_is_byte_identical_to_the_real_ledger(self):
        data = FROZEN_CARRY_LEDGER.read_bytes()
        assert len(data) == EXPECTED_CARRY_BYTES
        assert hashlib.sha256(data).hexdigest() == EXPECTED_CARRY_SHA256
        records = [json.loads(line) for line in data.decode().splitlines()]
        assert len(records) == 1
        fills = records[0]["virtual_fill_events"]
        assert len(fills) == 4

    def test_valuation_reproduces_the_four_positions_to_the_cent(self):
        """Independent hand recomputation of the REAL CARRY book."""
        record = json.loads(FROZEN_CARRY_LEDGER.read_text().splitlines()[0])
        # ---- independent replay (NOT via valuation.py) ----
        # The real ledger holds ONE event whose 4 fills open every
        # position from flat, so each entry prices at its own fill.
        cash = 100000.0
        cash += float(record["funding_cashflow"])  # settled funding delta
        positions = {}
        fees = slippage = 0.0
        for f in record["virtual_fill_events"]:
            signed = f["qty"] if f["side"] == "buy" else -f["qty"]
            cash -= signed * f["fill_price"] + f["fee"]
            fees += f["fee"]
            slippage += f["slippage_amount"]
            assert f["symbol"] not in positions  # fresh entries from flat
            positions[f["symbol"]] = {"qty": signed, "avg_price": f["fill_price"]}

        # the replayed cash must reproduce the recorded cash EXACTLY
        assert cash == record["cash"]
        assert fees == record["fee"] == 40.0
        assert slippage == record["slippage"]

        # test prices (arbitrary, hand-chosen, NOT the fill prices)
        test_prices = {
            "SOLUSDT": 105.0,
            "XRPUSDT": 1.40,
            "DOGEUSDT": 0.0800,
            "ETHUSDT": 2600.0,
        }
        expected_equity = cash + sum(
            positions[sym]["qty"] * price for sym, price in test_prices.items()
        )
        expected_unrealized = sum(
            positions[sym]["qty"] * (price - positions[sym]["avg_price"])
            for sym, price in test_prices.items()
        )

        mark = build_mark("XSECT-FUND-CARRY-7D", FROZEN_CARRY_LEDGER, test_prices)
        assert abs(mark["equity"] - expected_equity) < 0.005  # to the cent
        assert abs(mark["unrealized_pnl"] - expected_unrealized) < 0.005
        assert mark["cash"] == record["cash"]
        assert mark["fees"] == 40.0
        assert mark["slippage"] == pytest.approx(5.827486018214466)
        assert mark["funding"] == 0.0
        assert mark["status"] == "RUNNING"

        # and at the recorded fill prices the unrealized book is exactly 0
        fill_prices = {
            f["symbol"]: f["fill_price"] for f in record["virtual_fill_events"]
        }
        at_entry = build_mark(
            "XSECT-FUND-CARRY-7D", FROZEN_CARRY_LEDGER, fill_prices, "2026-09-15T00:20:00Z"
        )
        assert at_entry["unrealized_pnl"] == pytest.approx(0.0, abs=1e-9)

    def test_full_valuation_pass_leaves_frozen_ledger_unchanged(self, tmp_path):
        before = FROZEN_CARRY_LEDGER.read_bytes()
        state = valuation.rebuild_positions(str(FROZEN_CARRY_LEDGER))
        assert state["events_read"] == 1
        prices = {"SOLUSDT": 105.0, "XRPUSDT": 1.40, "DOGEUSDT": 0.0800, "ETHUSDT": 2600.0}
        mark = build_mark("XSECT-FUND-CARRY-7D", FROZEN_CARRY_LEDGER, prices)
        # append into a SANDBOX runtime root, never results/
        valuation.append_valuation_mark(str(tmp_path / "sandbox"), mark)
        after = FROZEN_CARRY_LEDGER.read_bytes()
        assert before == after
        assert hashlib.sha256(after).hexdigest() == EXPECTED_CARRY_SHA256

    def test_live_strategy_ledger_if_present_is_read_only_and_prefix_stable(self):
        live = next((p for p in LIVE_CARRY_CANDIDATES if p.exists()), None)
        if live is None:
            pytest.skip(
                "live XSECT-FUND-CARRY-7D strategy ledger not present on this "
                "machine at a known path (frozen copy covers the pinned bytes)"
            )
        before = live.read_bytes()
        # prefix proof: the live append-only ledger starts with the frozen bytes
        assert before.startswith(FROZEN_CARRY_LEDGER.read_bytes())
        state = valuation.rebuild_positions(str(live))
        assert state["events_read"] >= 1
        needed = sorted(valuation.open_positions(state))
        mark = build_mark(live.stem, live, {sym: 1.0 for sym in needed})
        assert mark["mark_id"]
        after = live.read_bytes()
        assert hashlib.sha256(after).hexdigest() == hashlib.sha256(before).hexdigest()

    def test_missing_price_for_open_position_is_fail_closed(self):
        record = json.loads(FROZEN_CARRY_LEDGER.read_text().splitlines()[0])
        fill_prices = {
            f["symbol"]: f["fill_price"] for f in record["virtual_fill_events"]
        }
        partial = dict(fill_prices)
        partial.pop("ETHUSDT")  # one open position without a price
        mark = build_mark("XSECT-FUND-CARRY-7D", FROZEN_CARRY_LEDGER, partial)
        assert mark["status"] == "UNAVAILABLE_FAIL_CLOSED"
        assert mark["accounting_status"] == "UNAVAILABLE_FAIL_CLOSED"
        assert mark["equity"] is None
        assert mark["unrealized_pnl"] is None
        assert mark["gross"] is None and mark["net"] is None
        assert mark["data_status"] == "DATA_BLOCKED"


# ----------------------------------------------------------------------
# flat sleeve / combined strict sum
# ----------------------------------------------------------------------
class TestFlatAndCombined:
    def test_flat_family_is_exactly_100000_flat_ok(self, tmp_path):
        empty_ledger = tmp_path / "ledgers" / "FAM-FLAT.jsonl"
        empty_ledger.parent.mkdir(parents=True, exist_ok=True)
        empty_ledger.write_bytes(b"")  # established empty ledger
        mark = build_mark("FAM-FLAT", empty_ledger, {})
        assert mark["status"] == "FLAT_OK"
        assert mark["equity"] == 100000.0
        assert mark["unrealized_pnl"] == 0.0
        assert mark["gross"] == 0.0 and mark["net"] == 0.0
        # absent ledger file is the same honest pre-first-event state
        mark_absent = build_mark("FAM-FLAT", tmp_path / "ledgers" / "nope.jsonl", {})
        assert mark_absent["status"] == "FLAT_OK"
        assert mark_absent["equity"] == 100000.0

    def test_btc_beta_is_honest_none(self, tmp_path):
        empty_ledger = tmp_path / "ledgers" / "FAM-B.jsonl"
        empty_ledger.parent.mkdir(parents=True, exist_ok=True)
        mark = build_mark("FAM-B", empty_ledger, {})
        assert mark["btc_beta"] is None

    def test_combined_is_strict_sum_at_common_mark(self, tmp_path):
        fids = sorted(FAMILY_REGISTRY)
        assert len(fids) == 4  # 3 founding + BTC4H-BANDRIDGE (mounted 2026-09-24)
        # sleeve A: long 2 @100 -> 99799.4 cash
        led_a = tmp_path / "ledgers" / f"{fids[0]}.jsonl"
        write_ledger(
            led_a,
            [_event(fids[0], "2026-09-15T00:00:00Z", "2026-09-15T00:15:15Z",
                    [_fill("BTCUSDT", "buy", 2.0, 100.0, 100.0, 0.6, 0.4)],
                    cash=99799.4, equity=99999.4)],
        )
        # sleeve B: short 1 @50 -> 100049.75 cash
        led_b = tmp_path / "ledgers" / f"{fids[1]}.jsonl"
        write_ledger(
            led_b,
            [_event(fids[1], "2026-09-15T00:00:00Z", "2026-09-15T00:15:15Z",
                    [_fill("ETHUSDT", "sell", 1.0, 50.0, 50.0, 0.25, 0.25)],
                    cash=100049.75, equity=99999.5)],
        )
        # sleeve C: flat
        led_c = tmp_path / "ledgers" / f"{fids[2]}.jsonl"
        led_c.parent.mkdir(parents=True, exist_ok=True)
        led_c.write_bytes(b"")
        # sleeve D (BANDRIDGE shape today: flat at seed)
        led_d = tmp_path / "ledgers" / f"{fids[3]}.jsonl"
        led_d.write_bytes(b"")

        marks = {}
        marks[fids[0]] = build_mark(fids[0], led_a, {"BTCUSDT": 110.0})
        marks[fids[1]] = build_mark(fids[1], led_b, {"ETHUSDT": 45.0})
        marks[fids[2]] = build_mark(fids[2], led_c, {})
        marks[fids[3]] = build_mark(fids[3], led_d, {})
        runtime = tmp_path / "runtime"
        for fid, mark in marks.items():
            assert valuation.append_valuation_mark(str(runtime), mark) == "appended"

        combined = valuation.combine_at_common_mark(
            {
                fid: [
                    {
                        "ts": m["mark_timestamp_utc"],
                        "equity": m["equity"],
                        "status": "OK" if m["accounting_status"] == "OK" else "GAP",
                    }
                ]
                for fid, m in marks.items()
            }
        )
        expected = (
            (99799.4 + 220.0)  # sleeve A
            + (100049.75 - 45.0)  # sleeve B
            + 100000.0  # sleeve C flat
            + 100000.0  # sleeve D flat
        )
        assert combined["status"] == "OK"
        assert combined["equity"] == pytest.approx(expected)
        assert combined["equity"] == pytest.approx(
            100019.4 + 100004.75 + 100000.0 + 100000.0
        )


# ----------------------------------------------------------------------
# idempotent appends / restart safety
# ----------------------------------------------------------------------
class TestIdempotentAppends:
    def test_restart_double_append_zero_duplicates_byte_identical(self, tmp_path):
        ledger = tmp_path / "ledgers" / "FAM-R.jsonl"
        write_ledger(
            ledger,
            [_event("FAM-R", "2026-09-15T00:00:00Z", "2026-09-15T00:15:15Z",
                    [_fill("BTCUSDT", "buy", 2.0, 100.0, 100.0, 0.6, 0.4)],
                    cash=99799.4, equity=99999.4)],
        )
        runtime = tmp_path / "runtime"
        seed = valuation.capital_seed_record("FAM-R", "2026-09-14T23:48:01Z")
        mark = build_mark("FAM-R", ledger, {"BTCUSDT": 110.0})
        path = Path(valuation.valuation_marks_path(str(runtime), "FAM-R"))
        # FIRST pass (like a worker run at cutover)
        assert valuation.append_valuation_mark(str(runtime), seed) == "appended"
        assert valuation.append_valuation_mark(str(runtime), mark) == "appended"
        first_bytes = path.read_bytes()
        first_ids = valuation.valuation_record_ids(path)
        # SECOND pass (restart/replay): everything skipped, bytes identical
        assert valuation.append_valuation_mark(str(runtime), seed) == "skipped_existing"
        assert valuation.append_valuation_mark(str(runtime), mark) == "skipped_existing"
        second_bytes = path.read_bytes()
        assert first_bytes == second_bytes
        assert len(valuation.valuation_record_ids(path)) == len(first_ids)
        ids = [r.get("mark_id") or r.get("seed_id")
               for r in valuation.read_valuation_records(path)]
        assert len(ids) == len(set(ids))  # zero duplicate mark/seed ids

    def test_deterministic_mark_ids_across_processes(self, tmp_path):
        ledger = tmp_path / "ledgers" / "FAM-D.jsonl"
        write_ledger(ledger, [])
        m1 = build_mark("FAM-D", ledger, {}, "2026-09-15T00:15:00Z")
        m2 = build_mark("FAM-D", ledger, {}, "2026-09-15T00:17:33Z")  # same window
        assert m1["mark_id"] == m2["mark_id"]
        assert m1["mark_timestamp_utc"] == "2026-09-15T00:15:00Z"
        assert m2["mark_timestamp_utc"] == "2026-09-15T00:15:00Z"
        expected = hashlib.sha256(
            b"PROSPECTIVE-SHADOW-V1|FAM-D|2026-09-15T00:15:00Z"
        ).hexdigest()[:32]
        assert m1["mark_id"] == expected


# ----------------------------------------------------------------------
# dashboard integration: counters + boundaries + seeds
# ----------------------------------------------------------------------
def _append_marks(runtime: Path, family_id, ledger: Path, specs):
    for stamp, price in specs:
        mark = build_mark(family_id, ledger, price, stamp)
        valuation.append_valuation_mark(str(runtime), mark)


class TestDashboardIntegration:
    def _scaffold(self, tmp_path):
        fid = FAMILY_CARRY
        ledger = tmp_path / "ledgers" / f"{fid}.jsonl"
        write_ledger(
            ledger,
            [_event(fid, "2026-09-15T00:00:00Z", "2026-09-15T00:15:15Z",
                    [_fill("BTCUSDT", "buy", 2.0, 100.0, 100.0, 0.6, 0.4)],
                    cash=99799.4, equity=99999.4)],
        )
        paths = {other: None for other in FAMILY_REGISTRY}
        paths[fid] = str(ledger)
        return fid, ledger, paths

    def test_valuation_marks_never_move_strategy_counters(self, tmp_path):
        fid, ledger, paths = self._scaffold(tmp_path)
        # production layout: the runtime root holds ledgers/ AND the
        # valuation_marks/ sibling the dashboard derives automatically
        runtime = tmp_path
        now = "2026-09-15T01:00:00Z"
        before = build_dashboard_snapshot(paths, now, shadow_start_utc="2026-09-14T23:48:01Z")
        counters_before = dict(before["families"][fid]["counters"])

        seed = valuation.capital_seed_record(fid, "2026-09-14T23:48:01Z")
        valuation.append_valuation_mark(str(runtime), seed)
        _append_marks(
            runtime, fid, ledger,
            [("2026-09-15T00:00:00Z", {"BTCUSDT": 100.0}),
             ("2026-09-15T00:05:00Z", {"BTCUSDT": 105.0})],
        )

        after = build_dashboard_snapshot(paths, now, shadow_start_utc="2026-09-14T23:48:01Z")
        counters_after = after["families"][fid]["counters"]
        assert counters_before == counters_after
        assert before["counters"] == after["counters"]
        assert (
            after["valuation"]["counters"]["valuation_mark_count"]
            == before["valuation"]["counters"]["valuation_mark_count"] + 2
        )
        assert after["valuation"]["counters"]["valuation_seed_count"] == 1

    def test_boundary_mark_validates_today_for_both_windows(self, tmp_path):
        fid, ledger, paths = self._scaffold(tmp_path)
        runtime = tmp_path / "runtime"
        # marks at 00:00Z (boundary) and 00:05Z; equity moves 99999.4 -> 100009.4
        _append_marks(
            runtime, fid, ledger,
            [("2026-09-15T00:00:00Z", {"BTCUSDT": 100.0}),
             ("2026-09-15T00:05:00Z", {"BTCUSDT": 105.0})],
        )
        snap = build_dashboard_snapshot(
            paths, "2026-09-15T00:07:00Z", shadow_start_utc="2026-09-14T23:48:01Z",
            valuation_marks_by_family={fid: str(valuation.valuation_marks_path(str(runtime), fid))},
        )
        vfam = snap["valuation"]["families"][fid]
        # 00:00 Asia/Ho_Chi_Minh == 17:00Z of the PRIOR day
        hcm = vfam["today"]["Asia/Ho_Chi_Minh"]
        utc = vfam["today"]["UTC"]
        assert hcm["status"] == "OK" and utc["status"] == "OK"
        assert hcm["window_start_utc"] == "2026-09-14T17:00:00Z"
        assert utc["window_start_utc"] == "2026-09-15T00:00:00Z"
        # BOTH windows start from the 00:00Z boundary mark (at/after rule)
        assert hcm["boundary_mark_ts"] == "2026-09-15T00:00:00Z"
        assert utc["boundary_mark_ts"] == "2026-09-15T00:00:00Z"
        assert hcm["pnl_usdt"] == pytest.approx(10.0)
        assert utc["pnl_usdt"] == pytest.approx(10.0)

    def test_combined_refuses_without_common_valid_mark(self, tmp_path):
        fids = sorted(FAMILY_REGISTRY)
        fid, ledger, paths = self._scaffold(tmp_path)
        runtime = tmp_path / "runtime"
        _append_marks(runtime, fid, ledger, [("2026-09-15T00:05:00Z", {"BTCUSDT": 105.0})])
        snap = build_dashboard_snapshot(
            paths, "2026-09-15T00:07:00Z", shadow_start_utc="2026-09-14T23:48:01Z",
            valuation_marks_by_family={f: None for f in fids},
        )
        combined = snap["valuation"]["combined"]
        assert combined["status"] == "NO_MARKS"  # explicit empty pin: no marks read

        # with marks pinned for ONE sleeve only: no common stamp -> fail closed
        snap2 = build_dashboard_snapshot(
            paths, "2026-09-15T00:07:00Z", shadow_start_utc="2026-09-14T23:48:01Z",
            valuation_marks_by_family={
                f: str(valuation.valuation_marks_path(str(runtime), f)) for f in fids
            },
        )
        combined2 = snap2["valuation"]["combined"]
        assert combined2["status"] == "UNAVAILABLE_FAIL_CLOSED"
        assert combined2["equity"] is None
        # per-sleeve newest is still shown with explicit ages
        per = combined2["per_sleeve_latest"][fid]
        assert per["mark_timestamp_utc"] == "2026-09-15T00:05:00Z"

    def test_seed_renders_as_seed_never_performance(self, tmp_path):
        fid, ledger, paths = self._scaffold(tmp_path)
        runtime = tmp_path / "runtime"
        seed = valuation.capital_seed_record(fid, "2026-09-14T23:48:01Z")
        assert seed["record_type"] == "CAPITAL_SEED_NO_MARK"
        assert seed["schema"] == "shv1_capital_seed@1"
        valuation.append_valuation_mark(str(runtime), seed)
        snap = build_dashboard_snapshot(
            paths, "2026-09-15T00:07:00Z", shadow_start_utc="2026-09-14T23:48:01Z",
            valuation_marks_by_family={
                f: str(valuation.valuation_marks_path(str(runtime), f))
                for f in sorted(FAMILY_REGISTRY)
            },
        )
        vfam = snap["valuation"]["families"][fid]
        assert vfam["seed_count"] == 1
        assert vfam["seeds"][0]["record_type"] == "CAPITAL_SEED_NO_MARK"
        assert vfam["mark_count"] == 0
        # the seed is NOT a performance point: series has no mark points
        assert vfam["series"] == []
        html = generate_html(snap)
        assert "CAPITAL_SEED_NO_MARK" in html
        assert "never performance" in html or "KHÔNG BAO GIỜ là hiệu suất" in html


# ----------------------------------------------------------------------
# ACTIVE_LIGHT: heavy lock + no-order surface
# ----------------------------------------------------------------------
WORKER_PATH = (
    WORKTREE
    / "research"
    / "control"
    / "prospective_shadow_v1"
    / "e"
    / "valuation_worker.py"
)


def _load_worker():
    import importlib.util

    spec = importlib.util.spec_from_file_location("shv1_valuation_worker", WORKER_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["shv1_valuation_worker"] = module
    spec.loader.exec_module(module)
    return module


def _synthetic_fetch(prices_by_symbol, source_ts=SOURCE_TS):
    def _fetch():
        return dict(prices_by_symbol), source_ts, SOURCE_DIGEST

    return _fetch


class TestActiveLight:
    def test_worker_once_loop_writes_marks_and_never_touches_heavy_lock(self, tmp_path):
        from research.governance import heavy_lock

        worker = _load_worker()
        fids = sorted(FAMILY_REGISTRY)
        runtime = tmp_path / "runtime"
        ledger = runtime / "ledgers" / f"{FAMILY_CARRY}.jsonl"
        write_ledger(
            ledger,
            [_event(FAMILY_CARRY, "2026-09-15T00:00:00Z", "2026-09-15T00:15:15Z",
                    [_fill("BTCUSDT", "buy", 2.0, 100.0, 100.0, 0.6, 0.4)],
                    cash=99799.4, equity=99999.4)],
        )
        heartbeat = worker.HeartbeatWriter(
            str(runtime / "runtime" / "valuation_heartbeat.json")
        )
        payload = worker.run_valuation_loop(
            "2026-09-14T23:48:01Z",
            str(runtime),
            now_utc="2026-09-15T00:15:27Z",
            fetch_fn=_synthetic_fetch({"BTCUSDT": 110.0, "ETHUSDT": 2500.0}),
            heartbeat=heartbeat,
        )
        heartbeat.close()
        # heartbeat contract (Q-13 + ACTIVE_LIGHT)
        for key in (
            "pid", "loop_count", "last_mark_per_family", "marks_written",
            "skipped_existing", "last_error", "heavy_lock_verdict",
            "valuation_heartbeat_inode_vs_path_check",
        ):
            assert key in payload
        inode_check = payload["valuation_heartbeat_inode_vs_path_check"]
        assert inode_check["match"] is True
        # the inspect verdict must be recorded faithfully each loop
        current = heavy_lock.inspect()["verdict"]
        assert payload["heavy_lock_verdict"] == current
        if current == "FREE_PROVEN":
            assert payload["heavy_lock_verdict"] == "FREE_PROVEN"
        assert payload["last_error"] is None
        assert payload["marks_written"] == 2 * len(fids)  # seed + mark per family
        # marks live in the SANDBOX runtime, never results/
        marks_path = valuation.valuation_marks_path(str(runtime), FAMILY_CARRY)
        assert marks_path.startswith(str(runtime))
        records = valuation.read_valuation_records(marks_path)
        ids = [r.get("mark_id") or r.get("seed_id") for r in records]
        assert len(ids) == len(set(ids))
        carry_mark = [r for r in records if r.get("mark_id")]
        assert carry_mark[-1]["equity"] == pytest.approx(100019.4)
        # flat families are FLAT_OK at exactly the seed (their OWN mark files)
        flat_fid = next(f for f in fids if f != FAMILY_CARRY)
        flat_records = valuation.read_valuation_records(
            valuation.valuation_marks_path(str(runtime), flat_fid)
        )
        flat_marks = [r for r in flat_records if r.get("mark_id")]
        assert flat_marks and flat_marks[-1]["status"] == "FLAT_OK"
        assert flat_marks[-1]["equity"] == 100000.0
        # heartbeat file exists under runtime/ (never results/ of the repo)
        assert (runtime / "runtime" / "valuation_heartbeat.json").exists()

    def test_worker_refuses_to_mark_before_shadow_start(self, tmp_path):
        worker = _load_worker()
        runtime = tmp_path / "runtime"
        payload = worker.run_valuation_loop(
            "2026-09-15T01:00:00Z",
            str(runtime),
            now_utc="2026-09-15T00:15:27Z",
            fetch_fn=_synthetic_fetch({}),
        )
        assert payload["pre_activation_quiet_noop"] is True
        assert payload["marks_written"] == 0
        assert not (runtime / "valuation_marks").exists()

    def test_price_fetch_failure_records_fail_closed_gap(self, tmp_path):
        worker = _load_worker()
        fids = sorted(FAMILY_REGISTRY)
        runtime = tmp_path / "runtime"
        ledger = runtime / "ledgers" / f"{FAMILY_CARRY}.jsonl"
        write_ledger(
            ledger,
            [_event(FAMILY_CARRY, "2026-09-15T00:00:00Z", "2026-09-15T00:15:15Z",
                    [_fill("BTCUSDT", "buy", 2.0, 100.0, 100.0, 0.6, 0.4)],
                    cash=99799.4, equity=99999.4)],
        )

        def _broken_fetch():
            raise OSError("network unreachable (synthetic)")

        payload = worker.run_valuation_loop(
            "2026-09-14T23:48:01Z",
            str(runtime),
            now_utc="2026-09-15T00:15:27Z",
            fetch_fn=_broken_fetch,
        )
        assert "network unreachable" in payload["last_error"]
        # the loop SURVIVED and wrote honest fail-closed evidence for the
        # open-position sleeve
        marks = valuation.read_valuation_records(
            valuation.valuation_marks_path(str(runtime), FAMILY_CARRY)
        )
        carry_marks = [r for r in marks if r.get("mark_id")]
        assert carry_marks, "fail-closed mark must still be appended"
        assert carry_marks[-1]["family_id"] == FAMILY_CARRY
        assert carry_marks[-1]["status"] == "UNAVAILABLE_FAIL_CLOSED"
        assert carry_marks[-1]["equity"] is None

    def test_valuation_module_imports_no_heavy_lock(self):
        source = (WORKTREE / "research" / "shadow_v1" / "valuation.py").read_text()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                assert not any(
                    "heavy_lock" in alias.name for alias in node.names
                ), f"valuation.py must not import heavy_lock: {node.names}"
            elif isinstance(node, ast.ImportFrom):
                assert "heavy_lock" not in (node.module or "")
        assert "heavy_lock.acquire" not in source
        assert "from research.governance" not in source

    def test_worker_source_has_no_heavy_lock_acquire(self):
        source = WORKER_PATH.read_text()
        assert "heavy_lock.acquire" not in source
        assert ".acquire(" not in source

    def test_no_order_surface_over_shadow_v1_including_valuation(self):
        hits = no_order.scan_for_forbidden_surface(PACKAGE_ROOT)
        assert hits == [], f"forbidden surface found: {hits[:5]}"
        scanned = no_order.scan_paths(PACKAGE_ROOT)
        assert any(p.endswith("valuation.py") for p in scanned)
        report = no_order.assert_no_order_surface(PACKAGE_ROOT)
        assert report["verdict"] == "NO_ORDER_SURFACE_CLEAN"

    def test_mark_proof_is_target_intent_only(self, tmp_path):
        ledger = tmp_path / "ledgers" / "FAM-P.jsonl"
        write_ledger(ledger, [])
        mark = build_mark("FAM-P", ledger, {})
        assert mark["no_order_proof"]["emitted_action_types"] == ["TARGET_INTENT"]
        assert isinstance(mark["no_order_proof"]["scan_digest"], str)


# ----------------------------------------------------------------------
# capital seed record
# ----------------------------------------------------------------------
class TestCapitalSeed:
    def test_seed_is_deterministic_and_not_a_mark(self):
        s1 = valuation.capital_seed_record("FAM-Z", "2026-09-14T23:48:01Z")
        s2 = valuation.capital_seed_record("FAM-Z", "2026-09-14T23:48:01Z")
        assert s1 == s2
        assert s1["record_type"] == "CAPITAL_SEED_NO_MARK"
        assert s1["ts_utc"] == "2026-09-14T23:48:01Z"
        assert s1["equity"] == 100000.0
        assert "NOT a market mark" in s1["note"]
        assert s1["no_order_proof"]["emitted_action_types"] == ["TARGET_INTENT"]

    def test_seed_and_mark_share_one_ledger_idempotently(self, tmp_path):
        runtime = tmp_path / "runtime"
        seed = valuation.capital_seed_record("FAM-Z", "2026-09-14T23:48:01Z")
        ledger = tmp_path / "ledgers" / "FAM-Z.jsonl"
        write_ledger(ledger, [])
        mark = build_mark("FAM-Z", ledger, {}, "2026-09-15T00:05:00Z")
        assert valuation.append_valuation_mark(str(runtime), seed) == "appended"
        assert valuation.append_valuation_mark(str(runtime), mark) == "appended"
        assert valuation.append_valuation_mark(str(runtime), seed) == "skipped_existing"
        path = valuation.valuation_marks_path(str(runtime), "FAM-Z")
        assert len(valuation.read_valuation_records(path)) == 2
