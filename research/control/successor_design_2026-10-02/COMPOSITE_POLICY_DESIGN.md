# COMPOSITE_POLICY_DESIGN v2 — successor_design_2026-10-02 (DRAFT FOR OWNER REVIEW; NOT RUN)

> **v2 (co-owner follow-up):** §6 budget recomputed exactly (v1's ≤140-row
> cap was arithmetically impossible); the design-law claim scoped to the
> measured set; hard risk caps made independent of economic selection; cost
> law made component-wise. All changes itemized in `ERRATUM_V2.md`.

Successor coordination architecture for the M1-pair composite (EURUSD,
GBPUSD, USDJPY leg families) with waiting slots for everything else. Every
design choice cites its journal evidence. Nothing here has been run; this is
the preregistration skeleton the successor cycle would freeze.

Design law (from the failure map), scoped to what was measured: **on this
calendar, the always-on netted blend outperformed every participation-gate
mechanism actually tested against it — 7 terminal overlay programs (DP §4
ancestry) plus the control arms B5 clock-gate (+54k vs B1 +689k), B6
inverted (−256k), B7 lagged (+591k), B8 eligibility-oracle (+389k), B2
equal-weight (+356k), GATE −385.5k vs SIZE −7.3k decomposition.** This is
evidence against THAT MEASURED SET of mechanisms on THAT calendar — not a
proof over all possible portfolio gates, and it transfers to new regimes
only as a prior. The successor therefore spends its complexity budget on
per-symbol admission hygiene, leg retirement by preregistered election,
and cost authority; a successor plan may re-open portfolio-level gating
only with a NEW mechanism, an explicit multiple-testing budget, and the
seven-deaths prior priced in.

## 0. Engine prerequisites (hard conditions, inherited + new)

1. **Quote-CCY ledger** per FILL_ACCOUNTING_SPEC §4 / DP §13 — the
   DAILY-EXPLORATORY-V1 engine already implements it (identity to 1e-9, 32
   tests) and is the designated lineage; pooled bars restated in quote-CCY
   with one frozen conversion convention.
2. **Per-leg exposure + MAE/MFE journaling** (docket A §9 unlock iii /
   B §9): every fill carries its leg attribution and excursion MFE/MAE.
   Scope honesty (F4): these fields support attribution FORENSICS; they do
   NOT by themselves resolve marginal contribution — the trig/pfold/solo
   ambiguity is resolved only by FULL-PATH REPLAY arms (LOL/LORO re-run the
   whole netting/caps/cost path; per-leg PnL arithmetic on a netted book is
   banned as a marginal-contribution estimate). Proxy statistics (trig /
   paper_fold_net_by_leg / solo) are DIAGNOSTICS, each naming its source
   law.
3. **Per-fill quoted-spread capture** from the M1 panel (replaces C-cell
   DECLARED bands where the bar is present; bands remain for absent-bar
   fallback).
4. **Cost law (component-wise; v2):** the owner has elected to continue
   EXPLORATORY research WITHOUT a brokerage statement — the absence of a
   statement is therefore NOT a blocker for exploratory work. Every number
   carries per-component labels: spread cells C1–C3 measured from panels;
   commission/slippage/swap = DECLARED bands labeled
   `NET_DEFAULT_COST`/PROVISIONAL. IF an owner statement lands later, it
   upgrades ONLY the components it can lawfully measure — commission and
   swap/interest accruals where attribution is valid — and measures neither
   slippage, nor spread-beyond-cells, nor capacity, nor any history it did
   not witness. DECLARED bands + ×1.5/×2.0 stress REMAIN in force for all
   exploratory results; no exploratory number ever becomes an "after-cost
   PASS" or a "measured edge" by virtue of a partial statement.
5. Journal: `journal_row@1` lineage + rejected-opportunity rows for every
   blocked/deferred/netted signal (the JOURNALING law is proven — DAILY's
   73 BLOCKED_STALE + 24 BLOCKED_FLOOR rows evidence it). CAVEAT (F1): the
   DAILY floor rows were emitted by a FOLD-TOTAL rule (lookahead as
   suppression — proven, SAMPLE_FEASIBILITY_MATRIX §floor-causality); the
   successor's floor law is the two-layer INF/ECO law in §1 — only the
   journaling pattern transfers, not the suppression mechanism.

## 1. Eligibility layer (per symbol, evidence-gated)

