"""Performance reporting for a completed backtest.

Produces a human-readable summary plus optional CSV / JSON artifacts under the
configured output directory.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from nautilus_trader.backtest.engine import BacktestEngine
from nautilus_trader.backtest.engine import BacktestResult
from nautilus_trader.model.identifiers import Venue

from config.settings import ReportSettings


def _fmt(value: object) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:,.4f}"
    return str(value)


def build_summary(result: BacktestResult) -> dict[str, object]:
    """Return a flat, JSON-serialisable summary of a backtest result."""
    risk = getattr(result, "risk_limits", None)
    summary: dict[str, object] = {
        "run_id": result.run_id,
        "iterations": result.iterations,
        "total_events": result.total_events,
        "total_orders": result.total_orders,
        "total_positions": result.total_positions,
        "elapsed_time": result.elapsed_time,
        "stats_pnls": result.stats_pnls,
        "stats_returns": result.stats_returns,
    }
    if risk is not None:
        summary["risk_limits"] = asdict(risk)
    return summary


def print_summary(result: BacktestResult) -> None:
    """Print a formatted performance summary to stdout."""
    line = "-" * 72
    print(line)
    print("PERFORMANCE REPORT")
    print(line)
    print(f"Run ID           : {result.run_id}")
    print(f"Iterations       : {result.iterations:,}")
    print(f"Total events     : {result.total_events:,}")
    print(f"Total orders     : {result.total_orders:,}")
    print(f"Total positions  : {result.total_positions:,}")
    print(f"Elapsed time     : {result.elapsed_time:.3f}s")
    print(line)

    for key, value in (result.stats_returns or {}).items():
        print(f"{key:<36}: {_fmt(value)}")

    pnls = result.stats_pnls or {}
    for group, stats in pnls.items():
        print(line)
        print(f"[{group}]")
        for key, value in stats.items():
            print(f"  {key:<34}: {_fmt(value)}")

    risk = getattr(result, "risk_limits", None)
    if risk is not None:
        print(line)
        print("Risk limits applied:")
        for key, value in asdict(risk).items():
            print(f"  {key:<34}: {_fmt(value)}")
    print(line)


def write_reports(
    engine: BacktestEngine,
    result: BacktestResult,
    settings: ReportSettings,
    *,
    venue: str = "BINANCE",
) -> list[Path]:
    """Write CSV / JSON report artifacts and return the list of written paths."""
    out_dir = Path(settings.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    written: list[Path] = []

    if settings.include_csv:
        account = engine.trader.generate_account_report(venue=Venue(venue))
        if not account.empty:
            p = out_dir / "account.csv"
            account.to_csv(p)
            written.append(p)

        fills = engine.trader.generate_order_fills_report()
        if not fills.empty:
            p = out_dir / "order_fills.csv"
            fills.to_csv(p)
            written.append(p)

        positions = engine.trader.generate_positions_report()
        if not positions.empty:
            p = out_dir / "positions.csv"
            positions.to_csv(p)
            written.append(p)

    if settings.include_json:
        p = out_dir / "summary.json"
        with p.open("w", encoding="utf-8") as f:
            json.dump(build_summary(result), f, indent=2, default=str)
        written.append(p)

    return written


def performance_report(
    engine: BacktestEngine,
    result: BacktestResult,
    settings: ReportSettings,
    *,
    venue: str = "BINANCE",
) -> list[Path]:
    """Print a summary and write report artifacts."""
    print_summary(result)
    return write_reports(engine, result, settings, venue=venue)
