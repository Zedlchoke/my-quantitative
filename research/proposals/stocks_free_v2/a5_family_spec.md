# A5 Family Specification — Time-Series ETF Trend with Volatility-Aware Defensive Allocation

- Family ID: **A5-SFV2-TREND-DEFENSIVE**
- Lane: Z3/A5 (stocks-free-v2). Outcome-blind specification; **no scored artifact exists and none may be created by this lane.**
- Base commit: `b345de411440b8db2f87a2ee61803f1d4aacc378`, branch `orca/stocks-free-v2-z3-trend`, tree clean at spec time.
- Created: 2026-09-03. Authority for digests: `a5_family_manifest.json` (sha256 `d69fb046b9b148f36747ce8968b332b071420f7836fc74a830b242dec3b4a3c8`).

## 0. Outcome-blind attestation

No returns, PnL, profit factor, Sharpe, ranking or backtest of any arm has been computed or read by the
Z3/A5 lane. All turnover ranges and event counts below are preregistered **expectations** derived from rule
structure and the frozen calendar, not computed results. The A4 (z3-momentum) lane's work was not read.
Budget remains 0/6 until Z8.

## 1. Mechanism and economic rationale

The family tests whether an ETF's **own trailing trend** (time-series momentum / moving-average trend)
carries forward-looking information for long-only exposure, and whether a **deterministic realized-vol
de-risking overlay** (vol target mapped to an equity/cash split) improves risk-adjusted evidence. Defensiveness
is **cash only**: TLT and GLD were excluded pre-census (`ISSUER_EVENT_VERIFICATION_UNAVAILABLE`), so no bond or
gold defensive asset exists in this cycle.

Literature basis (all `MODEL_INTERNAL_UNVERIFIED` — internal knowledge, no quotes/DOIs asserted):
Moskowitz/Ooi/Pedersen 2012 (JFE 104(2), time-series momentum, 12-month lookback); Faber 2007 (SSRN,
10-month SMA tactical timing); Barroso/Santa-Clara 2015 (JFE 116(1), vol-scaled momentum); Daniel/Moskowitz
2016 (JFE 122(2), momentum crashes and vol management); Moreira/Muir 2017 (JF 72(4), volatility-managed
portfolios); Zakamulin (data-snooping critique of MA rules — motivates freezing one canonical configuration).

## 2. Cohort usage (frozen)

All **11 accepted ETFs** — SPY, XLK, XLE, XLF, XLV, XLI, XLP, XLY, XLU, XLB, XLRE — are investable members
under one identical rule per arm; SPY additionally serves as the context benchmark. Cohort digest
`c9d4e88a33c53448120e79138057bcb0d100abecc1d33fbec92bd3d9c541bc96`.

Why broad + sectors and not a SPY-only core: (i) a SPY-only book places 100% of positive PnL in one ETF,
violating the preregistered <=35% positive-PnL concentration limit; (ii) index-level TSMOM is the literature's
core asset and sector-level trend timing is documented in the tactical-allocation literature. Declared
limitations: the 10 sectors plus SPY overlap heavily — equal weighting them is a fixed breadth choice, **not**
a diversification claim; the cohort is a current-survivor list; inference is limited to this frozen ETF cohort.

## 3. The three preregistered arms

| # | Arm ID | Role | One-line definition | Spec sha256 |
|---|--------|------|---------------------|-------------|
| 1 | `A5-SFV2-ARM1-TSM12-VOLTARGET` | Literature-backed anchor | Per-ETF 252-session (12m) time-series momentum sign gate on TR chains; eligible ETFs equal-weighted, cap 35%; gross scaled by `min(1, 10%/realized-vol)`; residual cash; MONTHLY clock | `6c301db551c8e5faa68bb923411137c28581d5aa9816984d076e3cbf603cfc57` |
| 2 | `A5-SFV2-ARM2-SMA200-WEEKLY` | Theoretically justified neighbour | Per-ETF 200-session SMA filter (TR close above its 200-session mean); identical vol-target mapping/caps; WEEKLY clock. Lever changed: trend-estimator form | `8c65c0d7ea7582b70df0c216c42b202f5ca23788a06945ec2e9676837e69c4c1` |
| 3 | `A5-SFV2-ARM3-TSM12-INVERTED-CONTROL` | Causal negative control | Exact sign inversion of the anchor: eligible iff 12m return NEGATIVE; everything else identical. Destroys the trend-selection mechanism | `5f3d93ba85241d22bde44978efa0bc98d3c5fbdb9cbee6f2d8881d313db39527` |

