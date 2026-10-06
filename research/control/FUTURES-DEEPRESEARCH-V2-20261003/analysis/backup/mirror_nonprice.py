#!/usr/bin/env python3
"""mirror_nonprice.py — DATA-BACKUP lane (FUTURES-DEEPRESEARCH-V2-20261003).

Mirror the complete nonprice dataset (raw families + normalized parquet +
raw_manifest.jsonl) from ~/.my-quantitative-data/futures-nonprice-10syms/ to
iCloud:
  /Users/hoangminhlong/Library/Mobile Documents/com~apple~CloudDocs/
    my-quantitative-futures/nonprice/

Discipline (owner instruction: 'backup lại dữ liệu ở đâu đó' — mirror ALL
datasets with verification):
  - rsync-style per-file copy (skip when dest exists with same size AND same
    sha256); never delete anything in the mirror.
  - SHA256 verification: FULL hash of every mirrored file against its source
    (exceeds the dispatch floor of "full-hash small files + all 4,565 NOAA";
    the whole set is 1.3GB so full hashing is cheap).
  - Cross-check raw-family files against the acquisition raw_manifest.jsonl
    sha256 (report-only; the on-disk source is the copy's ground truth, the
    manifest detects post-download mutation).
  - Honesty law: files present in CloudDocs are COPIED; actual cloud upload is
    macOS/iCloud's job -> SYNC_PENDING_UNVERIFIED. Owner's personal backup of
    public-domain / open-licensed data; no redistribution.

Exit 0 iff every source file (snapshot at start) is present in the mirror
with matching SHA256 when the script finishes.
"""
from __future__ import annotations

import hashlib
import json
import shutil
import sys
import time
from pathlib import Path

SOURCE = Path.home() / ".my-quantitative-data/futures-nonprice-10syms"
DEST = Path("/Users/hoangminhlong/Library/Mobile Documents/"
            "com~apple~CloudDocs/my-quantitative-futures/nonprice")
MANIFEST = SOURCE / "raw_manifest.jsonl"


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    t0 = time.time()
    manifest_sha: dict[str, str] = {}
    if MANIFEST.exists():
        for line in MANIFEST.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r.get("status") == "ok" and r.get("sha256"):
                manifest_sha[r["path"]] = r["sha256"]
    print(f"manifest ok-rows with sha: {len(manifest_sha)}")

    files = sorted(p for p in SOURCE.rglob("*") if p.is_file())
    sizes_at_start = {p: p.stat().st_size for p in files}
    total_bytes = sum(sizes_at_start.values())
    print(f"source files: {len(files)}, bytes: {total_bytes}")

    # preserve empty dirs (e.g. bls_gate) for structural fidelity
    for d in SOURCE.rglob("*"):
        if d.is_dir():
            (DEST / d.relative_to(SOURCE)).mkdir(parents=True, exist_ok=True)
    DEST.mkdir(parents=True, exist_ok=True)

    n_copied = n_verified = n_mismatch = n_fixed = n_fix_failed = 0
    n_manifest_agree = n_manifest_disagree = n_manifest_absent = 0
    copied_bytes = 0
    details: list[dict] = []

    for p in files:
        rel = p.relative_to(SOURCE)
        dst = DEST / rel
        src_size = p.stat().st_size
        need_copy = True
        if dst.exists() and dst.stat().st_size == src_size:
            # same size: confirm by hash below; only re-copy on mismatch
            need_copy = False
        if need_copy:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(p, dst)
            n_copied += 1
            copied_bytes += src_size
        src_sha = sha256_of(p)
        dst_sha = sha256_of(dst)
        if src_sha == dst_sha:
            n_verified += 1
        else:
            n_mismatch += 1
            # fix once: force re-copy
            shutil.copy2(p, dst)
            if sha256_of(dst) == src_sha:
                n_fixed += 1
                details.append({"file": str(rel), "status": "FIXED_RECOPIED"})
            else:
                n_fix_failed += 1
                details.append({"file": str(rel), "status": "FIX_FAILED",
                                "src_sha": src_sha, "dst_sha": sha256_of(dst)})
        # manifest cross-check (raw families only; rel path uses POSIX sep)
        key = rel.as_posix()
        if key in manifest_sha:
            if manifest_sha[key] == src_sha:
                n_manifest_agree += 1
            else:
                n_manifest_disagree += 1
                details.append({"file": key,
                                "status": "SOURCE_VS_RAW_MANIFEST_SHA_DISAGREE"})
        elif len(rel.parts) > 1 and rel.parts[0] != "normalized" \
                and rel.name != "raw_manifest.jsonl":
            n_manifest_absent += 1

    # mirror extras (never deleted): files in mirror not in source snapshot
    src_set = {p.relative_to(SOURCE).as_posix() for p in files}
    extras = [p.relative_to(DEST).as_posix()
              for p in DEST.rglob("*")
              if p.is_file() and p.relative_to(DEST).as_posix() not in src_set]

    # post-check: nothing on the source snapshot vanished or changed size mid-run
    n_src_changed = sum(1 for p in files if not p.exists()
                        or p.stat().st_size != sizes_at_start[p])

    report = {
        "source": str(SOURCE),
        "dest": str(DEST),
        "source_files": len(files),
        "source_bytes": total_bytes,
        "files_copied_this_run": n_copied,
        "bytes_copied_this_run": copied_bytes,
        "files_sha_verified_full": n_verified,
        "sha_mismatch_post_fix": n_mismatch - n_fixed if n_mismatch else 0,
        "fixed": n_fixed,
        "fix_failed": n_fix_failed,
        "raw_manifest_sha_agree": n_manifest_agree,
        "raw_manifest_sha_disagree": n_manifest_disagree,
        "raw_files_without_manifest_row": n_manifest_absent,
        "mirror_extra_files": extras,
        "source_files_changed_midrun": n_src_changed,
        "sync_state": "SYNC_PENDING_UNVERIFIED",
        "note": ("All files full-hash verified source vs iCloud local copy. "
                 "macOS performs the actual upload; not claimed verified "
                 "cloud-side. Personal backup; no redistribution."),
        "elapsed_sec": round(time.time() - t0, 1),
        "details": details,
    }
    out = Path("/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/"
               "prep/research/control/FUTURES-DEEPRESEARCH-V2-20261003/"
               "analysis/backup/nonprice_mirror_report.json")
    out.write_text(json.dumps(report, indent=1))
    print(json.dumps({k: v for k, v in report.items() if k != "details"}, indent=1))
    print(f"report -> {out}")
    return 0 if (n_fix_failed == 0 and n_verified + n_fixed == len(files)) else 1


if __name__ == "__main__":
    raise SystemExit(main())
