# PLAN — ILLIQ-LOSS-MECH-V1 (loss-mechanism forensics → H-A age rule / H-B majors-spread hedge)

- Status: REGISTERED `PLANNED_NOT_STARTED`. Nothing has run under this plan. The draft
  dossier (`research/control/illiq_loss_mech_v1_draft/`) is input evidence, not law.
- Authored: 2026-09-24 · Bootstrap/owner session per explicit owner dispatch 2026-09-24
  ("Mở một cycle nghiên cứu MỚI để tìm cơ chế gây lỗ của ILLIQ-AMIHUD-28D-W trong giai đoạn
  2024-08-22 đến 2025-08-21, và chỉ đề xuất cách sửa nếu có lý do kinh tế và bằng chứng PIT rõ ràng").
- Parent context: CHR3F (family `A8-V11-ILLIQ-AMIHUD`, engine frozen `c97283e0`, 18 files
  byte-identical per A7-r5 §7) and ILLIQ-REG-V1 (TERMINAL, FALSIFIED @2caeeefe).

## 0. Authority order

1. Latest explicit owner instruction.
2. This plan (highest registered live law for cycle `ILLIQ-LOSS-MECH-V1`).
3. `CLAUDE.md` + `HOW_TO_BE_A_LEAD_ENGINEER.md`.
4. Frozen PREREG draft `research/control/illiq_loss_mech_v1_draft/PREREG_ILLIQ-LOSS-MECH-V1.yaml`
   — its constants are carried into §5–§7 VERBATIM; superseded only where this plan is stricter.
5. CHR3F and ILLIQ-REG-V1 plans/artifacts: historical evidence, never current truth.

## 1. Mission and non-mission

**Mission.** Explain WHY the frozen `ILLIQ-AMIHUD-28D-W` anchor lost −56.31% (funded) on
S0R 2024-08-22→2025-08-21, via preregistered falsification of exactly two mechanism
hypotheses born in the owner-dispatched forensic dossier:

- **H-A** `A8-V11-ILLIQ-AMIHUD.v2-age` — long-leg Amihud ranks are contaminated by the
  young post-listing cohort (decay, not illiquidity premium); fix candidate = listing-age
  eligibility floor on the LONG leg only.
- **H-B** `A8-V11-ILLIQ-AMIHUD.v2-hedge` — the BTC-only beta hedge leaves the book short
  the majors-vs-BTC spread inside its own liquid leg (meme/ETH melt-ups), with 90d beta
  lag; fix candidate = add an EW-majors spread-neutrality target to the hedge.

**Non-mission.** No retune of the falsified O1/V2 gate or any gate variant; no
day/symbol/threshold selection after PnL; no parameter rescue of the anchor; no S1 access;
no shadow/paper/live deployment; no candidate promotion to any app; no loop-until-positive
(a FAIL verdict terminates its hypothesis in this cycle).

## 2. Ancestry disclosure (binding, verbatim)

> family A8-V11-ILLIQ-AMIHUD = V11 FAMILY_REJECT (fold-share 0.7055, window
> 2025-08-22..2026-08-21) → CHR3F replication outcome-exposed (Y2021 +1.0360, Y2024P
> +0.1377, S0R funded −0.5631 / INV +0.5459 / Y2024P INV −0.1501) → ILLIQ-REG-V1 gate
> O1+V2 FALSIFIED (gated −0.3458 vs preregistered bar −0.2947, FAIL margin −0.0511; MDD bar
> PASS; INV-gated +0.3297 = diagnostic on seen data only) → ILLIQ-LOSS-MECH-V1 forensics
> observed ALL of the above BEFORE proposing H-A/H-B. Every historical window
> {Y2021, Y2024P, S0R, 2025-26} carries confirmation weight ZERO for this cycle.

Immutable facts carried forward (never re-based): baseline funded −56.31%; gate improved to
−34.58% but FAILED the preregistered −29.47% bar; verdict FALSIFIED; inverse-gated +32.97%
is diagnostic-only.

## 3. Forensic facts this cycle starts from (P1, ledger-level, funded artifact)

Reproduction: 5/5 payload hashes recomputed=recorded; ledger sums match (price 0.0,
funding 9e-12); position-sum net −0.560534 vs −0.563058 explained exactly by 0.002524
boundary-turnover cost not attributed to position records (portfolio identity 1.1e-16); MDD
0.601152 recompute match; 4/4 headline cells match. Full detached-twin re-run:
NOT_RUN_RESOURCE_CONFLICT this session (machine heavy lock held by CHR3F BASISLV staging).

- SHORT leg (liquid quintile) = **85.8%** of net loss (−0.4807); LONG leg 14.2% (−0.0798).
- Loss is price-driven: funding +0.0263 (helps), cost −0.0086; stress ×1.5/×2.0 ≈ flat.
- Three clusters: late-2024 melt-up −0.1109 (short-majors only; DOGE/PEPE/ETH/SOL shorts;
  long leg +0.359); Jan-2025 −0.2449 (long-leg only; BOME/ACE/ZEC/ONG); Jul–Aug-2025
  −0.1984 (short-majors again; ETH-led).
- Listing-age split of long legs: age 90–365d at entry net **−0.1070**; age >365d net
  **+0.0272** — the entire long-leg loss is the young cohort.
- `book_beta_pre_hedge` (PIT, in-artifact): ≈0 in late-2024 (bleed was majors-vs-BTC
  idiosyncratic, not beta), +0.268 mean (max +0.480) in Jul–Aug 2025 (beta-dispersion +
  90d lag regime).

PIT availability table in dossier §2.7: leg membership/betas/ages/funding rates are
decision-time available; PnL/MDD decompositions are outcome-only diagnostics.

## 4. Surfaces

| Surface | Role | Weight |
|---|---|---|
| Y2022 (2022-01-03→2022-12-26), Y2023 (2023-01-02→2023-12-25) | **FRESH falsification folds** — never observed for this family (verified against MAP, FAMILY_FAILURES.jsonl, CHR3F tree at prelaunch) | falsification evidence |
| Y2021, Y2024P, S0R 2024-08-22→2025-08-21, W 2025-08-22→2026-08-21 | disclosure-only, diagnostic | confirmation weight 0 |
| Forward/prospective stamps after freeze (≥13 stamps interim; 52 full) | confirmatory shadow; scored only after typed owner GO at this cycle's gate | the only confirmation |

The S0R window is outcome-exposed: it may NEVER be labeled OOS or prospective in any
artifact of this cycle.

## 5. Frozen laws (constants carried verbatim from PREREG draft)

- Engine frozen `c97283e0` (CHR3F `recovered/v11_root`, byte-untouched); variants are
  plugin subclasses in THIS cycle's worktree (subprocess-isolation pattern from
  ILLIQ-REG-V1); CHR3F tree read-only.
