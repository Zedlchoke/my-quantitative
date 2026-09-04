# A5 lane search log — FOREX-FREE-V2, cycle F2-D1

- date: 2026-09-04
- lane: `.worktrees/forex-free-v2/d1-a5-proposals` (branch `orca/forex-free-v2-a5-proposals`, base `9e7e89c253caee2d7ec2681bbfe9e375da84c0d5`)
- assigned mechanism class: cross-sectional dispersion / relative-value dislocation
- deliverables: exactly two outcome-blind proposals (`proposal_1.json`, `proposal_2.json`) + this log

## 1. Information firewall (attestation)

Read (allowlist only): `PLAN_forex_v2.md`; `research/control/forex_free_v2_run/{run_contract,frequency_contract,data_manifest,forbidden_family_inventory}.json`; `research/assets/forex/sessions.py`; `research/assets/forex/calendar.py`; `research/assets/forex_free_v1/td_loader.py` (bar JSON schema only: `datetime/open/high/low/close`, completed-bar rule, quarantine rule).

NOT opened, grepped or read: anything under `research/control/forex_free_v1_run/`; `research/assets/forex_free_v1/{family1,family2,scored_runner,exec_driver,probe_td,completion_pass,repair_pass}.py`; anything under `research/proposals/` (any cycle — including directories only created, never listed); `tests/assets/forex_free_v1/`; `PLAN_forex.md`; any git history (`git log/show/diff` never invoked; only `branch --show-current`, `status --short`, `rev-parse HEAD` for lane identity).

No `data_raw/**` reads; no backtest, schedule simulation, or PnL computation of any kind was run. Both proposals are schedule-level designs with frozen constants only.

## 2. Design constraints taken as frozen

7 pairs (EUR/USD, GBP/USD, AUD/USD, NZD/USD, USD/JPY, USD/CHF, USD/CAD); H1 OHLC bar-open UTC grid only; D1 context-only; H4/bid-ask/rollover unavailable; missing bar => NO_TRADE fail-closed; 1.5 bps x tier {1.0,1.5,2.0} per side per leg on 10000 USD-unit notional; <= 1 entry/pair/UTC-day; <= 3 RT/pair/week; flat at the 16:00 America/New_York bar open (strictly before 17:00 NY rollover; 20:00Z EDT / 21:00Z EST); entry at next allowed H1 open after decision-bar completion; 3 chronological folds; pair-concentration and drop-one-pair checks; no grids/menus.

Forbidden-family discipline: V1's London-open continuation and late-NY standardized-extension fade (and nearby-clock/threshold/sign variants) are ineligible. Both A5 proposals are cross-sectional long-short constructions with no session-open clock and no single-pair directional signal, so they do not reuse, invert, or relabel either rejected family.

## 3. Candidate constructions considered (search process)

1. **Triangular parity / synthetic-cross arbitrage** — REJECTED as infeasible in this universe: the universe is USD + 6 foreign currencies, so every implied foreign/foreign cross (e.g. EUR/JPY from EUR/USD x USD/JPY) has no tradable third leg among the 7 pairs; no parity violation is observable or tradeable. Recorded so A7 sees the dead end was reasoned, not missed.
2. **Dispersion-regime directional USD bet (trade the level of cross-sectional dispersion as a risk state)** — REJECTED: it is a directional USD-factor bet, not USD-neutral; the class requires relative-value constructions.
3. **Basket-vs-all-members (member vs equal-weighted 7-pair basket, 7 legs)** — REJECTED on honest cost: 7 legs x 2 sides x 1.5 bps = 21 bps round trip intraday; designed-to-fail hurdle; not proposed.
4. **Correlation-breakdown pairs-of-pairs (trailing-correlation member divergence)** — REJECTED for internal overlap: with 7 pairs its trade reduces to a long-one/short-one cross spread selected from the same cross-sectional extremes as P1; signal novelty too thin to survive an overlap audit.
5. **Cross-pair lead/lag** — LEFT TO OTHER LANES: it is a separate listed V2 search domain (PLAN_forex_v2.md section 2) and not a dispersion/convergence construction; proposing it here would crowd the class assignment.
6. **SELECTED P1: same-day extreme residual dislocation convergence** — dispersion of day-to-date pair returns around the cross-sectional (USD-factor-removed) mean; extreme-vs-extreme spread; intraday convergence exit.
7. **SELECTED P2: prior-session outlier basket reversal** — cross-sectional reversal of the previous trading day's demeaned outliers, bottom-2 vs top-2 baskets, inter-day driver (liquidity provision), hold-to-flat exit.

