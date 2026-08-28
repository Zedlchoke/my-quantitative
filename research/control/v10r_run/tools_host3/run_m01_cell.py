"""V10R R3 — M01 scored-cell driver (one arm per invocation, serial).

Runs ONE preregistered arm (anchor M01-A / neighbour M01-N / control C2)
through the frozen adapter (run_full_stress_matrix) on the exec tree, with a
preflight pin artifact written BEFORE any scored metric exists, and exactly-
once trial publication via the frozen BG6 path (publish_trial) only with
--publish. Day-mean is a diagnostic substitution and is deliberately NOT a
scored arm here (owner directive 2026-08-28).

Data-feed pin: bars are read with the panel's deterministic duplicate rule
(lexically-last part wins per close stamp) because the inherited BTCUSDT/
ETHUSDT overlapping parts make hyp_a8_m01.read_bars_15m's strict
no-duplicate rejection unapplicable; every resolved value was verified
digit-exact against live fapi on all 8 consumed fields for the full
prewindow+window (host3_full_window_8field_report.json). This deviation is
recorded in the preflight artifact of every cell.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(r"C:\Users\ROYAL\my-quantitative")
DEFAULT_EXEC = Path(r"C:\Users\ROYAL\exec-v10-R1c")

ARM_SPECS = {
    "anchor": {"control_mode": "anchor", "neighbour_mode": "cross_sectional_z"},
    "neighbour": {"control_mode": "anchor", "neighbour_mode": "prewindow_dispersion"},
    "c2": {"control_mode": "c2_price_contrarian_placebo", "neighbour_mode": "cross_sectional_z"},
}
ARM_ORDER = ("anchor", "neighbour", "c2")


def dedupe_bars(catalog: Path, symbols, start_ns: int, end_ns: int):
    """M01Bar feed with panel dedupe semantics (lexically-last part wins)."""
    sys.path.insert(0, str(REPO))  # for yaml only
    import yaml

    import pyarrow.parquet as pq

    sys.path.insert(0, str(DEFAULT_EXEC))
    from research.hyp_a8_m01 import (  # noqa: E402
        M01Bar, _bar_type_dir, _decode_fixed16, _finite_decimal,
    )

    bars: dict[str, list] = {}
    for sym in symbols:
        files = sorted(Path(_bar_type_dir(str(catalog), sym)).rglob("*.parquet"))
        by_ts: dict[int, M01Bar] = {}
        for path in files:
            t = pq.read_table(path).to_pandas()
            cols = {c: t[c].tolist() for c in (
                "ts_event", "ts_init", "open", "high", "low", "close", "volume",
                "quote_volume", "count", "taker_buy_quote_volume")}
            for i, ts in enumerate(cols["ts_event"]):
                ts = int(ts)
                if ts < start_ns or ts > end_ns:
                    continue
                by_ts[ts] = M01Bar(
                    ts_event_ns=ts,
                    ts_init_ns=int(cols["ts_init"][i]),
                    open=_decode_fixed16(cols["open"][i]),
                    high=_decode_fixed16(cols["high"][i]),
                    low=_decode_fixed16(cols["low"][i]),
                    close=_decode_fixed16(cols["close"][i]),
                    volume=_decode_fixed16(cols["volume"][i]),
                    quote_volume=_finite_decimal(cols["quote_volume"][i]),
                    taker_buy_quote_volume=_finite_decimal(
                        cols["taker_buy_quote_volume"][i]
                    ),
                    count=int(cols["count"][i]),
                )
        bars[sym] = [by_ts[ts] for ts in sorted(by_ts)]
    return bars


def series_digest(bars: dict) -> str:
    h = hashlib.sha256()
    for sym in sorted(bars):
        for b in bars[sym]:
            h.update(f"{sym}|{b.ts_event_ns}|{b.open}|{b.high}|{b.low}|{b.close}|"
                     f"{b.volume}|{b.quote_volume}|{b.taker_buy_quote_volume}|{b.count}".encode())
    return h.hexdigest()


def load_settlements(funding_root: Path, symbols):
    sys.path.insert(0, str(DEFAULT_EXEC))
    from research.adapter_v10.protocol import SettlementPoint  # noqa: E402

    out = {}
    for sym in symbols:
        rows = json.loads((funding_root / sym / "funding.json").read_text())["rows"]
        out[sym] = tuple(
            SettlementPoint(publish_ts_ns=int(r["fundingTime"]) * 10**6,
                            value=float(r["fundingRate"]), kind="funding")
            for r in rows
        )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", choices=ARM_ORDER, required=True)
    ap.add_argument("--exec-root", default=str(DEFAULT_EXEC))
    ap.add_argument("--catalog", default="catalog_live_crypto")
    ap.add_argument("--funding-root", default="funding_data/scan_2026")
    ap.add_argument("--out-root", default="results/v10r_r3")
    ap.add_argument("--ledger", default=None, help="global ledger path for BG6 publication")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--dry-run", action="store_true",
                    help="stop after the preflight pin (no metrics computed)")
    args = ap.parse_args()

    exec_root = Path(args.exec_root)
    sys.path.insert(0, str(exec_root))
    from research.adapter_v10.m01_plugin import M01Plugin  # noqa: E402
    from research.adapter_v10.runner import run_full_stress_matrix  # noqa: E402
    from research.adapter_v10.publish import publish_trial, trial_denominator  # noqa: E402
    from research.hyp_a8_m01 import (  # noqa: E402
        SCORED_WINDOW_START_UTC, SCORED_WINDOW_END_UTC, prewindow_sigma_table,
        _window_bounds_ns,
    )

    import yaml  # noqa: E402

    cfg = yaml.safe_load((exec_root / "config/research_scan_top20.yaml").read_text())
    symbols = list(cfg["market"]["symbols"])

    start_ns, end_ns = _window_bounds_ns(SCORED_WINDOW_START_UTC, SCORED_WINDOW_END_UTC)
    pre_start_ns = start_ns - 30 * 86400 * 10**9
    bars = dedupe_bars(exec_root / args.catalog, symbols, pre_start_ns, end_ns)

    spec = ARM_SPECS[args.arm]
    sigma_table = None
    sigma_map = None
    if spec["neighbour_mode"] == "prewindow_dispersion":
        sigma_table = prewindow_sigma_table(bars, prewindow_end_ns=start_ns)
        sigma_map = sigma_table["sigma_i"]

    preflight = {
        "artifact": "v10r_r3_cell_preflight",
        "arm": args.arm,
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "exec_root": str(exec_root),
        "exec_head": __import__("subprocess").run(
            ["git", "-C", str(exec_root), "rev-parse", "HEAD"],
            capture_output=True, text=True).stdout.strip(),
        "window_pins": {"start": SCORED_WINDOW_START_UTC, "end": SCORED_WINDOW_END_UTC},
        "universe": symbols,
        "bars_per_symbol": {s: len(b) for s, b in sorted(bars.items())},
        "bars_series_sha256": series_digest(bars),
        "dedupe_rule": "lexically-last parquet part wins per close stamp "
        "(research.panel._read_bars rule); strict rejection unapplicable for "
        "inherited BTC/ETH overlap; resolved values digit-exact vs live fapi "
        "(host3_full_window_8field_report.json)",
        "prewindow_sigma_sha256": None if sigma_table is None else sigma_table["sha256"],
        "prewindow_sigma_i": None if sigma_table is None else sigma_table["sigma_i"],
    }
    out_dir = exec_root / args.out_root / args.arm
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "preflight.json").write_text(json.dumps(preflight, indent=1))
    print("PREFLIGHT bars:", preflight["bars_per_symbol"])
    print("PREFLIGHT series_sha256:", preflight["bars_series_sha256"])
    if args.dry_run:
        print("DRY-RUN: stopping after preflight (no metrics computed)")
        return 0

    plugin = M01Plugin(
        bars_by_symbol=bars,
        window_start_iso=SCORED_WINDOW_START_UTC,
        window_end_iso=SCORED_WINDOW_END_UTC,
        control_mode=spec["control_mode"],
        neighbour_mode=spec["neighbour_mode"],
        prewindow_sigma=sigma_map,
        settle_points_by_symbol=load_settlements(exec_root / args.funding_root, symbols),
    )
    matrix = run_full_stress_matrix(plugin, out_root=str(out_dir / "matrix"))
    (out_dir / "matrix_summary.json").write_text(json.dumps(
        {k: v for k, v in matrix.items() if k != "runs"}, indent=1, default=str))
    baseline_name = next(n for n in matrix["runs"] if "baseline" in n.lower())
    baseline_run = matrix["runs"][baseline_name]
    metrics = baseline_run.get("portfolio_metrics") or {}
    scored_metrics = {
        "score_valid": bool(baseline_run.get("scored", False)) or bool(metrics),
        "net_return_sum": metrics.get("net_return_sum"),
        "expectancy_per_day": metrics.get("expectancy_per_day"),
        "max_drawdown": metrics.get("max_drawdown"),
    }
    print("BASELINE metrics keys:", sorted(metrics.keys())[:12])
    print("SCORED metrics:", scored_metrics)

    if not args.publish:
        print("PUBLISH: skipped (--publish not set); cell artifacts written only")
        return 0
    result = publish_trial(
        identity=plugin.identity(),
        stress_signature=plugin.baseline_stress().__dict__,
        scored_metrics=scored_metrics,
        payload_digests=baseline_run.get("hashes", {}),
        experiment_digest=matrix["matrix_digest"],
        matrix_id=f"v10r-r3-{args.arm}",
        ledger_path=args.ledger,
    )
    (out_dir / "publish_record.json").write_text(json.dumps(result, indent=1, default=str))
    print("PUBLISH:", json.dumps({k: result.get(k) for k in
                                  ("published", "stage", "reasons", "denominator_after")}, default=str))
    print("DENOMINATOR NOW:", trial_denominator(args.ledger))
    return 0 if result.get("published") or result.get("stage") == "IDEMPOTENT_REPLAY_SKIPPED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
