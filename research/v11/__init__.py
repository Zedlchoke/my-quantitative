"""V11 research modules (PLAN.md section 7, P1 lanes).

Lane A4 owns :mod:`research.v11.exact_arm_dryrun` -- the no-real-PnL
exact-arm dry-run and platform-safe QA preflight.  Nothing in this package
computes, persists or publishes a scored metric; every write is confined to
caller-provided temporary paths.
"""
