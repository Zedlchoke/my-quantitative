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
   B §9): every fill carries its leg attribution and excursion MFE/MAE; kills
   the trig/pfold/solo ambiguity for future cycles.
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
  typing rule — never a selector (protocol §3).

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

- **Selection law (protocol §3):** composition and rule nodes freeze at
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
  any spend-cap is kept, it must be re-anchored to MEASURED capacity
  (statement-derived), not realized trailing spend.
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

## 6. Trial budget v2 (every trial/grid/control counted; DRAFT, zero rows exist)

Counting law: PB2 E-Law 8 (identities on the scored line; the C2 battery is
1 identity with ≤128 seed sub-runs on its OWN line — seed sub-runs never
write per-fold scored rows; stress and leave-one-* re-runs
identity-classified); PB2 §1 B0 law (B0 = 1 identity, 0 rows); CAM §3
floors (≥20/window, ≥3/fold, ≥100 aggregate per leg, typed NOT_RUN_THIN).
Fold count = 6 validation folds (protocol §1.3).

### Option A — full battery (all 12 LOL, crossed set, HN-5, contingency)

| identity class | identities | fold rows |
|---|---:|---:|
| SLATE (layered book) | 1 | 6 |
| B0 FLAT (0 rows by construction) | 1 | 0 |
| B1S always-on same-legs wall (PRIMARY baseline) | 1 | 6 |
| B2S equal-weight | 1 | 6 |
| B3S best-single (LEARN-selected) | 1 | 6 |
| C2 random dwell-matched battery (1 identity; seeds on own line) | 1 | 6 |
| C3 clock-shadow | 1 | 6 |
| C-PLAC placebo-session | 1 | 6 |
| LORO × rules {J1-JPY, J1-EUR, HN-2, G1-retire, J3-guard} | 5 | 30 |
| LOL × 12 legs {S002j,S003,S014,S023,S026,VC2-JPY; S009,S013,S046,VC2-EUR; S002g,S017} | 12 | 72 |
| Crossed (SLATE+guard)∖{S003}, (SLATE+guard)∖{S023} — A-H1 mandate | 2 | 12 |
| C4 ×1.5 stress: SLATE + B1S (governing) | 2 | 12 |
| C4 ×2.0 stress: SLATE + B1S (reporting, P6b) | 2 | 12 |
| HN-5 USD-cluster cap ×1.0 | 1 | 6 |
| HN-5 ×1.5 (anti-hypothesis: must beat B1S on the AND-pair at ×1.5) | 1 | 6 |
| **committed (scored line)** | **33** | **192** |
| contingency reserve (3 identities, E-Law 8) | 3 | 18 |
| **MAX (reserve fully consumed)** | **36** | **210** |
| LEARN-side grid rows: HN-1-JPY 3 nodes + HN-1-EUR 3 + HN-2 f-ratio 3 (clock-classes; the per-leg reading would be 12 — CHOSEN reading: clock-classes) + J3 {1.5, 2.0, ∞} 3 | — | 12 |
| **TOTAL rows (committed / max)** | | **204 / 222** |
| C2 seed line (own line, never scored rows; B3S LEARN-selection journals written, 0-counted per DAILY precedent) | — | ≤128 sub-runs |

Caps: **≤40 identities** (36 max + 4 headroom), **≤240 total rows** (222 max
+ 18 headroom). Precedent reconciliation: within PC12A's 48-identity cap;
EXCEEDS RULE_SLATE-M1 (24 ids) and DAILY (10 ids) — a registered amendment
superseding those caps, declared, not hidden.

### Option B — scoped (LOL cut to the 6 live retire/measure legs)

Identical to Option A except LOL = ×6 {S014, S017, USDJPY-S002, S026, S003,
S023} = 6 identities / 36 rows:

- **Committed (with HN-5): 27 identities / 156 scored rows / 168 total**;
  without HN-5 (struck by owner): **25 / 144 / 156**.
- **Max (reserve consumed, with HN-5): 30 identities / 174 fold rows / 186
  total**; without HN-5: **28 / 162 / 174**.
- Caps: **≤32 identities** (30 max + 2), **≤204 total rows** (186 max +
  18). Within PC12A 48; exceeds RULE_SLATE-M1 24 / DAILY 10 (declared
  supersession).

**DEFERRED under Option B (nothing silently dropped):** LOL for 6 legs —
VC2-JPY, S009, S013, S046, VC2-EUR, GBPUSD-S002. Reasons: no live
retire/measure question registered (S009/S013 questions are rule-level and
carried by LORO×{HN-2, HN-1-EUR}; VC2 legs benched/not admitted;
GBPUSD-S002's open question is exit-law, DATA-BLOCKED as B-H-G2). Their
P-LOL cells are typed `NOT_RUN_LOL_DEFERRED`, and the P-LOL bar is scoped
to the 6 live legs.

**Disclosed degeneracies (dedup law):** (a) LORO(J3) with the guard's
default node REMOVED is byte-identical to SLATE — that identity is realized
as the guard-IN arm (SLATE+guard at the LEARN-frozen multiplier); (b)
LOL∖S017 ≡ SLATE once G1 retires S017 at registration — S017's two-sided
contrast is carried by LORO(G1); declaring LOL over ADMITTED legs (11)
saves 1 identity + 6 rows and is the cleaner law (−1/−6 from either
option); (c) crossed(J3)∖S026 ≡ LOL∖S026 (the guard acts only on S026) — no
extra arm. **Convention choice:** C2 fold rows counted INSIDE the row
budget (RULE_SLATE §5, stricter); the DAILY convention (outside) reads
186/150 committed (A/B). ×2.0 arms identity-classified (RULE_SLATE/E-Law 8);
the DAILY convention (rows-only, −2 identities) is a declared alternative.

**Arithmetic provenance:** computed by the budget/accounting lane and
re-verified by the controller (the lane's Option B prose said 29/168
with-HN-5; table-consistent arithmetic is 27/156 — corrected here; see
ERRATUM_V2 §1).

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
registration (protocol §3); validation folds measure the frozen artifact;
any composition change they motivate requires a new cycle.

— end design v2 —
