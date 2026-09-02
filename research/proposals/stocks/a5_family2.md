# A5-S2 Family 2 — Ex-Date Tax-Clientele Dividend Capture (Honest Liability Accounting)

- lane: A5 (accounting / borrow / execution), sprint S2
- family_id: `A5-S2-F2-EXDATE-TAX-CLIENTELE-CAPTURE`
- arms: `anchor`, `neighbour`, `negative_control` — exactly 3 cells
- retrieval note: literature cited from **MODEL_INTERNAL_UNVERIFIED** memory (no network this sprint); no DOIs, no verbatim quotes; where the post-2003 US evidence is thin in memory, the gap is stated rather than masked with a citation.
- outcome-blind: no scored PnL/PF/Sharpe/ranking computed or read; cost-drag arithmetic is analytic, derived from the frozen cost models and published magnitudes only.

## 1. Economic mechanism and expected counterparty

The marginal sellers into cum-dividend dates are taxable investors for whom dividends carry a tax penalty relative to capital gains; equilibrium therefore sets the ex-date price drop below the dividend for penalized payers (Elton & Gruber 1970, *Journal of Finance*; Kalay 1982, *Journal of Finance* bounds; Michaely 1991, *Journal of Finance*, 1986 tax-reform evidence; Boyd & Jagannathan 1994, *Journal of Finance*). A tax-advantaged buyer holding through the ex-date mechanically earns **capture = (1 − r) × div** per share, where r is the drop ratio. The distortion concentrates in ordinary-income / non-qualified / high-yield payers (REITs are the clean case) and vanishes where dividends are qualified and small (r → 1). Green & Rydqvist (1999, *JFE*) show the sign can flip when the clientele's coupon penalty exceeds the capital-gains rate; Frank & Jagannathan (1998, *JFE*) document the no-tax microstructure counterpoint that motivates our control arm.

**The A5 lens is the point of this family.** On adjusted (total-return) series the entire effect is invisible by construction; on naive hedged backtests built from TR series the hedge leg's ex-date liability silently vanishes. The factory's explicit raw-price fills plus `DividendEvent` buckets (`cash_dividends` for the long, `short_dividend_liability` for any hedge short) are what make the accounting honest: capture is an explicit cash receipt inside the canonical identity, and the hedge's liability is a named identity term that must be paid.

Expected counterparties: (1) taxable sellers avoiding the dividend penalty; (2) ex-date liquidity providers/dealers whose effective penalty is low; (3) for the hedged variant, the lending desk supplying the sector-ETF short.

## 2. PIT fields and source authority

| Field | Authority | Status |
|---|---|---|
| declared dividend per share, PIT ex-date, declaration timestamp | corporate-actions master (A4) | fixture **now**; real **UNAVAILABLE_PENDING_ENTITLEMENT** |
| dividend tax character (qualified vs ordinary), REIT classification | security master + provider tax metadata | **UNAVAILABLE_PENDING_ENTITLEMENT** (fixture carries a declared boolean) |
| price, NBBO quotes at entry/exit events, halted/session flags | US equities quotes provider | fixture **now**; real **UNAVAILABLE_PENDING_ENTITLEMENT** |
| ADV / participation context | OHLCV provider | fixture **now**; real **UNAVAILABLE_PENDING_ENTITLEMENT** |
| ETF borrow locate + PIT rate (hedged variant) | prime-broker / securities-finance feed | **UNAVAILABLE_PENDING_ENTITLEMENT** |
| earnings timestamps (PIT, B/A) | earnings calendar provider | **UNAVAILABLE_PENDING_ENTITLEMENT** |
| splits with ex/effective timestamps | corporate-actions master (A4) | fixture **now**; real **UNAVAILABLE_PENDING_ENTITLEMENT** |

Only dividends **declared before** the formation signal enter the event calendar (no announcement leakage).

## 3. Universe, neutralization, benchmark

- Universe: US-listed common stocks and REITs paying discrete declared cash dividends above a fixed ex-date-yield floor; the **event** (name × ex-date) is the unit; membership evaluated PIT at each event's formation. The long leg is single-name only — no dividend-ETF stand-ins.
- Neutralization: the mechanism is not sectoral; the declared context is **event matching** — anchor and control are compared only on events matched by declaration month and yield bucket, with fixed dollar notional per event so no market-beta drift accumulates.
- Benchmarks: flat, SPY total return, and the declared factor-neutral context: the event-matched placebo (the negative-control arm is the matched context).

## 4. Formation, holding and execution clocks

- **Formation**: signal at the regular-session close 5 sessions before the ex-date (T−5), from the PIT declared-ex-date calendar.
- **Holding**: from the entry event through the ex-date (dividend receipt books at the ex-date event) to the exit at the T+1 session close; if the exit event is non-executable, hold to the next executable event — fail closed, never a stale print. Flat positions book nothing (factory-native: dividends apply only to positions held through the ex-date).
- **Execution**: entry at the first executable regular-session event strictly after the T−5 close (one-event delay); exit at the executable T+1 close event; every order passes `attempt_fill` with the HALTED → SESSION_CLOSED → MISSING_QUOTE → MISSING_ADV → PARTICIPATION_CAP fail-closed order. An entry NO_FILL skips the event entirely — capture counts only when the full round trip executes.

All three clocks are expressible in the existing factory with no new machinery.

## 5. Expected turnover, capacity and cost-drag reasoning

