# PLAN — ECONOMIC-ROBUSTNESS-PROGRAM-V1 (umbrella governance program)

- Authored: 2026-09-25, A1, from explicit owner instruction (verbatim intent:
  adjudicate the current shadow strategies, then design a research program to
  find strategies with **economic robustness** — premium that survives
  measured costs, controls, ancestry and prospective verification).
- Status: `DRAFT_NOT_REGISTERED`. This file is a draft umbrella governance
  plan. It registers nothing, starts no worker, opens no S1, creates no
  broker account, places no order, and consumes no GO. Registration goes
  through `researchctl` only after owner review (proposed command in
  `research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/OWNER_DECISIONS.md`).
- Class: **UMBRELLA, budget 0/0 scored cells.** This program governs future
  child cycles; it must never itself contain authority to score cells across
  all asset families in one cycle. Every scored surface lives in a child
  cycle with its own plan, budget, freeze chain, A7 arc and GO phrase.
- Intake snapshot for this draft (measured 2026-09-25, root checkout):
  `main` @ `7343dde57fe86b38d205b0bec5e8af92a4c4404d`; heavy lock
  `FREE_PROVEN`; cycle doctor has pre-existing HIGH findings only for
  TERMINAL-cycle pause packets whose worktrees were archived
  (CRYPTO-V17 / FOREX-FREE-V8 / STOCKS-FREE-V12 `FROZEN_ARTIFACT_DRIFT`)
  — recorded, not repaired here (§3).

---

## 1. Objective and non-objectives

### 1.1 Objective

Find and validate strategies with **economic robustness**: a strategy whose
edge is an identifiable premium paid by an identifiable counterparty for an
identifiable risk transfer, measured under PIT-authorized data, **measured**
costs (not stated), causal controls that fail to reproduce it, ancestry that
is not a relabeled reject, chronological folds that do not concentrate, and
prospective (forward-only) evidence that continues the backtested behaviour —
or the honest conclusion that **no family deserves further research**.

Two deliverable arcs:

- **Arc 1 — Adjudication contract** for the current shadow strategies
  (§4): owner-specified dispositions, made operational and evidence-bound.
- **Arc 2 — Research program** over three priority tracks (§5.4):
  A. FX liquidity provision / RANGEFADE replication;
  B. delta-neutral crypto basis/carry (funding, borrow, margin, liquidation,
     venue risk);
  C. forced-flow/event premiums with directly observable flow.

### 1.2 Non-objectives

- No scored cells, backtests, heavy jobs, worker restarts, order placement,
  S1 access, registry writes, or ledger edits inside the umbrella itself.
- No rescue of rejected families by re-labeling, timeframe swap, threshold
  nudge, cost reduction or universe pruning (ancestry law §6).
- No gate weakening to manufacture a survivor. A cohort may end
  `REJECT_ALL`; that is a valid program outcome (§9).
- No promotion of any shadow sleeve by this document. Adjudication
  dispositions in §4 are **laws for future owner-gated child cycles and
  amendments**, not actions taken now.
- No live-readiness claim of any kind (§1.3).

### 1.3 Three claims that must never be conflated (binding vocabulary)

1. **Profitability** (a positive after-cost expectancy on observed windows)
   is a statistical claim about the past.
2. **Paper/shadow evidence** (forward-only virtual book) is an operational
   claim that the frozen identity keeps behaving prospectively under a
   declared cost book — it is *not* profitability proof and *not* execution
   proof.
3. **Live readiness** (broker cost authority, fill/latency reality, risk
   limits, kill switch, monitoring) is an engineering + authority claim that
   this program does not grant anywhere. Live/paper/testnet deployment
   remains owner-only external state (CLAUDE.md; handbook §29).

A strategy may hold claim 1 and fail claim 2. Holding 1+2 grants nothing
toward 3. Every artifact of this program labels which claim it supports.

---

## 2. Authority order and permission boundary

### 2.1 Authority order

1. Latest explicit owner instruction (command, not question).
2. The applicable child-cycle plan registered in `plans/CYCLE_REGISTRY.json`
   (the only writable cycle authority; writes only via `researchctl`).
3. This umbrella plan, for program-level laws that child plans inherit
   unless a child plan is **stricter**. A child plan may never be weaker
   than this umbrella without an explicit owner amendment of the umbrella.
4. `CLAUDE.md` + `HOW_TO_BE_A_LEAD_ENGINEER.md` (handbook v2).
5. Frozen manifests/ledgers; historical plans are evidence of the past.

### 2.2 Permission boundary of the umbrella cycle (when registered)

Allowed: governance bookkeeping; read-only intake and re-measure; A7-style
audits; adjudication reporting; drafting child plans and amendments for
owner GO; prospective shadow decision-count accounting (no PnL
computation beyond what sleeve ledgers already book).

Forbidden without separate owner authority: scored cells; heavy jobs; S1
access; worker stop/start/restart; foreign lock/process touch; orders;
credentials; purchases; push/merge to `main`; registry edits outside
`researchctl`; editing historical ledgers; strategy implementation changes.

### 2.3 One-live-session and lock laws

