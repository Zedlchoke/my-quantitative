# A4 distress lane — D1 blind proposals (STOCKS-FREE-V9)

Lane: distress / delisting-risk conditioning (mandatory lane, PLAN_stocks_v9 §2 axis 1).
Wave SHA `86fecae8044d344e5d5ea9a49bbcfdb2f03c0b5a`, branch
`orca/stocks-free-v9-d1-a4-distress`. Outcome-blind: no returns computed in this lane.

## The two mechanisms

**SFV9-A4-H1 — Market-cushion failure proximity** (Campbell-Hilscher OME / Merton
distance lineage). Anchor ranks `s = L/(L+ME)` with `ME = RAW close × funded share
count`; far-from-failure tercile long, nearest-failure tercile short, sector-neutral,
inherited 21-session grid. Mechanism: mandate-constrained holders are forced sellers
only after the equity cushion visibly collapses, while lottery-preferring buyers
overweight far-out-of-the-money distressed equity — high failure probability prices
too high and drifts down (CH 2008). Neighbour: `Cash/(Assets−SE+ME)` (CASHMTA form,
same market-assets frame). Control: `L/(L+SE)` — book leverage with ZERO price and
ZERO share-count inputs. If the book-only control reproduces the anchor ≥0.5×, the
information is generic accounting leverage and the market-proximity claim is dead.
Momentum confound handled by a preregistered pre-selection bar (D2 rho vs 63-session
prior-return rank < 0.80, the V4/V5 catch region). Requires dead names: they populate
the near-failure tail; delisting returns ride the price series under the preregistered
dead-name book semantics.

**SFV9-A4-H2 — Cash-net depletion runway** (Shumway profitability / Ohlson-Altman
book lineage; pure filing data, no market input). Anchor score
`(RE(prior-year) − RE(now) − Cash(now))/Assets(now)` — an equal-weight Altman-form
linear distress score (depletion flow minus cash stock, one scaler, no free
parameters); RE legs are two as-of evaluations of one funded clock, fiscal-matched
330–400 effective days apart (inherited F-A7-7 guard); accruing+cash-rich long,
burning+cash-thin short. Neighbour: depletion velocity alone (trajectory without
runway). Control: `Cash/Assets` alone (runway without trajectory, single vintage,
no RE). The falsifiable claim is the JOINT: neighbour supports, control does not
reproduce — if cash level alone reproduces ≥0.5×, the effect is the thin-cash
characteristic (the exact pattern that killed V8 F1 via its stock-level control).
Sampling floor: fiscal-matched deltas populating <25% of eligible names at the median
decision = BLOCKED_DATA close at dry-run, never re-matched.

Both packets: both cohort legs (ALIVE_EVIDENCED 410 + DEAD_PRICE_CONFIRMED 1550),
inherited eligibility floor (63 bars, ADV63 ≥ $2M band C+, RAW ≥ $1.00), sector-neutral
terciles with min-6 abstention, inherited band costs A/B/C 10/15/25 bps (stress
20/30/50, fail-closed band resolution L-I3), preregistered fill-check /
exit-at-last-close / no-survivorship-resubstitution semantics. All fundamental inputs
cite the 800-day bounded funded clocks only — declared ex ante because on a
death-inclusive cohort an unbounded clock would let filing STALENESS become the
ranking variable (a vintage-age shadow). Clocks cited (all verified verbatim in
`p2_v9_coverage_first.json` dead_leg_funded_clocks, 56 clocks / 33 fields):
H1 — Liabilities/800, dei:EntityCommonStockSharesOutstanding/800,
StockholdersEquity/800, Assets/800, CashAndCashEquivalentsAtCarryingValue/800;
H2 — RetainedEarningsAccumulatedDeficit/800, Cash.../800, Assets/800.

## Control design rationale

Each control shares the minimum with its anchor needed to test one specific
alternative explanation and nothing more: H1's control removes the price leg
entirely (tests "market-transmitted" vs "book level"); H2's control removes the
trajectory entirely (tests "burn×runway interaction" vs "thin-cash level"). Both
controls are declared not-rank-identical (rho < 0.95 measured at D2 pre-selection)
per the V4/V5 lesson where rho 0.78–0.83 rank-identity was caught before selection.
Novelty declarations in each packet enumerate every forbidden ancestor
(SFV8-F1/F2 + shadows, V4 semivariance/participation, V2 momentum, V5 price placebo,
death-event axis) with concrete design differences; ancestral |rho| ≤ 0.20 gates are
D2 measurements, never prose.

## Self-check output (a4_distress_selfcheck.py, EXIT=0)

```
TOTAL: 38 checks, 0 FAIL, 38 PASS
```
Per packet (H1 and H2 identical check set, all PASS): json.load parses; schema
`stocks_free_v9_run/d1_proposal@1`; hypothesis_id; all required fields present; lane
is distress; wave_sha == HEAD; exactly 3 arms anchor/neighbour/control; mechanism
paragraph (who/why/observable/when); all cited clocks verbatim in the funded set
(H1: 5, H2: 3); universe has both cohort legs; eligibility floor (63-bar + band);
sector conditioning; dead-name book semantics; inherited 21-session grid no
deviation; band costs 10/15/25 + stress; margin-to-fail covers inherited gates;
novelty lists SFV8-F1+F2; control differs from anchor in data space; outcome-blind
attestation verbatim.

## Notes / limitations

- No BLOCKED condition: all input authorities present and read.
- `HYPOTHESIS_LEDGER.md` and `LESSONS.md` are not present on this worktree branch;
  the root copies (`/Users/hoangminhlong/my-quantitative/research/wayfinder/`) were
  read read-only as the authoritative cumulative register (P-1..P-8 honored).
- Warmup: H1 all arms 0 (level arms, F2 precedent); H2 anchor 4 (YoY delta arm,
  F1 precedent), neighbour/control 0.
- Feasibility note: the one bounded kernel change both families need is replacing
  the V8 runner's missing-price-leg skip with the preregistered exit-at-last-close
  dead-name semantics (frozen in p3); share-count fields load under unit "shares"
  (unit-aware, fail-closed); ME is split-aligned via the frozen corporate-actions
  module.
