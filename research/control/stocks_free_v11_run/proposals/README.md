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

---

# V11 D1 lane A4 — filing-event reaction (axis 1, mandatory lane)

Cycle: STOCKS-FREE-V11 · Phase: D1 · Wave SHA: `ea668797b661dfa2c9d2b2799e46fe0f13f71820`
Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v11/integration` (branch `orca/stocks-free-v11-integration`)

(The section above belongs to lane A5; this A4 section is appended additively
because the lanes share this directory. A5's bytes above are untouched.)

## Lane scope

A4 is a blind proposal lane: exactly two outcome-blind proposals on the
filing-event reaction axis — REACTION-form event-time books tied to the
V11-E1 evidenced `(cik, first_avail)` arrival stamps, trading the post-arrival
path at arrival-anchored decision instants (NOT characteristic ranks at a
periodic grid — the veto-entry-10 form is avoided by construction). The
lane-mandatory sham-event placebo is the CONTROL class in both families:
event dates shifted to hash-seeded clear non-filing windows, matched 20-bar
lengths, identical book arithmetic. Family falsification rule, frozen:
if the sham placebo reproduces the anchor at >= 0.5x expectancy same sign,
the family DIES — a reaction mechanism must beat its own placebo calendar
(V5 lesson imported).

- `a4_event_H1.json` | SFV11-A4-H1 | Post-arrival drift continuation: at
  every in-universe arrival, long/short the sign of the 5-bar
  sector-residual initial reaction, bar-6 entry to bar-20 exit,
  sector-neutralized weights; tests incomplete-first-estimate diffusion
  (limited attention, gradual diffusion, PEAD analog without consensus data).
- `a4_event_H2.json` | SFV11-A4-H2 | Amendment-arrival underreaction:
  identical continuation arithmetic restricted to amendment arrivals
  (chain position >= 2, PIT stamp-time rank within the filer-period group;
  no revision value read anywhere), with a strict ordering falsifier against
  the first-vintage neighbour (attention to marginal disclosures).

## Clocks cited (P2 verbatim)

| File | Clocks cited |
|---|---|
| `a4_event_H1.json` | `V11-E1-FILING-EVENT` (verbatim tuple) |
| `a4_event_H2.json` | `V11-E1-FILING-EVENT` (verbatim tuple); `V11-E2-CHAIN-DEPTH` / `V11-E3-AMEND-CADENCE` deliberately NOT cited — `last_avail` stamps would be look-ahead at mid-chain arrivals (declared in-file) |

Neither file cites `deadline_distance` (DATA_BLOCKED_VALID, P-1); the 69
unpriced-entity events are NOT_FUNDED_COVERAGE and never booked; no carried
V10 clock is cited.

## Identifiability gates declared (pre-selection, PIT + price availability only)

- Both: anchor-vs-control pooled Spearman rho < 0.95 on the aligned
  (entity, calendar-date) grid + sham-control runnability floors
  (>= 30 scored control decisions overall, >= 5 per fold; a sham that cannot
  run is a design failure, not a pass).
- H2 additionally: anchor/neighbour chain-position partition non-degeneracy
  (per-arm sample floors), else BLOCKED_DATA_OR_SELECTION.

## A4 self-check (run at this SHA, before commit)

- [x] Both files parse as valid JSON (`json.load`, exit 0, venv interpreter).
- [x] Schema `stocks_free_v11_run/d1_proposal@1`; cycle/phase/lane/worktree/branch/wave_sha/hypothesis_id/agent correct.
- [x] Exactly three arms each (anchor / neighbour / control).
- [x] Control arm IS the sham-event placebo (matched 20-bar clear windows, identical arithmetic, 1:1 hash-seeded).
- [x] Clocks cited verbatim with {clock_id, observable, available_at, max_age_days} tuple fields; max_age_days 800 everywhere.
- [x] No outcome-shaped field anywhere; no threshold/parameter grid; frozen_thresholds + no_parameter_grid_declaration present in each file.
- [x] Every gate has a failure interpretation written now; margin-to-fail expectations declared per gate (P-2).
- [x] Eleven-entry veto set addressed entry-by-entry in novelty_declaration; D2 pooled |rho| <= 0.20 declared measured, never argued.
- [x] Infeasibility declared with reasons (4,270 zero-window events; 69 unpriced-entity events; 737 sub-20-bar events; 19 event-saturated entities -> matched-subset placebo; 1,272 NOT_DEAD_NAME_ALIVE events; H2 mid-chain look-ahead trap; H2 unmeasured partition counts).
- [x] outcome_blind_attestation signed on the wave SHA in each file; V10 never-scored proposal files deliberately NOT read (blind convergence preserved).

## A4 off-limits / untouched

No outcome files accessed (none exist). A1-owned files untouched. A5's
`a5_process_H1.json` / `a5_process_H2.json` and A5's README section were not
modified by this lane (this section is additive). Only this lane's three
files (`a4_event_H1.json`, `a4_event_H2.json`, this README) are staged by
name; no push.
