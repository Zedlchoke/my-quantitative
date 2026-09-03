# Z4 A7 — Independent Proposal Audit (Stocks-Free V2)

- Auditor role: Z4/A7 — independent proposal auditor and selection-freeze gatekeeper
- Worktree: `/Users/hoangminhlong/my-quantitative/.worktrees/stocks-free-v2/z4-a7`
- Branch: `orca/stocks-free-v2-z4-a7`
- HEAD verified: `a53f43af2fb029545318491aa1e364f40d5b8dd7` (matches bootstrap `a53f43af2fb0`), status clean at audit start
- Inputs audited (read-only): A4 family spec (json+md), A5 manifest + family spec md + 3 arm JSONs, frozen run context (census, partition, split factors, DA1, DA2, snapshot, run contract, state), `PLAN_stocks_free.md` §3/§10/§11/§14
- The auditor did not repair any spec and computed no strategy returns.

## VERDICT

**SELECTION_FREEZE_AUTHORIZED**

Zero unresolved HIGH/CRITICAL objections across both families. Two MEDIUM pre-freeze completeness items and three LOW/INFO observations are recorded below; none alters any frozen mechanism. Per-arm freeze recommendation: all six arm ids in §Freeze recommendation.

## Identity and digest verification (dimension 9)

Recomputed sha256 (shasum -a 256) of every audited artifact and frozen input; all match recorded values byte-exactly:

| Artifact | Recorded | Recomputed | Match |
|---|---|---|---|
| `a4_z3_relative_momentum_spec.json` | `98d5307c…41416fa` (A4 md header; `state.json` z3.A4) | `98d5307c3c3810a236f230475b190b34bd38461461cc7ea0a5ebdf38741416fa` | YES |
| `a5_family_manifest.json` | `d69fb046…c3b4a3c8` (A5 md §12) | `d69fb046b9b148f36747ce8968b332b071420f7836fc74a830b242dec3b4a3c8` | YES |
| `a5_arm1_tsm12_ivol.json` | `6c301db5…03cfc57` (manifest + md) | `6c301db551c8e5faa68bb923411137c28581d5aa9816984d076e3cbf603cfc57` | YES |
| `a5_arm2_sma200_weekly.json` | `8c65c0d7…e69c4c1` (manifest + md) | `8c65c0d7ea7582b70df0c216c42b202f5ca23788a06945ec2e9676837e69c4c1` | YES |
| `a5_arm3_tsm12_inverted_control.json` | `5f3d93ba…313db39527` (manifest + md) | `5f3d93ba85241d22bde44978efa0bc98d3c5fbdb9cbee6f2d8881d313db39527` | YES |
| `cohort_census.json` (input) | `4f9cab6a…dc65a3a0f` (A5 frozen_inputs) | `4f9cab6af48126955a92e4d5d9ef12954a59a59a8250175a4c2d31cdc65a3a0f` | YES |
| `partition.json` (input) | `9b4ad799…23ef17c7` (manifest + A5 arms) | `9b4ad7993f943edb1f4a995184eb85083879168f9f86eb1720b2a66623ef17c7` | YES |
| `run_contract.json` (input) | `65410307…435735d8` (A5 frozen_inputs) | `65410307ca4e8b25fa31d74f1ebad0562097f32d251f5316bd007c0f435735d8` | YES |
| `split_factors.json` (input) | `f6665651…c135fc9b` (manifest + A5 arms) | `f666565124155bd26ecec8de9b88864b58f85831f404ccac48bcbb8cc135fc9b` | YES |
| `da2_evidence.json` (input) | `014e7368…bea172a1da` (A5 frozen_inputs) | `014e73682fa45d60332dcdac6f07b2807d51556cfff192baa6cd35bea172a1da` | YES |
| `PLAN_stocks_free.md` (input) | `d3458d85…f7318` (A5 frozen_inputs) | `d3458d858f0c39371361819541189e8e6b2ef4e310bde94edf40bf92919f7318` | YES |

Cohort digest `c9d4e88a…bc96` matches census `cohort_digest` in A4 contract_refs, A5 manifest, A5 arms, and `state.json`. Both families declare production from the same base commit `b345de4…` (A4 `bootstrap_sha256_short`, A5 `base_commit`). Single frozen configuration per arm confirmed: no grids, no threshold ranges, no alternative-lookback sets anywhere (grep: only `not_a_grid` / `not_a_lookback_grid` declarations). Digest authority chains are internally consistent (manifest is digest authority for A5 arms; A4 md header for the A4 JSON; independently corroborated by `state.json` z3 block).

