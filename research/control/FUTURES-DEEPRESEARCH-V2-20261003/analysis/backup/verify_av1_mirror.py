#!/usr/bin/env python3
"""verify_av1_mirror.py — DATA-BACKUP lane (FUTURES-DEEPRESEARCH-V2-20261003).

Independently verify the existing iCloud mirror of the Databento av1-trim
dataset against BOTH (a) the source files on local disk and (b) the SHA256s
recorded in the acquisition COMPLETION_LEDGER (vendor hashes at download
time). Fix missing/mismatched mirror files by copying from source and
re-verifying. Never deletes anything.

Mirror layout (established by FUTURES-BEHAVIOR-10SYMS-PREP acquisition):
  <ICLOUD>/<line_id>/<chunk_key>/<file>
where file is one of:
  <LINE>__<dates>__manifest.json | condition.json | metadata.json | *.dbn.zst
  <LINE>__<dates>.parquet
  qa.json            (from acquisition_download/qa/<chunk>.qa.json)
  ledger_entry.json  (written at mirror time; existence + JSON-parse check only)

Modes:
  verify   — report only
  fix      — copy source -> mirror for missing/mismatched, then re-verify

Exit code 0 iff after the run every ledger-MIRRORED chunk's expected files are
present in the mirror with matching SHA256 (post-fix in fix mode).
"""
from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import time
from pathlib import Path

