# SKEPTIC_REVIEW — PORTFOLIO-COMPOSITE-12ASSETS-100K-V1 (pre-GO, Lane S, session 2, 2026-09-29)

Independent adversarial review of the amended pre-GO package: eligibility
ladder v2 (292), draft plan v2, campaign design, policy architecture
(§0 amended, §10 superseded), PASS_BARS_V2, FILL_ACCOUNTING_SPEC (+C2
erratum), 5 fixtures, VOLPROF-M1 class spec r1, Lane D physical audit, Lane R
triage + 4 slates + feature inventory + missed-profit plan. Method: every
number below was re-derived with my own scripts (`build_portfolio_eligibility`
NOT executed — I re-implemented the blocking rules from my own reading), the
five fixtures were re-computed by a from-scratch engine written against the
spec text only, and every label claim was joined back to CENSUS_1200.tsv and
SLEEVE-FX5 F0_VERDICTS.md. No git operations, no network, no S1, no strategy
simulation. Write scope: this file + `handoffs/S_skeptic.json` only.

**Headline:** the package's disclosure culture is unusually honest and its
accounting core is verifiably clean (all 5 fixtures reproduce independently to
≤1e-12; the C2 erratum chain is faithful end-to-end to the machine audit
output; all 1,200 eligibility rows reconcile exactly to census + F0 inputs).
But the **binding PASS-bar authority contains one vacuous central bar (F-1,
CRITICAL), one degenerate governing baseline (F-2, HIGH) and budget
arithmetic that cannot hold (F-3, HIGH)** — text defects that are cheap to
fix now and lethal to discover after registration. The ladder v2's PIT axis
mislabels ~half of the 292 candidates (F-4, HIGH) — mitigated in practice by
Lane R's triage, but the plan repeats the ladder's claim as "PIT chain
provable".

Counts: **1 CRITICAL · 4 HIGH · 7 MEDIUM · 7 LOW · 6 INFO** (25 findings).

---

## CRITICAL

### F-1 — P5a's pass condition "DSR > 0" is VACUOUS: the amended protocol's central multiple-testing bar does not bind

**Severity:** CRITICAL — wrongful-admission hole at the exact point the owner's
amendment made binding ("the wider search makes DSR/PBO MORE binding, not
less").

**Evidence:** `policy/PASS_BARS_V2.md` §5, lines 232–241:

```
DSR       = Φ( (SR̂ − SR₀)·sqrt(n−1) / sqrt(1 − γ̂₃·SR̂ + ((γ̂₄ − 1)/4)·SR̂²) )
P5a = PASS iff  DSR > 0
```

DSR as defined is a normal CDF value — strictly positive for ANY finite
argument. `Φ(x) > 0` holds for every finite x, i.e. for every arm with
defined returns, whatever its Sharpe, whatever N, whatever V. P5a cannot
fail (except degenerate undefined-input cases). The transcription error is
inherited from V1 (`PORTFOLIO_POLICY_ARCHITECTURE.md` §10 "P5 DSR>0") and
from `campaign/BACKTEST_CAMPAIGN_DESIGN.md` §5 ("DSR (deflated Sharpe) over
all completed trials" — no threshold stated anywhere). Bailey & López de
Prado's construction tests **DSR > 0.95** (or, equivalently, drops the Φ
wrapper and tests `SR̂ − SR₀ > 0`). As frozen, P5 = P5a AND P5b reduces to
PBO ≤ 0.5 alone; the deflation bar over the 500–1,500-row discovery ledger —
the protection the owner was told prices the 292-wide reopening — is a no-op.

**What would resolve it:** one-line amendment of the frozen text before
registration: `P5a = PASS iff DSR > 0.95` (or `SR̂ > SR₀` with the Φ wrapper
removed), plus the calibration duty in F-6. Until then every "PASS_BARS_V2
governs" statement in the package certifies a bar that cannot fire.

---

## HIGH

### F-2 — B2 EQUAL_WEIGHT's realization formula is degenerate/ambiguous and contradicts P2's own N=1 edge case (governing bar P2a cannot be lawfully evaluated)

**Severity:** HIGH.

**Evidence:** `policy/PASS_BARS_V2.md` §1 line 91: B2 = "eligibility pinned
ON **and** L3 vol-targeted risk weights replaced by equal risk per leg
(**0.5/N of the frozen per-leg cap** each); L4–L6 identical to the policy".
Per-leg cap = 0.375% (architecture §3). Reading the formula literally, every
leg is sized at (0.5/N)×0.375%, so **B2's total book is 0.5×one-leg-cap =
0.1875% equity risk regardless of N** — vs the policy's portfolio heat of up
to 6.0% (architecture §5). At N=12 each B2 leg carries 0.0156% risk; B2's USD
maxDD is then structurally ~an order of magnitude smaller than the policy's,
making P2a's strict DD leg (`maxDD(P) < maxDD(B2)`) near-unpassable, while
its PnL leg is trivially passed by sizing alone — the bar degenerates in both
directions. The formula also **contradicts P2's own edge case** (§3 lines
168–170): "Single admitted leg (N=1): B1 = B2 = B3 coincide with the leg run
always-on" — at N=1 the formula gives 0.1875%, not the leg's L3 vol-targeted
size, so B2 ≠ B1 at N=1. One of the two sentences is wrong.