Handbook §3.2 (one Lead session per cycle) and §8 (machine-wide heavy lock,
`NOT_RUN_RESOURCE_CONFLICT` if held) apply to every child cycle. Shadow
sleeve workers are light pollers and must never hold the heavy lock
(PSV1 §E).

---

## 3. Phase 0 — control-plane recovery (gate for every child cycle)

Phase 0 is a **gate**, not a phase this draft executes. A child cycle may
open only when, re-measured at its own intake:

- P0-1 `researchctl cycle list` / `cycle doctor --json` / `locks inspect`
  captured; heavy lock `FREE_PROVEN` or held by that child for its bounded
  heavy operation.
- P0-2 **Lock-drift law**: if the heavy lock state is `CONTROL_STATE_DRIFT`,
  that child's Phase 0 is `BLOCKED`; no heavy/scored dispatch until the
  control-plane owner resolves it. Never repair-or-bypass inside a research
  cycle (owner instruction 2026-09-25, binding).
- P0-3 Pre-existing doctor HIGH findings are triaged: findings that affect
  the child's own freeze chain (its pause packets, its frozen artifacts)
  must be resolved; findings confined to TERMINAL cycles with archived
  worktrees (the 2026-09-25 class: `FROZEN_ARTIFACT_DRIFT` on
  CRYPTO-V17/FOREX-FREE-V8/STOCKS-FREE-V12 pause packets) are recorded as
  accepted-historical and do not block unrelated children.
- P0-4 Root owner changes preserved: `.zcode/`, `plan_at.md`,
  `research/control/DASHBOARD-AND-SHADOW-RELIABILITY-V1/`,
  `research/control/SANDBOX-OVERFIT-3ASSETS/`,
  `research/control/d2_curiosity_v1_sources/` are owner paths — never
  staged, cleaned or "tidied" by any lane.
- P0-5 Registry/projection/router consistency (`ROUTER_DRIFT` → STOP),
  one live Lead session, workers=0 for the child at bootstrap.

**Current Phase-0 status at this draft: PASS for light/plan work** (lock
`FREE_PROVEN`; the 14 HIGH doctor findings are all TERMINAL-cycle pause
packet drift, accepted-historical per P0-3). Not scored work — the umbrella
scores nothing.

---

## 4. Adjudication contract for current shadow strategies

All numbers below are re-measured 2026-09-25 from ledger bytes by the
explorer lane (`research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/plan_review/
EXPLORER_state_remeasure_REPORT.md`); the 2026-09-24 REVIEW.md numbers are
historical snapshots. Accounting definitions reconciled in §4.7. Each
disposition is owner-specified (instruction 2026-09-25); the "binding
conditions" columns are what a child cycle/amendment must implement.

### 4.1 FX RANGEFADE (EURUSD + GBPUSD, cycle FX-RANGEFADE-2M-SHADOW-V1)

**Disposition: `KEEP_PROSPECTIVE`. Parameters frozen — no change.**

Current measured state: journal 86 rows; 2 closed round trips realized
**+87 USD** (EURUSD +120, GBPUSD −33); both flat at 20:00Z daily as frozen;
workers alive (heartbeat fresh); **the journal has no fee/slippage/funding
fields at all** — it books gross price movement only (§4.7).

Binding conditions (implement via owner-GO amendment to
FX-RANGEFADE-2M-SHADOW-V1; none is a parameter change):

- **C-FX-1 Short-beta control arm MANDATORY.** Ancestors made it law:
  EURUSD-OPEN-SEARCH-V2 (SHORT_ALWAYS +314.0 pips beat C3 +274.0 on the
  same holdout; commit `bf4f07f1`) and EURUSD-RANGEEXP-SCORED-V1 (S6
  no-drift-flag but margins −17.3/−17.6 pips; commit `83264434`); FX-MAJORS
  added the JPY carry-beta analogue for USDJPY. Until the control arm is
  mounted and emitting records, every prospective PnL number of this sleeve
  carries the label `SHORT_BETA_UNSEPARATED — NOT PROMOTABLE`.
- **C-FX-2 Aggregate USD exposure accounting.** The two sleeves share one
  account and one quote source; same-side EURUSD+GBPUSD positions compound
  USD beta. The ledger/report must book aggregate same-side USD notional
  per decision epoch (display + record; capping exposure is an owner
  decision, not automatic).
- **C-FX-3 Stress-spread book.** A parallel cost view using the
  **event-time session spread curve ×2.0**, not the global median spread
  (range-edge fades fill exactly when spreads widen; data-cost critic
  condition). Declared cost book may continue as the primary book; the
  stress book is mandatory reporting from the first post-amendment event.
- **C-FX-4 Ledger cost fields.** Add per-fill fee/slippage fields to the
  journal schema (engineering-allowable, no exposure change) so round-trip
  win-rate is computable; without them the sleeve cannot be adjudicated at
  its 52-week gate.

### 4.2 BASISLV-PREMFADE-28D (PROSPECTIVE-SHADOW-V1 sleeve 2)

**Disposition: `KEEP_PROSPECTIVE_LOW_FREQUENCY` — observation only.**

Current measured state: 1 record, 2026-09-21 `DATA_BLOCKED` fail-closed
(vendor 286-bar gap; source healed; next weekly decision 09-28); 0 fills;
equity 100,000 FLAT.

Binding conditions:

