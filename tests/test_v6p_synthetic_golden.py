"""V6P synthetic-panel golden fixtures (PLAN section 6.3 items 1-9, owner A4).

Runs the REAL scored pipeline (real shared-capital engine) against the
deterministic ``--synthetic-panel`` injection path: two traded symbols +
flat BTC benchmark, two 15m bars per UTC day (three on day 1), three
declared folds, one known funding settlement. Every number below is
hand-derived:

Per fold the book opens +/-0.25 weights at the first bar of the fold and
force-closes at its last bar (constant ref prices => zero gross leg PnL),
so equity moves ONLY through commissions + slippage (-) and funding (+/-):

    open/close cost per side, fold 1 (qty 250):
        BUY  250 @ 100.01 -> fee 12.50125 + slip 2.5 = 15.00125
        SELL 250 @  99.99 -> fee 12.49875 + slip 2.5 = 14.99875
        (terminal close mirrors the open costs)
    fold 1 equity: 100000 - 30 + funding(+5) - 30 = 99945
    fold 2 target qty = floor_step(0.25*99945/100, 0.001) = 249.862
        per-side cost = fee + slip = 12.49434931/12.49185069 + 2.49862
        fold delta = -(29.98344 * 2) = -59.96688 -> 99885.03312
    fold 3 target qty = floor_step(0.25*99885.03312/100, 0.001) = 249.712
        per-side cost = 12.48684856/12.48435144 + 2.49712
        fold delta = -(29.96544 * 2) = -59.93088 -> 99825.10224
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

DAY_NS = 86_400_000_000_000
WINDOW_START = "2026-01-01T00:00Z"
WINDOW_END = "2026-01-04T00:00Z"
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


def _ns(iso_text: str) -> int:
    text = iso_text.replace("Z", "+00:00")
    dt = datetime.fromisoformat(text).astimezone(timezone.utc)
    return int(dt.timestamp() * 1_000_000_000)


def _ms(iso_text: str) -> int:
    return _ns(iso_text) // 1_000_000


def _bars(day_isos, closes_by_symbol):
    # Bars deliberately avoid internal fold-boundary midnights (the engine
    # claims a boundary timestamp for the EARLIER fold). Day 1 carries one
    # extra 00:00 bar so the engine's daily cutoff grid initializes on the
    # day-1 midnight stamp instead of skipping it.
    rows = []
    for day_iso in day_isos:
        stamps = ("00:00", "00:15", "00:30") if day_iso == day_isos[0] \
            else ("00:15", "00:30")
        for hhmm in stamps:
            ts = f"{day_iso}T{hhmm}:00Z"
            for sym, close in closes_by_symbol.items():
                rows.append({
                    "symbol": sym, "ts": ts,
                    "open": close, "high": close,
                    "low": close, "close": close, "volume": 1.0,
                })
    return rows


def _golden_spec_a() -> dict:
    days = ["2026-01-01", "2026-01-02", "2026-01-03"]
    return {
        "traded_symbols": ["SYMAUSDT", "SYMBUSDT"],
        "benchmark_symbol": "BTCUSDT",
        "initial_capital": 100000.0,
        "fee_taker": 0.0005,
        "slippage_ticks": 1,
        "tick_size": {"*": 0.01},
        "step_size": {"*": 0.001},
        "min_notional": 5.0,
        # Flat ref prices everywhere: zero gross leg PnL, costs/funding only.
        "bars": _bars(days, {
            "SYMAUSDT": 100.0, "SYMBUSDT": 100.0, "BTCUSDT": 100.0,
        }),
        "funding": [
            {"symbol": "SYMAUSDT",
             "funding_time_ms": _ms("2026-01-01T00:30:00Z"),
             "fundingRate": "0.0001"},
            {"symbol": "SYMBUSDT",
             "funding_time_ms": _ms("2026-01-01T00:30:00Z"),
             "fundingRate": "0.0003"},
        ],
        "targets": {
            "longs": [["SYMAUSDT", 0.25]],
            "shorts": [["SYMBUSDT", -0.25]],
        },
    }


@pytest.fixture()
def workspace(tmp_path, monkeypatch):
    """Repo-shaped tmp cwd with locked candidate + frozen runtime config."""
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


def _run_golden(workspace, spec, experiment_id):
    spec_path = workspace / f"{experiment_id}-panel.json"
    spec_path.write_text(json.dumps(spec), encoding="utf-8")
    from research.portfolio_runner import main

    code = main([
        "--experiment-id", experiment_id,
        "--lookback-days", "3",
        "--window-start", WINDOW_START,
        "--window-end", WINDOW_END,
        "--folds", "3",
        "--matrix-id", "v6p_golden",
        "--registry-path", "results/registry/experiments.jsonl",
        "--synthetic-panel", str(spec_path),
    ])
    assert code == 0
    return Path("results/portfolio_v4") / experiment_id


def _read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in
            path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_synthetic_golden_full_accounting(workspace):
    exp_dir = _run_golden(workspace, _golden_spec_a(), "V6P-GOLDEN-A")

    for name in ("portfolio_ledger.jsonl", "orders.jsonl", "positions.jsonl",
                 "funding_cashflows.jsonl", "terminal_positions.jsonl",
                 "exposure_control.jsonl", "accounting_reconciliation.json",
                 "commission_slippage.json"):
        assert (exp_dir / name).is_file(), name

    metrics = json.loads(
        (exp_dir / "canonical_metrics.json").read_text(encoding="utf-8"))
    approx = pytest.approx

    # Continuous-capital fold chain (N04).
    assert metrics["starting_equity"] == pytest.approx(100000.0)
    assert metrics["ending_equity"] == approx(99825.10224, rel=1e-9)
    assert metrics["total_pnl"] == approx(-174.89776, rel=1e-9)
    assert metrics["fold_pnls"]["F1"] == approx(-55.0, rel=1e-9)
    assert metrics["fold_pnls"]["F2"] == approx(-59.96688, rel=1e-9)
    assert metrics["fold_pnls"]["F3"] == approx(-59.93088, rel=1e-9)
    assert metrics["fold_returns"]["F1"] == approx(-0.00055, rel=1e-9)
    assert metrics["fold_returns"]["F2"] == approx(
        99885.03312 / 99945.0 - 1.0, rel=1e-9)
    assert metrics["fold_returns"]["F3"] == approx(
        99825.10224 / 99885.03312 - 1.0, rel=1e-9)
    assert metrics["fold_carry_ok"] is True
    assert metrics["fold_carry_max_gap"] == approx(0.0, abs=1e-9)

    # MDD from the CONTINUOUS path: monotonic decline from 100k peak
    # (stitched 100k resets would give max single-fold dd instead).
    assert metrics["max_drawdown_fraction"] == approx(
        174.89776 / 100000.0, rel=1e-9)

    # Risk mode wired end-to-end (N05); no breach in this scenario.
    assert metrics["risk_mode_requested"] == "RISK_MODE_V1"
    assert metrics["risk_mode_active"] is True
    assert metrics["exposure_control_rows"] == 0

    ledger = _read_jsonl(exp_dir / "portfolio_ledger.jsonl")
    assert ledger, "ledger rows missing"
    assert all(float(r["gross_exposure"]) <= 1.0 + 1e-6 for r in ledger)
    assert all(abs(float(r["net_exposure"])) <= 0.10 + 1e-6 for r in ledger)
    assert ledger[-1]["positions"] == {}  # flat final book

    # Settlement-level funding rows (hand-computed cashflows).
    funding = _read_jsonl(exp_dir / "funding_cashflows.jsonl")
    by_sym = {r["symbol"]: r for r in funding}
    assert set(by_sym) == {"SYMAUSDT", "SYMBUSDT"}
    assert by_sym["SYMAUSDT"]["cashflow"] == approx(-2.5, rel=1e-9)
    assert by_sym["SYMAUSDT"]["rate"] == approx(0.0001, rel=1e-12)
    assert by_sym["SYMBUSDT"]["cashflow"] == approx(7.5, rel=1e-9)
    assert by_sym["SYMBUSDT"]["rate"] == approx(0.0003, rel=1e-12)

    # Orders: open + terminal_liquidate per side per fold = 12 executed.
    orders = _read_jsonl(exp_dir / "orders.jsonl")
    executed = [o for o in orders if o.get("rejected_reason") is None]
    assert len(executed) == 12
    kinds = {}
    for o in executed:
        kinds[o["kind"]] = kinds.get(o["kind"], 0) + 1
    assert kinds == {"open": 6, "terminal_liquidate": 6}
    fold1_opens = [o for o in executed
                   if o["kind"] == "open" and o["ts"] == _ns("2026-01-01T00:00:00Z")]
    assert {o["symbol"]: o["qty"] for o in fold1_opens} == {
        "SYMAUSDT": 250.0, "SYMBUSDT": 250.0}
    fold2_qty = next(o["qty"] for o in executed
                     if o["kind"] == "open"
                     and o["ts"] == _ns("2026-01-02T00:15:00Z"))
    assert fold2_qty == 249.862  # floor_step(0.25*99945/100, 0.001)

    # Terminal rows reconcile to terminal closed legs; book left flat (N06).
    terminal_rows = _read_jsonl(exp_dir / "terminal_positions.jsonl")
    assert len(terminal_rows) == 6
    assert all(r["is_terminal"] for r in terminal_rows)

    # Exposure control file exists and is empty for this benign scenario.
    assert _read_jsonl(exp_dir / "exposure_control.jsonl") == []

    recon = json.loads(
        (exp_dir / "accounting_reconciliation.json").read_text(encoding="utf-8"))
    assert recon["identity_formula"].startswith("ending_equity - starting_equity")
    assert recon["experiment_identity"]["identity_ok"] is True
    assert recon["experiment_identity"]["residual"] == approx(0.0, abs=1e-6)
    assert recon["engine_accounting"]["all_ok"] is True
    assert set(recon["engine_accounting"]["per_fold"]) == {"0", "1", "2"}
    assert all(row["identity_ok"]
               for row in recon["engine_accounting"]["per_fold"].values())
    fr = recon["funding_reconciliation"]
    assert fr["all_ok"] is True
    assert fr["settlements_total"] == approx(5.0, rel=1e-9)
    assert fr["legs_allocated_total"] == approx(5.0, rel=1e-9)
    tr = recon["terminal_reconciliation"]
    assert tr["counts_ok"] is True and tr["sums_ok"] is True
    assert tr["terminal_rows"] == 6 and tr["terminal_closed_legs"] == 6
    assert tr["flat_final_book"] is True
    fc = recon["fold_carry"]
    assert fc["carry_ok"] is True
    assert fc["max_gap"] == approx(0.0, abs=1e-9)
    assert fc["folds"][1]["start_equity"] == approx(
        fc["folds"][0]["end_equity"], rel=1e-12)
    assert fc["folds"][1]["start_equity"] == approx(99945.0, rel=1e-9)

    costs = json.loads(
        (exp_dir / "commission_slippage.json").read_text(encoding="utf-8"))
    assert costs["total_commission"] == approx(149.9148, rel=1e-9)
    assert costs["total_slippage"] == approx(29.98296, rel=1e-9)

    # Artifact hash manifest covers the new V6P artifacts.
    hashes = json.loads(
        (exp_dir / "artifact_hashes.json").read_text(encoding="utf-8"))["hashes"]
    for name in ("funding_cashflows.jsonl", "terminal_positions.jsonl",
                 "exposure_control.jsonl", "accounting_reconciliation.json",
                 "commission_slippage.json"):
        assert name in hashes, name