These are **single frozen configurations, explicitly NOT a grid**: one lookback, one threshold, one estimator,
one vol target, one cap, one clock per arm. No parameter anywhere in this family was chosen by comparing
candidate outcomes.

## 4. Feature definitions and volatility estimator (frozen)

- **TR chain (signals):** amended FD2 architecture (`split_factors.json`, `amended_fd2_formula`): raw closes
  x issuer-confirmed split factors (XLK/XLE/XLY/XLU/XLB factor 2.0, eff 2025-12-05) + official SSGA/SPDR
  distribution records; TD `adjust=all` cross-check is smooth through the split. Features never use raw fill
  prices; fills never use TR prices.
- **Arm 1/3 signal:** `m_i(t) = TR_i(t)/TR_i(t-252) - 1` on completed sessions; eligible iff `m>0` (anchor) /
  `m<0` (control); `m==0` -> ineligible. No 1-month skip: the skip convention exists for cross-sectional
  reversal; canonical TSMOM uses the trailing 12-month return directly.
- **Arm 2 signal:** eligible iff `TR_i(t) > mean(TR_i, last 200 completed sessions)`; tie -> ineligible.
- **Vol estimator (all arms):** per-ETF `sigma_i` = std(ddof=1) of last 63 completed daily simple TR returns,
  annualized sqrt(252); `sigma_arena = sqrt(mean of sigma_i^2 over eligible i)` — deterministic variance
  average, no covariance estimation (sectors are highly correlated; declared a priori simplification).
- **Defensive mapping (all arms):** `g(t) = min(1.0, 0.10/sigma_arena)` (g=1 if sigma_arena<=0);
  `w_i = min(0.35, 1/|eligible|)`; final ETF weight `g*w_i`; **residual to CASH, never redistributed**. Empty
  eligible set -> 100% cash. Invariants: gross <= 1.0 always; single-ETF weight <= 0.35 always; long-only;
  no shorting; no leverage.

## 5. Decision clock and fills

- Anchor and control: **MONTHLY** — last completed regular session of each calendar month.
- Neighbour: **WEEKLY** — last completed regular session of each ISO week.
- Fill: next regular session, **RAW** executable closes, one-event delay mandatory, never the signal close.
  Targets are notional-based, so the S1 2025-12-05 raw-price halving changes share counts only, never weights.
- Full rebalance to the target book at each decision event; no intra-period trading.

## 6. Warmup, folds, purge, terminal handling

- Official warmup 2018-01-02..2018-04-03 (63 sessions): no scored trades.
- **Ramp-in rule (declared):** official warmup is shorter than the feature lookbacks (252/200 sessions).
  Data may not be extended backward or fabricated, so decisions are allowed only once every cohort member has
  >= L completed TR sessions from coverage start (L=252 anchor/control, L=200 neighbour); before that the book
  is 100% cash and unscored. Expected first decision: ~2019-01 (anchor/control), ~2018-10 (neighbour).
- Folds (purge 5, force-flat): S0_FOLD_1 scored 2018-04-04..2020-09-01; S0_FOLD_2 2020-09-10..2023-02-09;
  S0_FOLD_3 2023-02-17..2025-07-24. **Terminal:** fills only on sessions <= the fold's scored_end; book
  force-flat at scored_end close; no executions during purge; each fold starts flat.
- **S1 2025-08-01..2026-07-31 SEALED — existence only.** The 2025-12-05 split event lies inside S1; S0 is
  unaffected; TR-chain semantics above keep signals continuous there.

## 7. Benchmark, costs, delay

- **Hard benchmark: flat 0%** (cash at zero rate) — the primary directional gate for every arm.
- **Context benchmark: SPY TR** (amended architecture), reported as exposure/beta diagnostic, not the pass/fail
  gate. Fairness: identical costs, delay, caps and clocks structure across arms; SPY is treated like any other
  investable under the arm's rule.
- Costs: **10 bps per side** conservative spread+slippage (declared a priori; MODEL_INTERNAL_UNVERIFIED for
  current levels); one-event delay mandatory; no commission claims; cash rate 0.

## 8. Turnover expectation and capacity

- Anchor/control: expected **2.0x-4.0x** two-way annual (monthly clock, sticky binary states).
- Neighbour: expected **3.0x-6.0x** (weekly clock, very sticky SMA state). Context only: at 10 bps/side this
  bounds cost drag around ~0.6-0.9%/yr upper. All figures are preregistered expectations (rule structure),
  never computed; realized turnover is measured only by Z5/Z6 schedule-only feasibility.