## Dimension findings

### 1. Novelty and family overlap — PASS
A4 (`A4_XSEC_ETF_RELATIVE_MOMENTUM`) is cross-sectional relative ranking: rank the 10 sector ETFs by 12-1 TR momentum, hold the selected top (or bottom) subset, always gross-invested in the ranked book; the selection object is each ETF relative to the cross-section. A5 (`A5-SFV2-TREND-DEFENSIVE`) is time-series: each ETF's own trailing 12m return sign (or price-vs-SMA200 level state) decides per-asset eligibility, with a deterministic vol-target scalar mapping gross into equity-vs-cash; there is no cross-sectional ranking anywhere in A5. Mechanisms, decision variables, weighting levers, and failure modes (relative-persistence vs absolute-trend + vol-regime de-risking) are genuinely distinct. Input overlap (same cohort, 252-session lookbacks, TR chains) is a property of the frozen data contract, not mechanism identity. The six arm identities are unique strings with unique anchoring digests; no collisions across families.

### 2. Causal control adequacy — PASS
- A4 `ARM_A4_NEGCTRL_BOTTOM3_EQW_MOM121`: identical clock, cohort, 12-1 TR score, top-3 count, equal weight, caps, execution, delay, costs; only the ranking sign reverses (buffers explicitly disallowed to preserve the one-mutation property). It destroys the claimed cross-sectional persistence mechanism while holding the long-only sector-beta exposure constant, and the spec explicitly routes the operative comparison through the paired anchor-vs-control contrast. Falsification rule is concrete and stateable: control passes both primary gates (after-cost expectancy > 0 AND PF >= 1.10), OR matches/beats anchor after-cost expectancy in >= 2/3 folds → family FALSIFIED regardless of anchor.
- A5 `A5-SFV2-ARM3-TSM12-INVERTED-CONTROL`: pure sign mutation (eligible iff 12m TR < 0) of the anchor with every other lever bit-identical (cohort, lookback, threshold, vol estimator, 10% vol target, caps, clocks, costs, delay, ramp, folds, purge, force-flat, minimums). Holding the vol lever constant is justified (it tests the family's primary mechanism, trend sign). Falsification rule is concrete and names the frozen statistic: control's fold-level risk-adjusted evidence (excess vs flat 0%, realized-vol-normalized, per S0 fold) >= anchor in >= 2/3 folds → FALSIFIED; control self-void (evidence/invariants) → UNTESTED, fail-closed. Empty inverted eligible sets count as valid 100%-cash events (declared).

### 3. Look-ahead / PIT — PASS
- A4 anchor formula `mom_i(t) = P^TR_i(t-21)/P^TR_i(t-252) - 1`: the most-recent-month skip is explicit (evaluation point at t-21; sessions t-20..t excluded), canonical 12-1. The neighbour's vol estimator uses only [t-252, t-21] (231 log returns) — the skipped month leaks into no feature. Decisions at the completed month-end bar; fills at the next regular session on RAW executable prices; TR feature series strictly separated from raw fill series.
- A5 anchor/control `TR_i(t)/TR_i(t-252)-1` and neighbour `TR_i(t) > SMA200(t)` use only completed sessions through t; fills next session on raw closes; one-event delay declared mandatory in every arm; 63-session realized vol is trailing-only.
- S1 sweep (grep for 2025-08/09/10/11/12, 2026-*): every hit is (a) a SEALED-existence or force-flat boundary declaration, (b) the 2025-12-05 split-factor provenance inside the frozen FD2 formula description (split lies in S1; S0 unaffected; factor semantics frozen for the entire coverage — a data-construction fact, not S1 outcome usage), or (c) file timestamps. No S1 date enters any decision, hold, feature, or evaluation schedule in either family.
- Warmup/ramp: A4 2018-04..2018-12 slots are declared UNSCORED with "no truncated-lookback fallback permitted"; first valid decision 2019-01-31 (2018 contains only ~251 sessions, so the 253-session window is unavailable at 2018-12-31 — arithmetic checks). A5 pre-ramp book is 100% cash with no trades; first allowed events ~2019-01 (L=252) and ~2018-10 (L=200), consistent with the frozen calendar. Neither family computes partial-window scores.

### 4. Data compatibility — PASS
All features are expressible from raw closes plus issuer-reconstructed TR under the amended FD2 formula (`split_factors.json`: raw closes x issuer-confirmed split factors + SSGA/SPDR distribution records; the five 2:1 splits eff 2025-12-05 carry issuer press-release provenance and TD `adjust=all` cross-check). A4 declares SPY BENCHMARK_ONLY (census role `BROAD_US_EQUITY_BENCHMARK`), never ranked, never held, with explicit rationale; A5 declares SPY investable + benchmark dual role with an identical-rule, no-special-casing justification (PLAN §3.3 names SPY TR the primary benchmark; nothing forbids investable SPY, and the 35% positive-PnL concentration constraint motivates the breadth choice). No fundamentals, analyst, borrow, or off-cohort inputs anywhere; long-only makes borrow N/A; TLT/GLD excluded pre-census with recorded reason; defensiveness is cash-only.

### 5. Clocks and turnover — PASS (with LOW objection O3)
A4 MONTHLY and A5 MONTHLY/WEEKLY are inside the PLAN §3.2 weekly-or-monthly cap, frozen per arm, with deterministic decision/fill rules on `US_EQUITY_REGULAR_V1`. A4's feasibility ceiling <= 6.0x gross one-way/yr at 7 bps base (= ~42 bps/yr drag ceiling) with 12 bps stress declared Z6-only is reasonable and non-binding as a prior. A4 prior 1.5-3.5x/yr is plausible-to-optimistic for a bufferless monthly top-3; see O3 (internal inconsistency of the churn parenthetical). A5 expectations (2.0-4.0x two-way monthly anchor/control; 3.0-6.0x weekly neighbour; sticky-state reasoning; ~0.6-0.9%/yr drag context at 10 bps/side) are sane for their clocks. Gap: A5 declares no numeric feasibility ceiling and no stress-cost level (see MEDIUM O1). Capacity reasoning on both sides uses the census XLRE median dollar volume (~$197M; A5 quotes 196,872,580, consistent with census) with declared research-scale claim limits.

### 6. Concentration and exposure — PASS
Both families: gross <= 1.0 always, long-only, no shorts, no leverage, per-ETF cap 35% (A4 equal-weight top-3 = 33.33% by construction; inverse-vol capped-then-renormalized; A5 `min(0.35, 1/|E|)` with cap-binding residual to cash, never redistributed), explicit cash residual as the fill-all asset (yield 0 per run contract). SPY role separation is explicit in A4 and dual-role-justified in A5. Post-scoring 35% positive-PnL and 50% fold-concentration validity conditions are wired to PLAN §14 as measured gates, not spec claims.

### 7. Outcome blindness — PASS
Outcome-blind declarations present in all seven artifacts (A4 `no_tuning` + `status: FROZEN_OUTCOME_BLIND_NO_SCORED_ARTIFACT`; A5 manifest + per-arm `outcome_blind_declaration` + family md §0), including mutual-lane isolation (A4 never read the A5 lane and vice versa; both cross-declared). Greps for Sharpe/PnL/PF/expectancy find only literature citations (marked MODEL_INTERNAL_UNVERIFIED) and preregistered gate/falsification thresholds — no computed returns, PnL, rankings, or scored artifacts. Warmup-extension (A4) and ramp-in (A5) contribute no scored trades and no partial-window scores.

### 8. Evidence count minima — PASS (with LOW objection O2, INFO O4/O5)
- A4: minimums 60 total / 15 per fold. Independent recount on the frozen partition: fold 1 = 20 (2019-01..2020-08 month-ends), fold 2 = 29 derivable (2020-09-30..2023-01-31; spec records 28 — O2), fold 3 = 29 (2023-02-28..2025-06-30; the 2025-06-30 decision is explicitly counted, filling 2025-07-01 and force-flat 2025-07-24). Total 78 derivable vs 77 recorded. Under either count the 60/15 minima clear with wide margin; readiness arithmetic (first valid 2019-01-31) verified. Independence via non-overlapping monthly holds holds.
- A5 monthly arms: minimums 18/fold, 70 total vs capacity ~20/29/29 (≈78). Fold-1 headroom ~2 events — thin but honestly declared ("minimums leave headroom for the fold-1 ramp-in"); counting convention (fills and liquidation inside the scored window) is deterministic.
- A5 weekly neighbour: minimums 95/fold, 340 total vs declared capacity ~130/129/129 minus ~28 ramp weeks (≈102/129/129 ≈ 360). Fold-1 headroom thin (~5-7 events) but declared. Arithmetic plausible against the frozen calendar.

### 9. Selection-freeze readiness — PASS
Each arm is one frozen configuration with every numeric constant traced to literature convention or frozen plan constraints; no grids or ranges; no post-freeze revision clauses; digests recorded and verified (see table); arm keys unique; A1 can freeze `selection_freeze.json` with six unique arm keys.

## Objections by severity

### CRITICAL
None.

### HIGH
None.

### MEDIUM (pre-freeze completeness items for A1; no mechanism change)
- **O1 — A5 stress-cost and turnover ceiling not preregistered.** A4 self-declares a 12 bps stress level and a 6.0x/yr feasibility ceiling; A5 declares only the 10 bps/side base and expectation ranges. PLAN §14 makes "stressed PnL > 0 and stressed PF >= 1.00" and "turnover/capacity remain feasible" applicable per family, and no central control artifact defines the stress schedule (`run_contract.json` and `gates/` checked). Required before/at freeze: A1 records, a priori and outcome-blind, in `selection_freeze.json` (or a spec addendum that does not touch mechanism fields): (a) the A5 stress-cost multiplier (e.g., 2x base = 20 bps/side, mirroring A4's doubling convention), and (b) a numeric A5 turnover feasibility ceiling. Choosing these later would be a post-hoc degree of freedom; freeze is the correct moment to pin them.
- Fix instruction to A1: record O1 items at freeze; do not modify the frozen mechanism, feature, clock, cost-base, or falsification fields of either family.

### LOW
- **O2 — A4 fold-2 expected-slot arithmetic off-by-one.** Recorded 28; derivable 29 month-ends 2020-09-30..2023-01-31 (fill of 2020-09-30 lands 2020-10-01, inside fold 2's scored region). Recorded total 77 vs derivable 78. Erratum note only; the 60/15 minima are unaffected under either count. No repair required before freeze; recommend A1 note the erratum in `selection_freeze.json`.
- **O3 — A4 turnover prior internally inconsistent.** The parenthetical "about 1-2 of 3 holdings change per month" implies ~4-8x gross one-way/yr (each changed leg = 1/3 gross per side, x12 months), while the declared prior is 1.5-3.5x/yr; upper-churn realizations may bind the 6.0x Z6 ceiling. Both figures are explicitly preregistered priors and the 6.0x ceiling is a frozen gate, so this is a prior-hygiene defect, not a mechanism defect; a Z6 ceiling breach is a legitimate frozen-gate outcome, not grounds for repair.
- **O4 — (INFO) A5 fold-1 monthly headroom ~2 events** above the 18/fold minimum (capacity ~20). Declared; no action.
- **O5 — (INFO) A5 neighbour fold-1 weekly headroom ~5-7 events** above the 95/fold minimum (capacity ~100-102 after ramp). Declared; no action.

## Freeze recommendation

All six arms are recommended for the selection freeze:

1. `ARM_A4_ANCHOR_MOM121_EQW_TOP3`
2. `ARM_A4_NEIGHBOR_VOLADJ_MOM121_INVVOL_TOP3`
3. `ARM_A4_NEGCTRL_BOTTOM3_EQW_MOM121`
4. `A5-SFV2-ARM1-TSM12-VOLTARGET`
5. `A5-SFV2-ARM2-SMA200-WEEKLY`
6. `A5-SFV2-ARM3-TSM12-INVERTED-CONTROL`

**A1 must fix before/at freezing:** record in `selection_freeze.json` the A5 preregistered stress-cost multiplier and numeric turnover feasibility ceiling (O1); optionally note the A4 fold-2 slot-count erratum (O2). Nothing else may be changed: any post-audit edit to a mechanism, feature, clock, cost-base, gate, or falsification field voids this authorization and requires re-audit.
