# PLAN — WSL-WINPROB-SCORED-PREP-V1 (scored successor PREP: seasonal walk-forward, WSL-fresh arms, exposure-audited; $0; STOP before Owner GO and before any scored OOS)

- cycle_id: WSL-WINPROB-SCORED-PREP-V1 · asset: shared · ACTIVE_LIGHT ·
  budget max **3** scored cells (B0 / B1_ELO_DAVIDSON / B2_HCA_REFIT,
  consumed ONLY by the post-GO scored pass; this round consumes **0**) · GO
  phrase registered, NOT typed:
  **`GO WSL WINPROB SCORED PREP V1 SEASONAL RUN`** (owner-only, verbatim,
  fresh, at this cycle's own gate after A7).
- Owner authority 2026-10-09 (second round, this chat): prepare the scored
  successor now — complete seasonal walk-forward protocol, WSL-specific
  baseline + Elo/Davidson arms, trial budget, falsification criteria,
  day-batch D−1 law, team_id law, two-awarded-matches law, anomalous-row
  law; audit per-season EXPOSURE before any OOS choice; never call 2024–25
  a clean holdout; freeze + independent audit of BOTH the real path and the
  refusal path; STOP before Owner GO and before every scored OOS. Odds stay
  **NOT_RUN_ODDS** (inherited verdict); NO paper-trade hookup (no odds, no
  valid kickoff times).
- Inheritance (frozen pins from WSL-WINPROB-DISCOVERY-PREP-V1 @ 4c4c39bc):
  ewf-database snapshot `~/.my-quantitative-data/wsl-winprob-discovery-prep-v1/ewf-database/`
  git HEAD **ffd155623262b597e0d8e82fef879227f2035c76** (CC BY-SA 4.0
  verified verbatim; internal non-shared research unencumbered); WSL tier-1
  1,335 matches / 15 seasons 2011–2024/25; kickoff time + venue ABSENT ⇒
  date-granular laws only; 15 multi-named team_ids; 2 awarded WSL rows
  (0-0 + result flag + note); anomalous row `M-2024-2025-1-001-M`
  (2024-04-30, next row 2024-09-20); same-day max 6; men's parameters
  (K=48/ν=0.6/HCA=65) EXCLUDED by law.

## Per-season EXPOSURE AUDIT (before any OOS choice — owner order)

Measured classes, recorded in EXPOSURE_AUDIT.md and binding on every claim:
- **2020-21..2023-24**: B0-fit EXPOSED (DISCOVERY computed the train shares
  (H 0.429924 / D 0.170455 / A 0.399621) on these 528 matches) ⇒
  TRAIN_INTERNAL by design.
- **ALL seasons 2011–2024/25**: standings + match-count EXPOSED (DISCOVERY
  QC read both for every season) ⇒ **no season is a clean holdout**.
- **2024-25**: additionally the DISCOVERY's descriptive "held out" — owner
  law: **NOT a clean holdout**, never called one; its use in the scored OOS
  is under the exposure disclosure below, never as untouched evidence.

## Frozen design (pre-registered in this plan; freeze packet may tighten, never loosen)

- Identity: `team_id` is the rating identity (renames/relocations fold;
  Millwall→London City merge handled as ONE team_id lineage, documented).
- Data laws: **awarded matches (2 rows)** — excluded from targets AND
  features, counts disclosed; **anomalous row M-2024-2025-1-001-M** —
  excluded from targets AND features, count disclosed, documented; day-batch
  **D−1**: all date-D matches predicted from the end-of-(D−1) snapshot,
  ratings update after day close (kickoff times absent — nothing finer is
  claimable); shootout/penalty laws N/A at tier-1 league format (no KO ET in
  corpus rows — asserted at load, fail-closed if violated).
- Windows: warmup/burn-in seasons **2011–2018/19** (ratings only, never
  scored) · train-internal selection **2019-20..2022-23** (season blocks
  2019-20 / 2020-21 / 2021-22 / 2022-23, rolling) · chrono scored OOS
  **2023-24 + 2024-25** (~264 matches; pooled + per-season metrics).
- Arms (budget exactly 3): **B0** constant 3-way recomputed on train seasons
  only (value of record re-frozen at freeze; DISCOVERY value cited) ·
  **B1_ELO_DAVIDSON** K∈{8,12,16,20,24} × ν∈{0.30,0.41,0.55,0.70} ×
  HCA∈{0,12,25,40} selected train-internal (block-average LL, MIN_VALID 100
  per block) · **B2_HCA_REFIT** HCA co-selected on the same grid under the
  same rule (K,ν pinned to B1's winner). Designed nulls (K=0 ≡ B0-mechanics,
  HCA=0 equivalence) are CONTROL arms, never scored cells.
- Metrics + falsification (preregistered): pooled + per-season multi-class
  LL primary; RPS, Brier macro, argmax accuracy (DESCRIPTIVE label only),
  decile calibration; MIN_VALID 100 per eval season, 200 pooled; an arm
  FAILS to beat B0 unless pooled ΔLL ≤ −0.01 nats AND ΔRPS ≤ −0.005; a
  negative outcome (REJECT_ALL) is a valid terminal.
- Engine law: seal + GO-token + registry-consumption gate on the scored
  entrypoint (refuses without all three); ledger `wsl_scored_ledger@1`
  append-only sha-chain, no outcome columns pre-GO, real ledger file created
  ONLY post-GO; synthetic corpora only this round.
- Exposure disclosure (binding language): the scored OOS result is
  **partially-exposed-window evidence** (standings/count level on every
  season; B0-fit level on train seasons) — it can support a Stage-A-style
  candidate verdict on this corpus but can NEVER be called untouched-OOS
  evidence; 2024-25 is never "clean".

## Round tasks (this round consumes 0 scored)

1. L-ENGINE — implement the engine + laws on the pinned corpus schema;
   port + extend the DISCOVERY synthetic battery (awarded/anomalous
   exclusion, D−1 day-batch, season boundary, team_id rename continuity,
   3-way normalization, strict as-of, fail-closed, ledger tamper) — all
   synthetic; sandbox dry-run; NO real scored rows.
2. L-FREEZE — EXPOSURE_AUDIT.md; FREEZE_PACKET.md (windows, grids, budgets,
   falsification, MIN_VALID, seed, B0 value of record, claim caps,
   NOT_RUN_ODDS restatement, no-paper-trade law); arm_config digests after
   the train-internal selection run (journaled, S0-by-design); OWNER_GO_PACKET.
3. L-A7 — independent fresh-context audit of the REAL path (hash chain,
   laws, selection ledger, isolation) AND the REFUSAL path (no token →
   refuse; token without registry consumption → refuse; seal rehearsal).
4. Controller integrates; registry AWAITING_OWNER_GO; STOP.

## Boundaries

$0; no network needed (pinned clone only); no purchases/keys; no S1; no
push/merge/rebase; registry via researchctl CAS; NOT_RUN_ODDS stands — no
paper-trade hookup, no order/threshold changes anywhere; other cycles
untouched (incl. WSL DISCOVERY artifacts read-only); heavy lock serialized,
never kill foreign workers; calibration vocabulary only — no betting/edge
claims from accuracy or log loss.

## Worktrees / artifacts

Integration `.worktrees/wsl-winprob-scored-prep-v1/integration` on
`orca/wsl-winprob-scored-prep-v1-integration`. Data plane
`~/.my-quantitative-data/wsl-winprob-scored-prep-v1/`. Artifacts under
`research/control/WSL-WINPROB-SCORED-PREP-V1/`.

## Terminal outcomes (negative-first)

**PRELAUNCH_READY_PENDING_OWNER_GO** (all lanes + A7 PASS real & refusal
paths, GO not typed, 0 scored) | PRELAUNCH_BLOCKED_<gate> |
SELECTION_NEGATIVE_INSUFFICIENT_DATA (train-internal selection cannot meet
MIN_VALID — honest stop, nothing scored) | BLOCKED_LICENSE |
NOT_RUN_* | TECHABORT_*. An early/paraphrased GO dies unconsumed.
