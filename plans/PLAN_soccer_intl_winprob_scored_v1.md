# PLAN — SOCCER-INTL-WINPROB-SCORED-V1 (historical 3-way scored successor, PREPARED-THEN-STOPPED BEFORE OWNER GO)

- cycle_id: SOCCER-INTL-WINPROB-SCORED-V1 · asset: shared · budget **0/3**
  (arms B0 + B1 + V1_HCA_REFIT; budget consumed only by post-GO scored
  computation) · registered 2026-10-07.
- owner authority 2026-10-07 (this chat): authorization to open EXACTLY ONE
  historical scored successor to the TERMINAL SOCCER-INTL-WINPROB-PREP-V1
  (27bb57f2), fully prepare it, and **STOP BEFORE THE OWNER'S OWN GO**. This
  is registration/deployment/freeze/A7/dry-run authority. It is explicitly
  NOT a typed GO: **no real OOS metric may be computed before the owner's
  fresh GO** at this cycle's own gate; no held-out numbers; no retrospective
  PnL; no betting language (probabilities and calibration metrics only).
- GO phrase (REGISTERED_NOT_CONSUMED, typed ONLY by the owner, verbatim,
  fresh, at this cycle's gate):
  **`GO SOCCER-INTL WINPROB V1 SCORED`**

## Owner-frozen scope decisions (supersede any PREP open item)

- PRIMARY target: 3-way home/draw/away on the corpus home label, 90/120-min
  recorded score per the PREP freeze, over the FULL universe INCLUDING
  friendlies. Friendly vs competitive are **pre-registered reporting
  slices** — both reported, neither replaces the primary, no universe/arm
  re-choice after OOS.
- Neutral flag ⇒ HCA=0 exactly per law. V1 (venue-neutral / HCA-refit) is
  an ARM within the frozen trial budget — never a replacement of primary.
- B0 vector fixed at the PREP freeze value of record:
  **(0.495584, 0.231516, 0.272900)** on 21,627 exclusion-clean train rows.
- B1 Elo/Davidson: K×ν selected ONLY on train 1951–2000 via the frozen
  rolling-fit protocol (blocks 1961/71/81/91); warmup 1872–1950; chrono OOS
  2001–2022; held-out 2023+ UNTOUCHED and unopened.
- Data law: exclude exactly the one contradictory duplicate (Tahiti–New
  Caledonia 1974-02-17) from features and targets; day-D features use only
  results with date <D; the whole date-D batch is predicted from the D−1
  snapshot; rating updates after day close; kickoff times NEVER fabricated;
  shootout winners never modify the target.

## Frozen inputs (pins)

- corpus: `~/.my-quantitative-data/soccer-intl-winprob-prep-v1/corpus/results.csv`
  sha256 **df35268f8fc341ff7fb93d448b4e40356676ac35300a6b4461fd199a99ac1514**
  (49,547 rows; shootouts.csv + former_names.csv same snapshot; CC0-1.0).
- PREP freeze packet: DISCOVERY/PREP integration tree at 27bb57f2,
  `research/control/SOCCER-INTL-WINPROB-PREP-V1/FREEZE_PACKET.md`
  (sha256 5b0e62bbeb6f3b0e…, incl. ERRATA §) + TERMINAL_REPORT (b1ec755c…) +
  4 handoffs. Splits/metrics/budget/ordering law are inherited verbatim.
- Identity: IDENTITY_CROSSWALK from PREP L-DATA (28 renamed entities).
- Seed: 42 (B0 null-test shuffle; any stochastic step must derive from it
  and be recorded).

## OOS seal design (the heart of "prepared then stopped")

The engine carries a hard seal: every pre-GO invocation passes
`--sealed-through 2001-01-01`; the loader raises `SEALED_WINDOW_VIOLATION`
on any row dated ≥2001-01-01 (identity counting of the sealed window is
done only from the PREP QC numbers, not by re-reading sealed outcomes).
The scored entrypoint additionally requires BOTH (a) a GO token file whose
content hash is recorded in the ledger genesis, and (b) the registry row for
this cycle showing the GO phrase consumed — otherwise it refuses. A7 must
rehearse the refusal (no token → refuse; token without registry consumption
→ refuse) and verify no code path bypasses the seal. Held-out 2023+ rows are
carried through identity counting only in the freeze docs, never scored in
the post-GO primary run (they are a future decision).

## Trial budget (3 arms, frozen; no additions without a new plan)

1. B0 — constant vector above, no fit.
2. B1 — Elo/Davidson (init 1500; Davidson ν; HCA 65 home-only when
   neutral=FALSE; day-batch updates; K∈{8,16,20,24,32,48}×ν∈{0.6,0.9,1.2}
   rolling-selected on train blocks 1961/71/81/91 ONLY).
3. V1_HCA_REFIT — B1 with HCA co-selected on {40,55,65,80} under the same
   train-internal rule.
Metrics: multi-class log loss, RPS, Brier one-vs-rest (+macro), decile
calibration; MIN_VALID 200/1000/500; preregistered margins-to-fail
ΔLL ≥ 0.01 nats, ΔRPS ≥ 0.005 vs B0 on chrono OOS. Pre-GO work may run the
TRAIN-INTERNAL selection (PREGO run, heavy lock, journaled) and freeze the
selected arm configs — that is S0 exposure by design and computes ZERO OOS
metrics. Post-GO the single scored pass evaluates the three frozen arms on
OOS 2001–2022 once, reproducibly (repro twin after).

## Boundaries

$0; no push/merge/rebase; no S1; PREP (27bb57f2) and DISCOVERY (23b81a26)
trees and all NBA/WNBA/NFL/FUTURES cycles untouched; registry writes only
via researchctl CAS; one heavy job machine-wide (lock HELD by a foreign
worker at plan time → PREGO run records NOT_RUN_RESOURCE_CONFLICT and waits
politically if still held — never kill); data outside git under
`~/.my-quantitative-data/soccer-intl-winprob-scored-v1/` (ledger + run
artifacts); worktrees carry code/manifests/reports. Prospective operation:
NOT_RUN_SOURCE (no fixture feed; historical replay cycle only).

## Lanes and gate sequence

plan commit + `researchctl cycle register` (CAS, budget 3, GO phrase
registered-not-consumed) → worktrees (integration + lane-engine + lane-verify)
→ L-ENGINE (quant-implementer): deterministic engine implementing the frozen
law end-to-end on REAL corpus schema, sha-chained append-only ledger
(`soccer_intl_ledger@1`, tamper-detecting), synthetic + adversarial suite —
same-day leakage, duplicate row, neutral switch, shootout non-flip, renamed
teams, split boundary, 3-way normalization, missing-data fail-closed, ledger
tamper — plus sandbox dry-run (synthetic outcomes only; real-corpus mode is
seal-enforced and stops at 2001-01-01), NO stubs anywhere on the post-GO
path → handoff → controller integrates, runs the PREGO train-internal
selection under the heavy lock at the integrated SHA, freezes
SELECTION.json + arm configs into the ledger → L-VERIFY (quant-auditor,
fresh context, at the FINAL SHA after any fix): code-vs-freeze conformance,
seal mechanics, rights bytes, registry/head coherence, scored-count 0,
refusal rehearsal → fix blockers → A7 RE-RUN at the final SHA →
OWNER_GO_PACKET → registry phase AWAITING_OWNER_GO, budget 0/3, STOP.
Post-GO (owner action only): token + registry consumption → single scored
pass under heavy lock → repro twin → A7 terminal — all OUT of this round.

## Artifacts

`research/control/SOCCER-INTL-WINPROB-SCORED-V1/` in each worktree:
`DISPATCH/`, `handoffs/`, `lanes/{L_ENGINE,L_VERIFY}/`; at integration:
`SELECTION.json` (pre-GO, train-internal), `FREEZE_SCORED.md`,
`A7_PRELAUNCH_VERDICT.md`, `OWNER_GO_PACKET.md`. Ledger + run outputs under
`~/.my-quantitative-data/soccer-intl-winprob-scored-v1/` (outside git,
sha-chained).

## Terminal outcomes (negative-first)

For THIS round the intended stop is NOT terminal: registry stays
ACTIVE_LIGHT at **AWAITING_OWNER_GO** with scored 0/3. Negative paths:
PRELAUNCH_BLOCKED_<gate> (A7 unresolved HIGH/CRITICAL at final SHA) |
NOT_RUN_RESOURCE_CONFLICT (PREGO selection not completed — freeze carries
selection-pending state, never a fabricated pick) | TECHABORT_*. The GO is
the owner's alone; an early or paraphrased GO dies unconsumed.
