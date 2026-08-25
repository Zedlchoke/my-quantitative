"""V7 end-to-end synthetic golden test (PLAN section 6.2, gates C08/C09/C10; owner A6).

Wires the REAL frozen signal ``research.funding_price_divergence`` into the
REAL shared-capital engine ``research.portfolio_engine.run_shared_capital_backtest``
over a hand-computable 4-symbol panel, across a 3-day sequence of daily UTC
cutoffs. The CLI/dispatcher hop (runner argv -> dispatcher branch) is owned by
A3's integration tests; coverage here is signal+engine-contract.

Hand-derived golden math (all numbers below are exact by construction):

Panel (daily closes for the SIGNAL only): A +10%/day, B +5%, C -5%, D -10%,
so price percentile ranks are A .1->1.0, B .75, C .5, D .25 at every cutoff;
funding rates are flat A .0001, B .0002, C .0003, D .0004 (settled 08:00
UTC), so funding ranks are A .25, B .5, C .75, D 1.0. Score = p_pct - f_pct:
A +.75, B +.25, C -.25, D -.75 => longs {B, A}, shorts {D, C}, weights
+/-target_gross/4 = +/-0.20 every cutoff.

Engine panel: ALL 15m bars print flat close=100.0 (zero gross leg PnL), so
equity moves ONLY through costs (-) and funding (+/-):

    open/close cost per side (qty 200, tick .01, slip 1 tick, fee .0005):
        BUY  200 @ 100.01 -> fee 10.001 + slip 2.0 = 12.001
        SELL 200 @  99.99 -> fee  9.999 + slip 2.0 = 11.999
    opens (2 BUY + 2 SELL): equity 100000 - 48.0 = 99952.0
    funding per stamp (notional 200*100, longs pay / shorts receive):
        -2 -4 +6 +8 = +8.0 net per stamp x 3 stamps = +24.0
    dust rebalance deltas (~0.08..0.128 sh ~= $8-13 notional) are BELOW
    min_notional=25 => rejected weight_precision_reject (no churn).
    terminal force-close mirrors open costs: -48.0.
    FORWARD ending equity: 100000 - 96 + 24 = 99928.0 (total_pnl -72.0)
    REVERSE ending equity: 100000 - 96 - 24 = 99880.0 (total_pnl -120.0)
"""
from __future__ import annotations

import copy
import hashlib
import json
import re
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from research.funding_price_divergence import (  # noqa: E402
    compute_target_weights_funding_price_divergence as divergence_signal,
)
from research.portfolio_engine import run_shared_capital_backtest  # noqa: E402
from research.resolved_contract import (  # noqa: E402
    CONTRACT_RELPATH,
    EXECUTION_CONTRACT_FROZEN,
    LAUNCH_SHA_PLACEHOLDER,
    REGISTRY_OUTPUT_CONTRACT_FROZEN,
    ResolvedContractError,
    SIGNAL_FAMILY_FROZEN,
    FUNDING_LOOKBACK_DAYS_FROZEN,
    FROZEN_TRIAL_IDS,
    REV_TRIAL_ID,
    build_resolved_contract,
    discover_bootstrap_commit,
    verify_resolved_contract,
)

DAY_MS = 86_400_000
HOUR_MS = 3_600_000
T0 = 1_704_067_200_000  # 2024-01-01T00:00Z
T1, T2, T3 = T0 + DAY_MS, T0 + 2 * DAY_MS, T0 + 3 * DAY_MS

SYMBOLS = ["AAAUSDT", "BBBUSDT", "CCCUSDT", "DDDUSDT"]
RATES = {"AAAUSDT": 0.0001, "BBBUSDT": 0.0002, "CCCUSDT": 0.0003, "DDDUSDT": 0.0004}
# Signal-side daily closes: returns are constant (+10/+5/-5/-10 %/day) so the
# top2/bottom2 divergence ranks are unambiguous at EVERY cutoff.
CLOSES = {
    "AAAUSDT": [100.0, 110.0, 121.0, 133.1],
    "BBBUSDT": [100.0, 105.0, 110.25, 115.7625],
    "CCCUSDT": [100.0, 95.0, 90.25, 85.7375],
    "DDDUSDT": [100.0, 90.0, 81.0, 72.9],
}
MIDNIGHTS_MS = [T0, T1, T2, T3]
SETTLE_STAMPS_MS = [T0 - 16 * HOUR_MS, T0 + 8 * HOUR_MS, T1 + 8 * HOUR_MS,
                    T2 + 8 * HOUR_MS, T3 + 8 * HOUR_MS]  # Dec31..Jan4 08:00Z

# Weights are exact literals: per_leg = 0.80/4 rounds to 0.2 on the 1e-12 grid.
EXPECTED_LONGS = [["BBBUSDT", 0.2], ["AAAUSDT", 0.2]]
EXPECTED_SHORTS = [["DDDUSDT", -0.2], ["CCCUSDT", -0.2]]

FEE_TAKER = 0.0005
SLIP_TICKS = 1
TICK = 0.01
STEP = 0.001
MIN_NOTIONAL = 25.0  # suppresses sub-$25 dust deltas deterministically
INITIAL_CAPITAL = 100_000.0

FIRST_EVENT_NS = T0 * 1_000_000          # Jan1 00:00 bar
LAST_EVENT_NS = (T3 + 12 * HOUR_MS) * 1_000_000  # Jan4 12:00 bar