**What would resolve it:** pin B2's sizing as an actual equal split of a
portfolio-level risk budget (e.g., each leg at `min(per-leg cap, frozen
portfolio heat / N)`) and restate the N=1 case consistently; regenerate the
matrix row.

### F-3 — Stage-C budget caps are arithmetically incompatible with PASS_BARS_V2's own battery (24 vs 48 vs ≥100 seeds)

**Severity:** HIGH — a self-triggering STOP-2 by construction.

**Evidence:** `policy/PASS_BARS_V2.md` §1 line 93 + §4 lines 197–205: B4
RANDOM-GATE is "≥100 seeds, seed list frozen in the trial identity", "the
full B4 battery (all seeds), each seed an independent duty+turnover-matched
randomization"; P3 fails as `NOT_RUN_RANDOM_BATTERY` below 100 seeds. Each
seed arm is a scored execution on the pooled test folds. Minimal battery:
policy 1 + B0–B8 (9) + ≥100 seed arms + P6a/P6b/P6d stress pairs (≈6) + P8
leave-one-leg (2 arms × N ≤ 12 legs = 24) ≈ **140 arm-executions**. Against
this: plan v2 §4 caps "Stage-C scored arm-executions … **48**";
`campaign/BACKTEST_CAMPAIGN_DESIGN.md` §6 line 106 caps T2 at "**≤24**
(policy 1 + baselines 9 + robustness 14 …)" — a line that counts the
100-seed battery as if it were ONE arm — and `SESSION_REPORT.md` repeats
"≤24 scored arm-executions". Three mutually inconsistent numbers, all below
the battery the same package declares mandatory. Either the seed arms are
exempt from the cap (nowhere stated) or the campaign violates its own STOP-2
budget gate the moment P3 runs.

**What would resolve it:** state explicitly whether B4 seed arms count
toward the scored-arm-execution cap; recompute the cap (≈140–150 if they
count) and reconcile plan §4 / campaign §6 / SESSION_REPORT to one number
before the owner packet.

### F-4 — Ladder v2's PIT screen mislabels ~half of the 292 candidates; plan v2 §2 repeats the mislabel as "PIT chain provable" — while over-blocking other rows on keyword false-positives

**Severity:** HIGH (mitigated in practice by Lane R's triage; not mitigated
in the plan's and amendment's phrasing, nor in the machine-consumable
`pit_class` column).

**Evidence (all independently measured):**

1. **89 of the 292** EXPLORATORY_CANDIDATE rows carry census verdict
   `PIT_UNPROVEN` (CENSUS_1200.tsv `verdict` column) — the ladder admitted
   them anyway because its keyword classifier
   (`eligibility/build_portfolio_eligibility.py` lines 41–55) never consults
   the census's own PIT verdict. The ladder then labels 70 of them
   `PRICE_ONLY`, 11 `PRICE_PLUS_CALENDAR`, 8 `MACRO_PIT_EVIDENCED_PARTIAL`.
