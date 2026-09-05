"""V14 P1 A2 -- corrected LIQEPIS cost recompute + fill-identity proof.

Lane-local, READ-ONLY evidence generator for the append-only adjudication
``research/control/v14_run/p1_a2/LIQEPIS_cost_adjudication.json`` (L-V14-0).

What it does (per LIQEPIS arm, strictly serial, no ledger writes, no
artifact files written into any protected tree):

1. verifies every input file it reads byte-exactly against the committed
   staging authority ``research/audits/v12p/a3_staging_manifest.json``
   (the same 90-file authority the frozen equal-twin snapshot shipped;
   fail-closed before any compute);
2. loads the frozen LIQEPIS bars via the frozen family loader through the
   remediated driver builder ``build_liqepis`` inputs path, then runs the
   frozen baseline cell TWICE via the frozen generic runner:
   (a) UNIFORM-TICK plugin (the V13 defect parameterization,
       ``tick_sizes = 0.01`` for every symbol) -- its ``cost_charged_sum``
       is a strong checksum over the published V13 fill set: reproducing
       the published V13 value to the last digit proves the recomputed
       books/fills are IDENTICAL to the published run;
   (b) REAL-TICK plugin (the remediated parameterization: perp-metadata
       tick sizes) -- identical books/fills/positions, corrected cost;
3. emits a JSON evidence payload (per-cell corrected costs, published
   checksum comparison, positions-hash equality, input/output sha256).

Usage:
    .venv/bin/python research/control/v14_run/p1_a2/recompute_liqepis_cost.py \
        --staged-equivalent results/v14_p1_reproduction/staged_equivalent \
        --out results/v14_p1_reproduction/liqepis_cost_recompute.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DRIVER_REPO_ROOT = Path(__file__).resolve().parents[4]

# Published V13 values (execution-tree baseline_metrics.json, read before the
# exec tree was removed; corroborated at committed precision by
# research/control/v13_run/family_verdicts_v13.json -- cost 25.0252 / 15.8386
# / 25.0252, price_pnl -0.3065 / -0.2053 / +0.3065, funding 0.0, 600 positions).
PUBLISHED_V13 = {
    "LIQEPIS-28D": {
        "cost_charged_sum": 25.025172055575,
        "price_pnl_sum": -0.30648003269,
        "funding_sum": 0.0,
        "n_positions": 600,
        "n_days_with_records": 52,
    },
    "LIQEPIS-56D": {
        "cost_charged_sum": 15.838617381575,
        "price_pnl_sum": -0.2053,
        "funding_sum": 0.0,
        "n_positions": 600,
        "n_days_with_records": 52,
    },
    "LIQEPIS-SIGN-INV": {
        "cost_charged_sum": 25.025172055575,
        "price_pnl_sum": 0.30648003269,
        "funding_sum": 0.0,
        "n_positions": 600,
        "n_days_with_records": 52,
    },
}

ARMS = ("LIQEPIS-28D", "LIQEPIS-56D", "LIQEPIS-SIGN-INV")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def verify_inputs(staged_root: Path) -> dict[str, Any]:
    """90/90 sha256 of the staged-equivalent tree vs the committed authority."""
    authority_path = DRIVER_REPO_ROOT / (
        "research/audits/v12p/a3_staging_manifest.json"
    )
    authority = json.loads(authority_path.read_text(encoding="utf-8"))
    files = dict(authority["files"])
    problems: list[str] = []
    verified: dict[str, str] = {}
    for rel, meta in sorted(files.items()):
        path = staged_root / rel
        if not path.is_file():
            problems.append(f"missing: {rel}")
            continue
        actual = sha256_file(path)
        if actual != str(meta.get("sha256", "")):
            problems.append(f"sha256 mismatch: {rel}")
            continue
        verified[rel] = actual
    return {
        "authority": str(authority_path),
        "authority_sha256": sha256_file(authority_path),
        "expected_files": len(files),
        "verified_files": len(verified),
        "problems": problems,
        "ok": not problems and len(verified) == len(files),
        "file_sha256": verified,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--staged-equivalent",
        required=True,
        help="staged-equivalent root (labeled subtrees byte-verified vs a3)",
    )
    parser.add_argument("--out", required=True, help="evidence payload path")
    args = parser.parse_args()
    sys.path.insert(0, str(DRIVER_REPO_ROOT))

    import research.adapter_v10  # noqa: F401  (import-order contract)
    from research.adapter_v10.hashes import payload_sha256
    from research.adapter_v10.runner import run_strategy
    from research.v13.families.liqepis.audits import (
        load_fusion_series,
        tradeable_universe_symbols,
    )
    from research.v13.families.liqepis.plugin import LiqepisPlugin
    from research.v13.families.liqepis.strategy import (
        BENCHMARK_SYMBOL,
        DAY_NS,
        FIRST_STAMP_ISO,
        WINDOW_END_ISO,
        parse_iso_utc,
    )
    from research.v12.families.oilev_v2.audits import load_tick_sizes

    staged_root = Path(args.staged_equivalent).resolve()
    input_verification = verify_inputs(staged_root)
    if not input_verification["ok"]:
        print("FAIL-CLOSED: staged-equivalent inputs failed byte verification")
        for problem in input_verification["problems"][:10]:
            print(f"  - {problem}")
        return 2

    perp_root = staged_root / "crypto_perpetual_meta"
    bars_root = staged_root / "binance_bar_15m"
    universe = tradeable_universe_symbols()
    needed = sorted(set(universe) | {BENCHMARK_SYMBOL})
    first_stamp = parse_iso_utc(FIRST_STAMP_ISO)
    series = load_fusion_series(
        needed,
        bars_root=str(bars_root),
        start_ns=first_stamp - 56 * DAY_NS,
        end_ns=parse_iso_utc(WINDOW_END_ISO),
    )
    real_ticks = load_tick_sizes(needed, perp_root=str(perp_root))
    bars_by_symbol = {sym: s for sym, s in series.items() if sym in set(needed)}

    cells: dict[str, Any] = {}
    for arm_id in ARMS:
        t0 = time.time()
        published = PUBLISHED_V13[arm_id]
        runs: dict[str, Any] = {}
        for label, tick_sizes in (
            ("uniform_0p01", {sym: 0.01 for sym in needed}),
            ("real_perp_meta", dict(real_ticks)),
        ):
            plugin = LiqepisPlugin(
                arm_id=arm_id,
                bars_by_symbol=bars_by_symbol,
                tick_sizes=tick_sizes,
            )
            result = run_strategy(
                plugin, stress=None, write_artifact_file=False
            )
            metrics = result["portfolio_metrics"]
            # Cost-free position surface: every position field EXCEPT the
            # cost allocation, plus the cost-free daily-row surface. Two
            # parameterizations of the SAME fills must be identical here.
            cost_free_positions = payload_sha256(
                [
                    {
                        k: row[k]
                        for k in (
                            "symbol",
                            "fold_index",
                            "fold_label",
                            "entry_ns",
                            "exit_ns",
                            "signed_weight",
                            "entry_price",
                            "exit_price",
                            "price_pnl_per_unit",
                            "funding_cashflow_per_unit",
                        )
                    }
                    for row in sorted(
                        result["positions"],
                        key=lambda r: (r["entry_ns"], r["symbol"]),
                    )
                ]
            )
            cost_free_daily = payload_sha256(
                [
                    {
                        k: row[k]
                        for k in (
                            "decision_ns",
                            "price_pnl_per_unit",
                            "funding_cashflow_per_unit",
                            "gross_realised",
                        )
                    }
                    for row in sorted(
                        result["daily_returns"], key=lambda r: r["decision_ns"]
                    )
                ]
            )
            runs[label] = {
                "cost_model_default_tick_sizes": {
                    k: float(v)
                    for k, v in sorted(
                        plugin.cost_model().default_tick_sizes.items()
                    )
                },
                "cost_charged_sum": metrics["cost_charged_sum"],
                "price_pnl_sum": metrics["price_pnl_sum"],
                "funding_sum": metrics["funding_sum"],
                "n_positions": int(metrics["n_positions"]),
                "n_days_with_records": int(metrics["n_days_with_records"]),
                "net_return_sum": metrics["net_return_sum"],
                "expectancy_per_day": metrics["expectancy_per_day"],
                "max_drawdown": metrics["max_drawdown"],
                "position_pf": metrics["position_pf"],
                "positions_sha256": result["hashes"]["positions_sha256"],
                "cost_free_positions_sha256": cost_free_positions,
                "cost_free_daily_sha256": cost_free_daily,
                "per_stamp_cost_charged": [
                    row["cost_charged_per_unit"]
                    for row in sorted(
                        result["daily_returns"], key=lambda r: r["decision_ns"]
                    )
                ],
            }
        uniform = runs["uniform_0p01"]
        real = runs["real_perp_meta"]
        checksum_match = (
            round(uniform["cost_charged_sum"], 12)
            == round(published["cost_charged_sum"], 12)
        )
        price_match = (
            round(uniform["price_pnl_sum"], 12)
            == round(published["price_pnl_sum"], 12)
        )
        cells[arm_id] = {
            "published_v13": published,
            "uniform_0p01_run": uniform,
            "real_perp_meta_run": real,
            "fill_identity_proof": {
                "uniform_cost_matches_published_checksum": bool(checksum_match),
                "uniform_price_pnl_matches_published": bool(price_match),
                "uniform_n_positions_matches_published": bool(
                    uniform["n_positions"] == published["n_positions"]
                ),
                "cost_free_position_surface_equal_across_parameterizations": bool(
                    uniform["cost_free_positions_sha256"]
                    == real["cost_free_positions_sha256"]
                ),
                "cost_free_daily_surface_equal_across_parameterizations": bool(
                    uniform["cost_free_daily_sha256"] == real["cost_free_daily_sha256"]
                ),
                "funding_zero_both": bool(
                    uniform["funding_sum"] == 0.0 and real["funding_sum"] == 0.0
                ),
            },
            "corrected_cost_charged_sum": real["cost_charged_sum"],
            "published_over_corrected_ratio": (
                uniform["cost_charged_sum"] / real["cost_charged_sum"]
                if real["cost_charged_sum"]
                else None
            ),
            "seconds": round(time.time() - t0, 1),
        }
        print(
            f"{arm_id}: uniform={uniform['cost_charged_sum']} "
            f"(published {published['cost_charged_sum']}, "
            f"match={checksum_match}) corrected={real['cost_charged_sum']} "
            f"cost_free_surface_equal={uniform['cost_free_positions_sha256'] == real['cost_free_positions_sha256']}"
        )

    payload = {
        "artifact": "v14_p1_a2_liqepis_cost_recompute",
        "schema": "v14.p1.a2.cost_recompute.v1",
        "generated_utc": utc_now(),
        "producer_role": "A2",
        "lane_head_sha": (
            __import__("subprocess")
            .run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True)
            .stdout.strip()
        ),
        "lesson": "L-V14-0",
        "staged_equivalent_root": str(staged_root),
        "input_verification": input_verification,
        "perp_meta_ticks_used": {k: float(v) for k, v in sorted(real_ticks.items())},
        "cells": cells,
        "note": (
            "uniform-tick cost reproduces the published V13 cost_charged_sum "
            "exactly => the recomputed books/fills are identical to the "
            "published V13 run; the real-tick run differs ONLY through the "
            "cost term: the cost-free position surface (every position field "
            "except cost_allocated_per_unit) and the cost-free daily surface "
            "(price PnL / funding / gross) hash equal across the two "
            "parameterizations, while the full positions hash differs "
            "exactly through cost_allocated_per_unit."
        ),
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"WROTE {out_path} sha256={sha256_file(out_path)}")
    all_ok = all(
        cell["fill_identity_proof"]["uniform_cost_matches_published_checksum"]
        and cell["fill_identity_proof"][
            "cost_free_position_surface_equal_across_parameterizations"
        ]
        and cell["fill_identity_proof"][
            "cost_free_daily_surface_equal_across_parameterizations"
        ]
        for cell in cells.values()
    )
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
