# CYCLE VERDICT — EURUSD-OPEN-SEARCH-V2 (TERMINAL, 2026-09-23)

- Branch: `orca/eurusd-open-search-v2-integration` @ terminal anchor
  (see registry); plan `plans/PLAN_eurusd_open_search_v2.md`; owner option
  (a) ("A") opened the campaign — recorded as campaign opener, NOT a GO.
- Data: V1 corpus copied byte-identical (3,652 files verified against
  manifest sha 68416335…) + extension 2026-01..2026-06 (362 files, 0
  missing); full census BUILD_PASS — 130,911 valid 15m bars → 30,550 H1
  bars; 0 non-positive-spread minutes; spread p50 0.3 pips stable through
  2026-H1.

## VERDICT: `CANDIDATE_PENDING_PROSPECTIVE_VERIFICATION`

Exactly one enum per plan §6. For the first time in the program's forex
frontier, a strategy mechanism survived BOTH the 5-year development window
AND the untouched 2026-H1 holdout under measured two-sided costs. This is
program-S0 evidence: it entitles the mechanism to a prospective
(paper-forward) verification track — it is NOT a confirmation of
real-money profitability and opens no order/paper/live surface.

## The mechanism (frozen before the holdout opened)

**FX2-RANGEEXP — wide-prior-day-range fade**: when yesterday's true range
sits in the upper tail of its trailing 60-day distribution, today fade any
extension beyond yesterday's high (short) / low (long); exit halfway back
to the mid; flat every day by 20:00 UTC (no rollover/weekend/swap risk);
fills at next-H1-open at the opposite quote with measured spread.

## Numbers

| window | C3 net | C3 PF | C4 net | C4 PF |
|---|---|---|---|---|
| dev 2021–2025 (walk-forward F1–F6) | +7,147.1 pips | 1.7287 | +6,561.1 | 1.6497 |
| — all six folds | 6/6 positive | | 6/6 positive | |
| **holdout 2026-01..06 (ONE look)** | **+274.0** | 1.3086 | **+217.1** | 1.2368 |
| holdout @1.5× stress | +246.2 | 1.2739 | +189.3 | 1.2039 |
| holdout @2.0× stress | +218.4 | 1.2400 | +161.5 | 1.1718 |

87 trades in the holdout half-year (~15/month); hit ~59%. Preregistered
SUCCESS (net>0 @1.0 AND @1.5) → **MET by both candidates**. Random-matched
baseline −353.5 pips (engine cost honesty); LONG_ALWAYS −395.4.

## Disclosed weaknesses (read before getting excited)

- **SHORT_ALWAYS made +314.0 @1.0 on the same holdout window** — 2026-H1
  drifted down and a naive short beat the candidates on absolute net. The
  mechanism is direction-agnostic and its dev window contains both drift
  regimes (6/6 folds positive through the 2023–2025 long bias AND 2022
  weakness), which argues it is not short-beta — but a 6-month holdout
  cannot separate that cleanly. This is exactly why the verdict is
  "pending prospective verification", not "works".
- Both candidates are sibling configs of ONE mechanism; the holdout is
  effectively a single-mechanism test (disclosed in the freeze).
- Campaign denominator: 48/96 trials observed; RUN-1 of the campaign was
  VOIDED (f_daymom look-ahead bug caught by extended truncation fixtures +
  crash; whole run invalidated, incident artifact
  `outcomes/INCIDENT_RUN1_VOID.json`); RUN-2 is the only admitted record.
- FX2-GAP-C4 (3rd eligible) disclosed, not frozen; near-misses STOCH-C3/C4
  (G2 fail) recorded.

## Governance state

- A7 prelaunch: **AUTHORIZED** (independent byte-exact re-run of both
  candidates on dev; freeze chain + leak guards verified) —
  `audits/a7_prelaunch_audit.*`.
- Leak guards held physically: dev runner saw only bars < 2026-01-01;
  holdout runner only ≥ 2026-01-01; run_count = 1.
- S1 SEALED_UNTOUCHED (this cycle has no S1; the holdout was program-S0).
- Owner GO `GO EURUSD OPEN SEARCH V2 EXPLORATORY SCORED`: never consumed →
  extinguished UNCONSUMED at close (no scored-execution set exists to
  launch: the deliverable is a candidate, not a deployed strategy).
- Budget 48/96 observed. D2 = OWNER_WAIVED_EXPLORATORY in every record.
- Next authorized path (owner decision): open a prospective
  paper-forward tracking cycle for FX2-RANGEEXP (its own plan, freeze,
  gates) — paper evidence only; live trading remains forbidden without a
  separate owner deployment authorization.