WORKTREE = Path("/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep")
LEDGER = WORKTREE / "research/control/FUTURES-BEHAVIOR-10SYMS-PREP-20261002/acquisition_download/COMPLETION_LEDGER.json"
ICLOUD = Path("/Users/hoangminhlong/Library/Mobile Documents/com~apple~CloudDocs/my-quantitative-futures/av1-trim")


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 22), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    mode = sys.argv[1] if len(sys.argv) > 1 else "verify"
    fix = mode == "fix"
    ledger = json.loads(LEDGER.read_text())
    chunks = ledger["chunks"]

    mirrored = {k: c for k, c in chunks.items() if c.get("state") == "MIRRORED"}
    print(f"ledger chunks: {len(chunks)} total, {len(mirrored)} MIRRORED")

    n_files = n_verified = n_missing_src = n_missing_mirror = 0
    n_mismatch = n_fixed = n_fix_failed = n_ledger_sha_disagree = 0
    details: list[dict] = []
    t0 = time.time()

    for key, chunk in sorted(mirrored.items()):
        line_id = chunk["line_id"]
        dest_dir = ICLOUD / line_id / key

        # expected (source_path, mirror_name, ledger_sha_or_None)
        expected: list[tuple[Path, str, str | None]] = []
        for f in chunk.get("files", []):
            expected.append((Path(f["local_path"]), Path(f["local_path"]).name, f.get("sha256")))
        qa = chunk.get("qa", {})
        if qa.get("report_path"):
            expected.append((Path(qa["report_path"]), "qa.json", None))
        if qa.get("parquet_path"):
            expected.append((Path(qa["parquet_path"]), Path(qa["parquet_path"]).name, None))

        # ledger_entry.json: written at mirror time, no static source
        le = dest_dir / "ledger_entry.json"
        n_files += 1
        if not le.exists():
            rec = {"chunk": key, "file": "ledger_entry.json", "status": "MISSING_IN_MIRROR"}
            if fix:
                # regenerate from current ledger chunk (same content recipe as
                # mirror_batch.py: {"chunk":..., "manifest":{}})
                try:
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    le.write_text(json.dumps({"chunk": chunk, "manifest": {}}, default=str))
                    json.loads(le.read_text())
                    rec["status"] = "FIXED_REGENERATED"
                    n_fixed += 1
                except Exception as e:  # noqa: BLE001
                    rec["status"] = f"FIX_FAILED:{e}"
                    n_fix_failed += 1
            else:
                n_missing_mirror += 1
            details.append(rec)
        else:
            try:
                json.loads(le.read_text())
                n_verified += 1
            except Exception as e:  # noqa: BLE001
                details.append({"chunk": key, "file": "ledger_entry.json",
                                "status": f"UNPARSEABLE:{e}"})
                n_mismatch += 1

        for src, name, ledger_sha in expected:
            n_files += 1
            rec = {"chunk": key, "file": name}
            if not src.exists():
                n_missing_src += 1
                details.append({**rec, "status": "MISSING_IN_SOURCE"})
                continue
            dst = dest_dir / name
            src_sha = sha256_of(src)
            if ledger_sha and ledger_sha != src_sha:
                # source no longer matches vendor hash recorded at download
                n_ledger_sha_disagree += 1
                details.append({**rec, "status": "SOURCE_VS_LEDGER_SHA_DISAGREE",
                                "src": str(src)})
            if not dst.exists():
                n_missing_mirror += 1
                if fix:
                    dest_dir.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(src, dst)
                    if sha256_of(dst) == src_sha:
                        n_fixed += 1
                        details.append({**rec, "status": "FIXED_COPIED", "bytes": dst.stat().st_size,
                                        "sha256": src_sha, "src": str(src)})
                    else:
                        n_fix_failed += 1
                        details.append({**rec, "status": "FIX_COPY_SHA_MISMATCH"})
                else:
                    details.append({**rec, "status": "MISSING_IN_MIRROR"})
                continue
            dst_sha = sha256_of(dst)
            if dst_sha == src_sha:
                n_verified += 1
            else:
                n_mismatch += 1
                if fix:
                    shutil.copy2(src, dst)
                    if sha256_of(dst) == src_sha:
                        n_fixed += 1
                        details.append({**rec, "status": "FIXED_RECOPIED",
                                        "sha256": src_sha, "src": str(src)})
                    else:
                        n_fix_failed += 1
                        details.append({**rec, "status": "FIX_COPY_SHA_MISMATCH",
                                        "bad_sha": dst_sha})
                else:
                    details.append({**rec, "status": "SHA_MISMATCH",
                                    "mirror_sha": dst_sha, "source_sha": src_sha})

    # extras: files in mirror chunk dirs that no MIRRORED chunk expects (never deleted)
    expected_names: dict[str, set[str]] = {}
    for key, chunk in mirrored.items():
        d = ICLOUD / chunk["line_id"] / key
        expected_names[str(d)] = set()
        for f in chunk.get("files", []):
            expected_names[str(d)].add(Path(f["local_path"]).name)
        if chunk.get("qa", {}).get("parquet_path"):
            expected_names[str(d)].add(Path(chunk["qa"]["parquet_path"]).name)
        expected_names[str(d)].add("qa.json")
        expected_names[str(d)].add("ledger_entry.json")
    extras = []
    if ICLOUD.exists():
        for p in sorted(ICLOUD.rglob("*")):
            if p.is_file():
                rel = p.relative_to(ICLOUD)
                if len(rel.parts) >= 3:  # line/chunk/file
                    ck = str(ICLOUD / rel.parts[0] / rel.parts[1])
                    if ck in expected_names and p.name not in expected_names[ck]:
                        extras.append(str(rel))

    # source-side chunks not in ledger (concurrent FX-BACKFILL landing zone) — report only
    src_root = Path("/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim")
    new_src_chunks = []
    for line_dir in sorted((src_root / "raw" / "dbn_zst").glob("*/")):
        for f in line_dir.glob("*.dbn.zst"):
            stem = f.name  # LINE__dates__vendor.dbn.zst
            ck = "__".join(stem.split("__")[:2])
            if ck not in chunks:
                new_src_chunks.append(str(f.relative_to(src_root)))

    report = {
        "mode": mode,
        "ledger_path": str(LEDGER),
        "icloud_path": str(ICLOUD),
        "chunks_total": len(chunks),
        "chunks_mirrored_expected": len(mirrored),
        "files_expected": n_files,
        "files_sha_verified": n_verified,
        "files_missing_in_source": n_missing_src,
        "files_missing_in_mirror_pre_fix": n_missing_mirror,
        "files_sha_mismatch_pre_fix": n_mismatch,
        "source_vs_ledger_sha_disagreements": n_ledger_sha_disagree,
        "fixed": n_fixed,
        "fix_failed": n_fix_failed,
        "mirror_extra_files": extras,
        "source_chunks_not_in_ledger_fxbackfill_zone": new_src_chunks,
        "elapsed_sec": round(time.time() - t0, 1),
        "details": details,
    }
    out = WORKTREE / "research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/backup/av1_verify_report.json"
    out.write_text(json.dumps(report, indent=1))
    print(json.dumps({k: v for k, v in report.items() if k != "details"}, indent=1))
    print(f"report -> {out}")
    ok = (n_missing_src == 0 and n_fix_failed == 0 and n_ledger_sha_disagree == 0
          and (n_missing_mirror == 0 and n_mismatch == 0 if not fix
               else (n_missing_mirror == n_fixed or n_missing_mirror == 0)))
    # after fix mode, remaining problems are only what fix couldn't solve
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
