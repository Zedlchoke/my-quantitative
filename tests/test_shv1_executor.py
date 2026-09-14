"""Production-path tests for research/shadow_v1/executor.py (condition C1).

The ONLY executor under test is the production
``research.shadow_v1.executor.ForwardExecutor`` — no test-local executor
exists in this file. The feed is a synthetic in-memory PIT feed with the
same fetch surface as ``data_feed.KeylessBinanceFuturesClient`` (no
network); the adapter is a small scripted ``FamilyAdapter`` (the three
frozen family adapters keep their own identity suites in
test_shv1_families.py / test_shv1_engine_smoke.py).

Covers: plan section 8 events for due decisions; second run_due is
byte-identical with zero new events; POLICY REDUCING_SELL_NETS_POSITION
(a rebalance reducing sell succeeds without full-notional headroom while
an opening short still fails the cash checks); risk caps enforced
pre-fill (blocked + recorded, no fill); TARGET_INTENT-only emission;
DATA_BLOCKED under the deterministic event_id, never re-executed;
pending fill bar (a decision whose first post-decision bar has not
completed is not consumed); settled funding booked once while held; the
no-order scanner over research/shadow_v1/ stays at zero hits.
"""

import datetime as dt
from pathlib import Path

import pytest

from research.shadow_v1 import (
    accounting,
    data_feed,
    events,
    executor as executor_module,
    ledger,
    no_order,
    risk,
    scheduler,
    start_guard,
)
from research.shadow_v1.families import FamilyAdapter, IdentityConfigError

WORKTREE_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = WORKTREE_ROOT / "research" / "shadow_v1"

D1 = "2026-06-01T00:00:00Z"  # a Monday
D2 = "2026-06-08T00:00:00Z"
D3 = "2026-06-15T00:00:00Z"
PLUS_16M = "00:16:00Z"

BTC = "BTCUSDT"
ETH = "ETHUSDT"
BTC_PRICE = 50_000.0
ETH_PRICE = 2_000.0
TICK = 0.01

COST_BOOKS = {
    "LINEAGE_COST": {"fee_rate": 0.0004, "slippage_ticks": 1.0},
    "CURRENT_CONSERVATIVE_COST": {"fee_rate": 0.0005, "slippage_ticks": 1.0},
}


def iso(moment: dt.datetime) -> str:
    return moment.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse(text: str) -> dt.datetime:
    return dt.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(
        tzinfo=dt.timezone.utc
    )


def shift(stamp: str, **kwargs) -> str:
    return iso(parse(stamp) + dt.timedelta(**kwargs))


# ----------------------------------------------------------------------
# synthetic in-memory PIT feed (same fetch surface as the real client)
# ----------------------------------------------------------------------
class InMemoryFeed:
    def __init__(self):
        self.bars = {}  # symbol -> {open_dt: close_price}
        self.funding = {}  # symbol -> {(ft_dt): rate}

    def add_bar_series(self, symbol, start_open, count, price):
        for k in range(count):
            open_dt = start_open + k * dt.timedelta(minutes=15)
            self.bars.setdefault(symbol, {})[open_dt] = price

    def drop_bar(self, symbol, open_text):
        del self.bars[symbol][parse(open_text)]

    def add_funding(self, symbol, ft_text, rate):
        self.funding.setdefault(symbol, {})[parse(ft_text)] = rate

    def get_completed_bars(
        self, symbol, interval, start_exclusive, end_inclusive, cutoff_utc
    ):
        step = dt.timedelta(milliseconds=data_feed.INTERVAL_MS[interval])
        start_ms = int(data_feed.parse_iso_z(start_exclusive).timestamp() * 1000) + 1
        end_ms = int(data_feed.parse_iso_z(end_inclusive).timestamp() * 1000)
        cutoff_ms = int(data_feed.parse_iso_z(cutoff_utc).timestamp() * 1000)
        rows = []
        for open_dt in sorted(self.bars.get(symbol, {})):
            open_ms = int(open_dt.timestamp() * 1000)
            close_ms = int((open_dt + step).timestamp() * 1000)
            if open_ms < start_ms or open_ms > end_ms:
                continue
            if close_ms > cutoff_ms or close_ms > end_ms:
                continue
            rows.append(
                data_feed.Bar(
                    symbol=symbol,
                    interval=interval,
                    open_time_utc=iso(open_dt),
                    close_time_utc=iso(open_dt + step),
                    close_price=self.bars[symbol][open_dt],
                    quote_volume=1000.0,
                )
            )
        return rows

    def get_basis_buckets(
        self, pair, start_exclusive, end_inclusive, cutoff_utc, period="15m",
        contract_type="PERPETUAL",
    ):
        return []

    def get_settled_funding(self, symbol, start_exclusive, end_inclusive, cutoff_utc):
        cutoff_ms = int(data_feed.parse_iso_z(cutoff_utc).timestamp() * 1000)
        rows = []
        for ft_dt in sorted(self.funding.get(symbol, {})):
            if int(ft_dt.timestamp() * 1000) > cutoff_ms:
                continue
            rows.append(
                data_feed.FundingSettlement(
                    symbol=symbol,
                    funding_time_utc=iso(ft_dt),
                    funding_rate=self.funding[symbol][ft_dt],
                    mark_price=None,
                )
            )
        return rows


