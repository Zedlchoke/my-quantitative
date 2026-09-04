#!/usr/bin/env python3
"""A7 independent prelaunch verification: data authority re-hash (gate 5).

Recomputes, without trusting any recorded value:
  1. sha256 of the ETF snapshot MANIFEST.json bytes  (expect 62ac324d...)
  2. per-file sha256 of all 37 files listed in the manifest
  3. sha256 of the SEC PIT store pit_records.jsonl   (expect f53eb371...)
Read-only. No network. Prints one JSON blob with observed values.
"""
import hashlib
import json
import os
import sys

SNAPSHOT_ROOT = "/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/z8-exec-1/.staging"
SEC_STORE = ("/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v5/"
             "p0-a3-data/.staging_sec/pit_records.jsonl")
EXPECT_MANIFEST = "62ac324d7e683961b0d88f85153e4a072d09fe0a6745a54687b9e3b219d8f658"
EXPECT_SEC = "f53eb3712bc9d686ec8a91b3715beaf73be1e5243a89af1816bd62eea51df955"


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    out = {"schema": "stocks_free_v5_run/a7_data_authority_rehash@1"}

    manifest_path = os.path.join(SNAPSHOT_ROOT, "MANIFEST.json")
    out["manifest_sha256_observed"] = sha256_file(manifest_path)
    out["manifest_sha256_expected"] = EXPECT_MANIFEST
    out["manifest_sha256_match"] = out["manifest_sha256_observed"] == EXPECT_MANIFEST

    with open(manifest_path, "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    files = manifest["files"]
    out["manifest_files_listed"] = len(files)
    mismatches = []
    for rel, expect in sorted(files.items()):
        got = sha256_file(os.path.join(SNAPSHOT_ROOT, rel))
        if got != expect:
            mismatches.append({"file": rel, "expected": expect, "observed": got})
    out["manifest_per_file_mismatches"] = mismatches
    out["manifest_per_file_all_match"] = not mismatches

    store_present = os.path.exists(SEC_STORE)
    out["sec_store_present"] = store_present
    if store_present:
        size = os.path.getsize(SEC_STORE)
        out["sec_store_sha256_observed"] = sha256_file(SEC_STORE)
        out["sec_store_sha256_expected"] = EXPECT_SEC
        out["sec_store_bytes"] = size
        out["sec_store_sha256_match"] = out["sec_store_sha256_observed"] == EXPECT_SEC
        with open(SEC_STORE, "rb") as fh:
            lines = sum(1 for _ in fh)
        out["sec_store_lines"] = lines

    ok = (out["manifest_sha256_match"] and out["manifest_per_file_all_match"]
          and out.get("sec_store_sha256_match", False))
    out["verdict"] = "PASS" if ok else "FAIL"
    print(json.dumps(out, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
