from __future__ import annotations

import json
from pathlib import Path

from scripts.status_report import build_status_table
from scripts.status_report import collect_rows
from scripts.status_report import render_table


def _make_fixture(tmp_path: Path) -> tuple[Path, Path]:
    results = tmp_path / "results"
    forward_dir = results / "forward_test"
    scan_dir = results / "scan_matrix" / "20260801T000000Z"
    snap_dir = tmp_path / "research_snapshots"
    for directory in (forward_dir, scan_dir, snap_dir):
        directory.mkdir(parents=True)

    forward_payload = {
        "symbol": "BTCUSDT",
        "strategy_type": "mean_reversion",
        "holdout_days": 60,
        "window_end": "2026-08-01T00:00:00+00:00",
        "trades": 10,
        "expectancy": 0.1234,
        "profit_factor": 1.5,
        "win_rate": 0.6,
        "pnl": 12.3,
        "passes_oos": True,
    }
    (forward_dir / "20260801.json").write_text(json.dumps(forward_payload))

    scan_payload = [
        {
            "strategy_type": "reclaim_mr",
            "symbol": "NEARUSDT",
            "trades": 182,
            "positive_folds_after": "4/6",
            "exp_after": 0.148086,
            "pf_after": 1.463,
            "gate": "folds<5/6|bh_fail",
        },
        {
            "strategy_type": "reclaim_mr",
            "symbol": "ETHUSDT",
            "trades": 149,
            "positive_folds_after": "4/6",
            "exp_after": -0.150604,
            "pf_after": 0.611,
            "gate": "exp<=0",
        },
    ]
    (scan_dir / "report.json").write_text(json.dumps(scan_payload))

    tradfi_payload = {"eligible_count": 71, "total_contracts": 872}
    (snap_dir / "binance_tradfi_20260801.json").write_text(json.dumps(tradfi_payload))
    return results, snap_dir


def test_table_rows_from_small_fixture(tmp_path: Path) -> None:
    results, snapshots = _make_fixture(tmp_path)
    rows = collect_rows(results, snapshots)

    assert ("Forward-test BTCUSDT (mean_reversion)", "2026-08-01",
            "Trades 10 · Exp 0.12 · PF 1.50", "PASS OOS") in rows
    assert (
        "Scan matrix 20260801T000000Z (2 combos)",
        "2026-08-01",
        "Tốt nhất: NEARUSDT reclaim_mr · Exp 0.15 · PF 1.46 · folds 4/6",
        "1/2 đạt gate (Exp>0 & PF>=1.2)",
    ) in rows
    assert ("TradFi snapshot (USD-M universe)", "2026-08-01",
            "Đủ điều kiện 71/872 hợp đồng", "OK") in rows


def test_render_table_contains_header_and_rows(tmp_path: Path) -> None:
    results, snapshots = _make_fixture(tmp_path)
    table = build_status_table(results, snapshots)
    lines = table.splitlines()

    assert lines[0].startswith("| mục ")
    for header in ("mục", "ngày", "chỉ số chính", "trạng thái"):
        assert header in lines[0]
    assert "| Forward-test BTCUSDT (mean_reversion)" in table
    assert "| PASS OOS" in table
    assert "1/2 đạt gate" in table


def test_missing_artifacts_renders_placeholder_row(tmp_path: Path) -> None:
    empty_results = tmp_path / "empty_results"
    empty_snapshots = tmp_path / "empty_snapshots"
    empty_results.mkdir()
    empty_snapshots.mkdir()

    rows = collect_rows(empty_results, empty_snapshots)
    assert rows == []
    assert "chưa có artifact" in render_table(rows)


def test_forward_test_fail_oos_status(tmp_path: Path) -> None:
    forward_dir = tmp_path / "results" / "forward_test"
    forward_dir.mkdir(parents=True)
    payload = {"symbol": "ETHUSDT", "strategy_type": "mean_reversion",
               "trades": 11, "expectancy": -0.4, "profit_factor": 0.75,
               "passes_oos": False}
    (forward_dir / "20260823.json").write_text(json.dumps(payload))

    rows = collect_rows(tmp_path / "results", tmp_path / "nope")
    assert rows[0][0] == "Forward-test ETHUSDT (mean_reversion)"
    assert rows[0][3] == "FAIL OOS"
