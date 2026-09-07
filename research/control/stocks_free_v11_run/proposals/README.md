# V11 D1 lane A5 — amendment-process structure (axis 2)

Cycle: STOCKS-FREE-V11 · Phase: D1 · Wave SHA: `ea668797b661dfa2c9d2b2799e46fe0f13f71820`
Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v11/integration` (branch `orca/stocks-free-v11-integration`)

## Lane scope

A5 is a blind proposal lane: exactly two outcome-blind proposals on the
amendment-process axis, conditioned on the PROCESS only — cadence, chain
shape, depth, inter-arrival structure. Corrected VALUES (direction, magnitude,
breadth of revision) are never signal inputs anywhere; the V10 direction/breadth
USAGE FORMS are veto entries and are addressed head-on in each proposal's
`novelty_declaration`. Neither proposal cites `V11-E1-FILING-EVENT`,
`V10-R1-REV-DIR`, `V10-R2-REV-MAG`, the V10 T-clock z-forms, or
`deadline_distance` (DATA_BLOCKED_VALID, P-1).

## Files

| File | Hypothesis | Mechanism (one line) | Clocks cited (P2 verbatim) | Control (falsification) |
|---|---|---|---|---|
| `a5_process_H1.json` | SFV11-A5-H1 (CADENCE-LATENCY) | Long punctual-process filers, short vintage-patch-latent filers: share of as-of amendment chains re-addressed > 460d (pooled cadence p90) after their certified vintage predicts underperformance. | V11-E3-AMEND-CADENCE, V11-E2-CHAIN-DEPTH | Shuffled-chain control: within-sector marginal-preserving permutation of late_share (seed 20260907) — preserves every distributional artifact, destroys only the entity-value link; kills the "just holds small/old names" explanation. |
| `a5_process_H2.json` | SFV11-A5-H2 (CHAIN-SHAPE) | Short targeted-repetition filers, long broad-sweep filers: field-concentration Herfindahl of as-of vintage chains (same fields patched repeatedly = unresolved recurring problem) predicts underperformance vs one-time broad cleanups. | V11-E2-CHAIN-DEPTH, V11-E3-AMEND-CADENCE | Volume-and-cardinality-matched geometry-null control: per-entity field-label permutation preserving N and F exactly (seed 20260907) — kills the "concentration is just amendment volume" explanation. |

Both: per-sector net-zero tercile books on the death-inclusive cohort
(410 ALIVE_EVIDENCED + 1,550 DEAD_PRICE_CONFIRMED; exit-at-last-close; no
survivorship re-substitution), inherited 21-session grid (63+21k per fold over
S0_FOLD_1/2/3), band costs A/B/C 10/15/25 bps per side (stress x2 on booked
PnL, linear in fills, charged once per fill), warmup 0, three arms each.
Book-form provision 2.1 deliberately NOT invoked (declared rationale inside
each proposal: per-sector net-zero already neutralizes sector without ETF-leg
costs); ETF-share gate <= 0.50 declared and expected 0.00; SPY-excess
positivity declared binding.

## Self-check (run at this SHA, before commit)

- [x] Both files parse as valid JSON (`json.load` exit 0).
- [x] Schema `stocks_free_v11_run/d1_proposal@1`; cycle/phase/lane/worktree/branch/wave_sha/hypothesis_id/agent correct.
- [x] Exactly three arms each (anchor / neighbour / control); the third object key is a note, not an arm.
- [x] Control is a runnable falsification control under evidenced semantics (permutation of measured exposures / evidenced group keys; P-3 recompute declared).
- [x] NO rev_dir/rev_mag signal usage anywhere: the strings appear ONLY inside veto/novelty/leak-scan prose; exposure formulas load stamps/counts/keys only (I-phase leak scan declared).
- [x] Clocks cited verbatim as {clock_id, observable, available_at, max_age_days} tuples from p2_v11_coverage_first.json; max_age_days 800 everywhere; deadline_distance never cited.
- [x] No outcome-shaped fields (no returns/PnL/scored metrics; margin_to_fail entries are declared anticipations).
- [x] No parameter grids (frozen_thresholds + no_parameter_grid_declaration in each file).
- [x] Every gate carries a failure_interpretation written now.
- [x] pre_selection_identifiability_check gates measurable from PIT panel + price availability only.
- [x] outcome_blind_attestation signed on the wave SHA in each file.
- [x] V10 A4/A6 never-scored proposal texts deliberately NOT read (blind convergence preserved).

## Off-limits / untouched

No outcome files were accessed (none exist). A1-owned files (event_log.jsonl,
first_report.md, run_contract.json, p2/p3 files, incidents.md,
worktree_manifest.json) untouched. Only the three files in this directory are
staged by name; no push.
