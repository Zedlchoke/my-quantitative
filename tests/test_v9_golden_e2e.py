"""V9 golden end-to-end: TS-TREND through the REAL runner+engine (A3).

Wires ``research.v9_ts_trend`` through the REAL scored CLI path
(``research.portfolio_runner.main`` -> ``PORTFOLIO_SIGNAL_FAMILY=ts_trend``
dispatch -> embargoed Monday stamps -> ``research.portfolio_engine.
run_shared_capital_backtest``) over a hand-computable 6-symbol synthetic
panel (test_weekly_golden_e2e pattern).

Hand-derived golden math (all numbers exact by construction):

Window 2026-01-05T00:00Z .. 2026-02-16T00:00Z, 3 chronological folds of
exactly 14 days. Weekly Monday stamps with the 7-day fold embargo leave
exactly ONE scored cutoff per fold: Jan12, Jan26, Feb9 (00:00 UTC).
Warmup: max(14+7, ts_trend floor 21) = 21 days -> panel starts 2025-12-22.

Panel: one 15m bar per symbol per day at 12:00 UTC (step-function prices,
so each UTC day's close == that bar's price); daily closes carry stamp
D 00:00 for day D. The family reads closes STRICTLY BEFORE the cutoff, so
a Monday cutoff scores last_close(Monday-1d) against close(<= Monday-14d):

    symbol   Jan12 (ref Dec29 -> last Jan11)   | trend book +-0.20/slot
    AAAUSDT  200/100 - 1 = +100%   LONG        | long  {AAA, BBB}
    BBBUSDT  110/100 - 1 = +10%    LONG        | short {DDD, EEE}
    CCCUSDT    0                   FLAT        |
    DDDUSDT   50/100 - 1 = -50%    SHORT       |
    EEEUSDT   80/100 - 1 = -20%    SHORT       |
    FFFUSDT    0                   FLAT        |

At Jan26 every series is flat across the trailing window => ALL FLAT (OK
book with no positions; the engine skips the empty rebalance). At Feb9
only AAA (+20%: 240/200) and BBB (+10%: 121/110) trend => SINGLE-SIDED
long book carrying the FULL 0.80 gross: +0.40 per slot.

Determinism proof: the SAME scored CLI runs into two different temp roots
and the canonical_metrics.json artifacts must be byte-identical except
the experiment_id field, with equal orders/positions digests.

Negative control XSECT-TSTREND-CTRL (--reverse): inverted trend sign --
long {DDD, EEE} / short {AAA, BBB} end-to-end.
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

from research.portfolio_runner import (  # noqa: E402
    SIGNAL_FAMILY_ENV,
    main,
    read_jsonl,
    verify_artifact_hashes,
)

UTC = timezone.utc
WINDOW_START = "2026-01-05T00:00:00Z"
WINDOW_END = "2026-02-16T00:00:00Z"
LOCK_STAMP = "2026-01-04T00:00:00+00:00"
MATRIX_ID = "v9_multifamily"
REGISTRY_SHARD = "results/registry/shards/v9_ts_trend.jsonl"

TRADED = ["AAAUSDT", "BBBUSDT", "CCCUSDT", "DDDUSDT", "EEEUSDT", "FFFUSDT"]
BENCHMARK = "BTCUSDT"
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
        if day <= "2026-01-04":
            return 100.0
        return 240.0 if day >= "2026-01-27" else 200.0
    if symbol == "BBBUSDT":
        if day <= "2026-01-04":
            return 100.0
        return 121.0 if day >= "2026-01-27" else 110.0
    if symbol == "DDDUSDT":
        return 50.0 if day >= "2026-01-05" else 100.0
    if symbol == "EEEUSDT":
        return 80.0 if day >= "2026-01-05" else 100.0
    return 100.0  # CCCUSDT / FFFUSDT / BTCUSDT benchmark-flat


def golden_spec() -> dict:
    bars = []
    for day in _daterange("2025-12-15", "2026-02-15"):
        for sym in [*TRADED, BENCHMARK]:
            px = price_for(sym, day)
            bars.append({
                "symbol": sym, "ts": f"{day}T12:00:00Z",
                "open": px, "high": px, "low": px, "close": px,
                "volume": 1.0,
            })
    funding_rows = [
        {"symbol": sym, "funding_time_ms":
            int(dt(f"{day}T08:00:00Z").timestamp() * 1000),
         "fundingRate": "0.0001"}
        for day in _daterange("2025-12-23", "2026-02-15") for sym in TRADED
    ]
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
        "funding": funding_rows,
    }


CANDIDATE_YAML = (
    "hypothesis_id: H-XSECT-MOM-v1\n"
    "family: v9_ts_trend\n"
    "candidate_version: 1\n"
    "owner_agent: A3\n"
    "universe:\n"
    f"  traded_symbols: [{', '.join(TRADED)}]\n"
    f"  benchmark_symbol: {BENCHMARK}\n"
    "signal:\n"
    "  type: ts_trend\n"
    "  lookback_days: [14]\n"
)


def _scaffold_root(root: Path) -> Path:
    (root / "config").mkdir(parents=True)
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
    spec_path = root / "v9_ts_trend_panel_spec.json"
    spec_path.write_text(json.dumps(golden_spec()), encoding="utf-8")
    return spec_path


def _run_scored(root: Path, spec_path: Path, experiment_id: str,
                *, reverse: bool = False) -> Path:
    os.environ.pop(SIGNAL_FAMILY_ENV, None)
    argv = [
        "--experiment-id", experiment_id,
        "--lookback-days", "14",
        "--window-start", WINDOW_START,
        "--window-end", WINDOW_END,
        "--folds", "3",
        "--matrix-id", MATRIX_ID,
        "--output-root", "results/portfolio_v9",
        "--registry-path", REGISTRY_SHARD,
        "--synthetic-panel", str(spec_path),
        "--signal-family", "ts_trend",
    ]
    if reverse:
        argv.append("--reverse")
    code = main(argv)
    assert code == 0, experiment_id
    os.environ.pop(SIGNAL_FAMILY_ENV, None)
    return root / "results" / "portfolio_v9" / experiment_id


@pytest.fixture(scope="module")
def golden(tmp_path_factory):
    """TWO independent deterministic workspaces + one control run."""
    root_a = tmp_path_factory.mktemp("v9_tstrend_golden_a")
    root_b = tmp_path_factory.mktemp("v9_tstrend_golden_b")
    saved_env = os.environ.get(SIGNAL_FAMILY_ENV)
    prev_cwd = os.getcwd()

    try:
        exp_a = exp_b = exp_ctrl = None
        for tag, root in (("A", root_a), ("B", root_b)):
            spec_path = _scaffold_root(root)
            os.chdir(root)
            exp = _run_scored(root, spec_path, f"V9-TSTREND-GOLDEN-{tag}")
            if tag == "A":
                exp_a = exp
                exp_ctrl = _run_scored(root, spec_path,
                                       "XSECT-TSTREND-CTRL-A", reverse=True)
                shard_a = root / REGISTRY_SHARD
            else:
                exp_b = exp
        yield {
            "root_a": root_a,
            "root_b": root_b,
            "exp_a": exp_a,
            "exp_b": exp_b,
            "exp_ctrl": exp_ctrl,
            "shard_a": shard_a,
        }
    finally:
        os.chdir(prev_cwd)
        if saved_env is None:
            os.environ.pop(SIGNAL_FAMILY_ENV, None)
        else:
            os.environ[SIGNAL_FAMILY_ENV] = saved_env


def _json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _executed(rows: list[dict]) -> list[dict]:
    return [row for row in rows if row.get("rejected_reason") is None]


# --------------------------------------------------------------------------- #
# Golden schedule, picks, diagnostics, registry/output contract
# --------------------------------------------------------------------------- #
def test_ts_trend_golden_schedule_picks_and_contract(golden):
    exp = golden["exp_a"]
    assert exp.parent.name == "portfolio_v9"
    assert verify_artifact_hashes(exp) == []

    ranks = read_jsonl(exp / "signal_ranks.jsonl")
    assert len(ranks) == 3  # ONE embargoed Monday stamp per fold
    assert [row["rebalance_ts_utc"][:10] for row in ranks] == \
        list(SCORED_CUTOFFS)
    assert ranks[0]["status"] == "OK"
    assert ranks[0]["longs"] == [["AAAUSDT", 0.2], ["BBBUSDT", 0.2]]
    assert ranks[0]["shorts"] == [["DDDUSDT", -0.2], ["EEEUSDT", -0.2]]
    # Mid-window quietness => zero trailing returns everywhere => FLAT book.
    assert ranks[1] == {"experiment_fold": ranks[1]["experiment_fold"],
                        "rebalance_ts_utc": ranks[1]["rebalance_ts_utc"],
                        "signal_cutoff_ns": ranks[1]["signal_cutoff_ns"],
                        "status": "OK", "longs": [], "shorts": [],
                        "lookback_days": 14, "reverse": False}
    # Single-sided continuation: full 0.80 gross on the long side only.
    assert ranks[2]["status"] == "OK"
    assert ranks[2]["longs"] == [["AAAUSDT", 0.4], ["BBBUSDT", 0.4]]
    assert ranks[2]["shorts"] == []

    diagnostics = read_jsonl(exp / "signal_diagnostics.jsonl")
    assert len(diagnostics) == 3
    head = diagnostics[0]
    assert head["derived_diagnostics"] is True
    assert head["family"] == "ts_trend"
    assert head["skipped_reason"] is None
    assert head["lookback_days"] == 14
    assert head["per_symbol"]["AAAUSDT"]["trailing_return"] == \
        pytest.approx(1.0, abs=1e-12)
    assert head["per_symbol"]["DDDUSDT"]["trailing_return"] == \
        pytest.approx(-0.5, abs=1e-12)
    assert diagnostics[2]["per_symbol"]["AAAUSDT"]["trailing_return"] == \
        pytest.approx(0.2, abs=1e-12)

    metrics = _json(exp / "canonical_metrics.json")
    assert metrics["rebalances_scored"] == 2  # Jan26 book is flat -> skipped
    # F3's single-sided +0.80 long book trips the engine-side RISK_MODE_V1
    # hard_abs_net_cap (0.10): the SIGNAL targets stay 0.40/slot (ranks
    # above) while the exposure layer deterministically trims to the cap.
    assert metrics["legs_closed"] == 8  # 4 (F1) + 2 opens + 2 trims (F3)
    assert metrics["max_abs_target_weight"] == pytest.approx(0.40)
    assert metrics["risk_mode_requested"] == "RISK_MODE_V1"
    assert metrics["risk_mode_active"] is True
    assert metrics["fold_carry_ok"] is True
    assert sorted(metrics["fold_pnls"]) == ["F1", "F2", "F3"]

    manifest = yaml.safe_load(
        (exp / "launch_manifest.yaml").read_text("utf-8"))
    assert manifest["matrix_id"] == MATRIX_ID
    assert int(manifest["lookback_days"]) == 14
    assert int(manifest["warmup_bars"]) >= 21 * 96  # ts_trend warmup floor

    shard_rows = read_jsonl(golden["shard_a"])
    entry = next(row for row in shard_rows
                 if row.get("experiment_id") == "V9-TSTREND-GOLDEN-A"
                 and row.get("kind") == "CELL_RESULT")
    assert entry["status"] == "COMPLETED"
    assert entry["matrix_id"] == MATRIX_ID
    assert entry["inprocess_integrity"]["manifest_verify_reasons"] == []
    matrix_index = _json(exp.parent.parent.parent / "results" / "matrix" /
                         MATRIX_ID / "index.json")
    assert matrix_index["cells"]["V9-TSTREND-GOLDEN-A"]["status"] == \
        "COMPLETED"


def test_ts_trend_golden_orders_funding_accounting(golden):
    exp = golden["exp_a"]
    orders = _executed(read_jsonl(exp / "orders.jsonl"))
    kinds = {}
    for order in orders:
        kinds[order["kind"]] = kinds.get(order["kind"], 0) + 1
    # reduce_only_trim: RISK_MODE_V1 net-cap enforcement on the F3
    # single-sided book (see metrics note in the schedule test).
    assert kinds == {"open": 6, "reduce_only_trim": 2,
                     "terminal_liquidate": 6}

    cutoff_ns = ns(SCORED_CUTOFFS[0])
    first_opens = [o for o in orders
                   if o["kind"] == "open" and o["ts"] == ns(FIRST_OPEN_UTC)]
    assert len(first_opens) == 4
    assert all(o["ts"] >= cutoff_ns for o in orders)
    by_sym = {o["symbol"]: o for o in first_opens}
    assert {by_sym[s]["side"] for s in ("AAAUSDT", "BBBUSDT")} == {"BUY"}
    assert {by_sym[s]["side"] for s in ("DDDUSDT", "EEEUSDT")} == {"SELL"}

    ledger = read_jsonl(exp / "portfolio_ledger.jsonl")
    assert ledger
    assert ledger[-1]["positions"] == {}  # flat final book
    assert all(row["cash_identity_ok"] for row in ledger)
    assert all(float(row["gross_exposure"]) <= 1.0 + 1e-6 for row in ledger)

    funding = read_jsonl(exp / "funding_cashflows.jsonl")
    sums = {}
    for row in funding:
        sums[row["symbol"]] = sums.get(row["symbol"], 0.0) + row["cashflow"]
    assert sums["AAAUSDT"] < 0 and sums["BBBUSDT"] < 0      # longs pay
    assert sums["DDDUSDT"] > 0 and sums["EEEUSDT"] > 0      # shorts receive

    recon = _json(exp / "accounting_reconciliation.json")
    assert recon["experiment_identity"]["identity_ok"] is True
    assert recon["engine_accounting"]["all_ok"] is True
    assert recon["funding_reconciliation"]["all_ok"] is True
    assert recon["terminal_reconciliation"]["flat_final_book"] is True
    costs = _json(exp / "commission_slippage.json")
    assert costs["total_commission"] > 0 and costs["total_slippage"] > 0


# --------------------------------------------------------------------------- #
# Determinism: two scored CLI runs in DIFFERENT temp roots
# --------------------------------------------------------------------------- #
def test_two_temp_roots_byte_identical_canonical_metrics(golden):
    path_a = golden["exp_a"] / "canonical_metrics.json"
    path_b = golden["exp_b"] / "canonical_metrics.json"
    text_a = path_a.read_text(encoding="utf-8")
    text_b = path_b.read_text(encoding="utf-8")
    # Byte-identical except the experiment_id field.
    assert text_a.replace("V9-TSTREND-GOLDEN-A", "V9-TSTREND-GOLDEN-B") == \
        text_b
    doc_a, doc_b = _json(path_a), _json(path_b)
    assert doc_a.pop("experiment_id") != doc_b.pop("experiment_id")
    assert doc_a == doc_b
    for name in ("portfolio_ledger.jsonl", "orders.jsonl",
                 "positions.jsonl", "signal_ranks.jsonl"):
        da = hashlib.sha256((golden["exp_a"] / name).read_bytes()).hexdigest()
        db = hashlib.sha256((golden["exp_b"] / name).read_bytes()).hexdigest()
        assert da == db, name
    metrics = doc_a
    assert metrics["orders_digest"] == doc_b.get("orders_digest") or \
        metrics == doc_b


# --------------------------------------------------------------------------- #
# Negative control XSECT-TSTREND-CTRL: inverted trend sign, end-to-end
# --------------------------------------------------------------------------- #
def test_control_run_inverts_trend_sides_end_to_end(golden):
    base_row = read_jsonl(golden["exp_a"] / "signal_ranks.jsonl")[0]
    ctrl_ranks = read_jsonl(golden["exp_ctrl"] / "signal_ranks.jsonl")
    ctrl_row = ctrl_ranks[0]
    assert ctrl_row["reverse"] is True
    assert ctrl_row["longs"] == [["DDDUSDT", 0.2], ["EEEUSDT", 0.2]]
    assert ctrl_row["shorts"] == [["AAAUSDT", -0.2], ["BBBUSDT", -0.2]]
    assert {s for s, _ in ctrl_row["longs"]} == \
        {s for s, _ in base_row["shorts"]}
    assert {s for s, _ in ctrl_row["shorts"]} == \
        {s for s, _ in base_row["longs"]}
    assert len(_executed(read_jsonl(
        golden["exp_ctrl"] / "orders.jsonl"))) == 14

    gate = _json(golden["exp_ctrl"] / "gate_result.json")
    assert gate["cell_verdict"] == "CONTROL_ONLY"
    assert gate["is_negative_control"] is True

    def fund_sums(exp: Path) -> dict:
        sums = {}
        for row in read_jsonl(exp / "funding_cashflows.jsonl"):
            sums[row["symbol"]] = sums.get(row["symbol"], 0.0) + \
                row["cashflow"]
        return sums

    fwd, ctl = fund_sums(golden["exp_a"]), fund_sums(golden["exp_ctrl"])
    for sym in ("AAAUSDT", "BBBUSDT"):
        assert fwd[sym] < 0 and ctl[sym] > 0  # roles swapped end-to-end
    for sym in ("DDDUSDT", "EEEUSDT"):
        assert fwd[sym] > 0 and ctl[sym] < 0