- **C-BL-1 Price-only falsifier frozen now.** The family's identity
  manifest makes the price-only clause binding (historical edge was funding
  credit = carry harvesting, not premium fade — skeptic lane). The
  prospective report must always show price-only expectancy separately; if
  price-only prospective expectancy is non-positive over the adjudication
  window, the premium-fade mechanism is falsified prospectively.
- **C-BL-2 No rescue variants.** No 56/28-day swap, tercile change, delay
  change or universe edit. Any variant is a new strategy ID under §5.6.
- **C-BL-3 Power honesty.** Weekly cadence (≤52 decisions/year) sits below
  the 52-week two-sigma power bar for PF≈1.3–1.5 edges (REVIEW §2.2: the
  window resolves only annualized Sharpe ≥ ~2.0). This sleeve can produce
  *falsification* evidence (a clean negative) but never *promotion*
  evidence. Its only positive outcome is `OBSERVATION_CONTINUES`.
- **C-BL-4 Time-stop.** §5.13 law applies (13 valid weekly decisions =
  first interim adjudication; kill/time-stop preregistered there).

### 4.3 BTC4H-BANDRIDGE (PROSPECTIVE-SHADOW-V1 sleeve 4, amendment A1)

**Disposition: `CONDITIONAL_KEEP`.**

Current measured state: 61 records (56 forward-only fail-closed + 5 OK
no-trade since 09-24T08Z); **0 fills ever**; band gate currently ON
(band_r ≈ 0.066) but Donchian state 0; the ledger still carries the shared
cost digest `130d2e7e…` with **no 6 bps override in any record**; the
owner-decision field of the sizing packet remains blank.

Binding conditions — all three must be pinned **before the first fillable
decision is allowed to produce a fill**; any fill recorded before the pins
is labelled `UNPINNED_COST_LAW — NOT PROMOTABLE`:

- **C-BR-1 Sizing B (cost-aware, realized ≈ 0.99946).** Sizing A leaves the
  sleeve permanently unfilled (informational zero); sizing C breaks the
  no-leverage identity law. B is the recommendation carried from
  SHADOW-PAPER-REVIEW-V1 O1.
- **C-BR-2 Fill law A** — document the fill at the **first completed 15m
  bar** after the H4 decision (deterministic, PIT-safe).
- **C-BR-3 Cost-identity reconciliation.** Identity pin says 6 bps/side;
  the executor charges 5 bps + 1 tick. One side must be chosen and re-pinned
  in the identity manifest and the executor **before** the first fill; a
  dated cost-regime boundary (new frozen hash) is created either way. Never
  silently average the two.
- **C-BR-4 Disclosure carried.** The sleeve's S0 characterization shows
  F3 fold share ≈ 65% (single-regime money, the same structural pattern
  that killed ILLIQ/BASISLV ancestors at the 0.50 concentration gate).
  CONDITIONAL_KEEP never waives the concentration law at adjudication time.

### 4.4 ILLIQ-AMIHUD-28D-W (PROSPECTIVE-SHADOW-V1 sleeve 1)

**Disposition: `DIAGNOSTIC_ONLY` — not eligible for promotion; no rescue
variant.**

Current measured state: 1 decision (2026-09-21), 8 fills, booked total
**−63.21 USDT**; equity 100,348 MTM-inclusive. Ancestry chain (all labels
pinned): `V11_FAMILY_REJECT` (fold-share 0.7055) → CHR3F replication
outcome-exposed (S0R funded −56.31%; **mechanism INVERTED** in
2024-08..2025-08: INV +0.5459 vs anchor −0.5631) → ILLIQ-REG-V1 gate
FALSIFIED → ILLIQ-LOSS-MECH-V1 phase-1 complete: H_A `INCONCLUSIVE_VOID`
(no young cohort on the A4 universe), H_B `INCONCLUSIVE` (engagement
shortfall; no directional violation).

Binding conditions:

- **C-IL-1 Time-stop after 13 valid weekly decisions.** 13 valid decisions
  = first preregistered interim adjudication (PSV1 §7 13-week checkpoint;
  ILLIQ-LOSS-MECH-V1 ≥13-stamp law). At 13: if the prospective book is
  direction-consistent-negative or inverted-vs-anchor again, the sleeve
  STOPS (terminal `DIAGNOSTIC_CONTRADICTION`); if ambiguous,
  `DIAGNOSTIC_CONTINUE` to 26; nothing beyond 26 without a fresh owner GO.
- **C-IL-2 No promotion path exists from this sleeve**, by construction.
  Any ILLIQ-family promotion claim would require a new mechanism + new
  identity + this sleeve's outcomes disclosed as outcome-exposed ancestry.
- **C-IL-3 No rescue variant** (no gate retune — ILLIQ-REG-V1 already
  FALSIFIED the best gate; no age-floor rescue — H_A was VOID).

### 4.5 XSECT-FUND-CARRY-7D (PROSPECTIVE-SHADOW-V1 sleeve 3)

**Disposition: `RETIRE_CURRENT_IDENTITY` — ledger and evidence preserved
append-only.**