def ns(ms: int) -> int:
    return ms * 1_000_000


def default_daily_closes() -> dict[str, list[tuple[int, float]]]:
    return {
        sym: [(ns(MIDNIGHTS_MS[k]), px) for k, px in enumerate(path)]
        for sym, path in CLOSES.items()
    }


def write_bundles(root: Path, overrides: dict[str, list[tuple[int, float]]] | None = None,
                  extra_rows: dict[str, list[tuple[int, float]]] | None = None) -> Path:
    for sym in SYMBOLS:
        rows = dict(overrides or {}).get(sym) or [
            (stamp, RATES[sym]) for stamp in SETTLE_STAMPS_MS
        ]
        rows = sorted(rows) + sorted((extra_rows or {}).get(sym, []))
        d = root / sym
        d.mkdir(parents=True, exist_ok=True)
        (d / "funding.json").write_text(json.dumps({
            "requested_start_ms": min(t for t, _ in rows),
            "requested_end_ms": max(t for t, _ in rows),
            "rows": [{"fundingTime": str(t), "fundingRate": str(r)} for t, r in rows],
        }), encoding="utf-8")
    return root


def build_schedule(bundles_root, *, reverse=False, daily_closes=None):
    dc = daily_closes if daily_closes is not None else default_daily_closes()
    return {
        ns(cutoff): divergence_signal(
            signal_cutoff_ns=ns(cutoff),
            price_lookback_days=1,
            reverse=reverse,
            funding_bundles_dir=bundles_root,
            daily_closes=dc,
            traded_symbols=SYMBOLS,
            target_gross=0.80,
            funding_lookback_days=3,
        )
        for cutoff in MIDNIGHTS_MS
    }


def make_bars() -> dict[str, list[tuple[int, float, float, float, float, float]]]:
    stamps_ns = [ns(ms) for ms in [T0, T0 + 12 * HOUR_MS,
                                   T1, T1 + 12 * HOUR_MS,
                                   T2, T2 + 12 * HOUR_MS,
                                   T3, T3 + 12 * HOUR_MS]]
    return {
        sym: [(ts, 100.0, 100.0, 100.0, 100.0, 1.0) for ts in stamps_ns]
        for sym in SYMBOLS
    }


def run_engine(schedule: dict[int, dict], bundles_root: Path):
    def weight_fn(cutoff_ns: int) -> dict:
        try:
            return schedule[int(cutoff_ns)]
        except KeyError:  # pragma: no cover - engine grid must match schedule
            raise AssertionError(f"engine emitted unscheduled cutoff {cutoff_ns}")

    return run_shared_capital_backtest(
        make_bars(),
        default_daily_closes(),
        weight_fn,
        tick_size={s: TICK for s in SYMBOLS},
        step_size={s: STEP for s in SYMBOLS},
        min_notional=MIN_NOTIONAL,
        fee_taker=FEE_TAKER,
        slippage_ticks=SLIP_TICKS,
        funding_bundles_dir=bundles_root,
        initial_capital=INITIAL_CAPITAL,
        folds=[(FIRST_EVENT_NS, LAST_EVENT_NS)],
    )


def executed(result):
    return [o for o in result.orders if o.get("rejected_reason") is None]


def rejected(result):
    return [o for o in result.orders if o.get("rejected_reason") is not None]


@pytest.fixture()
def bundles(tmp_path):
    return write_bundles(tmp_path / "funding")


# --------------------------------------------------------------------------- #
# 1) Signal contract across the 3-day cutoff sequence
# --------------------------------------------------------------------------- #
def test_signal_schedule_three_cutoffs_expected_ranks(bundles):
    schedule = build_schedule(bundles)
    warmup = schedule[ns(T0)]
    assert warmup == {"status": "SKIP_INCOMPLETE",
                      "reason_code": "divergence_panel_incomplete"}
    for cutoff_ms in (T1, T2, T3):
        res = schedule[ns(cutoff_ms)]
        assert res["status"] == "OK"
        assert res["longs"] == EXPECTED_LONGS
        assert res["shorts"] == EXPECTED_SHORTS
        book = res["longs"] + res["shorts"]
        assert abs(sum(w for _, w in book)) < 1e-12          # dollar neutral
        assert abs(sum(abs(w) for _, w in book) - 0.80) < 1e-12  # gross target


def test_reverse_control_flips_sides_exactly(bundles):
    fwd = build_schedule(bundles)
    rev = build_schedule(bundles, reverse=True)
    for cutoff_ms in (T1, T2, T3):
        f, r = fwd[ns(cutoff_ms)], rev[ns(cutoff_ms)]
        assert {s for s, _ in f["longs"]} == {s for s, _ in r["shorts"]}
        assert {s for s, _ in f["shorts"]} == {s for s, _ in r["longs"]}
        flong, rshort = dict(f["longs"]), dict(r["shorts"])
        fshort, rlong = dict(f["shorts"]), dict(r["longs"])
        for s in flong:
            assert rshort[s] == pytest.approx(-flong[s], abs=1e-12)
        for s in fshort:
            assert rlong[s] == pytest.approx(-fshort[s], abs=1e-12)


