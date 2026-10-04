# PROVENANCE — publication-subset branch codex/futures-six-readiness-20261004-pub

This branch is a PUBLICATION SUBSET of the canonical round FUTURES-SIX-READINESS-20261004.
- Canonical (full evidence): local branch `codex/futures-six-readiness-20261004` @ 9fb66c88d464fd90748bc04d78280c2d87939cd3 (worktree .worktrees/futures-six-readiness/prep). NOT pushable to GitHub: 6 blobs >100MB (GitHub GH001 hard limit), git-LFS absent, LFS migration = history rewrite requiring owner authorization.
- This branch: created from main @ d8cf8eca; contains exactly the 123-file push set (62 AUTHORED_DOC + 34 SCRIPT + 10 SMALL_DERIVED + 17 RAW_CAPTURE; 2,922,690 B) enumerated with per-file sha256 in FUTURES-SIX-ADOPT-PREP-20261004/pub/publication_manifest.json (round 2, lane PUB-RIGHTS). Rights basis: repo measured PRIVATE (unauthenticated GitHub API 404, re-verified immediately before push); databento-derived small caches cleared for private-visibility push per pub/databento_rights.md (raw vendor files NEVER included; license text not in repo — posture fail-closed on any visibility flip to public).
- EXCLUDED heavy blobs (6, total 940,491,345 B) — all reproducible locally via committed scripts against the shared data root:
  * nq/cache_v3/nq_outright_1m_v3.parquet (149.0MB) sha256 in publication_manifest (not-recommended entry)
  * nq/cache_v3/nq_annotated_1m_v3.parquet (170.3MB) sha256 in publication_manifest (not-recommended entry)
  * FUTURES-DEEPRESEARCH-V2-20261003/analysis/NQ_cache/{nq_outright_1m,nq_annotated_1m}.parquet (140.8/167.8MB)
  * FUTURES-DEEPRESEARCH-V2-20261003/analysis/ES_cache/{es_1m_outright,es_1m_seg}.parquet
  Rebuild: research/control/FUTURES-SIX-READINESS-20261004/nq/nq_rebuild_v3.py (round-1, REPRODUCED digests in nq/reproduction.json).
- Round 2 (adoption/decision packets) lives on codex/futures-six-adopt-prep-20261004 and is NOT part of this subset.