Current measured state (2026-09-25 bytes): 11 daily decisions, 52 fills,
booked **−349.85 USDT** decomposition: price_pnl −354.45 (≈ −(fee 286.43 +
slip 68.02)), funding +4.60, `net` field 0.0 (legacy), equity 99,094.92
(valuation-mark basis, §4.7). Cost:carry ≈ **77:1** on these bytes (66:1 at
the 2026-09-24 review snapshot: 302.83 vs 4.60) — the sleeve is measuring
cost, not edge (turnover ~0.62×/day; cost run-rate ~11%/yr vs funding
capture ~1.7%/yr). Historical label `CANDIDATE_FAIL` (top-fold 51.66%)
unchanged.

Binding conditions:

- **C-XS-1 Retirement is of the identity, not the evidence.** Ledger,
  manifests, dashboards history stay append-only; no rewrite; historical
  verdict labels pinned in every future citation.
- **C-XS-2 Successor law.** Any successor **must use a new strategy ID**
  and may not inherit this sleeve's prospective history as its own. The
  successor's rebalance law must be frozen as: **rebalance only when
  expected carry over the intended holding period ≥ full round-trip stress
  cost** (measured anchor: two-leg taker round trip ≈ 20–25 bps + funding
  uncertainty; in-downtrend funding ≈ 1.11 bps/day → breakeven ≈ 18–23
  days, 27–34 at 1.5× stress → viable only ≥3–5 week low-turnover holds;
  maker-only execution is the natural reframe and must be measured, not
  assumed).
- **C-XS-3 Retirement mechanics** (owner-GO child amendment): stop opening
  new virtual positions at a preregistered timestamp; book remaining
  holdings to natural expiry per frozen law; terminal row
  `IDENTITY_RETIRED_COST_DOMINATED`; dashboard card moves to retired
  history. Until that amendment, the sleeve keeps running untouched
  (worker-restart prohibition stands).

### 4.6 Context sleeve: XAUUSD swing — already terminal

Owner-removed 2026-09-24 (`XAUUSD_SHADOW_V1_OWNER_REMOVAL`); closeout at
`research/control/XAUUSD-SHADOW-V1/CLOSEOUT_OWNER_REMOVAL_2026-09-24.md`;
reopening is a new owner-registered cycle with fresh identity (registry
law). No action in this program beyond ancestry memory.

### 4.7 Accounting-definitions reconciliation (binding, measured 2026-09-25)

Three PnL bases coexist across sleeves; every adjudication artifact must
state which basis it cites (explorer report §2 is the authority):

1. **Crypto decision rows**: `total_pnl = price_pnl + funding_cashflow`,
   where `price_pnl` is **net of fee and slippage at the decision bar**
   (residual ≤ 0.005 vs −(fee+slip)); the `net` field is a legacy constant
   0.0 and MUST NOT be read as PnL; `gross` is an exposure fraction
   (Σ|target_weights|), not dollars; decision-row equity is
   MTM-inclusive, non-compounding.
2. **FX journal**: gross price movement only; **fee/slippage/funding fields
   do not exist** (C-FX-4 closes this gap). Until then FX "realized +87" is
   a gross figure.
3. **Realized vs fee vs slippage vs funding vs net equity** must always be
   reported as separate named fields, never merged into one "PnL" number;
   win-rate/profit-factor claims require the round-trip basis (C-FX-4,
   SHADOW-PAPER-REVIEW E1).

---

## 5. Research program — mechanism-first architecture

### 5.1 Outcome-blind mechanism council

Each cohort begins with a mechanism council of outcome-blind lanes: each
lane receives NO scored outcome files and NO winner information (handbook
§12.5). The council's output is mechanism proposals only (§5.3 format). The
council's kills happen **pre-PnL** (§5.5). Composition per cohort: explorer
(evidence), skeptic (falsification), data/cost critic (measurability),
plus blind proposers. Council artifacts land under the child cycle's
control namespace with `zcode_orch_v3_handoff@1` handoffs at exact dispatch
paths.

### 5.2 Maximum three mechanisms per cohort

A cohort freezes **at most three (3) mechanisms** into trial freeze (§5.7).
Fewer is allowed; more is forbidden. Rationale: the program's measured
multiple-testing reality (DSR 0.00224 over N=146 — V14 terminal; EURUSD
open-search 1/48 survived selection then failed its one holdout look —
EURUSD-OPEN-SEARCH-V1 registry row; 0/60 scan-matrix PASS — NOTES.md
§18.1). A fourth mechanism requires a new cohort with its own budget and a
fresh council — never quiet expansion mid-cohort.

### 5.3 Proposal format (mandatory fields, frozen pre-outcome)

Every mechanism proposal must state, in one page, all of:

1. **Payer** — who is forced/impatient/risk-averse and pays (and why they
   cannot or will not arbitrage it away).
2. **Premium** — what is harvested, in expected bps per decision/period.
3. **Persistence** — why the premium persists (structural, regulatory,
   behavioral, balance-sheet) and what would erode it.
4. **Risk transferred** — what risk the strategy absorbs (the premium is
   rent for this risk; name the tail).
5. **Observable** — the PIT-authorized measurable that encodes the
   mechanism, with availability evidence (event/effective/available/
   retrieved separated; handbook §13).
6. **Holding horizon** — intended holding period and decision clock.
7. **Capacity** — notional at which the edge halves (order-of-magnitude,
   with reasoning from top-of-book/ADV).
