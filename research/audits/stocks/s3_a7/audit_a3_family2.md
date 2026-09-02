# A7 audit — A3 Family 2 `EQ_S2_A3_F2_LISTING_AGE` (listing-age overpricing of young listings)

Sources audited: `research/proposals/stocks/a3_family2.{md,json}` (twin, consistent).

## 1. Dimension findings (PLAN §9)

### Novelty — PASS (moderate-strong)
Young-listing underperformance is a very well-trodden space (Ritter 1991;
Loughran & Ritter 1995). The proposal's differentiators are real: the anchor
signal "is a security-master field: `listed_age = decision_date - listed_date`",
and the family makes the exact data pathologies that fake it — survivorship
sampling, delisting-print truncation, ticker-inception proxies — into declared
falsification conditions ("(c) the edge exists only when delisted names are
dropped or final prints truncated"). Grid prohibition is explicit and credible:
"exactly ONE young-age band (<= 12 months) and ONE seasoned threshold (>= 5
years)... No age grid, no lookback grid, no threshold sweep anywhere".

### Source quality — PASS (strong)
Ten citations, all real (Miller 1977; Ritter 1991; Loughran & Ritter 1995;
Shumway 1997; Shumway & Warther 1999; Field & Hanka 2001; Ofek & Richardson
2003; Nagel 2005; Kumar 2009; Hong & Stein 2007), honestly marked
`MODEL_INTERNAL_UNVERIFIED`. Shumway-style delisting-return treatment is
correctly assigned to the delisting-retention machinery, and the post-2000
episode-concentration caveat is stated rather than hidden.

### Correlation (structural only) — PASS with note
Observable: PIT `listed_age`. Clock: monthly first-session-close formation,
next-open entry, one-month roll. Counterparty: "constrained optimists —
lottery-preference and attention-driven flow plus momentum chasers". Numeric
prewindow rho: NOT_IMPLEMENTABLE_NO_REAL_DATA.
**Note (O2):** the neighbour arm selects its short leg on borrow-fee scarcity —
the same observable family as A5 F1's anchor. See orthogonality matrix.

### Data readiness vs as-built factory — PASS
Verified: `SecurityMaster` carries `listed_date`/`delisted_date`/`last_valid_event`
with effective-dated ticker history anchored at `listed_date`;
`EligibilityInput.history_days` exists; `evaluate_delisting_retention` enforces
final-print retention; `build_rebalance_snapshot` supports age rules as
selection logic; next-open events and one-event delay helpers verified in
`calendar.py`/`execution.py`. Real-data gaps (true PIT list dates, delist
reason codes, PIT GICS, PIT borrow, lockup records) are all correctly declared
UNAVAILABLE_PENDING_ENTITLEMENT, and the "free 'first bar seen' proxy for list
date is precisely the failure mode this family forbids" matches `provider.py`'s
DIAGNOSTIC_ONLY rule.

### Cost/borrow feasibility — PASS (binding constraint honestly declared)
"Young names are frequently unborrowable -- the family accepts reduced short
coverage and re-normalizes rather than simulating free shorts"; "with proxy-
borrow costs the family must be declared borrow-infeasible rather than run on
free shorts"; capacity "low tens of millions USD", young short leg binds;
borrow x2/unavailable stresses are inside the falsification rule; monthly
full-roll turnover (~24 one-side/yr) is coherent with the declared spread/impact
models, and the proposal itself flags that "spreads of tens of bps consume the
expected drift". No free-borrow/free-fill/halt-fill.

### Hidden crypto-family rescue — NO RESCUE (E6 = 1)
- vs M01: different observable (PIT listed_age vs order-book aggressor
  imbalance), counterparty (constrained optimists vs momentum aggressors),
  clock (monthly next-open vs intraday), control (aged-entry cohort clock vs
  crypto placebo). The aged-entry control severs "youngness" by the age clock
  while holding securities/sectors/schedule constant; a surviving drift in the
  control is declared falsifying.
- vs funding-carry: "No funding-rate or carry observable anywhere; the
  short-side fee is a cost/borrow constraint, not a signal" — see O1: true of
  the anchor, tension in the neighbour.
- vs weekly reversal: "the young short leg is not conditioned on past returns"
  — confirmed; monthly age book, not a reversal score.

## 2. Rubric scoring

- E1 = 1; E2 = 1; E3 = 1 (neighbour is mechanism-predictive — constraints bind
  where drift concentrates; the aged-entry control plausibly destroys the
  mechanism); E4 = 1; E5 = 1; E6 = 1; E7 = 1 (0 HIGH/CRITICAL).

**Sum 7/7 — ELIGIBLE.**

## 3. Quality score: 8.0 / 10

Justification: excellent data-artifact-aware construction with a genuinely
causal control expressible today; deep, correctly deployed literature;
borrow-feasibility honesty is exemplary ("declared borrow-infeasible rather
than run on free shorts"). Deductions: base anomaly is heavily documented and
episode-concentrated (null risk on any modern window), and the neighbour's
fee-conditioning creates both an internal attestation tension (O1) and a
cross-family observable overlap with A5 F1 (O2).

## 4. Objections

| id | severity | objection | resolution required |
|---|---|---|---|
| O1 | MEDIUM | Internal attestation tension: "the borrow fee is a cost constraint, not a signal", yet the neighbour's short leg is conditioned on "an available PIT borrow quote at a fee above a declared floor" — there the fee is a selection signal | Freeze must restate the attestation scope (anchor vs neighbour) and declare the fee floor ex ante |
| O2 | MEDIUM | Neighbour observable (borrow-fee scarcity) overlaps A5 F1's anchor observable; if both families are selected the structural matrix must document the shared space (see orthogonality_matrix.md) | Advisory for A1's selection; document, do not block |
| O3 | LOW | Borrow unavailability can shrink the young short leg below diversity; concentration caps could bind | Report short-leg coverage per rebalance as a declared diagnostic (already partially declared) |

## 5. Verdict

**ELIGIBLE** (7/7). No failed rubric items. Expected rank 3 under the frozen
rubric (quality 8.0; loses the 8.0 lex tie-break to `A5-S2-F1-...` because
`E` > `A`).
