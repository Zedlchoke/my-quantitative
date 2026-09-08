# A4 search log — FOREX-FREE-V2 F2-D1

Lane: A4 (proposals) — branch `orca/forex-free-v2-a4-proposals`
Base: `9e7e89c253caee2d7ec2681bbfe9e375da84c0d5`
Date: 2026-09-04
Assigned mechanism class: **conditional session-range expansion** (range-expansion/breakout mechanisms CONDITIONAL on a measurable state; NOT unconditional open-continuation).

## 1. Firewall statement

Inputs actually read (allowlist only):

- `PLAN_forex_v2.md`
- `research/control/forex_free_v2_run/run_contract.json`
- `research/control/forex_free_v2_run/frequency_contract.json`
- `research/control/forex_free_v2_run/data_manifest.json`
- `research/control/forex_free_v2_run/forbidden_family_inventory.json`
- `research/assets/forex/sessions.py`, `research/assets/forex/calendar.py`
- `research/assets/forex_free_v1/td_loader.py` (bar JSON schema only: datetime/open/high/low/close; no volume field)

Not read (and not opened/grepped): anything under `research/control/forex_free_v1_run/`, the V1 family/runner modules, anything under `research/proposals/` (any cycle, including other lanes), `tests/assets/forex_free_v1/`, `PLAN_forex.md`, any git history (`git log`/`git show`/`git diff` never run). No `data_raw/**` read; no backtest, PnL, or schedule simulation computed. The only V1 knowledge used is the mechanism names and summary evidence quoted inside the allowlisted forbidden inventory and owner plan.

## 2. Design constraints carried into the search

- H1 OHLC only (no volume in the free snapshot schema); D1 context-only (not used at all in the final two proposals); H4/bid-ask/rollover UNAVAILABLE fail-closed.
- Forced flat at the 16:00 America/New_York bar open on the entry UTC day (strictly before 17:00 NY rollover; no carry claims).
- <= 1 entry/pair/UTC-day; <= 3 round trips/pair/week; deterministic governor.
- Entry at next allowed H1 open after decision-bar completion; exits one-event lagged; missing bars NO_TRADE fail-closed.
- One frozen parameter set per arm; no grids/menus/ranges.
- Session wall times referenced to the named-zone conventions in `sessions.py`; those defaults are SYNTHETIC_TEST_ONLY provenance and A3 owns reconciliation to authorized provider semantics (flagged inside both proposals).
- Forbidden-inventory distance: no London-open continuation, no late-NY fade, no London-to-NY momentum, no sign inversion, no session relabeling, no nearby-threshold/horizon rescue of either V1 family.

## 3. Idea longlist and rejection reasons

| # | Idea | Disposition | Reason |
|---|------|-------------|--------|
| 1 | Unconditional London-open continuation | REJECTED | Identity (or nearby-clock variant) of forbidden V1 family1. |
| 2 | Late-NY standardized-extension fade | REJECTED | Identity of forbidden V1 family2. |
| 3 | Late-NY extension BREAKOUT (conditioned) | REJECTED | Clock adjacency to family2's late-NY anchor: high novelty-audit risk even with the mechanism sign flipped by construction rather than by inversion; dominated by the two selected anchors on distinctiveness. |
| 4 | Sign-inverted fade (breakout at late-NY extension) | REJECTED | Sign inversion is a forbidden rescue operation; also same as idea 3's adjacency problem. |
| 5 | London-open to NY-open momentum carry | REJECTED | The known forbidden near-duplicate. |
| 6 | Weekend-gap Monday continuation (Sunday-open gap state) | REJECTED | No literature source I can cite with certainty for FX Sunday-open gaps; frequency too thin (~1 candidate day/week, further gated by the gap-size state) to be robust against the minimum-trades contract; value-date/weekend structure cannot be validated without rollover authority. |
| 7 | NY opening-range breakout conditioned on a narrow opening range (classic ORB) | REJECTED as the second proposal | Same state KIND as P1 (pre-session compression -> breakout). With the anchor session swapped it would read as a menu twin inside my own lane; the mission requires genuinely different mechanisms. Kept Crabel's compression-conditioning idea but moved it to the Tokyo->London anchor (P1). |
| 8 | Inside-day / NR7-style same-session breakout | REJECTED | Compression state again — twin of idea 7/P1's state; adds nothing but a relabeled lookback. |
| 9 | Cross-pair lead/lag conditioned breakout | REJECTED | Outside the assigned mechanism class (lead/lag, not session-range expansion) and inside another lane's natural domain per the plan's search-domain list. |
| 10 | Cross-sectional dispersion / relative-value dislocation | REJECTED | Outside assigned class. |
| 11 | Macro/news-calendar conditioned expansion | REJECTED | No authoritative event calendar exists in the free snapshot; the PIT event clock in `calendar.py` requires an event source that is UNAVAILABLE fail-closed. |
| 12 | Spread/liquidity-conditioned variants (trade only when implied spread proxies are tight) | REJECTED | bid/ask UNAVAILABLE fail-closed; OHLC-only proxies cannot identify transaction liquidity. |
| 13 | Volatility-regime switches (range-of-range ratios, vol-of-vol) | REJECTED | State machinery without a range-expansion monetization rule; not in the assigned class. |
| 14 | Session relabeling of either rejected V1 family | REJECTED | Forbidden operation. |
| 15 | **Tokyo-range compression -> first London-morning breach of the overnight extremes** (SELECTED as P1) | SELECTED | Assigned class; conditional (fires only on a measured compression state); anchor session (Tokyo) and trigger (prior-range level breach) are both distinct from V1's open-continuation; certain literature trace (Crabel 1990; Osler 2000). |
| 16 | **London-AM range -> London-afternoon breach confirmed by retest-hold** (SELECTED as P2) | SELECTED | Assigned class; conditional on a post-break REACTION state (touch-and-hold beyond the broken pole) rather than any pre-session volatility state; different anchor session, different trigger window, different state kind, no trailing lookback at all; certain literature trace (Osler 2003; Brock/Lakonishok/LeBaron 1992). |
| 17 | Control option for P2: unconditional break-at-first-touch | REJECTED as the control design | It embeds a rival UNCONDITIONAL breakout mechanism, so a positive control would be uninformative about the proposed ingredient. Chose the complement-state (void-entry) placebo instead: same trigger day, opposite reaction state. |
| 18 | Control option for P1: unconditional (state-free) breakout | REJECTED as the control design | Same reason as 17. Chose the midpoint-level placebo: identical day, state, windows, and exits; only the level concept (extremes vs range center) changes. |

