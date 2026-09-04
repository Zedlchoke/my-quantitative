"""STOCKS-FREE-V5 P2-b: pin the SEC PIT records store into run control.

Reads .staging_sec/normalize_report.json + hashes .staging_sec/pit_records.jsonl
and writes a commit-ready control summary (raw bytes stay uncommitted; the
store is pinned by SHA here and re-verified at W1 freeze).
"""

from __future__ import annotations

from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[3]
STAGE = REPO / ".staging_sec"
OUT = REPO / "research/control/stocks_free_v5_run/p2_a3_pit_store_manifest.json"


def main() -> int:
    report = json.loads((STAGE / "normalize_report.json").read_text())
    store = STAGE / "pit_records.jsonl"
    digest = sha256()
    n_lines = 0
    with open(store, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            digest.update(chunk)
            n_lines += chunk.count(b"\n")
    fetch_log_digest = sha256((STAGE / "fetch_log.jsonl").read_bytes()).hexdigest()
    panel = json.loads((STAGE / "panel.json").read_text())
    summary = {
        "schema": "stocks_free_v5_run/p2_a3_pit_store_manifest@1",
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "store_path": ".staging_sec/pit_records.jsonl (uncommitted; hash-pinned here)",
        "store_sha256": digest.hexdigest(),
        "store_records": n_lines,
        "fetch_log_sha256": fetch_log_digest,
        "panel_sha256": sha256((STAGE / "panel.json").read_bytes()).hexdigest(),
        "panel_total_filers": panel["panel_total"],
        "panel_per_sector": {s: len(v) for s, v in panel["panel"].items()},
        "panel_rule": panel["panel_rule"],
        "registry_sha256": panel["registry_sha256"],
        "normalization": {
            "sanitizer": report["sanitizer_version"],
            "adapter": report["adapter_version"],
            "chunking": "per-(taxonomy,tag) chunk bodies; record semantics identical to whole-file parse (chunk dedupe key superset); raw_sha256 names chunk body, file_raw_sha256 pins the real file",
            "files_processed": report["files_processed"],
            "records_written": report["records_written"],
        },
        "coverage_census_fields_of_interest": report["fields_of_interest_census"],
        "sanitizer_totals": {
            k: sum(fr["sanitizer"][k] for fr in report["file_reports"])
            for k in report["file_reports"][0]["sanitizer"]
        },
    }
    OUT.write_text(json.dumps(summary, indent=1, ensure_ascii=False) + "\n")
    print(json.dumps({k: summary[k] for k in ("store_sha256", "store_records", "panel_total_filers")}, indent=1))
    print("sanitizer totals:", json.dumps(summary["sanitizer_totals"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