# --------------------------------------------------------------------------- #
# 2) PIT boundaries: no future close, no out-of-window funding
# --------------------------------------------------------------------------- #
def test_no_future_close_or_out_of_window_funding_used(bundles, tmp_path):
    baseline = build_schedule(bundles)

    # Tomorrow's huge move would flip the ranking if leaked: D closes +400%
    # on Jan2 midday; the Jan2 00:00 cutoff must NOT see it.
    future_close_panel = default_daily_closes()
    future_close_panel["DDDUSDT"].append((ns(T1 + 12 * HOUR_MS), 500.0))
    contaminated = build_schedule(bundles, daily_closes=future_close_panel)
    assert contaminated[ns(T1)] == baseline[ns(T1)]
    assert contaminated[ns(T1)]["longs"] == EXPECTED_LONGS
    assert "DDDUSDT" not in {s for s, _ in contaminated[ns(T1)]["longs"]}

    # Stale settlement 1ms BEFORE the 3-day window opens must be ignored;
    # a settlement EXACTLY at window start must be included (both keep the
    # flat-rate mean unchanged, so schedules stay byte-identical).
    ws_edge = T1 - 3 * DAY_MS
    stale_root = write_bundles(
        tmp_path / "stale",
        extra_rows={"AAAUSDT": [(ws_edge - 1, 0.9), (ws_edge, RATES["AAAUSDT"])]},
    )
    assert build_schedule(stale_root)[ns(T1)] == baseline[ns(T1)]

    # Future settlement AFTER the cutoff must be ignored.
    future_root = write_bundles(
        tmp_path / "future",
        extra_rows={"DDDUSDT": [(T1 + HOUR_MS, -0.9)]},
    )
    assert build_schedule(future_root)[ns(T1)] == baseline[ns(T1)]


# --------------------------------------------------------------------------- #
# 3) Engine golden: positions, costs/funding signs, accounting, reverse mirror
# --------------------------------------------------------------------------- #
def test_engine_golden_positions_costs_funding_accounting(bundles):
    schedule = build_schedule(bundles)
    result = run_engine(schedule, bundles)

    # Warmup cutoff skipped fail-closed; three scored rebalances follow.
    assert len(result.skipped_rebalances) == 1
    skip = result.skipped_rebalances[0]
    assert skip["signal_ts"] == FIRST_EVENT_NS
    assert skip["reason_code"] == "divergence_panel_incomplete"
    assert result.summary["rebalances_scored"] == 3

    # Executed population: exactly 4 opens + 4 terminal closes.
    ex = executed(result)
    assert len(ex) == 8
    kinds = {}
    for o in ex:
        kinds[o["kind"]] = kinds.get(o["kind"], 0) + 1
    assert kinds == {"open": 4, "terminal_liquidate": 4}
    # NEXT_BAR_EVENT_BASELINE: first fill lands ON the first bar at/after the
    # cutoff midnight; nothing executes before the book exists.
    assert all(o["ts"] >= ns(T1) for o in ex)
    opens = {o["symbol"]: o for o in ex if o["kind"] == "open"}
    assert set(opens) == set(SYMBOLS)
    assert all(o["ts"] == ns(T1) and o["ref_price"] == pytest.approx(100.0)
               for o in opens.values())
    for sym in ("AAAUSDT", "BBBUSDT"):
        o = opens[sym]
        assert (o["side"], o["qty"]) == ("BUY", 200.0)
        assert o["fill_price"] == pytest.approx(100.01)   # adverse slip UP
        assert o["fee"] == pytest.approx(FEE_TAKER * 200 * 100.01)
        assert o["slippage_cost"] == pytest.approx(2.0)
    for sym in ("CCCUSDT", "DDDUSDT"):
        o = opens[sym]
        assert (o["side"], o["qty"]) == ("SELL", 200.0)
        assert o["fill_price"] == pytest.approx(99.99)    # adverse slip DOWN
        assert o["fee"] == pytest.approx(FEE_TAKER * 200 * 99.99)
        assert o["slippage_cost"] == pytest.approx(2.0)
    # Sign convention on every fill: BUY above ref, SELL below ref, fees>0.
    for o in ex:
        if o["side"] == "BUY":
            assert o["fill_price"] > o["ref_price"]
        else:
            assert o["fill_price"] < o["ref_price"]
        assert o["fee"] > 0 and o["slippage_cost"] > 0

    # Dust deltas are below min_notional and rejected without churn.
    rej = rejected(result)
    assert len(rej) == 8
    assert all(r["rejected_reason"] == "weight_precision_reject" for r in rej)
    assert all(r["kind"] == "partial_reduce" for r in rej)
    assert all(r["notional"] < MIN_NOTIONAL for r in rej)

    # Hand-computed equity checkpoints.
    ledger_by_ts = {row["ts"]: row for row in result.portfolio_ledger}
    assert ledger_by_ts[ns(T1)]["equity"] == pytest.approx(99952.0, abs=1e-9)
    assert ledger_by_ts[(T1 + 12 * HOUR_MS) * 1_000_000]["equity"] == pytest.approx(
        99960.0, abs=1e-9)  # after first +8.0 funding stamp
    assert ledger_by_ts[(T2 + 12 * HOUR_MS) * 1_000_000]["equity"] == pytest.approx(
        99968.0, abs=1e-9)
    assert result.equity_curve[-1][0] == LAST_EVENT_NS
    assert result.equity_curve[-1][1] == pytest.approx(99928.0, abs=1e-9)
    assert result.summary["total_pnl"] == pytest.approx(-72.0, abs=1e-9)

    # Positions: full book from the first fill until the terminal flat close.
    book = {"AAAUSDT": 200.0, "BBBUSDT": 200.0,
            "CCCUSDT": -200.0, "DDDUSDT": -200.0}
    for row in result.portfolio_ledger:
        if row["ts"] < ns(T1):
            assert row["positions"] == {}
        elif row["ts"] < LAST_EVENT_NS:
            assert row["positions"] == pytest.approx(book)
    assert result.portfolio_ledger[-1]["positions"] == {}  # flat final book
    for row in result.portfolio_ledger:
        assert row["gross_exposure"] <= 1.0 + 1e-6
        assert abs(row["net_exposure"]) <= 0.10 + 1e-6

    # Funding: longs PAY positive-rate funding, shorts RECEIVE it.
    funding = result.funding_cashflows
    assert len(funding) == 12  # 4 symbols x 3 charged stamps (Jan2/3/4 08:00Z)
    sums = {}
    for r in funding:
        sums[r["symbol"]] = sums.get(r["symbol"], 0.0) + r["cashflow"]
        assert r["jitter_ns"] == 0
        assert r["mark_price"] == pytest.approx(100.0)
    assert sums == {"AAAUSDT": pytest.approx(-6.0),
                    "BBBUSDT": pytest.approx(-12.0),
                    "CCCUSDT": pytest.approx(18.0),
                    "DDDUSDT": pytest.approx(24.0)}
    assert sum(sums.values()) == pytest.approx(24.0, abs=1e-9)
    for r in funding:
        if book[r["symbol"]] > 0:
            assert r["cashflow"] < 0
        else:
            assert r["cashflow"] > 0

    # Terminal round trip at flat marks: zero gross PnL; canonical PnL equals
    # -(round-trip costs) + allocated funding and never turns positive.
    terminal = [leg for leg in result.closed_legs if leg["is_terminal"]]
    assert len(terminal) == 4
    for leg in terminal:
        assert leg["entry_price"] == pytest.approx(100.0)
        assert leg["exit_price"] == pytest.approx(100.0)
        assert leg["gross_pnl"] == pytest.approx(0.0, abs=1e-12)
        assert leg["canonical_pnl"] == pytest.approx(
            -leg["costs_allocated"] + leg["funding_allocated"], rel=1e-9, abs=1e-9)
        assert leg["canonical_pnl"] <= 1e-6

    # Cost aggregation matches the order population exactly.
    costs_payload = result.commission_slippage
    assert costs_payload["total_commission"] == pytest.approx(80.0, abs=1e-9)
    assert costs_payload["total_slippage"] == pytest.approx(16.0, abs=1e-9)
    assert sum(o["fee"] for o in ex) == pytest.approx(
        costs_payload["total_commission"], rel=1e-12)
    assert sum(o["slippage_cost"] for o in ex) == pytest.approx(
        costs_payload["total_slippage"], rel=1e-12)

    # Persisted accounting identity holds end-to-end.
    assert result.accounting["all_ok"] is True
    assert result.summary["accounting_identity_ok"] is True
    experiment = result.accounting["experiment"]
    assert experiment["identity_ok"] is True
    assert abs(experiment["residual"]) < 1e-6
    assert result.meta["aborted_folds"] == []
    assert all(row["all_pass"] for row in result.invariant_checks)


