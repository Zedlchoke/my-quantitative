#!/usr/bin/env python
"""PA0 substrate re-verify kill-test for RESEARCH-PLATFORM-V3.

Re-verifies, from disk (never from prior reports):
  1. ~/staging_backups/SHA256SUMS.txt 14/14 archives (backup side)
  2. ~/staging_backups/cleanup_2026-09-07/SHA256SUMS.txt (second manifest)
  3. Form-4 substrate family digest: substrate_manifest.json +
     .staging_sec_v13/form4_stream.jsonl at the frozen STOCKS-FREE-V13
     integration worktree (the S1 target-set substrate of plan section 7A.3)

Expected pins (recorded lineage, verified here by fresh hashing):
  - pre-F-1 vintage of substrate_manifest.json:  78c4fb1a5aceb8fe1fbd233f31
    93072bc6d8248ccf9c9524441c374333358742  (superseded append-only by F-1)
  - post-F-1 (current committed pin):  5d351623675f71a9950d0e290b1fafff899
    01265f18bf6c687660e96285ea26b
  - form4_stream.jsonl: 6ac2cd5bdd62566efe106b46de715030e9a8a940cb90f5a991d
    f5f05ba6742b2, 546039 rows (345150 XML doc pins unchanged)

A bulk re-hash (~2.9 GB) runs under the machine-wide heavy lock
(.runtime/heavy_worker.lock) with release in finally. Lock acquisition
failure = NOT_RUN_RESOURCE_CONFLICT; the script never kills foreign workers.

Exit codes: 0 = PASS, 2 = FAIL (any mismatch), 3 = NOT_RUN_RESOURCE_CONFLICT.
"""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import socket
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path("/Users/hoangminhlong/my-quantitative")
BACKUPS = Path.home() / "staging_backups"
V13 = ROOT / ".worktrees/stocks-free-v13/integration"
OUT = Path(__file__).resolve().parent / "gates"
LOCK = ROOT / ".runtime/heavy_worker.lock"

EXPECTED_SUBSTRATE_MANIFEST_POST_F1 = (
    "5d351623675f71a9950d0e290b1fafff89901265f18bf6c687660e96285ea26b"
)
EXPECTED_SUBSTRATE_MANIFEST_PRE_F1 = (
    "78c4fb1a5aceb8fe1fbd233f3193072bc6d8248ccf9c9524441c374333358742"
)
EXPECTED_STREAM = (
    "6ac2cd5bdd62566efe106b46de715030e9a8a940cb90f5a991df5f05ba6742b2"
)
EXPECTED_STREAM_ROWS = 546039


def sha256_file(path: Path, chunk: int = 1 << 20) -> str | None:
    try:
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            while True:
                b = fh.read(chunk)
                if not b:
                    break
                h.update(b)
        return h.hexdigest()
    except OSError:
        return None


