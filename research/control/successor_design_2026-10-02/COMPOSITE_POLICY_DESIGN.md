# COMPOSITE_POLICY_DESIGN — successor_design_2026-10-02 (DRAFT FOR OWNER REVIEW; NOT RUN)

Successor coordination architecture for the M1-pair composite (EURUSD,
GBPUSD, USDJPY leg families) with waiting slots for everything else. Every
design choice cites its journal evidence. Nothing here has been run; this is
the preregistration skeleton the successor cycle would freeze.

Design law (from the failure map): **the money is in the always-on netted
blend; every portfolio-level participation gate ever measured on this
calendar destroyed value (7 deaths + oracle control). The successor spends
its complexity budget on per-symbol admission hygiene, leg retirement by
measurement, and cost authority — never on portfolio gating of the blend.**

## 0. Engine prerequisites (hard conditions, inherited + new)

1. **Quote-CCY ledger** per FILL_ACCOUNTING_SPEC §4 / DP §13 — the
   DAILY-EXPLORATORY-V1 engine already implements it (identity to 1e-9, 32
   tests) and is the designated lineage; pooled bars restated in quote-CCY
   with one frozen conversion convention.
2. **Per-leg exposure + MAE/MFE journaling** (docket A §9 unlock iii /
   B §9): every fill carries its leg attribution and excursion MFE/MAE; kills
   the trig/pfold/solo ambiguity for future cycles.
3. **Per-fill quoted-spread capture** from the M1 panel (replaces C-cell
   DECLARED bands where the bar is present; bands remain for absent-bar
   fallback).
4. **DECLARED-cost kernel labels** (`NET_DEFAULT_COST` /
   PROVISIONAL_PENDING_COST_AUTHORITY) on every number until the owner
   statement lands (OI-2 law).
5. Journal: `journal_row@1` lineage + rejected-opportunity rows for every
   blocked/deferred/netted signal (proven in both prior cycles; 73
   BLOCKED_STALE + 24 BLOCKED_FLOOR rows are the DAILY evidence the law
   works).

## 1. Eligibility layer (per symbol, evidence-gated)

| tier | symbols | admission condition |
|---|---|---|
| A: journaled M1 majors | EURUSD, GBPUSD, USDJPY | panels + journals on file; costs = measured spread cells C1–C3 + DECLARED U2/U3/U4 (labels kept) |
| B: TRAIN-only H1 | USDCAD, AUDUSD | BLOCKED until C-H-C1/C2/C3 unlocks AND a changed-mechanism-axis re-attempt (Q-10); same-rule retries banned |
| C: daily-cohort D1 | NZDUSD, USDCHF, XAUUSD, XAGUSD | slots; each leg needs PIT declaration/threshold freeze + cost statement + plan amendment (owner-only unlocks); XAG additionally has ZERO consumer legs today |
| D: futures/index/commodity | NQ, ES, CL, NG, GC, SI, 6E, 6J, 6B, 6A, BRENT, WTI, NATGAS | FLAT-by-authority slots; no spot conclusion transfers to them; no admissible panel exists |

**FLAT law:** any symbol or leg without its tier's evidence is FLAT —
typed `NOT_RUN_*`, never silently skipped; a leg whose per-fold decision
floor fails is FLAT for THAT fold (DAILY precedent), and the fold row says
so.

## 2. Rule stack (what actually trades)

**Layer 0 — the book (the always-on netted core, structurally unchanged).**
Per-symbol netted voter over admitted legs, fixed 10,000-unit vote quantum,
L4 tie-netting, fold-edge force-flat. ("Structurally unchanged" ≠
validated: the core measured positive on EXPOSED folds under DECLARED costs
only — the selection-level DSR read REJECTS edge claims (DP corr-1); this
design claims hygiene improvements, not a validated engine.) No
portfolio-level eligibility gate exists anywhere in the stack
(class-refuted).