- Clock: weekly Monday 00Z engine-native. Costs: funding-wired `scan_2026_a` (B2 law),
  taker 5bps, slip +1 tick; stress fee ×1.5/×2.0 on every cell; turnover/concentration
  reported per fold; every scientifically computed cell enters the observed counter (P-9).
- Universe law engine-native (PIT listing-age ≥28d, MIN_ELIGIBLE=10, cap 0.30, SKIP law).
- **H-A frozen rule:** long-leg eligibility adds listing-age at stamp ≥ 365 days; short leg
  untouched. **H-B frozen rule:** hedge targets BTC **and** EW-majors-index (top-10 liquid
  universe names, PIT daily completed blocks) spread neutrality; weights otherwise
  engine-native. No other degree of freedom exists in this cycle.
- **H-A falsification bar:** young(<365d) vs old(≥365d) long-leg net, within the engine's
  illiquid quintile, same sign on BOTH fresh folds AND |Δ| ≥ 0.03 per-fold sum AND removing
  young names flips no positive baseline fold negative on fresh folds. Any miss ⇒ H-A
  FALSIFIED.
- **H-B falsification bar:** worst-decile short-leg weekly loss improves ≥ 30% vs baseline
  hedge on BOTH fresh folds AND no fresh-fold anchor sign flip vs baseline AND INV arm
  coherent. Any miss ⇒ H-B FALSIFIED.
- Preconditions for any cell run: machine heavy lock acquired;
  `/pit-data-audit` PASS on Y2022/Y2023 coverage (bars + funding + listing PIT); A7
  prelaunch AUTHORIZED 0 blocking; typed owner GO at this cycle's own gate (P-8).

## 6. Budget (staged)

- Phase 1: cap **8** diagnostic cells, `scored=False`, namespace
  `REPLICATION_NOT_PROSPECTIVE`: {H-A, H-B} × {Y2022, Y2023} × {variant} = 4;
  {baseline ANCHOR × Y2022, Y2023} = 2; {INV control × Y2022} = 1; {INV × H-B Y2023} = 1.
- Phase 2 (forward shadow + scored): NEVER opened without explicit owner amendment;
  GO phrase below is phase-1-scoped.

## 7. Governance

- Cycle: `ILLIQ-LOSS-MECH-V1` · branch `orca/illiq-loss-mech-v1-integration` ·
  worktree `.worktrees/illiq-loss-mech-v1/integration` · asset crypto.
- GO phrase registered, typed ONLY at this cycle's own gate:
  `GO ILLIQ LOSS MECH V1 SCORED EXECUTION`.
- A7 independent prelaunch review of THIS plan + leakage/identity check (fresh-fold claim,
  PIT observables, PREREG-vs-plan divergence) is a hard precondition; A7 writes audit
  artifacts only and never repairs.
- Heavy lock: currently HELD by CHR3F BASISLV data-staging — phase-1 execution waits;
  `NOT_RUN_RESOURCE_CONFLICT` otherwise. Never kill a foreign worker.
- S1 SEALED_UNTOUCHED throughout; no merge/push without owner authorization; lanes never
  touch ledgers/registries/other lanes.

## 8. Deliverables at close

Terminal report: cluster-level loss attribution (P1), evidence for/against H-A and H-B,
proposed change ONLY if a hypothesis survives its frozen bar on fresh folds (and even then
candidate status requires a separate owner-gated forward decision), all trials counted,
honest verdict, ELI5 section for the owner. Negative verdicts are terminal for the
falsified hypothesis in this cycle — no variant iteration, matching the ILLIQ-REG-V1
falsification-first template.