2. My independent token-level reading of `required_pit_data` for all 292
   (evidenced estate = own/derived-cross prices of the 5 pairs, EFFR, VIX
   daily close, Brent/WTI daily spot close, deterministic date calendars)
   finds **137/292 with at least one unevidenced required input** —
   consensus/surprise vintages (EURUSD-S016/S051, GBPUSD-S054/S055, …),
   equities (USDJPY-S062/S068/S090, AUDUSD-S067, EURUSD-S069), gilts/UST/ACGB
   (GBPUSD-S038/S062, AUDUSD-S008/S035, USDJPY-S061), options IV/RR/fly
   (AUDUSD-S076/S092/S094, USDCAD-S077, GBPUSD-S070/S094), OI/COFER/ETF-AUM
   (EURUSD-S073/S078, AUDUSD-S077/S078), copper/gold/iron-ore/NATGAS/TTF
   (EURUSD-S063/S068, AUDUSD-S061/S068/S070, USDCAD-S065/S070), DXY (via the
   blocked-list direction — correctly blocked), news/text/auction archives
   (GBPUSD-S052/S058/S077, USDCAD-S060, USDJPY-S052/S054/S058), blocked-symbol
   prices as inputs ("daily closes of 7 USD pairs incl USDCHF and NZDUSD" ×2,
   "6 JPY crosses (NZD/CHF legs unevidenced)" — the text itself says
   unevidenced), MOVE (USDCAD-S097). **129 of my 137 are confirmed by Lane
   R's own T3_PARK reasons** (each names the unevidenced input) — the
   package's own second layer contradicts the first layer's labels. 8 remain
   in the runnable set: 6 defensible (optional inputs or declared-off
   couplings — AUDUSD-S060 "(+ IV optional)", USDCAD-S069 "WCS optional",
   EURUSD-S021/S022 couplings declared-off, GBPUSD-S056 date-calendar,
   USDCAD-S078 vol-metric re-expressed on own panel) and **USDJPY-S020,
   which is a genuine PIT-lookahead trap (F-10)**.