**Layer 1 — per-symbol admission hygiene (the successor's active surface):**
- USDJPY: HN-1-JPY (handover NY-long block; hour-set learned on LEARN).
- EURUSD: HN-1-EUR (handover hour gate; same family, LEARN-learned).
- ALL legs: HN-2 clock-aware activity floors (E1 constants inherited frozen
  for SIG-exit-only legs; clock-relative ratio for the rest).
- GBPUSD-S017: retired at registration (SU-RS-G1; three-law agreement,
  zero parameters).
- USDJPY-S026 guard: the ONLY ON-rule candidate (A-H1), admitted into the
  battery solely because its LORO×LORO arms are mandatory anyway; default
  node = guard REMOVED (the measured attribution is negative against it).

**Layer 2 — leg-level measurement rules (decided by arms, not by
preregistered thresholds):**
- USDJPY-S014: stay/remove decided by the leave-one-leg identity under
  HN-3's preregistered decision rule.

**Layer 3 — optional single sizing identity:**
- HN-5 USD-cluster cap — ONE identity, optional, strict anti-hypothesis
  (must beat B1S on the AND-pair at ×1.5; auto-refuted if it binds like a
  gate).

**What is deliberately absent:** regime routers, ensemble schedulers,
breadth gates, portfolio on/off clocks, dynamic weights — the seven-deaths
class. A successor plan proposing any of them must first overturn the class
evidence with a mechanism not yet tested, not re-litigate the same class.

## 3. Leg selection and weighting

- **Selection on LEARN only**: legs admitted by eligibility + floors, never
  by exposed-fold PnL; the 12-leg slate carries over unless retired by
  Layer-1/2 law; new legs enter only through corpus DISCOVERY on fresh
  data (P-35 clock law applied a priori: expected decision rate × window ≥
  floors, computed BEFORE registration).
- **Weighting: fixed vote quantum, no re-weighting.** Evidence: B2
  equal-weight −332k vs B1; SIZE-layer interventions ≈ $0; CARRY is where
  the blend's value lives. Weight research is DEFERRED until (i) measured
  costs land and (ii) ≥6 fresh folds exist — then it is a NEW hypothesis
  with its own battery, not a parameter of this one.

## 4. Netting, caps and portfolio limits

- L4 netting tie → both-cancel (measured $0 harm — keep).
- L5 cluster caps retained (per RULE_SLATE §2 inheritance); cluster =
  {USD-factor} as the only measured common factor (HN-5 tests the soft
  version).
- L6 cost guard: default REMOVED from the stack (its measured attribution
  is −352,959 direct; the A-H1 relaxation hypothesis tests the opposite
  direction); if any spend-cap is kept, it must be re-anchored to MEASURED
  capacity (statement-derived), not realized trailing spend.
- Portfolio limits: one net position per symbol (unchanged); fold-edge
  force-flat (unchanged, asymmetry disclosed per PB2 E-Law 2); no leverage
  change, no initial-capital change ($100k book).

## 5. Baseline battery and controls (all NOT_RUN until the cycle registers)

| id | what | why |
|---|---|---|
| B0 | FLAT | absolute-zero reference (DAILY precedent: it dominated) |
| B1S | always-on same-legs wall | PRIMARY baseline (seven-deaths law; beat it on net AND DD) |
| B2S | equal-weight | sizing-null |
| B3S | best-single chosen on LEARN | concentration-null |
| C2 | random dwell-matched battery (≥100 seeds, ≤128) | cadence-as-value guard (PC12A: 128/128 random patterns beat the policy) |
| C3 | clock-shadow (deterministic every-k-th) | the control DAILY's battery SUBSTITUTED (TF-1) — in THIS battery it runs for real |
| C-PLAC | placebo-session control (block Tokyo-morning instead of handover hours) | HN-1 mechanism discriminator |
| LORO | leave-one-RULE-out × every Layer-1 rule | per-rule P-MW/P-FA bars (RULE_SLATE §7) |
| LOL | leave-one-LEG-out × every leg (12) | NEW, mandatory: resolves attribution conflicts (HN-3) and the one-carrier question |
| C4 | cost stress ×1.0/×1.5/×2.0 on SLATE + B1S | governing ×1.5; ×2.0 reporting with sign-flip disclosure |

## 6. Trial budget draft (every trial/grid/control counted)

Counting law: PB2 E-Law 8 (identities on the scored line; seed sub-runs on
their own line). Illustrative composition for a 6-fold fresh calendar:

| identity class | count |
|---|---:|
| SLATE (layered book) | 1 |
| B0 / B1S / B2S / B3S / C3 / C-PLAC | 6 |
| C2 battery (1 identity + seed line) | 1 |
| LORO × rules (J1-JPY, J1-EUR, HN-2, G1-retire, J3-guard) | 5 |
| LOL × 12 legs | 12 |
| C4 stress: SLATE+B1S × {×1.5, ×2.0} | 4 |
| **total identities** | **29** |
| LEARN-side grid rows (HN-1 hour-sets 3 nodes × 2 symbols + HN-2 f-ratio validation 3) | ~9 rows |

Caps: ≤ 32 identities, ≤ 140 rows (headroom for 3 contingency re-runs).
Floors inherited: 20/3/100 per leg per fold (CAM §3) + per-rule floors
(register §Part 1/2). Floor failure ⇒ typed `NOT_RUN_THIN`, never widened.
This budget is a DRAFT for the successor plan — no rows exist today.

## 7. Acceptance bars (inherited wholesale + additions)

- PB2 AND-semantics on (net ↑, DD ↓) vs B1S, pooled, strict, ties fail;
  ×1.5 governing; P7 fold concentration; P8R leave-one-rule; NEW P-LOL
  leave-one-leg reporting (every leg's removal delta disclosed two-sided).
- P-MW / P-FA two-sided tables mandatory for every OFF/ON rule; omission =
  `NOT_RUN_INTEGRITY`.
- Absolute sub-bar: netPnL(SLATE) > 0 at ×1.0 AND ×1.5 (DECLARED-cost
  labels retained until OI-2).
- Negative close is first-class: if B1S dominates again, the typed close is
  `POLICY_NO_INCREMENTAL_VALUE` (8th reading of the class) and the program
  pivots to cost authority + daily/futures cohort unlocks.

## 8. What this design does NOT promise

No edge is claimed or implied. The measured prior is that overlays die and
always-on won on a burned calendar under DECLARED costs; this design's
honest thesis is narrower — **hygiene-level rules (session admission,
clock-aware floors, stop-geometry retirement) may improve the blend's
risk-adjusted profile where governance-level rules failed, and the battery
will measure that claim or kill it.**

— end design —
