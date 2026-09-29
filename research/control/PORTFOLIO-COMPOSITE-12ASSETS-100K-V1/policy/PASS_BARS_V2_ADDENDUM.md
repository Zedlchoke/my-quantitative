# PASS_BARS_V2_ADDENDUM — A1 integration (2026-09-29, post-A7-prereview)

Author: A1 (integration authority), after Lane P's remediation agent hit
its usage limit. This addendum pins the three items the A7 prereview found
unpinned (D4/D7 sub-checks); it extends `PASS_BARS_V2.md` and is
subordinate to it wherever they overlap. Nothing here changes any
previously frozen bar semantics.

## A-1. P4 body (the bar defined by the V2 §9 matrix rows P4a/b/c)

**Claim under test:** the eligibility layer's value is not reproducible by
a clock (cadence alone), by inversion (being wrong on purpose), or by
stale information (last fold's decision).

Realization laws: B5 CLOCK-GATE, B6 INVERTED, B7 LAGGED per V2 §1 (each
re-runs the SAME legs, kernel, tier, calendar; only the named layer
changes). Quantities pooled over test folds, governing tier ×1.0.

```
P4a = PASS iff  netPnL(P) > netPnL(B5) AND maxDD(P) < maxDD(B5)
P4b = PASS iff  netPnL(P) > netPnL(B6) AND maxDD(P) < maxDD(B6)
P4c = PASS iff  netPnL(P) > netPnL(B7) AND maxDD(P) < maxDD(B7)
P4  = PASS iff  P4a AND P4b AND P4c
```

Fail close-codes: `POLICY_NO_INCREMENTAL_VALUE` sub-tags `P4_B5_CLOCK` /
`P4_B6_INVERTED` / `P4_B7_LAGGED`. Missing baseline → `NOT_RUN_BASELINE_B5`
(B6/B7 likewise). Edge cases: ties FAIL (E-Law 4); a policy with duty
0 or 1 degenerates B5 into B1 — then P4a reduces to P1 and still governs
(state this in the Stage-C report, do not skip it); B6 of a never-OFF
policy is a never-trading arm (netPnL=0) — P4b then reduces to the P1-B0
positivity requirement and still governs; B7's first test fold uses the
last TRAIN fold's eligibility state (frozen input, no leakage — it is the
point of the control).

## A-2. CSCV cluster accounting and dedup — the two edge rules pinned
(skeptic F-11, A7 D7 sub-check)

1. **Cluster-adjusted effective trial count.** The discovery ledger's N is
   replaced by `N_eff = Σ_clusters n_c²/Σ_c n_c·w_c` implemented as the
   simple union rule: every preregistered FAMILY (census family × arm-shape
   grouping, e.g. the 9 VOLPROF candidates = ONE cluster) contributes ONE
   effective trial to `E[max]` regardless of its internal row count;
   cluster membership is frozen at Stage-B freeze and written into each
   ledger row's `cluster_id`. `N_eff` (not raw N) enters the P5a `E[max_N]`
   construction; BOTH N and N_eff are reported with P5a.
2. **Dedup rule.** Two ledger rows with identical `arm_config_digest` AND
   identical `data_snapshot_digest` are ONE trial (byte-identical arms);
   the CSCV matrix keeps the first row and drops duplicates with a
   counted, disclosed exclusion list. Near-duplicate arms (same cluster,
   different digests) are NOT deduped — they are priced by the cluster
   rule above.

## A-3. Switch-cost dual-book reconciliation (skeptic F-12 disposition)

The ONOFF_LEDGER (planning estimate: switch costs at the measured cell
p50 of the intended fill hour) and the journal's realized crossings
(bar-quoted, spread-once) are TWO BOOKS WITH ONE AUTHORITY: **the
realized journal numbers govern every Stage-C report and every PASS bar
input; the ONOFF_LEDGER estimate exists only for pre-trade deferral
decisions (L6 cost guard) and is labeled ESTIMATE_CELL_P50.** At each
fold close, the ONOFF ledger row must carry the reconciliation residual
`realized_switch_cost − estimated_switch_cost` for that leg-fold; a
trailing |residual| > 50% of the estimate for ≥2 folds forces the estimate
schedule to re-pin to realized p50 at the next fold boundary (mechanical
re-pin, no judgment), and the re-pin is journaled.

## A-4. Ladder v1 reconstructibility (skeptic F-18 disposition)

Ladder v1 (session 1, novelty-gated law) was superseded in place by v2
before any commit — the working tree is uncommitted by design. The v1
ladder's full logic and counts are preserved in
`eligibility/LADDER_V1_APPENDIX.md` (verbatim from the session-1 builder,
reconstructed by A1 from the session-1 artifacts) so the package is
self-contained without git history. v1 remains dead law; nothing
downstream consumes it.
