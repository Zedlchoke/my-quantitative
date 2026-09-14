"""End-to-end VIRTUAL smoke: three families -> three sleeves + ledgers.

Rehearsal (P-23 class) of the full prospective pipeline on synthetic
data with NO network and NO orders:

- a deterministic formula-based feed produces 15m bars, 15m basis
  buckets and settled funding entirely in memory;
- each family adapter decides through its real ``decide`` path;
- the frozen A2 risk caps are applied through ``risk.check_and_apply``;
- virtual fills execute through the shared ``SleeveAccount`` surface at
  the fill reference (first completed 15m bar strictly after the
  decision); funding is booked once per settled event while held;
- ``scheduler.run_once`` drives the idempotent run loop into per-family
  JSONL ledgers under a temp runtime root.

Assertions: deterministic event_ids; second run adds ZERO events and
leaves byte-identical ledgers; every event carries all plan section 8
fields with data/accounting/risk/no_order statuses set; only
TARGET_INTENT action types exist; the combined view equals the sum of
sleeve equities at valid marks; the A2 no-order scanner over
research/shadow_v1/ (families/ included) reports zero forbidden
surfaces. An empty book for any family is a LOUD failure.
"""

import datetime as dt
import hashlib
import json
from pathlib import Path

import pytest

from research.shadow_v1 import (
    accounting,
    combined,
    events,
    ledger,
    no_order,
    risk,
    scheduler,
)
from research.shadow_v1.families import (
    FAMILY_REGISTRY,
    BasislvPremfadeAdapter,
    FamilySnapshot,
    IlliqAmihudAdapter,
    XsectFundCarryAdapter,
)

WORKTREE_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = WORKTREE_ROOT / "research" / "shadow_v1"

ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
START = "2026-03-02T00:00:00Z"  # a Monday
END = "2026-03-10T00:00:00Z"  # exclusive
BASE = dt.datetime(2026, 2, 1, tzinfo=dt.timezone.utc)
INTERVAL = dt.timedelta(minutes=15)

SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "LINKUSDT",
    "ADAUSDT",
    "LTCUSDT",
    "AVAXUSDT",
    "ATOMUSDT",
    "NEARUSDT",
    "ARBUSDT",
]
CARRY_UNIVERSE = [
    "ETHUSDT",
    "SOLUSDT",
    "BNBUSDT",
    "XRPUSDT",
    "DOGEUSDT",
    "LINKUSDT",
    "ADAUSDT",
]
LISTING_UTC = "2020-01-01T00:00:00Z"

ILLIQ_ENGINE = {
    "min_listing_age_days": 30.0,
    "min_daily_dollar_volume": 10_000.0,
    "btc_beta_tolerance": 1e-6,
    "hard_gross_cap": 1.0,
    "hard_abs_net_cap": 0.0,
}
COST_REGIME = {
    "LINEAGE_COST": {"fee_rate": 0.0004, "slippage_ticks": 1.0},
    "CURRENT_CONSERVATIVE_COST": {"fee_rate": 0.0005, "slippage_ticks": 1.0},
}
CODE_FREEZE_SHA = "shv1-smoke-rehearsal-code-freeze"
TICK_SIZE = 0.01
DUST_USDT = 1.0
#: Execution-only buffer of the rehearsal harness: target notionals are
#: scaled by (1 - buffer) so gross stays strictly below equity after
#: fees (no-leverage guard). Not an identity parameter.
COST_BUFFER = 0.005


def to_iso(moment: dt.datetime) -> str:
    return moment.astimezone(dt.timezone.utc).strftime(ISO_FMT)


def parse_iso(text: str) -> dt.datetime:
    return dt.datetime.strptime(text, ISO_FMT).replace(tzinfo=dt.timezone.utc)


def canonical_digest(payload) -> str:
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


