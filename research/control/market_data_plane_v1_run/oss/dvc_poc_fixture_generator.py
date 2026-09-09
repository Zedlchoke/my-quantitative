#!/usr/bin/env python
"""MDP-V1 DVC POC deterministic fixture generator.

Generates 32 files x 4 MiB = 128 MiB of non-proprietary synthetic bytes from a
fixed seed using a hashlib counter stream (deterministic across hosts and
processes). Writes bundle_manifest.json with per-file sha256 and totals.

Usage:
    python dvc_poc_fixture_generator.py <output_dir>

The output directory is a scratch location OUTSIDE git tracking. Nothing here
touches owner data. Run by the POC stage of MARKET-DATA-PLANE-V1 (plan §4.5).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

SEED = 20260909
FILE_COUNT = 32
FILE_BYTES = 4 * 1024 * 1024


def file_bytes(index: int) -> bytes:
    """Deterministic pseudo-random 4 MiB stream: sha256(seed || file_idx || block_idx)."""
    out = bytearray()
    block = 0
    while len(out) < FILE_BYTES:
        digest = hashlib.sha256(f"{SEED}:{index}:{block}".encode()).digest()
        out.extend(digest)
        block += 1
    return bytes(out[:FILE_BYTES])


def main(output_dir: str) -> int:
    root = Path(output_dir) / "bundle"
    root.mkdir(parents=True, exist_ok=True)
    entries = []
    for i in range(FILE_COUNT):
        name = f"synthetic_{i:04d}.bin"
        data = file_bytes(i)
        (root / name).write_bytes(data)
        entries.append(
            {
                "name": name,
                "sha256": hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
        )
        print(f"wrote {name} sha256={entries[-1]['sha256'][:16]}")
    total = sum(e["bytes"] for e in entries)
    manifest = {
        "schema": "mdp_dvc_poc_fixture@1",
        "seed": SEED,
        "file_count": FILE_COUNT,
        "total_bytes": total,
        "files": entries,
    }
    (Path(output_dir) / "bundle_manifest.json").write_text(json.dumps(manifest, indent=1) + "\n")
    print(f"bundle: {FILE_COUNT} files, {total} bytes; manifest written")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "."))
