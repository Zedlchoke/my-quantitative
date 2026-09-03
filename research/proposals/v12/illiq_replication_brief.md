# V12 ILLIQ replication brief — A12-V12-ILLIQ-REPLICATION (frozen)

Exact-mechanism replication of the V11 near-miss `A8-V11-ILLIQ-AMIHUD`
(12/13 gates PASS; sole failure: largest positive-fold share 0.705496856297
> frozen 0.50). Identity, arms, schedule, costs, stress and ALL frozen gates
are inherited unchanged from the V11 family spec
(`research/control/v11_run/selection_freeze_specs/A8-V11-ILLIQ-AMIHUD.json`):

- anchor `ILLIQ-REPL-28D-W`: 28d mean daily Amihud, weekly Monday stamps,
  long illiquid / short liquid quintiles, BTC-beta-neutral, 7d holding;
- neighbour `ILLIQ-REPL-56D-W`: 56d Amihud, otherwise identical;
- control `ILLIQ-REPL-28D-W-INV`: sign-inverted anchor (falsification:
  positive after-cost spread destroys the mechanism).

Only two things differ from V11: (1) the preregistered non-overlapping S0R
window `2024-08-22T00:00:00Z..2025-08-21T00:00:00Z`; (2) the corrected
drop-one-symbol diagnostic (largest realized |weight| held symbol,
deterministic tie-break — L-V11-7 repair).

**Window status: `V12_ILLIQ_REPLICATION_BLOCKED_DATA`.** A3 verified the
preferred S0R window is NOT locally covered (14/20 symbols missing window-head
bars; warmup unsatisfiable at the window head — earliest locally-servable 28d
stamp 2024-09-23 vs first stamp 2024-08-26; 13/20 symbols missing funding
head). Per plan: no download, no window substitution; the three ILLIQ slots
stay unused. Unblocking requires a new owner-authorized data remediation.

Preregistered explanatory question (diagnostic only): did the V11 fold
concentration arise from a single favorable regime such that the same sign
and robustness do not replicate in the earlier window?

The replication does not pass merely by being positive: it must pass the same
frozen gates that rejected V11, including concentration <= 0.50. The 0.50
gate is NOT lowered; the 28D/56D/inverted-control mechanism is NOT changed.