# ----------------------------------------------------------------------
# deterministic synthetic market data (no network, formula-based)
# ----------------------------------------------------------------------
def bar_index(open_dt: dt.datetime) -> int:
    return int((open_dt - BASE).total_seconds() // 900)


def price_at(sym_idx: int, open_dt: dt.datetime) -> float:
    wobble = ((bar_index(open_dt) * 7 + sym_idx * 13) % 199) - 99
    return 10.0 * (1 + sym_idx) * (1.0 + wobble / 100_000.0)


def quote_volume_at(sym_idx: int, open_dt: dt.datetime) -> float:
    return 1000.0 + 10.0 * sym_idx


def premium_of(sym_idx: int) -> float:
    return ((sym_idx % 5) - 2) * 5e-4


def funding_rate_of(sym_idx: int) -> float:
    # realistic magnitude (~1e-5/settlement) so cumulative funding drag
    # stays inside the execution buffer over the smoke horizon
    return ((sym_idx % 7) - 3) * 1e-5


def generate_bars(sym_idx: int, start_open: dt.datetime, days: int):
    rows = []
    for k in range(days * 96):
        open_dt = start_open + k * INTERVAL
        rows.append(
            {
                "open_time_utc": to_iso(open_dt),
                "close_time_utc": to_iso(open_dt + INTERVAL),
                "close_price": price_at(sym_idx, open_dt),
                "quote_volume": quote_volume_at(sym_idx, open_dt),
            }
        )
    return rows


def generate_buckets(sym_idx: int, start_open: dt.datetime, days: int):
    rows = []
    for k in range(days * 96):
        open_dt = start_open + k * INTERVAL
        index_price = price_at(sym_idx, open_dt)
        rows.append(
            {
                "open_time_utc": to_iso(open_dt),
                "close_time_utc": to_iso(open_dt + INTERVAL),
                "futures_price": index_price * (1.0 + premium_of(sym_idx)),
                "index_price": index_price,
            }
        )
    return rows


def generate_funding(sym_idx: int, first_day: dt.date, days: int):
    rows = []
    for day_offset in range(days):
        day = first_day + dt.timedelta(days=day_offset)
        for hour in (0, 8, 16):
            rows.append(
                {
                    "funding_time_utc": to_iso(
                        dt.datetime(day.year, day.month, day.day, hour, tzinfo=dt.timezone.utc)
                    ),
                    "funding_rate": funding_rate_of(sym_idx),
                }
            )
    return rows


class FormulaFeed:
    """Builds PIT FamilySnapshots on demand from the deterministic formulas."""

    @staticmethod
    def snapshot(family_id: str, decision_utc: str, feature_cutoff_utc: str) -> FamilySnapshot:
        decision = parse_iso(decision_utc)
        bars = {}
        buckets = {}
        funding = {}
        if family_id == IlliqAmihudAdapter.FAMILY_ID:
            start = decision - dt.timedelta(days=29)
            start = dt.datetime.combine(start.date(), dt.time(0, 0), tzinfo=dt.timezone.utc)
            for idx, symbol in enumerate(SYMBOLS):
                bars[symbol] = generate_bars(idx, start, 29)
            return FamilySnapshot(
                bars=bars,
                funding_settlements={},  # price-only family ignores funding
                btc_betas={symbol: 1.0 for symbol in SYMBOLS},
                listing_utc={symbol: LISTING_UTC for symbol in SYMBOLS},
            )
        if family_id == BasislvPremfadeAdapter.FAMILY_ID:
            start = decision - dt.timedelta(days=29)
            start = dt.datetime.combine(start.date(), dt.time(0, 0), tzinfo=dt.timezone.utc)
            for idx, symbol in enumerate(SYMBOLS):
                buckets[symbol] = generate_buckets(idx, start, 29)
            return FamilySnapshot(
                basis_buckets=buckets,
                funding_settlements={},  # price-only family ignores funding
            )
        if family_id == XsectFundCarryAdapter.FAMILY_ID:
            first_day = (decision - dt.timedelta(days=9)).date()
            for idx, symbol in enumerate(SYMBOLS):
                funding[symbol] = generate_funding(idx, first_day, 10)
            return FamilySnapshot(funding_settlements=funding)
        raise AssertionError(f"unknown smoke family {family_id}")


# ----------------------------------------------------------------------
# virtual executor: adapter -> risk -> SleeveAccount -> plan section 8
# ----------------------------------------------------------------------
class SmokeExecutor:
    def __init__(self, runtime_root: str):
        self.feed = FormulaFeed()
        self.runtime_root = runtime_root
        self.books = {
            name: accounting.BookCostParams(
                fee_rate=params["fee_rate"], slippage_ticks=params["slippage_ticks"]
            )
            for name, params in COST_REGIME.items()
        }
        self.cost_regime_digest = canonical_digest(COST_REGIME)
        self.config_digests = {}
        self.adapters = {}
        self.sleeves = {}
        self.caps = {}
        self.last_decision = {}
        for family_id, cls in FAMILY_REGISTRY.items():
            engine = ILLIQ_ENGINE if cls is IlliqAmihudAdapter else {}
            entry = next(
                e
                for e in json.loads(
                    (WORKTREE_ROOT / "research" / "control" / "prospective_shadow_v1" / "identity" / "identity_recovery.json").read_text()
                )["families"]
                if e["family_id"] == family_id
            )
            config = cls.build_config(entry, engine)
            adapter = cls(config, entry)
            self.adapters[family_id] = adapter
            self.config_digests[family_id] = canonical_digest(adapter.config)
            self.sleeves[family_id] = accounting.SleeveAccount(
                sleeve_id=f"sleeve_{family_id}",
                books=self.books,
                starting_cash=100_000.0,
                primary_book=accounting.DEFAULT_PRIMARY_BOOK,
            )
            self.caps[family_id] = self._caps_for(family_id, adapter)
            self.last_decision[family_id] = None

    @staticmethod
    def _caps_for(family_id: str, adapter):
        frozen = adapter.config["frozen"]
        engine = adapter.config["engine"]
        if family_id == IlliqAmihudAdapter.FAMILY_ID:
            return risk.FamilyRiskCaps(
                family_id=family_id,
                target_gross=frozen["gross_by_construction"],
                hard_gross_cap=float(engine["hard_gross_cap"]),
                hard_abs_net_cap=float(engine["hard_abs_net_cap"]),
                dollar_neutral=True,
                btc_beta_neutral=True,
                btc_beta_tolerance=float(engine["btc_beta_tolerance"]),
            )
        params = json.loads(
            (WORKTREE_ROOT / "research" / "control" / "prospective_shadow_v1" / "identity" / "identity_recovery.json").read_text()
        )
        entry = next(e for e in params["families"] if e["family_id"] == family_id)
        return risk.caps_from_identity_params(family_id, entry["score_affecting_parameters"])

    def _feature_cutoff(self, family_id: str, decision_utc: str) -> str:
        if family_id == XsectFundCarryAdapter.FAMILY_ID:
            # settled funding usable iff fundingTime < decision: the stamp
            # itself is the natural declared boundary
            return decision_utc
        # bars/buckets must be completed strictly before the stamp
        return to_iso(parse_iso(decision_utc) - INTERVAL)

    def _fill_references(self, family_id: str, decision_utc: str):
        """Fill reference = close of the first completed 15m bar strictly
        after the decision (A2 fill convention); that bar opens at the
        stamp, so its reference close is price_at(stamp)."""
        decision = parse_iso(decision_utc)
        symbols = (
            CARRY_UNIVERSE
            if family_id == XsectFundCarryAdapter.FAMILY_ID
            else SYMBOLS
        )
        return {
            symbol: price_at(SYMBOLS.index(symbol), decision) for symbol in symbols
        }

    def _apply_settled_funding(self, family_id, sleeve, prev_utc, decision_utc, refs):
        if prev_utc is None:
            return 0.0
        prev = parse_iso(prev_utc)
        decision = parse_iso(decision_utc)
        booked = 0.0
        for symbol, pos in list(sleeve.positions.items()):
            if pos.qty == 0.0:
                continue
            idx = SYMBOLS.index(symbol)
            for row in generate_funding(idx, prev.date(), (decision.date() - prev.date()).days + 2):
                ft = parse_iso(row["funding_time_utc"])
                if prev <= ft < decision:
                    result = sleeve.apply_funding(
                        symbol, row["funding_time_utc"], row["funding_rate"], refs[symbol]
                    )
                    if result.booked:
                        booked += result.cashflow
        return booked

    def _sell_with_headroom(self, sleeve, symbol, remaining_qty, refs, decision_utc):
        """Execute a sell in slices that always satisfy the frozen A2
        no-leverage guard, which conservatively computes
        ``gross_before + fill_notional`` even for REDUCING sells: each
        slice must stay within the current equity-minus-gross headroom.
        Every slice frees headroom, so the loop converges geometrically."""
        fills = []
        remaining = remaining_qty
        for _ in range(60):
            equity = sleeve.equity_snapshot().equity
            gross = sum(
                abs(p.qty) * float(p.last_mark)
                for p in sleeve.positions.values()
                if p.qty != 0.0
            )
            headroom_notional = equity - gross
            if headroom_notional <= 0:
                raise RuntimeError(
                    f"LOUD FAILURE: no sell headroom for {symbol} at "
                    f"{decision_utc} (gross {gross:.2f} >= equity {equity:.2f})"
                )
            slice_notional = min(
                remaining * refs[symbol], headroom_notional * 0.5
            )
            if slice_notional < DUST_USDT:
                if remaining * refs[symbol] < DUST_USDT:
                    break
                raise RuntimeError(
                    f"LOUD FAILURE: could not complete sell of {symbol} at "
                    f"{decision_utc}; headroom {headroom_notional:.2f} too small"
                )
            slice_qty = min(remaining, slice_notional / refs[symbol])
            fills.append(
                sleeve.apply_fill(
                    symbol, "sell", slice_qty, refs[symbol], TICK_SIZE, decision_utc
                )
            )
            remaining -= slice_qty
            if remaining * refs[symbol] < DUST_USDT:
                break
        else:
            raise RuntimeError(
                f"LOUD FAILURE: sell of {symbol} did not converge at {decision_utc}"
            )
        return fills

    def _rebalance(self, sleeve, weights, refs, decision_utc):
        """Transition to the target book under the frozen no-margin/
        no-leverage guards: (A) reduce/close longs, (B) buy back shorts,
        (C) buy new longs, (D) open shorts last — sells run through
        headroom-aware slicing so gross only ever grows in the final
        phase, up to the buffered target strictly below equity."""
        equity = sleeve.equity_snapshot().equity
        scale = 1.0 - COST_BUFFER
        desired = {
            symbol: w * equity * scale / refs[symbol] for symbol, w in weights.items()
        }
        current = {
            symbol: pos.qty for symbol, pos in sleeve.positions.items() if pos.qty != 0.0
        }
        phase_reduce_longs = []  # (symbol, sell_qty): cur>0, trimming toward flat
        phase_close_shorts = []  # (symbol, buy_qty): cur<0, covering toward flat
        phase_open_longs = []  # (symbol, buy_qty)
        phase_open_shorts = []  # (symbol, sell_qty)
        for symbol in sorted(set(desired) | set(current)):
            target_qty = desired.get(symbol, 0.0)
            cur_qty = current.get(symbol, 0.0)
            delta = target_qty - cur_qty
            if abs(delta) * refs[symbol] < DUST_USDT:
                continue
            if delta > 0:
                if cur_qty < 0:
                    cover = min(delta, -cur_qty)  # buy back the short toward flat
                    phase_close_shorts.append((symbol, cover))
                    remainder = delta - cover  # residual opens the long
                else:
                    remainder = delta
                if remainder * refs[symbol] >= DUST_USDT:
                    phase_open_longs.append((symbol, remainder))
            else:
                if cur_qty > 0:
                    trim = min(-delta, cur_qty)  # sell the long toward flat
                    phase_reduce_longs.append((symbol, trim))
                    remainder = -delta - trim  # residual opens the short
                else:
                    remainder = -delta
                if remainder * refs[symbol] >= DUST_USDT:
                    phase_open_shorts.append((symbol, remainder))

        def execute_buys(plan):
            fills = []
            for symbol, qty in plan:
                assert qty > 0, (symbol, qty, "buy")
                fills.append(
                    sleeve.apply_fill(
                        symbol, "buy", qty, refs[symbol], TICK_SIZE, decision_utc
                    )
                )
            return fills

        fills = []
        for symbol, qty in phase_reduce_longs:
            fills += self._sell_with_headroom(sleeve, symbol, qty, refs, decision_utc)
        fills += execute_buys(phase_close_shorts)
        fills += execute_buys(phase_open_longs)
        for symbol, qty in phase_open_shorts:
            fills += self._sell_with_headroom(sleeve, symbol, qty, refs, decision_utc)
        return fills

    def __call__(self, family_id, scheduled_decision_utc, event_id):
        adapter = self.adapters[family_id]
        sleeve = self.sleeves[family_id]
        decision_utc = scheduled_decision_utc
        cutoff = self._feature_cutoff(family_id, decision_utc)
        snapshot = self.feed.snapshot(family_id, decision_utc, cutoff)
        refs = self._fill_references(family_id, decision_utc)

        sleeve.record_decision()
        sleeve.record_order_intent()
        sleeve.update_marks(refs, decision_utc)
        equity_before = sleeve.equity_snapshot(decision_utc).equity
        funding_delta = self._apply_settled_funding(
            family_id, sleeve, self.last_decision[family_id], decision_utc, refs
        )
        equity_after_funding = sleeve.equity_snapshot().equity
        fee_before = sleeve.books[sleeve.primary_book].fee
        slippage_before = sleeve.books[sleeve.primary_book].slippage

        previous_weights = dict(
            sleeve.exposure_snapshot().get("weights", {})
        )
        proposal = adapter.decide(snapshot, decision_utc, cutoff, previous_weights)

        betas = snapshot.btc_betas
        approved, block = risk.check_and_apply(proposal.target_weights, self.caps[family_id], betas)
        if block.blocked:
            fills = []
            final_weights = {}
        else:
            if not proposal.target_weights:
                raise RuntimeError(
                    f"LOUD FAILURE: {family_id} produced an empty book at "
                    f"{decision_utc} without a risk block"
                )
            fills = self._rebalance(sleeve, approved, refs, decision_utc)
            if not fills:
                raise RuntimeError(
                    f"LOUD FAILURE: {family_id} produced zero virtual fills "
                    f"for a non-empty book at {decision_utc}"
                )
            final_weights = approved
        self.last_decision[family_id] = decision_utc

        equity_after = sleeve.equity_snapshot(decision_utc).equity
        exposure = sleeve.exposure_snapshot(betas)
        book = sleeve.books[sleeve.primary_book]
        fee_delta = book.fee - fee_before
        slippage_delta = book.slippage - slippage_before
        price_pnl = equity_after - equity_after_funding
        total_pnl = equity_after - equity_before

        intent = no_order.emit_target_intent(
            cycle_id=events.CYCLE_ID,
            family_id=family_id,
            arm_id=adapter.ARM_ID,
            event_id=event_id,
            generated_utc=decision_utc,
            target_weights=final_weights,
            note="internal paper TARGET_INTENT (virtual fill path)",
        )
        assert intent["action_type"] == "TARGET_INTENT"

        return events.build_event(
            family_id=family_id,
            arm_id=adapter.ARM_ID,
            scheduled_decision_utc=decision_utc,
            observed_at_utc=decision_utc,
            feature_cutoff_utc=cutoff,
            data_snapshot_digest=canonical_digest(
                {
                    "bars": {s: list(v) for s, v in snapshot.bars.items()},
                    "basis_buckets": {s: list(v) for s, v in snapshot.basis_buckets.items()},
                    "funding_settlements": {
                        s: list(v) for s, v in snapshot.funding_settlements.items()
                    },
                }
            ),
            code_freeze_sha=CODE_FREEZE_SHA,
            config_digest=self.config_digests[family_id],
            cost_regime_digest=self.cost_regime_digest,
            eligible_symbols=list(proposal.eligible_symbols),
            rejected_symbols_with_reason=dict(proposal.rejected_symbols_with_reason),
            signal_values=dict(proposal.signal_values),
            target_weights=final_weights,
            previous_weights=previous_weights,
            virtual_fill_events=[f.as_dict() for f in fills],
            fee=fee_delta,
            slippage=slippage_delta,
            funding_cashflow=funding_delta,
            price_pnl=price_pnl,
            total_pnl=total_pnl,
            cash=sleeve.cash,
            equity=equity_after,
            gross=exposure["gross"],
            net=exposure["net"],
            btc_beta=exposure["btc_beta"],
            no_order_proof=no_order.no_order_proof(str(PACKAGE_ROOT)),
        )


@pytest.fixture()
def smoke(tmp_path):
    executor = SmokeExecutor(str(tmp_path))
    results = {}
    for family_id in FAMILY_REGISTRY:
        results[family_id] = scheduler.run_once(
            family_id,
            END,
            executor,
            str(tmp_path),
            from_utc=START,
            to_utc=END,
        )
    return executor, results, tmp_path


def test_smoke_three_families_all_events_written(smoke):
    executor, results, tmp_path = smoke
    expected_counts = {
        IlliqAmihudAdapter.FAMILY_ID: 2,  # Mondays 03-02, 03-09
        BasislvPremfadeAdapter.FAMILY_ID: 2,
        XsectFundCarryAdapter.FAMILY_ID: 8,  # daily 03-02..03-09
    }
    for family_id, count in expected_counts.items():
        assert results[family_id]["emitted"] == count
        assert results[family_id]["blocked"] == 0
        records = ledger.scan_events(ledger.ledger_path(str(tmp_path), family_id))
        assert len(records) == count


def test_smoke_event_ids_deterministic_and_plan8_complete(smoke):
    executor, results, tmp_path = smoke
    for family_id, adapter in executor.adapters.items():
        records = ledger.scan_events(ledger.ledger_path(str(tmp_path), family_id))
        for record in records:
            events.validate_event_record(record)
            expected_id = events.compute_event_id(
                family_id, adapter.ARM_ID, record["scheduled_decision_utc"]
            )
            assert record["event_id"] == expected_id
            assert record["data_status"] == events.DATA_STATUS_OK
            assert record["accounting_status"] == events.ACCOUNTING_STATUS_OK
            assert record["risk_status"] == events.RISK_STATUS_OK
            assert record["no_order_proof"]["emitted_action_types"] == ["TARGET_INTENT"]
            # empty books are a LOUD failure, never a silent pass
            assert record["target_weights"], f"empty book for {family_id}"
            assert record["virtual_fill_events"], f"no fills for {family_id}"
            assert record["eligible_symbols"]
            assert record["gross"] > 0.0


def test_smoke_second_run_zero_new_events_byte_identical_ledgers(smoke):
    executor, results, tmp_path = smoke
    digests_before = {
        family_id: ledger.ledger_digest(ledger.ledger_path(str(tmp_path), family_id))
        for family_id in FAMILY_REGISTRY
    }
    raw_before = {
        family_id: ledger.read_raw_bytes(ledger.ledger_path(str(tmp_path), family_id))
        for family_id in FAMILY_REGISTRY
    }
    for family_id in FAMILY_REGISTRY:
        rerun = scheduler.run_once(
            family_id, END, executor, str(tmp_path), from_utc=START, to_utc=END
        )
        assert rerun["emitted"] == 0
        assert rerun["skipped_existing"] > 0
        assert rerun["ledger_digest"] == digests_before[family_id]
        assert (
            ledger.read_raw_bytes(ledger.ledger_path(str(tmp_path), family_id))
            == raw_before[family_id]
        )


def test_smoke_combined_view_equals_sum_of_sleeve_equities(smoke):
    executor, results, tmp_path = smoke
    sleeves = {}
    for family_id, sleeve in executor.sleeves.items():
        points = {}
        for ts, equity in sleeve.equity_history:
            points[ts] = equity  # last observation wins per timestamp
        sleeves[family_id] = [
            {"ts": ts, "equity": equity, "status": "OK"}
            for ts, equity in sorted(points.items())
        ]
        assert sleeves[family_id], f"no equity marks recorded for {family_id}"
    series = combined.combined_equity_series(sleeves)
    ok_points = [p for p in series if p["status"] == "OK"]
    assert ok_points, "combined view has no valid mark"
    for point in ok_points:
        total = sum(
            next(
                p["equity"]
                for p in sleeves[family_id]
                if p["ts"] == point["ts"]
            )
            for family_id in sleeves
        )
        assert point["equity"] == pytest.approx(total, abs=1e-6)
    # plan section 9.8: the three isolated sleeves each start at exactly
    # 100,000 USDT (the recorded decision-time marks are post-trade, so
    # the initial capital contract is asserted on the sleeve baseline)
    assert all(
        sleeve.starting_cash == pytest.approx(100_000.0)
        for sleeve in executor.sleeves.values()
    )
    assert sum(s.starting_cash for s in executor.sleeves.values()) == pytest.approx(
        300_000.0
    )
    # every sleeve has at least one valid mark and stays above zero equity
    assert all(
        p["equity"] > 0 for pts in sleeves.values() for p in pts
    )


def test_smoke_no_order_scanner_covers_families_package():
    verdict = no_order.assert_no_order_surface(str(PACKAGE_ROOT))
    assert verdict["hits"] == 0
    assert verdict["verdict"] == "NO_ORDER_SURFACE_CLEAN"
    scanned = no_order.scan_paths(str(PACKAGE_ROOT))
    assert any("families" in path for path in scanned), (
        "families/ package must be inside the scanned surface"
    )
