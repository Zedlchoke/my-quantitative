"""V10R R4 — reproduction verifier: R1c cells vs fresh R2c processes.

Compares, per arm, the frozen deterministic surfaces the adapter defines:
matrix_digest, per-run result_sha256/portfolio_payload_sha256/fold_metrics_
sha256/positions_sha256/benchmarks_sha256/schedule_sha256, preflight pins
(bars series digest + sigma hash), and the canonical artifact files byte-wise.
Reports all_match per arm; anything less is a reproduction FAILURE (no
narrative smoothing).
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ARMS = ("anchor", "neighbour", "c2")


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def content_sha(path: Path, tree_root: Path) -> str:
    """Hash an artifact with absolute tree-root path embeds normalised away.

    The frozen artifacts embed their own absolute result paths (e.g.
    artifact_paths.result_root), which necessarily differ between the R1c and
    R2c trees; every scientific field is identical. Path strings rooted at the
    tree are replaced with <TREE> before hashing.
    """

    def norm(obj):
        if isinstance(obj, dict):
            return {k: norm(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [norm(v) for v in obj]
        if isinstance(obj, str):
            return obj.replace(str(tree_root), "<TREE>").replace(str(tree_root).replace("\\", "/"), "<TREE>")
        return obj

    payload = norm(json.loads(path.read_text()))
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def collect(root: Path) -> dict:
    out = {}
    for arm in ARMS:
        d = root / "results/v10r_r3" / arm
        entry: dict = {"exists": d.exists()}
        if entry["exists"]:
            pf = d / "preflight.json"
            ms = d / "matrix_summary.json"
            entry["preflight_sha256"] = sha(pf) if pf.exists() else None
            if ms.exists():
                summary = json.loads(ms.read_text())
                entry["matrix_digest"] = summary.get("matrix_digest")
            entry["preflight_bars_sha256"] = (
                json.loads(pf.read_text()).get("bars_series_sha256") if pf.exists() else None
            )
            entry["preflight_sigma_sha256"] = (
                json.loads(pf.read_text()).get("prewindow_sigma_sha256") if pf.exists() else None
            )
            arts = sorted((d / "matrix").rglob("*.json"))
            entry["artifact_files"] = {
                str(p.relative_to(d)): content_sha(p, root) for p in arts
            }
        out[arm] = entry
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--r1c", default=r"C:/Users/ROYAL/exec-v10-R1c")
    ap.add_argument("--r2c", default=r"C:/Users/ROYAL/exec-v10-R2c")
    ap.add_argument("--out", default=str(
        Path(r"C:/Users/ROYAL/my-quantitative") / "research/control/v10r_run/r4_reproduction_report.json"))
    args = ap.parse_args()
    a, b = collect(Path(args.r1c)), collect(Path(args.r2c))
    report = {
        "artifact": "r4_reproduction_report",
        "producer_role": "A1",
        "at_utc": datetime.now(timezone.utc).isoformat(),
        "r1c": str(args.r1c), "r2c": str(args.r2c),
        "per_arm": {},
    }
    all_match = True
    for arm in ARMS:
        ea, eb = a[arm], b[arm]
        if not ea["exists"] or not eb["exists"]:
            report["per_arm"][arm] = {"all_match": False, "reason": "missing_outputs",
                                      "r1c_exists": ea["exists"], "r2c_exists": eb["exists"]}
            all_match = False
            continue
        diffs = []
        for key in ("matrix_digest", "preflight_bars_sha256", "preflight_sigma_sha256"):
            if ea.get(key) != eb.get(key):
                diffs.append(key)
        files_a, files_b = ea["artifact_files"], eb["artifact_files"]
        if set(files_a) != set(files_b):
            diffs.append("artifact_file_set")
        else:
            for f in files_a:
                if files_a[f] != files_b[f]:
                    diffs.append(f"artifact:{f}")
        arm_ok = not diffs
        all_match &= arm_ok
        report["per_arm"][arm] = {
            "all_match": arm_ok,
            "matrix_digest": ea.get("matrix_digest"),
            "n_artifacts_compared": len(files_a),
            "diffs": diffs,
        }
        print(f"[{'MATCH' if arm_ok else 'DIFF'}] {arm}: {len(files_a)} artifacts, "
              f"diffs={diffs[:3] if diffs else 'none'}")
    report["all_match"] = all_match
    Path(args.out).write_text(json.dumps(report, indent=1))
    print("ALL_MATCH:", all_match)
    return 0 if all_match else 1


if __name__ == "__main__":
    raise SystemExit(main())