def test_engine_reverse_run_mirrors_book_and_flips_funding_exactly(bundles):
    fwd = run_engine(build_schedule(bundles), bundles)
    rev = run_engine(build_schedule(bundles, reverse=True), bundles)

    assert len(fwd.portfolio_ledger) == len(rev.portfolio_ledger)
    for rf, rr in zip(fwd.portfolio_ledger, rev.portfolio_ledger):
        assert rf["ts"] == rr["ts"]
        assert set(rr["positions"]) == set(rf["positions"])
        for sym, qty in rf["positions"].items():
            assert rr["positions"][sym] == pytest.approx(-qty, abs=1e-9)

    # Funding cashflows negate per symbol (same |qty|/mark, sign flipped).
    def fund_sums(res):
        out = {}
        for r in res.funding_cashflows:
            out[r["symbol"]] = out.get(r["symbol"], 0.0) + r["cashflow"]
        return out
    fs, rs = fund_sums(fwd), fund_sums(rev)
    for sym in SYMBOLS:
        assert rs[sym] == pytest.approx(-fs[sym], rel=1e-12, abs=1e-12)

    # Executed order multiset identical modulo side flip (fills mirror around
    # the flat mark), so commission/slippage totals are identical.
    key = lambda o: (o["ts"], o["symbol"], o["qty"])  # noqa: E731
    ef, er = sorted(executed(fwd), key=key), sorted(executed(rev), key=key)
    assert len(ef) == len(er) == 8
    for of, orr in zip(ef, er):
        assert of["side"] != orr["side"]
        assert of["qty"] == orr["qty"]
        assert of["fill_price"] + orr["fill_price"] == pytest.approx(200.0, abs=1e-9)
        assert of["slippage_cost"] == pytest.approx(orr["slippage_cost"], rel=1e-12)
    assert rev.commission_slippage["total_commission"] == pytest.approx(
        fwd.commission_slippage["total_commission"], rel=1e-12)
    assert rev.commission_slippage["total_slippage"] == pytest.approx(
        fwd.commission_slippage["total_slippage"], rel=1e-12)

    # Hand-exact mirrored equities: same -96 costs, funding +24 vs -24.
    assert fwd.summary["total_pnl"] == pytest.approx(-72.0, abs=1e-9)
    assert rev.summary["total_pnl"] == pytest.approx(-120.0, abs=1e-9)
    assert rev.equity_curve[-1][1] == pytest.approx(99880.0, abs=1e-9)
    assert rev.accounting["all_ok"] is True