- Capacity: least liquid cohort member is XLRE (median daily dollar volume $196.9M, census). Declared research
  scope <= $10M notional -> participation orders of magnitude below 0.1% of that median. **No capacity claim
  beyond research scale.**

## 9. Concentration limits

Per-ETF gross cap **35%** (structural, always enforced). Post-scoring validity condition (Z8-checked): **no
single ETF > 35% of positive PnL** across S0; violation voids the arm; its slot stays unused (no reassignment,
PLAN §10).

## 10. Minimum evidence count

- Anchor/control: **>= 18 scored monthly decision events per fold and >= 70 across S0** (an event counts when
  its fills and force-flat liquidation both land inside the fold's scored window; 100%-cash decision events
  count).
- Neighbour: **>= 95 scored weekly events per fold and >= 340 across S0**.
- Exact counts derive from the frozen calendar at implementation; minimums leave headroom for the fold-1
  ramp-in. Below minimum -> arm VOID, slot unused.

## 11. Falsification rule (family)

**FALSIFIED** iff the causal control `A5-SFV2-ARM3-TSM12-INVERTED-CONTROL` achieves fold-level risk-adjusted
evidence (Z8 frozen scorer primary statistic: excess vs flat 0% benchmark, realized-vol-normalized, per S0
fold) **>= anchor in >= 2 of 3 S0 folds**. Predeclared expected direction: the control is materially below the
anchor (near or below zero). On falsification, all positive family claims are void and the family's three
slots stay unused. If the control voids itself (evidence minimums / invariant failures), the mechanism is
**UNTESTED** — not established, not supported. Naming the Z8 statistic here is preregistration; this lane
computes nothing.

## 12. Exact digests

| Artifact | sha256 |
|---|---|
| `a5_family_manifest.json` | `d69fb046b9b148f36747ce8968b332b071420f7836fc74a830b242dec3b4a3c8` |
| `a5_arm1_tsm12_ivol.json` | `6c301db551c8e5faa68bb923411137c28581d5aa9816984d076e3cbf603cfc57` |
| `a5_arm2_sma200_weekly.json` | `8c65c0d7ea7582b70df0c216c42b202f5ca23788a06945ec2e9676837e69c4c1` |
| `a5_arm3_tsm12_inverted_control.json` | `5f3d93ba85241d22bde44978efa0bc98d3c5fbdb9cbee6f2d8881d313db39527` |
| `cohort_census.json` (input) | `4f9cab6af48126955a92e4d5d9ef12954a59a59a8250175a4c2d31cdc65a3a0f` |
| `partition.json` (input) | `9b4ad7993f943edb1f4a995184eb85083879168f9f86eb1720b2a66623ef17c7` |
| `run_contract.json` (input) | `65410307ca4e8b25fa31d74f1ebad0562097f32d251f5316bd007c0f435735d8` |
| `split_factors.json` (input) | `f666565124155bd26ecec8de9b88864b58f85831f404ccac48bcbb8cc135fc9b` |
| `da2_evidence.json` (input) | `014e73682fa45d60332dcdac6f07b2807d51556cfff192baa6cd35bea172a1da` |
| `PLAN_stocks_free.md` (input) | `d3458d858f0c39371361819541189e8e6b2ef4e310bde94edf40bf92919f7318` |

## 13. No-tuning declaration

Every constant (252/200-session lookbacks, zero threshold and zero skip, 63-session vol window, 10% vol
target, 35% cap, monthly/weekly clocks, 10 bps/side) was preregistered at spec time from literature convention
or the plan's frozen constraints. No grid exists; no parameter was selected by comparing candidate outcomes on
any window; no parameter will be revised after freeze; S1 was never read and cannot influence this spec.

## 14. Implementation binding notes (for Z5/Z6, informative)

Required fixtures per PLAN §11: hand-computed feature vectors; one-event lag and no-lookahead; raw-fill vs
TR-signal separation; cash-state / no-short / no-leverage invariants; deterministic target books;
expected-sign and control-destruction fixtures; weekly/monthly calendar goldens; terminal-close goldens;
identity/config digest stability (manifest arm sha256s above must reproduce byte-exactly); double-generation
equality. Exposure diagnostics to be published (not tuned on): time-weighted mean gross, fraction of decision
events at 100% cash, per-ETF weight histograms, realized turnover, sector-overlap fraction.
