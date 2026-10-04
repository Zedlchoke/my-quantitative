# SLATE_PROPOSAL — SLEEVE-FX5-100K-V1 (Lane F0 court output)

- Court: Lane F0 (MECHANISM/ANCESTRY COURT), pre-GO sleeve program
  SLEEVE-FX5-100K-V1, cycle_id `SLEEVE-FX5-100K-V1-PREGO`.
- Measured-at (UTC, `date -u`): 2026-09-29T01:32:19Z.
- Input: the 15 DISTINCT_TESTABLE census rows (f0/DISTINCT15_INPUT.tsv);
  verdicts in f0/F0_VERDICTS.md (this file does not re-argue them).
- No priority score, no PnL, no backtest, no scoring, no git. Owner dirty tree
  preserved. The closed cycle TERMINAL PORTFOLIO-ROUTER-12ASSETS-100K-V1
  (ROUTER_STATES_THIN) is not rescued by anything below.

## A. Slate

# NO_ELIGIBLE_PROPOSAL

**0 of 15 rows survived the F-0 mechanism/ancestry court; the slate is empty.**

Admission arithmetic: 11 REJECT_VARIANT_SAME_FAMILY, 2 REJECT_NOT_STANDALONE
(EURUSD-S009, AUDUSD-S046), 2 REJECT_DATA_OR_COST (AUDUSD-S087, AUDUSD-S088).
No clustering step was reached (clustering operates on admitted rows only; with
zero admits there is nothing to cluster). This is a valid court outcome under
the dispatch ("do not stretch") and under P-27 law: the F-0 court runs BEFORE
rho and BEFORE PnL precisely so that dead-class variants cost 0 cells.

## B. Why the slate is empty (three structural reasons, not fifteen anecdotes)

1. **The sleeve's own observable classes are already measured-dead on the
   sleeve's own pairs.** The ERP1-TRACKA program (cohorts 1-2, 2026-09-25/26)
   killed, ON AUDUSD+USDCAD 2021-2025 with measured bid/ask costs and a full
   control battery: the range-edge fade class (`TRACKA1-M1-RANGEFADE-PIT`),
   gated variants of it (`TRACKA2-C1C2C3-REGATED-RANGEFADE`, fence: range-
   adjacent triggers need a NEW payer AND a NEW information layer), the
   retest-hold skeleton (`FXFV2-A4-P2`), and — decisively — the day-clock
   momentum/donchian continuation class (`TRACKA2-P3B-DINV-1D`: rho 0.30-0.31
   vs the dead `FX2-H1TSMOM-C1` / `FX2-H1DONCH-C1` shadows, reopening
   condition NONE, "re-clocking is ancestry violation"). Seven of the 15 rows
   (S001/S002-AUD, S002/S004/S025-USDCAD, S079-GBP, S027-EUR) are own-price
   trend/breakout/retest continuation books at H4/D1 clock on these pairs —
   every one lands inside a fence whose text names this exact re-label.
2. **The session-transition and oscillator-fade classes are measured-dead
   program-wide on FX.** FXFV1 (London-open continuation, late-NY fade: 6/6
   reject, 11,459 trades) + FXFV2 (Tokyo-range->London expansion; London-AM
   break+retest: placebo reproduced) close USDJPY-S012's family with the same
   observable and the same payer; FXOS-04 (holdout-failed oscillator MR fade
   on EURUSD with measured costs) + mean-reversion-transfer + the FX2-STOCH-C4
   shadow close AUDUSD-S017's. §14.3 makes sign/threshold/indicator-rename
   non-novelty, so "fade the extension" vs "join the compression" and "TD
   count" vs "Bollinger/RSI/Stoch" do not reopen anything.
3. **The two genuinely-different-payer candidates fail on bookability or
   data, which no payer story can fund.** AUDUSD-S046 is declared non-
   standalone by its own source text. USDCAD-S047's winter-energy payer IS
   distinct from the dead SFV3-A6-TOM-SETTLE equity-settlement payer (the
   court records this explicitly — payer identity alone was not enough to
   kill it as a variant) — but the mechanism needs a WTI hedge leg the FX5
   sleeve does not carry and holds ~1 decision/year (~5 episodes on the
   2021-2026 panels), an arithmetic power kill (P-29 ceiling-x-power: the
   empty grid is a pre-scoring veto). AUDUSD-S087/S088 need an M5 clock and a
   volume/tick-volume conditional on a pair whose declared panel is H1/15m
   with NO volume column — the conditionals are literally uncomputable.