8. **Costs** — full round-trip cost decomposition at base and stress
   (measured, not stated; §8).
9. **Falsifier** — the observable result that would kill the mechanism
   (with the specific control that must NOT reproduce it).
10. **Control and baseline** — the causal control, the inverted control,
    and the simple baseline it must beat (§5.7).

A proposal missing any field is `BLOCKED_INCOMPLETE`, not amended by A1.

### 5.4 The three priority tracks

**Track A — FX liquidity provision / RANGEFADE replication.**
Verdict (skeptic): `SURVIVES_AS_HYPOTHESIS` — the only program ancestor
that survived a fresh one-look holdout at 2.0× cost and replicated
cross-pair in a directionless window (GBPUSD +164.2 pips holdout where all
baselines lost). Data authority: measured (Dukascopy M1 bid/ask corpora
sha-pinned; spreads 0.3/0.8/0.5 pips p50). Gaps: broker cost authority
BLOCKED (DATA-EDGE-UNLOCK-V1 lane F: ten components unmeasured; stress 2.0
frozen pre-outcome) → child cycles run on the paper-shadow cost book under
the data-cost critic's **five binding conditions verbatim**
(DATACOST_critic_REPORT.md §1.2):
1. Verdict class bounded: output can only ever be
   `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION` (paper tier); no paper PASS
   may promote toward real-money inference without Lane F
   `PASS_BROKER_COST_AUTHORITY` (FOREX-NG8 stays closed per standing law).
2. Structural-zero financing enforced, not assumed: flat-by-20:00 UTC as a
   force-flat **fixture** in the executor (weekend holds likewise) — the
   V1 pandas force-flat bug precedent.
3. Per-session spread, not global p50: the executor charges the measured
   session/rollover spread curve at event time (sha-pinned census); the
   frozen ×2.0 stress applies to per-regime medians.
4. Adverse selection declared unmeasurable: fill quality (queue position,
   pick-off) is not observable in M1 bid/ask corpora — named declared-class
   in every verdict, stress-covered, never assumed into a measured number.
5. Marks-vs-fills seam disclosed: TrueFX 15s indicative marks vs
   Dukascopy-bar fills; the seam is disclosed in each report.
Cohort-A mechanism space: who pays at range edges (stop-flow,
mean-variance rebalancers, session liquidity cycles), on which pairs, at
which session boundaries — replication targets EURUSD/GBPUSD/USDJPY + at
most two new pairs with pre-registered carry-beta/short-beta controls.

**Track B — delta-neutral crypto basis/carry.**
Verdict (skeptic): `VETO_RISK_HIGH`; survives only as a reframed, stricter
child. Measured reality: the live XSECT shadow books cost:carry ≈ 66:1;
BASISLV's binding price-only clause marks its historical edge as carry
harvest; fold-concentration + DSR kills; FOREX-V4 carry ancestry rho
0.997–1.000. Track-B children must be: (a) **delta-neutral spot–perp
basis/funding carry with new strategy ID**, (b) **low-turnover by law**
(rebalance only when expected carry ≥ full round-trip stress cost; ≥3–5
week holds per §4.5 numbers), (c) **price-only disclosure clause** (if the
net edge is funding credit only, say so — that is Track-B premium, not
alpha from information), (d) **funding-path stress mandatory** (24.7% of
in-downtrend settlements negative; worst −0.30% ≈ 2.5 fee round trips in
one 8h tick), (e) venue-risk and liquidation-risk stated even when
unmeasured-blocked: **borrow rates, spot margin terms, liquidation tape
are BLOCKED data** — levered variants are not scoreable until a data
authority cycle unblocks them; unlevered perp-only funding carry and
cash-and-carry with disclosed venue risk are the scoreable forms.
Maker-only execution assumptions must be measured (queue-position
observable) before being used in a cost book.

**Track C — forced-flow/event premiums, directly observable.**
Verdict (skeptic+critic): `VETO as a pre-PnL strategy track today`; the
lawful child is **data-authority first**. Measured: liquidation feed 404 /
`liquidationSnapshot` ZERO coverage; multi-year PIT OI absent (OI
overwritten ~41.6h); cross-venue keyless collectors 34 min << 14-day
floors (lane-C contract: 303/336 + 152/168 STRICT, ≥4 cells/control/fold,
≥4 weekend days); keyless WS channels prospective-only and exclude depth
of book (Coinbase l2 rejected keyless; Deribit trades rejected); every
flow proxy already measured-dead (V13 LIQEPIS negative; V17 OICASCADE sham
out-earns; OI-level rho 0.3904; bear-recon double veto with 91.1% of
events in one COVID week). Track-C child #1 is a **collection cycle** on
the frozen lane-C contract; proposal lanes open only after floors pass.
Index-rebalancing/ETF-flow variants inherit the same law: observable
first, hypothesis second.

### 5.5 Pre-PnL mechanism falsification (gate before any scored cell)

Each frozen mechanism must survive its falsifier battery pre-PnL:

- ancestry rho vs the failure registry (§6) at the immovable 0.20 bar;
- its causal control must be **constructible** (a null that MOVES the
  signal; Q-11) and the inverted control must be runnable;
