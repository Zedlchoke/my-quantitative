# CONTINUE.md — STOCKS-FREE-V3 TERMINAL (REJECT_ALL) ENTRY STATE

Read `PLAN_stocks.md` completely. It is the fresh-context Stocks authority.

## Measured entry state

- **STOCKS-FREE-V3 is TERMINAL: `STOCKS_FREE_V3_REJECT_ALL`**, confirmed by
  independent terminal A7 (`STOCKS_FREE_V3_REJECT_ALL_CONFIRMED`, commit
  `ad897c8`, re-audit head `3251554`). Both preregistered families ran all
  three scored arms from `STOCKS_FREE_V3_W1 = 586f9fe` after an explicit
  owner GO; budget 6/6; V3 observed = published = 6; reproduction 6/6
  EXACT_MATCH from the detached r-reproduce twin.
- `SFV3-A5-IDIO-SHOCK-REVERSAL` — FAMILY_REJECT. The anchor lost 20.6% of
  equity (PF 0.43, alpha −0.25): market-adjusted idiosyncratic crash and
  overshoot episodes both fail to revert profitably after costs in this
  11-ETF cohort/window.
- `SFV3-A6-TOM-SETTLE` — FAMILY_REJECT. The anchor earned +38.5% raw PnL
  (PF 1.62, 3/3 folds, stress pass) but **negative incremental alpha
  (−0.13) vs risk-matched SPY and a failing placebo control** (mid-month
  window alpha −0.24): the raw PnL is scaled sector beta through a bullish
  window, not a turn-of-month premium. Per PLAN §16, raw PnL cannot
  override failed beta/control gates.
- Statistical denominator: 6 historical Stocks + 6 V3 trials = 12. Zero
  Stage-A survivors; nothing is locked for S1; nothing is promotable.
- S1 `2025-08-01..2026-07-31` remains SEALED_UNTOUCHED (max scored date
  2025-07-31). No paper, testnet, live or order authority exists.
  Workers zero. Integration tree clean. Nothing pushed; main untouched.
- Incident on record: terminal A7 found the ledger's publication digests
  pinned a wrapper, not the artifact bytes (A7T-B1 HIGH); A1 remedied
  append-only (six `ARTIFACT_DIGEST_REPINNED` entries), and A7T's re-audit
  proved the prior rows byte-identical before signing. Earlier incidents
  ADJ-1..ADJ-5 are recorded in `selection_freeze.json` /
  `family_verdicts.json`.
- Authoritative detail: `research/control/stocks_free_v3_run/terminal_report.json`;
  audit: `research/audits/stocks_free_v3/z9_a7_terminal_AUDIT_REPORT.md`.

## What a future stocks cycle inherits

1. Forbidden ancestry now also covers `SFV3-A5-IDIO-SHOCK-REVERSAL` and
   `SFV3-A6-TOM-SETTLE` (plus the non-selected pool and within-cycle
   cluster rule — see `forbidden_family_inventory.json`).
2. Mechanism lessons: (a) sector-beta drift dominates every simple
   long/cash ETF book here — an arm without positive risk-matched excess
   is dead regardless of raw PnL; (b) idiosyncratic daily shock reversal
   does not survive 10 bps/side on this cohort; (c) calendar-window
   premiums must beat the placebo window, not just zero.
3. Reusable, proven infrastructure (do not rebuild): canonical accounting
   `research/assets/stocks/factory.py`, sealed S0 readers
   (`research/stocks_free_v3/isolation.py`), frozen benchmarks +
   incremental-alpha contract, six-arm registry, staged equal-twin
   execution/reproduction pattern, gated publication ledger (with the
   wrapper-digest lesson: pin artifact bytes directly).
4. Any new cycle starts from a fresh owner plan; do not reopen scored V3
   cells, do not rescue either family, do not open S1.

## Boundaries

Unchanged: honest evidence first — REJECT_ALL, BLOCKED, INCOMPLETE are
valid outcomes; no tuning after observing a fold; no S1 access; no
paper/live; historical trees preserved; no push, main merge, worktree
deletion or history rewrite without explicit owner instruction; missing
evidence is `NOT_RUN`/`UNAVAILABLE_FAIL_CLOSED`, never inferred PASS.