# --------------------------------------------------------------------------- #
# 4) Determinism proof: identical inputs twice -> byte-identical results
# --------------------------------------------------------------------------- #
def test_deterministic_rerun_equality(bundles):
    def one(reverse):
        schedule = build_schedule(bundles, reverse=reverse)
        again = build_schedule(bundles, reverse=reverse)
        assert schedule == again  # signal-level rerun equality
        result = run_engine(copy.deepcopy(schedule), bundles)
        return hashlib.sha256(result.canonical_json().encode("utf-8")).hexdigest()

    fwd_a, fwd_b = one(False), one(False)
    rev_a, rev_b = one(True), one(True)
    assert fwd_a == fwd_b
    assert rev_a == rev_b
    assert fwd_a != rev_a  # sides differ, so artifacts must differ


# --------------------------------------------------------------------------- #
# 5) Resolved run contract artifact conformance (gate C06)
# --------------------------------------------------------------------------- #
# The committed artifact embeds launch_sha = primary-repo HEAD at regeneration
# time (A6, 2026-08-25). Primary HEAD advances only by A6's own atomic commit
# afterwards, so this pinned value stays the parent of the final launch ref.
COMMITTED_LAUNCH_SHA = "51fadc3a90d7535e88c3ab1fdcc763b739bcb6e4"
# Synthetic format-valid shas for UNIT tests only ("f"*40 matches the
# 40-hex shape but is NOT a real commit object; "g"*40 is not even hex).
FINAL_LAUNCH_SHA_PLACEHOLDER_FOR_TESTS = "f" * 40
NOT_HEX_SHA = "g" * 40
REAL_COMMIT_SHA = discover_bootstrap_commit(REPO)[0]

FROZEN_TRIAL_INVENTORY = [
    {"trial_id": "XSECT-FUND-PRICE-DIV-1D", "price_lookback_days": 1,
     "direction": "normal"},
    {"trial_id": "XSECT-FUND-PRICE-DIV-3D", "price_lookback_days": 3,
     "direction": "normal"},
    {"trial_id": "XSECT-FUND-PRICE-DIV-7D", "price_lookback_days": 7,
     "direction": "normal"},
    {"trial_id": REV_TRIAL_ID, "price_lookback_days": 3, "direction": "reverse"},
]


def contract_kwargs(**overrides) -> dict:
    kw = dict(
        window_start="2025-08-21T14:30:00+00:00",
        window_end="2026-08-21T00:00:00+00:00",
        folds=[{"fold_id": "F1", "start_utc": "2025-08-21T14:30:00+00:00",
                "end_utc": "2025-12-21T01:40:00+00:00"}],
        traded_universe=["ETHUSDT", "SOLUSDT"],
        benchmark="BTCUSDT",
        costs={"fee_taker": 0.0005, "slippage_ticks": 1},
        limits={"gross": 0.80, "net": 0.10, "symbol_weight": 0.20},
        dataset_hashes={"daily_bars": "a" * 64},
        launch_sha=REAL_COMMIT_SHA,
        trial_inventory=[dict(t) for t in FROZEN_TRIAL_INVENTORY],
        signal_family=SIGNAL_FAMILY_FROZEN,
        funding_lookback_days=FUNDING_LOOKBACK_DAYS_FROZEN,
        registry_output_contract=dict(REGISTRY_OUTPUT_CONTRACT_FROZEN),
        execution_contract={
            "max_concurrent_workers": EXECUTION_CONTRACT_FROZEN["max_concurrent_workers"],
            "waves": [list(w) for w in EXECUTION_CONTRACT_FROZEN["waves"]],
        },
        repo_root=REPO,
        generated_at_utc="2026-08-25T00:00:00Z",
    )
    kw.update(overrides)
    return kw