- clock-only and placebo shadows must not already explain the observable
  (release-calendar geometry killed RATES/COMMODITIES/V8; block-shuffle
  killed PSV1 timing; the S6 no-drift-flag law for fades);
- feasibility on the **nearest window** (Q-6), not archive average;
- cost-survivability ceiling: expected gross premium per holding period vs
  measured full round-trip stress cost — if the ceiling is negative, the
  mechanism is vetoed **before** scoring (VOL-NG1 precedent).

### 5.6 Child-cycle creation law

- A child cycle is created by owner GO on a child plan that cites this
  umbrella, names its track, its budget (scored-cell cap), its own GO
  phrase, and inherits §§5.3–9 unless stricter.
- **One asset family (or one mechanism cohort) per child cycle.** The
  umbrella grants no authority to score across all families in one cycle.
- Registration only via `researchctl cycle register`; the umbrella never
  pre-fills a child's GO; a child's GO phrase is typed fresh at the child's
  own gate (P-8).
- A child may not reopen a TERMINAL cycle's identity; successors take new
  IDs and disclose outcome-exposed ancestry (PSV1 §14 law).

### 5.7 Trial freeze contract (per child, before any scored computation)

Each frozen trial names:

- **one anchor** configuration (the mechanism's canonical form);
- **at most two neighbours** (parameter-support checks, e.g. one faster,
  one slower), never a grid;
- **one causal control** (removes the mechanism's information, keeps the
  exposure shape — e.g. clock-only shadow, sham-calendar, block-shuffle);
- **one inverted control** (sign-flipped book);
- **one simple baseline** (buy-and-hold / always-on / flat, per asset
  convention).

Frozen fields: hypothesis ID, universe, clock, warmup, features/lags,
entry/exit/fills, cost tier, fold contract, arm digests, trial budget,
thresholds with exclusion-zone logging (Q-12). Exact-arm dry-run must be
non-vacuous and leak-scanned (§5.11 reproduction class).

### 5.8 Observed vs published trial accounting

Two denominators per child and program-wide (P-9): every scientifically
computed outcome enters **observed** even if publication fails;
**published** counts only landed ledger rows. Prospective shadow sleeves
accrue decision counts (not scored cells) in a separate exposure ledger;
their outcomes are outcome-exposed ancestry for future blind discovery.
Intake snapshots ≠ current totals; current totals only from canonical
ledger.

### 5.9 Nested chronological walk-forward

Child scoring uses nested chronological folds: outer folds chronological
and non-overlapping; any in-fold tuning (none expected under §5.7) would
require inner walk-forward disclosed in the freeze. Force-flat at fold
boundaries; no fold-window substitution after any PnL is seen; fold
concentration reported against the §5.14 concentration law.

### 5.10 Sealed S1 one-shot law

S1 stays `SEALED_UNTOUCHED` everywhere (verified in registry for every
live/terminal cycle). Opening S1 requires: a Stage-A survivor from a child
cycle, an umbrella-level owner GO phrase typed fresh at a dedicated gate,
a sealed-criteria document (both data AND thresholds sealed — Q-9), and a
single unseal event. One shot per strategy identity: a failed S1 look is
terminal for that identity; no re-seal, no second look (one-shot law).
S1 outcomes enter observed denominators.

### 5.11 Independent reproduction and fresh-context A7

Before any S1 request or shadow promotion: detached reproduction at exact
hashes (record IDs, schedules/fills, costs, folds, verdicts byte-identical
modulo wall-clock fields) AND a fresh-context A7 audit that recomputes from
bytes, does not repair, and returns verdict + findings. A7 REFUSED is a
normal remediation arc (V15/V16/EURUSD-RANGEEXP precedents). Positive
claims get the stricter audit (handbook §22.2).

### 5.12 Prospective shadow decision-count gates

Shadow sleeves are adjudicated on **valid decision counts**, not calendar
alone (a DATA_BLOCKED week is not a valid decision; XAUUSD's ~1 entry/5.1
years is the measured failure mode of trade-count gating):

| Gate | Decisions (valid) | Allowed conclusion |
|---|---|---|
| D13 | 13 | interim: operational health + early falsification only |
| D26 | 26 | interim: falsification or OBSERVATION_CONTINUES |
| D52 | 52 | first full adjudication vs preregistered laws |
| D104 | 104 | final unless a preregistered extension law fired |

Weekly sleeves reach D52 ≈ 1 year; daily ≈ 52 trading days is D52-class
only if the child froze that equivalence (else the calendar power law §5.14
governs). Sub-power positives are `INCONCLUSIVE`, never PASS (critic law).

### 5.13 Preregistered promote / kill / time-stop laws

Preregistered at child freeze, per sleeve/mechanism, before data accrues:

- **PROMOTE(x)** — exact inequality set (net expectancy > 0 at base cost;
  ≥ threshold at stress; fold/concentration laws; control does not
  reproduce; baseline beaten; DSR reported). Promotion = eligibility to
  request S1 (§5.10) or a confirmatory plan — never live deployment.
- **KILL(y)** — exact failure set (any preregistered gate FAIL; inversion
  control out-earns anchor; cost-survivability ceiling negative). Kill is
  terminal for the identity; ancestry registry updated.
- **TIME-STOP(z)** — "if by N valid decisions / date Z the sleeve has
  produced < m fillable decisions or remains sub-power ambiguous, STOP" —
  the XAUUSD law (KILL_UNFUNDABLE class) and the ILLIQ D13 law (§4.4) are
  instances. Time-stop is an honest closure, not a failure verdict.

### 5.14 Default evidence guidance (floor values; child freezes actual bars
after pre-freeze power analysis)

