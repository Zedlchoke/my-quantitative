"""V11-specific research helpers (sprint V11P).

Lane-owned modules under ``research/v11/`` are add-only V11 helpers; nothing
here may mutate the historical V10 adapter surface. Modules are imported
explicitly (no eager re-exports here) so parallel lanes can add siblings
without import side effects:

* :mod:`.publication_identity` -- versioned trial identity (v2) and the
  append-only denominator reconciliation helpers (lane A2).
* :mod:`.cost_feasibility` -- schedule-only cost/turnover feasibility gate
  with frozen pre-score floors (lane A3).
"""
