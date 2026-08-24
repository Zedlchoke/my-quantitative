# V5R Clean-Lineage Contract (PLAN §12)

Frozen 2026-08-24T11:34:26.079337+00:00 at HEAD `66917f75b362` with a clean tree (zero dirty files allowed at freeze).

## Authority
Legacy V5 is permanently closed as **V5_FAIL** (`v5_legacy_transition.json`).
V5R is a NEW validation lineage: it never re-labels legacy artifacts as PASS and
cites quarantined evidence (`quarantine_manifest.json`) for forensic debugging only.

## Pre-execution freezes (this baseline)
- Source/spec/data-contract hashes: `source_spec_data_contract_hashes` (135 files).
- Reused frozen V4 candidate specs (DIAGNOSTIC_RECALC only): hashes per legacy
  experiment under `results/diagnostic_v5/*/frozen/`.
- Registry snapshot: 499 rows, sha256 `d4a117bc3573f4b8`; global trial ledger snapshot sha256 `fe972c1868f99af7`.
- Component freezes: A2 provenance/isolation, A3 data window+universe+funding
  cadence, A4 terminal/capital/risk/cost versions, A5 reconciler v2 + guarded
  finalization + no gate constants.

## Execution rules
1. Exactly four diagnostic recalc runs listed in `planned_v5r_experiments`;
   no parameter edits after launch; no fifth run.
2. Per-run output roots `results/diagnostic_v5r/<id>/`, separate registry shards
   under `results/registry/shards/`; A1 merges shards deterministically post-run.
   Diagnostics never increment the scored-trial count.
3. Reproductions via `--reproduce` into `results/reproduction_v5r/<verify_id>/`.
4. Gates R01-R18 evaluated from measured artifacts only; missing evidence fails closed.