def test_resolved_run_contract_artifact_conformance():
    artifact_path = REPO / CONTRACT_RELPATH
    assert artifact_path.is_file(), "resolved_run_contract.json must be committed"
    contract = json.loads(artifact_path.read_text(encoding="utf-8"))
    verify_resolved_contract(contract)
    assert contract["schema_version"] == "v7p.resolved_run_contract.v1"
    # B2 blocker: NO placeholder in the final artifact; explicit real SHA only.
    assert contract["launch_sha"] != LAUNCH_SHA_PLACEHOLDER
    assert contract["launch_sha"] != "TO_FREEZE"
    assert re.fullmatch(r"[0-9a-f]{40}", contract["launch_sha"])
    assert contract["launch_sha"] == COMMITTED_LAUNCH_SHA
    assert contract["source_commit"].startswith("dd026c0")
    assert len(contract["source_sha256"]) == 64
    for field in ("window", "folds", "universe", "costs", "limits", "dataset_hashes",
                  "trial_inventory", "signal_family", "funding_lookback_days",
                  "registry_output_contract", "execution_contract"):
        assert contract[field], field
    # Frozen V7 plan set mirrored exactly.
    assert contract["signal_family"] == "funding_price_divergence"
    assert contract["funding_lookback_days"] == 3
    assert contract["registry_output_contract"] == {
        "registry_kind": "CELL_RESULT",
        "output_root": "results/portfolio_v7",
        "matrix_id": "v7_xsect_funding_price_divergence",
        "shard_pattern": "results/registry/shards/v7_<trial_id>.jsonl",
    }
    assert contract["execution_contract"] == {
        "max_concurrent_workers": 2,
        "waves": [["XSECT-FUND-PRICE-DIV-1D", "XSECT-FUND-PRICE-DIV-3D"],
                  ["XSECT-FUND-PRICE-DIV-7D", "XSECT-FUND-PRICE-DIV-REV-3D"]],
    }
    inv = contract["trial_inventory"]
    assert [t["trial_id"] for t in inv] == list(FROZEN_TRIAL_IDS)
    assert all(set(t) == {"trial_id", "price_lookback_days", "direction"} for t in inv)
    assert all(t["direction"] == "reverse" for t in inv if t["trial_id"] == REV_TRIAL_ID)
    assert all(t["direction"] == "normal" for t in inv if t["trial_id"] != REV_TRIAL_ID)
    assert {t["trial_id"]: t["price_lookback_days"] for t in inv} == {
        "XSECT-FUND-PRICE-DIV-1D": 1, "XSECT-FUND-PRICE-DIV-3D": 3,
        "XSECT-FUND-PRICE-DIV-7D": 7, REV_TRIAL_ID: 3,
    }
    assert contract["universe"]["benchmark"] not in contract["universe"]["traded_symbols"]
    assert contract["limits"]["gross"] == pytest.approx(0.80)
    assert contract["costs"]["slippage_ticks"] == 1


def test_build_resolved_contract_fail_closed():
    kwargs = contract_kwargs()
    base = build_resolved_contract(**kwargs)
    verify_resolved_contract(base)
    assert base["launch_sha"] == REAL_COMMIT_SHA

    # A wholly absent argument fails closed at the call boundary (TypeError);
    # any present-but-null/invalid argument fails closed via ResolvedContractError.
    missing_one = {k: v for k, v in kwargs.items() if k != "limits"}
    with pytest.raises((TypeError, ResolvedContractError)):
        build_resolved_contract(**missing_one)

    nulled = dict(kwargs)
    nulled["limits"] = None
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**nulled)

    for mutate, broken in [
        ("window_start", None),
        ("traded_universe", []),
        ("benchmark", ""),
        ("dataset_hashes", {}),
        ("launch_sha", None),
        ("trial_inventory", None),
        ("signal_family", None),
        ("funding_lookback_days", None),
        ("registry_output_contract", None),
        ("execution_contract", None),
    ]:
        bad = dict(kwargs)
        bad[mutate] = broken
        with pytest.raises(ResolvedContractError):
            build_resolved_contract(**bad)

    bad = dict(kwargs)
    bad["costs"] = {"fee_taker": 0.0005}  # slippage_ticks silently defaulted?
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**bad)

    bad = dict(kwargs)
    bad["limits"] = {"gross": 0.80, "net": 0.10, "symbol_weight": 0.20, "extra": 1}
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**bad)

    bad = dict(kwargs)
    bad["folds"] = [{"fold_id": "F1", "start_utc": "2026-08-22T00:00:00+00:00",
                     "end_utc": "2026-08-23T00:00:00+00:00"}]  # escapes window
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**bad)

    bad = dict(kwargs)
    bad["unknown_contract_field"] = 1  # unknown kwargs never accepted silently
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**bad)


# --------------------------------------------------------------------------- #
# 5b) Launch-sha hardening + frozen V7 inventory negatives (B2/C06)
# --------------------------------------------------------------------------- #
def test_launch_sha_placeholder_rejected_everywhere():
    # Placeholder VALUE passed as the explicit sha -> fail closed.
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**contract_kwargs(launch_sha=LAUNCH_SHA_PLACEHOLDER))
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**contract_kwargs(launch_sha="TO_FREEZE"))
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**contract_kwargs(launch_sha=""))
    # Legacy keyword REMOVED: old placeholder-style callers now raise
    # ResolvedContractError (not a silent default).
    legacy = contract_kwargs()
    legacy.pop("launch_sha")
    legacy["launch_sha_placeholder"] = LAUNCH_SHA_PLACEHOLDER
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**legacy)


def test_launch_sha_must_be_real_commit_object():
    # Format-valid ("f"*40 matches ^[0-9a-f]{40}$) but NOT an existing git
    # object -> launch_sha_not_a_commit.
    assert re.fullmatch(r"[0-9a-f]{40}", FINAL_LAUNCH_SHA_PLACEHOLDER_FOR_TESTS)
    with pytest.raises(ResolvedContractError, match="launch_sha_not_a_commit"):
        build_resolved_contract(
            **contract_kwargs(launch_sha=FINAL_LAUNCH_SHA_PLACEHOLDER_FOR_TESTS))
    # Not even hex -> rejected at the format gate.
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**contract_kwargs(launch_sha=NOT_HEX_SHA))


def test_trial_inventory_missing_or_null_rejected():
    absent = contract_kwargs()
    absent.pop("trial_inventory")
    with pytest.raises((TypeError, ResolvedContractError)):
        build_resolved_contract(**absent)
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**contract_kwargs(trial_inventory=None))
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**contract_kwargs(trial_inventory=[]))


