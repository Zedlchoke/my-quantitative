# BACKUP_MANIFEST — FUTURES-DEEPRESEARCH-V2-20261003 / DATA-BACKUP

Generated (UTC): 2026-10-02T23:30:38+00:00

Owner instruction: 'backup lại dữ liệu ở đâu đó' — all raw datasets mirrored to iCloud with SHA verification.

iCloud root: `/Users/hoangminhlong/Library/Mobile Documents/com~apple~CloudDocs/my-quantitative-futures`

| dataset | files | bytes | sha-verified | mismatch | fixed | iCloud path | sync state |
|---|---|---|---|---|---|---|---|
| databento-av1trim | 504 | 2,695,144,303 | 504 | 0 | 0 | `/Users/hoangminhlong/Library/Mobile Documents/com~apple~CloudDocs/my-quantitative-futures/av1-trim/` | COPIED + SYNC_PENDING_UNVERIFIED |
| futures-nonprice-10syms | 10535 | 1,361,587,677 | 10535 | 0 | 0 | `/Users/hoangminhlong/Library/Mobile Documents/com~apple~CloudDocs/my-quantitative-futures/nonprice/` | COPIED + SYNC_PENDING_UNVERIFIED |

## Dataset details

### databento-av1trim (ohlcv-1m + definition/statistics raw dbn.zst, parquet, per-chunk qa/ledger evidence)
- source: `/Users/hoangminhlong/my-quantitative-data/futures-databento-av1trim/`
- files: 504  |  bytes: 2,695,144,303
- sha-verified: 504  |  mismatch: 0  |  missing pre-fix: 0  |  fixed this run: 0
- verification: per-file SHA256 vs BOTH on-disk source AND vendor sha256 recorded in COMPLETION_LEDGER.json (source_vs_ledger_sha_disagreements=0); ledger_entry.json verified by existence + JSON-parse
- scope: 72/72 MIRRORED chunks x 7 files = 504 files; 20 additional ledger chunks are DROPPED_BY_OWNER_RESCOPE (GC/SI/CL/NG — never downloaded, nothing to mirror)
- sync state: **COPIED + SYNC_PENDING_UNVERIFIED** (verified 2026-10-02T23:30:38+00:00)

### futures-nonprice-10syms (raw PIT families + normalized parquet + raw_manifest.jsonl)
- source: `/Users/hoangminhlong/.my-quantitative-data/futures-nonprice-10syms`
- files: 10535  |  bytes: 1,361,587,677
- sha-verified: 10535  |  mismatch: 0  |  missing pre-fix: 0  |  fixed this run: 0
- verification: FULL hash of every file source-vs-mirror (exceeds the sampled floor; all 4,565 NOAA files hashed fully); raw_manifest.jsonl cross-check: 10520 agree / 0 disagree; 0 raw files lack a manifest row
- scope: 13 family dirs (incl. empty bls_gate) + normalized/ (14 tidy parquet) + raw_manifest.jsonl; manifest lives in the data dir (repo path in dispatch does not exist — noted)
- sync state: **COPIED + SYNC_PENDING_UNVERIFIED** (verified 2026-10-02T23:30:38+00:00)

## In-git evidence (NOT mirrored)

In-git evidence (research/control/** manifests, ledgers, QA reports, dossiers) is NOT mirrored to iCloud: the git branch prep/futures-behavior-10syms-20261002 is its own backup. Push is not allowed by lane law; owner should push/remote-archive when they choose (worktree-local commits only so far).

## Disk-space impact (measured)

Measured impact: mirrors occupy 2.51 GiB (av1-trim) + 1.29 GiB (nonprice) = 3.80 GiB ADDITIONAL local disk (iCloud mirrors keep a full local copy until evicted; 0 evicted placeholders at verification time). Data volume free space was 30 GiB before the nonprice copy, 26 GiB after all lanes' concurrent activity. Once macOS finishes uploading, `brctl evict` can reclaim the ~3.8 GiB while iCloud retains the data.

## Honesty labels

COPIED = file present in the local CloudDocs folder with SHA256 equal to source. Actual cloud upload is macOS/iCloud's job and is NOT verified here -> SYNC_PENDING_UNVERIFIED. Eviction policy is macOS/owner-controlled.

## Concurrency (FX-BACKFILL)

FX-BACKFILL lane was actively adding chunks during this task (backfill_20261003 evidence dir created mid-run). Final delta pass at 2026-10-02T23:30:38+00:00 found no newly-completed un-mirrored chunks; in-flight chunks remain the FX lane's own mirror responsibility per its pipeline.

## Artifacts

- backup_manifest.json (this manifest, machine-readable)
- av1_verify_report.json (per-file verification detail, av1-trim)
- nonprice_mirror_report.json (per-run copy/verify detail, nonprice)
- verify_av1_mirror.py / mirror_nonprice.py / gen_backup_manifest.py (reproducible scripts)
