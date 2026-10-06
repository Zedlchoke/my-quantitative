# PROVENANCE_DRAFT — canonical vs publication-subset (for the future `-pub` branch)

Drafted by PUB-RIGHTS (FUTURES-SIX-ADOPT-PREP-20261004) on 2026-10-04 for
inclusion in the light `-pub` branch the controller creates FROM MAIN
(d8cf8eca). This file is the provenance contract of that branch.

## Canonical vs publication subset

- **Canonical evidence tree**: local branch
  `codex/futures-six-readiness-20261004` @ `9fb66c88d464fd90748bc04d78280c2d87939cd3`
  (worktree `/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness/prep`).
  It contains the FULL evidence for round FUTURES-SIX-READINESS-20261004,
  including the heavy parquet caches listed below. It is the authority for
  every number in the round's reports; nothing on `-pub` overrides it.
- **`-pub` branch**: publication subset created FROM MAIN (d8cf8eca) — the
  123 push-set files of `research/control/FUTURES-SIX-READINESS-20261004/**`
  (AUTHORED_DOC + SCRIPT + visibility-gated SMALL_DERIVED + RAW_CAPTURE) plus
  this provenance record. It exists for sharing/review; it is NOT the
  canonical tree. sha256 of every included file is pinned in the adopting
  round's `publication_manifest.json` (round
  FUTURES-SIX-ADOPT-PREP-20261004, pub/).
- Reproduction claims made on `-pub` are valid only against the canonical
  commit above; the caches it lacks are the 6 blobs below.

## The 6 excluded big blobs (>100MB; 940,491,345 B = 896.92 MiB total)

Group `cache_v3` — NQ v3 rebuild caches (rebuilt by this round from vendor
1m data):

| sha256 | bytes | local path (canonical worktree root) |
|---|---|---|
| `e233da66420b3daa8a5dfff84bb8cc19083c305a5eb66f4a936083c9028f6522` | 178,545,904 | `research/control/FUTURES-SIX-READINESS-20261004/nq/cache_v3/nq_annotated_1m_v3.parquet` |
| `10cfe94d9c7754c009a849cca251c19d64733a8c36a74c736a87b56cbf8bc463` | 148,997,026 | `research/control/FUTURES-SIX-READINESS-20261004/nq/cache_v3/nq_outright_1m_v3.parquet` |

Group `baseline_NQ_cache` — DEEP-v2 baseline NQ 1m caches (upstream input to
the v3 rebuild; built in round FUTURES-DEEPRESEARCH-V2-20261003):

| sha256 | bytes | local path |
|---|---|---|
| `716d2d4011e6112a28f6b8384336f9b8efbab054ab4168ca7e4543deccabc5ad` | 176,114,434 | `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/NQ_cache/nq_annotated_1m.parquet` |
| `db2b2d96266aff22ffce4c6d6c544b39bca08fdfca47ef05beef533641391851` | 147,517,755 | `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/NQ_cache/nq_outright_1m.parquet` |

Group `ES_cache` — DEEP-v2 ES 1m caches (inputs to this round's ES
readiness verification):

| sha256 | bytes | local path |
|---|---|---|
| `7ae6de2d5896d9e150f70209f2709ca70b625f0b06bbdbfed348b1b0e0227b95` | 109,199,264 | `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_cache/es_1m_outright.parquet` |
| `787c4912622e844bda9cc0ba6a4abe27dcfc0f15299f8f4fe322f7ccb17249de` | 180,116,962 | `research/control/FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_cache/es_1m_seg.parquet` |

(Paths above are repo-relative under the canonical worktree
`/Users/hoangminhlong/my-quantitative/.worktrees/futures-six-readiness/prep`;
the identical bytes are present at the same repo-relative paths in the
adopt-round worktree.)

## How to rebuild the excluded caches

All rebuild inputs live on the owner's machine; nothing rebuilds from
GitHub alone.

1. **Vendor raw (source of everything)**: Databento GLBX.MDP3 batch
   delivery under `~/my-quantitative-data/futures-databento-av1trim/`
   (parquet) and `~/.my-quantitative-data/futures-10syms-v1/raw` —
   acquired in round FUTURES-BEHAVIOR-10SYMS-PREP-20261002, per-chunk
   sha256 + params in its `COMPLETION_LEDGER.json` (72 MIRRORED chunks,
   $105.81 delivered). Vendor checksums verify before any rebuild.
2. **NQ `cache_v3`**: `research/control/FUTURES-SIX-READINESS-20261004/nq/`
   scripts — `nq_rebuild_v3.py` (rebuild; consumes the baseline NQ_cache
   parquets + `nq_deep_lib_v3.py`), QC via `nq_v3_qc.py` and
   `cache_v3/rebuild_stats.json` (in the push set), digests via
   `nq_reproduce_digest.py`; independent reproduction evidence in
   `cache_v3/_repro_run1/` (small parquets + `run1_digests.json` — both in
   the push set) and `reproduction.json`.
3. **ES caches**: `research/control/FUTURES-SIX-READINESS-20261004/es/` —
   `verify_o1m_roll.py`, `verify_expiry.py`, `verify_session_holiday.py`,
   `verify_fee_and_census.py`, `assemble_readiness.py` re-derive every
   readiness number FROM the ES_cache parquets; their outputs
   (`es_*_recheck.json`, `es_readiness.json`, …) are in the push set, so a
   reviewer can confirm the claims' internal consistency without the
   caches, and rebuild the caches locally from (1) + the DEEP-v2 round's
   build scripts.
4. **CME calendar captures** (`fx_eb/captures/*`): re-fetch via the recorded
   URLs in `fetch_log.jsonl` (in the push set) with the round's
   `fetch_svc_windows.sh`; on-disk sha256 in `SHA256SUMS_lane.txt`; the
   gzip wire-vs-disk reconciliation law is in `DECOMPRESSION_NOTE.json`.

## License posture of this branch

See the adopting round's `pub/databento_rights.md`. Short form: authored
documents and scripts are ours; derived caches and CME captures are present
only while the repo is PRIVATE (internal-research argument, measured
2026-10-04 as HTTP 404 ⇒ private); raw vendor files were never committed
anywhere and stay on the owner's disk. Any flip of repo visibility voids
the derived/captured inclusions and requires stripping them.
