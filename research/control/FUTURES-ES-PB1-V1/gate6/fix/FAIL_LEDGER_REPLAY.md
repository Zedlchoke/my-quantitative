# FAIL RECORD — trial_ledger.py reopen/append hash-chain defect (reproduced BEFORE fix)

- Reproduction (2026-10-04, controller, at HEAD 71326c8c, script inline in
  commit message context; exact API calls):
  1. `TrialLedger(path, 24 synthetic ids)`; `record_result("SYNTH-00","PASS")`
     → `verify()["ok"] == True`.
  2. NEW process object: `TrialLedger(path, same ids)` (reopen from disk);
     `record_result("SYNTH-01","PASS")` → **LedgerError: "hash-chain break at
     line 2 (predecessor tampered or link rewritten)"**.
- Root cause (code-level, gate6/trial_ledger.py L125):
  `self._prev_sha = row.get("prev_row_sha")` — replay restores the chain
  cursor from the LAST ROW'S `prev_row_sha` FIELD (a pointer to the
  second-to-last row) instead of the HASH OF THE LAST ROW itself
  (`_row_sha(row)`), which is what `_append` (L150) correctly maintains.
  Consequence: the first append after any reopen links to the wrong
  predecessor and the verifier (correctly) rejects the chain.
- Severity: CRITICAL for gate-6 operability (any scored run spanning more
  than one ledger session — the normal case: per-fold/per-identity
  appends across processes — would either fail verification or, worse,
  be misdiagnosed as tampering). The ledger's verification law itself is
  CORRECT; the defect is in replay-state restoration only.
- Law for the fix (append-only): the ledger FILE's history is never
  rewritten; the one-line replay fix restores the cursor correctly;
  correctness is re-proven by a comprehensive synthetic suite (reopen
  across many sessions, tamper rejection, interrupted-write law,
  duplicate/retry accounting, denominator preservation). No quarantined
  PnL read; nothing about hypotheses/costs/folds/identities changes.

— End FAIL record. Fix is NOT in this commit.