| tier | symbols | admission condition |
|---|---|---|
| A: journaled M1 majors | EURUSD, GBPUSD, USDJPY | panels + journals on file; costs = measured spread cells C1–C3 + DECLARED U2/U3/U4 (labels kept) |
| B: TRAIN-only H1 | USDCAD, AUDUSD | BLOCKED until C-H-C1/C2/C3 unlocks AND a changed-mechanism-axis re-attempt (Q-10); same-rule retries banned |
| C: daily-cohort D1 | NZDUSD, USDCHF, XAUUSD, XAGUSD | slots; each leg needs PIT declaration/threshold freeze + plan amendment (owner-only unlocks); costs run under the same component-wise law as tier A (DECLARED + stress for exploratory; a statement is an OPTIONAL component upgrade, never admission-mandatory); XAG additionally has ZERO consumer legs today |
| D: futures/index/commodity | NQ, ES, CL, NG, GC, SI, 6E, 6J, 6B, 6A, BRENT, WTI, NATGAS | FLAT-by-authority slots; no spot conclusion transfers to them; no admissible panel exists |

**FLAT law (v3, causality-corrected):** any symbol or leg without its
tier's EVIDENCE is FLAT, typed `NOT_RUN_*`, never silently skipped. Floor
law is TWO-LAYER (full text + pseudo-code + T1-T4 truncation-replay spec in
SAMPLE_FEASIBILITY_MATRIX.md): **INF** inference floors are fold-total,
evaluated at fold close, and only TYPE conclusions (NOT_RUN_THIN) — they
never suppress, resize, or retroactively zero any trade and never touch the
order path; **ECO** economic-eligibility floors are trailing-only, PIT at
each decision (a pure function of journal rows with ts < decision_ts plus
FREEZE-1-frozen constants incl. the seeding/cold-start law), journaled
pre-order-emission. v2's "FLAT for THAT fold (DAILY precedent)" is REPEALED
— the DAILY precedent's suppression was fold-total lookahead (proven;
bounded impact disclosed). No fold is ever zeroed retrospectively for low
n; thin folds type NOT_RUN_THIN and their rows stand.

**Sample feasibility is a registration input:** every hypothesis/arm
carries its feasibility row (SAMPLE_FEASIBILITY_MATRIX.md); cells
structurally underpowered are PRE-TYPED (S017 refutation expected
NOT_RUN_THIN, P(meet floor) ~= 0.03%; S023/VC2-JPY LOL pre-typed thin;
HN-3 pooled coin-flip 33-65% with the evaluation UNIT frozen at FREEZE-1;
HN-1 LEARN grids expected NOT_RUN_GRID_THIN, family-pooled read is the
rescue). No floor is loosened to make a cell pass.

## 2. Rule stack (what actually trades)

**Layer 0 — the book (the always-on netted core, structurally unchanged).**
Per-symbol netted voter over admitted legs, fixed 10,000-unit vote quantum,
L4 tie-netting, fold-edge force-flat. ("Structurally unchanged" ≠
validated: the core measured positive on EXPOSED folds under DECLARED costs
only — the selection-level DSR read REJECTS edge claims (DP corr-1); this
design claims measurable hygiene hypotheses, not a validated engine.) No
portfolio-level eligibility gate exists anywhere in the stack (prior
measured against it — see the scoped design law above).

**Layer 1 — per-symbol admission hygiene hypotheses (the successor's active
surface; every rule is a HYPOTHESIS to be measured, not an improvement
claim):**
- USDJPY: HN-1-JPY (handover NY-long block; hour-set learned on LEARN; the
  shared London→NY mechanism is a POST_OUTCOME hypothesis needing the
  C-PLAC placebo + clock-shadow + DST-aligned session marks to survive).
- EURUSD: HN-1-EUR (handover hour gate; same family, LEARN-learned; same
  POST_OUTCOME caveat).
- ALL legs: HN-2 clock-aware activity floors (E1 constants inherited frozen
  for SIG-exit-only legs; clock-relative ratio for the rest; f-ratio
  validated on LEARN at clock-class granularity).
- GBPUSD-S017: retired at registration by owner election (SU-RS-G1;
  three-law agreement, zero parameters; a validation-fold refutation of the
  retire can only close the claim negative — restoration requires a new
  cycle).
- USDJPY-S026 guard: the ONLY ON-rule candidate (A-H1), in the battery
  because its crossed arms are mandatory anyway; default node = guard
  REMOVED at registration (the measured attribution is against it).