### Salvage observations for a FUTURE cohort (NOT proposals, NOT this cycle)

These are recorded so the dead doors stay closed by condition rather than by
name (P-27 consequence law). None reopens this cycle; each would have to
arrive as a NEW census row through the normal proposal path:

1. **Volume-profile acceptance on the M1 pairs** — the ONLY observable class
   in the 15 with no dead ancestor found in the 169 records. Feasible data
   exists on exactly EURUSD/GBPUSD/USDJPY (Dukascopy `.bi5` carries
   volume_f32, verified in duka_lib.py ">5if"; per-bar spread measurable on
   those three pairs). Reopening shape: a new row proposing the value-area
   acceptance decision on an M1 pair's own volume — with a lagged-twin control
   and an inverted (break-join vs fade) arm per P-28. Pair-swap of AUDUSD-S087
   does NOT reopen row 7 (P-29); a new mechanism row on M1-pair data would be
   a fresh F-0 case.
2. **A calendar-conditioned FX book with a genuinely observed flow payer** —
   both calendar rows died on non-bookability/power, not on the payer
   question. Any successor must bring an OBSERVED flow source (e.g. measured
   fixing/rebalance prints), not an own-price proxy — the observed-CoT
   ancestor `COMMNG1-A4-P2-ARM1-NEUTRAL` shows even observed positioning
   loses to its own release-clock shadow, so the bar is: beat a clock-only
   shadow (Q-7) with the flow observable doing measurable work (Q-11).
3. **If the sleeve's data authority is extended to the ERP1 raw M1 corpus for
   AUDUSD/USDCAD** (which physically exists: 2,007 BID+ASK day-files per pair,
   2021-01..2026-06), rows 7-8's DATA kills would need re-adjudication —
   note the 2026-H1 segment of those panels is sealed holdout
   (ERP1-TRACKA-COHORT-2 PITDATA report) and must not be spent on a blocked
   mechanism (precedent: DTPFX1-A1-MEFIX-VARIANT).

## C. What this court did NOT do (scope fence)

- No rho measurement (F-0 precedes rho per P-27; with 0 admits there is
  nothing to measure against).
- No cost ceilings computed per mechanism (no mechanism survived to need one).
  For the record, the cost bands the slate WOULD have had to clear live in
  `research/control/PORTFOLIO-ROUTER-12ASSETS-100K-V1/cost/COST_ACCOUNTING_SPEC.md`
  §1.1: measured spread p50/p90 0.1-0.6 pip in ONE 02Z bucket (EURUSD 0.1/0.2,
  GBPUSD 0.4/0.5, USDJPY 0.4/0.6, USDCAD 0.6/0.6); unmeasured-bucket default
  2x measured p90 (floor 0.5 pip); commission 0.35 bps/side [DEFAULT U2];
  slippage 0.2/1.0 pip [DEFAULT U3]; swap 1.0 pip/night against position, Wed
  x3 [DEFAULT U4]; stress tiers 1.0/1.5/2.0x. The AUDUSD/USDCAD session-
  spread censuses (ERP1): AUDUSD p50 1.0 / USDCAD p50 1.2 pips overall,
  Sunday-open buckets 4.6/6.8 pips — the measured reason intraday fade books
  on those pairs died cost-dominated before.
- No rescue of TERMINAL PORTFOLIO-ROUTER-12ASSETS-100K-V1 (ROUTER_STATES_THIN)
  and no write to any ledger or registry.

## D. Court recommendation to the owner

Do not spend sleeve cells on any of the 15 rows. If the program wants a
populated slate, the cheapest legal paths are (in order): (1) a new census
pass over the FOREX-UNIFIED corpus whose ancestry search is class-based (the
current census missed nine applicable dead ancestors — incident N-1 in
F0_VERDICTS.md), filtering OUT every own-price trend/breakout/retest/
oscillator-fade/session-transition re-label up front; (2) the M1-pair
volume-profile class (salvage note 1), the one genuinely unclaimed observable
surface found in this review.
