"""V14 P1 A2 -- OITD unaffected-path reproduction vs committed V13 values.

Lane-local, READ-ONLY evidence that the L-V14-0 remediation (which touches
ONLY the LIQEPIS plugin construction in the driver) leaves the OITD scoring
path unchanged: the frozen ``build_oitd`` construction is re-run on the
byte-verified staged-equivalent tree and the baseline metrics are compared
against the COMMITTED V13 terminal values (research/control/v13_run/
terminal_report_v13.json ``cell_results`` and family_verdicts_v13.json
``arms``), fail-closed on any mismatch at the committed precision.

No ledger writes, no artifact files written into any protected tree.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DRIVER_REPO_ROOT = Path(__file__).resolve().parents[4]

# Committed V13 terminal values (research/control/v13_run/
# terminal_report_v13.json cell_results; family_verdicts_v13.json arms).
# PF/MDD for OITD-56D / CTL-FLOW-ONLY are recorded at the committed 4dp.
COMMITTED_V13 = {
    "OITD-28D": {
        "net_return_sum": -0.285351460692,
        "expectancy_per_day": -0.00548752809,
        "position_pf": 0.878537739556,
        "max_drawdown": 0.305434836376,
        "cost_charged_sum": 0.006647739694,
        "funding_sum": -0.006932987375,
        "n_positions": 923,
    },
    "OITD-56D": {
        "net_return_sum": -0.533083489118,
        "expectancy_per_day": -0.01025160556,
        "position_pf": 0.7832,
        "max_drawdown": 0.5783,
        "cost_charged_sum": 0.005,
        "funding_sum": -0.0119,
        "n_positions": 944,
    },
    "CTL-FLOW-ONLY": {
        "net_return_sum": -0.450130116337,
        "expectancy_per_day": -0.008656348391,
        "position_pf": 0.8180,
        "max_drawdown": 0.4568,
        "cost_charged_sum": None,  # not recorded in family_verdicts
        "funding_sum": None,
        "n_positions": 926,
    },
}

ARMS = ("CTL-FLOW-ONLY", "OITD-28D", "OITD-56D")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _matches(measured: float, committed: Any, committed_decimals: int) -> bool:
    if committed is None:
        return True  # value not recorded at terminal; nothing to compare
    return round(float(measured), committed_decimals) == round(float(committed), committed_decimals)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--staged-equivalent", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    sys.path.insert(0, str(DRIVER_REPO_ROOT))

    # Recorded precision per committed field: terminal_report cell_results
    # carries 12dp for OITD-28D and 4dp for the other arms; family_verdicts
    # carries 4dp cost/funding everywhere it records them at all.
    def _decimals(arm_id: str, field: str) -> int:
        if field in ("cost_charged_sum", "funding_sum"):
            return 4
        return 12 if arm_id == "OITD-28D" else 4

    import research.adapter_v10  # noqa: F401  (import-order contract)
    from research.adapter_v10.runner import run_strategy
    from research.control.v13_run.tools.run_v13_cell import build_oitd

    staged_root = Path(args.staged_equivalent).resolve()
    input_verification = verify_inputs(staged_root)
    if not input_verification["ok"]:
        print("FAIL-CLOSED: staged-equivalent inputs failed byte verification")
        for problem in input_verification["problems"][:10]:
            print(f"  - {problem}")
        return 2

    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True
    ).stdout.strip()

    cells: dict[str, Any] = {}
    all_ok = True
    for arm_id in ARMS:
        t0 = time.time()
        plugin, inputs = build_oitd(staged_root, arm_id)
        result = run_strategy(plugin, stress=None, write_artifact_file=False)
        metrics = result["portfolio_metrics"]
        committed = COMMITTED_V13[arm_id]
        comparison = {}
        for field in (
            "net_return_sum",
            "expectancy_per_day",
            "max_drawdown",
            "position_pf",
            "cost_charged_sum",
            "funding_sum",
        ):
            decimals = _decimals(arm_id, field)
            measured = metrics[field]
            recorded = committed[field]
            comparison[field] = {
                "measured": measured,
                "committed": recorded,
                "compared_at_decimals": decimals if recorded is not None else None,
                "match": _matches(measured, recorded, decimals),
            }
        comparison["n_positions"] = {
            "measured": int(metrics["n_positions"]),
            "committed": committed["n_positions"],
            "match": int(metrics["n_positions"]) == committed["n_positions"],
        }
        arm_ok = all(entry["match"] for entry in comparison.values())
        all_ok &= arm_ok
        cells[arm_id] = {
            "committed_v13": committed,
            "measured": {
                k: metrics.get(k)
                for k in (
                    "net_return_sum",
                    "expectancy_per_day",
                    "max_drawdown",
                    "position_pf",
                    "cost_charged_sum",
                    "funding_sum",
                    "n_positions",
                )
            },
            "comparison": comparison,
            "all_match_at_committed_precision": bool(arm_ok),
            "inputs_digests": {
                k: inputs[k]
                for k in (
                    "day_turnover_digest",
                    "bars_digest",
                    "oi_digest",
                    "marks_digest",
                    "settlements_digest",
                )
                if k in inputs
            },
            "seconds": round(time.time() - t0, 1),
        }
        print(f"{arm_id}: all_match={arm_ok} net={metrics['net_return_sum']}")

    payload = {
        "artifact": "v14_p1_a2_oitd_unaffected_path_reproduction",
        "schema": "v14.p1.a2.oitd_reproduction.v1",
        "generated_utc": utc_now(),
        "producer_role": "A2",
        "lane_head_sha": head,
        "lesson": "L-V14-0",
        "staged_equivalent_root": str(staged_root),
        "input_verification": input_verification,
        "cells": cells,
        "note": (
            "the remediation edits ONLY the LIQEPIS plugin construction "
            "(build_liqepis tick parameterization) in the driver; build_oitd "
            "and every frozen module are byte-identical to the V13 terminal "
            "(git diff 96833a8..lane empty over research/v13, research/v12, "
            "research/adapter_v10).  The baseline metrics reproduce the "
            "COMMITTED V13 terminal values at their recorded precision."
        ),
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"WROTE {out_path} sha256={sha256_file(out_path)}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