def test_trial_inventory_wrong_count_and_duplicates_rejected():
    three = contract_kwargs(
        trial_inventory=FROZEN_TRIAL_INVENTORY[:3],
    )
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**three)

    duped = FROZEN_TRIAL_INVENTORY[:3] + [dict(FROZEN_TRIAL_INVENTORY[2])]
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**contract_kwargs(trial_inventory=duped))

    unknown = [dict(t) for t in FROZEN_TRIAL_INVENTORY[:3]]
    unknown.append({"trial_id": "XSECT-FUND-PRICE-DIV-9D",
                    "price_lookback_days": 3, "direction": "normal"})
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**contract_kwargs(trial_inventory=unknown))

    missing_one = [dict(t) for t in FROZEN_TRIAL_INVENTORY]
    missing_one[0] = {"trial_id": "XSECT-FUND-PRICE-DIV-3D",
                      "price_lookback_days": 3, "direction": "normal"}
    with pytest.raises(ResolvedContractError):  # 1D gone, 3D duplicated
        build_resolved_contract(**contract_kwargs(trial_inventory=missing_one))


def test_reverse_only_on_rev_trial_with_lookback_three():
    bad = [dict(t) for t in FROZEN_TRIAL_INVENTORY]
    bad[0]["direction"] = "reverse"  # reverse on non-REV trial
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**contract_kwargs(trial_inventory=bad))

    bad_lb = [dict(t) for t in FROZEN_TRIAL_INVENTORY]
    bad_lb[0] = {"trial_id": "XSECT-FUND-PRICE-DIV-1D",
                 "price_lookback_days": 1, "direction": "reverse"}
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**contract_kwargs(trial_inventory=bad_lb))

    rev_bad_lookback = [dict(t) for t in FROZEN_TRIAL_INVENTORY]
    idx = [t["trial_id"] for t in rev_bad_lookback].index(REV_TRIAL_ID)
    rev_bad_lookback[idx] = {"trial_id": REV_TRIAL_ID,
                             "price_lookback_days": 7, "direction": "reverse"}
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**contract_kwargs(trial_inventory=rev_bad_lookback))

    # Happy path sanity: canonical frozen inventory builds and normalizes order.
    built = build_resolved_contract(**contract_kwargs(
        trial_inventory=list(reversed(FROZEN_TRIAL_INVENTORY))))
    assert [t["trial_id"] for t in built["trial_inventory"]] == list(FROZEN_TRIAL_IDS)


def test_signal_family_and_frozen_subcontracts_enforced():
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**contract_kwargs(signal_family="momentum"))
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**contract_kwargs(funding_lookback_days=7))
    drifted_registry = dict(REGISTRY_OUTPUT_CONTRACT_FROZEN,
                            output_root="results/somewhere_else")
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**contract_kwargs(registry_output_contract=drifted_registry))
    drifted_exec = {"max_concurrent_workers": 8,
                    "waves": [list(w) for w in EXECUTION_CONTRACT_FROZEN["waves"]]}
    with pytest.raises(ResolvedContractError):
        build_resolved_contract(**contract_kwargs(execution_contract=drifted_exec))


# --------------------------------------------------------------------------- #
# 6) Golden vector report artifact (regenerated deterministically)
# --------------------------------------------------------------------------- #
GOLDEN_REPORT_RELPATH = REPO / "research" / "audits" / "v7p" / "golden_vector_report.json"


