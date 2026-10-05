# PLAN — WNBA-PLAYERFEAT-SCORED-V1 (WNBA player-feature win-prob scored successor, $0)

- cycle_id: WNBA-PLAYERFEAT-SCORED-V1 · asset: shared · ACTIVE_LIGHT, budget 0/9 arms scored,
  GO phrase registered NOT typed: `GO WNBA PLAYERFEAT SCORED V1 EVALUATION`
- owner authority 2026-10-05 (this chat): bring the WNBA program to GO-READY — registration,
  freeze, implementation, synthetic fixtures, exact-arm dry-run, independent A7 per gate;
  **STOP before owner typed GO**. No scored/OOS computation this round: the walk-forward OOS
  window is frozen here, evaluated only after GO. Train-internal selection (B1-WNBA grid +
  feature-arm φ) is the gate-sanctioned path for freeze completion; nothing on OOS seasons.
- Hard boundaries: as NBA plan (no GO typing, no OOS run, no S1/paper/live/betting/purchases/
  push/merge/backfill; calibration vocabulary only; internal-research-only rights posture).

## Inheritance (re-measured 2026-10-05)

- Feature table (WINPROB-PLAYERFEAT-PREP-V1 lane B + D verified): 11,976 rows = 2×5,988
  universe games 2002–2026 at `~/.my-quantitative-data/playerfeat-prep-v1/wnba/features/`
  (deterministic rebuild sha-identical; lineage 20-key; 0 outcome columns). Era floors:
  minutes-quality 2013+ for minutes-weighted variants; continuity rows 2014–2026 (v2 law);
  DNP 2012+; expansion/2002 rows neutral+flagged; `active`/`reason` never read.
- Baseline law (successor packet §2, proposal inherited): B0 floor + **fresh B1-WNBA own-Elo**
  grid K∈{8,16,32} × HCA∈{0,50,100} × γ∈{0.65,0.75,0.85} (27 fits, all counted), 1997–2001
  stats-side warm-up feeding streams if on disk (else warm-up 2002–2004, disclosed); degenerate
  K→0 kill. Selected config frozen in this cycle's freeze; HCA prior expectation positive but
  UNMEASURED — grid must include 0; NBA's K=32/HCA=100 citable context only.
- Windows (successor packet §1 inherited with disclosed adaptation): ERA LAW 1997–2001
  warm-up only; TRAIN 2002–2018; WALK-FORWARD OOS = final 7 complete seasons at freeze —
  pin **2019–2025 is NOT chosen here**: freeze pins OOS = [2020..2026] (2026 in-progress
  games excluded from any historical evaluation; only completed seasons counted post-GO;
  placeholder TBD rows never games). Feature-arm selection folds pinned to seasons
  2014–2018 (5 expanding-origin single-season folds — adaptation from the packet's 4×2-season
  blocks, justified by the measured era floors 2013+/2014+; B1-WNBA grid selection uses the
  packet's 4 expanding-origin 2-season validation blocks over the TRAIN tail). PROSPECTIVE
  future seasons = ledger work post-GO, out of scope here.
- W-H2 PIT law (packet §4): continuity v2 = game-1 membership used only from game 2 onward;
  v1 NOT_RUN_PIT restated. Target-game roster/active/starter/DNP/injury = NOT_RUN_PIT (no
  pre-game publish timestamps) — law, restated, never re-litigated.
- Dead-shape law + controls: features enter INSIDE the rating argument (R̃ = R + φ·x or
  continuity-modulated season-start carryover), designed-null ≡ parent bit-for-bit;
  time-shuffled twins per arm (diagnostic, outside budget; twin beats parent ⇒ MACHINERY_
  SUSPECT + arm UN-SCORED); warm-up-vs-cold-start rerun = diagnostic only.
- Metrics/uncertainty: as NBA plan (LL primary; Brier/reliability/slope band [0.85,1.15];
  paired tip-date-cluster bootstrap 10,000 resamples seed 20261005; season-fold majority
  bars; single-batch OOS scoring law) — bound at freeze for the post-GO read. Neutral-site
  rows → HCA=0 default with separate report (packet §5).

## Tasks (owner round 2026-10-05; stop before GO)

1. Lane T — IMPLEMENTATION + TRAIN-INTERNAL SELECTION: harness with modes `select` (real data
   hard-capped: B1-WNBA grid folds ≤2018; feature folds ≤2018 with era floors) and
   `evaluate-oos` (refuses real data without GO token; synthetic only) + `--selftest`
   (hand-computed fixtures: Elo update, HCA argument, γ reversion, lineage joins via 20-key
   table, continuity carryover arithmetic, designed-null ≡ parent, era-floor/neutral rules,
   leakage canaries). Run B1-WNBA grid (27 fits) → freeze config; feature arms WF-A
   (continuity-modulated carryover: R_start = 1500 + γ·c_i·(R_end−1500), c from table rows
   2014+, null c≡1 ≡ parent), WF-B (load/concentration φ_B·(x_H−x_A)), WF-C (top-player
   form/absence φ_C·(x_H−x_A)); grids φ ∈ {−50,−25,0,25,50}; folds 2014–2018; selection
   pooled inner LL; G-ENTRY as NBA (point <0 vs frozen B1-WNBA, slope in band, twin clean).
   SELECTION_LEDGER.jsonl + SELECTION_REPORT.md with frozen configs or slot releases.
2. Lane S — SYNTHETIC FIXTURES + EXACT-ARM DRY-RUN: as NBA plan (designed-null byte-identity,
   determinism, era-floor/neutral/expansion fixtures, lineage-canary (raw-abbreviation join
   must fail), evaluate-oos refusal without GO token, sandbox rehearsal, exact-arm identity).
3. Lane A7 — INDEPENDENT PRELAUNCH AUDIT: as NBA plan (+ verify era floors enforced, lineage
   law, v2-roster law; OWNER_GATE_BRIEF.md). Verdict PASS | REFUSED.

## Boundaries / Artifacts / Terminal outcomes

As NBA-PLAYERFEAT-SCORED-V1 plan, with worktree `.worktrees/wnba-playerfeat-scored-v1/`,
data sandbox `~/.my-quantitative-data/wnba-playerfeat-scored-v1/`, control state
`research/control/WNBA-PLAYERFEAT-SCORED-V1/`, terminal outcomes negative-first incl.
PRELAUNCH_READY_PENDING_OWNER_GO | SELECTION_NEGATIVE_ALL_CANDIDATES_FAILED | BLOCKED_* |
TECHABORT_*. GO typed only by the owner at this cycle's own gate after the A7 verdict.
