# RECOMMENDATION — publication-subset push set (PUB-RIGHTS lane, 2026-10-04)

Round FUTURES-SIX-ADOPT-PREP-20261004 · for the controller's decision on the
light `-pub` branch FROM MAIN (d8cf8eca). Full per-file evidence in
`publication_manifest.json`; license reasoning in `databento_rights.md`;
canonical-vs-pub stub in `PROVENANCE_DRAFT.md`.

## Rule applied

1. Minimum bar (always pushable): **AUTHORED_DOC + SCRIPT** — our work
   product, safe at any visibility.
2. **SMALL_DERIVED** (≤100MB derivatives of vendor/official data) and
   **RAW_CAPTURE** (verbatim archived official CME payloads): included ONLY
   because the measured visibility is **PRIVATE** (unauthenticated API →
   HTTP 404 on 2026-10-04; push history proves the repo exists ⇒ private,
   not nonexistent) AND the rights verdicts are PUSH_SAFE-CONDITIONAL on
   exactly that visibility (internal-research argument: Databento
   DATA_ACQUISITION_SPEC.md L93–110 "redistribution/external distribution
   requires the Plus tier; internal research does not — we are
   internal-research only"; round-1 verifier: beyond-research-reuse is
   fail-closed). If the repo is PUBLIC: exclude both classes.
3. **BIG_DERIVED** (>100MB): never pushable — 6 blobs, excluded in all
   scenarios (also above GitHub's hard blob limit).
4. Credential scan over the whole enumerated set: NO_MATCH (patterns: api
   key/secret/token/password/Bearer/AKIA/literal DATABENTO_API_KEY
   assignment).

## Recommended push set (123 files, 2,922,690 B ≈ 2.79 MiB)

| Class | Count | Bytes | Push | Condition |
|---|---|---|---|---|
| AUTHORED_DOC | 62 | 722,006 | yes | none (any visibility) |
| SCRIPT | 34 | 349,322 | yes | none (any visibility) |
| SMALL_DERIVED | 10 | 1,751,565 | yes | PRIVATE only (measured 404); strip on PUBLIC flip |
| RAW_CAPTURE | 17 | 99,797 | yes | PRIVATE only (measured 404); strip on PUBLIC flip |
| BIG_DERIVED | 2 | 327,542,930 | NO | excluded in all scenarios |
| **Total enumerated** | **125** | | | |

Excluded-from-any-push heavy blobs (all 6, incl. the 4 that live under the
sibling `FUTURES-DEEPRESEARCH-V2-20261003` tree and were part of the round-1
branch payload): 940,491,345 B = 896.92 MiB — matches the dispatch's
"6 blobs >100MB, 897MB total" (2× cache_v3, 2× baseline NQ_cache, 2×
ES_cache). Hashes + local paths: `publication_manifest.json`
`excluded_big_blobs` and `PROVENANCE_DRAFT.md`.

## Controller action requested

**MAY PROCEED.** Concretely:

1. Create the light branch FROM MAIN (d8cf8eca) — no history rewrite, no LFS.
2. Copy in the 123 push-set files under their existing repo-relative paths
   (`research/control/FUTURES-SIX-READINESS-20261004/**` minus the two
   `nq/cache_v3/nq_{annotated,outright}_1m_v3.parquet`). Do NOT copy anything
   from `FUTURES-DEEPRESEARCH-V2-20261003` (its ≤100MB files were never in
   scope; its 4 >100MB files are excluded blobs).
3. Include `pub/PROVENANCE_DRAFT.md` in the -pub branch (it exists to live
   there) and this pub/ set as the controller sees fit.
4. Re-measure visibility immediately before the push (one unauthenticated
   GET). If not 404/PRIVATE: push only AUTHORED_DOC + SCRIPT (96 files) and
   report the deviation.
5. On any future visibility flip to public: strip SMALL_DERIVED +
   RAW_CAPTURE from the -pub branch and re-adjudicate.

## Residual disclosures

- **LICENSE_TEXT_NOT_IN_REPO**: no verbatim Databento (or CME) terms text is
  captured; verdicts rest on our sourced paraphrases (URLs + access dates)
  plus round-1's verifier ruling. Re-adjudicate if the actual agreement text
  becomes available.
- 404 ⇒ PRIVATE carries a residual ambiguity (nonexistent), resolved by push
  history only probabilistically; re-measure before push.
- AUTHORED_DOC/SMALL_DERIVED boundary for a handful of mid-size JSONs is a
  judgment call (measurement records vs extracts); the classification of
  every file and the boundary rule are recorded in
  `publication_manifest.json` so the controller can re-cut the line without
  re-deriving it. The conservative fallback (drop the 2 SMALL_DERIVED JSON
  extractions, keep parquet caches) changes the set by only 2 files.
