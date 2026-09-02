"""V11-specific research helpers (sprint V11P).

Modules are imported explicitly (no eager re-exports here) so parallel lanes
can add siblings without import side effects:

* :mod:`.publication_identity` -- versioned trial identity (v2) and the
  append-only denominator reconciliation helpers (lane A2).
"""
