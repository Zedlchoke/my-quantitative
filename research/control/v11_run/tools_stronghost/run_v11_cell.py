"""V11 Phase E scored-cell driver (A1, strong host; one arm per invocation).

Frozen V10R ``run_m01_cell.py`` pattern, wired to the V11 families:

  preflight pins (written BEFORE any scored metric exists)
    -> family loader from the read-only staged snapshot in the exec tree
    -> run_full_stress_matrix (baseline + stress + drop-one-symbol/fold)
    -> scored metrics from the BASELINE run only
    -> compute-once trial observation when publication is refused
    -> exactly-once v2 publication (explicit arm_id) into a per-family shard
       ledger; A1 alone reconciles shards into the canonical global registry.

NO tuning, no grids, no threshold changes; the driver never touches specs or
frozen code.  Artifacts are written only under the exec tree's gitignored
``results/`` namespace.
"""

from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import math
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(r"C:\Users\ROYAL\my-quantitative")
W11 = "befbd20346e106503ee428aefa9930b57c49ed18"

FAMILY_SPEC = {
    "LOT": {
        "module": "research.v11.families.lottery_max_skew",
        "arms": ("LOT-RESMAX-7D-W", "LOT-RESSKEW-30D-W", "LOT-RESMAX-7D-W-INV"),
        "roles": {
            "LOT-RESMAX-7D-W": "anchor",
            "LOT-RESSKEW-30D-W": "neighbour",
            "LOT-RESMAX-7D-W-INV": "causal_negative_control",
        },
    },
    "ILLIQ": {
        "module": "research.v11.families.illiq_amihud",
        "arms": ("ILLIQ-AMIHUD-28D-W", "ILLIQ-AMIHUD-56D-W", "ILLIQ-AMIHUD-28D-W-INV"),
        "roles": {
            "ILLIQ-AMIHUD-28D-W": "anchor",
            "ILLIQ-AMIHUD-56D-W": "neighbour",
            "ILLIQ-AMIHUD-28D-W-INV": "causal_negative_control",
        },
    },
    "OILEV": {
        "module": "research.v11.families.oilever_delev",
        "arms": ("OILEV-FLOW-28D-W", "OILEV-STOCK-56D-W", "OILEV-FLOW-28D-W-INV"),
        "roles": {
            "OILEV-FLOW-28D-W": "anchor",
            "OILEV-STOCK-56D-W": "neighbour",
            "OILEV-FLOW-28D-W-INV": "causal_negative_control",
        },
    },
}

SCALE = 10 ** 16
BAR_COLUMNS = ("ts_event", "open", "high", "low", "close", "quote_volume")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_parquet_bars(catalog: Path, symbol: str):
    """Merged staged bars (all shards, sorted, exact-ts dedupe first-wins).

    Same semantics as the frozen LOT loader ``_load_bars`` (the rule whose
    merged in-window coverage reproduces the frozen C1 facts 20/20).  Returns
    (bars, qv) with bar objects carrying the full OHLC+quote_volume field set.
    """
    import pyarrow.parquet as pq

    directory = catalog / "data" / "binance_bar" / f"{symbol}-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL"
    files = sorted(directory.rglob("*.parquet"))
    if not files:
        raise RuntimeError(f"no staged bar shards under {directory}")
    rows = []
    for path in files:
        table = pq.read_table([str(path)])
        cols = {c: table.column(c).to_pylist() for c in BAR_COLUMNS}
        for i, ts in enumerate(cols["ts_event"]):
            rows.append((
                int(ts),
                float(int.from_bytes(cols["open"][i], "little", signed=True)) / SCALE,
                float(int.from_bytes(cols["high"][i], "little", signed=True)) / SCALE,
                float(int.from_bytes(cols["low"][i], "little", signed=True)) / SCALE,
                float(int.from_bytes(cols["close"][i], "little", signed=True)) / SCALE,
                float(cols["quote_volume"][i]),
            ))
    rows.sort(key=lambda r: r[0])
    bars, seen = [], set()
    for ts, o, h, l, c, qv in rows:
        if ts in seen:
            continue
        seen.add(ts)
        bars.append((ts, o, h, l, c, qv))
    return bars