def verify_sums(manifest: Path) -> dict:
    started = time.time()
    lines = [l for l in manifest.read_text().splitlines() if l.strip()]
    results = []
    ok = fail = missing = 0
    for line in lines:
        expected, name = line.split(None, 1) if "  " in line else (line[:64], line[66:])
        name = name.strip().lstrip("*")
        target = manifest.parent / name
        if not target.is_file():
            missing += 1
            results.append({"file": name, "status": "MISSING"})
            continue
        got = sha256_file(target)
        if got is None:
            missing += 1
            results.append({"file": name, "status": "UNREADABLE"})
        elif got == expected:
            ok += 1
            results.append({"file": name, "status": "OK"})
        else:
            fail += 1
            results.append({"file": name, "status": "DRIFT", "got": got})
    return {
        "manifest": str(manifest),
        "entries": len(lines),
        "ok": ok,
        "drift": fail,
        "missing": missing,
        "seconds": round(time.time() - started, 2),
        "files": results,
        "verdict": "PASS" if fail == 0 and missing == 0 and ok == len(lines) else "FAIL",
    }


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    lock_fh = open(LOCK, "a+")
    lock_state: str
    try:
        fcntl.flock(lock_fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        lock_state = "ACQUIRED"
    except OSError as exc:
        artifact = {
            "schema": "research_platform_v3_run/pa0_substrate_reverify@1",
            "verdict": "NOT_RUN_RESOURCE_CONFLICT",
            "lock_error": repr(exc),
            "measured_utc": datetime.now(timezone.utc).isoformat(),
        }
        (OUT / "V3-GA0_pa0_substrate_reverify_NOT_RUN.json").write_text(
            json.dumps(artifact, indent=2) + "\n"
        )
        print(json.dumps(artifact, indent=2))
        return 3

    started = time.time()
    try:
        main_sums = verify_sums(BACKUPS / "SHA256SUMS.txt")
        cleanup_sums = None
        cleanup_manifest = BACKUPS / "cleanup_2026-09-07/SHA256SUMS.txt"
        if cleanup_manifest.is_file():
            cleanup_sums = verify_sums(cleanup_manifest)

        substrate_manifest_path = (
            V13 / "research/control/stocks_free_v13_run/substrate_manifest.json"
        )
        stream_path = V13 / ".staging_sec_v13/form4_stream.jsonl"

        substrate_manifest_sha = (
            sha256_file(substrate_manifest_path)
            if substrate_manifest_path.is_file()
            else None
        )
        stream_sha = sha256_file(stream_path) if stream_path.is_file() else None

        stream_rows = None
        if stream_path.is_file():
            with open(stream_path, "rb") as fh:
                stream_rows = sum(1 for _ in fh)

        form4 = {
            "substrate_manifest_path": str(substrate_manifest_path),
            "substrate_manifest_exists": substrate_manifest_path.is_file(),
            "substrate_manifest_sha256": substrate_manifest_sha,
            "expected_post_f1": EXPECTED_SUBSTRATE_MANIFEST_POST_F1,
            "expected_pre_f1_superseded": EXPECTED_SUBSTRATE_MANIFEST_PRE_F1,
            "stream_path": str(stream_path),
            "stream_exists": stream_path.is_file(),
            "stream_sha256": stream_sha,
            "expected_stream": EXPECTED_STREAM,
            "stream_rows_measured": stream_rows,
            "expected_stream_rows": EXPECTED_STREAM_ROWS,
        }
        form4_match = (
            substrate_manifest_sha == EXPECTED_SUBSTRATE_MANIFEST_POST_F1
            and stream_sha == EXPECTED_STREAM
            and stream_rows == EXPECTED_STREAM_ROWS
        )
        form4["verdict"] = "PASS" if form4_match else "FAIL"

        overall = (
            "PASS"
            if main_sums["verdict"] == "PASS"
            and (cleanup_sums is None or cleanup_sums["verdict"] == "PASS")
            and form4["verdict"] == "PASS"
            else "FAIL"
        )
        artifact = {
            "schema": "research_platform_v3_run/pa0_substrate_reverify@1",
            "gate": "V3-GA0",
            "cycle": "RESEARCH-PLATFORM-V3",
            "measured_utc": datetime.now(timezone.utc).isoformat(),
            "host": socket.gethostname(),
            "method": "fresh re-hash from disk under machine-wide heavy lock; "
            "no value copied from prior reports",
            "heavy_lock": lock_state,
            "staging_backups_sums": main_sums,
            "cleanup_2026_09_07_sums": cleanup_sums,
            "form4_substrate": form4,
            "seconds_total": round(time.time() - started, 2),
            "verdict": overall,
        }
        (OUT / "V3-GA0_pa0_substrate_reverify.json").write_text(
            json.dumps(artifact, indent=2) + "\n"
        )
        print(json.dumps(artifact, indent=2))
        return 0 if overall == "PASS" else 2
    finally:
        fcntl.flock(lock_fh, fcntl.LOCK_UN)
        lock_fh.close()


if __name__ == "__main__":
    sys.exit(main())