The following are program **floors** — a child plan must run its own power
analysis at freeze and may only raise them (never lower) unless the
umbrella is amended by owner:

- FX intraday: ≥100 closed round trips AND ≥6 months;
  (power note: n=100 detects per-trade SR≈0.20 / PF≈1.5 at 2σ; PF≈1.3
  needs n≈236 — children targeting thin edges must raise n accordingly).
- H4: ≥100 closed trades AND ≥2 volatility regimes, each regime passing
  preregistered occupancy floors (TWO-REGIME measured 20/3/100 floors
  failing in 6.7y — regimes are a disclosed control unless floors pass,
  else `NOT_RUN_THIN`); the owner-stated 50-trade floor is retained as a
  smoke/screening floor only, never adjudication.
- daily: ≥100 valid decisions as smoke floor; adjudication floor 252
  valid decisions unless the child's power analysis justifies fewer with
  a thicker edge (power note: 100 daily decisions implies a ~3.17
  annualized-Sharpe bar at fixed-window law — internally inconsistent
  with the 2.0 program bar if used for adjudication).
- weekly: ≥52 valid decisions (sub-power for PF 1.3–1.5 by §5.12 law —
  weekly sleeves adjudicate falsification-first).
- positive net result under base (measured) cost;
- non-negative under 1.5× stress unless the child froze stricter;
- 2.0× stress always reported;
- majority of chronological folds positive;
- top fold/event contribution ≤ 50% of positive PnL, unless the child
  preregistered and scientifically justified an alternative concentration
  statistic before any outcome;
- beat the simple baseline AND the causal control must not reproduce the
  edge;
- Deflated Sharpe Ratio reported across ALL program trials of the cohort
  (per-period series persisted — V15/V16 driver lesson);
- PBO computed only where the frozen variant/fold structure supports it
  (≥8 configs class; else NOT_RUN fail-closed);
- independent reproduction before any S1 unseal or shadow promotion.

### 5.15 Portfolio aggregation contract (reporting layer across sleeves)

Mandatory aggregate reporting (display + record; caps are owner actions):

- **BTC/crypto beta**: aggregate across crypto sleeves (BANDRIDGE long-only
  w≈1, XSECT funding-credit-in-bull-regime, ILLIQ gross-neutral-but-tail);
  report aggregate beta to BTC and to a crypto index.
- **USD beta**: aggregate same-side FX notional (EURUSD+GBPUSD share one
  account; short-beta control quantifies it).
- **Correlation + drawdown overlap**: pairwise return correlation of
  sleeves; joint drawdown overlap statistics (two "diversified" books
  peaking in the same week is one book).
- **Capacity**: per-sleeve capacity estimate (§5.3 field 7) aggregated —
  sum of individually-viable capacities is not portfolio capacity where
  sleeves share order flow.
- **Venue concentration**: single-venue dependency (Binance for 4 crypto
  sleeves — one 418/outage kills four sleeves; the 2026-09-21 shared-IP
  418 outage precedent, CHR3F plan §0.4; TrueFX for both FX sleeves).
- **Data-source concentration**: single-source risk per sleeve with the
  BASISLV 286-bar-gap lesson; gateway cutover (LIVE-DATA-GATEWAY-V1) is
  the standing mitigation and remains owner-gated (SHADOW-PAPER-REVIEW-V1
  item O6; owner D8 2026-09-25: not yet approved).

---

## 6. Ancestry and failure-memory audit (standing law)

- Every proposal runs the ancestry gate against
  `research/wayfinder/FAMILY_FAILURES.jsonl` + MAP closed-bullets: pooled
  |rho| ≤ 0.20 vs named dead shadows (immovable bar; NG-generation law),
  plus class vetoes (re-clock, calendar geometry, displaced-fade,
  nominal-level exposure, vol-level, premium-fade ancestry
  −0.418/−0.515 measured in bear-recon).
- No family rejected under this program re-enters by timeframe/threshold/
  symbol/fee/name/sign/session change (handbook §14.3; Q-3).
- The failure registry is append-only; kills are assets (Q-16); every
  cohort's DSR uses the full program trial history.

## 7. PIT, license, timestamp, calendar, survivorship contract

- Three timestamps separated (event/effective/available; retrieved is not
  availability); no self-assumed `available_time`; measured beats stated
  (Q-8) for every vendor constant (spread, fee, coverage — the 21,000× fee
  error and the 7.8× funding constant are the standing precedents).
- License gate per source: `DOCUMENTED_CANDIDATE → AUTHORIZED_INTERNAL_
  RESEARCH | UNAVAILABLE_FAIL_CLOSED | REJECTED_LICENSE`; free ≠
  authorized; FX sources carry `OWNER_DIRECTIVE_SOURCE_AUTHORIZATION` with
  `TCU_RISK_DISCLOSED` where applicable.