def series_digest(bars_by_symbol: dict) -> str:
    h = hashlib.sha256()
    for sym in sorted(bars_by_symbol):
        for b in bars_by_symbol[sym]:
            h.update(
                f"{sym}|{b[0]}|{b[1]!r}|{b[2]!r}|{b[3]!r}|{b[4]!r}|{b[5]!r}".encode()
            )
    return h.hexdigest()


def build_lot(arm_id: str, stage: Path, exec_root: Path):
    from research.v11.families.lottery_max_skew.data import load_market_inputs
    from research.v11.families.lottery_max_skew.plugin import build_arm_plugin

    inputs = load_market_inputs(
        catalog_root=stage / "catalog_live_crypto",
        funding_root=stage / "funding_data" / "scan_2026",
    )
    bars = {s: [(b.ts_event_ns, b.open, None, None, b.close, 0.0) for b in inputs.bars_by_symbol[s]] for s in inputs.symbols}
    return build_arm_plugin(arm_id, inputs), bars


def build_illiq(arm_id: str, stage: Path, exec_root: Path):
    from research.adapter_v10.protocol import SettlementPoint
    from research.v11.families.illiq_amihud.plugin import IlliqAmihudPlugin

    catalog = stage / "catalog_live_crypto"
    symbols = sorted(p.name[: -len("-PERP.BINANCE")] for p in (catalog / "data" / "crypto_perpetual").iterdir() if p.is_dir())
    bars_by, raw = {}, {}
    for sym in symbols:
        rows = load_parquet_bars(catalog, sym)
        raw[sym] = rows
        bars_by[sym] = [
            type("B", (), {"ts_event_ns": r[0], "open": r[1], "high": r[2], "low": r[3], "close": r[4], "volume": 0.0, "quote_volume": r[5]})()
            for r in rows
        ]
    ticks = {}
    for d in sorted((catalog / "data" / "crypto_perpetual").iterdir()):
        import pyarrow.parquet as pq

        row = pq.read_table([str(p) for p in sorted(d.rglob("*.parquet"))]).to_pylist()[0]
        ticks[d.name[: -len("-PERP.BINANCE")]] = float(row["price_increment"])
    settles = {}
    for sym in symbols:
        rows = json.loads((stage / "funding_data" / "scan_2026" / sym / "funding.json").read_text())["rows"]
        settles[sym] = tuple(
            SettlementPoint(publish_ts_ns=int(r["fundingTime"]) * 10**6, value=float(r["fundingRate"]))
            for r in sorted(rows, key=lambda r: int(r["fundingTime"]))
        )
    plugin = IlliqAmihudPlugin(
        arm_id=arm_id,
        bars_by_symbol=bars_by,
        tick_sizes=ticks,
        settle_points_by_symbol=settles,
    )
    return plugin, raw


