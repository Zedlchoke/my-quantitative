# PLAN — NFL-WINPROB-P2-RESELECT-PREP-V1 (owner option P2 successor: identical θ grid re-selected under the base-10 machinery of record, TRAIN-internal only)

- cycle_id: NFL-WINPROB-P2-RESELECT-PREP-V1 · asset: shared · ACTIVE_LIGHT ·
  budget max **3** scored cells (B0 / B1_STAR / C3θ*, consumed ONLY by a
  post-GO one-shot pass in a LATER round; this round consumes **0**) · GO
  phrase registered but NOT typed:
  **`GO NFL WINPROB P2 RESELECT PREP V1 SCORED PASS`** (owner-only, verbatim,
  fresh, at this cycle's own gate after A7).
- Owner authority 2026-10-09 (this chat): DECISION_PACKET_R3_MACHINE_TRANSFER
  option **P2** (machrem 12aa5306/c8d07bc5): one new registered cycle that
  re-runs the IDENTICAL preregistered θ grid {0,25,50,75,100} on the
  IDENTICAL 2000–2018 inner folds under the **base-10** machinery of record,
  freezes the winner BEFORE any 2019–2025 outcome read, then — later, only
  after its own gates + owner GO — runs its own 3-cell scored pass under the
  same gates. This round executes the re-selection + freeze and STOPS before
  every scored step and before the GO.
- Machinery law (from the audited R3 chain): the NG selection that picked
  θ=50 ran `arms.py 19dddd3f…` with the base-e link `sig((R_own−R_opp)/400)`
  (effective divisor ≈173.72), while the machinery of record — predecessor
  `elo.py e4183b6c…` port `nfl_winprob/elo.py`, reproduced at E1 — evaluates
  `1/(1+10^(−(R_home+HCA−R_away)/400))` (base-10, divisor 400). The two are
  never compared as the same measurement (estimand separation E1/E2/E3). The
  z-table (EPA→rating offsets; pure mean/sd, no link term) is
  machinery-INDEPENDENT and transfers; only the θ scalar and the link are
  machinery-conditional.

## Round tasks

1. **MACHINE CHECKS FIRST (all CONTROL, consume no scored cell):**
   (a) E1 reproduction re-run at this cycle's base using the byte-identical
   predecessor port (machrem data plane, PORT manifest re-verified): pooled RS
   LL 0.6407092590929282 and 7/7 per-season anchors within 1e-9 — FAIL ⇒
   **NOT_RUN_REPRODUCTION, halt everything**; (b) B0 constant re-derived
   (0.571399049390 home-win rate; pooled inner LL 0.683037) — link-free
   identity, must match the NG selection run exactly (same 5,057 rows, tie
   exclusions, folds); (c) z-table rebuilt from the pinned pbp 2000–2017
   parquets (574 (season,lineage) entries, boundaries 2001–2018) —
   determinism hash recorded; no link term by construction; (d) designed-null
   equivalence under base-10: C3 θ=0 ≡ B1* p_home stream **bit-for-bit**
   (max |Δp| = 0) before any other base-10 number is believed.
2. **BASE-10 SELECTION (TRAIN 2000–2018 only; heavy lock required):**
   port the NG selection machinery into this cycle's tree as a new module with
   ONE delta — the link function replaced by the base-10 form above, used
   identically for rating updates and the LL evaluation stream (diff cited in
   the artifact; no other line touched); re-run the IDENTICAL rolling-origin
   inner folds (warm replay 2000→s−1, evaluate s ∈ {2014..2018}) for B1* and
   C3 θ ∈ {25,50,75,100} (θ=0 is the null arm). Winner rule verbatim from
   PROTOCOL §6.1: lowest pooled inner LL subject to calibration slope in
   [0.85, 1.15]; tie-break fewer active parameters, then lexicographic config
   id; date-cluster bootstrap CIs (10,000, seed 20261008 inherited). Every
   evaluated config into a selection ledger (trial accounting). Hard load
   filters `SEASON_MAX_GAMES=2018` / `SEASON_MAX_PBP=2017` kept
   grep-auditable; ZERO reads of season > 2018 outcomes (assert + hook).
3. **FREEZE BEFORE ANY 2019–2025 READ:** `SELECTION_B10.json` (θ* value of
   record, margins vs neighbors, slope band, ledger digest) +
   `FREEZE_COMPARISON_B10.md` inheriting machrem FREEZE_COMPARISON.md gates
   verbatim (universe 1,865 non-tie RS 2019–2025 rows + POST separate, tie
   law, kickoff batch law, season-boundary law, metrics, paired ΔLL
   kickoff-date cluster bootstrap, SUPPORT/REFUTE predicates, claim cap) with
   a delta table: C3 slot re-paired to θ*, machinery of record = base-10
   declared, estimand separation stated. Only after the freeze commit may any
   replication-window number later be computed (separate round, post-GO).
4. Controller: integrate, A7 fresh-context at final HEAD (link-diff audit,
   null equivalence re-run, no-2019+ access, NG/walkfwd isolation byte-check,
   registry coherence) → OWNER_GO_PACKET → STOP.

## Exposure disclosure (binding language for every artifact)

2019–2025 is EXPOSED (both to the predecessor cycle and to the e-machine
pairing). Any future number computed on 2019–2025 under this cycle carries
**replication/process value only** — it can NEVER be fresh-mechanism evidence
for C3. New mechanism evidence for C3 is the **prospective 2026+ ledger**
owned by NFL-WINPROB-NG-SCORED-V1 (live cycle; READ-ONLY here; no backfill,
no re-forecast, cadence untouched; heavy-lock etiquette around its weekly
firing). 0.6407 and 0.65052 remain exposed anchors, never targets.

## Boundaries

$0; no network; no purchases; no accounts; no S1; no push/merge/rebase;
registry via researchctl CAS; calibration vocabulary only — no
PnL/betting/edge language; missing evidence = NOT_RUN_*; frozen artifacts and
ledgers of every other cycle (machrem, NG-SCORED, walkfwd, WNBA, soccer,
NBA…) read-only; handoff JSON `zcode_orch_v3_handoff@1` at each handoff_path.

## Worktrees / data

Integration `.worktrees/nfl-winprob-p2-reselect-prep-v1/integration` on
`orca/nfl-winprob-p2-reselect-prep-v1-integration`. Base SHA = this plan's
commit on main. Data (read-only): machrem port + derived
`~/.my-quantitative-data/nfl-machrem-v1/`; pbp
`~/.my-quantitative-data/nfl-ng-scored-v1/raw_pbp_2000_2017/`. No new bulk
downloads. Artifacts under `research/control/NFL-WINPROB-P2-RESELECT-PREP-V1/`.

## Terminal outcomes (negative-first)

**THETA_RESELECT_FROZEN_PENDING_OWNER_GO** (machine checks PASS, grid run,
θ* frozen, A7 PASS, GO not typed, 0 scored) |
**SELECTION_NEGATIVE_NO_THETA_BEATS_B1STAR_BASE10** (no grid point both
improves pooled LL and calibrates in-band → C3 slot-release recommendation
recorded for owner — P3-semantics; nothing scored; a valid negative) |
NOT_RUN_REPRODUCTION | NOT_RUN_RESOURCE_CONFLICT | BLOCKED_TOOLING |
BLOCKED_DATA | TECHABORT_*. The GO phrase is owner-only; agents never type or
paraphrase it; an early/paraphrased GO dies unconsumed.
