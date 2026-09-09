# MDP-V1 operator documentation

## 1. Provider-adapter checklist (before any adapter lands)

1. Source registered in the Data Fusion source registry as a CANDIDATE
   (`CANDIDATE_NOT_AUTHORIZED` or `DOCUMENTED_CANDIDATE`) — never
   implicit authority; entitlement/license evidence reference recorded.
2. Availability evidence: exact release timestamps where evidenced;
   date-only evidence maps to the next-day 00:00:00 exclusive upper
   bound (DF-ISSUE-1 semantics) — never invented timestamps.
3. Manifest first: `mdp.raw_chunk_manifest@1` with secrets-removed
   request identity, completeness status, gap reasons, sequence
   semantics (`CONTIGUOUS` only if truly guaranteed), ordered-delivery
   flag honest.
4. Events through `models.build_event` (27 fields, decimal strings,
   required `manifest_sha256`), classified via `quality.evaluate` with
   explicit `QualityParams` (staleness threshold, instrument registry).
5. Negative tests: malformed, truncated, hash-drift, duplicate, gap,
   reset, out-of-order, crossed, stale, timezone-naive inputs.
6. Provider-neutral synthetic fixtures only in git; raw payloads
   gitignored with sha256 manifests. A fixture proves code semantics,
   never data authority.

## 2. Archive recovery and quarantine runbook

- Symptom: `scan_orphans(root)` reports chunk-without-manifest,
  manifest-without-chunk, trailing partial record, or stray temps.
- Rule: orphans are DIAGNOSED, never guessed complete. Never append to
  a published chunk; never overwrite a content-addressed path.
- Recovery: (a) verify surviving bytes (`verify_chunk`); (b) if the
  chunk verifies, republish the manifest after human review; (c) if
  bytes are partial, quarantine the recoverable records with
  `QUARANTINE_ORPHAN` reason + lineage (chunk sha, byte offset) and
  re-ingest the source range as a NEW chunk with a new manifest.
- Crash windows are test-pinned: interruption before flush, before
  rename, after rename but before manifest publication.
- Hash disagreement at an existing content path = CORRUPTION: stop,
  fail closed, restore from a verified replica; never overwrite.

## 3. Asset adoption checklist (for every future cycle)

- This plane authorizes ZERO datasets. Each asset cycle must, in its
  own plan: declare the source, its entitlement, its PIT semantics,
  its coverage census, and pass its own gates before any proposal.
- Frozen semantics: an asset cycle adopting the plane inherits
  `mdp.market_event@1` as-is; any semantic change is a schema bump plus
  recomputation of every affected control (P-3), never a retrofit.
- Counters/ledgers untouched: the plane never writes scientific
  counters (proven in the DVC/POC zero-mutation check).

## 4. DVC operator note (`docs/MDP_DVC_OPERATOR.md`)

Separate the five verbs: `git pull` (code+manifests), `dvc pull`
(bytes), manifest verification (`sha256` vs committed manifests),
data-authority verification (entitlement/PIT — never implied by any
checksum), and `dvc repro` (forbidden for scored research without a
future owner plan). Know DVC-LIMITATION-1: transfers are not re-hashed.

## 5. Hypothesis test-author guide

Profiles live in `tests/mdp_hypothesis/profiles.py` (`mdp_ci`
derandomized CI; `mdp_deep` alone-running 500-example gate). When a
property fails: (1) capture the minimized counterexample from the
failure output; (2) if it is a REAL defect, write it as a small
deterministic golden test FIRST (committed before the fix is declared);
(3) the hidden example database is never reproduction evidence.

## 6. Future RD-Agent sandbox contract (design-only; NOT installed)

Trigger: MDP-V1 PASS + at least one reboot asset cycle completed under
the plane. Then RD-Agent may run in a no-outcome proposal sandbox:
outputs go through FAMILY_PIPELINE cheap-kills; A7 stays independent;
RD-Agent never sees S0/S1 performance while proposing; it is never a
scorer, selector, auditor, GO authority, or S1 reader. Deferred-tool
trigger checklist: plan §4.8 (skfolio: two independent survivors;
Dagster: 2 hosts or 10 recurring jobs or 2 evidenced scheduler
failures; Qlib: pinned offline conformance only; OpenLineage:
interoperability need, after mapping existing IDs).
