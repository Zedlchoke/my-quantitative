"""Bounded V1R1 OFR acquisition. Values from .env are never printed.

Run as ``python -m research.control.free_data_frontier_v1r1_run.run_ofr``.
"""

from __future__ import annotations

import json
from pathlib import Path

import requests

from research.free_data_frontier.env import check_presence, load_secret
from research.free_data_frontier.http import DiskGuard
from research.free_data_frontier.manifest import write_manifest, verify_manifest
from research.free_data_frontier.sources.base import SourceContext
from research.free_data_frontier.sources.ofr import run


REPO = Path(__file__).resolve().parents[3]
CONTROL = REPO / "research/control/free_data_frontier_v1r1_run"
RAW = Path("/Users/hoangminhlong/.my-quantitative-data/free-data-frontier-v1r1/raw")


def main() -> int:
    context = SourceContext(
        raw_root=RAW,
        control_dir=CONTROL,
        session=requests.Session(),
        limiters={},
        disk_guard=DiskGuard(),
        presence=check_presence(["SEC_CONTACT_NAME", "SEC_CONTACT_EMAIL", "EIA_API_KEY"]),
        secret_loader=load_secret,
    )
    state = run(context)
    summary = state.summarize()
    manifest_dir = CONTROL / "manifests"
    manifest_dir.mkdir(parents=True, exist_ok=True)
    records = [record for record in state.records if record.get("raw_path")]
    manifest_path = manifest_dir / "ofr_stfm_v1r1_manifest.json"
    summary["manifest"] = write_manifest(manifest_path, records)
    verification = verify_manifest(manifest_path)
    summary["verification"] = {k: v for k, v in verification.items() if k != "rows"}
    output = CONTROL / "ofr_v1r1_summary.json"
    output.write_text(json.dumps(summary, sort_keys=True, indent=2) + "\n")
    print(json.dumps({
        "status": summary["status"],
        "objects": summary["objects"],
        "verification": summary["verification"],
    }, indent=2))
    return 0 if summary["status"] == "PASS_SAMPLE" and verification["verdict"] == "ALL_MATCH" else 2


if __name__ == "__main__":
    raise SystemExit(main())