**Layer 2 — leg-level membership (frozen at registration, measured on
validation as diagnostics ONLY):**
- USDJPY-S014: membership frozen at registration by owner election (LEARN
  cannot decide it: ≈3–6 expected entries on any 26–40w LEARN vs ≥20
  floor); the LOL∖S014 arm reports as a fixed diagnostic under HN-3's
  typing rule — never a selector (protocol §2).

**Layer 3 — optional single sizing identity:**
- HN-5 USD-cluster cap — ONE identity pair (×1.0 + ×1.5), optional, strict
  anti-hypothesis (must beat B1S on the AND-pair at ×1.5; auto-refuted if
  it binds like a gate).

**What is deliberately absent:** regime routers, ensemble schedulers,
breadth gates, portfolio on/off clocks, dynamic weights — the measured-set
class the design law scopes. A successor plan proposing any of them must
bring a NEW mechanism, an explicit multiple-testing budget, and the
seven-deaths prior priced in — not re-litigate the measured set.

## 3. Leg selection and weighting

- **Selection law (protocol §2):** composition and rule nodes freeze at
  registration; LEARN-side data only for anything learned; validation-fold
  LOL/LORO are diagnostics, never selectors; any composition change
  discovered on validation requires a new cycle.
- **Leg admission** by eligibility + floors, never by exposed-fold PnL; the
  12-leg slate carries over minus preregistered retirements; new legs enter
  only through corpus DISCOVERY on fresh
  data (P-35 clock law applied a priori: expected decision rate × window ≥
  floors, computed BEFORE registration).
- **Weighting: fixed vote quantum, no re-weighting.** Evidence: B2
  equal-weight −332k vs B1; SIZE-layer interventions ≈ $0; CARRY is where
  the blend's value lives. Weight research is DEFERRED until (i) measured
  costs land and (ii) ≥6 fresh folds exist — then it is a NEW hypothesis
  with its own battery, not a parameter of this one.

## 4. Netting, caps and portfolio limits

**Hard risk caps (frozen at registration; independent of any economic
gate/eligibility selection — they bind every arm identically, including
B1S):** per-symbol max position (vote-quantum multiples, frozen value at
registration); portfolio heat ceiling; maxDD kill-switch (typed FLAT until
re-registration — execution-law, never re-parameterized in-cycle); fold-edge
force-flat. These exist to bound tail risk and are NOT part of, and cannot
be traded off against, any hypothesis's economics.

- L4 netting tie → both-cancel (measured $0 harm — keep).
- L5 cluster caps retained (per RULE_SLATE §2 inheritance); cluster =
  {USD-factor} as the only measured common factor (HN-5 tests the soft
  version).
