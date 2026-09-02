# V10-N2 — A7-N independent rescue-risk challenge (six candidates)

- **Agent:** A7-N (independent challenge role, wave N2)
- **Worktree:** `/Users/hoangminhlong/my-quantitative-v10-wt/n2-a7-rescue`
- **Branch:** `orca/v10-n2-a7n` · **Base HEAD verified clean:** `a1528dcb608ccdf2817b6389e524417c11f4d392`
- **Written (UTC child clock):** 2026-08-27T06:4xZ (deadline 07:15Z)
- **Machine-readable companion:** `research/audits/v10/a7n_rescue_challenge_v10.json`
- **Scope:** evidence only. No scored backtest, no metric inspection, no writes
  outside the two deliverable paths, no network.

**Method.** One test drives every rescue verdict: could the construction be
reached from a terminal-rejected or already-adjudicated ancestor by changing
only a lookback, threshold, cadence, symbol set, cap, direction rule or
post-result filter (PLAN §3)? Materiality is then judged against the closest
ancestor **by input observable and payoff geometry**, not by the ancestor the
proposer volunteered.

---

## 1. Verdicts

| Mechanism | Rescue verdict | Dims material | Negative control | Concur / object |
|---|---|---|---|---|
| A8-M01 AGGRESSOR-ABSORPTION-PANEL | GENUINELY_NEW | 4/4 (dim 3 weak) | INADEQUATE as specified | CONCUR_CONDITIONAL |
| A8-M02 TICKET-SIZE-SIGNATURE | GENUINELY_NEW | **3/4** | INADEQUATE | OBJECT |
| A8-M03 LEAVE-ONE-OUT-RESIDUAL-DIFFUSION | **RESCUE_FORBIDDEN** | ≤2/4 | Adequate mechanism, wrong placement | **OBJECT** |
| A9-FORCEDFLOW | GENUINELY_NEW | 4/4 conditional | CONDITIONAL | CONCUR_CONDITIONAL |
| A9-INFSPILL | BORDERLINE | 3–3.5/4, hinge on clamp | ADEQUATE (cleanest in pool) | CONCUR_CONDITIONAL |
| A9-RVRELVAL | BORDERLINE | **2/4 clearly** | INADEQUATE (fails by construction) | OBJECT |

Where I disagree with the proposers' self-flagged "contested" hedges:

* A9 flagged FORCEDFLOW dim 3 as contested. I credit it — weakly. Entering into
  the collapse bar without any reclaim confirmation flips which side of the
  dislocation is monetized versus `reclaim_mr`, which waits for one confirming
  print; and the entry predicate contains no price-level knowledge at all.
* A9 flagged RVRELVAL dim 3 as contested. My flags are on different rows: dim 3
  (atomic two-leg spread book) is the **solid** dimension, verifiably absent
  from every ancestor; it is dims 1 and 4 that fail.
* A8 asserted M01's geometry with disclosure and dim 4 flatly. Both are right,
  but A8's dim-4 claim for M02 is not — see §3.

---

## 2. Strongest objection in the pool: A8-M03

**M03 is a re-parameterization of a mechanism this programme already measured
and archived as a rescue.**

1. `research/v9_residual_mr.py` implements, inside a registered V9 signal
   family wired into `portfolio_runner.V9_SIGNAL_FAMILIES`: OLS residualization
   of alt returns against BTC (`beta_i` over a trailing 30-day window),
   `e_i = r_i − beta_i * r_btc`, z-standardized, **faded**, on the Monday-00:00
   UTC weekly clock. Same object class, same sign class, same clock as M03.
2. `research/audits/v9p/p07_no_rescue_check.json` graded that proposal against
   weekly price reversal at `overlap_risk: HIGH` and prescribed a frozen
   pre-launch orthogonality gate whose stated consequence was *"gate failure =>
   classify as rescue attempt of weekly_reversal_V8 and archive without
   consuming budget."*
3. `research/audits/v9p/f2_orthogonality_gate.json` executed it:
   `mean_abs_spearman: 0.676` (max `0.9515`) over 33 Monday stamps against a
   0.50 threshold — `verdict: FAIL_RESCUE_ARCHIVE`.
4. `v9_budget_freeze.json` and `master_report_v9.json` record the disposition:
   `f2_residual_mr = ARCHIVED_NOT_RUN_RESCUE_OF_REJECTED_FAMILY`.
