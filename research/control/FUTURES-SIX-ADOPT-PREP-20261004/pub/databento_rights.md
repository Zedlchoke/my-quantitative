# DATABENTO_RIGHTS — publication-rights verdicts (PUB-RIGHTS lane)

Round FUTURES-SIX-ADOPT-PREP-20261004 · task PUB-RIGHTS · generated 2026-10-04.
Scope: what the acquired data's license posture permits pushing to the
GitHub remote `Zedlchoke/my-quantitative` as part of a publication-subset
branch created FROM MAIN (d8cf8eca) by the controller.

Verdict enum: `PUSH_SAFE` / `PUSH_UNSAFE` / `UNRESOLVED_FAIL_CLOSED`.

## 0. Evidence base (all read-only, sibling worktree futures-behavior)

| # | Evidence | Pointer |
|---|---|---|
| E1 | `DATA_ACQUISITION_SPEC.md` §3, licensing/tier FACT(sourced) (catalog page, access 2026-10-02): "historical data requires **no license**; live data requires a CME license"; and price-chain caveats item 3: "**Redistribution/external distribution requires the Plus tier; internal research does not. We are internal-research only.**" | `/Users/hoangminhlong/my-quantitative/.worktrees/futures-behavior/prep/research/control/FUTURES-BEHAVIOR-10SYMS-PREP-20261002/DATA_ACQUISITION_SPEC.md` lines 93–110 |
| E2 | `DOWNLOAD_REPORT.md` iCloud-mirror section: "This is the owner's personal backup of licensed data; **no redistribution**." | same round, `acquisition_download/DOWNLOAD_REPORT.md` line 134 |
| E3 | Round-1 independent verifier (VERIFY-A7READY handoff, 2026-10-04): entitlement = owner-authorized paid purchase ($105.81 delivered vs $125 ceiling); "**license scope beyond research reuse UNRESOLVED fail-closed**." | `research/control/FUTURES-SIX-READINESS-20261004/dispatch/handoff_VERIFY-A7READY.json` (summary + authority_claims) |
| E4 | Acquisition mechanics: 72 MIRRORED chunks, sha256-verified per chunk, COMPLETION_LEDGER SUBMITTED-first; raw `.dbn.zst` + parquet delivered to owner data roots outside the repo | `acquisition_download/DOWNLOAD_REPORT.md`, `acquisition_download/COMPLETION_LEDGER.json` (schema `futures_behavior_acq_completion_ledger@1`) |
| E5 | **LICENSE_TEXT_NOT_IN_REPO**: no verbatim Databento ToS / data-license agreement text is captured anywhere under the FUTURES-BEHAVIOR round or the repo. E1's statements are our own sourced paraphrases of the vendor's public catalog/pricing pages (URLs + access dates recorded), not the contract text itself. | repo-wide grep (license/terms/redistribut/internal-research), 2026-10-04 |
| E6 | Repo visibility measured 2026-10-04: unauthenticated GET → HTTP **404 ⇒ PRIVATE** (push history proves existence; 404 ambiguity disclosed). | `pub/repo_visibility.json` |

CME-side note: the `fx_eb/captures/*` files are verbatim captures of
publicly served official CME web data (CmeWS trading-hours service,
ProductCalendar endpoints, one product-calendar XLS). No CME terms text is
captured either (E5 applies to CME terms too); they are treated under the
same internal-research-vs-redistribution rule, fail-closed on visibility.

## 1. Verdict (a) — raw vendor files (Databento `.dbn.zst` / delivered batch files)

**PUSH_UNSAFE** (exclude from any push; fail-closed if this is ever contested).

- E1: external distribution requires the Plus tier; owner is internal-research
  only. E2: lane explicitly framed delivery as owner's personal backup, no
  redistribution. E3: verifier's standing ruling — anything beyond research
  reuse is UNRESOLVED fail-closed. E5: we do not hold the verbatim license
  text, so no broader reading can be evidenced.
- Mitigating fact: no raw vendor file is inside the round-1 tree anyway —
  raw `.dbn.zst` lives under owner data roots outside the repo
  (`~/my-quantitative-data/futures-databento-av1trim`,
  `~/.my-quantitative-data/futures-10syms-v1/raw`). Exclusion costs nothing.
- Note: a PRIVATE GitHub repo is owner-controlled storage (E2's iCloud-backup
  analogy), but since no raw vendor file needs to be pushed, we do not need
  to adjudicate that analogy. Excluded by construction.

## 2. Verdict (b) — derived parquet caches (our rebuilds from vendor data)

**PUSH_SAFE, CONDITIONAL on the measured PRIVATE visibility** (404,
2026-10-04). If the repo is or becomes PUBLIC: **PUSH_UNSAFE** — strip and
re-adjudicate.

- These caches (≤100MB: held chains, sessions, held daily, hold segments,
  roll stats; and the two >100MB `cache_v3` parquets which are excluded from
  any push by size regardless) are our transformations of licensed data —
  derivative works of vendor data, not authored content.
- Private, access-controlled repo = internal research use: exactly the
  posture E1 records as permitted ("internal research does not [require
  Plus]"), the posture E2 affirms (owner's own backup), and the boundary E3
  drew (research reuse inside, everything beyond fail-closed).
- Flip rule (hard): visibility flip to PUBLIC ⇒ the derived-data argument
  dies (external distribution ⇒ Plus tier per E1). Controller must then
  rebuild the subset with SMALL_DERIVED excluded.
- Honesty caveat: verdict rests on our sourced paraphrase (E1), not on
  verbatim terms (E5). If the owner ever obtains the Databento agreement
  text, re-adjudicate against the actual clause.

## 3. Verdict (c) — aggregate statistics embedded in authored reports

**PUSH_SAFE** at any visibility (private or public).

- The authored reports (DATA_READINESS_*.md, readiness/verify/census JSONs)
  contain small aggregates and measured facts: roll switch dates, census
  counts, session-structure tables, fee figures, reproduction digests —
  analysis conclusions with attribution, not redistributable bulk series.
  Content probes 2026-10-04 (see `publication_manifest.json`
  classification_rules + boundary_note).
- Standard analytical/quotation posture; sources are cited in-document with
  access dates (round discipline: FACT(sourced) taxonomy). Round-1's own
  language scan (`verify/language_scan.json`) reports 0 forbidden claims.

## 4. CME captures (`fx_eb/captures/*` — RAW_CAPTURE class)

**PUSH_SAFE, CONDITIONAL on the measured PRIVATE visibility**; PUBLIC ⇒
**PUSH_UNSAFE** (exclude). Same structure as (b): captures of publicly
served official CME data used for calendar/holiday verification inside the
round; no terms text captured (E5); internal-research argument holds only
while the repo is private. Companion authored audit records
(`DECOMPRESSION_NOTE.json`, `SHA256SUMS_lane.txt`, `fetch_log.jsonl`) are
AUTHORED_DOC and always pushable.

## 5. Standing law

1. Publication authority = controller; this lane only classifies and
   recommends.
2. The visibility gate is a measured fact with a timestamp — it must be
   re-measured before any push that includes SMALL_DERIVED/RAW_CAPTURE.
3. Big blobs (>100MB, 6 files, 940,491,345 B = 896.92 MiB) stay local in all
   scenarios (see `PROVENANCE_DRAFT.md`).
4. Anything not covered here (future vendor files, new captures) is
   UNRESOLVED_FAIL_CLOSED until classified by a rights lane.