- Turnover: one round trip per event; annualized two-sided turnover of deployed notional of order 50–150 round trips per year-slot across a broad payer calendar — fast and event-concentrated, so the cost identity, not the signal, binds.
- Friction per event (frozen model): commission ~0.3–1 bps per leg; half-spread on both legs — quotes of order 1–5 bps for liquid large-cap payers, declared conservative proxy 5–15 bps; declared slippage; sqrt impact at ≤ 2% participation with hard cap. All-in round trip of order **4–20 bps** by liquidity tier.
- Gross capture = (1 − r) × ex-date yield, with honestly uncertain post-2003 r ∈ [0.6, 0.95]: a 0.5%-of-price quarterly event captures ~2.5–20 bps — friction can fully consume it at the high-r end; a 1.0–1.5%-of-price REIT event captures ~25–75 bps at the low-r end, comfortably above friction, collapsing below it as r → 0.95. The family lives or dies on (a) targeting the high-penalty tail and (b) the honest spread/impact ledger. A naive engine that books the dividend into an adjusted series, or books the hedge carry as zero, **manufactures capture out of the accounting itself**.
- Capacity: a small percent of pre-ex-date ADV per event (capture buying moves the drop ratio itself — r endogeneity self-limits size); strategy-wide realistically order 10–100M USD.

## 6. Anchor, neighbour, causal negative control (3 cells)

1. **anchor** — long through ex-date on declared non-qualified / ordinary-income / top-yield-quintile payers, fixed notional, honest dividend receipt on the raw-price ledger; declared hedged variant: sector-ETF short with explicitly booked borrow fee and its own ex-date dividend liability.
2. **neighbour** — the same mechanism restricted to **REITs**, the clean ordinary-income class with the largest predicted tax penalty; Elton-Gruber theory predicts the shortfall scales with the holder's penalty, so the mechanism's strongest form lives exactly there (Green & Rydqvist 1999 provide the analogous sign-flip precedent).
3. **negative_control** — identical clock, cost model and notional on **qualified-dividend, lowest-yield-quintile** payers, where theory predicts r ≈ 1 and capture ≈ 0, so the honest ledger should show a spread at or below round-trip friction. Anchor-like capture there falsifies the tax-clientele mechanism as a generic yield/price-pressure artifact.

## 7. Corporate actions, earnings, borrow, dividends

- **Corporate actions**: the dividend is the action — booked from the PIT `DividendEvent` at ex-date; events with a split inside the holding window are excluded (clean identity); special dividends allowed only if declared before T−5 and flagged.
- **Earnings**: events whose [T−1, T+1] window contains the name's PIT earnings timestamp are excluded entirely (drop/surprise confound); on the fixture this runs against fixture timestamps only.
- **Borrow (special duty)**: the anchor core is long-only and needs no locate. The hedged variant shorts a sector ETF under the full locate discipline: PIT `BorrowLocate` per hedge; missing/unavailable locate falls back to the unhedged variant (fail closed, never a free short); daily fee accrual at `rate*days/360`. Feasibility conditional declared: hedge only when the GC-level rate's expected 6–7-session cost (order 3–10 bps of hedge notional) is below the diversification benefit.
- **Dividends**: long receipt into `cash_dividends` at the ex-date; hedge ETF short books its own ex-date payouts into `short_dividend_liability` — explicitly, on the ETF's own ex-dates, never assumed away; flat positions book nothing (no phantom receipt).

## 8. Falsification rule and external-validity caveats

Falsify the family if ANY of:

1. anchor's net per-event capture (dividend receipt minus raw-price round trip minus all four cost buckets minus hedge borrow/liability when hedged) is not positive across S0 event folds;
2. the negative-control arm shows capture of anchor-like magnitude;
3. the REIT neighbour does not rank at or above the anchor (tax-penalty ordering violated);
4. capture appears only in a configuration where the dividend is credited without the raw ex-date drop being paid — on the honest ledger that configuration is impossible, so this is enforced as a construction assertion in goldens, not as a scored outcome.

Preregistered before any scored cell exists.

Caveats: the post-2003 qualified-dividend regime compresses the shortfall (honest prior: thin); the Frank–Jagannathan microstructure alternative (bid-ask bounce) motivates executable-quote fills but cannot be excluded ex ante — hence the mandatory control arm; dividend capture is a crowded dealer trade and r is endogenous to capture demand; tax-law changes are structural breaks; REIT ex-day microstructure idiosyncrasies (low prices, lot sizes) could fail the neighbour for non-mechanism reasons.

## 9. Maximum trial count

**Exactly 3 cells** (anchor, neighbour, negative_control). No lookback/threshold grid anywhere; the yield floor is a fixed universe-definition parameter, not a searched threshold.

## Eligibility and novelty

- Not an indicator/lookback/threshold grid: one mechanism, three theory-linked arms.
- Not a rescue of the rejected crypto families (M01 aggressor-flow absorption, funding-carry, weekly reversal): distinct **observable** (PIT declared-dividend/ex-date calendar and tax character), distinct **counterparty** (taxable cum-date sellers and ex-date dealers), distinct **clock** (event-driven multi-day holds keyed to ex-dates), distinct **causal control** (qualified low-yield placebo removing the tax-penalty channel).

## Data readiness

- Synthetic-fixture factory: **IMPLEMENTABLE NOW** (`DividendEvent` fixtures, quotes/halt flags, ADV, split exclusion, locate records are first-class factory inputs).
- Real data: **BLOCKED pending owner-authorized entitlement** (PIT declared dividends + tax character, earnings calendar, ETF borrow). This proposal authorizes no purchase.
