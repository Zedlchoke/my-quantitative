"""V11-specific research helpers (sprint V11P).

Lane-owned modules under ``research/v11/`` are add-only V11 helpers; nothing
here may mutate the historical V10 adapter surface, and nothing in this
package computes, persists or publishes a scored metric. Modules are imported
explicitly (no eager re-exports here) so parallel lanes can add siblings
without import side effects:

* :mod:`.publication_identity` -- versioned trial identity (v2) and the
  append-only denominator reconciliation helpers (lane A2).
* :mod:`.cost_feasibility` -- schedule-only cost/turnover feasibility gate
  with frozen pre-score floors (lane A3).
* :mod:`.exact_arm_dryrun` -- no-real-PnL exact-arm dry-run and
  platform-safe QA preflight; every write is confined to caller-provided
  temporary paths (lane A4).
"""