# ----------------------------------------------------------------------
# scripted adapter (the executor, not the adapter, is what is under test)
# ----------------------------------------------------------------------
class ScriptedAdapter(FamilyAdapter):
    FAMILY_ID = "SCRIPTED-REBALANCE"
    HISTORICAL_FAMILY_ID = "SCRIPTED-REBALANCE-HIST"
    HISTORICAL_VERDICT_LABEL = "CANDIDATE_FAIL"
    ARM_ID = "SCRIPTED-REBALANCE"

    def __init__(self, script):
        super().__init__(
            {},
            {
                "family_id": self.FAMILY_ID,
                "historical_family_id": self.HISTORICAL_FAMILY_ID,
                "historical_verdict_label": self.HISTORICAL_VERDICT_LABEL,
                "score_affecting_parameters": {},
            },
        )
        self.script = dict(script)

    @staticmethod
    def build_frozen(identity_params):
        return dict(identity_params)

    def validate_config(self, config, identity_entry):
        for key, expected in (
            ("family_id", self.FAMILY_ID),
            ("historical_family_id", self.HISTORICAL_FAMILY_ID),
            ("historical_verdict_label", self.HISTORICAL_VERDICT_LABEL),
        ):
            if identity_entry.get(key) != expected:
                raise IdentityConfigError(f"{key} disagrees with pinned identity")
        return {"frozen": {}, "engine": {}}

    def decide(self, data_snapshot, decision_utc, feature_cutoff_utc,
               previous_weights=None):
        target = self.script.get(decision_utc)
        if target is None:
            raise data_feed.DataBlocked(f"no scripted target for {decision_utc}")
        from research.shadow_v1.families import DecisionProposal

        return DecisionProposal(
            family_id=self.FAMILY_ID,
            arm_id=self.ARM_ID,
            eligible_symbols=tuple(sorted(target)),
            rejected_symbols_with_reason={},
            signal_values={},
            target_weights=dict(target),
            exit_policy="scheduled_rebalance",
            decision_utc=decision_utc,
            feature_cutoff_utc=feature_cutoff_utc,
            previous_weights=dict(previous_weights or {}),
        )


