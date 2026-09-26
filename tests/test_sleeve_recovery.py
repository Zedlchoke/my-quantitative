"""Boot-time sleeve recovery fixtures (incident 2026-09-26 root-cause fix).

INCIDENT: research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/
INCIDENT_psv1_restart_wipes_sleeve_accounts_2026-09-26.md — every
e-worker restart reset all four virtual sleeves (fresh
SleeveAccount(starting_cash=100_000) per build, no boot replay).
Engine fix (owner-delegated decision
OWNER_DELEGATED_DECISION_engine_fix_2026-09-26.json):
ForwardExecutor.recover_sleeve_from_ledger() replays the family's
append-only ledger into a fresh sleeve BEFORE the first run_due.

Fixtures:
(a) clean recovery: 2 buys + a settled-funding delta restore qty/cash/
    equity to the last recorded row; verdict RECOVERED_CLEAN;
(b) wipe-artifact discontinuity: a mid-ledger row whose recorded cash
    jumps +51.62 with zero fills (the incident shape) is reported as a
    RECOVERY_DISCONTINUITY while the replay keeps the pre-jump truth;
(c) restart-idempotence: the worker's recovery marker event_id is
    deterministic from the ledger's first row, so re-building the
    executors never duplicates it, and the marker id can never collide
    with a frozen decision stamp (run_due known_ids safety);
(d) empty/missing ledger: no-op recovery, no marker row;
(e) XSECT-shaped integration fixture through the REAL ForwardExecutor
    constructor: 4 positions (2 long / 2 short) + a wipe-artifact
    terminal row restore exactly, with the pre-wipe cash;
(f) apply_recorded_funding parity with the live apply_funding booking;
(g) apply_recorded_fill parity with apply_fill's mutation path, and the
    measured reason the live admission guard is NOT re-run on replay
    (an opening short refused live is exactly the case a stale-mark
    replay must NOT re-litigate — see the real-ledger dry-run);
(h) lineage reset: a mid-ledger WIPE rebalance row (the measured real
    XSECT row 2026-09-19 shape — previous_weights {} with cash equal to
    a fresh 100k minus its own rebalance costs) is a lineage boundary:
    the replay reseeds to the fresh lineage and re-verifies, while a
    trailing zero-fill artifact row keeps the fill truth.

All tests are offline: recovery never fetches through the feed.
"""

from pathlib import Path

import pytest

from research.shadow_v1 import (
    accounting,
    events,
    executor as executor_module,
    ledger,
    risk,
    scheduler,
)
from research.shadow_v1.families import FamilyAdapter
from research.control.prospective_shadow_v1.e import shadow_worker as sw

FAMILY = "RECOVERY-FIXTURE"
ARM = "RECOVERY-FIXTURE"
BTC = "BTCUSDT"
ETH = "ETHUSDT"

D1 = "2026-09-20T00:00:00Z"
D2 = "2026-09-21T00:00:00Z"

COST_BOOKS = {
    "LINEAGE_COST": {"fee_rate": 0.0004, "slippage_ticks": 1.0},
    "CURRENT_CONSERVATIVE_COST": {"fee_rate": 0.0005, "slippage_ticks": 1.0},
}
PRIMARY = "CURRENT_CONSERVATIVE_COST"
TICK = 0.01
START_CASH = 100_000.0


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------
class _ForbiddenFeed:
    """A feed recovery must never touch."""

    def __getattr__(self, name):
        raise AssertionError(f"recovery must never fetch via feed.{name}")