5. The three deltas M03 offers — leave-one-out peer composite instead of BTC,
   frozen pre-window estimator instead of rolling, continuous capped book
   instead of ±0.20 tail slots — map one-to-one onto the PLAN §3 enumeration of
   things that do not constitute a new mechanism, and none touches the
   information source, sign, clock or causal claim that the 0.676 measurement
   convicted.
6. The proposal asserts the ancestor does not exist (a8 memo L910: *"no V1–V9
   family constructs any beta-, hedge-, index- or orthogonality-adjusted object
   (confirmed against the full family inventory)"*), and repeats the claim in
   its recommendation section when ranking M03 first on raw novelty. That is
   factually wrong; the inventory consulted covered `research/hypotheses/**`
   headers only, and the residual family lives in code plus the v9p artifacts —
   precisely the blind spot this wave exists to cover.

Any novelty score issued from those materials inherits a false premise. Cheap
remedy, precedented by V9 itself: rerun the orthogonality measurement with the
leave-one-out neutralizer on pre-freeze PIT data (it consumed zero budget in V9)
and admit the family only if mean|rho| ≤ 0.50 over ≥ 33 stamps.

Runner-up objection: INFSPILL reassembles the realized book shape that the same
p07 artifact blames for V4 momentum's terminal failure (up to ten same-signed
legs, no net exposure clamp) while omitting the clamp that ruling requires — and
faces a zero-credit S0 screen (#24) on the identical mechanism at null.

---

## 3. Per-mechanism notes (compressed)

### M01 aggressor absorption — GENUINELY_NEW, concur conditional
No V1–V9 family ever consumed `taker_buy_quote_volume`; verified by grep across
the repository (only `data/catalog.py:34-35` passthrough and test fixtures).
Nearest rejected families: H-XSECT-FUNDING-CARRY-v1 (terminal CANDIDATE_FAIL;
closest on both axes — daily normalized signed quantity → capped dollar-neutral
book) and H-XSECT-MOM-v1 (V4 lineage; M01 reproduces its book skeleton nearly
clause for clause). Control defect: substituting the cross-sectional day mean
destroys symbol-specific variation but never asks whether flow adds anything
over plain contrarian weighting of *price* — the exact confusion that killed V9's
residual proposal at 0.676. The specified control also degenerates into an
all-long/all-short net-exposed book once λ is bisected to gross 1.0, conflating
market tilt with information loss. Required before freeze: strict-later-event
fill clock fleet-wide (A8 fills at the open of the bar opening exactly at the
decision instant; A9's uniform policy requires strictly later), weight-vector
rank correlation against XSECT-WREV/XSECT-MOM, and ATT-TAKER-QV satisfied.

### M02 ticket-size signature — GENUINELY_NEW on observable, OBJECT on materiality
`count` is genuinely novel as a signal input. But dimension 4 fails: A8 claims
"predicts from the identified class of the marginal trader," while its own cited
nearest rejected family H-FUNDCROWD-MR-v2 states `expected_counterparty`:
*"Over-leveraged crowded-side perp holders … who must unwind into adverse moves."*
That is the same actor reaching the same behavioural conclusion through funding
percentile. One delta cannot be credited twice across two dimensions. Also: a
fail-closed prerequisite (ATT-COUNT) cannot coexist with a published feasibility
grade, and the control (record-HIGH arm) shares the untested premise that
direction-matched extreme-participation days revert at all.

### M04/FORCEDFLOW — GENUINELY_NEW, concur conditional, one HIGH finding
Hidden joint scalar pair: `exc_t = (close−open)/(sqrt(L_exc)*sig)` with
`L_exc=4`. `sqrt(L_exc)` appears nowhere else; it is purely a divisor, so the
entry condition is algebraically |close−open| ≥ 4.0·σ₁. `(L_exc, threshold)` is
one free sensitivity number written as two structural constants — the exact thing
A9's own §3 pledges make proposals void. Collapse to `L_exc=1, threshold=4.0`
before freeze. Dim 4 must be downgraded from counterparty-*identity* prediction
to footprint prediction: there is no OI, liquidation or margin feed locally, so
the claimed actor is never observed. Hold_max=16 bars is class C in name only.

### INFSPILL — BORDERLINE, concur conditional on a clamp
Cleanest negative control in the pool (stale-shock placebo retains co-movement
while destroying freshness). Two problems. First, the realized book under a
2σ benchmark shock is up to ten same-signed legs — no net clamp, no beta bound —
which reproduces the V4 death mode p07 explicitly requires continuation families
to pre-register safeguards against ("gross drift >1.0 intraperiod, MDD 24–37%").
Second, its justification for `hold = 32 bars` — "aligns to the settlement cadence
boundary" — is false: the frozen manifest reports 1,095 settlements/year for nine
symbols and 2,189 for ENAUSDT; there is no single boundary to align to. Positive
finding worth recording: `research/v9_residual_mr.py` establishes repo precedent
for consuming BTC bars as a conditioning input while excluding BTC from ranks,
weights and PnL, which resolves the authorization ambiguity A9 hedged about.

### RVRELVAL — BORDERLINE rescue, OBJECT on materiality
Two-leg atomic spread book is the one genuine structural addition in the pool.
But dims 1 and 4 fail independently: the source story is the rejected single-name
mean-reversion account relocated onto a ratio, and the named counterparty
(unlock/allocation flow in one leg) is undetectable by a design holding no flow
or OI observables. Its control (`rr* = ln(A_t/A_{t−96})`) is structurally
non-reverting — entries cluster at extreme z, convergence rarely fires, timeouts
dominate — so it cannot lose gracefully, and observing "control worse than
anchor" was guaranteed by construction. Leg B swapped for a mechanically-chosen
deep cohort member would discriminate cleanly at identical cost. Positives: pair
pinning by pre-window manifest rank with substitution forbidden is exemplary
anti-rescue hygiene.

---

## 4. Aggregate: what collapses tonight without pretending otherwise

Not the falsification procedures — **shared infrastructure**. Two gaps affect all
six.

**(a) Panel bars absent from every V10 tree.** The universe manifest pins bars at
`catalog_live_crypto/data/binance_bar/<SYMBOL>-PERP.BINANCE-15-MINUTE-LAST-EXTERNAL`.
That path exists only in `/Users/hoangminhlong/my-quantitative` (20 symbol dirs,
including all ten selected). This worktree, `integration-v10`, `n-a8-proposals`
and `n-a9-proposals` each carry at most `catalog/data/binance_bar/{BTCUSDT,
ETHUSDT}-PERP.BINANCE-…`. Four mechanisms are panel-wide, RVRELVAL needs SOL as
well as ETH, INFSPILL needs BTC plus all ten alts — so **no candidate is runnable
in any current V10 worktree**, including the cheapest (RVRELVAL, estimated ≤1
wall-clock hour) for want of SOLUSDT bars. Staging must be an explicit A1/A6 act
with sha256 verification against manifest pins, visible to detached R1/R2, or
G05 freeze and repro-`all_match` are unsatisfiable by construction.

**(b) No funding companion anywhere, so native accrual gating is unrunnable.**
All six specify native funding accrual between entry and exit, and PLAN §11/§12
bind the cost gate to "5 bp + tick + **native funding**". Confirmed locally: no
`derivatives_data/`, no `funding_data/scan_2026`; `catalog/data/crypto_perpetual`
holds instrument definitions only. As written, no family can complete a cost-
gated run. Honest resolutions: stage the bundles, or freeze a stricter explicit
substitute. Silent substitution violates the cost baseline. Note the irony:
FUNDCROWD-MR-v2's era had funding data none of the current trees carry either.

Also recorded: field-population attestations for M01/M02 are unmeetable tonight
(only BTC+ETH ever decoded); the multiple-testing item resolves to
`UNAVAILABLE_FAIL_CLOSED` for every family (both proposers concede), so selection
buys at most two attempted disproofs, not two promotable edges; and A8 used the
manifest's measured window start 14:30Z while A9 used the contract window 00:00Z
with a per-symbol denominator wrong for ETH by 57 slots — fold boundaries differ
at the head by 58 slots if both firms are selected, so one window definition must
be frozen fleet-wide.

Two cells are designed to inform nothing regardless of staging: M03-N (a
four-point weekly regression) and RVRELVAL-CTRL (see above).

---

## 5. Selection guidance for A1/A5

1. Cleanest no-rescue candidates, in order: **INFSPILL** (once clamped),
   **FORCEDFLOW** (once the scalar pair collapses), **M01** (once the fill clock
   is unified and the orthogonality report exists).
2. Must not proceed as submitted: **M03** (rescue-forbidden), **M02** and
   **RVRELVAL** (four-dimension requirement fails on the frozen threshold).
3. Cheapest way to settle the M03 question costs zero budget: rerun the 33-stamp
   orthogonality measurement with the peer-composite neutralizer.
4. Whatever is selected, both staging blockers above need named owners before
   I-stage, else every scored cell lands on a run that cannot reproduce.