3. The reverse error: 18 rows blocked `BLOCKED_PIT_UNEVIDENCED` on keyword
   false-positives. The clearest: **USDJPY-S012** (Tokyo range fade) —
   `required_pit_data` "H1 OHLC repo; Japan news calendar (public schedule)"
   hits the 'news' keyword; under Lane R's own class-(iii) convention
   (GROUPING_PROPOSAL §1.1: release/event DATE calendars are "deterministic
   public, not staged" → cap at T2, not park) this row is runnable-with-
   staging. USDJPY-S012 is one of the 15 F0-court rows
   (REJECT_VARIANT_SAME_FAMILY) and census DISTINCT_TESTABLE — i.e. **an
   F0-adjudicated diagnostic row is excluded from the diagnostic pool on a
   technicality the same package treats as non-blocking elsewhere**, while 89
   PIT_UNPROVEN rows were admitted. The screen is noisy in both directions,
   so the headline "292" is a convention artifact, not a measurement.
4. Downstream phrasing repeats the mislabel as fact: plan v2 §2 (lines
   54–63) "a corpus idea is an EXPLORATORY candidate iff implementable — …
   **PIT chain provable** … 292 rows qualify (ladder v2)"; amendment §3
   presents the BLOCKED_PIT_UNEVIDENCED=115 / 292 partition as a clean
   screening. The eligibility summary's reading rule 0 ("the badge certifies
   panel/data/cost gates only, NOT input availability") is the honest
   disclosure — but the plan oversells it, and the `pit_class` column (which
   Lane R's handoff advertises as joinable machine input) is wrong for ~47%
   of candidate rows.

**What would resolve it:** (a) plan v2 §2 and amendment §3 re-worded to
"292 rows pass a keyword PIT screen with disclosed blind spots; the
operative input-evidence layer is Lane R's triage (147 runnable)"; (b) the
ladder's `pit_class` column annotated or regenerated from the triage's
input-evidence findings; (c) the 'news'-keyword false-positives (at minimum
USDJPY-S012, USDCAD-S048) re-adjudicated under the class-(iii) convention —
including whether the owner wants F0-court rows in the diagnostic pool.

### F-5 — SOFR is falsely asserted to be an evidenced PIT input in three artifacts (the dossier pins only EFFR/VIX/Brent−WTI)

**Severity:** HIGH (contained today by parking, but it sits in the LAW a
future engine would consume).

**Evidence:** `pit/PIT_DOSSIER.md` (pr12a100k, in the portfolio-router
worktree) is titled "macro state-variable channels (VIX, Brent, WTI, EFFR)"
and contains G-PIT-V1 EFFR / G-PIT-V2 VIX / G-PIT-V3 Brent−WTI only; the sole
SOFR mention (line 35) is a note that SOFR's API *namespace* had to be
corrected away from; no SOFR series is staged anywhere in the PIT estate.
Despite this: (a) the ladder maps the keyword 'sofr' →
`MACRO_PIT_EVIDENCED_PARTIAL` (builder line 51), admitting GBPUSD-S006,
GBPUSD-S031, GBPUSD-S040 on that basis; (b) the eligibility summary's I-R2
says "only the US leg is evidenced" — implying SOFR is the evidenced US leg;
(c) **Lane R's grouping proposal asserts it twice as law**: §1.1 evidence
table line 53 "EFFR/SOFR daily (d+1 15:00 ET) … **EVIDENCED** — pr12a100k
PIT_DOSSIER G-PIT-V1/V2/V3 (PASS_EVIDENCED)" and §3.6 FORBIDDEN list item 5
"only **EFFR/SOFR**/VIX/Brent−WTI are evidenced"; the triage reasons repeat
it ("SOFR leg evidenced", "SOFR/EFFR evidenced only"). A future engine
consuming the feature inventory's lawful-input list could use SOFR in
L2/L3/L5 features believing it sha-pinned. (Lane R's §6 honesty section
repeats the error: "the repo evidences exactly four macro series
(EFFR/SOFR, VIX, Brent, WTI…)".)

**What would resolve it:** correct Lane R's table + forbidden list and the
builder's 'sofr' mapping (or stage a SOFR dossier under G-PIT-V1's pattern
— the NY Fed publishes SOFR on the same API); re-issue the three GBPUSD
rows' pit_class as unevidenced (they are T3-parked regardless, so counts
don't move).

---

## MEDIUM

### F-6 — P5's DSR inputs are under-pinned and the construction double-corrects; even after fixing F-1 the bar is likely calibrated beyond any real portfolio

**Severity:** MEDIUM (design soundness of the bar the owner was told "prices
the whole ledger").

**Evidence:** `policy/PASS_BARS_V2.md` §5 lines 221–231. (i) The
frequency/estimation window of the trial Sharpes {SR_n} entering V is
unpinned — "common evaluation window per the CSCV matrix" is asserted, not
enforced; walk-forward Stage-A trials evaluated on differing spans make V
ill-defined (mixing incomparable SR estimates). (ii) SR̂ is measured on
pooled TEST folds (line 230) while SR₀ = √V·E[max_N] is the expected maximum
of N TRAIN-side trials — under the null, an OOS SR is not selection-inflated,
so subtracting the full in-sample expected max overcorrects (the deflation
and the out-of-sample evaluation are two independent corrections stacked).
(iii) Calibration: with E[max_1500] = 3.369 (Euler–Mascheroni form, verified
numerically) and any plausible V — even estimation-noise-only, sd ≈ 1/√130
weeks = 0.088 → V ≈ 0.0077 — SR₀ ≈ 0.30 weekly ≈ **annualized SR 2.1**; an
annualized-SR-1.0 policy (weekly SR 0.139, n = 208) gives DSR ≈ 0.01. After
repairing F-1 to the canonical DSR > 0.95, the bar demands the policy's OOS
annualized Sharpe exceed ~2–3 — beyond essentially any real FX portfolio.
A bar no survivor can pass is not protection; it silently converts every
outcome into `POLICY_DEFLATION_FAIL`. The pass condition should be
calibrated (e.g., DSR applied to the Stage-B selection objective, with the
OOS SR̂ tested by PSR vs 0 and PBO carrying the selection-overfitting duty),
or the double-correction explicitly defended with a worked example.

**What would resolve it:** pin the trial-SR window/frequency; state the
IS/OOS mixture and either justify or restructure it; publish a worked
calibration showing what edge magnitude P5a can actually admit.

### F-7 — E-Law 2's fold-edge force-flat charges arms differentially by their fold-edge holdings (undisclosed systematic bias favoring the policy on every PnL leg vs always-on baselines)

**Severity:** MEDIUM.

**Evidence:** `policy/PASS_BARS_V2.md` E-Law 2 (lines 46–51): "all positions
are force-flatted at that decision (exit fills at next-bar-open, full kernel
charged, booked inside the closing fold)". The mechanism is common to all
arms, but an always-on baseline (B1/B2/B3) holds at fold edges and pays
forced round-trip crossings (plus ~1 week of forced flatness per 26-week
fold) that a gating policy may avoid — a protocol artifact inflating the
P1/P2a/P6a/P6d/P8 PnL increments in the policy's favor. Direction is
systematic; magnitude is second-order (order $4–8 per forced crossing per
leg at 10k units, ×8 edges ×N legs); the mechanism is disclosed but the
asymmetry is not. DD is essentially unaffected (marks are mid-continuous).
**What would resolve it:** disclose the asymmetry and quantify per-arm
fold-edge cost in the Stage-C report, or exempt fold-edge force-flat fills
from the cross-arm PnL comparison (symmetric shadow charge).

### F-8 — Campaign design's budget and false-edge arithmetic is stale vs the amended width (three internal inconsistencies)

**Severity:** MEDIUM.

**Evidence:** `campaign/BACKTEST_CAMPAIGN_DESIGN.md` §5 lines 92–94 still
states "at α=0.05, a **300-row** discovery ledger manufactures ~15 false
'edges'" and §6 line 118 "trial-ledger rows ≤ 300" — vs plan v2 §4's
**1,500** discovery rows (→ ~75 expected false edges at α=0.05). Campaign §6
T2 row (line 106) "≤24 scored arm-executions … **3 corpus rows** + ≤9 fresh
class candidates" — vs ladder v2 where only **1** of the 3 volume-profile
rows is a candidate (EURUSD-S010; USDJPY-S030/S056 are BLOCKED_DATA_FEATURE)
and vs Lane R's 147-runnable triage. Plan v2 §4's own estimate "292
candidates × (1 diagnostic + 2–3 controls) … ≈ 900–1,200 engine runs" is
also stale vs Lane R's ~500 worst case (145 rows parked at zero runs). The
amendment §5 marked the campaign's DSR/PBO/larger-ledger update "(next)" —
it never landed; the dispatch's "campaign design (amended)" is only true of
§1–§2. **What would resolve it:** one pass over campaign §5/§6 with the
triage's 147/145 split, the 1,500-row ledger and the F-3-reconciled arm cap;
refresh the false-edge arithmetic to the actual ledger width.

### F-9 — CTRL-B's day-blocked volume shuffle preserves cross-day volume↔price-range association: the placebo is weaker than its "destroys the level-acceptance structure" claim

**Severity:** MEDIUM.

**Evidence:** `poolB/class_spec/CLASS_SPEC_VOLPROF_M1.md` §7b (lines
519–528): "within each trading day … permute the minute→volume assignment
… This destroys the level-acceptance structure". A within-day shuffle
destroys the within-day level→volume mapping but **preserves the cross-day
association** (which days carried volume at which price ranges): a 20-day
profile whose structure comes from high-volume trending days at the top of
the range survives the placebo largely intact, so "arm > placebo p90" is
easier than claimed; conversely a purely cross-day structure fails the
movement diagnostic (median |POC_placebo − POC_real| < 1×W_BIN) and dies as
`OBSERVABLE_NOT_IDENTIFIABLE` — a possible wrongful kill. CTRL-D (uniform
per-minute) does not isolate the gap (it removes weighting at all scales).
**What would resolve it:** add a cross-day shuffle or day-permutation member
to the placebo ensemble (N_SHUFFLE=20 allows it), or disclose the boundary
in §7b.

### F-10 — USDJPY-S020 (runnable T2) carries a PIT-lookahead trap: the MOF-intervention exclusion

**Severity:** MEDIUM.

**Evidence:** triage reason (mechanization_triage_292.tsv): "ATR14 p95(2y) +
reversal close after 3-bar run named; **declare MOF-intervention exclusion
(public archive not staged)** + limit-at-50% mechanics"; census
`required_pit_data` "D1 OHLC repo; MOF intervention dates to exclude". MOF
interventions are disclosed ex post (often months later); excluding
intervention days in a backtest without a disclosure-lag rule uses future
information at decision time. The Wave-2 defaults pass must freeze a
PIT-legal rule (exclude only interventions publicly disclosed ≥ N days
before the decision) or the row parks. **What would resolve it:** name this
in the T2 defaults-registration checklist as a PIT-rule (not a parameter)
preregistration, with the lag constant frozen.

### F-11 — PBO/CSCV machinery: no dedup/cluster handling despite 192/292 census-variant candidates; two edge rules missing

**Severity:** MEDIUM.

**Evidence:** PASS_BARS_V2 §5 lines 243–271. (i) 192 of the 292 candidates
carry census verdict VARIANT_OR_DUPLICATE and enter the N×T trial matrix as
separate trials — the CSCV ranking is dominated by near-duplicate rows
(rank-redundancy), which the spec does not treat (no dedup by mech_key, no
cluster-level CSCV, no disclosed sensitivity). (ii) The exclusion rule
covers trials "with no returns in a CSCV block" for ranking, but ω_c is
undefined when the TRAIN-BEST trial n*(c) has no returns in that
combination's TEST blocks — the combination's handling is unspecified.
(iii) "out-of-sample rank fraction" normalization (rank/N vs rank/(N+1)) is
unpinned (it matters at the λ=±∞ extremes the spec does define).
**What would resolve it:** declare a deduped-mech_key sensitivity run
alongside the primary PBO; add the two edge rules.

### F-12 — Two parallel switch-cost books: ONOFF_LEDGER's switch_cost_usd (cell p50) vs the journal's realized crossings (bar-quoted, spread-once)

**Severity:** MEDIUM-LOW.

**Evidence:** GROUPING_PROPOSAL §4.2: `switch_cost_usd` is "charged at the
**measured spread cell of the actual fill hour** (C1 per-hour p50 cell …)"
while the book charges the fill bar's quoted spread through the fill price
(FILL_ACCOUNTING_SPEC §2). The ledger metric and the realized journal costs
can diverge (bar quotes vs cell p50), creating two "switching bills" whose
difference is nowhere reconciled or bounded. **What would resolve it:** pin
`switch_cost_usd` to the journal's realized crossing lines (spread_once +
slip on the actual fills), or declare the cell-based figure an estimate with
a stated divergence tolerance.

---

## LOW

### F-13 — fx2's expected.timeline step numbering skips 8 (steps 1–7, 9–11)

Editing artifact in `journal/fixtures/fx2_overnight_hold_with_wed.json`
(timeline `step` fields); harmless for the README's order-based runner, but a
step-number-asserting implementation trips; fx1/fx3/fx4/fx5 are continuous.
Resolve: renumber or drop the field.

### F-14 — Swap-line weekday casing inconsistent across fixtures

fx2 `weekday_utc` "Sunday"/"Monday"… vs fx5 "sunday"/"monday"… — pin the enum
before an engine string-compares it.

### F-15 — The swap-calendar identity claim is stronger than the calendar

FILL_ACCOUNTING_SPEC §2: "exactly 7 pip-nights per 7 calendar nights for a
continuously held position" holds only for accrual-event-aligned windows
(Fri 20:00→Fri 20:00 as in fx2/fx5); e.g. Wed 21:00→Thu 23:00 accrues 4
pip-nights in ~1 calendar night, Thu 23:00→Fri 21:00 accrues 0. Standard
triple-Wednesday convention — but the identity sentence should say
"per accrual-aligned week"; fixtures only exercise the aligned case.

### F-16 — No fixture pins the §1.5 worst-fill grading path

Gap-through/stop-through fills beyond `quoted side + slip` (the
slippage-beyond-halfspread EXCESS line and LOSS_FILL candidacy) are
unexercised by all five fixtures — add a gap-fill fixture before the engine
gate is relied on for stop-heavy legs (VC1/VC2 ATR stops).

### F-17 — B3 definitional wobbles

PASS_BARS_V2 §1 line 92: B3 = "best **deflated, ×2.0-cost-stressed** TRAIN
objective" but P2b evaluates at governing ×1.0 — B3 is not the strongest
×1.0 single leg, softening P2b vs its claim text ("the single best TRAIN
leg"); and "run ALONE through the same L2–L6 machinery" (eligibility
active?) sits awkwardly against P8's N=1 note equating B3 with the leg
"always-on". State the intent.

### F-18 — Ladder v1 is not reconstructible from the package as delivered

The eligibility summary says v1 is "preserved in git history" while the
charter calls the whole control dir uncommitted; the v2 builder regenerated
the same path in place. An owner auditing the untracked control dir cannot
perform the "did any row change more than its label" v1→v2 diff. (I
substituted a full v2↔census provenance audit — see F-25 — which passes;
the v1 diff remains unperformable without git.) Resolve: keep a v1 copy or
the regeneration diff inside the control dir.

### F-19 — Campaign T2's "3 corpus rows" for P_B is stale

Ladder v2 has exactly 1 of the 3 volume-profile rows as a candidate
(EURUSD-S010); USDJPY-S030/S056 are BLOCKED_DATA_FEATURE (consistent with
class spec §1.2's non-preregistration of them). Refresh campaign §6.

---

## INFO

### F-20 — Grouping prose arithmetic nit: "F-EVENT 2/30 runnable" vs its own table n=32

GROUPING_PROPOSAL §1.3 item 2 says 2/30 (and accounts for 30 rows: "28 …
surprise … 2 more on CB text"); the §1.2 family table says F-EVENT n=32
(0/2/30). Cosmetic; the table is right.

### F-21 — VERIFIED CLEAN: fixtures, spread-once law, erratum chain (the wrongful-kill check)

All five fixtures were re-derived by a from-scratch engine implementing the
spec text only (fills from bar quotes + U3 slip, spread-once decomposition,
commission, the 22:00-UTC swap calendar walk with Wed ×3 and Fri ×0, the 28d
cost-guard with trailing-spend windows, netting deltas, gross-vs-mid in
closed and open forms, the §6 invariant). **Every expected number in fx1–fx5
reproduces within 1e-9 (observed ≤ 1e-12); zero mismatches.** The fx3
virtual attribution sums exactly to book totals; fx5's defer/execute guard
decisions (trailing 9.180191 ≥ 9.00 → DEFER at 07-05; 0.780191 < 9.00 →
ALLOW at 07-12) reproduce from the spec's guard rule. The FILL_ACCOUNTING
§3 worked example also checks ($5.50 = $4.50 + $1.00, commission
$0.3799425). Lane D's audit numbers verify against the machine output
(audit_summary.json): C1 0.3/0.5 n=286/286; corrected C2 Mon–Thu 1.2/3.7
n=65,109 (EURUSD); integral-volume fractions 0.02488/0.03501/0.03711 =
2.49/3.50/3.71% as quoted in the erratum and class spec. The dual-source
C2 mechanism (per-cell GOVERNING source, corrected cells cited verbatim,
single remaining "2.7" flagged as the undercharge note) is sound, and the
P handoff's revision incident (C2 erratum, fx4 boolean patch) is honestly
recorded with shas. No double-count path exists in the fixtures: the only
crossing lines are spread_once + slip, summing to |fill − mid|×|Δ|, and
gross is mid-to-mid.

### F-22 — ARTIFACT_PINS.json does not exist yet

Plan §10 says all pins "live in the A1-maintained external manifest
../manifest/ARTIFACT_PINS.json"; the manifest dir contains only the builder
(`build_pins.py`). Generate before the owner packet.

### F-23 — Stale "tick-volume" terminology survives in the triage

EURUSD-S010's T2 reason says "M1 tick-volume evidenced" — after erratum I-3
refuted tick-count semantics (the column is size-weighted, unit-opaque).
The row's substance is fine (the EURUSD M1 volume column exists; the
release-calendar is dates-only), but the reason text should use the
corrected name.

### F-24 — Dead-ancestor tension (surface 7): honestly disclosed everywhere it matters — A7-defensible

Plan §0 ("the changed axis is authorization + accounting discipline, **not
new information**"); architecture §0 table (the RGC-V1 row names itself
"the one A7 will scrutinize hardest"); amendment §4 (full tension section);
class spec §8 (informative-not-gating, verbatim fence texts, no rebranding);
grouping §6 ("expected per-leg outcome is negative"). No artifact quietly
rebrands the gating-dead-legs pattern as novel. One nit: the session-1
SESSION_REPORT still carries the pre-amendment separation claim ("no gating
of inadmissible legs") with no in-file amendment pointer — annotate or
supersede it in the owner packet.

### F-25 — Outcome-exposure containment (surface 2): VERIFIED — labels are exact functions of the authorized inputs; no current-panel fold outcome exists anywhere

Machine verification over all 1,200 rows: gid join to CENSUS_1200.tsv exact
(1,200 unique); every copied field (symbol, s_id, family, title_short,
mech_key, horizon, census_verdict) matches the census verbatim (0
mismatches); the 15 F0 verdicts match SLEEVE-FX5 F0_VERDICTS.md's table
exactly (10 REJECT_VARIANT_SAME_FAMILY / 3 REJECT_DATA_OR_COST / 2
REJECT_NOT_STANDALONE; 11 of the 15 are among the 292 — the other 4 are
blocked: USDJPY-S012 PIT over-block per F-4, AUDUSD-S087/S088/S046 data
ceiling); the label rule (F0 → F0_INDIVIDUAL_REJECT; VARIANT_OR_DUPLICATE
or ancestry_hits → FAMILY_HISTORY_NEGATIVE; else PRIOR_NOT_SCORED) produces
0 deviations on all 1,200 rows (292 = 222 FHN + 59 PRIOR + 11 F0, matching
every published count). Lane R's triage TSV reconciles 292/292 with the
eligibility table on symbol/family/horizon/label. No test-fold outcome
exists to leak (T0; no engine, no scored cell, no PnL anywhere); the
slates' reasoning is mechanism-prior only and every slate reports its label
mix; 16-row corpus spot-checks (12 parked + 4 admitted) all faithful to the
corpus text at the cited source_refs — no parked row is actually runnable
and no admitted row is vague on the samples drawn.

---

## Verdict

The accounting core, the audit chain, the triage and the disclosure culture
survive hostile review. The binding-bar layer does not: a vacuous P5a (F-1),
a degenerate B2 (F-2), an impossible budget (F-3), a mislabeled PIT axis
repeated as fact in the plan (F-4) and a false "SOFR evidenced" claim in the
feature-inventory law (F-5) are all registration-blocking text defects. All
five are cheap, localized fixes — none requires new measurement — but the
package must not reach the owner as "bars frozen" while its central
multiple-testing bar cannot fire.

**VERDICT: REVISE_BEFORE_OWNER** — 1 CRITICAL, 4 HIGH, 7 MEDIUM, 7 LOW, 6
INFO (25 findings; 2 of the INFO are affirmative verifications of the
accounting/label core).