def make_feed():
    feed = InMemoryFeed()
    start_open = parse("2026-05-28T00:00:00Z")
    # through d3 + 2h so every fill bar through the last decision exists
    count = int((parse(D3) + dt.timedelta(hours=2) - start_open).total_seconds() // 900)
    feed.add_bar_series(BTC, start_open, count + 8, BTC_PRICE)
    feed.add_bar_series(ETH, start_open, count + 8, ETH_PRICE)
    return feed


def make_config(script, feed=None, caps=None, **overrides):
    cfg = {
        "code_freeze_sha": "shv1-executor-tests-code-freeze",
        "tick_size": TICK,
        "cost_books": COST_BOOKS,
        "primary_book": "CURRENT_CONSERVATIVE_COST",
        "caps": caps
        or risk.FamilyRiskCaps(
            family_id=ScriptedAdapter.FAMILY_ID,
            target_gross=0.9,
            hard_gross_cap=1.5,
            hard_abs_net_cap=1.0,
        ),
        "snapshot_spec": {
            "bars": {
                "symbols": [BTC, ETH],
                "interval": "15m",
                "lookback_seconds": 2 * 86400,
            }
        },
        "feature_cutoff_offset_seconds": 900.0,  # F6 pin: one frozen 15m interval
        "schedule": scheduler.SCHEDULE_WEEKLY_MONDAY_0000Z,
        "adapter": ScriptedAdapter(script),
    }
    cfg.update(overrides)
    return cfg


def make_executor(script, tmp_path, **overrides):
    feed = overrides.pop("feed", None) or make_feed()
    return executor_module.ForwardExecutor(
        ScriptedAdapter.FAMILY_ID,
        make_config(script, **overrides),
        str(tmp_path),
        feed,
        overrides.pop("shadow_start_utc", D1),
    ), feed


def ledger_file(tmp_path):
    return start_guard.prospective_ledger_root(str(tmp_path)) + (
        f"/{ScriptedAdapter.FAMILY_ID}{ledger.LEDGER_SUFFIX}"
    )


# ----------------------------------------------------------------------
# plan section 8 events + idempotency
# ----------------------------------------------------------------------
def test_due_decisions_produce_plan8_events_with_ok_statuses(tmp_path):
    exec_ = make_executor(
        {D1: {BTC: 0.9}, D2: {BTC: 0.2}, D3: {BTC: 0.2}}, tmp_path
    )[0]
    result = exec_.run_due(shift(D3, minutes=16))
    assert result["emitted"] == 3
    assert result["due"] == [D1, D2, D3]
    records = ledger.scan_events(ledger_file(tmp_path))
    assert len(records) == 3
    for record in records:
        events.validate_event_record(record)
        assert record["data_status"] == events.DATA_STATUS_OK
        assert record["accounting_status"] == events.ACCOUNTING_STATUS_OK
        assert record["risk_status"] == events.RISK_STATUS_OK
        assert record["no_order_proof"]["emitted_action_types"] == ["TARGET_INTENT"]
        assert isinstance(record["no_order_proof"]["scan_digest"], str)
        assert record["code_freeze_sha"] == "shv1-executor-tests-code-freeze"
        assert record["event_id"] == events.compute_event_id(
            ScriptedAdapter.FAMILY_ID, ScriptedAdapter.ARM_ID,
            record["scheduled_decision_utc"],
        )
    first = records[0]
    assert first["target_weights"] == {BTC: 0.9}
    assert len(first["virtual_fill_events"]) == 1
    fill = first["virtual_fill_events"][0]
    assert fill["side"] == "buy"
    assert fill["ref_price"] == pytest.approx(BTC_PRICE)
    assert fill["fill_price"] == pytest.approx(BTC_PRICE + TICK)  # buy at ref + tick
    assert first["cash"] == pytest.approx(100_000.0 - 1.8 * (BTC_PRICE + TICK) - 45.0)
    assert first["fee"] == pytest.approx(1.8 * BTC_PRICE * 0.0005)
    assert first["slippage"] == pytest.approx(1.8 * TICK)
    assert first["equity"] == pytest.approx(100_000.0 - 45.0 - 1.8 * TICK)
    assert first["gross"] == pytest.approx(
        1.8 * BTC_PRICE / (100_000.0 - 45.0 - 1.8 * TICK)
    )


def test_second_run_due_zero_new_events_byte_identical_ledger(tmp_path):
    exec_ = make_executor(
        {D1: {BTC: 0.9}, D2: {BTC: 0.2}, D3: {BTC: 0.2}}, tmp_path
    )[0]
    exec_.run_due(shift(D3, minutes=16))
    path = ledger_file(tmp_path)
    raw_before = ledger.read_raw_bytes(path)
    digest_before = ledger.ledger_digest(path)
    rerun = exec_.run_due(shift(D3, minutes=16))
    assert rerun["emitted"] == 0
    assert rerun["skipped_existing"] == 3
    assert rerun["ledger_digest"] == digest_before
    assert ledger.read_raw_bytes(path) == raw_before


# ----------------------------------------------------------------------
# POLICY: REDUCING_SELL_NETS_POSITION
# ----------------------------------------------------------------------
def test_reducing_sell_nets_position_without_full_notional_headroom(tmp_path):
    exec_, feed = make_executor({D1: {BTC: 0.9}, D2: {BTC: 0.2}}, tmp_path)
    exec_.run_due(shift(D1, minutes=16))
    sleeve = exec_.sleeve
    assert sleeve.positions[BTC].qty == pytest.approx(1.8)
    equity_before_sell = sleeve.equity_snapshot().equity
    gross_before_sell = 1.8 * BTC_PRICE

    result = exec_.run_due(shift(D2, minutes=16))
    assert result["emitted"] == 1
    records = ledger.scan_events(ledger_file(tmp_path))
    sell_record = records[-1]
    sells = [
        f for f in sell_record["virtual_fill_events"] if f["side"] == "sell"
    ]
    assert len(sells) == 1
    sold_qty = sells[0]["qty"]
    # positive evidence the OLD (overcounting) guard would have refused:
    # pre-sell gross + full sell notional exceeded equity by a wide margin
    assert gross_before_sell + sold_qty * BTC_PRICE > equity_before_sell + 50_000.0
    # the sell nets against the long: quantity reduced, not refused
    target_qty = 0.2 * equity_before_sell / BTC_PRICE
    assert sleeve.positions[BTC].qty == pytest.approx(target_qty, rel=1e-9)
    # proceeds credited cash after fees/slippage; modest starting cash left
    assert sleeve.cash > 60_000.0
    assert sell_record["accounting_status"] == events.ACCOUNTING_STATUS_OK
    assert sell_record["virtual_fill_events"][0]["fill_price"] == pytest.approx(
        BTC_PRICE - TICK
    )  # sell at ref - tick
    # equity moved by exactly the booked costs (identity asserted upstream)
    assert sell_record["equity"] == pytest.approx(
        equity_before_sell - sells[0]["fee"] - sells[0]["slippage_amount"]
    )


def test_opening_short_still_fails_cash_checks_when_headroom_insufficient(tmp_path):
    exec_ = make_executor(
        {D1: {BTC: 0.9}, D2: {BTC: 0.9, ETH: -0.2}}, tmp_path
    )[0]
    exec_.run_due(shift(D1, minutes=16))
    result = exec_.run_due(shift(D2, minutes=16))
    assert result["accounting_fail_closed"] == 1
    records = ledger.scan_events(ledger_file(tmp_path))
    failed = records[-1]
    assert failed["accounting_status"] == events.ACCOUNTING_STATUS_UNAVAILABLE
    assert failed["risk_status"] == events.RISK_STATUS_OK
    # the BTC trim occurred and is recorded honestly; the ETH short did NOT
    assert len(failed["virtual_fill_events"]) == 1
    assert failed["virtual_fill_events"][0]["symbol"] == BTC
    assert ETH not in exec_.sleeve.positions
    assert exec_.sleeve.fill_count == 2


def test_flip_through_zero_sell_keeps_full_no_leverage_checks(tmp_path):
    # fresh sleeve, no long: selling 2 BTC of notional > equity must refuse
    acct = accounting.SleeveAccount(
        sleeve_id="t",
        books={
            name: accounting.BookCostParams(
                fee_rate=cfg["fee_rate"], slippage_ticks=cfg["slippage_ticks"]
            )
            for name, cfg in COST_BOOKS.items()
        },
    )
    with pytest.raises(accounting.InsufficientCashError):
        acct.apply_fill(BTC, "sell", 2.0, 80_000.0, TICK, D1)
    assert acct.fill_count == 0
    assert acct.cash == pytest.approx(100_000.0)


# ----------------------------------------------------------------------
# risk caps enforced BEFORE any fill
# ----------------------------------------------------------------------
def test_cap_violating_target_blocked_and_recorded_without_fills(tmp_path):
    tight_caps = risk.FamilyRiskCaps(
        family_id=ScriptedAdapter.FAMILY_ID,
        target_gross=0.4,
        hard_gross_cap=1.5,
        hard_abs_net_cap=1.0,
        max_abs_weight=0.5,
    )
    exec_ = make_executor(
        {D1: {BTC: 0.9}, D2: {BTC: 0.4}}, tmp_path, caps=tight_caps
    )[0]
    result = exec_.run_due(shift(D2, minutes=16))
    assert result["risk_blocked"] == 1
    assert result["emitted"] == 1
    records = ledger.scan_events(ledger_file(tmp_path))
    blocked = records[0]
    assert blocked["risk_status"] == events.RISK_STATUS_BLOCKED
    assert blocked["target_weights"] == {}
    assert blocked["virtual_fill_events"] == []
    assert blocked["eligible_symbols"] == [BTC]  # the intent existed
    # d1 was blocked BEFORE any fill; d2 then executed its single buy
    assert exec_.sleeve.fill_count == 1
    assert exec_.sleeve.positions[BTC].qty > 0
    assert exec_.sleeve.decision_count == 2  # d1 blocked + d2 executed
    assert exec_.sleeve.order_intent_count == 2
    executed = records[1]
    assert executed["risk_status"] == events.RISK_STATUS_OK
    assert len(executed["virtual_fill_events"]) == 1


# ----------------------------------------------------------------------
# TARGET_INTENT only
# ----------------------------------------------------------------------
def test_only_target_intent_action_types_emitted(tmp_path):
    exec_ = make_executor({D1: {BTC: 0.9}, D2: {BTC: 0.2}}, tmp_path)[0]
    exec_.run_due(shift(D2, minutes=16))
    for record in ledger.scan_events(ledger_file(tmp_path)):
        assert record["no_order_proof"]["emitted_action_types"] == ["TARGET_INTENT"]
        events.validate_event_record(record)  # refuses any other action type


def test_no_order_scanner_stays_zero_hits_over_package(tmp_path):
    verdict = no_order.assert_no_order_surface(str(PACKAGE_ROOT))
    assert verdict["hits"] == 0
    assert verdict["verdict"] == "NO_ORDER_SURFACE_CLEAN"
    scanned = no_order.scan_paths(str(PACKAGE_ROOT))
    scanned_names = [Path(p).name for p in scanned]
    assert "executor.py" in scanned_names
    assert "start_guard.py" in scanned_names


# ----------------------------------------------------------------------
# DATA_BLOCKED semantics + pending fill bar
# ----------------------------------------------------------------------
def test_data_gap_produces_data_blocked_and_never_reexecutes(tmp_path):
    exec_, feed = make_executor({D1: {BTC: 0.9}, D2: {BTC: 0.2}}, tmp_path)
    gap_open = "2026-05-30T01:00:00Z"  # inside the d1 feature window
    feed.drop_bar(BTC, gap_open)
    result = exec_.run_due(shift(D1, minutes=16))
    assert result["data_blocked"] == 1
    records = ledger.scan_events(ledger_file(tmp_path))
    assert len(records) == 1
    blocked = records[0]
    assert blocked["data_status"] == events.DATA_STATUS_BLOCKED
    assert blocked["accounting_status"] == events.ACCOUNTING_STATUS_UNAVAILABLE
    assert blocked["risk_status"] == events.RISK_STATUS_OK
    assert blocked["event_id"] == events.compute_event_id(
        ScriptedAdapter.FAMILY_ID, ScriptedAdapter.ARM_ID, D1
    )
    assert blocked["data_snapshot_digest"].startswith("DATA_BLOCKED:")
    path = ledger_file(tmp_path)
    digest_before = ledger.ledger_digest(path)
    # heal the data: the blocked decision is NEVER re-executed
    feed.bars[BTC][parse(gap_open)] = BTC_PRICE
    rerun = exec_.run_due(shift(D1, minutes=16))
    assert rerun["emitted"] == 0
    assert rerun["skipped_existing"] == 1
    assert ledger.ledger_digest(path) == digest_before
    assert ledger.scan_events(path)[0]["data_status"] == events.DATA_STATUS_BLOCKED
    # forward progress continues for later decisions
    resumed = exec_.run_due(shift(D2, minutes=16))
    assert resumed["emitted"] == 1
    assert resumed["skipped_existing"] == 1


def test_fill_bar_pending_decision_not_consumed_then_executed(tmp_path):
    exec_ = make_executor({D1: {BTC: 0.9}}, tmp_path)[0]
    early = exec_.run_due(shift(D1, minutes=5))
    assert early["emitted"] == 0
    assert early["pending_fill_bar"] == [D1]
    assert ledger.read_raw_bytes(ledger_file(tmp_path)) is None
    result = exec_.run_due(shift(D1, minutes=16))
    assert result["emitted"] == 1
    assert result["pending_fill_bar"] == []
    assert len(ledger.scan_events(ledger_file(tmp_path))) == 1


def test_missing_fill_bar_with_later_bars_is_data_blocked(tmp_path):
    exec_, feed = make_executor({D1: {BTC: 0.9}}, tmp_path)
    feed.drop_bar(BTC, D1)  # the bar opening at the decision (the fill bar)
    result = exec_.run_due(shift(D1, minutes=45))
    assert result["data_blocked"] == 1
    records = ledger.scan_events(ledger_file(tmp_path))
    assert records[0]["data_status"] == events.DATA_STATUS_BLOCKED


# ----------------------------------------------------------------------
# settled funding booked once while held
# ----------------------------------------------------------------------
def test_settled_funding_booked_once_while_held_with_side_rule(tmp_path):
    exec_, feed = make_executor({D1: {BTC: 0.9}, D2: {BTC: 0.9}}, tmp_path)
    feed.add_funding(BTC, "2026-06-01T08:00:00Z", 0.0001)
    exec_.run_due(shift(D1, minutes=16))
    d1_record = ledger.scan_events(ledger_file(tmp_path))[0]
    assert d1_record["funding_cashflow"] == 0.0
    result = exec_.run_due(shift(D2, minutes=16))
    assert result["emitted"] == 1
    d2_record = ledger.scan_events(ledger_file(tmp_path))[-1]
    # long pays positive rate: cashflow = -rate * qty * mark
    assert d2_record["funding_cashflow"] == pytest.approx(-0.0001 * 1.8 * BTC_PRICE)
    assert exec_.sleeve.positions[BTC].funding_paid == pytest.approx(
        -0.0001 * 1.8 * BTC_PRICE
    )


def test_both_cost_books_keep_identical_quantities(tmp_path):
    exec_ = make_executor({D1: {BTC: 0.9}, D2: {BTC: 0.2}}, tmp_path)[0]
    exec_.run_due(shift(D2, minutes=16))
    sleeve = exec_.sleeve
    lineage = sleeve.books["LINEAGE_COST"]
    conservative = sleeve.books["CURRENT_CONSERVATIVE_COST"]
    assert lineage.fee > 0 and conservative.fee > 0
    # every fill books the SAME qty*ref into both books with each book's
    # own rate: fees scale exactly by the rate ratio, slippage is equal
    assert lineage.fee == pytest.approx(conservative.fee * 0.0004 / 0.0005)
    assert lineage.slippage == pytest.approx(conservative.slippage)
    # same quantities, different cost parameters: the equity views exist
    assert sleeve.equity_view("LINEAGE_COST") is not None
    assert sleeve.equity_view("CURRENT_CONSERVATIVE_COST") is not None
    assert sleeve.snapshot()["cash"] == sleeve.cash


# ----------------------------------------------------------------------
# forward-only guard wired through the production executor
# ----------------------------------------------------------------------
def test_executor_construction_without_shadow_start_refused_in_prospective(tmp_path):
    with pytest.raises(start_guard.StartGuardError):
        executor_module.ForwardExecutor(
            ScriptedAdapter.FAMILY_ID,
            make_config({D1: {BTC: 0.9}}),
            str(tmp_path),
            make_feed(),
            None,
        )


def test_run_due_before_shadow_start_is_quiet_noop(tmp_path):
    exec_ = executor_module.ForwardExecutor(
        ScriptedAdapter.FAMILY_ID,
        make_config({D1: {BTC: 0.9}}),
        str(tmp_path),
        make_feed(),
        D2,
    )
    result = exec_.run_due(shift(D1, minutes=16))
    assert result["due"] == []
    assert result["executed"] == []
    assert ledger.read_raw_bytes(ledger_file(tmp_path)) is None


def test_pre_start_decision_refused_by_guard_inside_executor(tmp_path):
    exec_ = executor_module.ForwardExecutor(
        ScriptedAdapter.FAMILY_ID,
        make_config({D1: {BTC: 0.9}, D2: {BTC: 0.2}}),
        str(tmp_path),
        make_feed(),
        D2,
    )
    with pytest.raises(start_guard.StartGuardError):
        exec_.run_due(shift(D2, minutes=16), from_utc=D1)
    assert ledger.read_raw_bytes(ledger_file(tmp_path)) is None
    with pytest.raises(start_guard.StartGuardError):
        exec_(ScriptedAdapter.FAMILY_ID, D1, "anyeventid")


def test_run_due_after_start_executes_boundary_decision(tmp_path):
    exec_ = executor_module.ForwardExecutor(
        ScriptedAdapter.FAMILY_ID,
        make_config({D2: {BTC: 0.9}}),
        str(tmp_path),
        make_feed(),
        D2,
    )
    result = exec_.run_due(shift(D2, minutes=16))
    assert result["emitted"] == 1  # decision == shadow_start is allowed