## 4. Why the two proposals are genuinely different (not menu twins)

| Dimension | P1 | P2 |
|-----------|----|----|
| Anchor range measured | Tokyo session 09:00-18:00 Asia/Tokyo (prior session) | London-AM 08:00-12:00 Europe/London (same-day morning) |
| Conditionality state KIND | Pre-session volatility state (range compression vs trailing-20 median) | Post-break REACTION state (retest touch-and-hold beyond the broken pole); no volatility filter at all |
| Trading window | London morning [08:00,12:00) local | London afternoon [12:00,17:00) local, resolution to [12:00,19:00) |
| Trigger | Overnight-range extreme breach | Morning-range extreme breach + confirmed retest |
| Lookback/warmup | 600 H1 bars (21 Tokyo sessions of state history) | 48 H1 bars (same-day state; no history needed) |
| Literature anchor | Crabel (1990); Osler (2000) | Osler (2003); Brock/Lakonishok/LeBaron (1992) |
| Expected frequency | ~1.3 RT/pair/week | ~1.0 RT/pair/week |

Both share the frozen exit law (close-back-inside invalidation + 16:00 NY forced flat), governor, folds, concentration, drop-one, cost authority, and pair universe — that is schedule comparability, not mechanism similarity.

## 5. Novelty self-check against the forbidden inventory

- P1: not London-open continuation (no open price/direction; conditional on compression; trigger is a prior-session range breach; ~30% of days vs daily cadence). Not late-NY anything. No inversion, relabeling, or threshold rescue of V1 families.
- P2: not London-open continuation (entry requires a same-day reaction state; levels from the pre-break range, not the open). Not London-to-NY momentum (no cross-session direction carry; all entries close inside the London afternoon, entry deadline < 20:00 London). Not late-NY fade (opposite mechanism family, different anchor). No inversion, relabeling, or rescue.
- A7-N owns the independent novelty decision; these self-checks are input to that audit, not a substitute.

## 6. Assumption register (implementation-relevant, frozen here)

1. Stop-style exits execute at the next H1 open after the triggering completed bar (one-event lag, conservative; no intrabar stop fills are claimed).
2. Forced-flat bar absent (Friday 16:00 NY weekly close) => exit at the open of the immediately preceding existing bar (recorded `early_forced_flat`); no position crosses 17:00 NY.
3. Range-validity is strict: any missing bar in a measured window voids the day (NO_TRADE fail-closed); trailing state requires 20 valid sessions within 30 calendar days.
4. Both-in-one-bar double breaks resolve by close position vs the range midpoint; exact ties do not trade.
5. Frequency numbers are schedule-level estimates for the feasibility audit; they are not tuned and carry explicit bands; the governor guarantees the caps regardless of estimate error.
6. Literature citations were included only where I am certain the source exists with the stated venue/year and claim; no source was reconstructed from memory beyond author/venue/year/one-sentence-claim precision.