- Calendar law: exchange/session calendars per asset; DST/rollover
  fixtures; TradFi historical backtests may not synthesize holiday
  schedules (Binance TradFi §13.6 law); weekend/quiet-hours effects
  disclosed (funding Settlement clock).
- Survivorship: PIT listing/delisting universes (dead names +
  never-existed canaries per channel — bundle ≠ endpoint, P-7);
  cross-sectional books state their dead-name treatment; death-inclusive
  panels where the asset class has them.

## 8. Measured-cost and stress-cost contract

- Primary cost book = **measured** components only (spread curves by
  session/size where measurable, fees from venue-published tiers validated
  against fills, funding from settlement series, slippage from
  replay-vs-fill where available). Declared components are allowed only in
  a clearly-labeled declared book that never overrides the measured book.
- Stress: per-track laws, not one generic multiplier — FX: event-time
  session spread ×2.0 (frozen); crypto carry: funding-path stress + fee
  ×1.5/×2.0 + turnover budget from the breakeven horizon; events: adverse
  gap/queue assumptions at event time.
- Cost-regime boundaries are dated + hashed; venue fee changes never
  rewrite history in place.
- The BANDRIDGE 6bps-vs-5bps+1tick case is the standing example: two cost
  laws for one sleeve is `UNPINNED_COST_LAW` until reconciled (§4.3).

## 9. Final verdict vocabulary

Child-cycle terminal verdicts draw from (umbrella-superset; children may
specialize but never weaken):

```text
REJECT_ALL                       no mechanism survived its falsifier battery
NO_ELIGIBLE_PROPOSAL             council produced zero freezable mechanisms
BLOCKED_DATA_OR_SELECTION       data/ancestry gate closed before scoring
BLOCKED_SOURCE_OR_SCHEMA         source/license/schema fail-closed
BLOCKED_COST_AUTHORITY           cost unmeasurable in authorized space
CANDIDATE_PENDING_PROSPECTIVE    survived scored gates; needs forward evidence
PROSPECTIVE_VERIFIED             forward window confirmed (still not live-ready)
PROSPECTIVE_FALSIFIED            forward window killed the identity
IDENTITY_RETIRED_<reason>        shadow retirement (e.g. COST_DOMINATED)
DIAGNOSTIC_<outcome>             diagnostic-only sleeves (ILLIQ class)
TECHABORT_PRESERVED              technical invalidation, evidence kept
```

`REJECT_ALL` is an explicit, expected, non-failure outcome of the program.

## 10. Proposed child-cycle sequence (proposal only — none created)

Ordered by information value per unit cost (critic + skeptic ranking):

1. **ERP1-AMEND-FX-CONTROLS** (amendment to FX-RANGEFADE-2M-SHADOW-V1):
   C-FX-1..4 (short-beta control mount, USD exposure, stress-spread book,
   ledger cost fields). Unblocks the only strong track's interpretability.
2. **ERP1-AMEND-BANDRIDGE-PIN** (amendment to PROSPECTIVE-SHADOW-V1):
   C-BR-1..3 pins before first fill; disclosure C-BR-4.
3. **ERP1-AMEND-XSECT-RETIRE** (amendment to PROSPECTIVE-SHADOW-V1):
   C-XS-1..3 retirement mechanics at a preregistered timestamp.
4. **ERP1-ILLIQ-TIMESTOP-GOVERNANCE** (light, under this umbrella):
   declare the D13 adjudication window for the ILLIQ sleeve (C-IL-1).
5. **ERP1-TRACKA-COHORT-1** (new child, forex): mechanism council for FX
   liquidity provision; ≤3 mechanisms; RANGEFADE replication targets +
   controls; budget per child plan.
6. **ERP1-TRACKB-CARRY-DELTA-NEUTRAL-V2** (new child, crypto): new-ID
   low-turnover delta-neutral funding/basis carry with cost-survivability
   ceiling, price-only clause, funding-path stress; unlevered forms only
   until borrow/margin data authority unblocks.
7. **ERP1-TRACKC-FLOW-DATA-AUTHORITY** (new child, data): resume lane-C
   collectors to the frozen 14-day floors; zero proposal lanes; coverage
   report is the deliverable.
8. Re-assessment checkpoint after 1–7: owner reviews; cohorts 2 of Track
   A/B only if cohort 1 left falsification room.

Each child: own plan, own budget, own GO phrase, own A7 arc; umbrella laws
§§5–9 inherited.

## 11. Umbrella governance and close

- The umbrella cycle (when registered) is `ACTIVE_LIGHT`, budget 0/0, no GO
  phrase (nothing to launch). It closes when the owner ends the program or
  supersedes it; its artifacts are the adjudication reports, child-plan
  charters and this law set.
- Denominators: the umbrella never touches scored denominators; children
  do, under P-9.
- Incidents, drift, and any sleeve-accounting mismatch are recorded per
  handbook §26 in the child/umbrella control namespace.

## 12. Verdict of this drafting session

Draft complete; awaiting owner decisions
(`research/control/ECONOMIC-ROBUSTNESS-PROGRAM-V1/OWNER_DECISIONS.md`) and
A7 plan audit (`.../plan_review/`). Nothing executed, nothing scored, no
worker touched, S1 untouched, no orders.
