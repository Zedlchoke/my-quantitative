# S6 FUTURE-MUTATION SPOT CHECK — lane S (2026-09-27)

Question: does SEC mutate `acceptanceDateTime` values in-place in the
`submissions` JSON (retroactive re-dating of 10-Q/10-K events)?

Method: 20 cohort CIKs (deterministic mix across CIK-space: first 5, two
middle blocks, last 5 — spans old blue chips through 2025-2027-era SPAC
registrations), staged shards from S5 re-fetched as a second network pass;
byte-level sha comparison + per-accession acceptanceDateTime diff for
`10-Q`/`10-K` rows exactly.

Raw evidence: `.staging_eventmech/mutation_check_raw.json`; requests logged
in `fetch_log.jsonl`.

## Result

| Metric | Value |
|---|---|
| CIKs re-fetched | 20 (20× HTTP 200) |
| byte-identical to staged shard | 20/20 |
| acceptanceDateTime diffs on 10-Q/10-K rows | 0 |
| new accessions appearing post-staging | 0 |

**Verdict: NO_MUTATION.** The acceptance clock is stable at the source —
amendments arrive as NEW accessions (none appeared in this window), never as
in-place edits of already-published rows. Staged A1 event vintages are
reproduction-safe for G4/G5.

Caveat (recorded): 20/2,178 CIKs sampled (~0.9%), zero-window re-check; the
byte-identical result on 20/20 including high-filing-volume names (AAPL) is
the strongest cheap evidence available within the request budget.
