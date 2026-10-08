# PLAN — NFL-WINPROB-MACHREM-V1 (machinery remediation BEFORE any tune, $0, CONTROL-first)

- cycle_id: NFL-WINPROB-MACHREM-V1 · asset: shared · ACTIVE_LIGHT, budget max
  **3** scored cells (B0 / B1_STAR / C3, consumed ONLY by the post-GO one-shot
  pass) · GO phrase registered but NOT typed:
  **`GO NFL WINPROB MACHREM V1 SCORED PASS`** (owner-only, verbatim, at this
  cycle's own gate after A7).
- owner authority 2026-10-08 (second round, this chat): fix the
  MACHINERY_SUSPECT before ANY tune. Separate estimands E1 (predecessor
  machine), E2 (NG machine), E3 (successor comparison) — the three LLs are
  never compared as if they were the same measurement. Byte-identical port of
  predecessor code + data; reproduce anchor B1-c **0.6407092590929282** and all
  7 per-season anchors within **1e-9** — a CONTROL machinery check, never a
  model-optimization target; failure ⇒ **NOT_RUN_REPRODUCTION** halt. Outcome-
  blind probe to localize the FIRST game where the predecessor and NG streams
  differ; prove the implementation cause in a bridge table. NEVER choose a
  modification because it moves any LL toward 0.6407. Only after bridge +
  designed-null + twin gates may the B0/B1_STAR/C3 comparison be PREPARED
  (universe, tie law, playoff law, metrics, CI, 3-cell budget, SUPPORT/REFUTE
  frozen BEFORE any C3 LL is read). 2019–2025 is EXPOSED: replication/process
  language only. The NG prospective 2026+ ledger belongs to the live cycle:
  READ-ONLY, no backfill, no re-forecast. Scope this round: plan → registration
  → implementation/control probes (allowed) → freeze → synthetic rehearsal →
  independent A7 → decision packet. **STOP before every scored C3/OOS step and
  before the owner GO.**

## Inheritance (frozen pins from SPORTS-WINPROB-TUNE-PREP-V1 TERMINAL a7694a70; re-measured at bootstrap)

- `lanes/L_NFL/REMEDIATION_PACKET.md` (216 lines, binding verbatim): estimands
  §1; S0 self-anchor protocol §2 (six predecessor files sha-pinned: elo.py
  e4183b6c…, export_features.py a6b74a3b…, build_dataset.py b4642f70…,
  run_evaluation.py 1dac3f5f…, protocol.py eb88a43e…, features.py 71b4ad6d…;
  code freeze 91dcff14…; data vintage f1e8fe78…; derived pins f7909fa5… /
  4ee2175e… / 977a43e2…); bridge §3 (one OPEN axis: B1 walk implementation);
  probes §4 (P1 stream equivalence outcome-blind; P2 axis toggles ATTRIBUTION
  ONLY; designed null θ=0 ≡ B1_STAR bit-for-bit; time-shuffled twin C3_TWIN
  c86b3710… seed 20261005; anchor-status ban); RC2 gates §5; budget §6
  (3 scored + CONTROL probes + 1 frozen mechanism hypothesis = C3's offseason
  EPA prior); evidence §7; frozen-input register §8.
- E2 exposed diagnostic 0.6505203624255933 (never a baseline to beat); halted
  walkfwd ledger a94830e1… (7,840 rows) read-only; NG weeks 5–7 chain 67e89b2e…
  byte-unchanged; MACHINERY_DIFF_TABLE.md (15 axes) and EXPOSURE_TABLE_NFL.md
  inherited.
- Exposure law: 2000–2018 TRAIN_INTERNAL (selection territory); 2019–2025
  RETROSPECTIVE_WALK_FORWARD (replication/process ONLY); 2026+ prospective
  owned by NFL-WINPROB-NG-SCORED-V1 (read-only).

## Round tasks

1. **L-REPRO** — S0 SELF-ANCHOR + probes (all CONTROL, consume no scored cell):
   (a) byte-identical port of the six predecessor files + PORT manifest (any
   byte difference = BLOCKED_TOOLING); (b) rebuild the predecessor data plane
   from its own vintage (f1e8fe78…) with derived outputs re-hashed against the
   frozen pins (mismatch = BLOCKED_DATA); (c) reproduction run restricted to
   REPORTING (predecessor verdict predicates NOT re-evaluated): pooled RS LL
   and 7/7 per-season anchors each within 1e-9, fold census equal — **FAIL ⇒
   NOT_RUN_REPRODUCTION, halt everything**; (d) P1 stream-equivalence probe:
   run BOTH walks (P `run_elo` and N `replay_elo`, constants K=40/HCA=0/γ=2/3/
   μ=1500) over the same completed-rows input, outcome-blind (no outcome join,
   no LL) — report the FIRST game in kickoff order with |Δp| > 1e-12 (season,
   batch, lineages) + final max |Δp|; (e) P2 axis toggles for ATTRIBUTION only
   (candidate families: batch update arithmetic order, reversion timing,
   warm-up construction, lineage lookup) — each toggle: does P1's first
   divergence disappear? Hard ban: no probe result selects machinery because
   it scores better; (f) complete the bridge table (OPEN axis → attributed
   cause; RC2-b branch (i) close-with-1e-9-hit or (ii) predict-then-verify —
   the branch choice recorded BEFORE any C3 number exists).
2. **L-FREEZE** — comparison freeze (parallel to L-REPRO; disjoint files):
   FREEZE_COMPARISON.md verbatim-consolidating REMEDIATION_PACKET §4–§6:
   universe (1,865 non-tie RS 2019–2025 rows + POST separate), tie law
   (S=0.5 stream, excluded from scoring, counts disclosed), kickoff batch law,
   season-boundary law, metrics (pooled + per-season LL primary; Brier,
   reliability, calibration slope band), paired ΔLL kickoff-date cluster
   bootstrap 10,000, seed frozen now (20261008) pre-outcome, SUPPORT/REFUTE
   predicates verbatim, twin law, claim cap (RETROSPECTIVE_WALK_FORWARD
   process-discipline only), budget 3 scored + CONTROL probes, C3_TWIN
   diagnostic-only; OWNER_GO_PACKET.md (exact phrase; what the one post-GO
   pass runs and can never do); exposure citations.
3. **SYNTH (within L-REPRO)** — synthetic rehearsal of the successor
   comparison harness on FAKE games only: identical-game-set assertion,
   designed-null θ=0 ≡ B1_STAR bit-for-bit, twin determinism, one-shot
   scoring shape, ledger hash-chain tamper detection, missing-input
   fail-closed. ZERO real C3/outcome numbers.
4. Controller: sequential cherry-pick → freeze commit → **A7** fresh-context
   at final HEAD (port byte-equality, reproduction evidence, probe evidence,
   no-C3-number assertion, NG/walkfwd isolation byte-check, registry) →
   DECISION_PACKET.md → STOP.

## Boundaries

$0; no network; no accounts; no S1; no push/merge/rebase; registry via
researchctl CAS; heavy lock machine-wide (bounded recheck ≥60s; never kill
foreign workers; NG cadence fires 00:00 local — never contend past it);
calibration vocabulary only — no PnL/betting/edge; **0.6407 and 0.65052 are
exposed anchors, never targets**; the live NG cycle, walkfwd halted artifacts,
and every other cycle are read-only citation-only; missing evidence =
NOT_RUN_*; handoff JSON `zcode_orch_v3_handoff@1` at each handoff_path.

## Worktrees / branches

Integration `.worktrees/nfl-winprob-machrem-v1/integration` on
`orca/nfl-winprob-machrem-v1-integration`; lanes `…/lane-repro`, `…/lane-freeze`
on `orca/nflmr-lane-repro`, `orca/nflmr-lane-freeze`. Base SHA = this plan's
commit on main. Data plane: `~/.my-quantitative-data/nfl-machrem-v1/` (PORT
manifest + rebuilt derived artifacts; no new bulk downloads).

## Artifacts

`research/control/NFL-WINPROB-MACHREM-V1/` in each worktree: `DISPATCH/`,
`handoffs/`, `lanes/{L_REPRO,L_FREEZE,A7}/`; at integration: `PORT_MANIFEST.json`,
`REPRODUCTION_RESULT.json` (E1), `DIVERGENCE_PROBE_RESULT.json` (P1/P2),
`BRIDGE_TABLE.md` (completed), `FREEZE_COMPARISON.md`, `OWNER_GO_PACKET.md`,
`SYNTH_REPORT.md`, `A7_PRELAUNCH_VERDICT.md`, `DECISION_PACKET.md`.

## Terminal outcomes (negative-first)

**REMEDIATION_PRELAUNCH_PENDING_OWNER_GO** (E1 reproduced, bridge
closed-or-re-derived, freeze + synth + A7 PASS, GO not typed, 0 scored) |
**NOT_RUN_REPRODUCTION** (E1 anchor not reproduced within 1e-9 — honest halt,
remediation needs a new round) | BLOCKED_TOOLING | BLOCKED_DATA | NOT_RUN_* |
TECHABORT_*. The GO phrase is owner-only; agents never type or paraphrase it.
