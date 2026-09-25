# INCIDENT — RANGEFADE ancestor-law PIT seam (recorded 2026-09-25)

Namespace: `ECONOMIC-ROBUSTNESS-PROGRAM-V1/tracka_cohort1/` (umbrella control
plane; handbook §26 format). Recorded by A1 from the outcome-blind council's
code-audit findings + A7's independent line-by-line confirmation
(`A7_tracka1_plan_audit_REPORT.md` §C, all claims CONFIRMED). **Nothing was
executed, restarted, edited or re-scored to record this incident.**

## What happened

A static code audit of the frozen ancestor signal law (no PnL computed
anywhere) found that the law scored by three ancestry cycles contains a
same-day lookahead in its regime variable, plus two structural seams:

1. **Whole-day mode leak.** In `f_rangeexp` (code authority
   `.worktrees/fx-rangefade-2m-shadow-v1/research/control/EURUSD-RANGEEXP-SCORED-V1/scripts/v2_lib.py:265-320`),
   the day-`d` fade/follow mode `pct[d]` is the percentile of day `d`'s OWN
   FULL-DAY high−low range (`ranges[d][0]` at :271; `pct` at :274-281;
   `_prev_day_stats` accumulates full-day stats at :66-79) and is consumed at
   day `d`'s first bar (:291-301). The mode is therefore decided up to ~20
   hours before the information exists; 100% of day-`d` session fills inherit
   it (first fillable hour 07:00; full-day range completes ~20:00 UTC).
2. **Hindsight flat-day filter.** The `pct[d] > 0` guard (:293) silently
   refuses to trade exactly the days whose full-day range ties/undercuts the
   trailing 60-day minimum — a hindsight range filter.
3. **Three-laws seam.** The running shadow daemon
   (`FX-RANGEFADE-2M-SHADOW-V1/daemon/shadow_daemon.py:225-228, 277-288`)
   replays the same function on a growing panel, so its day-`d` mode is a
   RUNNING partial-range percentile that can flip intraday — a THIRD law,
   PIT-legal in itself but numerically different from both the scored
   backtest law (full-day percentile) and the PIT-clean re-specification
   (`pct[d−1]`, frozen as R-ANCHOR in the child plan). The daemon's parity
   self-test (:515-525) compares the same function on the same panel and is
   structurally blind to this divergence; `:284` sets a cosmetic hard-coded
   PASS.

## Scope — which evidence is affected

- **Ancestor backtests are NO LONGER evidence for the daemon's running law,
  and never were evidence for the PIT-clean law.** By direct consequence of
  finding 1+3: the scored results of `EURUSD-OPEN-SEARCH-V2` (selection +
  its one holdout look), `EURUSD-RANGEEXP-SCORED-V1` (scored confirmation)
  and `FX-MAJORS-SEARCH-V1` (GBPUSD/USDJPY transfer + holdouts) were all
  computed under the leaking R-ORIG semantics. They remain valid AS
  historical facts about R-ORIG on those consumed windows (append-only
  evidence, unchanged), but:
  - they MUST NOT be cited as evidence about the law the daemon is running
    (different law), nor about the PIT-clean R-ANCHOR (never measured);
  - no future artifact may cite the shadow's "parity self-test PASS" as
    evidence about R-ORIG semantics.
- The prospective shadow journal (FX-RANGEFADE-2M-SHADOW-V1) is unaffected
  as raw data (it records what the daemon law actually did) but its
  interpretive class changes pending owner decision — see the separate
  classification proposal (`PROPOSAL_SHADOW_CLASSIFICATION_FX-RANGEFADE-2M_2026-09-25.md`).

## Outcome-data exposure? / repair

- None. No new computation was run to produce this incident; the findings are
  static code reads, independently confirmed by A7 at
  `69ddc60447d223249319f82b71b21e26ab941203` with line citations.
- No repair performed or needed to historical artifacts: ledgers, journals,
  verdicts and worktrees are append-only evidence and were not touched.
  The daemon process (PID 79157) was verified alive and untouched.

## Why the program's conclusions remain valid (and how they change)

- The incident does not invalidate any recorded TERMINAL verdict (those were
  facts about R-ORIG windows). It invalidates a FUTURE inference: treating
  ancestry outcomes as support for "the RANGEFADE mechanism" as such.
- The child plan `ERP1-TRACKA-COHORT-1` (§4.2) is built on exactly this
  correction: R-ANCHOR (PIT-clean, `pct[d−1]`) is the only selectable
  anchor; R-ORIG runs only as the leak-probe diagnostic; falsifier F-PIT-1
  (M-1..M-5 + the three-clause seam law) adjudicates before any PnL, with
  `KILL_PIT_SEAM` as an accepted outcome.

## Prevention added

- F-PIT-1 mutation battery M-1..M-5 (shift-equivalence proof, non-vacuity
  floor, daemon-seam emulation, self-test-blindness fixture, panel-truncation
  PIT proof) frozen in the child plan §8 before GO-1.
- Semantic diff table law: any prose describing the law cites code authority;
  the §4.2 erratum precedent (prose inverted the code mapping) is recorded.
- Citation ban: "shadow parity PASS" may not be cited as semantics evidence;
  ancestry numbers carry the `R-ORIG-SEMANTICS` provenance label in future
  artifacts of this program.
