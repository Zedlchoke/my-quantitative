"""V6P accounting/risk/one-pass WFA fixtures (PLAN section 6.3, owner A4).

Unit-level coverage for the runner's one-pass orchestration helpers and the
accounting_reconciliation payload, plus an integration run through the real
engine + synthetic panel that forces RISK_MODE_V1 reduce-only trims and
proves post-trim exposure caps hold on every completed bar.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from research.portfolio_runner import (
    _segment_equities,
    _supported_kwargs,
    build_v6p_accounting_payload,
    execute_experiment,
)

DAY_NS = 86_400_000_000_000
BASE_NS = int(datetime(2026, 1, 1, tzinfo=timezone.utc).timestamp() * 1e9)
WINDOW_START = datetime(2026, 1, 1, tzinfo=timezone.utc)
WINDOW_END = datetime(2026, 1, 4, tzinfo=timezone.utc)
LOCK_STAMP = "2026-01-05T00:00:00+00:00"

CANDIDATE_YAML = (
    "hypothesis_id: H-XSECT-MOM-v1\n"
    "family: cross_sectional_momentum\n"
    "candidate_version: 1\n"
    "owner_agent: A4\n"
    "universe:\n"
    "  traded_symbols: [SYMAUSDT, SYMBUSDT]\n"
    "  benchmark_symbol: BTCUSDT\n"
    "signal:\n"
    "  type: cumulative_log_return_rank\n"
    "  lookback_days: [3]\n"
)


# --------------------------------------------------------------------------- #
# pure helper units
# --------------------------------------------------------------------------- #
def test_supported_kwargs_drops_unsupported_and_keeps_var_keyword():
    def modern(a, b=0, *, folds=None, risk_mode=None):
        raise AssertionError("not called")

    def legacy(a, b=0):
        raise AssertionError("not called")

    def catch_all(**kwargs):
        raise AssertionError("not called")

    kwargs = {"a": 1, "b": 2, "folds": [(0, 1)], "risk_mode": "RISK_MODE_V1"}
    assert set(_supported_kwargs(modern, kwargs)) == {
        "a", "b", "folds", "risk_mode"}
    assert _supported_kwargs(legacy, kwargs) == {"a": 1, "b": 2}
    assert _supported_kwargs(catch_all, kwargs) == kwargs


def test_segment_equities_carry_chain_and_pre_sample_anchor():
    curve = [
        (BASE_NS + DAY_NS, 101000.0),   # F1 end sample
        (BASE_NS + 2 * DAY_NS, 99000.0),
        (BASE_NS + 5 * DAY_NS // 2, 99500.0),
        (BASE_NS + 3 * DAY_NS, 100500.0),
    ]
    edges = [
        (BASE_NS, BASE_NS + 2 * DAY_NS),          # F1
        (BASE_NS + 2 * DAY_NS, BASE_NS + 4 * DAY_NS),  # F2
        (BASE_NS + 4 * DAY_NS, BASE_NS + 6 * DAY_NS),  # F3
    ]
    segments = _segment_equities(curve, edges)
    assert segments[0]["start_equity"] == 101000.0  # first sample fallback
    assert segments[0]["end_equity"] == pytest.approx(99000.0)
    assert segments[1]["start_equity"] == pytest.approx(
        segments[0]["end_equity"])  # exact carry by construction
    assert segments[1]["end_equity"] == pytest.approx(100500.0)
    assert segments[2]["start_equity"] == pytest.approx(100500.0)
    assert segments[2]["end_equity"] == pytest.approx(100500.0)


# --------------------------------------------------------------------------- #
# one-pass WFA orchestration (N04) with counting fake engines
# --------------------------------------------------------------------------- #
def _fake_engine(runner_fn, *, meta=None, summary=None, extra_result=None):
    calls = {"n": 0, "kwargs": None}

    def build_daily_panel(symbols, window_start_ns, window_end_ns):
        stamps = list(range(window_start_ns, window_end_ns + 1, DAY_NS))
        return {"daily_closes": {"BTCUSDT": [(t, 100.0) for t in stamps]},
                "coverage": {"days_per_symbol": {"BTCUSDT": len(stamps)},
                             "btc_days": len(stamps)},
                "benchmark_clean": True,
                "benchmark_daily_closes": []}

    def compute_target_weights(daily_closes, signal_cutoff_ns,
                               lookback_days, reverse=False):
        return {"status": "OK",
                "longs": [["SYMAUSDT", 0.25]],
                "shorts": [["SYMBUSDT", -0.25]]}

    def run_shared_capital_backtest(**kwargs):
        calls["n"] += 1
        calls["kwargs"] = kwargs
        return runner_fn(kwargs)

    engine = {
        "build_daily_panel": build_daily_panel,
        "run_shared_capital_backtest": run_shared_capital_backtest,
        "compute_target_weights": compute_target_weights,
        "_calls": calls,
    }
    return engine


def test_execute_experiment_single_engine_call_with_folds_and_risk_mode():
    def runner(kwargs):
        # One continuous curve crossing all three daily folds; samples never
        # sit on internal fold boundaries. Ledger rows carry ts.
        half = DAY_NS // 2
        curve = [
            (BASE_NS, 100000.0),
            (BASE_NS + half, 101000.0),              # F1 end
            (BASE_NS + DAY_NS + half, 99000.0),      # F2 end
            (BASE_NS + 2 * DAY_NS + half, 100500.0),  # F3 end
        ]
        ledger = [{"ts": t, "gross_exposure": 0.5, "net_exposure": 0.0}
                  for t, _ in curve]
        legs = [{"ts": BASE_NS + DAY_NS // 2, "symbol": "SYMAUSDT",
                 "canonical_pnl": 500.0,
                 "gross_pnl": 600.0, "funding_allocated": -25.0}]
        return {
            "portfolio_ledger": ledger,
            "orders": [{"ts": BASE_NS + DAY_NS // 2, "fee": 1.0,
                        "slippage_cost": 0.5, "rejected_reason": None}],
            "closed_legs": legs,
            "equity_curve": curve,
            "skipped_rebalances": [],
            "invariants": [],
            "summary": {"rebalances_scored": 3},
            "meta": {**(meta := {"initial_capital": 100000.0,
                                 "risk_mode": "RISK_MODE_V1"})},
            "funding_cashflows": [{"ts": BASE_NS, "symbol": "SYMAUSDT",
                                   "cashflow": -25.0}],
            "terminal_positions": [],
            "exposure_control": [],
            "accounting": {},
            "commission_slippage": {},
        }

    engine = _fake_engine(runner)
    execution = execute_experiment(
        engine=engine, traded_symbols=["SYMAUSDT"],
        benchmark_symbol="BTCUSDT",
        window_start=WINDOW_START, window_end=WINDOW_END,
        lookback_days=3, reverse=False, folds=3,
    )
    calls = engine["_calls"]
    assert calls["n"] == 1, "one-pass WFA must call the engine exactly once"
    assert len(calls["kwargs"]["folds"]) == 3
    assert calls["kwargs"]["risk_mode"] == "RISK_MODE_V1"

    metrics = execution["metrics"]
    assert metrics["fold_pnls"] == {
        "F1": pytest.approx(1000.0),
        "F2": pytest.approx(-2000.0),
        "F3": pytest.approx(1500.0),
    }
    assert metrics["fold_returns"]["F1"] == pytest.approx(0.01)
    assert metrics["fold_returns"]["F2"] == pytest.approx(99000.0 / 101000.0 - 1)
    assert metrics["fold_returns"]["F3"] == pytest.approx(100500.0 / 99000.0 - 1)
    assert metrics["fold_carry_ok"] is True
    assert metrics["total_pnl"] == pytest.approx(500.0)
    assert metrics["starting_equity"] == pytest.approx(100000.0)
    assert metrics["ending_equity"] == pytest.approx(100500.0)
    # Continuous MDD: peak 101000 -> trough 99000.
    assert metrics["max_drawdown_fraction"] == pytest.approx(
        2000.0 / 101000.0, rel=1e-9)
    assert metrics["risk_mode_active"] is True
    assert metrics["one_pass"]["single_engine_call"] is True


def test_execute_experiment_legacy_engine_degrades_honestly():
    def runner(kwargs):
        assert "folds" not in kwargs, "legacy engine must not receive folds"
        assert "risk_mode" not in kwargs
        curve = [(BASE_NS, 100000.0), (BASE_NS + 3 * DAY_NS, 100250.0)]
        return {
            "portfolio_ledger": [{"rebalance_ts_ns": BASE_NS}],
            "orders": [{"symbol": "SYMAUSDT"}],  # no fee/ts fields
            "closed_legs": [],
            "equity_curve": curve,
            "skipped_rebalances": [],
            "invariants": [],
            "summary": {},
            "meta": {},
            "funding_cashflows": [],
            "terminal_positions": [],
            "exposure_control": [],
            "accounting": {},
            "commission_slippage": {},
        }

    class LegacyEngine(dict):
        pass

    engine = _fake_engine(runner)
    # Strip the V6P kwargs from the callable signature (legacy engine).
    def run_legacy(*, daily_closes, target_schedule, window_start_ns,
                   window_end_ns, fee_multiplier=1.0, adverse_ticks=0,
                   extra_delay_events=0):
        return runner({"daily_closes": daily_closes})

    engine["run_shared_capital_backtest"] = run_legacy

    execution = execute_experiment(
        engine=engine, traded_symbols=["SYMAUSDT"],
        benchmark_symbol="BTCUSDT",
        window_start=WINDOW_START, window_end=WINDOW_END,
        lookback_days=3, reverse=False, folds=3,
    )
    metrics = execution["metrics"]
    assert metrics["one_pass"]["single_engine_call"] is True
    assert metrics["one_pass"]["folds_kwarg_supported"] is False
    assert metrics["one_pass"]["risk_mode_kwarg_supported"] is False
    assert metrics["risk_mode_active"] is False


# --------------------------------------------------------------------------- #
# accounting reconciliation payload (N06)
# --------------------------------------------------------------------------- #
def _base_execution():
    return {
        "metrics": {
            "starting_equity": 100000.0,
            "ending_equity": 100010.0,
            "fold_carry_max_gap": 0.0,
            "fold_carry_ok": True,
            "risk_mode_requested": "RISK_MODE_V1",
            "risk_mode_active": True,
            "exposure_control_rows": 1,
        },
        "orders": [
            {"ts": 1, "fee": 3.0, "slippage_cost": 1.0,
             "rejected_reason": None},
            {"ts": 2, "fee": 0.0, "slippage_cost": 0.0,
             "rejected_reason": "margin_breach"},
        ],
        "closed_legs": [
            {"symbol": "SYMAUSDT", "gross_pnl": 20.0, "canonical_pnl": 16.0,
             "funding_allocated": -4.0, "is_terminal": False},
            {"symbol": "SYMAUSDT", "gross_pnl": -2.0, "canonical_pnl": -2.0,
             "funding_allocated": 0.0, "is_terminal": True},
        ],
        "portfolio_ledger": [{"ts": 9, "positions": {}}],
        "funding_cashflows": [
            {"symbol": "SYMAUSDT", "cashflow": -4.0},
        ],
        "terminal_positions": [
            {"symbol": "SYMAUSDT", "canonical_pnl": -2.0},
        ],
        "accounting": {},
        "fold_edges_utc": [{"fold_id": "F1"}],
        "fold_segments": [
            {"fold_id": "F1", "start_equity": 100000.0,
             "end_equity": 100010.0, "pnl": 10.0, "return": 0.0001},
        ],
    }


def test_accounting_payload_identity_ok_when_rows_reconcile():
    payload = build_v6p_accounting_payload(
        _base_execution(), experiment_id="E", matrix_id="M")
    # delta 10 == closed 20 + terminal -2 + funding -4 - comm 3 - slip 1
    assert payload["experiment_identity"]["identity_ok"] is True
    assert payload["components"] == {
        "closed_price_pnl": 20.0, "terminal_pnl": -2.0,
        "funding_cashflows": -4.0, "commissions": 3.0, "slippage": 1.0,
        "rejection_costs": 0.0,
    }
    fr = payload["funding_reconciliation"]
    assert fr["all_ok"] is True
    assert fr["settlements_total"] == pytest.approx(-4.0)
    assert fr["legs_allocated_total"] == pytest.approx(-4.0)
    tr = payload["terminal_reconciliation"]
    assert tr["counts_ok"] and tr["sums_ok"] and tr["flat_final_book"]
    assert payload["fold_carry"]["carry_ok"] is True


def test_accounting_payload_flags_broken_identity_and_funding_mismatch():
    execution = _base_execution()
    execution["closed_legs"][0]["gross_pnl"] = 25.0  # break identity by +5
    execution["funding_cashflows"][0]["cashflow"] = -1.0  # funding mismatch
    payload = build_v6p_accounting_payload(
        execution, experiment_id="E", matrix_id="M")
    assert payload["experiment_identity"]["identity_ok"] is False
    fr = payload["funding_reconciliation"]
    assert fr["all_ok"] is False
    assert fr["residual"] != 0


def test_accounting_payload_stub_rows_report_unknown_not_false():
    execution = _base_execution()
    execution["orders"] = [{"symbol": "X"}]  # stub rows carry no fee field
    payload = build_v6p_accounting_payload(
        execution, experiment_id="E", matrix_id="M")
    assert payload["experiment_identity"]["engine_native_rows"] is False
    assert payload["experiment_identity"]["identity_ok"] is None


# --------------------------------------------------------------------------- #
# integration: RISK_MODE_V1 trim enforcement via synthetic panel (N05)
# --------------------------------------------------------------------------- #
def _trim_spec_b() -> dict:
    days = ["2026-01-01", "2026-01-02", "2026-01-03"]
    bars = []
    for day in days:
        # Keep bars off fold-boundary midnights; day 1 additionally starts
        # at 00:00 so the engine's daily cutoff grid catches that stamp.
        stamps = ("00:00", "00:15", "00:30") if day == days[0] \
            else ("00:15", "00:30")
        for hhmm in stamps:
            ts = f"{day}T{hhmm}:00Z"
            close_a = 200.0 if (day == "2026-01-01" and hhmm == "00:30") else 100.0
            close_b = 50.0 if (day == "2026-01-01" and hhmm == "00:30") else 100.0
            for sym, close in (("SYMAUSDT", close_a),
                               ("SYMBUSDT", close_b),
                               ("BTCUSDT", 100.0)):
                bars.append({"symbol": sym, "ts": ts, "open": close,
                             "high": close, "low": close, "close": close,
                             "volume": 1.0})
    return {
        "traded_symbols": ["SYMAUSDT", "SYMBUSDT"],
        "benchmark_symbol": "BTCUSDT",
        "initial_capital": 100000.0,
        "bars": bars,
        "targets": {
            "longs": [["SYMAUSDT", 0.25]],
            "shorts": [["SYMBUSDT", -0.25]],
        },
    }


@pytest.fixture()
def workspace(tmp_path, monkeypatch):
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "research_baseline_altcoin.yaml").write_text(
        "backtest:\n  fee_model: stub\n", encoding="utf-8")
    hyp = tmp_path / "research" / "hypotheses" / "H-XSECT-MOM-v1"
    hyp.mkdir(parents=True)
    (hyp / "candidate.yaml").write_text(
        CANDIDATE_YAML + f'locked_at_utc: "{LOCK_STAMP}"\n', encoding="utf-8")
    dc = tmp_path / "results" / "matrix" / "data_contract_v2"
    dc.mkdir(parents=True)
    (dc / "data_contract_v2.json").write_text('{"schema_version": 2}',
                                              encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _run(workspace, spec, experiment_id):
    spec_path = workspace / f"{experiment_id}-panel.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    from research.portfolio_runner import main

    code = main([
        "--experiment-id", experiment_id,
        "--lookback-days", "3",
        "--window-start", "2026-01-01T00:00Z",
        "--window-end", "2026-01-04T00:00Z",
        "--folds", "3",
        "--matrix-id", "v6p_accounting",
        "--registry-path", "results/registry/experiments.jsonl",
        "--synthetic-panel", str(spec_path),
    ])
    assert code == 0
    return Path("results/portfolio_v4") / experiment_id


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in
            path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_risk_mode_trims_breach_and_post_trim_caps_hold(workspace):
    exp_dir = _run(workspace, _trim_spec_b(), "V6P-TRIM-B")

    metrics = json.loads(
        (exp_dir / "canonical_metrics.json").read_text(encoding="utf-8"))
    assert metrics["risk_mode_requested"] == "RISK_MODE_V1"
    assert metrics["risk_mode_active"] is True
    assert metrics["exposure_control_rows"] >= 1

    # Day-1 00:30 bar doubles the long (100->200) and halves the short
    # (100->50): net fraction ~0.27 > 0.10 cap -> deterministic trim.
    exposure = _read_jsonl(exp_dir / "exposure_control.jsonl")
    net_trims = [r for r in exposure if r["metric"] == "net"]
    assert net_trims, "expected at least one net-cap trim event"
    for row in net_trims:
        assert row["action_taken"] == "reduce_only_trim"
        assert row["value"] > row["cap"]
        assert row["trimmed_notional"] > 0
        assert row["cap"] == pytest.approx(0.10)

    # Enforcement holds on EVERY completed bar: post-trim ledger state must
    # satisfy gross<=1.00 and |net|<=0.10 on all rows.
    ledger = _read_jsonl(exp_dir / "portfolio_ledger.jsonl")
    assert ledger
    assert all(float(r["gross_exposure"]) <= 1.0 + 1e-6 for r in ledger)
    assert all(abs(float(r["net_exposure"])) <= 0.10 + 1e-6 for r in ledger)

    orders = _read_jsonl(exp_dir / "orders.jsonl")
    kinds = {o.get("kind") for o in orders}
    assert "reduce_only_trim" in kinds

    recon = json.loads(
        (exp_dir / "accounting_reconciliation.json").read_text(encoding="utf-8"))
    assert recon["experiment_identity"]["identity_ok"] is True
    assert recon["terminal_reconciliation"]["flat_final_book"] is True
    assert recon["fold_carry"]["carry_ok"] is True


def test_synthetic_panel_runs_are_deterministic(workspace):
    first = _read_jsonl(_run(workspace, _trim_spec_b(), "V6P-DET-1")
                        / "orders.jsonl")
    second = _read_jsonl(_run(workspace, _trim_spec_b(), "V6P-DET-2")
                         / "orders.jsonl")
    assert first == second