class _StubAdapter(FamilyAdapter):
    FAMILY_ID = FAMILY
    HISTORICAL_FAMILY_ID = FAMILY + "-HIST"
    HISTORICAL_VERDICT_LABEL = "CANDIDATE_FAIL"
    ARM_ID = ARM

    def __init__(self):
        super().__init__(
            {},
            {
                "family_id": self.FAMILY_ID,
                "historical_family_id": self.HISTORICAL_FAMILY_ID,
                "historical_verdict_label": self.HISTORICAL_VERDICT_LABEL,
                "score_affecting_parameters": {},
            },
        )

    @staticmethod
    def build_frozen(identity_params):
        return dict(identity_params)

    def validate_config(self, config, identity_entry):
        return {"frozen": {}, "engine": {}}

    def decide(self, *args, **kwargs):  # pragma: no cover - never called
        raise AssertionError("recovery tests must never decide")


def make_executor(tmp_path) -> executor_module.ForwardExecutor:
    """A REAL ForwardExecutor (full __init__) with a stub adapter; the
    recovery path under test touches only sleeve/ledger state."""
    cfg = {
        "code_freeze_sha": "sleeve-recovery-tests-code-freeze",
        "tick_size": TICK,
        "cost_books": dict(COST_BOOKS),
        "primary_book": PRIMARY,
        "caps": risk.FamilyRiskCaps(
            family_id=FAMILY,
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
        "feature_cutoff_offset_seconds": 900.0,
        "schedule": scheduler.SCHEDULE_DAILY_0000Z,
        "adapter": _StubAdapter(),
    }
    return executor_module.ForwardExecutor(
        FAMILY, cfg, str(tmp_path), _ForbiddenFeed(), "2026-09-19T00:00:00Z"
    )


def ledger_file(tmp_path) -> str:
    return str(Path(tmp_path) / "ledgers" / f"{FAMILY}{ledger.LEDGER_SUFFIX}")


def make_books(params_by_name):
    return {
        name: accounting.BookCostParams(**params)
        for name, params in params_by_name.items()
    }


def scratch_account() -> accounting.SleeveAccount:
    """A truthful live twin: the rows' recorded cash/equity are produced
    by the SAME apply_fill / funding mutations the live executor
    performed (identical float arithmetic)."""
    return accounting.SleeveAccount(
        sleeve_id="scratch",
        books=make_books(COST_BOOKS),
        starting_cash=START_CASH,
        primary_book=PRIMARY,
    )


def fill_spec(symbol, side, qty, ref, ts):
    return (symbol, side, qty, ref, ts)


def apply_fill_spec(account, spec):
    symbol, side, qty, ref, ts = spec
    event = account.apply_fill(symbol, side, qty, ref, TICK, ts)
    return dict(event.as_dict(), tick_size=TICK)


def decision_row(family, arm, ts, fills, funding_delta, cash, equity):
    """One plan-section-8 record (validated by build_event)."""
    return events.build_event(
        family_id=family,
        arm_id=arm,
        scheduled_decision_utc=ts,
        observed_at_utc=ts,
        feature_cutoff_utc=ts,
        data_snapshot_digest="recovery-fixture",
        code_freeze_sha="sleeve-recovery-tests-code-freeze",
        config_digest="recovery-fixture",
        cost_regime_digest="recovery-fixture",
        eligible_symbols=[],
        rejected_symbols_with_reason={},
        signal_values={},
        target_weights={},
        previous_weights={},
        virtual_fill_events=fills,
        fee=0.0,
        slippage=0.0,
        funding_cashflow=funding_delta,
        price_pnl=0.0,
        total_pnl=0.0,
        cash=cash,
        equity=equity,
        gross=0.0,
        net=0.0,
        btc_beta=0.0,
    )


def build_ledger(tmp_path, row_specs):
    """Drive a truthful scratch account through the row specs and append
    the resulting records to the fixture family's ledger.

    Spec row keys: ts, fills (list of fill_spec), funding (delta in the
    ledger convention: cash += delta), cash_override / equity (write an
    artifact value instead of the truthful one), extra (post-build row
    decorations, as the executor appends retirement flags).
    Returns (rows, scratch).
    """
    scratch = scratch_account()
    rows = []
    for spec in row_specs:
        funding = float(spec.get("funding") or 0.0)
        if funding != 0.0:
            scratch.apply_recorded_funding(funding)
        fill_events = [
            apply_fill_spec(scratch, fill) for fill in spec.get("fills", [])
        ]
        cash = spec.get("cash_override")
        if cash is None:
            cash = scratch.cash
        equity = spec.get("equity")
        if equity is None:
            equity = scratch.equity_snapshot(ts_utc=spec["ts"]).equity
        row = decision_row(
            FAMILY, ARM, spec["ts"], fill_events, funding, cash, equity
        )
        row.update(spec.get("extra") or {})
        rows.append(row)
    path = ledger_file(tmp_path)
    for row in rows:
        ledger.append_event(path, row)
    return rows, scratch


# ----------------------------------------------------------------------
# (a) clean recovery: fills + funding restore the last recorded row
# ----------------------------------------------------------------------
def test_a_clean_recovery_restores_last_row(tmp_path):
    rows, _ = build_ledger(
        tmp_path,
        [
            {"ts": D1, "fills": [fill_spec(BTC, "buy", 1.0, 50_000.0, D1)]},
            {
                "ts": D2,
                "fills": [fill_spec(ETH, "buy", 0.5, 2_000.0, D2)],
                "funding": -3.25,  # settled cost paid: cash decreases
            },
        ],
    )
    ex = make_executor(tmp_path)
    summary = ex.recover_sleeve_from_ledger()

    assert summary["verdict"] == "RECOVERED_CLEAN"
    assert summary["discontinuities"] == []
    assert summary["rows_replayed"] == 2
    assert summary["fills_replayed"] == 2
    assert summary["funding_booked"] == pytest.approx(-3.25)
    assert summary["positions_after"] == {
        BTC: pytest.approx(1.0),
        ETH: pytest.approx(0.5),
    }

    last = rows[-1]
    assert summary["cash_after"] == pytest.approx(last["cash"], abs=0.01)
    assert summary["equity_after"] == pytest.approx(last["equity"], abs=0.01)

    # cost books carry the replayed economics (identical delta on every
    # book — the verified parity property of the recorded-funding path)
    for name in COST_BOOKS:
        book = ex.sleeve.books[name]
        assert book.fee > 0.0 and book.slippage > 0.0
        assert book.funding_cashflow == pytest.approx(-3.25)

    # idempotence: a second recovery rebuilds the identical state
    again = ex.recover_sleeve_from_ledger()
    assert again == summary
    assert ex.sleeve.cash == pytest.approx(last["cash"], abs=0.01)


def test_a_recovery_sets_last_decision_utc(tmp_path):
    build_ledger(
        tmp_path,
        [
            {"ts": D1, "fills": [fill_spec(BTC, "buy", 1.0, 50_000.0, D1)]},
            {"ts": D2, "fills": [fill_spec(ETH, "buy", 0.5, 2_000.0, D2)]},
        ],
    )
    ex = make_executor(tmp_path)
    ex.recover_sleeve_from_ledger()
    # settled-funding fetch bounds need the last executed decision stamp
    assert ex._last_decision_utc == D2


# ----------------------------------------------------------------------
# (b) wipe-artifact discontinuity (the incident shape)
# ----------------------------------------------------------------------
def test_b_wipe_artifact_row_reported_replay_keeps_pre_jump_truth(tmp_path):
    # 1 BTC bought at 50,000 with tick 0.01 costs the primary book
    # exactly 51.62 USDT (fill 50,000.01 + fee 25.0 + slip 1.0 x qty...
    # engineered so the truthful cash is START_CASH - 51.62), then the
    # artifact row resets the book to exactly 100,000 with zero fills —
    # the recorded +51.62 jump of the incident.
    qty = 51.62 / (50_000.0 + TICK + 50_000.0 * COST_BOOKS[PRIMARY]["fee_rate"])
    rows, _ = build_ledger(
        tmp_path,
        [
            {"ts": D1, "fills": [fill_spec(BTC, "buy", qty, 50_000.0, D1)]},
            {
                "ts": D2,
                "fills": [],
                "cash_override": START_CASH,
                "equity": START_CASH,
            },
        ],
    )
    truthful_cash = rows[0]["cash"]
    assert START_CASH - truthful_cash == pytest.approx(51.62, abs=0.01)

    ex = make_executor(tmp_path)
    summary = ex.recover_sleeve_from_ledger()

    assert summary["verdict"] == "RECOVERED_WITH_DISCONTINUITIES"
    assert len(summary["discontinuities"]) == 1
    disc = summary["discontinuities"][0]
    assert disc["kind"] == "RECOVERY_DISCONTINUITY"
    assert disc["row_ts"] == D2
    assert disc["recorded_cash"] == pytest.approx(START_CASH)
    assert disc["replay_cash"] == pytest.approx(truthful_cash)
    assert disc["delta"] == pytest.approx(truthful_cash - START_CASH, abs=1e-9)

    # fills are the authority: the position and pre-jump cash survive
    assert summary["positions_after"] == {BTC: pytest.approx(qty)}
    assert summary["cash_after"] == pytest.approx(truthful_cash, abs=0.01)


# ----------------------------------------------------------------------
# (c) restart-idempotence of the worker recovery marker
# ----------------------------------------------------------------------
def _future_shadow_start():
    return "2030-01-07T00:00:00Z"


def _seed_carry_ledger(runtime_root: Path) -> Path:
    carry = sw.FAMILY_CARRY
    ledger_path = runtime_root / "ledgers" / f"{carry}{ledger.LEDGER_SUFFIX}"
    ledger_path.parent.mkdir(parents=True)
    scratch = accounting.SleeveAccount(
        sleeve_id="seed",
        books=make_books(sw.cost_books_for(carry)),
        starting_cash=START_CASH,
        primary_book=PRIMARY,
    )
    ts = "2026-09-25T00:00:00Z"
    fill = dict(
        scratch.apply_fill("ETHUSDT", "buy", 0.2, 2_000.0, 0.01, ts).as_dict(),
        tick_size=0.01,
    )
    row = decision_row(
        carry, carry, ts, [fill], 0.0, scratch.cash,
        scratch.equity_snapshot(ts_utc=ts).equity,
    )
    ledger.append_event(str(ledger_path), row)
    return ledger_path


def test_c_marker_row_deterministic_and_never_duplicated(tmp_path):
    carry = sw.FAMILY_CARRY
    runtime_root = Path(tmp_path) / "runtime"
    ledger_path = _seed_carry_ledger(runtime_root)
    seeded_rows = ledger.scan_events(str(ledger_path))
    assert len(seeded_rows) == 1
    anchor = seeded_rows[0]["scheduled_decision_utc"]

    execs1 = sw.build_executors(
        str(runtime_root), _future_shadow_start(), feed=_ForbiddenFeed()
    )
    rows_after_first = ledger.scan_events(str(ledger_path))
    markers = [
        r for r in rows_after_first if r.get("schema") == sw.RECOVERY_SCHEMA
    ]
    assert len(markers) == 1
    marker = markers[0]
    expected_id = events.compute_event_id(carry, carry, f"RECOVERY-{anchor}")
    assert marker["event_id"] == expected_id
    assert marker["scheduled_decision_utc"] == anchor  # scan-compat anchor
    assert marker["summary"]["fills_replayed"] == 1
    assert marker["summary"]["verdict"] == "RECOVERED_CLEAN"
    # the executor's sleeve was recovered from the seeded ledger
    assert execs1[carry].sleeve.cash == pytest.approx(
        seeded_rows[0]["cash"], abs=0.01
    )
    assert execs1[carry].sleeve.positions["ETHUSDT"].qty == pytest.approx(0.2)

    raw_after_first = ledger.read_raw_bytes(str(ledger_path))

    # second boot: the deterministic id is skipped, bytes never rewritten
    execs2 = sw.build_executors(
        str(runtime_root), _future_shadow_start(), feed=_ForbiddenFeed()
    )
    assert ledger.read_raw_bytes(str(ledger_path)) == raw_after_first
    markers2 = [
        r
        for r in ledger.scan_events(str(ledger_path))
        if r.get("schema") == sw.RECOVERY_SCHEMA
    ]
    assert len(markers2) == 1 and markers2[0] == marker
    assert execs2[carry].sleeve.cash == pytest.approx(
        seeded_rows[0]["cash"], abs=0.01
    )

    # run_due known_ids safety: the marker id can never collide with a
    # frozen decision stamp of the family
    stamps = scheduler.pending_decisions(
        carry,
        "2026-01-01T00:00:00Z",
        "2031-01-01T00:00:00Z",
        schedule=scheduler.FAMILY_SCHEDULES[carry],
    )
    decision_ids = {events.compute_event_id(carry, carry, s) for s in stamps}
    assert expected_id not in decision_ids
    # run_due's known_ids are exactly the ledger's event ids: the seeded
    # decision id (a genuine stamp) plus the marker id — nothing else.
    assert ledger.event_ids(str(ledger_path)) == {
        events.compute_event_id(carry, carry, anchor),
        expected_id,
    }


def test_c_families_that_never_held_anything_get_no_marker(tmp_path):
    runtime_root = Path(tmp_path) / "runtime_empty"
    execs = sw.build_executors(
        str(runtime_root), _future_shadow_start(), feed=_ForbiddenFeed()
    )
    for family_id, ex in execs.items():
        assert ledger.scan_events(ex.ledger_file) == []
        summary = ex.recover_sleeve_from_ledger()
        assert summary["verdict"] == "RECOVERED_CLEAN"
        assert summary["rows_replayed"] == 0
        assert summary["fills_replayed"] == 0
        assert sw._append_recovery_marker(ex, summary) is None
        assert ledger.scan_events(ex.ledger_file) == []


# ----------------------------------------------------------------------
# (d) empty ledger: no-op
# ----------------------------------------------------------------------
def test_d_empty_or_missing_ledger_is_a_noop(tmp_path):
    ex = make_executor(tmp_path)  # no ledger file written at all
    summary = ex.recover_sleeve_from_ledger()
    assert summary["verdict"] == "RECOVERED_CLEAN"
    assert summary["rows_replayed"] == 0
    assert summary["fills_replayed"] == 0
    assert summary["funding_booked"] == 0.0
    assert summary["discontinuities"] == []
    assert summary["positions_after"] == {}
    assert summary["cash_after"] == pytest.approx(START_CASH)
    assert sw._append_recovery_marker(ex, summary) is None
    assert not Path(ledger_file(tmp_path)).exists()

    # an existing but EMPTY ledger file behaves identically
    Path(ledger_file(tmp_path)).parent.mkdir(parents=True, exist_ok=True)
    Path(ledger_file(tmp_path)).write_bytes(b"")
    summary2 = ex.recover_sleeve_from_ledger()
    assert summary2["verdict"] == "RECOVERED_CLEAN"
    assert summary2["rows_replayed"] == 0
    assert sw._append_recovery_marker(ex, summary2) is None


# ----------------------------------------------------------------------
# (e) XSECT-shaped fixture through the REAL executor: 4 positions
#     (2 long / 2 short) + wipe-artifact terminal row
# ----------------------------------------------------------------------
def test_e_xsect_shape_four_positions_restored_with_pre_wipe_cash(tmp_path):
    ada, bnb, doge, xrp = "ADAUSDT", "BNBUSDT", "DOGEUSDT", "XRPUSDT"
    rows, scratch = build_ledger(
        tmp_path,
        [
            {
                "ts": D1,
                "fills": [
                    fill_spec(ada, "sell", 0.2, 1.0, D1),    # short
                    fill_spec(bnb, "buy", 0.2, 300.0, D1),   # long
                    fill_spec(doge, "sell", 0.2, 0.15, D1),  # short
                    fill_spec(xrp, "buy", 0.2, 0.5, D1),     # long
                ],
            },
            # the terminal wipe artifact (real row-12 shape): zero fills,
            # book reset to exactly 100,000, retirement decoration.
            {
                "ts": D2,
                "fills": [],
                "cash_override": START_CASH,
                "equity": START_CASH,
                "extra": {"retired": True},
            },
        ],
    )
    pre_wipe_cash = rows[0]["cash"]
    pre_wipe_equity = rows[0]["equity"]
    ex = make_executor(tmp_path)
    summary = ex.recover_sleeve_from_ledger()

    assert summary["verdict"] == "RECOVERED_WITH_DISCONTINUITIES"
    assert summary["fills_replayed"] == 4
    positions = summary["positions_after"]
    assert len(positions) == 4
    assert positions[ada] == pytest.approx(-0.2)
    assert positions[bnb] == pytest.approx(0.2)
    assert positions[doge] == pytest.approx(-0.2)
    assert positions[xrp] == pytest.approx(0.2)
    assert summary["cash_after"] == pytest.approx(pre_wipe_cash, abs=0.01)
    assert summary["cash_after"] != pytest.approx(START_CASH, abs=0.01)
    assert summary["equity_after"] == pytest.approx(pre_wipe_equity, abs=0.01)
    assert summary["discontinuities"][0]["row_ts"] == D2

    # the restored book is measurable at the fill marks (no mark gap)
    exposure = ex.sleeve.exposure_snapshot()
    assert exposure["status"] == "OK"
    expected_gross_notional = (
        0.2 * 1.0 + 0.2 * 300.0 + 0.2 * 0.15 + 0.2 * 0.5
    )
    assert exposure["gross"] == pytest.approx(
        expected_gross_notional / pre_wipe_equity, rel=1e-6
    )


# ----------------------------------------------------------------------
# (h) lineage reset: a mid-ledger wipe rebalance row (the measured real
#     XSECT row 2026-09-19 shape: previous_weights {} + cash == fresh
#     100k minus its own costs) is a lineage boundary — the replay
#     reseeds, the later rows re-verify, and a trailing zero-fill
#     artifact row keeps the fill truth
# ----------------------------------------------------------------------
def test_h_lineage_reset_row_reseeds_replay(tmp_path):
    # OLD lineage: one buy, truthfully recorded
    scratch = scratch_account()
    ts0 = "2026-09-17T00:00:00Z"
    old_fill = apply_fill_spec(scratch, fill_spec(BTC, "buy", 1.0, 50_000.0, ts0))
    row_old = decision_row(
        FAMILY, ARM, ts0, [old_fill], 0.0, scratch.cash,
        scratch.equity_snapshot(ts_utc=ts0).equity,
    )
    path = ledger_file(tmp_path)
    ledger.append_event(path, row_old)

    # LINEAGE BOUNDARY row (real row-2026-09-19 shape): the live book was
    # wiped to a fresh 100k BEFORE this row; the rebalance executed on
    # the fresh book. Recorded cash = START_CASH - this row's own costs,
    # previous_weights {} (flat evidence).
    fresh = accounting.SleeveAccount(
        sleeve_id="fresh-lineage",
        books=make_books(COST_BOOKS),
        starting_cash=START_CASH,
        primary_book=PRIMARY,
    )
    ts1 = "2026-09-19T00:00:00Z"
    f1 = apply_fill_spec(fresh, fill_spec(ETH, "buy", 2.0, 2_000.0, ts1))
    f2 = apply_fill_spec(fresh, fill_spec(BTC, "sell", 0.5, 50_000.0, ts1))
    row_reset = decision_row(
        FAMILY, ARM, ts1, [f1, f2], 0.0, fresh.cash,
        fresh.equity_snapshot(ts_utc=ts1).equity,
    )
    row_reset["previous_weights"] = {}  # already {} from build_event
    ledger.append_event(path, row_reset)

    # next truthful row of the NEW lineage: a funding cost + a top-up buy
    ts2 = "2026-09-20T00:00:00Z"
    funding = -4.0
    fresh.apply_recorded_funding(funding)
    f3 = apply_fill_spec(fresh, fill_spec(ETH, "buy", 0.5, 2_000.0, ts2))
    row_next = decision_row(
        FAMILY, ARM, ts2, [f3], funding, fresh.cash,
        fresh.equity_snapshot(ts_utc=ts2).equity,
    )
    ledger.append_event(path, row_next)

    # trailing zero-fill artifact (the row-12 shape): book reset claim
    ts3 = "2026-09-21T00:00:00Z"
    row_artifact = decision_row(
        FAMILY, ARM, ts3, [], 0.0, START_CASH, START_CASH
    )
    ledger.append_event(path, row_artifact)

    ex = make_executor(tmp_path)
    summary = ex.recover_sleeve_from_ledger()

    assert summary["verdict"] == "RECOVERED_WITH_DISCONTINUITIES"
    kinds = {(d["row_ts"], d["action"]) for d in summary["discontinuities"]
             if d["kind"] == "RECOVERY_DISCONTINUITY"}
    assert (ts1, "RESEEDED_TO_FRESH_LINEAGE") in kinds
    assert (ts3, "TRUTH_KEPT") in kinds
    reset_entry = next(
        d for d in summary["discontinuities"]
        if d.get("row_ts") == ts1 and d["kind"] == "RECOVERY_DISCONTINUITY"
    )
    assert reset_entry["flat_evidenced"] is True
    assert reset_entry["reseeded_verifies"] is True
    assert summary["reseeded_at"] == ts1

    # the recovered book IS the new lineage's book (old-lineage BTC long
    # discarded with the wiped account; the artifact's 100k claim refused)
    assert summary["positions_after"] == {
        ETH: pytest.approx(2.5),
        BTC: pytest.approx(-0.5),
    }
    assert summary["cash_after"] == pytest.approx(row_next["cash"], abs=0.01)
    assert summary["cash_after"] != pytest.approx(START_CASH, abs=0.01)
    assert summary["funding_booked"] == pytest.approx(-4.0)
    # rows 1 and 2 verified before the reset; row 3 re-verified after it;
    # only the reset row and the artifact are disclosed discontinuities
    assert summary["rows_replayed"] == 4
    assert summary["fills_replayed"] == 3
def test_f_recorded_funding_parity_with_apply_funding():
    def open_long():
        acc = accounting.SleeveAccount(
            sleeve_id="parity",
            books=make_books(COST_BOOKS),
            starting_cash=START_CASH,
            primary_book=PRIMARY,
        )
        acc.apply_fill(ETH, "buy", 2.0, 2_000.0, TICK, "2026-09-20T00:00:00Z")
        return acc

    live = open_long()
    result = live.apply_funding(ETH, "2026-09-20T08:00:00Z", 0.0001, 2_010.0)
    assert result.booked is True
    assert result.cashflow < 0  # positive rate: a LONG pays (cost)

    replay = open_long()
    booked = replay.apply_recorded_funding(result.cashflow)
    assert booked.booked is True
    assert booked.cashflow == result.cashflow

    # identical cash and per-book funding to the live booking path
    assert replay.cash == live.cash
    for name, book in live.books.items():
        assert replay.books[name].funding_cashflow == book.funding_cashflow

    # a positive delta is a credit RECEIVED (mirrors a short's receipt /
    # negative-rate long); zero is an explicit no-op
    replay.apply_recorded_funding(1.5)
    assert replay.cash == pytest.approx(live.cash + 1.5)
    zero = replay.apply_recorded_funding(0.0)
    assert zero.booked is False and zero.reason == "zero_delta"

    # disclosed limitation: per-position attribution is not
    # reconstructible from the aggregate per-decision delta
    assert replay.positions[ETH].funding_paid == 0.0
    assert live.positions[ETH].funding_paid == pytest.approx(result.cashflow)


# ----------------------------------------------------------------------
# (g) apply_recorded_fill parity with apply_fill, and the measured
#     reason the live admission guard is NOT re-run on replay
# ----------------------------------------------------------------------
def test_g_recorded_fill_parity_with_apply_fill():
    seq = [
        (BTC, "buy", 1.0, 50_000.0, D1),
        (ETH, "sell", 0.75, 2_000.0, D1),   # opening short
        (BTC, "sell", 0.4, 50_100.0, D2),   # reducing sell
        (ETH, "buy", 0.25, 1_990.0, D2),    # buy back toward flat
    ]
    live = accounting.SleeveAccount(
        sleeve_id="live",
        books=make_books(COST_BOOKS),
        starting_cash=START_CASH,
        primary_book=PRIMARY,
    )
    replayed = accounting.SleeveAccount(
        sleeve_id="replayed",
        books=make_books(COST_BOOKS),
        starting_cash=START_CASH,
        primary_book=PRIMARY,
    )
    for symbol, side, qty, ref, ts in seq:
        live.apply_fill(symbol, side, qty, ref, TICK, ts)
        replayed.apply_recorded_fill(symbol, side, qty, ref, TICK, ts)

    assert replayed.cash == live.cash
    assert replayed.realized_pnl == pytest.approx(live.realized_pnl)
    assert replayed.fill_count == live.fill_count
    for symbol, pos in live.positions.items():
        other = replayed.positions[symbol]
        assert other.qty == pytest.approx(pos.qty)
        assert other.avg_price == pytest.approx(pos.avg_price)
        assert other.last_mark == pytest.approx(pos.last_mark)
    for name, book in live.books.items():
        assert replayed.books[name].fee == pytest.approx(book.fee)
        assert replayed.books[name].slippage == pytest.approx(book.slippage)


def test_g_recorded_fill_does_not_rerun_live_admission_guard():
    # MEASURED reason (incident 2026-09-26 fix): an opening short whose
    # gross notional exceeds the flat-sleeve equity is lawfully refused
    # by the LIVE path, but the recorded ledger carries fills that passed
    # live admission with decision-time marks the replay cannot
    # reconstruct — re-running the guard on stale replay marks would
    # spuriously refuse them (dry-run on the real XSECT/ILLIQ ledgers).
    ref, qty = 50_000.0, 2.1  # gross 105,000 > 100,000 equity

    live = accounting.SleeveAccount(
        sleeve_id="live",
        books=make_books(COST_BOOKS),
        starting_cash=START_CASH,
        primary_book=PRIMARY,
    )
    with pytest.raises(accounting.InsufficientCashError):
        live.apply_fill(BTC, "sell", qty, ref, TICK, D1)

    replayed = accounting.SleeveAccount(
        sleeve_id="replayed",
        books=make_books(COST_BOOKS),
        starting_cash=START_CASH,
        primary_book=PRIMARY,
    )
    event = replayed.apply_recorded_fill(BTC, "sell", qty, ref, TICK, D1)
    assert event.fill_price == pytest.approx(ref - TICK)
    assert replayed.positions[BTC].qty == pytest.approx(-qty)
    assert replayed.cash == pytest.approx(
        START_CASH + qty * (ref - TICK) - qty * ref * COST_BOOKS[PRIMARY]["fee_rate"]
    )
    # invalid fills are still refused by the primitive itself
    with pytest.raises(accounting.AccountingError):
        replayed.apply_recorded_fill(BTC, "sell", -1.0, ref, TICK, D1)
    with pytest.raises(accounting.AccountingError):
        replayed.apply_recorded_fill(BTC, "hold", qty, ref, TICK, D1)
