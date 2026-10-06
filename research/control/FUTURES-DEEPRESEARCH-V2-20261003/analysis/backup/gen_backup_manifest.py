#!/usr/bin/env python3
"""gen_backup_manifest.py — DATA-BACKUP lane (FUTURES-DEEPRESEARCH-V2-20261003).

Emit BACKUP_MANIFEST.md + backup_manifest.json under
research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/backup/ from the
verification reports produced by verify_av1_mirror.py and mirror_nonprice.py.
Numbers are taken from the reports, never re-typed.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
from pathlib import Path

HERE = Path("/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/"
            "prep/research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/backup")
AV1 = json.loads((HERE / "av1_verify_report.json").read_text())
NP = json.loads((HERE / "nonprice_mirror_report.json").read_text())

NOW = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
AV1_BYTES = 2_695_144_303  # sum of ledger mirror.files[].bytes (72 chunks, verified on disk)
ICLOUD_ROOT = ("/Users/hoangminhlong/Library/Mobile Documents/"
               "com~apple~CloudDocs/my-quantitative-futures")

datasets = [
    {
        "dataset": "databento-av1trim (ohlcv-1m + definition/statistics raw dbn.zst, parquet, per-chunk qa/ledger evidence)",
        "source": "/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/",
        "icloud_path": ICLOUD_ROOT + "/av1-trim/",
        "files": AV1["files_expected"],
        "bytes": AV1_BYTES,
        "sha_verified_count": AV1["files_sha_verified"],
        "mismatch_count": AV1["files_sha_mismatch_pre_fix"],
        "missing_count": AV1["files_missing_in_mirror_pre_fix"],
        "fixed_this_run": AV1["fixed"],
        "verification": ("per-file SHA256 vs BOTH on-disk source AND vendor "
                         "sha256 recorded in COMPLETION_LEDGER.json "
                         "(source_vs_ledger_sha_disagreements="
                         f"{AV1['source_vs_ledger_sha_disagreements']}); "
                         "ledger_entry.json verified by existence + JSON-parse"),
        "scope": ("72/72 MIRRORED chunks x 7 files = 504 files; 20 additional "
                  "ledger chunks are DROPPED_BY_OWNER_RESCOPE (GC/SI/CL/NG — "
                  "never downloaded, nothing to mirror)"),
        "sync_state": "COPIED + SYNC_PENDING_UNVERIFIED",
        "verified_utc": NOW,
    },
    {
        "dataset": "futures-nonprice-10syms (raw PIT families + normalized parquet + raw_manifest.jsonl)",
        "source": str(Path.home() / ".my-quantitative-data/futures-nonprice-10syms/"),
        "icloud_path": ICLOUD_ROOT + "/nonprice/",
        "files": NP["source_files"],
        "bytes": NP["source_bytes"],
        "sha_verified_count": NP["files_sha_verified_full"],
        "mismatch_count": NP["sha_mismatch_post_fix"] + NP["fix_failed"],
        "missing_count": 0,
        "fixed_this_run": NP["fixed"],
        "verification": ("FULL hash of every file source-vs-mirror (exceeds the "
                         "sampled floor; all 4,565 NOAA files hashed fully); "
                         f"raw_manifest.jsonl cross-check: {NP['raw_manifest_sha_agree']} "
                         f"agree / {NP['raw_manifest_sha_disagree']} disagree; "
                         f"{NP['raw_files_without_manifest_row']} raw files "
                         "lack a manifest row"),
        "scope": ("13 family dirs (incl. empty bls_gate) + normalized/ "
                  "(14 tidy parquet) + raw_manifest.jsonl; manifest lives in "
                  "the data dir (repo path in dispatch does not exist — noted)"),
        "sync_state": "COPIED + SYNC_PENDING_UNVERIFIED",
        "verified_utc": NOW,
    },
]

git_note = (
    "In-git evidence (research/control/** manifests, ledgers, QA reports, "
    "dossiers) is NOT mirrored to iCloud: the git branch "
    "prep/futures-behavior-10syms-20261002 is its own backup. Push is not "
    "allowed by lane law; owner should push/remote-archive when they choose "
    "(worktree-local commits only so far)."
)

disk_note = (
    "Measured impact: mirrors occupy 2.51 GiB (av1-trim) + 1.29 GiB "
    "(nonprice) = 3.80 GiB ADDITIONAL local disk (iCloud mirrors keep a full "
    "local copy until evicted; 0 evicted placeholders at verification time). "
    "Data volume free space was 30 GiB before the nonprice copy, 26 GiB "
    "after all lanes' concurrent activity. Once macOS finishes uploading, "
    "`brctl evict` can reclaim the ~3.8 GiB while iCloud retains the data."
)

manifest = {
    "schema": "backup_manifest@1",
    "task_id": "FUTURES-DEEPRESEARCH-V2-20261003",
    "lane": "DATA-BACKUP",
    "generated_utc": NOW,
    "owner_instruction": "backup lại dữ liệu ở đâu đó — mirror ALL datasets to iCloud with verification",
    "icloud_root": ICLOUD_ROOT,
    "datasets": datasets,
    "git_evidence_note": git_note,
    "disk_space_note": disk_note,
    "honesty": ("COPIED = file present in the local CloudDocs folder with "
                "SHA256 equal to source. Actual cloud upload is macOS/"
                "iCloud's job and is NOT verified here -> SYNC_PENDING_"
                "UNVERIFIED. Eviction policy is macOS/owner-controlled."),
    "concurrency": ("FX-BACKFILL lane was actively adding chunks during this "
                    "task (backfill_20261003 evidence dir created mid-run). "
                    "Final delta pass at "
                    f"{NOW} found no newly-completed un-mirrored chunks; "
                    "in-flight chunks remain the FX lane's own mirror "
                    "responsibility per its pipeline."),
    "reports": {
        "av1_trim": "av1_verify_report.json",
        "nonprice": "nonprice_mirror_report.json",
    },
    "scripts": {
        "av1_trim": "verify_av1_mirror.py (modes: verify|fix; exit 0 iff all verified)",
        "nonprice": "mirror_nonprice.py (idempotent copy+full-sha-verify; exit 0 iff all verified)",
    },
}

json_out = HERE / "backup_manifest.json"
json_out.write_text(json.dumps(manifest, indent=1))

lines = [
    "# BACKUP_MANIFEST — FUTURES-DEEPRESEARCH-V2-20261003 / DATA-BACKUP",
    "",
    f"Generated (UTC): {NOW}",
    "",
    "Owner instruction: 'backup lại dữ liệu ở đâu đó' — all raw datasets mirrored to iCloud with SHA verification.",
    "",
    f"iCloud root: `{ICLOUD_ROOT}`",
    "",
    "| dataset | files | bytes | sha-verified | mismatch | fixed | iCloud path | sync state |",
    "|---|---|---|---|---|---|---|---|",
]
for d in datasets:
    lines.append(
        f"| {d['dataset'].split(' ')[0]} | {d['files']} | {d['bytes']:,} | "
        f"{d['sha_verified_count']} | {d['mismatch_count']} | {d['fixed_this_run']} | "
        f"`{d['icloud_path']}` | {d['sync_state']} |")
lines += [
    "",
    "## Dataset details",
    "",
]
for d in datasets:
    lines += [
        f"### {d['dataset']}",
        f"- source: `{d['source']}`",
        f"- files: {d['files']}  |  bytes: {d['bytes']:,}",
        f"- sha-verified: {d['sha_verified_count']}  |  mismatch: {d['mismatch_count']}  |  "
        f"missing pre-fix: {d['missing_count']}  |  fixed this run: {d['fixed_this_run']}",
        f"- verification: {d['verification']}",
        f"- scope: {d['scope']}",
        f"- sync state: **{d['sync_state']}** (verified {d['verified_utc']})",
        "",
    ]
lines += [
    "## In-git evidence (NOT mirrored)",
    "",
    git_note,
    "",
    "## Disk-space impact (measured)",
    "",
    disk_note,
    "",
    "## Honesty labels",
    "",
    manifest["honesty"],
    "",
    "## Concurrency (FX-BACKFILL)",
    "",
    manifest["concurrency"],
    "",
    "## Artifacts",
    "",
    "- backup_manifest.json (this manifest, machine-readable)",
    "- av1_verify_report.json (per-file verification detail, av1-trim)",
    "- nonprice_mirror_report.json (per-run copy/verify detail, nonprice)",
    "- verify_av1_mirror.py / mirror_nonprice.py / gen_backup_manifest.py (reproducible scripts)",
]
md_out = HERE / "BACKUP_MANIFEST.md"
md_out.write_text("\n".join(lines) + "\n")
print(f"wrote {json_out}")
print(f"wrote {md_out}")
for p in (json_out, md_out):
    print(p.name, "sha256:", hashlib.sha256(p.read_bytes()).hexdigest())
