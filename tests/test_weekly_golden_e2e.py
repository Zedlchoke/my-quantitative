"""V8P T13 golden end-to-end: weekly reversal through the REAL runner+engine.

Wires the frozen weekly signal (``research.weekly_reversal``) through the
REAL scored CLI path (``research.portfolio_runner.main`` ->
``PORTFOLIO_SIGNAL_FAMILY=weekly_reversal`` dispatch -> embargoed Monday
stamps -> ``research.portfolio_engine.run_shared_capital_backtest``) over a
hand-computable 6-symbol synthetic panel (test_v6p_synthetic_golden
pattern).

Hand-derived golden math (all numbers exact by construction):

Window 2026-01-05T00:00Z .. 2026-02-16T00:00Z, 3 chronological folds of
exactly 14 days (F1 Jan5-19, F2 Jan19-Feb2, F3 Feb2-16). Weekly Monday
stamps with the 7-day fold embargo leave exactly ONE scored cutoff per
fold: Jan12, Jan26, Feb9 (all 00:00 UTC). Warmup floor 14 days puts the
panel start at 2025-12-22.

Panel: one 15m bar per symbol per day at 12:00 UTC (step-function prices,
so each UTC day's close == that bar's price). Daily closes therefore carry
timestamp D 00:00 for day D, and a Monday 00:00 cutoff sees the CURRENT
Monday's close (completed <=) against the close at-or-before
cutoff-minus-lookback.

Prices (base 100 everywhere else):

    AAAUSDT  >= Jan12: 40          BBBUSDT  Jan5: 200, Jan9..11: 105, >=Jan12: 100
    CCCUSDT  flat 100              DDDUSDT  >= Jan12: 101
    EEEUSDT  Jan9..11: 140, >=Jan12: 141
    FFFUSDT  >= Jan9: 250

At the Jan12 cutoff (7D ref = Jan5, 3D ref = Jan9):

    symbol   7D      3D       |  reversal 7D: long  {AAA, BBB}
    AAA      -60%    -60%     |                short {EEE, FFF}
    BBB      -50%    -4.7619% |  reversal 3D: long  {AAA, BBB}
    CCC        0       0      |                short {EEE, DDD}
    DDD      +1%     +1%      |  WMOM ctrl 7D: long {EEE, FFF}
    EEE      +41%    +0.71%   |                short {AAA, BBB}
    FFF      +150%     0      |

At Jan26/Feb9 every post-move price is flat => all formation returns are
exactly 0 => deterministic symbol-ascending ties give
longs {AAA, BBB} / shorts {EEE, FFF} again.

Each fold opens 4 legs at its scored cutoff's 12:00 bar and force-liquidates
at its last observable bar (flat marks => zero gross leg PnL), so executed
orders are exactly 4 opens + 4 terminals per fold x 3 folds = 24, and
equity moves ONLY through costs (-) and funding (+/-). Funding settles at
08:00 UTC daily at a flat +0.0001 for the six traded symbols, so LONG legs
PAY and SHORT legs RECEIVE.
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from research.portfolio_engine import run_shared_capital_backtest  # noqa: E402
from research.portfolio_runner import (  # noqa: E402
    CONTROL_MOMENTUM_ENV,
    SIGNAL_FAMILY_ENV,
    main,
    read_jsonl,
    verify_artifact_hashes,
)

UTC = timezone.utc
GOLDEN_REPORT_RELPATH = REPO / "research" / "audits" / "v8p" / "golden_vector_report_v8.json"

WINDOW_START = "2026-01-05T00:00:00Z"
WINDOW_END = "2026-02-16T00:00:00Z"
LOCK_STAMP = "2026-01-04T00:00:00+00:00"
MATRIX_ID = "v8p_golden_weekly"

TRADED = ["AAAUSDT", "BBBUSDT", "CCCUSDT", "DDDUSDT", "EEEUSDT", "FFFUSDT"]
BENCHMARK = "BTCUSDT"

EXPECTED_7D_LONGS = [["AAAUSDT", 0.2], ["BBBUSDT", 0.2]]
EXPECTED_7D_SHORTS = [["EEEUSDT", -0.2], ["FFFUSDT", -0.2]]
EXPECTED_3D_SHORTS = [["EEEUSDT", -0.2], ["DDDUSDT", -0.2]]
SCORED_CUTOFFS = ("2026-01-12", "2026-01-26", "2026-02-09")
FIRST_OPEN_UTC = "2026-01-12T12:00:00Z"  # first bar event at/after cutoff


def dt(text: str) -> datetime:
    return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(UTC)


def ns(text_or_dt) -> int:
    value = dt(text_or_dt) if isinstance(text_or_dt, str) else text_or_dt
    return int(value.timestamp() * 1_000_000_000)


def _daterange(start: str, end: str):
    cursor = dt(start)
    while cursor <= dt(end):
        yield cursor.strftime("%Y-%m-%d")
        cursor += timedelta(days=1)


def price_for(symbol: str, day: str) -> float:
    if symbol == "AAAUSDT":
        return 40.0 if day >= "2026-01-12" else 100.0
    if symbol == "BBBUSDT":
        if day == "2026-01-05":
            return 200.0
        if "2026-01-09" <= day < "2026-01-12":
            return 105.0
        return 100.0 if day >= "2026-01-12" else 100.0
    if symbol == "DDDUSDT":
        return 101.0 if day >= "2026-01-12" else 100.0
    if symbol == "EEEUSDT":
        if "2026-01-09" <= day < "2026-01-12":
            return 140.0
        return 141.0 if day >= "2026-01-12" else 100.0
    if symbol == "FFFUSDT":
        return 250.0 if day >= "2026-01-09" else 100.0
    return 100.0  # CCCUSDT benchmark-flat


def golden_spec() -> dict:
    bars = []
    for day in _daterange("2025-12-22", "2026-02-15"):
        for sym in [*TRADED, BENCHMARK]:
            px = price_for(sym, day)
            bars.append({
                "symbol": sym, "ts": f"{day}T12:00:00Z",
                "open": px, "high": px, "low": px, "close": px,
                "volume": 1.0,
            })
    funding = [
        {"symbol": sym, "funding_time_ms": f"{day}T08:00:00Z",
         "fundingRate": "0.0001"}
        for day in _daterange("2025-12-23", "2026-02-15") for sym in TRADED
    ]
    # funding_time_ms accepts epoch ms OR ISO via the loader coercion.
    for row in funding:
        row["funding_time_ms"] = int(dt(row.pop("funding_time_ms")).timestamp() * 1000)
    return {
        "traded_symbols": TRADED,
        "benchmark_symbol": BENCHMARK,
        "initial_capital": 100000.0,
        "fee_taker": 0.0005,
        "slippage_ticks": 1,
        "tick_size": {"*": 0.01},
        "step_size": {"*": 0.001},
        "min_notional": 25.0,
        "bars": bars,
        "funding": funding,
    }


CANDIDATE_YAML = (
    "hypothesis_id: H-XSECT-MOM-v1\n"
    "family: cross_sectional_momentum\n"
    "candidate_version: 1\n"
    "owner_agent: A3\n"
    "universe:\n"
    f"  traded_symbols: [{', '.join(TRADED)}]\n"
    f"  benchmark_symbol: {BENCHMARK}\n"
    "signal:\n"
    "  type: weekly_reversal\n"
    "  lookback_days: [3, 7, 14]\n"
)


@pytest.fixture(scope="module")
def golden(tmp_path_factory):
    """ONE deterministic workspace + all scored runs shared by the tests."""
    root = tmp_path_factory.mktemp("v8p_weekly_golden")
    (root / "config").mkdir()
    (root / "config" / "research_baseline_altcoin.yaml").write_text(
        "backtest:\n  fee_model: stub\n", encoding="utf-8")
    hyp = root / "research" / "hypotheses" / "H-XSECT-MOM-v1"
    hyp.mkdir(parents=True)
    (hyp / "candidate.yaml").write_text(
        CANDIDATE_YAML + f'locked_at_utc: "{LOCK_STAMP}"\n', encoding="utf-8")
    contract = root / "results" / "matrix" / "data_contract_v2"
    contract.mkdir(parents=True)
    (contract / "data_contract_v2.json").write_text('{"schema_version": 2}',
                                                    encoding="utf-8")
    spec_path = root / "weekly_panel_spec.json"
    spec_path.write_text(json.dumps(golden_spec()), encoding="utf-8")

    env_keys = (SIGNAL_FAMILY_ENV, CONTROL_MOMENTUM_ENV)
    saved_env = {key: os.environ.get(key) for key in env_keys}
    prev_cwd = os.getcwd()
    os.chdir(root)

    def run_main(experiment_id: str, *, lookback: int,
                 control: bool = False) -> Path:
        for key in env_keys:
            os.environ.pop(key, None)
        argv = [
            "--experiment-id", experiment_id,
            "--lookback-days", str(lookback),
            "--window-start", WINDOW_START,
            "--window-end", WINDOW_END,
            "--folds", "3",
            "--matrix-id", MATRIX_ID,
            "--registry-path", "results/registry/experiments.jsonl",
            "--synthetic-panel", str(spec_path),
            "--signal-family", "weekly_reversal",
        ]
        if control:
            argv.append("--control-momentum")
        code = main(argv)
        assert code == 0, experiment_id
        for key in env_keys:
            os.environ.pop(key, None)
        return root / "results" / "portfolio_v4" / experiment_id

    try:
        exp7 = run_main("V8-WREV-7D-GOLDEN", lookback=7)
        exp7_rerun = run_main("V8-WREV-7D-GOLDEN-RERUN", lookback=7)
        exp3 = run_main("V8-WREV-3D-GOLDEN", lookback=3)
        expc = run_main("V8-WREV-CONTROL-GOLDEN", lookback=7, control=True)

        code = main([
            "--reproduce", str(exp7),
            "--verify-id", "V8P-T13-WEEKLY-REPRO",
            "--registry-path", "results/registry/experiments.jsonl",
            "--reproduction-root", "results/reproduction_v4",
            # run_main() scrubs the family env after each scored run, so the
            # reproduce launcher must re-select it explicitly; the flag sets
            # PORTFOLIO_SIGNAL_FAMILY and the worker subprocess inherits it.
            "--signal-family", "weekly_reversal",
        ])
        assert code == 0
        comparison = json.loads(
            (root / "results" / "reproduction_v4" / "V8P-T13-WEEKLY-REPRO" /
             "comparison.json").read_text(encoding="utf-8"))
        yield {
            "root": root,
            "spec_path": spec_path,
            "exp7": exp7,
            "exp7_rerun": exp7_rerun,
            "exp3": exp3,
            "expc": expc,
            "comparison": comparison,
        }
    finally:
        os.chdir(prev_cwd)
        for key in env_keys:
            if saved_env.get(key) is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = saved_env[key]


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _executed(rows: list[dict]) -> list[dict]:
    return [row for row in rows if row.get("rejected_reason") is None]


# --------------------------------------------------------------------------- #
# Weekly cadence + golden picks + hashes (PLAN 5.2 items 1/4/6/8/9)
# --------------------------------------------------------------------------- #
def test_weekly_golden_schedule_picks_and_hashes(golden):
    exp = golden["exp7"]
    assert verify_artifact_hashes(exp) == []

    ranks = read_jsonl(exp / "signal_ranks.jsonl")
    assert len(ranks) == 3  # ONE embargoed Monday stamp per fold
    assert [row["rebalance_ts_utc"][:10] for row in ranks] == list(SCORED_CUTOFFS)
    first = ranks[0]
    assert first["status"] == "OK"
    assert first["longs"] == EXPECTED_7D_LONGS
    assert first["shorts"] == EXPECTED_7D_SHORTS
    for row in ranks[1:]:
        # Post-move flatness -> all-zero returns -> deterministic symbol ties.
        assert row["status"] == "OK"
        assert row["longs"] == EXPECTED_7D_LONGS
        assert row["shorts"] == EXPECTED_7D_SHORTS

    diagnostics = read_jsonl(exp / "signal_diagnostics.jsonl")
    assert len(diagnostics) == 3
    head = diagnostics[0]
    assert head["derived_diagnostics"] is True
    assert head["skipped_reason"] is None
    assert head["formation_lookback_days"] == 7
    assert head["per_symbol"]["AAAUSDT"]["formation_return"] == \
        pytest.approx(-0.60, abs=1e-12)
    assert head["per_symbol"]["FFFUSDT"]["formation_return"] == \
        pytest.approx(1.50, abs=1e-12)
    assert {sym: leg["rank"] for sym, leg in head["per_symbol"].items()} == {
        "AAAUSDT": 1, "BBBUSDT": 2, "CCCUSDT": 3,
        "DDDUSDT": 4, "EEEUSDT": 5, "FFFUSDT": 6,
    }

    metrics = _json(exp / "canonical_metrics.json")
    assert metrics["rebalances_scored"] == 3
    assert metrics["legs_closed"] == 12  # 4 legs per fold x 3 folds
    assert metrics["max_abs_target_weight"] == pytest.approx(0.20)
    assert metrics["risk_mode_requested"] == "RISK_MODE_V1"
    assert metrics["risk_mode_active"] is True
    assert metrics["fold_carry_ok"] is True
    assert sorted(metrics["fold_pnls"]) == ["F1", "F2", "F3"]

    manifest = yaml.safe_load((exp / "launch_manifest.yaml").read_text("utf-8"))
    # exact_backtest_argv captures the OUTER process argv under in-process
    # pytest, so family resolution is evidenced by the manifest's lookback/
    # warmup fields plus the family-gated diagnostics artifact below.
    assert int(manifest["lookback_days"]) == 7
    assert int(manifest["warmup_bars"]) >= 14 * 96  # PLAN 5.1 warmup >= 14d
    registry = read_jsonl(golden["root"] / "results" / "registry" /
                          "experiments.jsonl")
    entry = next(row for row in registry
                 if row.get("experiment_id") == "V8-WREV-7D-GOLDEN"
                 and row.get("kind") == "CELL_RESULT")
    assert entry["status"] == "COMPLETED"
    assert entry["inprocess_integrity"]["manifest_verify_reasons"] == []


def test_weekly_golden_orders_ledger_costs_identity(golden):
    exp = golden["exp7"]
    orders = _executed(read_jsonl(exp / "orders.jsonl"))
    assert len(orders) == 24
    kinds = {}
    for order in orders:
        kinds[order["kind"]] = kinds.get(order["kind"], 0) + 1
    assert kinds == {"open": 12, "terminal_liquidate": 12}

    # Signal cutoff and execution event are SEPARATE: fills land on the
    # first completed bar EVENT at/after the Monday 00:00 cutoff (12:00),
    # never before the cutoff instant.
    cutoff_ns = ns(SCORED_CUTOFFS[0])
    first_opens = [o for o in orders
                   if o["kind"] == "open" and o["ts"] == ns(FIRST_OPEN_UTC)]
    assert len(first_opens) == 4
    assert all(o["ts"] >= cutoff_ns for o in orders)
    by_sym = {o["symbol"]: o for o in first_opens}
    assert {by_sym[s]["side"] for s in ("AAAUSDT", "BBBUSDT")} == {"BUY"}
    assert {by_sym[s]["side"] for s in ("EEEUSDT", "FFFUSDT")} == {"SELL"}

    ledger = read_jsonl(exp / "portfolio_ledger.jsonl")
    assert ledger
    assert ledger[-1]["positions"] == {}  # flat final book
    assert all(row["cash_identity_ok"] for row in ledger)
    assert all(float(row["gross_exposure"]) <= 1.0 + 1e-6 for row in ledger)

    funding = read_jsonl(exp / "funding_cashflows.jsonl")
    assert funding and all(row["jitter_ns"] == 0 for row in funding)
    sums = {}
    for row in funding:
        sums[row["symbol"]] = sums.get(row["symbol"], 0.0) + row["cashflow"]
    assert sums["AAAUSDT"] < 0 and sums["BBBUSDT"] < 0  # longs pay
    assert sums["EEEUSDT"] > 0 and sums["FFFUSDT"] > 0  # shorts receive

    recon = _json(exp / "accounting_reconciliation.json")
    assert recon["experiment_identity"]["identity_ok"] is True
    assert recon["engine_accounting"]["all_ok"] is True
    assert recon["funding_reconciliation"]["all_ok"] is True
    assert recon["terminal_reconciliation"]["counts_ok"] is True
    assert recon["terminal_reconciliation"]["flat_final_book"] is True
    costs = _json(exp / "commission_slippage.json")
    assert costs["total_commission"] > 0 and costs["total_slippage"] > 0
    stress = _json(exp / "stress_report.json")
    assert stress["baseline"]["canonical_pnl"] == \
        pytest.approx(metrics_total_pnl(exp), abs=1e-9)
    assert stress["variants"]["fee_x1_5"]["executed"] is True


def metrics_total_pnl(exp: Path) -> float:
    return float(_json(exp / "canonical_metrics.json")["total_pnl"])


# --------------------------------------------------------------------------- #
# Lookback routing + WMOM control flip (PLAN 5.2 items 4/9)
# --------------------------------------------------------------------------- #
def test_three_day_formation_changes_golden_shorts(golden):
    exp = golden["exp3"]
    assert verify_artifact_hashes(exp) == []
    ranks = read_jsonl(exp / "signal_ranks.jsonl")
    assert ranks[0]["longs"] == EXPECTED_7D_LONGS
    assert ranks[0]["shorts"] == EXPECTED_3D_SHORTS
    assert _executed(read_jsonl(exp / "orders.jsonl"))


def test_control_run_flips_sides_vs_same_lookback_reversal(golden):
    rev_ranks = read_jsonl(golden["exp7"] / "signal_ranks.jsonl")[0]
    ctl_ranks = read_jsonl(golden["expc"] / "signal_ranks.jsonl")[0]
    assert ctl_ranks["longs"] == [["EEEUSDT", 0.2], ["FFFUSDT", 0.2]]
    assert ctl_ranks["shorts"] == [["AAAUSDT", -0.2], ["BBBUSDT", -0.2]]
    assert {s for s, _ in ctl_ranks["longs"]} == \
        {s for s, _ in rev_ranks["shorts"]}
    assert {s for s, _ in ctl_ranks["shorts"]} == \
        {s for s, _ in rev_ranks["longs"]}
    assert len(_executed(read_jsonl(golden["expc"] / "orders.jsonl"))) == 24

    gate = _json(golden["expc"] / "gate_result.json")
    assert gate["cell_verdict"] == "CONTROL_ONLY"
    assert gate["is_negative_control"] is True

    def fund_sums(exp: Path) -> dict:
        sums = {}
        for row in read_jsonl(exp / "funding_cashflows.jsonl"):
            sums[row["symbol"]] = sums.get(row["symbol"], 0.0) + row["cashflow"]
        return sums

    fwd, ctl = fund_sums(golden["exp7"]), fund_sums(golden["expc"])
    for sym in ("AAAUSDT", "BBBUSDT"):
        assert fwd[sym] < 0 and ctl[sym] > 0  # roles swapped end-to-end
    for sym in ("EEEUSDT", "FFFUSDT"):
        assert fwd[sym] > 0 and ctl[sym] < 0


# --------------------------------------------------------------------------- #
# Two-run determinism + reproduction harness (PLAN 5.2 items 8/10)
# --------------------------------------------------------------------------- #
def test_two_identical_runs_produce_equal_canonical_digests(golden):
    a = _json(golden["exp7"] / "canonical_metrics.json")
    b = _json(golden["exp7_rerun"] / "canonical_metrics.json")
    assert a.pop("experiment_id") != b.pop("experiment_id")
    assert a == b
    assert a["orders_digest"] == b["orders_digest"]
    assert a["positions_digest"] == b["positions_digest"]
    for name in ("portfolio_ledger.jsonl", "orders.jsonl",
                 "positions.jsonl", "signal_ranks.jsonl"):
        da = hashlib.sha256((golden["exp7"] / name).read_bytes()).hexdigest()
        db = hashlib.sha256(
            (golden["exp7_rerun"] / name).read_bytes()).hexdigest()
        assert da == db, name


def test_reproduction_harness_full_surface_match(golden):
    comparison = golden["comparison"]
    assert comparison["rerun_process_separate"] is True
    assert comparison["all_match"] is True
    checks = comparison["checks"]
    for key in ("orders_digest_match", "positions_digest_match", "pnl_match",
                "signals_match", "ledger_match", "positions_match",
                "canonical_metrics_match", "artifact_hashes_match",
                "gate_result_verdicts_match", "scorecard_totals_match"):
        assert checks[key] is True, key


# --------------------------------------------------------------------------- #
# Delay stress shifts execution exactly ONE event (PLAN 5.2 item 5)
# --------------------------------------------------------------------------- #
def test_signal_cutoff_and_execution_event_separation_delay_stress():
    symbols = ["AAAUSDT", "BBBUSDT"]
    stamps = [ns(f"2026-01-{day:02d}T12:00:00Z") for day in range(10, 17)]
    bars = {
        sym: [(ts, 100.0, 100.0, 100.0, 100.0, 1.0) for ts in stamps]
        for sym in symbols
    }
    schedule = {
        ns("2026-01-12T00:00:00Z"): {
            "status": "OK",
            "longs": [["AAAUSDT", 0.25]],
            "shorts": [["BBBUSDT", -0.25]],
        },
    }

    def weight_fn(cutoff_ns: int) -> dict:
        entry = schedule.get(int(cutoff_ns))
        if entry is None:
            return {"status": "SKIP_INCOMPLETE",
                    "reason_code": "incomplete_cross_section_skip"}
        return entry

    def run(extra_delay_events: int):
        result = run_shared_capital_backtest(
            {s: list(b) for s, b in bars.items()},
            {s: [(ts, 100.0) for ts in stamps] for s in symbols},
            weight_fn,
            tick_size={s: 0.01 for s in symbols},
            step_size={s: 0.001 for s in symbols},
            min_notional=5.0,
            fee_taker=0.0005,
            slippage_ticks=1,
            funding_bundles_dir=None,
            initial_capital=100000.0,
            folds=[(ns("2026-01-10T00:00:00Z"), ns("2026-01-17T00:00:00Z"))],
            extra_delay_events=extra_delay_events,
        )
        return [o for o in result.orders if o.get("rejected_reason") is None]

    cutoff_ns = ns("2026-01-12T00:00:00Z")
    immediate = [o for o in run(0) if o["kind"] == "open"]
    delayed = [o for o in run(1) if o["kind"] == "open"]
    assert {o["ts"] for o in immediate} == {ns(FIRST_OPEN_UTC)}
    assert {o["ts"] for o in delayed} == {ns("2026-01-13T12:00:00Z")}
    assert all(o["ts"] >= cutoff_ns for o in (*immediate, *delayed))
    # Exactly ONE bar-event shift, nothing more.
    event_index = stamps.index(ns(FIRST_OPEN_UTC))
    assert stamps[event_index + 1] == ns("2026-01-13T12:00:00Z")


# --------------------------------------------------------------------------- #
# Golden vector report artifact (regenerated deterministically, committed)
# --------------------------------------------------------------------------- #
def test_golden_vector_report_v8_artifact(golden):
    exp7 = golden["exp7"]
    ranks = read_jsonl(exp7 / "signal_ranks.jsonl")
    ctl_ranks = read_jsonl(golden["expc"] / "signal_ranks.jsonl")
    metrics = _json(exp7 / "canonical_metrics.json")
    recon = _json(exp7 / "accounting_reconciliation.json")

    def picks(exp: Path) -> dict:
        row = read_jsonl(exp / "signal_ranks.jsonl")[0]
        return {
            "longs": [s for s, _ in row["longs"]],
            "shorts": [s for s, _ in row["shorts"]],
        }

    p7, p3 = picks(exp7), picks(golden["exp3"])
    pc = picks(golden["expc"])
    report = {
        "schema_version": "v8p.golden_vector_report.v1",
        "artifact": "golden_vector_report_v8",
        "owner_agent": "A3",
        "gate": "T13",
        "signal_module": (
            "research.weekly_reversal."
            "compute_target_weights_weekly_reversal"),
        "engine_entrypoint":
            "research.portfolio_engine.run_shared_capital_backtest",
        "runner_entrypoint": "research.portfolio_runner.main",
        "frozen_behavior": {
            "signal_clock_utc": "Monday 00:00",
            "formation_lookbacks_days_tested": [3, 7],
            "reversal_rule": "long bottom-2 losers / short top-2 winners",
            "control_rule": "WMOM at 7D: long winners / short losers",
            "hold_days": 7,
            "target_gross": 0.80,
            "per_leg_weight": 0.20,
            "all_six_eligibility": True,
            "skip_reason": "weekly_panel_incomplete",
            "fold_embargo_days": 7,
            "min_warmup_days": 14,
        },
        "panel": {
            "traded_symbols": TRADED,
            "benchmark_symbol": BENCHMARK,
            "window": [WINDOW_START, WINDOW_END],
            "folds": 3,
            "scored_cutoffs_utc": [f"{day}T00:00:00Z" for day in SCORED_CUTOFFS],
            "formation_returns_at_first_cutoff_7d": {
                row_sym: leg["formation_return"]
                for row_sym, leg in
                read_jsonl(exp7 / "signal_diagnostics.jsonl")[0]
                ["per_symbol"].items()
            },
        },
        "expected_vs_actual": {
            "reversal_7d": {
                "expected": {"longs": ["AAAUSDT", "BBBUSDT"],
                             "shorts": ["EEEUSDT", "FFFUSDT"]},
                "actual": p7,
                "match": p7 == {"longs": ["AAAUSDT", "BBBUSDT"],
                                "shorts": ["EEEUSDT", "FFFUSDT"]},
            },
            "reversal_3d": {
                "expected": {"longs": ["AAAUSDT", "BBBUSDT"],
                             "shorts": ["EEEUSDT", "DDDUSDT"]},
                "actual": p3,
                "match": p3 == {"longs": ["AAAUSDT", "BBBUSDT"],
                                "shorts": ["EEEUSDT", "DDDUSDT"]},
            },
            "wmom_control_7d": {
                "expected": {"longs": ["EEEUSDT", "FFFUSDT"],
                             "shorts": ["AAAUSDT", "BBBUSDT"]},
                "actual": pc,
                "match": pc == {"longs": ["EEEUSDT", "FFFUSDT"],
                                "shorts": ["AAAUSDT", "BBBUSDT"]},
            },
            "weights_per_leg": {
                "expected": 0.20,
                "actual": metrics["max_abs_target_weight"],
                "match": metrics["max_abs_target_weight"] ==
                    pytest.approx(0.20, abs=1e-12),
            },
            "executed_orders": {
                "expected": 24,
                "actual": len(_executed(read_jsonl(
                    exp7 / "orders.jsonl"))),
                "match": len(_executed(read_jsonl(
                    exp7 / "orders.jsonl"))) == 24,
            },
            "first_open_event_utc": {
                "expected": FIRST_OPEN_UTC,
                "match": True,
            },
        },
        "accounting": {
            "identity_ok": recon["experiment_identity"]["identity_ok"],
            "engine_all_ok": recon["engine_accounting"]["all_ok"],
            "funding_sign_split_forward": {
                "longs_pay": ["AAAUSDT", "BBBUSDT"],
                "shorts_receive": ["EEEUSDT", "FFFUSDT"],
            },
            "ledger_nonempty": bool(read_jsonl(
                exp7 / "portfolio_ledger.jsonl")),
        },
        "determinism": {
            "two_run_canonical_digests_equal":
                metrics["orders_digest"] == _json(
                    golden["exp7_rerun"] / "canonical_metrics.json"
                )["orders_digest"],
            "orders_digest": metrics["orders_digest"],
            "positions_digest": metrics["positions_digest"],
        },
        "cli_resolution": {
            "signal_family_flag": "weekly_reversal",
            "artifact_hashes_verify_clean": {
                str(exp): verify_artifact_hashes(Path(exp)) == []
                for exp in (str(exp7), str(golden["exp3"]),
                            str(golden["expc"]))
            },
            "registry_cell_result_recorded": True,
            "warmup_bars_ge_14_days": int(yaml.safe_load(
                (Path(exp7) / "launch_manifest.yaml").read_text("utf-8"))
                ["warmup_bars"]) >= 14 * 96,
        },
        "reproduction": {
            "verify_id": "V8P-T13-WEEKLY-REPRO",
            "all_match": golden["comparison"]["all_match"],
        },
    }
    assert report["expected_vs_actual"]["reversal_7d"]["match"] is True
    assert report["expected_vs_actual"]["reversal_3d"]["match"] is True
    assert report["expected_vs_actual"]["wmom_control_7d"]["match"] is True
    assert report["expected_vs_actual"]["weights_per_leg"]["match"] is True
    assert report["expected_vs_actual"]["executed_orders"]["match"] is True
    assert report["accounting"]["identity_ok"] is True
    assert report["accounting"]["engine_all_ok"] is True
    assert report["accounting"]["ledger_nonempty"] is True
    assert report["determinism"]["two_run_canonical_digests_equal"] is True
    assert all(report["cli_resolution"]["artifact_hashes_verify_clean"].values())
    assert report["cli_resolution"]["warmup_bars_ge_14_days"] is True
    assert report["reproduction"]["all_match"] is True

    GOLDEN_REPORT_RELPATH.parent.mkdir(parents=True, exist_ok=True)
    GOLDEN_REPORT_RELPATH.write_text(
        json.dumps(report, indent=2, sort_keys=True, default=str) + "\n",
        encoding="utf-8")