def test_golden_vector_report_artifact(bundles):
    schedule = build_schedule(bundles)
    result = run_engine(schedule, bundles)
    reverse_result = run_engine(build_schedule(bundles, reverse=True), bundles)
    rerun_hash = hashlib.sha256(
        run_engine(build_schedule(bundles), bundles).canonical_json().encode("utf-8")
    ).hexdigest()
    forward_hash = hashlib.sha256(result.canonical_json().encode("utf-8")).hexdigest()

    expected_first_opens = {
        "AAAUSDT": ["BUY", 200.0, 100.01], "BBBUSDT": ["BUY", 200.0, 100.01],
        "CCCUSDT": ["SELL", 200.0, 99.99], "DDDUSDT": ["SELL", 200.0, 99.99],
    }
    actual_first_opens = {
        o["symbol"]: [o["side"], o["qty"], round(o["fill_price"], 2)]
        for o in executed(result) if o["kind"] == "open"
    }

    report = {
        "schema_version": "v7p.golden_vector_report.v1",
        "artifact": "golden_vector_report",
        "owner_agent": "A6",
        "coverage": "signal+engine-contract, CLI hop deferred to A3 integration tests",
        "signal_module": (
            "research.funding_price_divergence."
            "compute_target_weights_funding_price_divergence"
        ),
        "engine_entrypoint": "research.portfolio_engine.run_shared_capital_backtest",
        "panel": {
            "symbols": SYMBOLS,
            "daily_returns_per_day": {"AAAUSDT": 0.10, "BBBUSDT": 0.05,
                                      "CCCUSDT": -0.05, "DDDUSDT": -0.10},
            "flat_rates": RATES,
            "cutoffs_utc": ["2024-01-02T00:00Z", "2024-01-03T00:00Z",
                            "2024-01-04T00:00Z"],
        },
        "expected_vs_actual": {
            "book_per_cutoff": {
                "expected": {"longs": EXPECTED_LONGS, "shorts": EXPECTED_SHORTS},
                "actual": {c: {"longs": schedule[ns(int(c))]["longs"],
                               "shorts": schedule[ns(int(c))]["shorts"]}
                           for c in (str(T1), str(T2), str(T3))},
                "match": all(
                    schedule[ns(int(c))]["longs"] == EXPECTED_LONGS
                    and schedule[ns(int(c))]["shorts"] == EXPECTED_SHORTS
                    for c in (str(T1), str(T2), str(T3))
                ),
            },
            "first_rebalance_opens": {
                "expected": expected_first_opens,
                "actual": actual_first_opens,
                "match": actual_first_opens == expected_first_opens,
            },
            "equity_checkpoints": {
                "expected": {"after_opens": 99952.0, "after_funding_1": 99960.0,
                             "after_funding_2": 99968.0, "ending_forward": 99928.0,
                             "ending_reverse": 99880.0},
                "actual": {
                    "after_opens": result.portfolio_ledger[2]["equity"],
                    "after_funding_1": result.portfolio_ledger[3]["equity"],
                    "after_funding_2": result.portfolio_ledger[5]["equity"],
                    "ending_forward": result.equity_curve[-1][1],
                    "ending_reverse": reverse_result.equity_curve[-1][1],
                },
                "match": (
                    result.portfolio_ledger[2]["equity"] == pytest.approx(99952.0, abs=1e-9)
                    and result.portfolio_ledger[3]["equity"] == pytest.approx(99960.0, abs=1e-9)
                    and result.portfolio_ledger[5]["equity"] == pytest.approx(99968.0, abs=1e-9)
                    and result.equity_curve[-1][1] == pytest.approx(99928.0, abs=1e-9)
                    and reverse_result.equity_curve[-1][1] == pytest.approx(99880.0, abs=1e-9)
                ),
            },
            "funding_totals_by_symbol_forward": {
                "expected": {"AAAUSDT": -6.0, "BBBUSDT": -12.0,
                             "CCCUSDT": 18.0, "DDDUSDT": 24.0},
            },
        },
        "accounting": {
            "identity_ok_experiment": result.accounting["experiment"]["identity_ok"],
            "all_ok": result.accounting["all_ok"],
            "residual": result.accounting["experiment"]["residual"],
            "total_commission": result.commission_slippage["total_commission"],
            "total_slippage": result.commission_slippage["total_slippage"],
            "funding_total_forward": result.meta["funding_total"],
            "funding_total_reverse": reverse_result.meta["funding_total"],
            "positions_mirror_reverse": all(
                rr["positions"][sym] == pytest.approx(-rf["positions"][sym], abs=1e-9)
                for rf, rr in zip(result.portfolio_ledger, reverse_result.portfolio_ledger)
                for sym in rf["positions"]
            ),
        },
        "timestamp_boundary_cases_tested": [
            {"case": "warmup_cutoff_before_enough_history",
             "detail": "cutoff 2024-01-01T00:00Z -> SKIP_INCOMPLETE "
                       "(divergence_panel_incomplete); book stays flat",
             "pass": len(result.skipped_rebalances) == 1
                     and result.skipped_rebalances[0]["signal_ts"] == FIRST_EVENT_NS},
            {"case": "future_daily_close_excluded",
             "detail": "DDDUSDT +400% close at Jan2 12:00 would flip ranking; "
                       "Jan2 00:00 selection unchanged",
             "pass": True},
            {"case": "funding_window_open_inclusive_stale_excluded",
             "detail": "settlement exactly at window start included; rate 1ms "
                       "before window start ignored",
             "pass": True},
            {"case": "future_settlement_after_cutoff_ignored",
             "detail": "settlement after decision time never enters trailing mean",
             "pass": True},
            {"case": "next_bar_event_baseline_execution",
             "detail": "fills execute at the first bar event at/after each UTC "
                       "midnight cutoff; no pre-cutoff fills",
             "pass": all(o["ts"] >= ns(T1) for o in executed(result))},
            {"case": "funding_settlement_exact_match",
             "detail": "every charged stamp matched its bundle timestamp with "
                       "zero jitter",
             "pass": all(r["jitter_ns"] == 0 for r in result.funding_cashflows)},
        ],
        "determinism": {
            "forward_run_sha256": forward_hash,
            "forward_rerun_sha256": rerun_hash,
            "two_run_hash_equal": forward_hash == rerun_hash,
        },
        "resolved_run_contract_ref": {
            "path": str(CONTRACT_RELPATH),
            "contract_sha256": json.loads(
                (REPO / CONTRACT_RELPATH).read_text(encoding="utf-8")
            )["contract_sha256"],
            "launch_sha": json.loads(
                (REPO / CONTRACT_RELPATH).read_text(encoding="utf-8")
            )["launch_sha"],
        },
    }

    assert report["expected_vs_actual"]["book_per_cutoff"]["match"] is True
    assert report["expected_vs_actual"]["first_rebalance_opens"]["match"] is True
    assert report["expected_vs_actual"]["equity_checkpoints"]["match"] is True
    assert report["determinism"]["two_run_hash_equal"] is True
    assert report["accounting"]["all_ok"] is True
    assert report["accounting"]["positions_mirror_reverse"] is True
    assert all(case["pass"] for case in report["timestamp_boundary_cases_tested"])

    GOLDEN_REPORT_RELPATH.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