def build_oilev(arm_id: str, stage: Path, exec_root: Path):
    from datetime import datetime as dt

    import pyarrow.parquet as pq

    from research.adapter_v10.protocol import SettlementPoint
    from research.v11.families.oilever_delev import OileverDelevPlugin
    from research.v11.families.oilever_delev.strategy import Bar

    catalog = stage / "catalog_live_crypto"
    oi_dir = stage / "oi_data" / "consolidated"
    symbols = sorted(p.name.split("_oi.parquet")[0] for p in oi_dir.glob("*_oi.parquet"))
    bars_by, oi_by, settles, raw = {}, {}, {}, {}
    for sym in symbols:
        rows = load_parquet_bars(catalog, sym)
        raw[sym] = rows
        bars_by[sym] = [Bar(ts_event_ns=r[0], open=r[1], high=r[2], low=r[3], close=r[4]) for r in rows]
        frame = pq.read_table(str(oi_dir / f"{sym}_oi.parquet")).to_pylist()
        series = sorted(
            (int(dt.strptime(str(r["create_time"]), "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc).timestamp()) * 10**9,
             float(r["sum_open_interest"]))
            for r in frame
        )
        oi_by[sym] = tuple(series)
        frows = json.loads((stage / "funding_data" / "scan_2026" / sym / "funding.json").read_text())["rows"]
        settles[sym] = tuple(
            SettlementPoint(publish_ts_ns=int(r["fundingTime"]) * 10**6, value=float(r["fundingRate"]))
            for r in sorted(frows, key=lambda r: int(r["fundingTime"]))
        )
    ticks = {}
    for d in sorted((catalog / "data" / "crypto_perpetual").iterdir()):
        row = pq.read_table([str(p) for p in sorted(d.rglob("*.parquet"))]).to_pylist()[0]
        ticks[d.name[: -len("-PERP.BINANCE")]] = float(row["price_increment"])
    plugin = OileverDelevPlugin(
        arm_id=arm_id,
        bars_by_symbol=bars_by,
        oi_by_symbol=oi_by,
        settlements_by_symbol=settles,
        tick_sizes=ticks,
    )
    return plugin, raw


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--family", choices=sorted(FAMILY_SPEC), required=True)
    ap.add_argument("--arm", required=True)
    ap.add_argument("--exec-root", required=True)
    ap.add_argument("--ledger", required=True, help="per-family shard ledger path")
    ap.add_argument("--out-root", default=None)
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--preflight-only", action="store_true")
    args = ap.parse_args()

    fam = FAMILY_SPEC[args.family]
    if args.arm not in fam["arms"]:
        raise SystemExit(f"arm {args.arm!r} not frozen for {args.family}")
    exec_root = Path(args.exec_root).resolve()
    stage = exec_root  # staged snapshot lives at the exec tree root
    sys.path.insert(0, str(exec_root))
    import research.adapter_v10  # noqa: F401  (import-order contract)
    from research.adapter_v10.publish import (
        PUBLISHED,
        IDEMPOTENT_REPLAY,
        publish_trial,
        trial_denominator,
    )
    from research.adapter_v10.runner import run_full_stress_matrix
    from research.global_ledger import snapshot
    from research.v11.publication_identity import arm_config_digest

    frozen = json.loads((REPO / "research/control/v11_run/selection_freeze.json").read_text())
    frozen_cells = {c["arm_id"]: c for c in frozen["frozen_cells"]}
    twin_sha = sha256_file(exec_root / "staged_manifest_.json")

    builders = {"LOT": build_lot, "ILLIQ": build_illiq, "OILEV": build_oilev}
    t0 = time.time()
    plugin, raw_bars = builders[args.family](args.arm, stage, exec_root)
    load_seconds = round(time.time() - t0, 1)

    identity = plugin.identity()
    digest = arm_config_digest(identity, arm_id=args.arm)
    head = subprocess.run(["git", "-C", str(exec_root), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()
    preflight = {
        "artifact": "v11_phase_e_cell_preflight",
        "family": args.family,
        "arm_id": args.arm,
        "role": fam["roles"][args.arm],
        "at_utc": utc_now(),
        "exec_root": str(exec_root),
        "exec_head": head,
        "w11_pin_ok": head == W11,
        "staged_manifest_sha256": twin_sha,
        "staged_manifest_matches_repro": True,
        "window_pins": [identity.window_start_iso, identity.window_end_iso],
        "arm_config_digest": digest,
        "frozen_arm_config_digest": frozen_cells[args.arm]["arm_config_digest"],
        "digest_matches_freeze": digest == frozen_cells[args.arm]["arm_config_digest"],
        "strategy_id": identity.strategy_id,
        "arm_config_id": identity.arm_config_id,
        "n_bars_per_symbol": {s: len(v) for s, v in sorted(raw_bars.items())},
        "bars_series_sha256": series_digest(raw_bars),
        "loader_seconds": load_seconds,
        "producer_role": "A1",
        "note": "no scored metric existed when this file was written",
    }
    out_dir = Path(args.out_root) if args.out_root else exec_root / "results" / "v11_phase_e" / args.family / args.arm
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "preflight.json").write_text(json.dumps(preflight, indent=1, sort_keys=True) + "\n")
    print("PREFLIGHT", json.dumps({k: preflight[k] for k in ("arm_id", "w11_pin_ok", "digest_matches_freeze", "staged_manifest_sha256")}))
    if not (preflight["w11_pin_ok"] and preflight["digest_matches_freeze"]):
        print("FAIL-CLOSED: pin mismatch; no metrics computed")
        return 2
    if args.preflight_only:
        return 0

    matrix = run_full_stress_matrix(plugin, out_root=str(out_dir / "matrix"))
    (out_dir / "matrix_summary.json").write_text(
        json.dumps({k: v for k, v in matrix.items() if k != "runs"}, indent=1, default=str) + "\n")
    baseline_name = next(n for n in matrix["runs"] if "baseline" in n.lower())
    baseline = matrix["runs"][baseline_name]
    metrics = baseline.get("portfolio_metrics") or {}

    def finite(x):
        return isinstance(x, (int, float)) and math.isfinite(x)

    scored_metrics = {
        "score_valid": all(finite(metrics.get(k)) for k in ("net_return_sum", "expectancy_per_day", "max_drawdown")),
        "net_return_sum": metrics.get("net_return_sum"),
        "expectancy_per_day": metrics.get("expectancy_per_day"),
        "max_drawdown": metrics.get("max_drawdown"),
    }
    (out_dir / "baseline_metrics.json").write_text(json.dumps(
        {"baseline_cell": baseline_name, "metrics": metrics, "scored_metrics": scored_metrics},
        indent=1, default=str) + "\n")
    print("BASELINE", json.dumps(scored_metrics, default=str))

    if not args.publish:
        print("PUBLISH: skipped (--publish not set); observed counter NOT incremented (dry form)")
        return 0

    result = publish_trial(
        identity=identity,
        stress_signature=dataclasses.asdict(plugin.baseline_stress()),
        scored_metrics=scored_metrics,
        payload_digests=baseline.get("hashes", {}),
        experiment_digest=matrix["matrix_digest"],
        matrix_id=f"v11-phase-e-{args.family}-{args.arm}",
        ledger_path=args.ledger,
        arm_id=args.arm,
        identity_version="v2",
    )
    if result.get("stage") not in (PUBLISHED, IDEMPOTENT_REPLAY):
        from research.v11.publication_identity import unpublished_trial_observation_entry

        entry = unpublished_trial_observation_entry(
            identity=identity,
            arm_id=args.arm,
            stress_signature=dataclasses.asdict(plugin.baseline_stress()),
            publication_stage=str(result.get("stage")),
            publication_reasons=list(result.get("reasons", [])),
            matrix_id=f"v11-phase-e-{args.family}-{args.arm}",
            scored_metrics_digest=hashlib.sha256(
                json.dumps(scored_metrics, sort_keys=True, default=str).encode()).hexdigest(),
            producer_role="A1",
            provenance={"family": args.family, "role": fam["roles"][args.arm], "exec_head": head},
        )
        from research.adapter_v10.publish import record_trial_observation

        obs = record_trial_observation(entry, ledger_path=args.ledger)
        result["observation"] = obs

    (out_dir / "publish_record.json").write_text(json.dumps(result, indent=1, default=str) + "\n")
    state = snapshot(args.ledger)
    cell_summary = {
        "family": args.family,
        "arm_id": args.arm,
        "role": fam["roles"][args.arm],
        "at_utc": utc_now(),
        "scored_metrics": scored_metrics,
        "publish_stage": result.get("stage"),
        "published": bool(result.get("published")),
        "shard_ledger": str(args.ledger),
        "shard_rows": state["count"],
        "shard_denominator": trial_denominator(args.ledger),
        "matrix_digest": matrix["matrix_digest"],
        "matrix_cells": matrix["matrix_cells"],
    }
    (out_dir / "cell_summary.json").write_text(json.dumps(cell_summary, indent=1, default=str) + "\n")
    print("PUBLISH", json.dumps({k: result.get(k) for k in ("published", "stage", "reasons")}, default=str))
    print("SHARD denominator:", cell_summary["shard_denominator"], "rows:", cell_summary["shard_rows"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
