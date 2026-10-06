"""freeze_wiring.wiring — adapter-to-runner integration seam for
FUTURES-5SYM-PRESCORED-20261005 (LANE-WIRING-FIX, wave-4, PREP-only).

Two encodings, one runner:

  intent_executor.py  — the REAL INTENT-EXECUTION SEAM
      (futures_5sym_prescored/intent_packet@1): every wired intent executes
      as its OWN trade (per-intent direction, signal/decision/entry/exit
      timestamps and declared fills preserved, ordering preserved) through
      the UNMODIFIED-runner accounting/twin/ledger/publication path. This is
      the production path a future registered cycle calls per identity
      (canonical lock around it — CANONICAL_INTEGRATION.md).

  spec_compiler.py    — the POSITIONAL ACCOUNTING-TEST compiler
      (encoding "POSITIONAL_ACCOUNTING_TEST_ONLY"): single-intent groups
      only; multi-intent/mixed-direction groups REFUSE
      (REFUSED_POSITIONAL_SCOPE). It proves runner accounting on one
      positionally-encoded trade; it is not a strategy timeline.

The runner files in exec/ are only ever modified by an explicit runner-
extension decision (wave-4 added the intent-mode engine inside
scored_runner_v2.py behind the intent_packet@1 schema; spec_packet@1
behavior is byte-unchanged and the 42-test exec suite stays green).
"""