## 4. Why the two are genuinely different mechanisms

| dimension | P1 | P2 |
|---|---|---|
| causal driver | intraday overshoot-and-correction of a same-day pair-specific dislocation (order-cluster microstructure) | inter-day inventory unwinding / liquidity-provision compensation for yesterday's one-sided flow |
| signal window | current trading day, day-to-date, measured at the decision bar | the PREVIOUS full trading session (T-1), stale by construction |
| trade object | argmin-vs-argmax extreme pair spread (2 legs) | bottom-2 vs top-2 demeaned baskets (4 legs) |
| decision/entry clock | 12:00Z decision bar -> 13:00Z entry | 07:00Z decision bar -> 08:00Z entry |
| exit | conditional half-reversion (0.5 x entry dislocation) or forced flat | hold-to-flat (forced flat is the only exit) |
| literature | Lustig-Roussanov-Verdelhan 2011 JF; Osler 2003 JF | Lehmann 1990 QJE; Nagel 2012 RFS |
| round-trip cost (base) | 6.0 bps | 12.0 bps |

Shared skeleton (unavoidable in this universe): any USD-neutral RV trade is an equal-notional long/short set whose spread cancels the equal-weighted USD index exactly; both proposals freeze that algebra explicitly and additionally freeze a USD-drift diagnostic expectation.

## 5. Literature confidence notes (anti-fabrication)

All four citations are real works whose existence and content the author is certain of: Lustig/Roussanov/Verdelhan, "Common Risk Factors in Currency Markets", Journal of Finance 66(4), 2011 (dollar factor + cross-sectional carry factor; dollar-neutral portfolios isolate the cross-section). Osler, "Currency Orders and Exchange Rate Dynamics: An Explanation for the Predictive Success of Technical Analysis", Journal of Finance 58(5), 2003 (order clustering at predictable levels; execution-driven overshoot and reversal). Lehmann, "Fads, Martingales, and Market Efficiency", Quarterly Journal of Economics 105(1), 1990 (weekly cross-sectional contrarian/reversal profits). Nagel, "Evaporating Liquidity", Review of Financial Studies 25(7), 2012 (short-term reversal as liquidity-provision compensation). Claims in the JSONs are restricted to what these papers actually show; Lehmann and Nagel are equity-market results ported as mechanism templates and are labeled as such in the economic_mechanism text (the tradeable claim for FX is the proposal's own causal prediction, falsifiable by the frozen arms).

## 6. Honest cost and frequency math (a priori, no data)

- P1: 2 legs -> 4 side-leg charges/RT -> 6.0/9.0/12.0 bps RT at tiers 1.0/1.5/2.0. Frequency: gate z-range >= 3.0 fires ~0.5-0.7 of days -> ~3.0 RT/week total -> ~0.86 RT/pair/week; substitution backstop enforces the 3 RT/pair/week cap in the worst case.
- P2: 4 legs -> 8 side-leg charges/RT -> 12.0/18.0/24.0 bps RT. Frequency: gate z-range >= 2.0 fires ~0.6-0.8 of days -> ~3.5 RT/week total -> ~2.0 RT/pair/week expected, capped at 3 by the frozen substitution backstop.
- Both: break-even diagnostic computes empirical C* = mean gross bps / (side-leg charges) and requires C* > 1.5 (base) and C* > 3.0 (tier 2.0 with its extra fill delay). No cost menu exists anywhere; tiers are the frozen authority.

## 7. Fail-closed mechanics shared by both proposals

Missing any required bar for any pair (day-first bar, decision bar, monitoring bar, or trailing sigma windows) => NO_DECISION/NO_TRADE for that day; never fill-forward. Cross-sectional computations require all 7 pairs; a missing forced-flat bar exits at the first later H1 open the same UTC day, logged FAIL_LATE_FILL. All signal clocks frozen in UTC; the forced-flat boundary alone is New-York anchored via zoneinfo (DST-correct). Warmup 600 H1 bars both proposals.
