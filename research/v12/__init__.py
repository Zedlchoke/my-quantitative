"""V12 factory helpers (P1 lane A2 -- publication and ledger hardening).

Modules:

* :mod:`research.v12.accounting`     -- zero-position publication guard,
  observed-once refusal accounting, replay idempotence and the
  family-contract cell guard over the portable V12 ledger package
  (``research/control/v12_run/ledger_package/schema.json``).
* :mod:`research.v12.ledger_transfer` -- portable ledger transfer: verify a
  ``transfer_manifest.json`` (recomputed sha256 per file, fail closed) and
  regenerate one from a ledger path for host migration.

This lane computes no PnL and touches no family strategy code.
"""