- L6 cost guard: default REMOVED from the stack at registration (its
  measured attribution is −352,959 direct; hypothesis A-H1/J3 tests adding
  a re-anchored version back — a hypothesis, not an improvement claim); if
  any spend-cap is kept, it must be re-anchored to owner-declared capacity
  limits or measured EXECUTION history — a brokerage statement provides
  commission/swap attribution only, NOT a capacity measure — and never to
  realized trailing spend.
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
| C2 | random dwell-matched battery (≥100 seeds, ≤128, own ledger line; counted in the multiple-testing/compute denominator) | cadence-as-value guard (prior: DP §2.3's 128/128 duty-matched random DIAGNOSTIC beat the frozen policy's objective — a diagnostic, not a scored battery; PC12A's B4 never executed) |
| C3 | clock-shadow (deterministic every-k-th) | the control DAILY's battery SUBSTITUTED (TF-1) — in THIS battery it runs for real |
| C-PLAC | placebo-session control (block Tokyo-morning instead of handover hours) | HN-1 mechanism discriminator |
| LORO | leave-one-RULE-out × every Layer-1 rule | per-rule P-MW/P-FA bars (RULE_SLATE §7) |
| LOL | leave-one-LEG-out × every leg (12) | NEW, mandatory: resolves attribution conflicts (HN-3) and the one-carrier question |
| C4 | cost stress ×1.0/×1.5/×2.0 on SLATE + B1S | governing ×1.5; ×2.0 reporting with sign-flip disclosure |

## 6. Trial budget v3 — CANONICAL (machine-verified; one number per option)

Machine-readable authority: `analysis/arm_manifest.json` (every arm: id,
class, composition, tier, folds, rows, option membership) — verified by
`analysis/verify_arm_manifest.py` (recomputes all totals from the arms
list; structural checks: no LOL over retired S017, B0 = 1 identity/0 rows,
exactly one seed battery). **v2's tables (33/192 A, 27/156 B) are superseded
— their LOL sets included retired/benched legs and undeclared alternatives;
the v2 numbers survive only in git history and ERRATUM_V3's appendix.**

Canonical resolutions (one law, alternatives in ERRATUM_V3 appendix only):
LOL is declared over ADMITTED legs (S017 retired at registration → no
LOL/S017 arm; its two-sided contrast rides LORO(G1)); LORO(J3) is realized
as the guard-IN arm; C2 fold rows count INSIDE the scored-row budget;
×2.0 arms identity-classified; seeds on their own ledger line AND in the
multiple-testing/compute denominator.

| | Option A (full) | Option B (scoped) |
|---|---:|---:|
| composition | 8 singletons + 5 LORO + 11 LOL (admitted legs) + 2 crossed + 4 stress | same but LOL = 5 live legs {S014, S002-JPY, S026, S003, S023} |
| committed identities (core / with HN-5) | **30 / 32** | **24 / 26** |
| committed scored rows (core / with HN-5) | **174 / 186** | **138 / 150** |
| max with reserve (3 ids, technical-only) | 35 ids / 204 rows | 29 ids / 168 rows |
| + LEARN grid rows (12) = TOTAL max | **216** | **180** |
| caps (max + explicit headroom) | ≤39 ids / ≤228 rows | ≤32 ids / ≤198 rows |
| seed line | ≤128 sub-runs, own line, in multiple-testing denominator | same |
| pre-typed thin cells | LOL∖S023, LOL∖VC2-JPY → NOT_RUN_THIN expected; HN-1 LEARN grids → NOT_RUN_GRID_THIN expected; S017 refutation (LORO(G1)) → NOT_RUN_THIN expected (P(meet ≥50) ≈ 0.03%) | same + LOL∖S023 carried as declared-typed |
| deferred (Option B only) | — | LOL for S009, S013, S046, VC2-EUR, GBP-S002, VC2-JPY typed `NOT_RUN_LOL_DEFERRED` (Option A carries them) |

Registration-time elections (FREEZE-1, all declare-or-pre-type, none a
floor change): the campaign aggregate floor's READING (per-leg: 8–9 of 12
legs expected NOT_RUN_THIN_AGGREGATE on 6×26w; battery-pooled: trivially
passes) — opposite verdicts, must be pinned; the HN-3 evaluation UNIT
(decision-unit 108 pooled vs ≥20 comfortable; entry-unit coin-flip 33–65%);
the decisions→trades conversion law (≈2.5:1) for every trade-denominated
P-MW/P-FA bar. Reserve = TECHNICAL re-runs only (TECHABORT twins, integrity
re-runs): never new hypotheses after FREEZE-2, never PnL search; headroom
spendable only by registered amendment before FREEZE-2. Selection is
deterministic TRAIN-only with frozen tie-breaks.

## 7. Acceptance bars (inherited wholesale + additions)

- PB2 AND-semantics on (net ↑, DD ↓) vs B1S, pooled, strict, ties fail;
  ×1.5 governing; P7 fold concentration; P8R leave-one-rule; NEW P-LOL
  leave-one-leg reporting (every leg's removal delta disclosed two-sided).
- P-MW / P-FA two-sided tables mandatory for every OFF/ON rule; omission =
  `NOT_RUN_INTEGRITY`.
- Absolute sub-bar: netPnL(SLATE) > 0 at ×1.0 AND ×1.5 under the governing
  cost labels (component-wise per §0-4: measured cells + DECLARED bands —
  a later statement upgrades only commission/swap attribution and never
  converts an exploratory read into a measured-edge claim).
- Negative close is first-class: if B1S dominates again, the typed close is
  `POLICY_NO_INCREMENTAL_VALUE` (8th reading of the class) and the program
  pivots to cost authority + daily/futures cohort unlocks.

## 8. What this design does NOT promise

No edge is claimed or implied. The measured prior is that overlays die and
always-on won on a burned calendar under DECLARED costs; this design's
honest thesis is narrower — **hygiene-level rules (session admission,
clock-aware floors, stop-geometry retirement) may improve the blend's
risk-adjusted profile where governance-level rules failed, and the battery
will measure that claim or kill it.** The final portfolio freezes at
registration (protocol §2); validation folds measure the frozen artifact;
any composition change they motivate requires a new cycle.

— end design v2 —
